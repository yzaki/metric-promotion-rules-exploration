#!/usr/bin/env bash
# Co-author outcomes split by covered vs not-covered institutions (India UGC, Russia 5-100); extra analysis.
set -u
P=${PYTHON:-python}
export PYTHONIOENCODING=utf-8
$P -u coauthors.py --treated IN --groups results_india/india_groups.csv --covered-label UGC-covered --out results_coauthors_groups > logs/coauthors_groups_IN.txt 2>&1
echo "IN exit $? $(date)"
$P -u coauthors.py --treated RU --groups results_russia/russia_groups.csv --covered-label 5-100 --out results_coauthors_groups > logs/coauthors_groups_RU.txt 2>&1
echo "RU exit $? $(date)"
