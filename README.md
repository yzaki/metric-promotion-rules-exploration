# Replication package: "Scientists moved less between neighbouring research topics after Italy introduced metric-based promotion rules"

Nouar AlDahoul. Code, analysis-ready data and result tables for every estimate, figure and table
in the paper and its Supplementary Materials.

## What is included

| Folder / file | Content |
|---|---|
| `*.py`, `*.sh` | All analysis code (Python) |
| `data/` (Physics), `data_field22/` (Engineering), `data_field13/` (Biochemistry), `data_field20/` (Economics), `data_field16/` (Chemistry) | Analysis-ready yearly choices of every sampled scientist (`trajectories*.csv.gz`), one file per specification |
| `results*/` | Every result table (CSV) behind the paper's figures and tables, and diagnostic plots |
| `career_start/career_start.tsv.gz` | True career start per scientist: first publication year in the matched Microsoft Academic Graph record (`mag_first_year`), with match diagnostics; author identifiers only |
| `jubail/` | The SciSciNet matching job (`match_career.py`, run on a cluster with the SciSciNet tables) |

**Not included:** raw OpenAlex records (about 1 GB; CC0, re-downloadable with the `fetch_*.py` scripts),
author names and inferred gender (personal data), and the SciSciNet subset (CC BY; obtainable from
Figshare, see below). Scientists appear only as OpenAlex author identifiers.

### Trajectory files

One row per decision (consecutive active years of a scientist): `author_id` (OpenAlex), `country`,
`group` (IT or CTRL), `year`, state in year t (`s_tier`: citation tier 0/1/2, `s_tenure`: time in topic
0/1/2, `s_career`: career stage 0/1/2), `action` (stay / near / far), and the state in the next active year
(`ns_*`). Suffixes:

| Suffix | Specification |
|---|---|
| (none) | Italy vs France + Germany; citation tiers from the study countries |
| `_es` | + Spain as a control |
| `_world`, `_world_es` | citation tiers from world-wide citation rates (main specification) |
| `_world_near10` | nearby = the ten most similar topics (instead of same subfield) |
| `_world_ctrl_XX` | one control country (FR, DE, ES, NL, PT) or all five |
| `_team20` | Physics, articles with at most 20 authors |
| `_world_career`, `_world_career_ctrl5`, `_career` (Economics) | career stage from the true career start; matched scientists only |
| `_world_PL`, `_world_RO` | Poland or Romania as the treated country (stored as `group` = IT) vs France + Germany, Italy excluded |

**Career stage.** In the files without `career`, `s_career` counts years since the first article in our
data, which begin in 1998, so no scientist reaches the 16+ stage before 2014. It is a valid state variable
(measured identically in every country) but must not be used for career-stage comparisons; use the
`_career` files for those.

## Reproduce the estimates

```bash
python -m venv .venv
.venv\Scripts\activate          # macOS/Linux: source .venv/bin/activate
pip install -r requirements.txt
gunzip -k data*/trajectories*.csv.gz            # or decompress with any tool
```

Fields are selected with the environment variable `CT_FIELD_ID` (31 Physics = default, 22 Engineering,
13 Biochemistry, 20 Economics). Example for the main Physics result:

```bash
python estimate.py --input data/trajectories_world.csv --out results_world --event-study --by-career
python estimate.py --input data/trajectories_world.csv --out results_world --placebo-year 2007
python effect_sizes.py --input data/trajectories_world.csv --results results_world
```

For Engineering: `set CT_FIELD_ID=22` (Windows) or `export CT_FIELD_ID=22`, then the same commands with
`data_field22/` and `results_field22_world`. Bootstrap draws use a fixed seed (42), so results reproduce
exactly with the same library versions.

## Map from the paper to code and results

| Paper item | Script | Result files |
|---|---|---|
| Fig. 1B, Table S2 (main effects) | `estimate.py` | `results*_world/did_main.csv`, `results*_world_es/` |
| Fig. 1C, Table S6 (effect in choice shares) | `effect_sizes.py` | `results*_world/effect_sizes.csv` |
| Fig. 2A–C (event studies) | `estimate.py --event-study` | `results*_world_es/event_study.csv` |
| Fig. 2D, Table S5 (career stages, true career start) | `run_career.sh` (`estimate.py --by-career`, `ddd_checks.py`, `career_bands.py`) | `results*_world_career/` |
| Fig. 3, Tables S2–S3 (citation weight, placebo) | `estimate.py` | `did_main.csv`, `did_placebo_2007.csv` (world and four-country folders) |
| Table S4 (robustness, Physics) | `estimate.py` (`--gamma`, `--balanced`) | `results_g08/`, `results_g095/`, `results_balanced/`, `results_team20/`, `results_es/` |
| Fig. 4A, Table S7 (output, citations) | `outcomes_citations.py` | `results*/outcomes_citations.csv` |
| Fig. 4B (new references) | `novelty.py` (needs reference lists, `fetch_references.py`) | `results*/novelty.csv` |
| Fig. 4C (specialisation, Abramo et al.) | `reconcile_abramo.py` (needs raw data) | `results*/reconcile_abramo.csv` |
| Fig. 4D (disruption, atypicality) | `disruption.py` (needs SciSciNet subset) | `results*/disruption.csv` |
| Table S8 (distance to thresholds) | `dose_response.py` (needs raw data) | `results*_world/dose_response.csv` |
| Table S9 (longer-run outcomes) | `long_run.py` (needs raw data) | `results*/long_run.csv` |
| Table S10 (validation) | `reduced_form.py`, `rich_model.py`, `build_trajectories.py --near-k 10` | `reduced_form.csv`, `rich_model_effect.csv`, `results*_world_near10/` |
| Table S11 (out-of-sample fit) | `rich_model.py`, `model_fit.py` | `rich_model_fit.csv`, `model_fit.csv` |
| Table S12 (2016 relaxation) | `relax_2016.py` | `results*_world/relax_2016.csv` |
| Table S13 (counterfactual rules) | `counterfactual.py` | `results*_world/counterfactual.csv` |
| Table S14 (gender, region, ORCID) | `heterogeneity.py` (needs `fetch_authors.py`) | `results*_world/heterogeneity.csv` |
| Table S15 (control countries) | `run_controls.sh` | `results*_world_ctrl_*/` |
| Fig. 5 (first entries vs returns; who changed) | `paper_figures.py` (`main_fig5`) | `first_entry.csv`, `rank_exposure.csv`, `sector_thresholds.csv`, `institution_split.csv` |
| Table S17 (within careers vs composition) | `composition_check.py`, `composition_decompose.py` | `results*_world/composition_*.csv` |
| Table S18 (each country treated as if reformed) | `placebo_space.py` (in `run_career.sh`) | `results*_world_career_placebo_space/` |
| Table S19 (first entries and returns) | `first_entry.py` (needs raw data) | `results*_world/first_entry.csv` |
| Table S20 (Poland, Romania) | `run_newcountries.sh` | `results*_world_PL/`, `results*_world_RO/` |
| Table S21 (what followed a return) | `return_value.py` (needs raw data) | `results*_world/return_value_lead2.csv` |
| Table S22 (threshold vs committee rules, exploratory) | `stacked_rules.py`, `spain_check.py` | `results_stacked_rules/`, `results*_world_spain/` |
| Table S23 (academic rank in 2011) | `rank_exposure.py`, `register_split.py` (need the MUR staff register exports and author names; not distributed) | `results*_world_career/rank_exposure.csv`, `register_split.csv` |
| Table S24 (distance to own sector bar) | `sector_thresholds.py` (needs the register, raw data and ANVUR 2012 medians: roars.it/wp-content/uploads/2012/08/Mediane-ASN-2012-in-formato-Excel.zip) | `results*_world_career/sector_thresholds.csv` |
| Table S25 (institution type 2009-12) | `fetch_affiliations.py`, `institution_split.py` | `results*_world_career/institution_split.csv` |
| Table S26 (chemistry, specified in advance) | `run_chemistry_a.sh`, `run_chemistry_b.sh`; plan `PREREGISTRATION_chemistry_2026-11-05.md` | `results_field16_world*/` |
| True career start | `export_author_papers.py`, `jubail/match_career.py` (needs author names and SciSciNet) | `career_start/career_start.tsv.gz` |
| Economics placebo field | `estimate.py` with `CT_FIELD_ID=20` | `results_field20*/` |
| All figures / all tables | `paper_figures.py`, `paper_tables.py` | written to `../paper_overleaf/` (adjust `OUT`) |

Folder names: `results` = Physics, `results_field22` = Engineering, `results_field13` = Biochemistry,
`results_field20` = Economics.

## Rebuild everything from raw data (optional)

1. Free OpenAlex API key (https://openalex.org/settings/api); set `OPENALEX_API_KEY`.
2. `python fetch_openalex.py --countries IT FR DE ES` (per field via `CT_FIELD_ID`; NL, PT for Table S15).
3. `python fetch_world_citations.py` (world-wide citation rates), `python fetch_references.py`
   (reference lists), `python fetch_authors.py` (author metadata for Table S14).
4. `python build_trajectories.py --world [--controls FR DE ES] [--tag ...]`.
5. SciSciNet_Papers (Lin et al. 2023, Figshare collection 6076908, file 38839110), filtered to the
   OpenAlex work ids of the sample (OpenAlex W-ids of MAG-era works equal MAG PaperIDs).
6. True career start: `python export_author_papers.py`, then run `jubail/match_career.py` next to
   SciSciNet_PaperAuthorAffiliations (file 36139278), SciSciNet_Authors (file 36139323) and
   SciSciNet_Papers; then `bash run_career.sh`.
7. Poland and Romania: `python fetch_openalex.py --countries RO PL` per field, then `bash run_newcountries.sh`.

The raw download used the OpenAlex API in November 2026; OpenAlex updates continuously, so a fresh
download may differ slightly.

## Licences

Code: MIT (see LICENSE). Data derived from OpenAlex (CC0). SciSciNet metrics are CC BY (Lin et al. 2023).

## Citation

AlDahoul, N. Metric-based promotion rules reduce scientists' exploration of neighbouring topics (2026).
