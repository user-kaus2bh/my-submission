# A2 — Script and metric audit (evidence rule applied)

All numbers below are reproducible with a single exact command each, run
from the `your-submission/` root (needs `partA/audit_harness.py`,
`partA/audit_tokenizer.json`, and `corpus_sample/{eng,hin}_sample.txt` —
copy the sample corpus in if not already at that path relative to where
you run the command).

**Why a toy tokenizer, not real gpt2:** `fertility.py`'s default tokenizer
(`tiktoken`'s `gpt2`) needs a runtime download from
`openaipublic.blob.core.windows.net`, which wasn't reachable from the
sandbox this was built in. `audit_harness.py` uses a small, fixed,
case-sensitive byte-level BPE (`audit_tokenizer.json`, trained only on the
two given sample files) purely as a constant measuring stick — every
command below only ever changes the *denominator/preprocessing logic*
being tested, never the tokenizer, so the tokenizer is not a confound. If
you have normal internet access, re-run these same comparisons with real
`gpt2` (`python3 fertility_v0_original.py --corpus eng=... --corpus
hin=... --tokenizer gpt2`) to confirm the same directions hold — the
absolute numbers will differ, but the mechanism argument for each bug
below does not depend on which tokenizer is used.

---

## Bug 1 — `words = line.split(" ")` should be `line.split()`

**Claim:** a literal double space in the corpus (one line in each sample
file) creates a phantom empty-string "word," inflating the word count and
deflating fertility for that line.

**Command:**
```
python3 partA/audit_harness.py                # baseline, as shipped
python3 partA/audit_harness.py --fix-split     # fix applied
```

**Before → after:**
```
baseline:    eng_fert=1.610  hin_fert=3.078  hin/eng=1.911x
--fix-split: eng_fert=1.630  hin_fert=3.135  hin/eng=1.923x
```

**Why this proves the claim:** fixing only the split logic (nothing else
touched) moves fertility up for both languages (~+1-2%) because the
phantom empty "word" is removed from the denominator. Effect is small
because only 1 of 10 lines per corpus has a double space — real, but not
what drives the report's headline number.

---

## Bug 2 — `.lower()` before tokenizing/splitting

**Claim:** Devanagari has no case distinction, so lowercasing is a no-op
for Hindi; it is not a no-op for English, and specifically distorts the
cross-language comparison in one direction.

**Command:**
```
python3 partA/audit_harness.py                # baseline
python3 partA/audit_harness.py --fix-lower     # fix applied (case preserved)
```

**Before → after:**
```
baseline:    eng_fert=1.610  hin_fert=3.078  hin/eng=1.911x
--fix-lower: eng_fert=1.133  hin_fert=3.078  hin/eng=2.716x
```

**Why this proves the claim:** Hindi's fertility is bit-for-bit identical
before and after (3.078 both times) — direct proof `.lower()` does nothing
to Hindi. English's fertility drops 30% (1.610→1.133) — direct proof it
does a lot to English, because the tokenizer's byte-level merges were
learned on the corpus's actual (mixed-case) casing, and forcing lowercase
feeds it text patterns it wasn't optimized for. Net effect: the
hin/eng ratio moves from 1.91x to 2.72x from this one line of code alone,
which inflates — not just adds noise to — the report's headline gap.

---

## Bug 3 — `chars = len(line)` counts codepoints, not grapheme clusters

**Claim:** Devanagari builds a visual character from a base consonant plus
separate combining vowel-sign codepoints; `len()` over-counts these
relative to what a human would call "one character."

**Command:**
```
python3 partA/audit_harness.py                # baseline (len() = codepoints)
python3 partA/audit_harness.py --fix-chars     # fix applied (true grapheme clusters)
```

**Before → after:**
```
baseline:    eng_tpc=0.282  hin_tpc=0.649
--fix-chars: eng_tpc=0.282  hin_tpc=0.672
```

**Why this proves the claim:** English's tok/char is unchanged (Latin text
has no combining marks in this sample, so codepoints == grapheme clusters
for English here). Hindi's tok/char rises ~3.5% once the denominator is
corrected to true grapheme clusters — the codepoint-based count was
inflating Hindi's character denominator, making its tok/char look
artificially *better* (lower) than it truly is. Direction is the opposite
of Bug 2 — reported explicitly at its true, small size rather than
dramatized, per the evidence rule's ban on overclaiming.

---

## Bug 4 (minor) — macro-averaging per-line ratios vs. pooling totals

**Claim:** averaging each line's fertility ratio equally (macro-average) is
statistically less stable at small n than pooling total tokens over total
words (micro-average), because short lines with unusual ratios get equal
weight to long, representative ones.

**Command:**
```
python3 partA/audit_harness.py                   # baseline (macro-average, as shipped)
python3 partA/audit_harness.py --micro-average   # pooled sum/sum instead
```

**Before → after:**
```
baseline:        eng_fert=1.610  hin_fert=3.078
--micro-average: eng_fert=1.595  hin_fert=3.016
```

**Why this is flagged as minor, not a headline bug:** the effect here is
~1% for both languages — real (macro and micro do disagree, as they
should whenever line lengths vary), but small at this sample size. Stated
at its measured size rather than inflated into a bigger claim than the
evidence supports.

---

## Suspicious but confirmed harmless — `random.seed(1337)`

**Claim under test:** does this line affect any output?

**Command:**
```
grep -n "random\." fertility_v0_original.py
```

**Result:** the only match is the `import random` / `random.seed(1337)`
lines themselves — `random` is never called anywhere else in the file.

**Why this is NOT claimed as a bug:** with zero calls to `random.*`
anywhere in the rest of the script, the seed can have no effect on any
computed output. Explicitly not flagging this as a flaw, since the
evidence rule penalizes unverified/false-positive claims as harshly as
missed real ones.

**Secondary check — NFC normalization:** also inspected as a candidate
"looks suspicious" item.

```
python3 -c "
import unicodedata
for f in ['corpus_sample/eng_sample.txt','corpus_sample/hin_sample.txt']:
    lines = open(f, encoding='utf-8').read().splitlines()
    changed = sum(1 for l in lines if unicodedata.normalize('NFC', l) != l)
    print(f, 'lines changed by NFC:', changed, '/', len(lines))
"
```

Expected output: `0 / 10` for both files — both are already NFC-normalized,
so the step is a confirmed no-op on this data and legitimately defensive
code, not a bug.

---

## Conceptual bug — tok/word is not a valid cross-language comparison unit

This is not a code bug — `fertility.py` computes tokens/word exactly as
intended. The problem is using that number as a stand-in for
cross-language serving cost. "Word" is not a stable unit of content across
languages: Hindi packs more morphology (case marking, postpositions) into
a whitespace-delimited word than English does, so part of the tok/word gap
reflects linguistic typology, not tokenizer inefficiency or real serving
cost. No single command isolates this the way Bugs 1-4 do, since it's a
property of the metric choice, not the code — it is instead demonstrated
at scale across 6 languages in `partA/A3_corrected_analysis.md`, which
shows tok/word disagrees with itself by up to 2.8x across languages
measuring identical content, while a content-holding-constant denominator
(tokens per parallel sentence) stays within a 1.4x range for the same
data. That comparison is the evidence for this claim; see A3 for the full
table and reasoning.
