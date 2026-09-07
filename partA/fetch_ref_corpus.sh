#!/bin/bash
# Re-fetches the English reference corpus used to train tok_A (web-english).
# Not committed to the repo (6.5MB, easily re-downloaded).
curl -s "https://raw.githubusercontent.com/dscape/spell/master/test/resources/big.txt" \
  -o "$(dirname "$0")/ref_corpus_big_en.txt"
echo "Saved to $(dirname "$0")/ref_corpus_big_en.txt"
