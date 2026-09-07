# A3 — Corrected cross-language analysis

## Setup

Two tokenizers, same algorithm (byte-level BPE), different training data —
isolating "what the tokenizer saw" as the only variable:

| | tok_A "web-english" | tok_B "multilingual-indic" |
|---|---|---|
| training data | Norvig's `big.txt`, ~6.5MB natural English prose (Project Gutenberg books + word lists) | UDHR **train split** (articles 1–20, all 8 languages) — ~160 short lines total |
| role | proxy for a GPT-2-style tokenizer trained on English-dominated web text | proxy for an Indic-aware multilingual tokenizer (MuRIL/IndicBERT-style) |
| vocab budget | 8,000 | 8,000 |
| vocab actually learned | 8,000 (budget fully used) | 2,841 (ran out of frequent-enough merges — training data is tiny) |

**No leakage:** tok_B is trained only on articles 1–20; all fertility numbers
below are measured on the **held-out** articles 21–30, which tok_B never saw
during training.

**Caveat carried forward from A1:** tok_B's training set (~160 lines) is
minuscule next to a real production tokenizer (billions of tokens). Its
absolute vocab size (2,841) is toy-scale. What generalizes from this
experiment is the *mechanism and direction* — vocab budget allocation
across languages changes fertility — not the exact numbers. This is stated
explicitly so it isn't mistaken for a production benchmark.

Four denominators, all using the A2-fixed code (`split()` not `split(" ")`,
no forced lowercasing, true grapheme clusters via Unicode `\X` clusters not
raw codepoints, micro-averaged as sum/sum not per-line macro-average).

## Headline numbers (UDHR eval split, held out)

| lang | tokzr | tok/word | tok/grapheme | tok/byte | tok/sentence |
|---|---|---|---|---|---|
| eng | web-english (A) | 1.35 | 0.221 | 0.220 | 87.4 |
| eng | multiling (B) | 2.08 | 0.338 | 0.338 | 134.1 |
| hin | web-english (A) | 14.41 | 4.299 | **1.000** | 1096.2 |
| hin | multiling (B) | 3.88 | 1.157 | 0.269 | 295.0 |
| kan | web-english (A) | 26.73 | 4.194 | **1.000** | 1077.4 |
| kan | multiling (B) | 7.30 | 1.146 | 0.273 | 294.3 |
| tam | web-english (A) | 31.03 | 4.419 | **1.000** | 1374.7 |
| tam | multiling (B) | 8.70 | 1.239 | 0.280 | 385.5 |
| tel | web-english (A) | 26.39 | 4.700 | **1.000** | 1129.3 |
| tel | multiling (B) | 7.09 | 1.263 | 0.269 | 303.5 |
| mal | web-english (A) | 39.67 | 6.215 | **1.000** | 1241.8 |
| mal | multiling (B) | 10.92 | 1.711 | 0.275 | 341.9 |
| ben | web-english (A) | 19.47 | 4.490 | **1.000** | 991.0 |
| ben | multiling (B) | 5.36 | 1.236 | 0.275 | 272.7 |
| mar | web-english (A) | 19.90 | 4.707 | **1.000** | 1136.2 |
| mar | multiling (B) | 5.52 | 1.307 | 0.278 | 315.4 |

(Casual-domain subset, eng+hin only — same direction, confirms it's not a
formal-register artifact: tok/word ratio 7.6× under tok_A vs. 1.1× under
tok_B; full numbers in `corrected_analysis.py` output.)

## Finding 1 — the report's "it's the script, not the tokenizer" claim is wrong

Look at the **hin/eng ratio** for the *same script*, under the two
tokenizers:

| denominator | ratio under tok_A (web-english) | ratio under tok_B (multilingual) |
|---|---|---|
| tok/word | **10.65×** | **1.87×** |
| tok/grapheme | 19.50× | 3.42× |
| tok/byte | 4.54× | 0.80× |
| tok/sentence | 12.54× | 2.20× |

Same Hindi text, same script, same content. The ratio moves by **5–8×**
depending purely on what the tokenizer was trained on. Under tok_A, Hindi's
`tok/byte` is exactly **1.0000** — every single UTF-8 byte becomes its own
token, because a tokenizer that has never seen a Devanagari byte sequence
has no merges for it and falls back to raw bytes. This is the real,
well-documented failure mode of English-centric BPE tokenizers (GPT-2's
real tokenizer does exactly this to Hindi/Kannada/Tamil/Telugu/Malayalam
text). REPORT_v0's claim that "any tokenizer will struggle... this is a
property of the script, not the tokenizer" is directly falsified by this
experiment: swapping only the tokenizer's training data cuts the gap by
roughly 5–8× while the script stays identical.

## Finding 2 — which denominator to trust, and why

The spread across denominators, under the *same* (multilingual) tokenizer:

| lang | tok/word ratio vs eng | tok/sentence ratio vs eng | tok/byte ratio vs eng | tok/grapheme ratio vs eng |
|---|---|---|---|---|
| hin | 1.87 | 2.20 | 0.80 | 3.42 |
| kan | 3.52 | 2.19 | 0.81 | 3.39 |
| tam | 4.19 | 2.87 | 0.83 | 3.66 |
| tel | 3.42 | 2.26 | 0.80 | 3.73 |
| mal | 5.26 | 2.55 | 0.81 | 5.06 |
| ben | 2.58 | 2.03 | 0.81 | 3.65 |
| mar | 2.66 | 2.35 | 0.82 | 3.86 |

Reasoning through each candidate, per the assignment's hint ("what is the
denominator supposed to hold constant?"):

- **tok/word** — supposed to hold "one unit of language" constant, but
  doesn't: Malayalam and Tamil are more agglutinative than Hindi (more
  morphology packed per whitespace-delimited word), so their ratio (5.26×,
  4.19×) is inflated by *word-segmentation convention*, not real cost. This
  is exactly the A2 conceptual bug, confirmed here across 6 more languages.
- **tok/grapheme** — supposed to hold "one visual character" constant, but
  a Devanagari/Dravidian grapheme cluster (consonant + vowel sign,
  sometimes + conjunct) typically encodes more phonetic/orthographic
  information than a single Latin letter. Ratio (3.4–5.1×) partly reflects
  that information-per-grapheme difference, not tokenizer waste.
- **tok/byte** — supposed to hold "one unit of transmitted data" constant,
  but UTF-8 encodes Devanagari/Dravidian scripts in 3 bytes/character vs.
  Latin's 1 byte/character. That inflates the byte denominator for Indic
  languages independent of content, which is why the ratio here is
  **below 1** (0.80–0.83×) — i.e. tok/byte makes Hindi look *cheaper* than
  English, which is clearly not the real-world experience of serving it.
  This denominator is biased in the *opposite* direction from tok/word.
- **tok/sentence (tokens per parallel content unit)** — supposed to hold
  "the same real content" constant, and for once actually can: every
  article number is a translation of identical meaning across all 8
  languages. This is also the *tightest* spread across 6 typologically
  distinct languages (2.03–2.87×, a 1.4× range) versus tok/word's
  1.87–5.26× (a 2.8× range) or tok/grapheme's 3.39–5.06× (a 1.5× range,
  but all inflated). Tighter spread across unrelated languages measuring
  the same content is itself evidence this metric is capturing something
  more real and less an artifact of any one language's segmentation
  convention.

**Answer: tokens-per-unit-of-equivalent-content (tok/sentence here) should
drive the routing/cost decision.** It's the only denominator that holds the
thing an actual serving-cost decision cares about — how many billable
tokens it takes to handle the same real request — constant across
languages. Word count, grapheme count, and byte count all vary with
orthographic and morphological convention in ways that have nothing to do
with cost, and each biases the comparison in a different, non-obvious
direction (tok/word and tok/grapheme *overstate* the Indic penalty by
conflating it with morphology/script density; tok/byte *understates* it by
conflating it with UTF-8 encoding width).

**Limitation to flag explicitly:** tok/sentence only works because we have
genuinely parallel content (UDHR articles translated from the same source).
In production you won't have "the same request" issued in every language —
you'd need either (a) a translation-equivalent benchmark set built for this
purpose, or (b) a proxy like tokens-per-resolved-user-intent measured from
real logs where the same intent occurs in multiple languages. This is the
biggest caveat to carry into A4.
