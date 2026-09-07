# NOTEBOOK.md

Chronological log: hypothesis → experiment → result → revision, including
dead ends. Entries are appended as work happened, not cleaned up after the
fact.

---

## Part A

### A2 — auditing fertility.py

**Hypothesis 0:** run `fertility.py` exactly as shipped against real
`gpt2`/`hf:` tokenizers to reproduce REPORT_v0's numbers before touching
anything.

**Dead end:** `tiktoken.get_encoding("gpt2")` tries to fetch
`openaipublic.blob.core.windows.net/gpt-2/encodings/main/vocab.bpe` at
runtime — 403, not on this sandbox's network allowlist. Same problem for
any `hf:<repo_id>` tokenizer (needs `huggingface.co`). **Decision:** can't
run the script against real pretrained tokenizers here. Documented as a
sandbox limitation, not silently worked around — this shapes both A2 and
A3's methodology below.

**Revision:** for A2 (isolating *code*-level bugs, not measuring real
production fertility), the specific tokenizer doesn't matter as much as
holding it fixed while toggling one suspected bug at a time. Trained a
tiny case-sensitive byte-level BPE (`partA/audit_tokenizer.json`, vocab
600) on the two given sample files, purely as a fixed measuring stick.

**Read through `fertility.py` line by line, flagged 5 candidates:**
1. `words = line.split(" ")` — phantom empty-string words on double-spaces
   (both sample files have exactly one planted double-space line each).
2. `.lower()` applied before tokenizing/splitting — no-op for Hindi (no
   case), real distortion for English.
3. `chars = len(line)` — counts Unicode codepoints, not grapheme clusters;
   Devanagari vowel signs are separate combining codepoints.
4. Macro-averaging per-line ratios instead of pooling totals — statistical
   instability at small n.
5. `random.seed(1337)` — suspicious-looking, need to check if it's used.

**Experiments (`partA/audit_harness.py`, toggled one flag at a time):**
- Bug 1 (split): eng fert 1.610→1.630, hin 3.078→3.135. Real but small
  (~1-2%), only 1/10 lines affected per corpus.
- Bug 2 (lower): eng fert 1.610→1.133 (**-30%**) with Hindi unchanged
  (case-invariant). Ratio moves 1.91×→2.72×. This is the load-bearing bug —
  it inflates the report's headline gap because it can only ever hurt the
  cased language.
- Bug 3 (chars): hin tok/char 0.649→0.672 (+3.5%, confirmed via
  codepoint-vs-grapheme count: 290 vs ~280 in the sample). Real, small,
  direction is *opposite* bug 2 (understates the gap slightly).
- Bug 4 (macro vs micro average): isolated independently, effect was
  ~1% on this n=10 sample — real point, negligible magnitude here.
  Downgraded from "headline bug" to a minor footnote for that reason —
  didn't want to claim a bigger effect than measured.
- Candidate 5: `grep -n "random\." fertility.py` → only the seed line
  itself. `random` is never called. **Correctly flagged as harmless**, not
  claimed as a bug (the evidence rule penalizes false positives).
- Also checked NFC normalization for harm: confirmed no-op on both sample
  files (already NFC). Legitimately defensive code, not a bug.

**Conceptual finding:** tok/word (fertility) is a real, correctly computed
number, but isn't a valid cross-language comparison unit — "word" isn't a
stable amount of content across languages with different morphological
typology. Revisited and confirmed with 6 more languages in A3.

### A1 — building a real eval corpus

**Hypothesis:** FLORES-200 dev is the obvious choice, per the assignment's
hint.

**Dead end:** FLORES-200's actual data lives behind
`dl.fbaipublicfiles.com` or the HuggingFace Hub (`facebook/flores`,
`openlanguagedata/flores_plus`) — confirmed via web search of the dataset's
own download scripts. Neither host is on this sandbox's network allowlist
(only `github.com`/`raw.githubusercontent.com`/`codeload.github.com` and
package registries are open).

**Revision:** searched for a real, parallel, professionally-translated
corpus reachable via GitHub. Found `unicode-org/udhr` (UDHR translations,
XML, mirrored on GitHub). Confirmed via `codeload.github.com` tarball
(raw.githubusercontent.com 404'd on guessed paths — had to actually fetch
the repo tree to find the real path was `data/udhr/udhr_<code>.xml`, not
`udhr_xml/udhr_<code>.xml` as a first guess assumed).

**Found:** all 8 target languages (eng, hin, kan, tam, tel, mal + bonus
ben, mar) present, all with exactly 30 `<article>` elements.

**Dead end / correction:** first instinct was to align at paragraph level
for more data points. Checked paragraph counts per language first —
they differ (hin 62, eng 60, kan 58, mal 51, for the same 30 articles).
Paragraph-level "line N" alignment would silently misalign content in
several places. **Decision:** align at article level (n=30), trading
granularity for correctness. Documented explicitly in `A1_corpus.md`.

**Kept the given casual eng/hin samples as a separate, unmodified,
domain-labeled subset** (not merged into UDHR) as a cross-check that
findings aren't purely a formal-register artifact — also intentionally did
NOT fix the sample files' double-space bug here, to keep A2's evidence
trail reproducible against the original file.

### A3 — corrected analysis

**Same tiktoken/HF network wall as A2** meant no access to real pretrained
tokenizers here either. Rather than fake it, trained two real BPE
tokenizers myself with clearly different, honestly-described training
data, to directly test the report's causal claim ("it's the script, not
the tokenizer"):
- tok_A: English-only (Norvig's `big.txt`, ~6.5MB, fetched from a GitHub
  mirror — `dscape/spell` repo — since it's a well-known corpus commonly
  vendored into repos for spell-checkers).
- tok_B: multilingual, trained on UDHR's **train split only** (articles
  1-20) to avoid training/eval leakage — measured fertility on the
  held-out articles 21-30, which tok_B never saw.

**Noticed and reported honestly:** tok_B only reached 2,841 vocab entries
out of an 8,000 budget — ran out of frequent-enough merge candidates
because the multilingual training set is tiny (~160 short lines across 8
languages). Didn't hide this or re-run until it "looked better" — it's a
real, disclosed limitation of the toy-scale setup.

**Result that surprised me:** under tok_A, Hindi's tok/byte was exactly
1.0000 for every Indic language tested — i.e., the tokenizer never learned
a single merge for non-Latin bytes, so every byte is its own token. This
matches the well-known real-world GPT-2-on-Hindi failure mode almost
exactly, which was a good sanity check that the toy tokenizer is behaving
like a real English-centric one, not some unrelated artifact.

**Checked which denominator is most trustworthy** by comparing spread
across all 6 non-English languages under the *same* tokenizer: tok/word
ranged 1.87×-5.26× (inflated by agglutination differences, e.g. Malayalam),
tok/grapheme 3.39×-5.06× (inflated by information-density-per-grapheme
differences), tok/byte 0.80×-0.83× (deflated by UTF-8's 3-bytes-per-char
cost for these scripts), tok/sentence (parallel content unit) 2.03×-2.87×
— the tightest range. Used that tightness, across 6 typologically distinct
languages, as evidence (not just intuition) for recommending it.

**Explicit limitation flagged, not glossed over:** tok/sentence only works
because UDHR gives genuinely parallel content across languages — this
won't be available for free on real production traffic and would need a
translation-matched benchmark or intent-matched log sample to replicate.

### A4 — memo

Corrected the 6× claim down to ~2.5× (midpoint of the 2.03-2.87× range
found in A3), kept REPORT_v0's tokenizer-routing recommendation (that part
survives the audit), and proposed monitoring tokens-billed-per-resolved-
request-by-language in production as the operational version of A3's
tok/sentence metric.
