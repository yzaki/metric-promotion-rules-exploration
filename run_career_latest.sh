#!/usr/bin/env bash
# Career-stage analyses with the career start re-matched on the latest sample (match_career.py).
cd "$(dirname "$0")"; P=${PYTHON:-python}; CS=career_start/career_start.tsv.gz; L=logs/latest
one() {
  F=$1; export CT_FIELD_ID=$F; D=data; R=results; [ $F != 31 ] && D=data_field$F && R=results_field$F
  $P build_trajectories.py --world --career-start $CS --tag world_career > $L/c$F.b.txt 2>&1
  C=$D/trajectories_world_career.csv
  $P -u estimate.py --input $C --out ${R}_world_career --n-boot 100 --by-career > $L/c$F.e.txt 2>&1
  $P -u ddd_checks.py --input $C --out ${R}_world_career >> $L/c$F.e.txt 2>&1
  $P -u ddd_checks.py --input $C --out ${R}_world_career --placebo-year 2007 >> $L/c$F.e.txt 2>&1
  $P -u reduced_form.py --input $C --out ${R}_world_career >> $L/c$F.e.txt 2>&1
  $P -u career_bands.py --input $C --out ${R}_world_career >> $L/c$F.e.txt 2>&1
  if [ $F != 16 ]; then
    $P build_trajectories.py --world --career-start $CS --controls FR DE ES NL PT --tag world_career_ctrl5 > $L/c$F.p.txt 2>&1
    $P -u placebo_space.py --input $D/trajectories_world_career_ctrl5.csv --out ${R}_world_career_placebo_space --n-boot 100 >> $L/c$F.p.txt 2>&1
  fi
  echo "$(date) career $F done" >> $L/progress.txt
}
for F in 31 22 13 16; do one $F & done
export CT_FIELD_ID=20
$P build_trajectories.py --career-start $CS --tag career > $L/c20.b.txt 2>&1
$P -u estimate.py --input data_field20/trajectories_career.csv --out results_field20_career --n-boot 100 --by-career > $L/c20.e.txt 2>&1
$P -u ddd_checks.py --input data_field20/trajectories_career.csv --out results_field20_career >> $L/c20.e.txt 2>&1
$P -u ddd_checks.py --input data_field20/trajectories_career.csv --out results_field20_career --placebo-year 2007 >> $L/c20.e.txt 2>&1
wait
$P paper_tables.py > $L/tables2.txt 2>&1
$P paper_figures.py > $L/figures2.txt 2>&1
echo "$(date) CAREER + TABLES DONE" >> $L/progress.txt
