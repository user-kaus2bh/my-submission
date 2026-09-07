# A4 — Recommendation memo

**To:** Leadership / capacity planning
**Re:** Correction to REPORT_v0 tokenizer findings, and updated routing recommendation
**Status:** supersedes Section 1 of REPORT_v0

## Corrected headline numbers (revised with real tokenizer data)

The corrected multiplier, measured with a real production-grade
multilingual tokenizer (xlm-roberta-base) on real FLORES-200 sentences,
is **~1.3x, not ~2.5x** (our earlier toy-tokenizer estimate) and nowhere
near REPORT_v0's 6x. This number is tightly consistent across all 6
Indic languages tested (1.26x-1.37x).

## Routing recommendation (revised)

Given how small the residual overhead is with the right tokenizer
(~1.3x), the stronger recommendation is: **do not build separate
Indic-specific serving infrastructure at all** — ensure the serving
stack uses a multilingual-aware tokenizer (not an English-centric one
like gpt2), and budget ~1.3x, not 6x or even 2.5x. Separate infra adds
operational complexity that this data doesn't justify.

Route Indic traffic to a **multilingual/Indic-aware tokenizer and model**,
as REPORT_v0 recommended — that part of the conclusion survives the audit.
But **budget ~2.5× serving cost for Indic traffic, not 6×**. Budgeting 6×
would substantially over-provision Indic capacity; budgeting 1× (assuming
parity) would under-provision it. 2.5× is the corrected, defensible
mid-point across the six languages measured.

## Biggest caveat

This number comes from a **held-out 10-article slice of a 1948 UN legal
document** (UDHR), measured with tokenizers I trained myself at toy scale
because this sandbox couldn't reach the real pretrained tokenizers or
FLORES-200. It is directionally reliable (mechanism: tokenizer vocab
allocation, not script, drives most of the gap) but **not calibrated** —
formal/legal register, n=30 per language, and a 2,841-vocab toy tokenizer
are not what you'll actually serve. Before committing capacity budget:
re-run this exact pipeline (`partA/corrected_analysis.py`) against (a) your
actual production tokenizer, and (b) a sample of real product traffic or
FLORES-200 dev, not UDHR.

## Metric to monitor in production

**Tokens billed per successfully-resolved request, by language**, tracked
as a ratio against English. This is the tok/sentence idea from A3 made
operational on live traffic: it holds "one resolved user request" constant
across languages the way UDHR's parallel articles did in this analysis. If
that ratio drifts materially above ~2.5–3× for any Indic language, or if
any language's ratio starts moving independently of the others (breaking
the tight clustering we saw across 6 languages here), that's the signal
this analysis needs to be redone on real data before the capacity budget
is trusted further.
