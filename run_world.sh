#!/usr/bin/env bash
# One field (usage: bash run_world.sh 13): world-wide citation distributions, waiting out the daily
# API budget if needed, then rebuild and re-estimate with --world.
# Run from this folder: bash run_world22.sh
set -u
F=$1; export CT_FIELD_ID=$F
P=${PYTHON:-python}
mkdir -p logs
for attempt in 1 2 3 4 5 6; do
    rm -f data_field$F/world/*.part
    PYTHONUNBUFFERED=1 $P fetch_world_citations.py >> logs/fetch_world$F.txt 2>&1
    n=$(ls data_field$F/world/*.csv.gz 2>/dev/null | wc -l)
    echo "attempt $attempt: $n/22 years" >> logs/fetch_world$F.txt
    [ "$n" -ge 22 ] && break
    sleep 10800   # check again in 3 h (budget resets at midnight UTC)
done
[ "$(ls data_field$F/world/*.csv.gz | wc -l)" -ge 22 ] || { echo "download incomplete"; exit 1; }
$P build_trajectories.py --world --tag world > logs/f${F}_build_world.txt 2>&1 && \
$P estimate.py --input data_field$F/trajectories_world.csv --out results_field${F}_world --event-study --by-career > logs/f${F}_world_main.txt 2>&1 && \
$P estimate.py --input data_field$F/trajectories_world.csv --out results_field${F}_world --placebo-year 2007 > logs/f${F}_world_placebo.txt 2>&1 && \
$P build_trajectories.py --world --controls FR DE ES --tag world_es > logs/f${F}_build_world_es.txt 2>&1 && \
$P estimate.py --input data_field$F/trajectories_world_es.csv --out results_field${F}_world_es --event-study > logs/f${F}_world_es_main.txt 2>&1 && \
$P estimate.py --input data_field$F/trajectories_world_es.csv --out results_field${F}_world_es --placebo-year 2007 > logs/f${F}_world_es_placebo.txt 2>&1
echo "world $F pipeline exit $?"
