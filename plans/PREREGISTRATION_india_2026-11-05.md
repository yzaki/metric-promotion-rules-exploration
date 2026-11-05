# Analysis plan: India as a second treated country

Written 5 November 2026, **before any Indian data were downloaded or inspected**. Only article counts per
field were queried (India, 1998–2019: physics 70,315; engineering 214,851; biochemistry 96,090; chemistry
108,294). The file's timestamp and the first line of `logs/fetch_india.txt` document the order. Written
after all Italian results were known; India was chosen as the country whose policy is closest to Italy's.

## Policy
The University Grants Commission (UGC) Regulations 2010, notified in the Gazette of India on 18 September
2010, made promotion of university and college teachers under the Career Advancement Scheme conditional on
minimum scores of a point-based Academic Performance Indicator (API), with research and publications scored
in its category III. The regulations were amended in 2013 and 2016 (requirements relaxed in 2016) and
replaced in 2018. They apply to teachers of UGC-governed universities and colleges, not to autonomous
institutes of national importance or to government research laboratories.

## Design (identical to the Italian analysis; code as of this date in `citation-targets-irl/`)
Treated: India (Italy excluded). Controls: France + Germany (main); + Spain (second). OpenAlex fields 31
(physics), 22 (engineering), 13 (biochemistry), 16 (chemistry). Articles 1998–2019; decision years
2004–09 (before) and 2013–18 (after), 2010–12 transition; at least 5 active years; 80% single-country
affiliation; MAX_GAP 2; γ = 0.9; world-wide citation measure; 100 bootstrap draws per field.

## Hypotheses
- **I1 (primary):** in a model-free difference-in-differences stacked over the four fields (field-specific
  scientist and year fixed effects, standard errors clustered by scientist), the yearly probability of a
  nearby move falls in India relative to France + Germany: estimate negative, 95% interval below 0.
  Also reported per field: nearby-move weight (IRL) and model-free estimate.
- **I2 (placebo):** the 2007 placebo (2004–06 vs 2007–09), stacked model-free, has an interval including 0.
- **I3 (returns):** the decline is in returns to familiar topics: the stacked model-free estimate for nearby
  returns (no article in the topic in the previous six years = first entry; otherwise return) is negative.
- **I4 (mechanism):** the decline is larger among scientists whose main Indian affiliation in 2009–12
  (OpenAlex dated affiliations) is a UGC-governed university or college than among scientists at institutions
  not covered: government or facility institutions, and education institutions whose names contain "Indian
  Institute of Technology", "Indian Institute of Science", "Indian Institute of Science Education and
  Research", "National Institute of Technology", "Indian Statistical Institute", "Tata Institute", "All India
  Institute of Medical Sciences", "Indian Institute of Management", "Indian Institute of Information
  Technology" or "Homi Bhabha". Test: UGC-covered minus not covered, nearby-move weight per field and stacked
  model-free; prediction negative.

## Decision rules
- **Pre-trend rule:** event study (FR+DE) per field, two-year windows relative to 2008–09. If 2004–05 or
  2006–07 excludes 0 in a field, FR+DE+ES is primary for that field; if both specifications show a pre-trend,
  that field's estimate is reported as "not interpretable as a reform effect".
- **India replicates the Italian result** if I1 is supported and I2 holds, and the decline is not explained
  by pre-trends in the fields that drive it. **Mechanism supported** if I4 is negative with an interval
  excluding 0 in the stacked estimate.
- India's science system grew fast in this period, and the regulations also coincided with a documented rise
  of publishing in low-quality journals; both are reasons to expect pre-trends or noise, and results will be
  reported as they are.
- Every result is reported in the paper whatever its direction.
