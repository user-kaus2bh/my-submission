"""
audit_harness.py -- isolates each suspected flaw in fertility.py's analyze()
by toggling ONE change at a time against a fixed tokenizer, so the tokenizer
itself is never a confound. Tokenizer: partA/audit_tokenizer.json, a tiny
case-sensitive byte-level BPE trained only on the two given sample corpora --
used ONLY to hold "some encoder" fixed while we test code-level denominator
bugs. It is NOT used for A3's corrected cross-language analysis.
"""
import unicodedata
from tokenizers import Tokenizer

tok = Tokenizer.from_file("partA/audit_tokenizer.json")
encode = lambda s: tok.encode(s).ids


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
    """Approximate grapheme-cluster count: count codepoints that are NOT
    combining marks (Unicode category Mn/Mc-ish). Good enough to demonstrate
    the direction/magnitude of the codepoint-vs-grapheme gap; not a full
    Unicode UAX#29 implementation."""
    return sum(1 for ch in s if unicodedata.combining(ch) == 0)


def analyze(lines, *, fix_split=False, fix_lower=False, fix_chars=False,
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


def run(label, **kwargs):
    eng = analyze(read_lines("corpus_sample/eng_sample.txt"), **kwargs)
    hin = analyze(read_lines("corpus_sample/hin_sample.txt"), **kwargs)
    ratio = hin[0] / eng[0]
    print(f"{label:38s} eng_fert={eng[0]:.3f}  hin_fert={hin[0]:.3f}  "
          f"eng_tpc={eng[1]:.3f}  hin_tpc={hin[1]:.3f}  hin/eng={ratio:.3f}x")
    return eng, hin, ratio


if __name__ == "__main__":
    import argparse

    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--fix-split", action="store_true",
                     help="Bug 1: use line.split() instead of line.split(' ')")
    ap.add_argument("--fix-lower", action="store_true",
                     help="Bug 2: do not lowercase before tokenizing/splitting")
    ap.add_argument("--fix-chars", action="store_true",
                     help="Bug 3: count grapheme clusters instead of codepoints")
    ap.add_argument("--micro-average", action="store_true",
                     help="Use sum(tokens)/sum(denominator) instead of per-line macro-average")
    ap.add_argument("--all", action="store_true", help="Apply all three fixes")
    args = ap.parse_args()

    if args.all:
        kwargs = dict(fix_split=True, fix_lower=True, fix_chars=True,
                       micro_average=args.micro_average)
        label = "ALL FIXES" + (" + micro-avg" if args.micro_average else "")
    else:
        kwargs = dict(fix_split=args.fix_split, fix_lower=args.fix_lower,
                       fix_chars=args.fix_chars, micro_average=args.micro_average)
        flags_on = [k for k, v in kwargs.items() if v]
        label = "baseline (as shipped)" if not flags_on else "+".join(flags_on)

    run(label, **kwargs)
