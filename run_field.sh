#!/usr/bin/env bash
# Full pipeline for one OpenAlex field: download IT/FR/DE/ES (waiting out the daily API
# budget if needed), build, estimate (FR+DE and FR+DE+ES), placebo, effect sizes.
# Usage (from this folder): bash run_field.sh 13
set -u
F=$1
export CT_FIELD_ID=$F
P=${PYTHON:-python}
D=data_field$F
R=results_field$F
mkdir -p logs
for attempt in 1 2 3 4 5 6 7 8; do
    rm -f $D/raw/*.part
    PYTHONUNBUFFERED=1 $P fetch_openalex.py --countries IT FR DE ES >> logs/fetch_field$F.txt 2>&1
    n=$(ls $D/raw/*.csv.gz 2>/dev/null | wc -l)
    echo "attempt $attempt: $n/88 files" >> logs/fetch_field$F.txt
    [ "$n" -ge 88 ] && break
    sleep 10800   # check again in 3 h (budget resets at midnight UTC)
done
[ "$(ls $D/raw/*.csv.gz | wc -l)" -ge 88 ] || { echo "field $F download incomplete"; exit 1; }
$P build_trajectories.py > logs/f${F}_build.txt 2>&1 && \
$P estimate.py --event-study --by-career > logs/f${F}_main.txt 2>&1 && \
$P estimate.py --placebo-year 2007 > logs/f${F}_placebo.txt 2>&1 && \
$P effect_sizes.py > logs/f${F}_effects.txt 2>&1 && \
$P build_trajectories.py --controls FR DE ES --tag es > logs/f${F}_build_es.txt 2>&1 && \
$P estimate.py --input $D/trajectories_es.csv --out ${R}_es --event-study > logs/f${F}_es_main.txt 2>&1 && \
$P estimate.py --input $D/trajectories_es.csv --out ${R}_es --placebo-year 2007 > logs/f${F}_es_placebo.txt 2>&1
echo "field $F pipeline exit $?"
