#!/usr/bin/env bash
. "$(dirname "$0")/run_lib.sh"   # strict mode (set -euo pipefail) and waitall
# Journal and institutions per article, four fields in parallel, IT FR DE IN RU, decision years (plan V1, V2, C4);
# then journal metadata. Reruns skip finished files.
P=${PYTHON:-python}
export PYTHONIOENCODING=utf-8
for F in "$@"; do
  ( CT_FIELD_ID=$F $P -u fetch_venues.py > logs/venues_fetch_$F.txt 2>&1; echo "field $F exit $? $(date)" ) &
done
waitall
# physics may be running from an earlier start: waitall for any fetch_venues process to end
while ps -W 2>/dev/null | grep -q "[p]ython"; do
  pgrep -f fetch_venues >/dev/null || break
  sleep 20
done
grep -l "budget used up" logs/venues_fetch_*.txt && { echo "budget exhausted; rerun tomorrow"; exit 3; }
$P -u fetch_sources.py > logs/fetch_sources.txt 2>&1; echo "sources exit $? $(date)"
echo "all done $(date)"
