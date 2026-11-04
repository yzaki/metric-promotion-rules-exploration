#!/usr/bin/env bash
# Engineering (OpenAlex field 22) replication: download until done, waiting out the
# daily budget if needed, then build and estimate (IT vs FR+DE, and with ES).
# Run from this folder: bash run_field22.sh
set -u
export CT_FIELD_ID=22
P=.venv/Scripts/python
mkdir -p logs
for attempt in 1 2 3; do
    PYTHONUNBUFFERED=1 $P fetch_openalex.py --countries IT FR DE ES >> logs/fetch_field22.txt 2>&1
    n=$(ls data_field22/raw/*.csv.gz 2>/dev/null | wc -l)
    echo "attempt $attempt: $n/88 files" >> logs/fetch_field22.txt
    [ "$n" -ge 88 ] && break
    sleep 17400   # wait for the daily budget to reset (~4.8 h), then resume
done
[ "$(ls data_field22/raw/*.csv.gz | wc -l)" -ge 88 ] || { echo "download incomplete"; exit 1; }
$P build_trajectories.py > logs/f22_build.txt 2>&1 && \
$P estimate.py --event-study --by-career > logs/f22_main.txt 2>&1 && \
$P estimate.py --placebo-year 2007 > logs/f22_placebo.txt 2>&1 && \
$P build_trajectories.py --controls FR DE ES --tag es > logs/f22_build_es.txt 2>&1 && \
$P estimate.py --input data_field22/trajectories_es.csv --out results_field22_es --event-study > logs/f22_es_main.txt 2>&1 && \
$P estimate.py --input data_field22/trajectories_es.csv --out results_field22_es --placebo-year 2007 > logs/f22_es_placebo.txt 2>&1
echo "field22 pipeline exit $?"
