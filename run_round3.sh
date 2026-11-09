#!/usr/bin/env bash
# Round-3 additions: timing (with SEs) for all four fields; IRL event studies with France + Germany.
P=${PYTHON:-python}
for F in 31 22 13 16; do
  ( export CT_FIELD_ID=$F; D=data; R=results; [ $F != 31 ] && D=data_field$F && R=results_field$F
    $P first_entry.py --timing > logs/r3_fe_$F.txt 2>&1
    [ $F != 16 ] && $P estimate.py --input $D/trajectories_world.csv.gz --out ${R}_world_esFRDE --event-study --n-boot 200 > logs/r3_es_$F.txt 2>&1
    echo "field $F done" ) &
done
wait
