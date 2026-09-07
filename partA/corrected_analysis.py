"""
corrected_analysis.py -- A3: recompute cross-language tokenization cost
properly. Two tokenizers (tok_A web-english, tok_B multilingual-indic),
four denominators, on the held-out EVAL split (articles 21-30, never seen
during tokenizer training) plus the casual-domain subset as a cross-check.

Denominators:
  words    -- len(line.split())                (fixed: no split(" ") bug)
  graphs   -- true grapheme-cluster count via regex \X (fixed: not codepoints)
  bytes    -- len(line.encode("utf-8"))
  sentence -- 1 per line (article/sentence) -- i.e. tokens-per-parallel-unit,
              which is just mean tokens per line; this is the "hold content
              constant" denominator since every line across languages is a
              translation of the same source content.

All ratios use MICRO-averaging (sum of tokens / sum of denominator across
the whole eval set), not per-line macro-averaging -- per the A2 finding
that macro-averaging is unstable at small n.

No lowercasing anywhere (A2 bug fix carried forward).
"""
import glob
import regex
import unicodedata
from tokenizers import Tokenizer

LANGS = ["eng", "hin", "kan", "tam", "tel", "mal", "ben", "mar"]
SPLIT_DIR = "partA/corpus_split"

tok_A = Tokenizer.from_file("partA/tok_A_web_english.json")
tok_B = Tokenizer.from_file("partA/tok_B_multilingual_indic.json")


def read_lines(path):
    lines = []
    for raw in open(path, encoding="utf-8"):
        line = raw.strip()
        if not line:
            continue
        lines.append(unicodedata.normalize("NFC", line))
    return lines


def grapheme_count(s):
    return len(regex.findall(r"\X", s))


def measure(lines, tok):
    tot_tok = tot_words = tot_graphs = tot_bytes = 0
    for line in lines:
        ids = tok.encode(line).ids
        tot_tok += len(ids)
        tot_words += len(line.split())
        tot_graphs += grapheme_count(line)
        tot_bytes += len(line.encode("utf-8"))
    n_lines = len(lines)
    return {
        "tok/word": tot_tok / tot_words,
        "tok/grapheme": tot_tok / tot_graphs,
        "tok/byte": tot_tok / tot_bytes,
        "tok/sentence": tot_tok / n_lines,
        "n_lines": n_lines,
        "n_tokens": tot_tok,
    }


def run_subset(name, split_dirfmt, langs):
    print(f"\n=== {name} ===")
    header = f"{'lang':6}{'tokzr':14}{'tok/word':>10}{'tok/graph':>11}{'tok/byte':>10}{'tok/sent':>10}"
    print(header)
    print("-" * len(header))
    results = {}
    for lang in langs:
        lines = read_lines(split_dirfmt.format(lang=lang))
        for tname, tok in [("web-english(A)", tok_A), ("multiling(B)", tok_B)]:
            m = measure(lines, tok)
            results[(lang, tname)] = m
            print(f"{lang:6}{tname:14}{m['tok/word']:>10.3f}{m['tok/grapheme']:>11.4f}"
                  f"{m['tok/byte']:>10.4f}{m['tok/sentence']:>10.2f}")
    return results


if __name__ == "__main__":
    res_udhr = run_subset("UDHR eval split (held out, 10 articles/lang, formal register)",
                           f"{SPLIT_DIR}/{{lang}}_eval.txt", LANGS)

    res_casual = run_subset("Casual subset (10 sentences, eng+hin only, cross-check)",
                             "partA/corpus_v1/{lang}_casual.txt", ["eng", "hin"])

    print("\n=== hin/eng ratio by denominator (UDHR eval, tok_B multiling) ===")
    h = res_udhr[("hin", "multiling(B)")]
    e = res_udhr[("eng", "multiling(B)")]
    for key in ["tok/word", "tok/grapheme", "tok/byte", "tok/sentence"]:
        print(f"{key:14s}: hin={h[key]:.4f}  eng={e[key]:.4f}  ratio={h[key]/e[key]:.3f}x")

    print("\n=== Same, but with tok_A (web-english) -- shows tokenizer-choice sensitivity ===")
    h2 = res_udhr[("hin", "web-english(A)")]
    e2 = res_udhr[("eng", "web-english(A)")]
    for key in ["tok/word", "tok/grapheme", "tok/byte", "tok/sentence"]:
        print(f"{key:14s}: hin={h2[key]:.4f}  eng={e2[key]:.4f}  ratio={h2[key]/e2[key]:.3f}x")

    print(f"\n{'lang':6}{'tok/word ratio':>16}{'tok/sentence ratio':>20}{'tok/byte ratio':>16}{'tok/grapheme ratio':>20}")
    eng_b = res_udhr[("eng", "multiling(B)")]
    for lang in LANGS:
        r = res_udhr[(lang, "multiling(B)")]
        print(f"{lang:6}{r['tok/word']/eng_b['tok/word']:>16.2f}{r['tok/sentence']/eng_b['tok/sentence']:>20.2f}"
              f"{r['tok/byte']/eng_b['tok/byte']:>16.2f}{r['tok/grapheme']/eng_b['tok/grapheme']:>20.2f}")
