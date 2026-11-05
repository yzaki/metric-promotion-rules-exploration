# Analysis plan: Russia as a third treated country

Written 5 November 2026, **before any Russian data were downloaded or inspected**. Only article counts per
field were queried (Russia, 1998–2019: physics 144,483; engineering 184,945; biochemistry 57,876; chemistry
77,490). The file's timestamp and the first line of `logs/fetch_russia.txt` document the order. Written after
the Italian and Indian results were known (India did not replicate the Italian result).

## Policy
The presidential decree of 7 May 2012 set the goal of placing five Russian universities in the world's top
100, implemented from 2013 by Project 5-100 (first 15 universities selected on 8 May 2013, six more in
October 2015; programme to 2020), which tied university funding to performance targets including
publications in Web of Science and Scopus journals and passed them on to staff as individual publication
targets and bonuses. The period also saw the 2013 reform of the Russian Academy of Sciences, whose institutes
were evaluated with publication indicators. Unlike Italy's, these are institutional and contractual targets,
not national promotion thresholds.

## Design (identical to the Italian and Indian analyses; code as of this date)
Treated: Russia (Italy excluded). Controls: France + Germany (main); + Spain (second). OpenAlex fields 31, 22,
13, 16. Articles 1998–2019; decision years 2004–09 (before) and 2013–18 (after), 2010–12 transition;
at least 5 active years; 80% single-country affiliation; MAX_GAP 2; γ = 0.9; world-wide citation measure;
100 bootstrap draws per field.

## Hypotheses
- **R1 (primary):** in the model-free difference-in-differences stacked over the four fields (field-specific
  scientist and year fixed effects, standard errors clustered by scientist), the yearly probability of a
  nearby move falls in Russia relative to France + Germany: estimate negative, 95% interval below 0. Also
  reported per field (nearby-move weight and model-free estimate).
- **R2 (placebo):** the 2007 placebo (2004–06 vs 2007–09), stacked model-free, has an interval including 0.
- **R3 (returns):** the stacked model-free estimate for nearby returns (topic with an article by the
  scientist in the previous six years) is negative.
- **R4 (mechanism):** the decline is larger among scientists whose main Russian affiliation in 2009–12
  (OpenAlex dated affiliations) is one of the 21 Project 5-100 universities than among other Russian
  scientists. 5-100 universities are identified by these name patterns (case-insensitive): Higher School of
  Economics; Moscow Institute of Physics and Technology; MISiS / MISIS; MEPhI / National Research Nuclear
  University; Lobachevsky; "Novosibirsk State University" not followed by "of"; Sechenov / First Moscow State
  Medical University; Peoples' Friendship University / RUDN; Samara National Research University / Samara
  University; Electrotechnical University / LETI; Peter the Great / Saint Petersburg Polytechnic /
  St. Petersburg Polytechnic; Siberian Federal University; "Tomsk State University" not followed by "of";
  Tomsk Polytechnic; University of Tyumen / Tyumen State University; ITMO; Ural Federal University; "South
  Ural State University" not followed by "of"; Immanuel Kant / Baltic Federal University; Far Eastern Federal
  University; Kazan Federal University. Test: 5-100 minus other, nearby-move weight per field and stacked
  model-free; prediction negative.

## Decision rules
- **Pre-trend rule:** event study per field relative to 2008–09; if 2004–05 or 2006–07 excludes 0 with both
  FR+DE and FR+DE+ES, that field's estimate is reported as "not interpretable as a reform effect".
- **Russia replicates the Italian result** if R1 is supported and R2 holds, and the decline is not explained
  by pre-trends in the fields that drive it. **Mechanism supported** if R4 is negative with an interval
  excluding 0 in the stacked estimate.
- Confounders known in advance: the Academy of Sciences reform (2013), sanctions and the rouble crisis
  (2014–15), changes in OpenAlex coverage of Russian-language journals. Results are reported as they are.
- Every result is reported in the paper whatever its direction.
