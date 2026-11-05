# Pre-registration: replication and placebo fields

Written 4 Nov 2026, **before any data from these fields was downloaded or inspected**.
The local file timestamp and the first download log line (`logs/fetch_field13.txt`,
`logs/fetch_field20.txt`) document the order. For a formal record, upload this file
unchanged to OSF (https://osf.io) before reading the new results.

## Background
In Physics (OpenAlex field 31) and Engineering (field 22), the reform effect (Italy vs
France+Germany, after 2013–18 minus before 2004–09) was a drop in the nearby-move reward
weight: Physics −0.16 [−0.21, −0.11], Engineering −0.11 [−0.16, −0.05]. Citation-weight and
distant-jump effects were about zero. These were found after the original hypotheses (higher
citation weight, lower distant-jump weight) were specified, so the following tests confirm
the nearby-move finding on fields not yet examined.

## Fields
1. **Biochemistry, Genetics and Molecular Biology** (OpenAlex field 13). In the 2012
   habilitation these sectors were **bibliometric** (citation and h-index thresholds).
   **Confirmatory replication.**
2. **Economics, Econometrics and Finance** (OpenAlex field 20). In the 2012 habilitation,
   Area 13 (economics and statistics) was **non-bibliometric**: thresholds on counts of
   books, articles/chapters and articles in class-A journals, **no citation thresholds**.
   **Placebo / mechanism test.**

## Design (identical to Physics/Engineering; no changes after seeing data)
Code as of this date in `citation-targets-irl/` (config.py unchanged except `CT_FIELD_ID`).
Countries IT (treated); FR, DE (main control); FR, DE, ES (second control). Articles only;
years 1998–2019; decision years before 2004–09, after 2013–18; at least 5 active years,
80% single-country affiliation, MAX_GAP 2, γ = 0.9, 200 bootstrap draws resampling authors.
Citation potential as in the main run (downloaded countries). The world-wide measure is
added if budget allows and is reported as secondary.

## Hypotheses
- **H-R1 (field 13):** the nearby-move DiD is **negative**, with a 95% bootstrap interval
  below 0, in the FR+DE specification. Supported if the interval excludes 0 and is negative.
- **H-R2 (field 13):** the 2007 placebo nearby-move DiD interval **includes 0**.
- **H-R3 (field 13):** the effect is larger (more negative) for career stages 0–5 and 6–15
  than for 16+.
- **H-P1 (field 20), two-sided, interpretation fixed in advance:**
  - If the nearby-move DiD interval **includes 0**, that supports *citation* thresholds
    specifically as the cause.
  - If it is **negative and excludes 0**, that implies *publication-count* targets in general
    (which economics also had) suffice to cause staying put. This is a mechanism result, not
    a failure.
  - Economics' smaller sample is acknowledged in advance: a wide interval that includes 0
    is reported as inconclusive, not as evidence of no effect.

## Pre-trend rule
If the event-study nearby-move estimates for 2004–05 or 2006–07 have intervals excluding 0
in the FR+DE specification, the FR+DE+ES specification is the primary result for that field
(the same rule as applied to Physics).

## Reporting
All four quantities (citation, nearby, distant DiD; placebo) are reported for both fields
whatever their direction.
