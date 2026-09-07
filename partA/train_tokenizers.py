"""
train_tokenizers.py

Splits the UDHR corpus per language into a TRAIN slice (articles 1-20) and
an EVAL slice (articles 21-30), so the multilingual tokenizer is never
trained on the same text we measure fertility on (avoiding leakage that
would make the comparison meaningless).

Trains two byte-level BPE tokenizers, same algorithm, same vocab budget,
different training data -- this isolates "what the tokenizer was trained
on" as the variable, which is the whole point of the A2 conceptual finding:

  tok_A ("web-english"): trained ONLY on English text (Norvig's big.txt,
      ~6.5MB of natural mixed-case English prose) -- a proxy for a
      GPT-2-style tokenizer trained on English-dominated web text.

  tok_B ("multilingual-indic"): trained on the TRAIN slice of all 8 UDHR
      languages combined -- a proxy for an Indic-aware multilingual
      tokenizer (like MuRIL/IndicBERT) that explicitly allocates vocab
      budget to Indic scripts.

Caveat (stated once here, repeated in A3 write-up): tok_B's training data
is tiny (~160 short lines across 8 languages) compared to a real production
tokenizer trained on billions of tokens. Absolute vocab sizes and fertility
numbers here are toy-scale. The MECHANISM and DIRECTION of the effect
(vocab budget allocation changes fertility) is what generalizes; the exact
magnitudes should not be quoted as production numbers.
"""
import os
from tokenizers import Tokenizer, models, trainers, pre_tokenizers, decoders

LANGS = ["eng", "hin", "kan", "tam", "tel", "mal", "ben", "mar"]
SRC = "partA/corpus_v1"
SPLIT_DIR = "partA/corpus_split"
os.makedirs(SPLIT_DIR, exist_ok=True)

TRAIN_N = 20  # articles 1-20 (index 0-19) for training
# remaining articles 21-30 (index 20-29) reserved for EVAL, untouched by training

for lang in LANGS:
    lines = open(f"{SRC}/{lang}_udhr.txt", encoding="utf-8").read().splitlines()
    assert len(lines) == 30
    train_lines, eval_lines = lines[:TRAIN_N], lines[TRAIN_N:]
    open(f"{SPLIT_DIR}/{lang}_train.txt", "w", encoding="utf-8").write("\n".join(train_lines) + "\n")
    open(f"{SPLIT_DIR}/{lang}_eval.txt", "w", encoding="utf-8").write("\n".join(eval_lines) + "\n")

print(f"Split into {TRAIN_N} train / {30-TRAIN_N} eval articles per language, for {len(LANGS)} languages.")

VOCAB_BUDGET = 8000


def train_bpe(files, out_path, vocab_size):
    tok = Tokenizer(models.BPE(unk_token="[UNK]"))
    tok.pre_tokenizer = pre_tokenizers.ByteLevel(add_prefix_space=False)
    tok.decoder = decoders.ByteLevel()
    trainer = trainers.BpeTrainer(vocab_size=vocab_size, special_tokens=["[UNK]"], show_progress=False)
    tok.train(files, trainer)
    tok.save(out_path)
    return tok.get_vocab_size()


# tok_A: English-only, large natural corpus
size_a = train_bpe(["partA/ref_corpus_big_en.txt"], "partA/tok_A_web_english.json", VOCAB_BUDGET)

# tok_B: multilingual, TRAIN slice only, all 8 languages
train_files = [f"{SPLIT_DIR}/{lang}_train.txt" for lang in LANGS]
size_b = train_bpe(train_files, "partA/tok_B_multilingual_indic.json", VOCAB_BUDGET)

print(f"tok_A (web-english) actual vocab size: {size_a}  (budget {VOCAB_BUDGET})")
print(f"tok_B (multilingual-indic) actual vocab size: {size_b}  (budget {VOCAB_BUDGET})")
