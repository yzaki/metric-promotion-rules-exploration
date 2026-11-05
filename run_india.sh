#!/usr/bin/env bash
# India (UGC Regulations 2010) as a second treated country; plan ../PREREGISTRATION_india_2026-11-05.md.
# Run from this folder after: fetch_openalex.py --countries IN for fields 31, 22, 13, 16.
set -u
P=.venv/Scripts/python
export PYTHONIOENCODING=utf-8
mkdir -p logs results_india
N=$(ls data/raw/works_IN_*.csv.gz data_field*/raw/works_IN_*.csv.gz 2>/dev/null | wc -l)
if [ "$N" -lt 88 ]; then echo "only $N of 88 Indian files downloaded; stopping (rerun fetch_openalex.py --countries IN)"; exit 1; fi
for F in 31 22 13 16; do
  export CT_FIELD_ID=$F
  D=data; [ "$F" != "31" ] && D=data_field$F
  R=results; [ "$F" != "31" ] && R=results_field$F
  $P build_trajectories.py --world --treated IN --tag world_IN > logs/in_build_$F.txt 2>&1
  $P build_trajectories.py --world --treated IN --controls FR DE ES --tag world_IN_es > logs/in_build_es_$F.txt 2>&1
  $P -u estimate.py --input $D/trajectories_world_IN.csv --out ${R}_world_IN --n-boot 100 --event-study > logs/in_est_$F.txt 2>&1
  $P -u estimate.py --input $D/trajectories_world_IN.csv --out ${R}_world_IN --n-boot 100 --placebo-year 2007 > logs/in_plac_$F.txt 2>&1
  $P -u estimate.py --input $D/trajectories_world_IN_es.csv --out ${R}_world_IN_es --n-boot 100 --event-study > logs/in_est_es_$F.txt 2>&1
  $P -u estimate.py --input $D/trajectories_world_IN_es.csv --out ${R}_world_IN_es --n-boot 100 --placebo-year 2007 > logs/in_plac_es_$F.txt 2>&1
  $P -u reduced_form.py --input $D/trajectories_world_IN.csv --out ${R}_world_IN > logs/in_rf_$F.txt 2>&1
  $P -u first_entry.py --treated IN --out ${R}_world_IN --save-choices results_india/choices_$D.csv.gz > logs/in_first_$F.txt 2>&1
  echo "field $F done $(date)"
done
OPENALEX_API_KEY="$OPENALEX_API_KEY" $P -u fetch_affiliations.py --suffix IN --out affiliations_in.csv.gz > logs/in_affil.txt 2>&1
$P -u india_mechanism.py --out results_india > logs/in_mech.txt 2>&1
$P -u india_stacked.py --out results_india --groups results_india/india_groups.csv > logs/in_stacked.txt 2>&1
echo "all done $(date)"
