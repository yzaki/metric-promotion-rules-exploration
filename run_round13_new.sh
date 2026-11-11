#!/usr/bin/env bash
. "$(dirname "$0")/run_lib.sh"   # strict mode (set -euo pipefail) and waitall
# Round 13: any-move / distant / any-return outcomes with timing; estimates on articles whose field did not change;
# balance of the reclassification.
cd "$(dirname "$0")"
P=${PYTHON:-python}; export PYTHONIOENCODING=utf-8; L=logs/r13
one() { F=$1; export CT_FIELD_ID=$F; R=results; [ $F != 31 ] && R=results_field$F
  $P -u first_entry.py --timing > $L/fe_$F.txt 2>&1 || echo "FAILED fe $F" >> $L/progress.txt
  [ $F != 16 ] && { $P -u first_entry.py --stable-only --out ${R}_world_stable --timing > $L/stable_$F.txt 2>&1 || echo "FAILED stable $F" >> $L/progress.txt; }
  echo "$(date '+%F %T') new outcomes $F done" >> $L/progress.txt; }
for F in 31 22 13 16; do one $F & done
$P -u reclass_check.py > $L/reclass.txt 2>&1 || echo "FAILED reclass" >> $L/progress.txt
waitall
echo "$(date '+%F %T') NEW DONE" >> $L/progress.txt
