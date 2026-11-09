#!/usr/bin/env bash
# Chemistry (OpenAlex field 16), stage A: everything that does not need the true career start.
# Analysis plan: ../PREREGISTRATION_chemistry_2026-11-05.md (written before the download).
set -u
P=${PYTHON:-python}
export PYTHONIOENCODING=utf-8 CT_FIELD_ID=16
D=data_field16; R=results_field16
mkdir -p logs
$P build_trajectories.py --world --tag world > logs/chem_build_world.txt 2>&1
$P build_trajectories.py --world --controls FR DE ES --tag world_es > logs/chem_build_world_es.txt 2>&1
$P -u estimate.py --input $D/trajectories_world.csv --out ${R}_world --event-study > logs/chem_est.txt 2>&1
$P -u estimate.py --input $D/trajectories_world.csv --out ${R}_world --placebo-year 2007 > logs/chem_plac.txt 2>&1
$P -u estimate.py --input $D/trajectories_world_es.csv --out ${R}_world_es --event-study > logs/chem_est_es.txt 2>&1
$P -u estimate.py --input $D/trajectories_world_es.csv --out ${R}_world_es --placebo-year 2007 > logs/chem_plac_es.txt 2>&1
$P -u effect_sizes.py --input $D/trajectories_world.csv --results ${R}_world > logs/chem_eff.txt 2>&1
$P -u reduced_form.py --input $D/trajectories_world.csv --out ${R}_world > logs/chem_rf.txt 2>&1
$P -u composition_check.py --input $D/trajectories_world.csv --out ${R}_world > logs/chem_comp.txt 2>&1
$P -u composition_decompose.py --input $D/trajectories_world.csv --out ${R}_world --n-boot 100 > logs/chem_decomp.txt 2>&1
$P -u first_entry.py > logs/chem_first.txt 2>&1
OPENALEX_API_KEY="$OPENALEX_API_KEY" $P -u fetch_authors.py > logs/chem_authors.txt 2>&1
$P -u export_author_papers.py > logs/chem_export.txt 2>&1
echo "stage A done $(date)"
