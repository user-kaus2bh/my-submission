# A4 — Recommendation memo

**To:** Leadership / capacity planning
**Re:** Correction to REPORT_v0 tokenizer findings, and updated routing recommendation
**Status:** supersedes Section 1 of REPORT_v0

## Corrected headline numbers

REPORT_v0 claimed Hindi costs **~6× more tokens than English** to serve,
attributed to "a property of the script." Both the multiplier and the
causal claim are wrong.

- The 6× figure came from `fertility.py`'s tokens-per-word metric, computed
  with a tokenizer-agnostic framing that isn't tokenizer-agnostic at all:
  under an English-trained tokenizer the same script shows **10–20× worse**
  fertility; under a multilingual-aware tokenizer the same script shows
  **~2–3× worse**. The gap is dominated by *which tokenizer you use*, not
  an inherent property of Devanagari or Dravidian scripts.
- On the denominator that actually holds real content constant — tokens
  needed per unit of equivalent translated content, not per word/byte/
  grapheme, all of which distort the comparison in different directions
  (see A3) — the corrected multiplier for Hindi, Kannada, Tamil, Telugu,
  Bengali, and Marathi against English is **~2.0×–2.9×**, tightly
  clustered across all six languages, not 6×.

## Routing recommendation

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
