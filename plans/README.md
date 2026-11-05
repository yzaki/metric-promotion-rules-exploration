# Time-stamped analysis plan: replication (biochemistry) and placebo (economics) fields

Accompanies: "Metric-based promotion rules reduced scientists' movement between neighbouring research topics" (N. AlDahoul).

## What this deposit is

`PREREGISTRATION_new_fields_2026-11-04.md` is the analysis plan for the two fields added after the
physics and engineering results: OpenAlex field 13 (Biochemistry, Genetics and Molecular Biology; the
replication field) and field 20 (Economics, Econometrics and Finance; the field without citation
thresholds). It states the hypotheses, specifications and decision rules. The file is deposited unchanged.

It is a **time-stamped analysis plan, not a preregistration in the strict sense**: it was written before
any data from these two fields were downloaded, but it was deposited publicly afterwards. The evidence for
the order of events is local file metadata, listed below.

## Timeline (Gulf Standard Time, UTC+4)

| Event | Time |
|---|---|
| Plan written (file created; never modified since) | 2026-11-04 08:05:05 |
| Download logs started (`logs/fetch_field13.txt`, `logs/fetch_field20.txt`) | 2026-11-04 08:35:13 |
| First economics data file downloaded (`data_field20/raw/works_IT_1998.csv.gz`) | 2026-11-04 08:35:56 |
| First biochemistry data file downloaded (`data_field13/raw/works_IT_1998.csv.gz`) | 2026-11-04 08:35:57 |
| Public deposit (this OSF entry) | date of deposit |

SHA-256 of the plan file:
`6F8A65399827BE528F5C5D7A51D219BA20E432594BC58BA0FEBC3CBA16767E5F`

## Second plan: chemistry (field 16)

`PREREGISTRATION_chemistry_2026-11-05.md` fixes hypotheses C1–C5 and decision rules for chemistry, chosen
as the field most similar to engineering after the results for the other fields were known.

| Event | Time (UTC+4) |
|---|---|
| Plan written (file created; never modified since) | 2026-11-05 03:55:11 |
| Chemistry download started (`logs/fetch_field16.txt`, first line) | 2026-11-05 03:55:29 |

Only article counts per country were queried before the plan. SHA-256:
`AD53CFF5E1D67C24F7195CA20CEEFF9BDCC8EEFD9B359AF8C808E2DB1B0D62AD`.
Outcome (paper, Table S26): C1 and C2 met; C3 and C5 consistent; C4 not supported. The plan did not anticipate
pre-trends under both control groups; the paper reports that the chemistry decline began before the reform.

## Deviations from the plan, reported in the paper

1. **H-R3 (effect larger for early and mid-career than for senior scientists).** The plan measured career
   stage as years since a scientist's first article in the downloaded data, which start in 1998. With that
   measure no scientist is in the 16+ year stage before the reform, so the H-R3 comparison was not a valid
   difference-in-differences. The paper reports the result as specified, explains the problem, and reports
   the corrected test using each scientist's first publication year in the full Microsoft Academic Graph
   record (via SciSciNet).
2. **Citation measure.** The plan made citation potential from the downloaded countries the primary measure
   and the world-wide measure secondary ("added if budget allows"). The paper leads with the world-wide
   measure in every field, because the four-country measure failed its placebo test in physics; the
   pre-specified biochemistry estimate is reported alongside.
3. **Within-career decomposition.** Not in the plan: the paper reports that the biochemistry decline came
   from scientists entering Italian research rather than from those already in it.
