#!/usr/bin/env bash
. "$(dirname "$0")/run_lib.sh"   # strict mode (set -euo pipefail) and waitall
# Item 3: alternative control groups (leave-one-country-out and extra countries), world measure.
# For each field and control set: build trajectories, IRL main estimate, model-free DiD.
# Run from this folder: bash run_controls.sh
P=${PYTHON:-python}
mkdir -p logs
for F in 31 22 13; do
  export CT_FIELD_ID=$F
  D=data; [ "$F" != "31" ] && D=data_field$F
  R=results; [ "$F" != "31" ] && R=results_field$F
  for SET in "FR" "DE" "ES" "NL" "PT" "FR DE ES NL PT"; do
    TAG="world_ctrl_$(echo $SET | tr ' ' '_')"
    $P build_trajectories.py --world --controls $SET --tag $TAG > logs/ctrl_build_${F}_${TAG}.txt 2>&1 || { echo "build failed $F $SET"; continue; }
    $P estimate.py --input $D/trajectories_$TAG.csv --out ${R}_$TAG --n-boot 100 > logs/ctrl_est_${F}_${TAG}.txt 2>&1
    $P reduced_form.py --input $D/trajectories_$TAG.csv --out ${R}_$TAG > logs/ctrl_rf_${F}_${TAG}.txt 2>&1
    echo "field $F controls [$SET] done"
  done
done
