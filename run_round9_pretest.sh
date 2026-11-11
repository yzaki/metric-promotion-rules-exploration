#!/usr/bin/env bash
. "$(dirname "$0")/run_lib.sh"   # strict mode (set -euo pipefail) and waitall
# Round 9: annual model-free pre-tests for every move type (incl. gap returns) in Russia and India.
cd "$(dirname "$0")"
P=${PYTHON:-python}; export PYTHONIOENCODING=utf-8
mkdir -p logs/latest
one() {
  F=$1; C=$2; export CT_FIELD_ID=$F
  R=results; [ $F != 31 ] && R=results_field$F
  $P -u first_entry.py --treated $C --out ${R}_world_$C --timing > logs/latest/r9_pretest_${C}_$F.txt 2>&1
  echo "$(date) $C $F done" >> logs/latest/r9_progress.txt
}
for C in RU IN; do for F in 31 22 13 16; do one $F $C & done; waitall; done
