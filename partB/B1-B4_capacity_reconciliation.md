# Part B — Capacity reconciliation

All arithmetic below was hand-derived, then verified with a short Python
calculator script (`verify.py`, included) — not run as a "trust the code"
step, but as a check on hand arithmetic, per the instruction to avoid
running code except where it matters. Every number here is checked against
`bench_log.csv` directly.

## B1 — KV-cache bytes/token, max concurrent 4096-token sequences

**KV-cache bytes per token (exact):**

```
bytes/token = 2 (K and V) × n_layers × n_kv_heads × head_dim × bytes/element
            = 2 × 28 × 8 × 128 × 2        (fp16 = 2 bytes, GQA: 8 KV heads not 24 Q heads)
            = 114,688 bytes/token  (= 112 KiB/token)
```

Uses `n_kv_heads` (8, the GQA count), not `n_heads` (24) — this is the
whole point of GQA: multiple query heads share each KV head, so the cache
only needs to be sized for 8 heads' worth of K/V, not 24.

**Max concurrent 4096-token sequences:**

GPU memory budget (assumption stated explicitly: using decimal GB = 1e9
bytes, the NVIDIA spec convention for VRAM totals):

```
total GPU memory        = 24e9 bytes
usable (util 0.92)       = 0.92 × 24e9        = 22.08e9 bytes
model weights (fp16)     = 4.2e9 params × 2   = 8.40e9 bytes
non-KV overhead (given)  =                      1.60e9 bytes
--------------------------------------------------------
available for KV cache    = 22.08e9 − 8.40e9 − 1.60e9 = 12.08e9 bytes

bytes for one full 4096-token sequence = 114,688 × 4096 = 469,762,048 bytes

max concurrent full sequences = 12.08e9 / 469,762,048 ≈ 25.7  →  ~25
```

**Check against the log (this is the important part):** at `batch=24,
prompt=3584, gen=512` (i.e. every sequence grows to exactly 3584+512=4096
tokens — the full context window), `kv_cache_util=0.93` and
`preempted_seqs=0`. Working backward from that data point:

```
bytes actually used by 24 full sequences = 24 × 4096 × 114,688 = 11,274,289,152
implied total KV pool = 11,274,289,152 / 0.93 = 12,122,891,561 bytes
implied max sequences = 12,122,891,561 / 469,762,048 ≈ 25.8
```

**This matches the theoretical estimate (25.7) to within 0.4%.** Two more
checks confirm it: at `batch=16` (same prompt/gen), predicted util =
16/25.7 = **0.622**, log shows **0.62** exactly. At `batch=32`,
`preempted_seqs=7`, and 32−7=**25** — exactly the computed ceiling. The
scheduler is preempting precisely the sequences that don't fit.

## B2 — the long-context throughput anomaly

Naive expectation: throughput scales with batch size. Instead, in the
`prompt=3584` rows, `reported_tok_s` **peaks at batch=24 (1607.4)** and then
**falls** at batch=32 (1384.0, −14%) and batch=48 (1298.5, −19% from peak) —
even though more requests are being served.

**Mechanism, using specific rows:** this is the same KV-cache ceiling from
B1 (~25 sequences). At batch=24 (≤25), everything fits, `preempted_seqs=0`.
At batch=32 and 48 (>25), the scheduler runs out of KV cache mid-generation
and **preempts** sequences — `preempted_seqs` jumps to 7 (batch=32) and 23
(batch=48), while `kv_cache_util` caps at 0.97 (can't exceed the physical
pool). A preempted sequence's KV cache is evicted; when it's rescheduled,
its ~3584-token prompt has to be **reprocessed from scratch** (re-prefill)
before decode can resume. That reprocessing burns GPU cycles that produce
zero new output tokens, which is why total throughput drops even as more
requests are nominally "in flight." The symptom shows up doubly in
`e2e_ms_p95`, which balloons from 69,221ms (batch=24) to 97,466ms (batch=32)
to 105,427ms (batch=48) — latency getting much worse while throughput gets
*worse*, the classic preemption-thrashing signature.

**Proposed change:** cap `max_num_seqs` (admission control) at ~24 for this
prompt/gen-length profile, rather than letting the scheduler admit 32 or 48
requests and then thrash. **Predicted effect:** sustained throughput stays
at the observed peak (~1607 tok/s) instead of degrading to 1298.5 tok/s
under batch=48 offered load — a **~24% relative throughput improvement**,
plus avoiding the latency blowup (69s p95 vs 105s p95, ~34% better) that
comes from preemption/requeue cycles. (A second-order option — more GPU
memory, e.g. an L4 with more VRAM or 2×L4 tensor-parallel — raises the
ceiling itself rather than just avoiding crossing it; admission control is
the zero-hardware-cost fix available immediately.)

## B3 — the misread column, and honest goodput

**What REPORT_v0 misread:** `reported_tok_s` counts **prompt + generated
tokens together**, divided by wall-clock time — not just newly generated
("goodput") tokens. Verified directly from the log:

```
reported_tok_s == (prompt_len + gen_len) × num_requests / wall_clock_s

batch=1,  prompt=512:  (512+256)×1/10.94   = 70.2   (reported: 70.2)  ✓
batch=16, prompt=512:  (512+256)×16/13.91  = 883.4  (reported: 883.2) ✓
batch=16, prompt=3584: (3584+512)×16/49.97 = 1311.5 (reported: 1311.4) ✓
batch=24, prompt=3584: (3584+512)×24/61.16 = 1607.3 (reported: 1607.4) ✓
```

The formula reproduces every reported value exactly (to rounding). This is
the single root cause of **both** of REPORT_v0's Section 2 conclusions:

- "Longer prompts give better throughput" — no: long prompts have a much
  bigger one-time prefill token count (3584 vs 512), which this metric
  counts identically to decode tokens. It looks faster because it's
  counting work (prefill) the user never experiences as "generation
  speed," not because decode is actually faster.
- "Batch 48 → ~3200 tok/s" — built on the same inflated metric, then
  extrapolated linearly, ignoring the preemption ceiling from B1/B2 (which
  makes batch=48 *slower* in the log, not faster).

**Honest decode goodput for batch=24, prompt=3584** — derived two
independent ways:

*Method A — directly from the log:*
```
goodput = gen_len × num_requests / wall_clock_s
        = 512 × 24 / 61.16
        = 200.9 tok/s
```

*Method B — from the per-token latency columns (ttft/itl), which are not
derived from reported_tok_s at all:*
```
per-sequence time to generate 512 tokens ≈ ttft_p50 + (gen_len−1) × itl_p50
        = 0.5005s + 511 × 0.09607s
        = 49.59s
per-sequence goodput = 512 / 49.59s = 10.32 tok/s
aggregate goodput (24 concurrent sequences) = 10.32 × 24 = 247.8 tok/s
```

Both methods land in the **~200-250 tok/s** range — roughly **8× lower**
than the reported 1607.4 tok/s. The two methods aren't identical (200.9 vs
247.8) because Method A's wall-clock includes queueing/scheduling overhead
that per-token median latencies in Method B don't fully capture, but they
agree on the order of magnitude and both are an order of magnitude below
the reported figure.

**What the report should have said:** separate prefill throughput
(compute-bound, mostly a one-time cost per request, and what makes long
prompts *look* fast on this metric) from decode/goodput throughput (the
number that actually reflects what a user experiences as generation
speed). The honest goodput at batch=24/prompt=3584 is ~200-250 tok/s, not
1607 tok/s — and batch=48 should have been flagged as *past* the capacity
ceiling (B1), not extrapolated past it.

## B4 — metric to confirm the B2 mechanism

Pull the serving stack's **preemption / recomputed-prefill-token counter**
(in vLLM-style stacks, something like `num_preemptions_total` alongside the
scheduler's running vs. waiting queue lengths) rather than relying only on
the already-visible `preempted_seqs` column, because that counter would
directly show GPU cycles being spent *re-processing already-seen prompt
tokens* for evicted sequences rather than producing new output — the actual
mechanism claimed in B2, not just its symptom. Expected value: nonzero and
growing exactly where `preempted_seqs` is nonzero (batch=32 onward), with
the number of recomputed tokens roughly tracking `preempted_seqs ×
prompt_len` — e.g. at batch=48 (23 preemptions), on the order of
23 × 3584 ≈ 82,400 wastefully-reprocessed prefill tokens, against only
48 × 512 = 24,576 tokens of actual new content generated in that run —
which is the real reason throughput collapses rather than merely plateaus.
