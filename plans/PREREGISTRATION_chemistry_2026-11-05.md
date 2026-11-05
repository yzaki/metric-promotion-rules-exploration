# Analysis plan: chemistry as a second test of the habilitation mechanism

Written 5 November 2026, **before any chemistry (OpenAlex field 16) data were downloaded or inspected**.
Only the article counts per country were queried (1998–2019: IT 46,752; FR 76,152; DE 123,525;
ES 59,488). The file's timestamp and the first download log line (`logs/fetch_field16.txt`) document
the order. To be deposited unchanged with the earlier plan (OSF).

## Why chemistry
In the three fields studied so far, Italian scientists made fewer nearby topic moves after the 2012
habilitation. Only in engineering did the decline follow the incentive of the habilitation: it was
among university staff and absent at research institutes, among associate professors rather than full
professors, and larger for scientists below the bar of their own competition sector. In physics it was
as large at research institutes not bound by the rules. Chemistry was chosen because it is the field
most similar to engineering in structure: bibliometric sectors in the 2012 habilitation (area 03), mostly
university-based, with a distinct group of research-institute scientists (CNR) as a comparison. It was
chosen before seeing any chemistry data, and no other field will be added on the basis of its results.

## Design (identical to the other fields; code as of this date in `citation-targets-irl/`)
Treated: Italy. Controls: France + Germany (main); + Spain (second). Articles only, 1998–2019; decision
years 2004–09 (before) and 2013–18 (after); at least 5 active years; 80% single-country affiliation;
MAX_GAP 2; γ = 0.9; world-wide citation measure (main); 200 bootstrap draws (main estimate), 100 for
subgroup analyses. True career start from the SciSciNet/MAG match; academic rank from the MUR staff
register at 31/12/2011 (already downloaded, all areas); institution type from OpenAlex dated affiliations
(2009–12).

## Hypotheses
- **C1 (main):** the nearby-move DiD (Italy vs FR+DE) is negative, 95% interval below 0. Also reported:
  model-free DiD with scientist and year FE.
- **C2 (placebo):** the 2007 placebo nearby-move interval includes 0.
- **C3 (mechanism: institutions):** the decline is larger among Italian university staff (in the 2011
  register) than among Italian research-institute scientists (main affiliation type facility/government,
  2009–12). Test: university staff minus research institute < 0.
- **C4 (mechanism: rank):** the decline is larger among associate professors and researchers (who needed
  the habilitation) than among full professors. Test: "needed it" minus full professors < 0.
- **C5 (mechanism: own bar):** the decline is larger for associates and researchers below the bar of their
  own sector (0–1 of 3 indicators) than for those who met it. Test: below minus met < 0.

## Decision rules
- C1 and C2 together: "the decline replicates in chemistry". C1 without C2: "not interpretable".
- C3–C5 are each "supported" if the point estimate is negative and the 95% interval excludes 0;
  "consistent" if negative with an interval including 0; "not supported" otherwise. Chemistry supports
  the engineering mechanism if at least two of C3–C5 are supported or consistent and none is in the
  opposite direction with an interval excluding 0.
- Power is limited (about a third of engineering's Italian sample); wide intervals including 0 will be
  reported as inconclusive, not as evidence of no effect.
- Every result is reported in the paper whatever its direction.

## Pre-trend rule
As before: if the 2004–05 or 2006–07 event-study estimates exclude 0 with FR+DE, the FR+DE+ES
specification is the primary result.
