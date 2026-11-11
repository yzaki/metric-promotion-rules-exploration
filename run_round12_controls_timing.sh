#!/usr/bin/env bash
. "$(dirname "$0")/run_lib.sh"   # strict mode (set -euo pipefail) and waitall
# Round 12: timing checks (annual pre-test, 2007 placebo) against Spain + Netherlands + Portugal and
# Netherlands + Portugal, for Italy and Russia (first_entry.py --controls --timing).
cd "$(dirname "$0")"
P=${PYTHON:-python}; export PYTHONIOENCODING=utf-8
L=logs/r12; mkdir -p $L
one() { F=$1; export CT_FIELD_ID=$F; R=results; [ $F != 31 ] && R=results_field$F
  $P -u first_entry.py --controls ES NL PT --out ${R}_world_esnlpt --timing > $L/ct_it_esnlpt_$F.txt 2>&1 || echo "FAIL IT ESNLPT $F" >> $L/progress.txt
  $P -u first_entry.py --controls NL PT --out ${R}_world_nlpt --timing > $L/ct_it_nlpt_$F.txt 2>&1 || echo "FAIL IT NLPT $F" >> $L/progress.txt
  $P -u first_entry.py --treated RU --controls ES NL PT --out ${R}_world_RU_esnlpt --timing > $L/ct_ru_esnlpt_$F.txt 2>&1 || echo "FAIL RU ESNLPT $F" >> $L/progress.txt
  echo "$(date '+%F %T') controls timing $F done" >> $L/progress.txt; }
for F in 31 22 13 16; do one $F & done; waitall
