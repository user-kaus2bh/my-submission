"""
verify.py -- checks the hand-derived arithmetic in B1-B4_capacity_reconciliation.md
against bench_log.csv. Run: python3 partB/verify.py
"""
import csv

# ---- B1: KV cache bytes/token and max concurrent sequences ----
n_layers, n_kv_heads, head_dim, bytes_per_elem = 28, 8, 128, 2
kv_bytes_per_token = 2 * n_layers * n_kv_heads * head_dim * bytes_per_elem
assert kv_bytes_per_token == 114688

total_gb, util = 24e9, 0.92
usable = total_gb * util
weights = 4.2e9 * 2
overhead = 1.6e9
kv_pool = usable - weights - overhead
bytes_per_full_seq = kv_bytes_per_token * 4096
max_seqs = kv_pool / bytes_per_full_seq

print("=== B1 ===")
print(f"KV bytes/token: {kv_bytes_per_token} ({kv_bytes_per_token/1024:.1f} KiB)")
print(f"KV pool available: {kv_pool:,.0f} bytes")
print(f"Theoretical max concurrent full (4096-tok) sequences: {max_seqs:.2f}")

rows = list(csv.DictReader(open("bench_log.csv")))
rows = [{k: (float(v) if k not in ("preempted_seqs",) else int(v)) if k != "" else v
         for k, v in r.items()} for r in rows]
for k in rows[0]:
    pass

row24 = next(r for r in rows if r["batch_size"] == 24 and r["prompt_len"] == 3584)
util24 = row24["kv_cache_util"]
implied_pool = (24 * 4096 * kv_bytes_per_token) / util24
print(f"Implied pool from batch=24 kv_cache_util={util24}: {implied_pool:,.0f} bytes "
      f"(implied max seqs: {implied_pool/bytes_per_full_seq:.2f})")

row32 = next(r for r in rows if r["batch_size"] == 32 and r["prompt_len"] == 3584)
print(f"batch=32: preempted_seqs={int(row32['preempted_seqs'])}, "
      f"32 - preempted = {32 - int(row32['preempted_seqs'])} (vs. max_seqs {max_seqs:.1f})")

row16 = next(r for r in rows if r["batch_size"] == 16 and r["prompt_len"] == 3584)
print(f"batch=16: predicted util {16/max_seqs:.3f} vs observed {row16['kv_cache_util']}")

# ---- B3: reported_tok_s formula check ----
print("\n=== B3 ===")
for r in rows:
    pred = (r["prompt_len"] + r["gen_len"]) * r["num_requests"] / r["wall_clock_s"]
    print(f"batch={int(r['batch_size']):<3} prompt={int(r['prompt_len']):<5} "
          f"predicted={pred:8.1f}  reported={r['reported_tok_s']:8.1f}  "
          f"diff={abs(pred-r['reported_tok_s']):.2f}")

# honest goodput, batch=24 long-prompt row, two methods
g1 = row24["gen_len"] * row24["num_requests"] / row24["wall_clock_s"]
ttft_s = row24["ttft_ms_p50"] / 1000
itl_s = row24["itl_ms_p50"] / 1000
seq_time = ttft_s + (row24["gen_len"] - 1) * itl_s
g2 = (row24["gen_len"] / seq_time) * row24["num_requests"]
print(f"\nGoodput batch=24/prompt=3584 -- Method A: {g1:.1f} tok/s, Method B: {g2:.1f} tok/s")
print(f"Reported (misleading) figure: {row24['reported_tok_s']} tok/s "
      f"({row24['reported_tok_s']/g1:.1f}x higher than Method A goodput)")
