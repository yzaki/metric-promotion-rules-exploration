#!/usr/bin/env bash
# Chemistry (OpenAlex field 16), stage B: after data_meta/career_start.tsv.gz includes chemistry authors.
# Tests C3-C5 of ../PREREGISTRATION_chemistry_2026-11-05.md.
set -u
P=.venv/Scripts/python
export PYTHONIOENCODING=utf-8 CT_FIELD_ID=16
D=data_field16; R=results_field16_world_career
mkdir -p logs
$P build_trajectories.py --world --career-start data_meta/career_start.tsv.gz --tag world_career > logs/chem_build_career.txt 2>&1
$P -u estimate.py --input $D/trajectories_world_career.csv --out $R --n-boot 100 --by-career > logs/chem_career.txt 2>&1
$P -u rank_exposure.py --input $D/trajectories_world_career.csv --out $R --n-boot 100 > logs/chem_rank.txt 2>&1
$P -u register_split.py --input $D/trajectories_world_career.csv --out $R > logs/chem_regsplit.txt 2>&1
$P -u sector_thresholds.py --input $D/trajectories_world_career.csv --out $R --n-boot 100 > logs/chem_sector.txt 2>&1
OPENALEX_API_KEY="$OPENALEX_API_KEY" $P -u fetch_affiliations.py > logs/chem_affil.txt 2>&1
$P -u institution_split.py --input $D/trajectories_world_career.csv --out $R --n-boot 100 > logs/chem_inst.txt 2>&1
echo "stage B done $(date)"
