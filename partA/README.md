# Part A — reproduction order

1. `bash fetch_ref_corpus.sh` — pulls the English reference corpus (not committed, 6.5MB).
2. `python3 build_corpus.py` — extracts corpus_v1/*_udhr.txt from the UDHR XML
   (requires udhr-main/data/udhr/*.xml — see A1_corpus.md for the source repo
   and how it was fetched: `codeload.github.com/unicode-org/udhr/tar.gz/refs/heads/main`).
3. `python3 audit_harness.py` — A2 bug-isolation experiments (uses audit_tokenizer.json, included).
4. `python3 train_tokenizers.py` — A3: splits corpus_v1 into train/eval, trains tok_A and tok_B.
5. `python3 corrected_analysis.py` — A3: runs the 2-tokenizer x 4-denominator analysis.

Read in order: A1_corpus.md -> (A2 findings are in the main conversation /
top-level writeup) -> A3_corrected_analysis.md -> A4_recommendation_memo.md.

`fertility_v0_original.py` and `REPORT_v0_original.md` are the unmodified
files as given, kept here for side-by-side reference during the defense.
