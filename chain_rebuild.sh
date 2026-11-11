#!/usr/bin/env bash
. "$(dirname "$0")/run_lib.sh"   # strict mode (set -euo pipefail) and waitall
cd "$(dirname "$0")"
until grep -q "ALL FETCHED" logs/latest_fetch.txt 2>/dev/null; do sleep 600; done
./run_latest_rebuild.sh
