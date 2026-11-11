#!/usr/bin/env bash
. "$(dirname "$0")/run_lib.sh"   # strict mode (set -euo pipefail) and waitall
# Download everything the rebuild needs from the latest OpenAlex version. Resumable; waits out budget resets.
cd "$(dirname "$0")"
export OPENALEX_API_KEY=$(tr -d '[:space:]' < ~/.openalex.key)
P=${PYTHON:-python}
nfiles() { ls $1 2>/dev/null | wc -l | tr -d ' '; }
dir() { [ $1 = 31 ] && echo data || echo data_field$1; }
step() {  # step <done-check-count> <glob> <log> <cmd...>
  local need=$1 glob=$2 log=$3; shift 3
  [ "$(nfiles "$glob")" -ge $need ] && return 0
  "$@" >> logs/$log 2>&1; [ "$(nfiles "$glob")" -ge $need ]
}
field_loop() {  # one field, until complete
  F=$1; export CT_FIELD_ID=$F; D=$(dir $F)
  while true; do
    ok=1
    if [ $F = 20 ]; then
      for C in IT FR DE ES; do step 22 "$D/raw/works_${C}_*.csv.gz" fetch_${C}_20.txt $P fetch_openalex.py --countries $C || ok=0; done
    else
      step 22 "$D/world/cites_*.csv.gz" world_$F.txt $P fetch_world_citations.py || ok=0
      for C in ES NL PT IN RU; do step 22 "$D/raw/works_${C}_*.csv.gz" fetch_${C}_$F.txt $P fetch_openalex.py --countries $C || ok=0; done
      if [ $F != 16 ]; then for C in PL RO; do step 22 "$D/raw/works_${C}_*.csv.gz" fetch_${C}_$F.txt $P fetch_openalex.py --countries $C || ok=0; done; fi
      step 76 "$D/refs/refs_*.csv.gz" refs_$F.txt $P fetch_references.py --countries IT FR DE ES || ok=0
      step 60 "$D/venues/venues_*.csv.gz" venues_$F.txt $P fetch_venues.py || ok=0
    fi
    [ $ok = 1 ] && break
    echo "$(date): field $F incomplete; retrying in 10 min" >> logs/latest_fetch.txt
    sleep 600
  done
  echo "$(date): field $F fetched" >> logs/latest_fetch.txt
}
for F in 31 22 13 16 20; do field_loop $F & done
waitall
$P fetch_sources.py >> logs/fetch_sources.txt 2>&1
echo "$(date): ALL FETCHED" >> logs/latest_fetch.txt
