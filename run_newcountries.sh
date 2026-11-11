#!/usr/bin/env bash
. "$(dirname "$0")/run_lib.sh"   # strict mode (set -euo pipefail) and waitall
# Further treated countries with national metric-based promotion rules from 2011-2012:
# Romania (minimum scientometric standards for habilitation and professorships, Law 1/2011, Orders
# 4692/2011 and 6560/2012) and Poland (habilitation criteria with bibliometric indicators, Sept 2011).
# Same design as Italy: treated country vs France + Germany, world citation measure, Italy left out.
# Run from this folder after fetch_openalex.py --countries RO PL for fields 31, 22, 13.
P=${PYTHON:-python}
export PYTHONIOENCODING=utf-8
mkdir -p logs
for F in 31 22 13; do
  export CT_FIELD_ID=$F
  D=data; [ "$F" != "31" ] && D=data_field$F
  R=results; [ "$F" != "31" ] && R=results_field$F
  for C in PL RO; do
    $P build_trajectories.py --world --treated $C --tag world_$C > logs/new_build_${F}_$C.txt 2>&1 || { echo "build failed $F $C"; continue; }
    $P -u estimate.py --input $D/trajectories_world_$C.csv --out ${R}_world_$C --n-boot 100 --event-study > logs/new_est_${F}_$C.txt 2>&1
    $P -u estimate.py --input $D/trajectories_world_$C.csv --out ${R}_world_$C --n-boot 100 --placebo-year 2007 > logs/new_plac_${F}_$C.txt 2>&1
    $P -u reduced_form.py --input $D/trajectories_world_$C.csv --out ${R}_world_$C > logs/new_rf_${F}_$C.txt 2>&1
    echo "field $F $C done $(date)"
  done
done
echo "all done $(date)"
