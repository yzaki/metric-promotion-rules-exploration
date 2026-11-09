#!/usr/bin/env bash
cd "$(dirname "$0")"
until grep -q "ALL FETCHED" logs/latest_fetch.txt 2>/dev/null; do sleep 600; done
./run_latest_rebuild.sh
