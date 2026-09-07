# A1 — Eval corpus documentation

## Source

**Primary subset — UDHR (formal/legal register), 8 languages:**
Universal Declaration of Human Rights, official UN translations, mirrored as
XML at `github.com/unicode-org/udhr` (pulled via `codeload.github.com`
tarball — see "why not FLORES-200" below). Languages pulled: English,
Hindi, Kannada, Tamil, Telugu, Malayalam (the 4 required — English, Hindi,
2 Dravidian), plus Bengali and Marathi as a bonus 2 languages for a bit
more typological range (Indo-Aryan siblings of Hindi).

**Secondary subset — casual/conversational register, 2 languages:**
the `eng_sample.txt` / `hin_sample.txt` given in the starter kit (10 short
everyday sentences each, English + Hindi only). Kept as a separate labeled
slice, not merged into the UDHR numbers, so we can sanity-check whether a
fertility gap measured on formal UN legal prose also shows up in ordinary
conversational text.

## Why not FLORES-200 directly

FLORES-200 is the right dataset for this (1012 dev sentences/language,
genuinely parallel, standard benchmark). But its actual data lives behind
`dl.fbaipublicfiles.com` or the HuggingFace Hub — neither is reachable from
this sandbox's network allowlist (only `github.com`/`raw.githubusercontent.com`/
`codeload.github.com` and a few package registries are open). UDHR is the
best *real, parallel, professionally-translated* corpus I could reach that
covers exactly these languages. It's also a long-standing corpus in
typological NLP work for exactly this kind of cross-language tokenizer
comparison, so it's a reasonable substitute — not an ideal one. **If you
run this on a machine with normal internet access, swap in FLORES-200 dev
(`facebookresearch/flores`) — same pipeline, just point `--corpus` at the
FLORES files instead of `partA/corpus_v1/*_udhr.txt`.**

## Size

| subset | languages | units/lang | alignment | total chars (eng) |
|---|---|---|---|---|
| UDHR | eng, hin, kan, tam, tel, mal, ben, mar | 30 | article-level | 8,247 |
| casual | eng, hin | 10 | line-level | ~450 |

**Alignment unit for UDHR = article, not paragraph or sentence.** All 30
articles are present in every translation, but the number of `<para>`
elements per article differs slightly across languages (some translators
split a sentence differently — e.g. hin has 62 total paragraphs across the
document vs. eng's 60, kan's 58, mal's 51). Aligning at paragraph or
sentence level would silently pair non-corresponding text across languages
in those cases. Article number is the one thing guaranteed stable, so each
article's full text is concatenated into a single "line" per language.
This trades granularity (30 units, not ~120+) for correctness of alignment.

## Domain

UDHR is formal, legalistic, declarative prose — third-person, abstract
nouns ("dignity", "inalienable rights"), long compound sentences. It is
**not** representative of real product traffic (chat turns, search
queries, casual assistant replies), which is exactly the kind of text a
serving-cost decision should be measured on. The casual subset is a small
corrective, but only exists for English/Hindi.

## Preprocessing

1. Extracted `<para>` text within each `<article number="N">` block, per
   language XML file.
2. HTML-unescaped entities, stripped remaining tags, collapsed whitespace.
3. NFC-normalized (matches what `fertility.py` already does — kept
   consistent).
4. Concatenated all paragraphs within an article into one line, one
   article per line, 30 lines per language file.
5. Casual subset copied verbatim from the starter kit (no changes) —
   including its double-space artifact on line 7/10, which we already
   isolated as a code bug in A2 rather than "fixing" here, so the A2
   evidence stays reproducible against the original file.

## What this corpus cannot tell you (caveats)

- **n=30 (or n=10) is small.** These are point estimates, not
  distributions with real confidence intervals. A single unusually long or
  short article/sentence can move the mean noticeably — this is the same
  fragility A2 already flagged in `fertility.py`'s macro-averaging.
- **Single domain, single register, translated *from* English (for most
  of these languages).** UN legal-declaration prose has long sentences,
  formal vocabulary and syntax that is not representative of casual
  assistant traffic, code-mixed text, or short queries — real product
  traffic. Whatever fertility numbers we get are ceiling/formal-register
  numbers, not necessarily what serving actually sees.
- **UDHR translations are 1948-era, revised over decades by different
  translator teams per language** — style/formality is not perfectly
  matched across languages the way a single modern translation agency's
  parallel corpus (like FLORES) would be.
- **Article-level alignment loses sentence-internal granularity** — we
  can't isolate which specific sentence within a multi-sentence article
  drives a fertility difference.
- Bottom line: treat every number in A3 as "directionally indicative on
  formal UN prose, small sample" — not a production-grade estimate. The
  A4 memo says explicitly what to re-measure before trusting this for a
  real routing/capacity decision.
