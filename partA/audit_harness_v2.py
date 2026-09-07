"""
audit_harness_v2.py -- A2 bug isolation, now using the REAL tokenizer
(gpt2, or --tokenizer hf:xlm-roberta-base) via fertility_v0_original.py's
own load_tokenizer(), on the ORIGINAL corpus_sample files -- the exact
same corpus and tokenizer REPORT_v0 used. This replaces the toy-tokenizer
version and directly satisfies "measure the effect on the reported
numbers" from the evidence rule.
"""
import sys
import unicodedata
import argparse

sys.path.insert(0, "partA")
from fertility_v0_original import load_tokenizer

import regex


def read_lines(path):
    lines = []
    with open(path, "r", encoding="utf-8") as f:
        for raw in f:
            line = raw.strip()
            if not line:
                continue
            line = unicodedata.normalize("NFC", line)
            lines.append(line)
    return lines


def grapheme_len(s):
    return len(regex.findall(r"\X", s))


def analyze(lines, encode, *, fix_split=False, fix_lower=False, fix_chars=False,
            micro_average=False):
    per_line_fert, per_line_tpc = [], []
    tot_tokens = tot_words = tot_chars = 0
    for raw_line in lines:
        line = raw_line if fix_lower else raw_line.lower()
        tokens = encode(line)
        words = line.split() if fix_split else line.split(" ")
        chars = grapheme_len(line) if fix_chars else len(line)
        per_line_fert.append(len(tokens) / len(words))
        per_line_tpc.append(len(tokens) / chars)
        tot_tokens += len(tokens)
        tot_words += len(words)
        tot_chars += chars
    if micro_average:
        return tot_tokens / tot_words, tot_tokens / tot_chars
    n = len(per_line_fert)
    return sum(per_line_fert) / n, sum(per_line_tpc) / n


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--tokenizer", default="gpt2")
    ap.add_argument("--fix-split", action="store_true")
    ap.add_argument("--fix-lower", action="store_true")
    ap.add_argument("--fix-chars", action="store_true")
    ap.add_argument("--micro-average", action="store_true")
    ap.add_argument("--all", action="store_true")
    args = ap.parse_args()

    encode = load_tokenizer(args.tokenizer)

    kwargs = dict(fix_split=args.fix_split or args.all,
                  fix_lower=args.fix_lower or args.all,
                  fix_chars=args.fix_chars or args.all,
                  micro_average=args.micro_average)

    eng = analyze(read_lines("corpus_sample/eng_sample.txt"), encode, **kwargs)
    hin = analyze(read_lines("corpus_sample/hin_sample.txt"), encode, **kwargs)
    ratio = hin[0] / eng[0]
    print(f"tokenizer={args.tokenizer}  flags={kwargs}")
    print(f"eng_fert={eng[0]:.3f}  hin_fert={hin[0]:.3f}  "
          f"eng_tpc={eng[1]:.3f}  hin_tpc={hin[1]:.3f}  hin/eng={ratio:.3f}x")