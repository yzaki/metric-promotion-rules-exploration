#!/usr/bin/env bash
# Output-controlled check of the below-bar contrast (Table S40) with output in the destination year (the next active
# year, one or two years after the decision) instead of the calendar year after it. Needs the staff-register match
# (results*_world_career/rank_2011_match.csv; not distributed).
. "$(dirname "$0")/run_lib.sh"
cd "$(dirname "$0")"
P=${PYTHON:-python}; export PYTHONIOENCODING=utf-8
L=logs/audit; mkdir -p $L
for F in 31 22 13 16; do
  export CT_FIELD_ID=$F; D=data; R=results; [ $F != 31 ] && D=data_field$F && R=results_field$F
  $P -u sector_thresholds.py --input $D/trajectories_world_career.csv --out ${R}_world_career --output-check-only > $L/sector_out_$F.txt 2>&1
  echo "$(date '+%H:%M:%S') field $F done"
done
