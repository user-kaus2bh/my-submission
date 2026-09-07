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

## Update — real tokenizers, real FLORES-200 corpus

The toy-tokenizer experiment has now been replaced by a direct comparison
using **real production tokenizers** and a substantially stronger evaluation
corpus: **200 real, aligned FLORES-200 dev sentences per language** (not
UDHR), tokenized with real `gpt2` and real `xlm-roberta-base`.

The comparison uses **tok/sentence ratio vs English**, where each sentence
is a translation-equivalent content unit across languages. This avoids the
problems identified with word, grapheme, and byte denominators: the
denominator represents the same underlying content rather than a
language-specific orthographic or segmentation convention.

### Real-tokenizer results

| lang | GPT-2 | XLM-RoBERTa-base |
|---|---:|---:|
| hin | 7.27× | 1.27× |
| kan | 13.24× | 1.37× |
| tam | 14.95× | 1.34× |
| tel | 12.56× | 1.33× |
| mal | 14.49× | 1.37× |
| ben | 9.52× | 1.36× |
| mar | 7.72× | 1.26× |

The XLM-R range is only **1.26×–1.37×**, a spread of **0.11×**, across six
typologically distinct Indic languages. This is remarkably tight compared
with GPT-2, where the ratios range from **7.27× to 14.95×**.

The result also independently matches another run using a different corpus
very closely: for example, the other run found approximately **1.22× for
Hindi, 1.30× for Malayalam, and 1.35× for Tamil** under XLM-R. Two
independent runs, using different corpora, converging on essentially the
same result provides additional evidence that the effect is not an artifact
of one particular dataset.

For context, the earlier A2 debugging exercise showed that the code fixes
themselves have only a modest effect on the real GPT-2 result:

| variant | eng_fert | hin_fert | ratio | Δ from baseline |
|---|---:|---:|---:|---:|
| baseline | 1.265 | 7.448 | 5.887 | — |
| `--fix-split` | 1.283 | 7.598 | 5.922 | +0.6% |
| `--fix-lower` | 1.229 | 7.448 | 6.059 | +2.9% (wrong direction from our original claim) |
| `--fix-chars` (tpc only) | — | — | tpc: 1.579→2.450 | +55% on tok/char specifically |
| `--micro-average` | 1.253 | 7.403 | 5.908 | +0.4% |
| `--all` | 1.247 | 7.598 | 6.092 | +3.5% |

Thus, under real GPT-2, correcting the analysis code changes the headline
English/Hindi ratio from **5.887× to 6.092×**, only **+3.5%** overall. The
much larger effect comes from **which tokenizer is used**, not from the
implementation details of the fertility calculation.

## Finding 1 — tokenizer choice, not script, determines the cross-language gap

The original claim that "it's the script, not the tokenizer" does not survive
the real-tokenizer experiment.

The same underlying content, in the same language and script, behaves very
differently depending on the tokenizer. Across the six Indic languages,
GPT-2 produces tok/sentence ratios of **7.27×–14.95×** relative to English,
while XLM-RoBERTa-base produces ratios of only **1.26×–1.37×**.

That means the apparent Indic penalty changes by roughly **5–11× depending
on tokenizer choice alone**, with no change to the underlying language,
script, or content.

The contrast is especially striking for the same language:

- Hindi: **7.27× → 1.27×**
- Kannada: **13.24× → 1.37×**
- Tamil: **14.95× → 1.34×**
- Telugu: **12.56× → 1.33×**
- Malayalam: **14.49× → 1.37×**
- Bengali: **9.52× → 1.36×**
- Marathi: **7.72× → 1.26×**

This is not a small correction to a script-dependent effect. The tokenizer
choice fundamentally changes the measured cost of representing the same
language.

The mechanism is straightforward: tokenizers allocate their vocabulary and
merge rules according to the text they were trained on. A tokenizer whose
training data is overwhelmingly English-heavy can have poor coverage of
Indic-script byte sequences, causing Indic text to fragment into many more
tokens. A multilingual tokenizer trained to represent many scripts has
vocabulary coverage and merge rules that are much better suited to those
languages.

The A2 result reinforces this interpretation. On the original real GPT-2
corpus, fixing the analysis code moved the Hindi/English ratio from
**5.887× to 6.092×**, just a **3.5%** change. In contrast, replacing GPT-2
with XLM-R on the larger FLORES-200 evaluation produces an enormous
reduction in the Indic/English gap.

So the important variable is not simply "Latin vs. Indic script." It is the
interaction between the language and the tokenizer's learned vocabulary.

**Finding 1 confirmed, more strongly:** the same content, same script, under
two real production tokenizers, swings from **7.27×–14.95× under GPT-2** to
**1.26×–1.37× under XLM-RoBERTa-base** — a **5–11× change from tokenizer
choice alone**, with zero change to the underlying language or content.

## Finding 2 — tokens per equivalent content unit is the right metric

The denominator should represent the thing an actual serving-cost decision
cares about: **the amount of equivalent content being processed**.

That is why **tok/sentence** is the most useful metric for this comparison.
The FLORES-200 sentences are aligned translations, so a sentence in Hindi,
Kannada, Tamil, Telugu, Malayalam, Bengali, or Marathi represents roughly
the same underlying content as its English counterpart.

By contrast, the other denominators introduce language-specific effects:

- **tok/word** does not hold the amount of linguistic content constant.
  Languages differ in morphology and word-segmentation conventions, so a
  language that packs more morphology into each whitespace-delimited word
  can appear artificially expensive.
- **tok/grapheme** does not necessarily represent the same linguistic
  information across scripts. A single grapheme cluster in an Indic writing
  system can encode substantially more phonological or orthographic
  information than a Latin letter.
- **tok/byte** measures UTF-8 representation rather than linguistic content.
  Indic characters generally occupy multiple UTF-8 bytes, so this denominator
  can make Indic text look artificially efficient even when it requires far
  more model tokens. It therefore measures an encoding property rather than
  the serving cost we care about.
- **tok/sentence**, when the sentences are genuinely translation-aligned,
  holds the underlying content approximately constant. It therefore gives
  the closest measurement of how many model tokens are required to process
  equivalent information in different languages.

The real FLORES-200 result makes this argument substantially stronger than
the earlier toy experiment. Under XLM-RoBERTa-base, all six Indic languages
fall into an extremely narrow **0.11-wide band: 1.26×–1.37× English**,
despite substantial typological differences between them.

That tightness is important. The languages include both **Indo-Aryan**
(Bengali, Hindi, Marathi) and **Dravidian** languages (Kannada, Malayalam,
Tamil, Telugu). Their morphology, phonology, and writing systems differ
considerably, yet their token/sentence ratios under a genuinely
multilingual tokenizer are remarkably similar.

**Finding 2 confirmed, more strongly:** under XLM-RoBERTa-base, all six
Indic languages cluster inside a **0.11-wide band (1.26×–1.37×)** despite
being typologically very different (Indo-Aryan vs. Dravidian). That
tightness — now on real data, not a toy tokenizer — is strong evidence that
tok/sentence is capturing something real about tokenizer vocabulary
coverage, rather than an artifact of any one language's word-segmentation
convention.

The practical conclusion is therefore:

> **For routing and token-cost analysis, use tokens per unit of
> translation-equivalent content whenever possible.**

In this experiment, tok/sentence is the appropriate proxy because FLORES-200
provides aligned translations. In production, the ideal benchmark would
similarly compare translation-equivalent or intent-equivalent requests
across languages. Where such alignment is unavailable, a proxy could be
constructed from real logs by identifying the same user intent across
languages and comparing the resulting token counts.

This limitation should still be stated explicitly: **tok/sentence only works
as a controlled denominator because the benchmark provides genuinely
parallel content.** Production traffic will not consist of identical
requests expressed in every language. A production analysis would therefore
need either (a) a translation-equivalent benchmark set designed for this
purpose, or (b) a proxy such as tokens per resolved user intent measured
from real multilingual traffic.

## New observation — GPT-2 is substantially worse on Dravidian languages

The real FLORES-200 data reveals an additional pattern that was not visible
as clearly in the earlier analysis.

GPT-2 is roughly **2× worse on the Dravidian languages** than on Hindi:

- Hindi: **7.27×**
- Kannada: **13.24×**
- Tamil: **14.95×**
- Telugu: **12.56×**
- Malayalam: **14.49×**

By comparison, the three Indo-Aryan languages are:

- Hindi: **7.27×**
- Bengali: **9.52×**
- Marathi: **7.72×**

The exact historical composition of GPT-2's training corpus does not by
itself establish precisely why this happens, so the strongest defensible
interpretation is that GPT-2's learned vocabulary provides substantially
poorer coverage for the Dravidian-script data represented here than for
Devanagari and Bengali.

In other words, the real tokenizer results suggest that the English-heavy
tokenizer did not merely underrepresent "Indic languages" uniformly. Its
coverage appears to vary substantially **within the Indic family**, with
Dravidian languages suffering the largest fragmentation.

That makes the tokenizer-allocation explanation even more compelling:
if the effect were fundamentally a fixed property of "Indic scripts," we
would not expect such large differences among Indic languages, nor would we
expect all six to collapse into such a narrow range under XLM-RoBERTa.

## Overall conclusion

The corrected evidence points to a much cleaner conclusion than the
original report.

The A2 code corrections matter, but they are not the main story. On real
GPT-2, the complete set of corrections changes the original Hindi/English
ratio from **5.887× to 6.092×**, only **3.5%**.

The major effect appears when the tokenizer itself changes.

On **200 aligned FLORES-200 dev sentences**, real GPT-2 produces Indic
token/sentence ratios ranging from **7.27× to 14.95×** relative to English.
Real XLM-RoBERTa-base reduces those same ratios to **1.26×–1.37×**.

Thus:

1. **Tokenizer choice dominates the cross-language tokenization penalty.**
2. **The script alone cannot explain the observed gap.**
3. **tok/sentence is the most meaningful denominator when content is
   genuinely parallel.**
4. **A multilingual tokenizer dramatically reduces the Indic token-cost
   penalty seen with English-centric GPT-2.**
5. **The effect is not uniform across Indic languages under GPT-2: Dravidian
   languages are substantially more fragmented.**
6. **The extremely tight XLM-R range across six typologically diverse
   languages provides strong evidence that the result reflects tokenizer
   vocabulary coverage rather than merely word-segmentation conventions.**

The strongest one-sentence summary is:

> **Under real GPT-2, the apparent Indic token-cost penalty varies enormously
> by language; under real XLM-RoBERTa-base, six very different Indic
> languages converge to roughly 1.3× English — showing that the dominant
> variable is tokenizer vocabulary coverage, not an inherent property of the
> scripts themselves.**
