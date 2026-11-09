#!/usr/bin/env bash
# Journal tier, fee-charging open access and institutions (plan V1, V2, C4) for Italy, India and Russia.
# Run after run_venues_fetch.sh. One country at a time (each loads the raw author rows).
set -u
P=${PYTHON:-python}
export PYTHONIOENCODING=utf-8
$P -u venues.py --treated IT --out results_venues > logs/venues_IT.txt 2>&1; echo "IT exit $? $(date)"
$P -u venues.py --treated IN --groups results_india/india_groups.csv --covered-label UGC-covered --out results_venues > logs/venues_IN.txt 2>&1; echo "IN exit $? $(date)"
$P -u venues.py --treated RU --groups results_russia/russia_groups.csv --covered-label 5-100 --out results_venues > logs/venues_RU.txt 2>&1; echo "RU exit $? $(date)"
$P -u venue_checks.py --treated IT > logs/venue_checks_IT.txt 2>&1
$P -u venue_checks.py --treated IN --groups results_india/india_groups.csv --covered-label UGC-covered > logs/venue_checks_IN.txt 2>&1
$P -u venue_checks.py --treated RU --groups results_russia/russia_groups.csv --covered-label 5-100 > logs/venue_checks_RU.txt 2>&1
# timing checks for institutions (venue panels) and co-authorship (co-author panels written by coauthors.py)
$P -u venue_checks.py --treated IT --outcomes n_institutions single_inst --tag _inst > logs/venue_checks_inst_IT.txt 2>&1
$P -u venue_checks.py --treated IN --groups results_india/india_groups.csv --covered-label UGC-covered --outcomes n_institutions single_inst --tag _inst > logs/venue_checks_inst_IN.txt 2>&1
$P -u venue_checks.py --treated RU --groups results_russia/russia_groups.csv --covered-label 5-100 --outcomes n_institutions single_inst --tag _inst > logs/venue_checks_inst_RU.txt 2>&1
$P -u venue_checks.py --treated IT --out results_coauthors --outcomes international new_coauthors log_team > logs/venue_checks_co_IT.txt 2>&1
$P -u venue_checks.py --treated IN --groups results_india/india_groups.csv --covered-label UGC-covered --out results_coauthors --outcomes international new_coauthors log_team > logs/venue_checks_co_IN.txt 2>&1
$P -u venue_checks.py --treated RU --groups results_russia/russia_groups.csv --covered-label 5-100 --out results_coauthors --outcomes international new_coauthors log_team > logs/venue_checks_co_RU.txt 2>&1
