#!/usr/bin/env bash
# Return outcomes with each scientist's influence on the estimates saved (first_entry.py --save-influence), so that
# Table S34 computes Italy-minus-Russia/India contrasts and pooled estimates with the covariance from shared control
# scientists and from scientists in several fields. Point estimates are unchanged.
. "$(dirname "$0")/run_lib.sh"
cd "$(dirname "$0")"
P=${PYTHON:-python}; export PYTHONIOENCODING=utf-8
L=logs/audit; mkdir -p $L
one() {
  F=$1; export CT_FIELD_ID=$F; D=data; R=results; [ $F != 31 ] && D=data_field$F && R=results_field$F
  $P -u first_entry.py --out ${R}_world --save-influence ${R}_world/first_entry_influence.csv.gz > $L/fe_it_$F.txt 2>&1
  $P -u first_entry.py --treated RU --out ${R}_world_RU --save-choices results_russia/choices_$D.csv.gz \
    --save-influence ${R}_world_RU/first_entry_influence.csv.gz > $L/fe_ru_$F.txt 2>&1
  $P -u first_entry.py --treated IN --out ${R}_world_IN --save-choices results_india/choices_$D.csv.gz \
    --save-influence ${R}_world_IN/first_entry_influence.csv.gz > $L/fe_in_$F.txt 2>&1
  $P -u first_entry.py --controls ES NL PT --out ${R}_world_esnlpt \
    --save-influence ${R}_world_esnlpt/first_entry_influence.csv.gz > $L/fe_it_esnlpt_$F.txt 2>&1
  $P -u first_entry.py --treated RU --controls ES NL PT --out ${R}_world_RU_esnlpt \
    --save-influence ${R}_world_RU_esnlpt/first_entry_influence.csv.gz > $L/fe_ru_esnlpt_$F.txt 2>&1
  echo "$(date '+%H:%M:%S') field $F done"
}
for F in 31 22 13 16; do one $F & done
waitall
echo "$(date '+%H:%M:%S') ALL DONE"
