#!/usr/bin/env bash
# Russia (Project 5-100, from 2013) as a third treated country; plan ../PREREGISTRATION_russia_2026-11-05.md.
# Run from this folder after: fetch_openalex.py --countries RU for fields 31, 22, 13, 16.
set -u
P=${PYTHON:-python}
export PYTHONIOENCODING=utf-8
mkdir -p logs results_russia
N=$(ls data/raw/works_RU_*.csv.gz data_field*/raw/works_RU_*.csv.gz 2>/dev/null | wc -l)
if [ "$N" -lt 88 ]; then echo "only $N of 88 Russian files downloaded; stopping (rerun fetch_openalex.py --countries RU)"; exit 1; fi
for F in 31 22 13 16; do
  export CT_FIELD_ID=$F
  D=data; [ "$F" != "31" ] && D=data_field$F
  R=results; [ "$F" != "31" ] && R=results_field$F
  $P build_trajectories.py --world --treated RU --tag world_RU > logs/ru_build_$F.txt 2>&1
  $P build_trajectories.py --world --treated RU --controls FR DE ES --tag world_RU_es > logs/ru_build_es_$F.txt 2>&1
  $P -u estimate.py --input $D/trajectories_world_RU.csv --out ${R}_world_RU --n-boot 100 --event-study > logs/ru_est_$F.txt 2>&1
  $P -u estimate.py --input $D/trajectories_world_RU.csv --out ${R}_world_RU --n-boot 100 --placebo-year 2007 > logs/ru_plac_$F.txt 2>&1
  $P -u estimate.py --input $D/trajectories_world_RU_es.csv --out ${R}_world_RU_es --n-boot 100 --event-study > logs/ru_est_es_$F.txt 2>&1
  $P -u estimate.py --input $D/trajectories_world_RU_es.csv --out ${R}_world_RU_es --n-boot 100 --placebo-year 2007 > logs/ru_plac_es_$F.txt 2>&1
  $P -u reduced_form.py --input $D/trajectories_world_RU.csv --out ${R}_world_RU > logs/ru_rf_$F.txt 2>&1
  $P -u first_entry.py --treated RU --out ${R}_world_RU --save-choices results_russia/choices_$D.csv.gz > logs/ru_first_$F.txt 2>&1
  echo "field $F done $(date)"
done
OPENALEX_API_KEY="$OPENALEX_API_KEY" $P -u fetch_affiliations.py --suffix RU --out affiliations_ru.csv.gz > logs/ru_affil.txt 2>&1
$P -u russia_mechanism.py --out results_russia > logs/ru_mech.txt 2>&1
$P -u india_stacked.py --suffix RU --covered-label 5-100 --out results_russia --groups results_russia/russia_groups.csv > logs/ru_stacked.txt 2>&1
echo "all done $(date)"
