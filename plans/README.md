# Time-stamped analysis plan: replication (biochemistry) and placebo (economics) fields

Accompanies: "Italian scientists moved less among neighboring research topics after a metric promotion reform" (N. AlDahoul and Y. Zaki; prepared for PNAS Nexus).

## What this deposit is

`PREREGISTRATION_new_fields_2026-11-04.md` is the analysis plan for the two fields added after the
physics and engineering results: OpenAlex field 13 (Biochemistry, Genetics and Molecular Biology; the
replication field) and field 20 (Economics, Econometrics and Finance; the field without citation
thresholds). It states the hypotheses, specifications and decision rules. The file is deposited unchanged at https://osf.io/m3xgh.

It is a **time-stamped analysis plan, not a preregistration in the strict sense**: it was written before
any data from these two fields were downloaded, but it was deposited publicly on 9 November 2026 at https://osf.io/m3xgh, after the analyses (https://osf.io/m3xgh). The evidence for
the order of events is local file metadata and the original fetch logs, listed below. All times in this file follow one
timeline, the one used in the paper (main text, Methods; SI Methods, Analysis plans):

- plan times are the file times of the plan files supplied from the authors' original working repository. They are stored at
  two-second resolution and are therefore up to two seconds later than the file-creation times given in earlier versions of
  this README (08:05:05, 03:55:11 and 07:00:10); the order of events is the same under either set;
- download start times are the "started" lines of the original fetch logs (`logs/original_download/`) where they exist;
  the biochemistry and economics logs have no start line, so for them the first data-file times are used;
- data-file times are those of `data_meta/raw_manifest_original_download.csv`.

## Timeline (Gulf Standard Time, UTC+4)

| Event | Time |
|---|---|
| Plan written (file time; never modified since) | 2026-11-04 08:05:06 |
| Download logs (`logs/original_download/fetch_field13.txt`, `fetch_field20.txt`) | no start line |
| First economics data file (`data_field20/works_IT_1998.csv.gz`) | 2026-11-04 08:36:00 |
| First biochemistry data file (`data_field13/works_IT_1998.csv.gz`) | 2026-11-04 08:36:24 |
| Public deposit (OSF) | 9 November 2026, https://osf.io/m3xgh |

SHA-256 of the plan file:
`6F8A65399827BE528F5C5D7A51D219BA20E432594BC58BA0FEBC3CBA16767E5F`

## Second plan: chemistry (field 16)

`PREREGISTRATION_chemistry_2026-11-05.md` fixes hypotheses C1–C5 and decision rules for chemistry, chosen
as the field most similar to engineering after the results for the other fields were known.

| Event | Time (UTC+4) |
|---|---|
| Plan written (file time; never modified since) | 2026-11-05 03:55:12 |
| Chemistry download started (`logs/original_download/fetch_field16.txt`, first line) | 2026-11-05 03:55:29 |
| First chemistry data file (`data_field16/works_IT_1998.csv.gz`) | 2026-11-05 03:55:56 |

Only article counts per country were queried before the plan. SHA-256:
`AD53CFF5E1D67C24F7195CA20CEEFF9BDCC8EEFD9B359AF8C808E2DB1B0D62AD`.
Outcome (paper, Table S26, latest download): C1 and C2 met; C3 not supported (+0.00 [-0.28, +0.27]); C4 not supported; C5 consistent; the mechanism rule (at least two of C3-C5 supported or consistent) is not met. On the original download C3 and C5 were consistent and the rule was met (Table S35). An earlier version of this README and of Table S26 labeled C3 "consistent" on the latest download; that label was carried over from the original download and has been corrected. The plan did not anticipate
pre-trends under both control groups; the paper reports that the chemistry decline began before the reform.

## Third plan: India as a second treated country

`PREREGISTRATION_india_2026-11-05.md` fixes hypotheses I1–I4, a pre-trend rule and decision rules for India
(University Grants Commission Regulations 2010), chosen after all Italian results were known.

| Event | Time (UTC+4) |
|---|---|
| Plan written (file time; never modified since) | 2026-11-05 07:00:12 |
| Indian download started (`logs/original_download/fetch_india.txt`, first line) | 2026-11-05 07:00:24 |
| First Indian data file (`data/works_IN_1998.csv.gz`) | 2026-11-05 07:00:52 |

Only article counts per field were queried before the plan. SHA-256:
`2F6483B083EA70A7BA005A90E06ED724FF92834C822BDE1C04899136BE374E79`.
Outcome (paper, Table S27, latest download of 7-8 November 2026; first download in Table S35): I1 not supported
(stacked −0.3 pp [−1.0, +0.4]); I2 met (+0.4 [−0.5, +1.3]); I3 not supported (returns rose, +1.2 pp [+0.6, +1.7]);
I4 not supported (+1.5 pp [+0.2, +2.9]: covered universities declined less, the opposite of the prediction; main institution by OpenAlex records, as corrected after an external audit); physics not interpretable under the pre-trend rule. (Values as in Table S35,
latest download, current build; the first download gives the same verdicts.)
India does not replicate the Italian result.

## Deviations from the plan, reported in the paper

1. **H-R3 (effect larger for early and mid-career than for senior scientists).** The plan measured career
   stage as years since a scientist's first article in the downloaded data, which start in 1998. With that
   measure no scientist is in the 16+ year stage before the reform, so the H-R3 comparison was not a valid
   difference-in-differences. The paper reports the result as specified, explains the problem, and reports
   the corrected test using each scientist's first publication year in the full Microsoft Academic Graph
   record (via SciSciNet).
2. **Citation measure.** The plan made citation potential from the downloaded countries the primary measure
   and the worldwide measure secondary ("added if budget allows"). The paper leads with the worldwide
   measure in every field, because the four-country measure failed its placebo test in physics; the
   pre-specified biochemistry estimate is reported alongside.
3. **Within-career decomposition.** Not in the plan. On the first download the biochemistry decline came
   mostly from scientists entering Italian research; on the latest download (the one the paper reports) the
   same scientists changed (Table S17).


## Deviations and additions after the plans (November 2026 revision)

- The split of nearby moves into returns and first entries was first specified in the India plan (5 November 2026, 07:00) and is exploratory for Italy (physics, engineering, biochemistry, chemistry).
- Gap returns (no article in the destination topic in the decision year) and concurrent returns were added in the revision (7 November 2026); no plan specified them. They were estimated on OpenAlex records re-downloaded in November 2026.
- The pre-trend rule of the India and Russia plans was applied to the Italian fields after the fact (Table S33): chemistry would not be interpretable as a policy effect under it, and physics passes it only at the margin.
- The Italy-minus-Russia and Italy-minus-India comparisons of returns (Table S34) were not specified in advance.
- Main affiliation (I4, R4): the plans define groups by the main affiliation in 2009-12. The first implementation classified each scientist's affiliation records and took the most frequent class, and matched Russia's 5-100 universities by name patterns that also caught four unrelated institutions and missed MISiS. After an external audit (10 November 2026) the scripts take each scientist's main institution (most records; ties to the most recent) and list the 21 universities by OpenAlex ID. I4 and R4 remain not supported on both downloads (Table S35).
- The plans were deposited publicly on 9 November 2026, after the analyses, at https://osf.io/m3xgh (hashes match those listed above).
- The reported results use a second OpenAlex download (7-8 November 2026), made after all results on the first (original) download (3-5 November) were known. The pre-specified tests listed in Table S35, including chemistry C3-C5 and the chemistry mechanism rule, are reported on both downloads (`download_comparison.py`; only the per-field pre-trend verdicts are not repeated there); all verdicts in that table are identical except those marked with an asterisk there (engineering's all-returns estimate; biochemistry's model-free nearby moves; the engineering and chemistry distant-jump weights; chemistry C3 and the chemistry mechanism rule; and Russia's replication rule, which is not met on the first download (decline driven by engineering, which fails the pre-trend rule) and met on the second (driven by physics); the definition of the fields that drive the decline is our reading of the plan. The 2011 staff-register analyses (Tables S23-S25) were later rerun on the latest download with register exports supplied by the authors (see "Round-13 additions").

## Fourth plan: Russia as a third treated country

`PREREGISTRATION_russia_2026-11-05.md` fixes hypotheses R1-R3, the pre-trend rule and the replication rule
for Russia (Project 5-100), written after the Italian and Indian results were known.
SHA-256: `5F5C43CFCA725916BBB58A127E40E1142E619B7193D55AD40EAFCA7073858E3A`.

| Event | Time (UTC+4) |
|---|---|
| Plan written (file time; never modified since) | 2026-11-05 11:54:36 |
| Russian download started (`logs/original_download/fetch_russia.txt`, first line) | 2026-11-05 11:54:50 |
| First Russian data file (`data/works_RU_1998.csv.gz`) | 2026-11-05 11:55:34 |

The plan cites `logs/fetch_russia.txt` for the order of events; that log and the field 13/16/20 and India fetch
logs cited above are now in `logs/original_download/` (copied from the authors' original working repository,
supplied on 9 November 2026). The definition of "the fields that drive the decline" used for the replication
rule is our reading of the plan (Table S35).

## Fifth plan: co-authorship and journals

`PREREGISTRATION_venues_coauthors_2026-11-05.md` fixes the predictions for co-authorship and journal
outcomes (Tables S29-S32), written before these outcomes were computed.
SHA-256: `79D15BBDD98BEFE50B60C371F6B6C151F653F5C9C818317A0E2045E741BD4809`.
Under the 2007 placebo check applied to India and Russia, the Italian co-authorship comparisons are also not
interpretable as policy effects (Table S32).

## Round-9 addition (8 November 2026)

- The model-free annual pre-test for Russia and India first reported in Table S38 used the before and after
  years only; the test applied to Italy (Table S33) uses all years 2004-18. Table S38 now reports both, and
  the full-year version for every move type (`run_round9_pretest.sh`, `country_pretrend.py`). Under the
  full-year test Russian engineering passes for nearby moves (p = 0.074; 0.017 in the earlier version) and
  fails for gap returns (p = 0.011); Indian chemistry fails for gap returns (p = 0.004). Fig. 5 now reads
  its hollow markers from these tests.

## Round-10 and round-11 additions (8 November 2026), added after the results
- Fig. 5 and Table S38 apply Italy's full model-free timing check to Russia and India (joint pre-2009 test or
  2007 placebo, for every move type). This makes Russian engineering and Indian physics nearby moves hollow.
- Table S34 adds Italy-Russia and Italy-India comparisons pooled over the fields that pass the timing check in
  both countries (the round-10 version pooled each country over its own passing fields and has been
  replaced). In the current build (latest download, round 12 onwards), pooled over the fields passing the
  timing check in both countries, the Italy-minus-Russia difference in all returns is -0.8 [-1.6, +0.04]
  (p = 0.061), so it is no longer significant (Table S34).
- Russia against Spain, the Netherlands and Portugal (`run_round11_russia_esnlpt.sh`, `first_entry.py
  --controls`): against these controls Russia's nearby moves (-0.4 [-1.1, +0.2]) and all returns (-0.3
  [-0.8, +0.2]) do not fall significantly, so Russia's partial replication holds against France and Germany
  only (Table S34).

## Round-12 re-download (8 November 2026)
- The 7-8 November rebuild had reused Italian, French and German works for physics, engineering and
  biochemistry fetched on 5 November (`fetch_openalex.py` skips existing files). Between 5 and 7 November
  OpenAlex reassigned the primary topic of many articles (16-23% of engineering and biochemistry articles and
  6-9% of physics articles left the field), so that build combined two topic classifications. These files were
  downloaded again on 8 November and every analysis rerun (`run_round12_refetch.sh`); results on the 5 November
  files were kept outside this package (`snapshot_r11`, not distributed). The round-9 note above (Russian engineering p = 0.074) refers to the earlier
  build; on the current build Russian engineering nearby moves fail the full-year test (Table S38).
- Timing checks against Spain + Netherlands + Portugal and Netherlands + Portugal added
  (`run_round12_controls_timing.sh`; Table S38, last panel).
- S35 verdicts that differ between the original and the latest download are unchanged: Russia's replication rule
  and engineering's all-returns estimate.

## Round-13 additions (8 November 2026), after the main analysis
- Staff-register analyses (Tables S23-S25, Fig. 2B-C) rerun on the latest download with the 2011 MUR register
  exports supplied by the authors (`data_meta/staff_register/`, SHA-256 in `MANIFEST.sha256`; not distributed);
  `run_round13_register.sh`.
- Table S39 (`run_round13_new.sh`, `reclass_check.py`, `first_entry.py --stable-only`): any move, distant jumps and
  all returns; estimates on articles in the field on both 5 and 8 November; balance of the reclassification.
- `data_meta/raw_manifest.csv` (`raw_manifest.py`): every raw works file with download time, SHA-256, articles and
  the live OpenAlex count on 8 November; all files are within a few percent of the live counts (the superseded
  5 November engineering files were 16-17% off).
- Table S35 adds model-free nearby moves per field; biochemistry's is significant only on the latest download.

## Status note (9 November 2026)
Entries above are dated and record what was known at each step; where a later build changed a number, the current
value is the one in the paper's Table S35 (pre-specified tests on both downloads) and Table S34. The bootstrap
behind Tables S24 and S26 (C5) uses 300 scientist resamples (`n_boot` column in `sector_thresholds.csv`; logs in
`logs/r13/sector4_*.txt`); Table S23 uses 100.

## Original download: logs, raw files and git history (added 9 November 2026)
The authors supplied their original working repository. From it:
- `logs/original_download/fetch_*.txt`: the original fetch logs. The timeline is the one in the tables above (UTC+4):
  biochemistry/economics plan 4 Nov 08:05:06, first data files 08:36:00 (economics) and 08:36:24 (biochemistry; the
  field 13 and 20 logs have no start line); chemistry plan 5 Nov 03:55:12, log started 03:55:29; India plan 07:00:12,
  log started 07:00:24; Russia plan 11:54:36, log started 11:54:50; co-authorship/journals plan 12:59:12. The plan
  files' SHA-256 hashes match those listed above.
- `data_meta/raw_manifest_original_download.csv`: SHA-256 hashes, times and article counts of the 880 raw works
  files of the original download (3-5 November 2026), including chemistry. `articles` is the number of unique `work_id`s
  in each file; it may differ, by up to about 2.5%, from the logs' "saved N papers", which count the rows saved per query
  page, including duplicates.
- Git history of the original replication repository (github.com/yzaki/metric-promotion-rules-exploration):
  the plans were committed on 5 November 2026 at 05:56 (chemistry, commit 6a91531), 06:32 (biochemistry/economics, in
  the new `plans/` folder, 53fa0a4), 09:08 (India, 97d31db) and 14:28 (Russia, co-authorship, 37afb1e). These are
  client-recorded commit times; each committed plan file (`git show <commit>:<path> | sha256sum`) has the SHA-256 hash
  listed above. The commits corroborate that the plans existed on that day; the order relative to each download
  rests on the file times and logs above.
- Chemistry's reclassification can now be measured (Table S39): 0.7% of the original Italian chemistry articles
  left the field and 15% of the current ones were not in it; the difference between Italy and France + Germany is
  not significant with topic clustering (with robust intervals leaving is, +0.3 [+0.02, +0.61]), and the results on
  articles in chemistry on both dates match the full sample (nearby moves -1.30) but not the original download (-0.47),
  on largely the same articles; the stable-article check therefore does not isolate the reclassification of articles,
  and the difference reflects the remapped subfields (6.4% of the stable articles) and other record changes.
