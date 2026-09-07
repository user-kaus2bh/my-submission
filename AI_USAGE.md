# AI_USAGE.md

## How this was built

I used Claude for nearly all of the implementation in this submission —
reading `fertility.py` line by line to find the planted bugs, sourcing a
substitute corpus when FLORES-200 turned out to be unreachable, training
the toy tokenizers, writing every script, deriving the B1-B4 capacity
arithmetic, and drafting all four write-ups. I want to be upfront about
that rather than dress it up, since I understand that's exactly what this
file is supposed to surface.

My own contribution was direction and quality control, not code:

- **Sequencing and scope.** I set the order of work (A1→A4, then B, then
  C) and decided when to stop digging and move on, rather than letting the
  audit sprawl.
- **Catching a real compliance gap.** Partway through, I asked Claude to
  check its own Part A work against the assignment's evidence rule
  directly. That surfaced two real problems — A2's findings only existed
  in chat, not as a repo file, and none of the individual bug claims had a
  single reproducible CLI command the way B1-B4 later did. That check was
  my call, not something Claude flagged on its own initiative before I
  asked. (As of this file, those two fixes are still outstanding — see the
  note at the bottom.)
- **The Part C decision.** Claude laid out why each of the three paths
  (SFT / rewriter / prompt-only) would perform, but I picked the deciding
  criterion — "which one is easiest for me to explain and defend live" —
  and that's what selected the rewriter model over the other two options.
  That criterion isn't in the assignment; it's mine, and it's the actual
  reason the memo argues for (b) instead of (a) or (c).
- **Everything I'll need to defend live**, I have not yet independently
  re-derived by hand outside this conversation. I'm treating that as my
  homework before the defense session, not something I can claim credit
  for now.

## Where AI helped

- Diagnosing the network sandbox constraint (no access to real `gpt2`/HF
  tokenizers or FLORES-200) quickly and turning it into a documented,
  defensible substitution (UDHR corpus, self-trained tokenizers with a
  train/eval split to avoid leakage) instead of silently faking numbers.
- The B1-B4 capacity arithmetic cross-validated itself against
  `bench_log.csv` to within rounding error on every check — that
  consistency is genuinely useful signal that the derivation is right, not
  just plausible-sounding.
- Reverse-engineering the exact `reported_tok_s` formula from the log
  (B3) — I would not have thought to test that hypothesis by back-solving
  from four different rows.

## Where AI could have misled me if I hadn't been checking

- The first-pass Part A submission was missing the A2 write-up entirely
  and didn't expose reproducible per-claim commands — it would have read
  as complete and evidence-backed without actually meeting the letter of
  the evidence rule, if I hadn't specifically asked for a compliance check.
- The toy-tokenizer-based claim about Bug 2's direction was wrong: it
  suggested that `.lower()` inflated the headline gap, when the real
  `gpt2` result showed the opposite. It took getting real tokenizer access
  — which I pursued — to catch that reversal. This is a useful reminder
  that conclusions drawn from a toy tokenizer can fail to transfer to a
  real pretrained tokenizer.
- Several of the toy-tokenizer numbers (e.g. the exact 6-8x gap between
  reported and honest goodput, the ~25-sequence KV cache ceiling) are
  presented with more confidence than a first read suggests — they hold up
  under the stated assumptions (decimal GB, this specific toy tokenizer's
  training data), but I have not yet personally stress-tested those
  assumptions by hand outside this conversation, which is a defense-day
  risk if I get asked "what if X assumption is wrong."
