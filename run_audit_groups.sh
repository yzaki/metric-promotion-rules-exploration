#!/usr/bin/env bash
. "$(dirname "$0")/run_lib.sh"   # strict mode (set -euo pipefail) and waitall
# Rerun after the audit's correction of the India and Russia main-affiliation rule (main institution by OpenAlex ID;
# Russia's 21 Project 5-100 universities listed by ID): mechanism tests, stacked tests, co-authorship and journal
# outcomes by covered group, and their timing checks. Stops at the first failure.
set -euo pipefail
cd "$(dirname "$0")"
P=${PYTHON:-python}; export PYTHONIOENCODING=utf-8
L=logs/audit; mkdir -p $L
step() { echo "$(date '+%H:%M:%S') $*"; "$@"; }
step $P -u india_mechanism.py --out results_india > $L/in_mech.txt 2>&1
step $P -u russia_mechanism.py --out results_russia > $L/ru_mech.txt 2>&1
step $P -u india_stacked.py --out results_india --groups results_india/india_groups.csv > $L/in_stacked.txt 2>&1
step $P -u india_stacked.py --suffix RU --covered-label 5-100 --out results_russia --groups results_russia/russia_groups.csv > $L/ru_stacked.txt 2>&1
step $P -u coauthors.py --treated IN --groups results_india/india_groups.csv --covered-label UGC-covered --out results_coauthors_groups > $L/coauthors_groups_IN.txt 2>&1
step $P -u coauthors.py --treated RU --groups results_russia/russia_groups.csv --covered-label 5-100 --out results_coauthors_groups > $L/coauthors_groups_RU.txt 2>&1
step $P -u venues.py --treated IN --groups results_india/india_groups.csv --covered-label UGC-covered --out results_venues > $L/venues_IN.txt 2>&1
step $P -u venues.py --treated RU --groups results_russia/russia_groups.csv --covered-label 5-100 --out results_venues > $L/venues_RU.txt 2>&1
for C in IN RU; do
  G=results_india/india_groups.csv; LAB=UGC-covered; [ $C = RU ] && G=results_russia/russia_groups.csv && LAB=5-100
  step $P -u venue_checks.py --treated $C --groups $G --covered-label $LAB > $L/venue_checks_$C.txt 2>&1
  step $P -u venue_checks.py --treated $C --groups $G --covered-label $LAB --outcomes n_institutions single_inst --tag _inst > $L/venue_checks_inst_$C.txt 2>&1
  step $P -u venue_checks.py --treated $C --groups $G --covered-label $LAB --out results_coauthors --outcomes international new_coauthors log_team > $L/venue_checks_co_$C.txt 2>&1
done
echo "$(date '+%H:%M:%S') ALL DONE"
