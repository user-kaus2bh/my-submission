"""
build_corpus.py -- extracts the 30 UDHR articles (title + all <para> text
concatenated per article) for each target language, from the raw XML
mirrored from unicode-org/udhr (github.com/unicode-org/udhr).

Alignment unit = ARTICLE, not paragraph. Paragraph counts differ slightly
across translations (e.g. some translators split a clause into an extra
sentence), so paragraph-level "line N" alignment would silently misalign
content across languages. Article number is stable across all 30 articles
in every official UN translation, so it's the safe join key.
"""
import re
import html
import unicodedata

LANGS = {
    "eng": "English",
    "hin": "Hindi",
    "kan": "Kannada",
    "tam": "Tamil",
    "tel": "Telugu",
    "mal": "Malayalam",
    "ben": "Bengali",
    "mar": "Marathi",
}

SRC_DIR = "udhr-main/data/udhr"
OUT_DIR = "partA/corpus_v1"

import os
os.makedirs(OUT_DIR, exist_ok=True)

tag_re = re.compile(r"<[^>]+>")
ws_re = re.compile(r"\s+")

def clean(text):
    text = html.unescape(text)
    text = tag_re.sub(" ", text)
    text = ws_re.sub(" ", text).strip()
    text = unicodedata.normalize("NFC", text)
    return text

summary = []
for code, name in LANGS.items():
    path = f"{SRC_DIR}/udhr_{code}.xml"
    data = open(path, encoding="utf-8").read()
    articles = re.findall(r'<article number="(\d+)"[^>]*>(.*?)</article>', data, re.S)
    articles.sort(key=lambda x: int(x[0]))
    assert len(articles) == 30, f"{code}: expected 30 articles, got {len(articles)}"
    lines = []
    for num, body in articles:
        # drop the <title>Article N</title> line, keep only <para> content
        paras = re.findall(r"<para>(.*?)</para>", body, re.S)
        joined = " ".join(clean(p) for p in paras)
        lines.append(joined)
    out_path = f"{OUT_DIR}/{code}_udhr.txt"
    with open(out_path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")
    n_chars = sum(len(l) for l in lines)
    summary.append((code, name, len(lines), n_chars))

print(f"{'code':6}{'lang':10}{'#articles':10}{'total chars':12}")
for code, name, n, ch in summary:
    print(f"{code:6}{name:10}{n:<10}{ch:<12}")
