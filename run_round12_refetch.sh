#!/usr/bin/env bash
# Round 12: re-download Italy/France/Germany works for physics, engineering and biochemistry from the latest
# OpenAlex (the 7-8 Nov rebuild had reused files fetched on 5 Nov, because fetch_openalex.py skips existing
# files), then rerun every analysis. Each step's exit status is logged; the script stops on failure.
cd "$(dirname "$0")"
P=${PYTHON:-python}; export PYTHONIOENCODING=utf-8
export OPENALEX_API_KEY=$(tr -d '[:space:]' < ~/.openalex.key)
L=logs/r12; mkdir -p $L
log() { echo "$(date '+%F %T') $*" | tee -a $L/progress.txt; }
run() { "$@" || { log "FAILED: $*"; exit 1; }; }
# 0. snapshot of the results on the 5 Nov IT/FR/DE files (for the change report)
if [ ! -d ../snapshot_r11 ]; then
  mkdir -p ../snapshot_r11
  for d in results*/ ; do mkdir -p ../snapshot_r11/$d; find $d -maxdepth 1 -name '*.csv' -exec cp {} ../snapshot_r11/$d \; ; done
  cp -R ../v3_out ../snapshot_r11/v3_out; cp career_start/career_start.tsv.gz ../snapshot_r11/; cp -R data_meta ../snapshot_r11/data_meta
  log "snapshot done"
fi
# 1. fresh raw folders: other countries hard-linked from the 7-8 Nov files, IT/FR/DE downloaded again
for D in data data_field22 data_field13; do
  if [ -L $D/raw ]; then
    SRC=$(readlink $D/raw); mv $D/raw $D/raw_ITFRDE_5nov; mkdir $D/raw
    for f in $SRC/works_*.csv.gz; do b=$(basename $f); case $b in works_IT_*|works_FR_*|works_DE_*) ;; *) ln $f $D/raw/$b ;; esac; done
  fi
done
fetch() { F=$1; export CT_FIELD_ID=$F; D=data; [ $F != 31 ] && D=data_field$F
  for C in IT FR DE; do
    until [ "$(ls $D/raw/works_${C}_*.csv.gz 2>/dev/null | wc -l | tr -d ' ')" -ge 22 ]; do
      $P -u fetch_openalex.py --countries $C >> $L/fetch_${C}_$F.txt 2>&1 || { echo "$(date) retry in 10 min" >> $L/fetch_${C}_$F.txt; sleep 600; }
    done
  done
  log "fetched IT FR DE field $F"; }
for F in 31 22 13; do fetch $F & done; wait
# 2. full rebuild (as on 7-8 Nov) on the new files
run bash run_latest_rebuild.sh
log "rebuild done"
# 3. career start (SciSciNet/MAG) re-matched on the new sample, SciSciNet subset, disruption, career, timing
run $P -u export_author_papers.py > $L/export_pairs.txt 2>&1
run $P -u ../extra/sciscinet_subset.py > $L/sciscinet_subset.txt 2>&1
( cd ../match_work && run $P -u ../repo_v3/jubail/match_career.py > match_r12.log 2>&1 )
run gzip -c ../match_work/career_start.tsv > career_start/career_start.tsv.gz
log "career start re-matched"
for F in 31 22 13 16; do (CT_FIELD_ID=$F $P -u disruption.py > $L/disruption_$F.txt 2>&1) & done; wait
run bash run_career_latest.sh
run bash run_round3.sh
log "career and timing done"
# 4. returns checks, S37, MDPI, Russia/India pre-tests, Russia vs ES+NL+PT
for F in 31 22 13 16; do (CT_FIELD_ID=$F $P -u returns_checks.py > $L/rc_$F.txt 2>&1) & done; wait
for F in 31 22 13 16; do (CT_FIELD_ID=$F $P -u returns_placebo_space.py > $L/rps_$F.txt 2>&1) & done; wait
for F in 31 22 13 16; do (CT_FIELD_ID=$F $P -u mdpi_check.py > $L/mdpi_$F.txt 2>&1) & done; wait
run bash run_round9_pretest.sh
run bash run_round11_russia_esnlpt.sh
run $P -u country_pretrend.py > $L/country_pretrend.txt 2>&1
run $P -u download_comparison.py > $L/download_comparison.txt 2>&1
run $P paper_tables.py > $L/tables.txt 2>&1
run $P paper_figures.py > $L/figures.txt 2>&1
log "ALL DONE"
