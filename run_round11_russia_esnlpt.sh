#!/usr/bin/env bash
. "$(dirname "$0")/run_lib.sh"   # strict mode (set -euo pipefail) and waitall
# Round 11: Russia vs Spain + Netherlands + Portugal (France and Germany left out), model-free move types.
cd "$(dirname "$0")"
P=${PYTHON:-python}; export PYTHONIOENCODING=utf-8
mkdir -p logs/latest
one() {
  F=$1; export CT_FIELD_ID=$F
  R=results; [ $F != 31 ] && R=results_field$F
  $P -u first_entry.py --treated RU --controls ES NL PT --out ${R}_world_RU_esnlpt > logs/latest/r11_ru_esnlpt_$F.txt 2>&1
  echo "$(date) RU ESNLPT $F done" >> logs/latest/r11_progress.txt
}
for F in 31 22 13 16; do one $F & done; waitall
