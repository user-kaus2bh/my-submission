"""
corrected_analysis_v2.py -- A3 rebuilt with REAL tokenizers (gpt2 via
tiktoken, xlm-roberta-base via transformers) on the REAL FLORES-200
corpus (partA/corpus_v2/*_flores.txt, 200 aligned sentences x 8 languages).

Replaces the toy self-trained-tokenizer version used when HuggingFace
Hub / tiktoken's blob storage weren't reachable.

Denominators: tok/word, tok/grapheme (regex \\X), tok/byte, tok/sentence
(tokens per aligned parallel sentence -- holds content constant).
"""
import sys
import unicodedata
import regex

sys.path.insert(0, "partA")
from fertility_v0_original import load_tokenizer

LANGS = ["eng", "hin", "kan", "tam", "tel", "mal", "ben", "mar"]
CORPUS_DIR = "partA/corpus_v2"


def read_lines(path):
    lines = []
    for raw in open(path, encoding="utf-8"):
        line = raw.strip()
        if line:
            lines.append(unicodedata.normalize("NFC", line))
    return lines


def grapheme_count(s):
    return len(regex.findall(r"\X", s))


def measure(lines, encode):
    tot_tok = tot_words = tot_graphs = tot_bytes = 0
    for line in lines:
        ids = encode(line)
        tot_tok += len(ids)
        tot_words += len(line.split())
        tot_graphs += grapheme_count(line)
        tot_bytes += len(line.encode("utf-8"))
    n = len(lines)
    return {
        "tok/word": tot_tok / tot_words,
        "tok/grapheme": tot_tok / tot_graphs,
        "tok/byte": tot_tok / tot_bytes,
        "tok/sentence": tot_tok / n,
    }


if __name__ == "__main__":
    tokenizers = {
        "gpt2": load_tokenizer("gpt2"),
        "xlm-roberta-base": load_tokenizer("hf:xlm-roberta-base"),
    }

    results = {}
    for tname, encode in tokenizers.items():
        print(f"\n=== {tname} ===")
        print(f"{'lang':6}{'tok/word':>10}{'tok/graph':>11}{'tok/byte':>10}{'tok/sent':>10}")
        for lang in LANGS:
            lines = read_lines(f"{CORPUS_DIR}/{lang}_flores.txt")
            m = measure(lines, encode)
            results[(lang, tname)] = m
            print(f"{lang:6}{m['tok/word']:>10.3f}{m['tok/grapheme']:>11.4f}"
                  f"{m['tok/byte']:>10.4f}{m['tok/sentence']:>10.2f}")

    print(f"\n{'lang':6}{'tok/word ratio':>16}{'tok/sentence ratio':>20}"
          f"{'tok/byte ratio':>16}{'tok/grapheme ratio':>20}   (vs eng, xlm-roberta-base)")
    eng = results[("eng", "xlm-roberta-base")]
    for lang in LANGS:
        r = results[(lang, "xlm-roberta-base")]
        print(f"{lang:6}{r['tok/word']/eng['tok/word']:>16.2f}"
              f"{r['tok/sentence']/eng['tok/sentence']:>20.2f}"
              f"{r['tok/byte']/eng['tok/byte']:>16.2f}"
              f"{r['tok/grapheme']/eng['tok/grapheme']:>20.2f}")

    print(f"\n{'lang':6}{'tok/word ratio':>16}{'tok/sentence ratio':>20}   (vs eng, gpt2)")
    eng2 = results[("eng", "gpt2")]
    for lang in LANGS:
        r = results[(lang, "gpt2")]
        print(f"{lang:6}{r['tok/word']/eng2['tok/word']:>16.2f}"
              f"{r['tok/sentence']/eng2['tok/sentence']:>20.2f}")