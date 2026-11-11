#!/usr/bin/env bash
. "$(dirname "$0")/run_lib.sh"   # strict mode (set -euo pipefail) and waitall
# Round 13: staff-register analyses (Tables S23-S25, Fig. 2B-C) on the latest download, with the 2011 MUR
# register exports supplied by the author (data_meta/staff_register/, areas 01-09, 31/12/2011; not distributed).
cd "$(dirname "$0")"
P=${PYTHON:-python}; export PYTHONIOENCODING=utf-8
L=logs/r13; mkdir -p $L
one() { F=$1; export CT_FIELD_ID=$F; D=data; R=results; [ $F != 31 ] && D=data_field$F && R=results_field$F
  C=$D/trajectories_world_career.csv
  $P -u rank_exposure.py --input $C --out ${R}_world_career --n-boot 100 > $L/rank_$F.txt 2>&1 || { echo "FAILED rank $F" >> $L/progress.txt; return; }
  $P -u register_split.py --input $C --out ${R}_world_career > $L/regsplit_$F.txt 2>&1 || echo "FAILED regsplit $F" >> $L/progress.txt
  $P -u sector_thresholds.py --input $C --out ${R}_world_career --n-boot 100 > $L/sector_$F.txt 2>&1 || echo "FAILED sector $F" >> $L/progress.txt
  $P -u institution_split.py --input $C --out ${R}_world_career --n-boot 100 > $L/inst_$F.txt 2>&1 || echo "FAILED inst $F" >> $L/progress.txt
  echo "$(date '+%F %T') register $F done" >> $L/progress.txt; }
for F in 31 22 13 16; do one $F & done; waitall
$P paper_tables.py > $L/tables.txt 2>&1 && $P paper_figures.py > $L/figures.txt 2>&1 && echo "$(date '+%F %T') ALL DONE" >> $L/progress.txt
