"""
build_flores_corpus.py -- extracts a real, aligned FLORES-200 dev-split
corpus for our 8 target languages from openlanguagedata/flores_plus.

Alignment: every language config shares the same `id` field for the same
underlying sentence -- that's the join key. dev split has 997 sentences
total; we take a slice of them (not random -- a contiguous slice keeps it
simple and fully reproducible without needing to fix a random seed).
"""
import os
from datasets import load_dataset

LANGS = {
    "eng": "eng_Latn",
    "hin": "hin_Deva",
    "kan": "kan_Knda",
    "tam": "tam_Taml",
    "tel": "tel_Telu",
    "mal": "mal_Mlym",
    "ben": "ben_Beng",
    "mar": "mar_Deva",
}

N_SENTENCES = 200  # out of 997 available in dev split
OUT_DIR = "partA/corpus_v2"
os.makedirs(OUT_DIR, exist_ok=True)

datasets = {}
for code, config in LANGS.items():
    print(f"Loading {config} ...")
    ds = load_dataset("openlanguagedata/flores_plus", config, split="dev")
    # index by id for alignment
    datasets[code] = {row["id"]: row["text"] for row in ds}

# use the first N_SENTENCES ids present in ALL languages (should be all 997,
# but check explicitly rather than assume)
common_ids = set(datasets["eng"].keys())
for code in LANGS:
    common_ids &= set(datasets[code].keys())
common_ids = sorted(common_ids)[:N_SENTENCES]

print(f"\nUsing {len(common_ids)} sentences present in all {len(LANGS)} languages "
      f"(out of {len(datasets['eng'])} total in dev split).")

for code in LANGS:
    lines = [datasets[code][i].strip().replace("\n", " ") for i in common_ids]
    out_path = f"{OUT_DIR}/{code}_flores.txt"
    with open(out_path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")
    print(f"  {code}: wrote {len(lines)} lines -> {out_path}")

# save the id list so the split is fully reproducible/auditable later
with open(f"{OUT_DIR}/sentence_ids_used.txt", "w") as f:
    f.write("\n".join(str(i) for i in common_ids) + "\n")
print(f"\nSaved sentence IDs used to {OUT_DIR}/sentence_ids_used.txt")