# Analysis plan: where and with whom scientists published (journals and co-authors)

Written 5 November 2026, before any journal or co-authorship outcome was computed for any country. Written
after the topic results for Italy and India were known (Russia's were not yet available). These analyses are
**secondary**: they ask how scientists met the targets, not whether the main topic result holds.

## Countries, fields and design
Treated: Italy (2012 habilitation), India (2010 UGC Regulations), Russia (Project 5-100 from 2013), each vs
France + Germany (Italy excluded for India and Russia). Fields: OpenAlex 31, 22, 13, 16. Same samples as the
topic analyses (trajectory files `trajectories_world*.csv`); scientist-years with at least one article;
before 2004–09, after 2013–18. Model-free difference-in-differences of the scientist-year outcome with
scientist and year fixed effects, standard errors clustered by scientist; per field, and stacked over the
four fields per country with field-specific fixed effects.

## Outcomes (scientist-year means over the scientist's articles in the field)
Co-authorship (from the stored author lists and affiliation countries):
- **C1 Team size**: number of listed authors (OpenAlex lists at most 100), and its logarithm.
- **C2 International co-authorship**: share of articles with at least one author outside the scientist's
  country.
- **C3 New co-authors**: share of the year's distinct co-authors with whom the scientist had no article in
  the six previous years.
Requiring re-downloaded journal and institution fields:
- **V1 Journal tier**: share of articles in the top and in the bottom quartile of journals in the field,
  journals ranked by OpenAlex two-year mean citedness (current values), quartiles weighted by the field's
  articles in our data; and the mean percentile of the journal.
- **V2 Fee-charging open-access journals**: share of articles in journals listed in DOAJ with an article
  processing charge.
- **C4 Institutions**: number of distinct institutions per article and share of single-institution articles.

## Predictions
- **Italy** (thresholds on articles, citations and h-index, not on journals): no shift towards the bottom
  journal quartile (V1 bottom share not higher); larger teams and more co-authors (C1, C3 higher).
- **India** (points for publications in listed journals): higher bottom-quartile share (V1) and higher share
  in fee-charging open-access journals (V2).
- **Russia** (Scopus/Web of Science publication targets): higher bottom-quartile share (V1); higher
  international co-authorship (C2).
A prediction is "supported" if the stacked estimate has the predicted sign with a 95% interval excluding 0,
"not supported" otherwise. All outcomes are reported for all three countries whatever their direction.

## Caveats fixed in advance
Journal citedness is current, not contemporaneous; field quartiles are computed from our sample's journals.
Team size is capped at 100 listed authors. These are descriptive responses of the treated countries, not
separate causal tests of the rules.
