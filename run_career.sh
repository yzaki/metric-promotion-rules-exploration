#!/usr/bin/env bash
. "$(dirname "$0")/run_lib.sh"   # strict mode (set -euo pipefail) and waitall
# Career-stage reanalysis with the true career start (SciSciNet/MAG match, career_start/career_start.tsv.gz),
# plus the value-of-returns analysis. Runs everything one after another (low-memory machine).
# Run from this folder: bash run_career.sh
P=${PYTHON:-python}
CS=career_start/career_start.tsv.gz
mkdir -p logs
export PYTHONIOENCODING=utf-8
for F in 31 22 13; do
  export CT_FIELD_ID=$F
  D=data; [ "$F" != "31" ] && D=data_field$F
  R=results; [ "$F" != "31" ] && R=results_field$F
  IN=$D/trajectories_world_career.csv; OUT=${R}_world_career
  $P build_trajectories.py --world --career-start $CS --tag world_career > logs/career_build_$F.txt 2>&1
  $P -u estimate.py --input $IN --out $OUT --n-boot 100 --by-career > logs/career_est_$F.txt 2>&1
  $P -u ddd_checks.py --input $IN --out $OUT > logs/career_ddd_$F.txt 2>&1
  $P -u ddd_checks.py --input $IN --out $OUT --placebo-year 2007 > logs/career_dddp_$F.txt 2>&1
  $P -u reduced_form.py --input $IN --out $OUT > logs/career_rf_$F.txt 2>&1
  echo "field $F career done $(date)"
done
export CT_FIELD_ID=20
$P build_trajectories.py --career-start $CS --tag career > logs/career_build_20.txt 2>&1
$P -u estimate.py --input data_field20/trajectories_career.csv --out results_field20_career --n-boot 100 --by-career > logs/career_est_20.txt 2>&1
$P -u ddd_checks.py --input data_field20/trajectories_career.csv --out results_field20_career > logs/career_ddd_20.txt 2>&1
$P -u ddd_checks.py --input data_field20/trajectories_career.csv --out results_field20_career --placebo-year 2007 > logs/career_dddp_20.txt 2>&1
echo "economics career done $(date)"
for F in 31 22 13; do
  export CT_FIELD_ID=$F
  D=data; [ "$F" != "31" ] && D=data_field$F
  R=results; [ "$F" != "31" ] && R=results_field$F
  $P build_trajectories.py --world --career-start $CS --controls FR DE ES NL PT --tag world_career_ctrl5 > logs/career_build5_$F.txt 2>&1
  $P -u placebo_space.py --input $D/trajectories_world_career_ctrl5.csv --out ${R}_world_career_placebo_space --n-boot 100 > logs/career_pspace_$F.txt 2>&1
  echo "field $F placebo-space done $(date)"
done
for F in 31 22 13; do
  export CT_FIELD_ID=$F
  $P -u return_value.py > logs/return_value_$F.txt 2>&1
  echo "field $F return value done $(date)"
done
echo "all done $(date)"
