#!/usr/bin/env bash
# Core rebuild on the latest OpenAlex download (Nov 2026): Italy vs France + Germany (+ Spain),
# four fields with bibliometric thresholds. Run after run_latest_fetch.sh has finished.
cd "$(dirname "$0")"
P=${PYTHON:-python}; export PYTHONIOENCODING=utf-8
CS=career_start/career_start.tsv.gz
mkdir -p logs/latest
one() {
  F=$1; export CT_FIELD_ID=$F
  D=data; R=results; [ $F != 31 ] && D=data_field$F && R=results_field$F
  L=logs/latest/f$F
  # trajectories
  $P build_trajectories.py --world --tag world > $L.b1.txt 2>&1
  $P build_trajectories.py --world --controls FR DE ES --tag world_es > $L.b2.txt 2>&1
  $P build_trajectories.py > $L.b3.txt 2>&1
  $P build_trajectories.py --controls FR DE ES --tag es > $L.b4.txt 2>&1
  $P build_trajectories.py --world --near-k 10 --tag world_near10 > $L.b5.txt 2>&1
  $P build_trajectories.py --world --career-start $CS --tag world_career > $L.b6.txt 2>&1
  [ $F = 31 ] && $P build_trajectories.py --max-team 20 --tag team20 > $L.b7.txt 2>&1
  W=$D/trajectories_world.csv
  # main specification (France + Germany, world-wide citation measure)
  $P -u estimate.py --input $W --out ${R}_world --event-study > $L.e1.txt 2>&1
  $P -u estimate.py --input $W --out ${R}_world --placebo-year 2007 >> $L.e1.txt 2>&1
  $P -u effect_sizes.py --input $W --results ${R}_world >> $L.e1.txt 2>&1
  $P -u reduced_form.py --input $W --out ${R}_world >> $L.e1.txt 2>&1
  $P -u counterfactual.py --input $W --results ${R}_world >> $L.e1.txt 2>&1
  $P -u relax_2016.py --input $W --out ${R}_world >> $L.e1.txt 2>&1
  $P -u rich_model.py --input $W --out ${R}_world >> $L.e1.txt 2>&1
  $P -u composition_check.py --input $W --out ${R}_world >> $L.e1.txt 2>&1
  $P -u composition_decompose.py --input $W --out ${R}_world --n-boot 100 >> $L.e1.txt 2>&1
  $P -u first_entry.py --timing >> $L.e1.txt 2>&1
  # + Spain, study-country measure, nearby = 10 most similar topics
  $P -u estimate.py --input $D/trajectories_world_es.csv --out ${R}_world_es --event-study > $L.e2.txt 2>&1
  $P -u estimate.py --input $D/trajectories_world_es.csv --out ${R}_world_es --placebo-year 2007 >> $L.e2.txt 2>&1
  $P -u effect_sizes.py --input $D/trajectories_world_es.csv --results ${R}_world_es >> $L.e2.txt 2>&1
  $P -u reduced_form.py --input $D/trajectories_world_es.csv --out ${R}_world_es >> $L.e2.txt 2>&1
  $P -u estimate.py --input $D/trajectories.csv --out $R > $L.e3.txt 2>&1
  $P -u estimate.py --input $D/trajectories.csv --out $R --placebo-year 2007 >> $L.e3.txt 2>&1
  $P -u estimate.py --input $D/trajectories_es.csv --out ${R}_es > $L.e4.txt 2>&1
  $P -u estimate.py --input $D/trajectories_es.csv --out ${R}_es --placebo-year 2007 >> $L.e4.txt 2>&1
  $P -u estimate.py --input $D/trajectories_world_near10.csv --out ${R}_world_near10 > $L.e5.txt 2>&1
  $P -u estimate.py --input $D/trajectories_world_near10.csv --out ${R}_world_near10 --placebo-year 2007 >> $L.e5.txt 2>&1
  $P -u reduced_form.py --input $D/trajectories_world_near10.csv --out ${R}_world_near10 >> $L.e5.txt 2>&1
  # career stage from the true career start
  C=$D/trajectories_world_career.csv
  $P -u estimate.py --input $C --out ${R}_world_career --n-boot 100 --by-career > $L.e6.txt 2>&1
  $P -u ddd_checks.py --input $C --out ${R}_world_career >> $L.e6.txt 2>&1
  $P -u ddd_checks.py --input $C --out ${R}_world_career --placebo-year 2007 >> $L.e6.txt 2>&1
  $P -u reduced_form.py --input $C --out ${R}_world_career >> $L.e6.txt 2>&1
  # outcomes computed from the raw records
  $P -u outcomes_citations.py > $L.o1.txt 2>&1
  $P -u reconcile_abramo.py > $L.o2.txt 2>&1
  $P -u long_run.py > $L.o3.txt 2>&1
  $P -u return_value.py > $L.o4.txt 2>&1
  if [ $F = 31 ]; then   # physics robustness (Table S4)
    $P -u estimate.py --input data/trajectories.csv --out results_g08 --gamma 0.8 > $L.r.txt 2>&1
    $P -u estimate.py --input data/trajectories.csv --out results_g095 --gamma 0.95 >> $L.r.txt 2>&1
    $P -u estimate.py --input data/trajectories.csv --out results_balanced --balanced >> $L.r.txt 2>&1
    $P -u estimate.py --input data/trajectories_team20.csv --out results_team20 >> $L.r.txt 2>&1
  fi
  echo "$(date) field $F rebuilt" >> logs/latest/progress.txt
}
for F in 31 22 13 16; do one $F & done
wait
# ---------- everything beyond the Italy core ----------
export OPENALEX_API_KEY=$(tr -d '[:space:]' < ~/.openalex.key)
more() {
  F=$1; export CT_FIELD_ID=$F
  D=data; R=results; [ $F != 31 ] && D=data_field$F && R=results_field$F
  L=logs/latest/m$F
  # more outcomes from raw records and reference lists
  $P -u outcomes_citations.py --input $D/trajectories_es.csv --controls FR DE ES --tag es > $L.o5.txt 2>&1
  $P -u outcomes_citations.py --lead 1 > $L.o6.txt 2>&1
  $P -u novelty.py > $L.n1.txt 2>&1
  $P -u novelty.py --input $D/trajectories_es.csv --controls FR DE ES --tag es > $L.n2.txt 2>&1
  $P -u dose_response.py --input $D/trajectories_world.csv --out ${R}_world --n-boot 100 > $L.d.txt 2>&1
  if [ $F != 16 ]; then
    # control countries (Table S15)
    for SET in "FR" "DE" "ES" "NL" "PT" "FR DE ES NL PT"; do
      TAG="world_ctrl_$(echo $SET | tr ' ' '_')"
      $P build_trajectories.py --world --controls $SET --tag $TAG > $L.c_$TAG.txt 2>&1
      $P -u estimate.py --input $D/trajectories_$TAG.csv --out ${R}_$TAG --n-boot 100 >> $L.c_$TAG.txt 2>&1
      $P -u reduced_form.py --input $D/trajectories_$TAG.csv --out ${R}_$TAG >> $L.c_$TAG.txt 2>&1
    done
    # each country treated as if reformed (true career start)
    $P build_trajectories.py --world --career-start $CS --controls FR DE ES NL PT --tag world_career_ctrl5 > $L.ps.txt 2>&1
    $P -u placebo_space.py --input $D/trajectories_world_career_ctrl5.csv --out ${R}_world_career_placebo_space --n-boot 100 >> $L.ps.txt 2>&1
    # Poland and Romania
    for C in PL RO; do
      $P build_trajectories.py --world --treated $C --tag world_$C > $L.$C.txt 2>&1
      $P -u estimate.py --input $D/trajectories_world_$C.csv --out ${R}_world_$C --n-boot 100 --event-study >> $L.$C.txt 2>&1
      $P -u estimate.py --input $D/trajectories_world_$C.csv --out ${R}_world_$C --n-boot 100 --placebo-year 2007 >> $L.$C.txt 2>&1
      $P -u reduced_form.py --input $D/trajectories_world_$C.csv --out ${R}_world_$C >> $L.$C.txt 2>&1
    done
  fi
  # India and Russia
  mkdir -p results_india results_russia
  for C in IN RU; do
    $P build_trajectories.py --world --treated $C --tag world_$C > $L.$C.txt 2>&1
    $P build_trajectories.py --world --treated $C --controls FR DE ES --tag world_${C}_es >> $L.$C.txt 2>&1
    $P -u estimate.py --input $D/trajectories_world_$C.csv --out ${R}_world_$C --n-boot 100 --event-study >> $L.$C.txt 2>&1
    $P -u estimate.py --input $D/trajectories_world_$C.csv --out ${R}_world_$C --n-boot 100 --placebo-year 2007 >> $L.$C.txt 2>&1
    $P -u estimate.py --input $D/trajectories_world_${C}_es.csv --out ${R}_world_${C}_es --n-boot 100 --event-study >> $L.$C.txt 2>&1
    $P -u estimate.py --input $D/trajectories_world_${C}_es.csv --out ${R}_world_${C}_es --n-boot 100 --placebo-year 2007 >> $L.$C.txt 2>&1
    $P -u reduced_form.py --input $D/trajectories_world_$C.csv --out ${R}_world_$C >> $L.$C.txt 2>&1
    OUTD=results_india; [ $C = RU ] && OUTD=results_russia
    $P -u first_entry.py --treated $C --out ${R}_world_$C --save-choices $OUTD/choices_$D.csv.gz >> $L.$C.txt 2>&1
  done
  echo "$(date) field $F extra done" >> logs/latest/progress.txt
}
for F in 31 22 13 16; do more $F & done
wait
# economics (field 20; no citation thresholds; study-country measure)
export CT_FIELD_ID=20; L=logs/latest/f20
$P build_trajectories.py > $L.b.txt 2>&1
$P build_trajectories.py --controls FR DE ES --tag es >> $L.b.txt 2>&1
$P build_trajectories.py --career-start $CS --tag career >> $L.b.txt 2>&1
$P -u estimate.py --input data_field20/trajectories.csv --out results_field20 --event-study --by-career > $L.e.txt 2>&1
$P -u estimate.py --input data_field20/trajectories.csv --out results_field20 --placebo-year 2007 >> $L.e.txt 2>&1
$P -u effect_sizes.py --input data_field20/trajectories.csv --results results_field20 >> $L.e.txt 2>&1
$P -u estimate.py --input data_field20/trajectories_es.csv --out results_field20_es --event-study >> $L.e.txt 2>&1
$P -u estimate.py --input data_field20/trajectories_es.csv --out results_field20_es --placebo-year 2007 >> $L.e.txt 2>&1
$P -u estimate.py --input data_field20/trajectories_career.csv --out results_field20_career --n-boot 100 --by-career >> $L.e.txt 2>&1
$P -u ddd_checks.py --input data_field20/trajectories_career.csv --out results_field20_career >> $L.e.txt 2>&1
$P -u ddd_checks.py --input data_field20/trajectories_career.csv --out results_field20_career --placebo-year 2007 >> $L.e.txt 2>&1
$P -u long_run.py >> $L.e.txt 2>&1
# affiliations, mechanisms, stacked tests (India, Russia), institution type (Italy)
$P -u fetch_affiliations.py --suffix IN --out affiliations_in.csv.gz > logs/latest/affil_in.txt 2>&1
$P -u india_mechanism.py --out results_india > logs/latest/in_mech.txt 2>&1
$P -u india_stacked.py --out results_india --groups results_india/india_groups.csv > logs/latest/in_stacked.txt 2>&1
$P -u fetch_affiliations.py --suffix RU --out affiliations_ru.csv.gz > logs/latest/affil_ru.txt 2>&1
$P -u russia_mechanism.py --out results_russia > logs/latest/ru_mech.txt 2>&1
$P -u india_stacked.py --suffix RU --covered-label 5-100 --out results_russia --groups results_russia/russia_groups.csv > logs/latest/ru_stacked.txt 2>&1
$P -u fetch_affiliations.py > logs/latest/affil_it.txt 2>&1
for F in 31 22 13 16; do export CT_FIELD_ID=$F; D=data; R=results; [ $F != 31 ] && D=data_field$F && R=results_field$F
  $P -u institution_split.py --input $D/trajectories_world_career.csv --out ${R}_world_career --n-boot 100 > logs/latest/inst_$F.txt 2>&1; done
# author metadata and heterogeneity (gender, region, ORCID)
$P -u fetch_authors.py > logs/latest/authors.txt 2>&1
for F in 31 22 13; do export CT_FIELD_ID=$F; D=data; R=results; [ $F != 31 ] && D=data_field$F && R=results_field$F
  $P -u heterogeneity.py --input $D/trajectories_world.csv --out ${R}_world > logs/latest/het_$F.txt 2>&1; done
# co-authorship and journals
for C in IT IN RU; do $P -u coauthors.py --treated $C > logs/latest/coauthors_$C.txt 2>&1; done
$P -u coauthors.py --treated IN --groups results_india/india_groups.csv --covered-label UGC-covered --out results_coauthors_groups > logs/latest/coauthors_groups_IN.txt 2>&1
$P -u coauthors.py --treated RU --groups results_russia/russia_groups.csv --covered-label 5-100 --out results_coauthors_groups > logs/latest/coauthors_groups_RU.txt 2>&1
PYTHON=$P bash run_venues.sh > logs/latest/venues.txt 2>&1
# threshold vs committee rules; Spain
$P -u stacked_rules.py > logs/latest/stacked_rules.txt 2>&1
for F in 31 22 13; do export CT_FIELD_ID=$F; D=data; R=results; [ $F != 31 ] && D=data_field$F && R=results_field$F
  $P -u spain_check.py --input $D/trajectories_world_ctrl_FR_DE_ES_NL_PT.csv --out ${R}_world_spain > logs/latest/spain_$F.txt 2>&1; done

$P paper_tables.py > logs/latest/tables.txt 2>&1
$P paper_figures.py > logs/latest/figures.txt 2>&1
echo "$(date) REBUILD DONE" >> logs/latest/progress.txt
