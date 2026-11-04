"""Step 2: turn downloaded papers into scientists' yearly topic choices.

Reads data/raw/works_*.csv.gz and writes data/trajectories.csv with one row per
choice: the scientist's state in year t, what they did (stay / near / far), and
their state in their next active year.

Usage:
    python build_trajectories.py
    python build_trajectories.py --max-team 20 --tag team20   # robustness: drop big-team papers
"""
import argparse
import glob
import os

import numpy as np
import pandas as pd

import config


def load_raw():
    files = sorted(f for f in glob.glob(os.path.join(config.RAW_DIR, "works_*.csv.gz"))
                   if os.path.basename(f).split("_")[1] in config.COUNTRIES)
    if not files:
        raise SystemExit(f"No files in {config.RAW_DIR}. Run fetch_openalex.py first.")
    df = pd.concat((pd.read_csv(f, dtype={"countries": str}) for f in files), ignore_index=True)
    df["countries"] = df["countries"].fillna("")
    # A paper with authors from two countries appears in both countries' files
    df = df.drop_duplicates(["work_id", "author_id"])
    print(f"Loaded {df.work_id.nunique():,} papers and {len(df):,} paper-author rows from {len(files)} files")
    return df


def window_mean(stats, key, window):
    """Mean of c_norm over the `window` years BEFORE each year, for each topic or subfield."""
    parts = []
    for lag in range(1, window + 1):
        s = stats.copy()
        s["year"] = s["year"] + lag
        parts.append(s)
    w = pd.concat(parts).groupby([key, "year"])[["sum", "count"]].sum()
    return (w["sum"] / w["count"]).rename(f"potential_{key}").reset_index()


def citation_potential(df):
    """Topic citation potential: mean year-normalised citations over the previous years."""
    works = df.drop_duplicates("work_id")[["work_id", "year", "cited_by_count", "topic_id", "subfield_id"]]
    year_mean = works.groupby("year").cited_by_count.transform("mean")
    works = works.assign(c_norm=works.cited_by_count / year_mean.replace(0, np.nan))
    pot = {}
    for key in ("topic_id", "subfield_id"):
        stats = works.groupby([key, "year"]).c_norm.agg(["sum", "count"]).reset_index()
        pot[key] = window_mean(stats, key, config.CITE_WINDOW)
    return pot


def citation_potential_world(df):
    """Same as citation_potential, but from world-wide counts (fetch_world_citations.py).

    Subfields are aggregated from their topics, using the topic -> subfield map in df.
    """
    files = sorted(glob.glob(os.path.join(config.DATA_DIR, "world", "cites_*.csv.gz")))
    if not files:
        raise SystemExit("No world citation files. Run fetch_world_citations.py first.")
    w = pd.concat((pd.read_csv(f) for f in files), ignore_index=True)
    w["cites"] = w.cited_by_count * w.n
    year_mean = w.groupby("year").cites.sum() / w.groupby("year").n.sum()
    w["c_norm_sum"] = w.cites / w.year.map(year_mean).replace(0, np.nan)
    topic_sub = df.drop_duplicates("topic_id").set_index("topic_id").subfield_id
    w["subfield_id"] = w.topic_id.map(topic_sub)
    print(f"World citations: {w.n.sum():,} papers, {w.topic_id.nunique()} topics, "
          f"years {w.year.min()}-{w.year.max()}")
    pot = {}
    for key in ("topic_id", "subfield_id"):
        stats = (w.dropna(subset=[key]).groupby([key, "year"])
                 .agg(sum=("c_norm_sum", "sum"), count=("n", "sum")).reset_index())
        pot[key] = window_mean(stats, key, config.CITE_WINDOW)
    return pot


def assign_countries(df):
    """Keep authors with at least MIN_COUNTRY_SHARE of affiliations in one study country."""
    aff = df[["author_id", "countries"]].assign(country=df.countries.str.split("|")).explode("country")
    aff = aff[aff.country.isin(config.COUNTRIES)]
    counts = aff.groupby(["author_id", "country"]).size().rename("n").reset_index()
    counts["share"] = counts.n / counts.groupby("author_id").n.transform("sum")
    top = counts.sort_values(["author_id", "n"], ascending=[True, False]).drop_duplicates("author_id")
    top = top[top.share >= config.MIN_COUNTRY_SHARE]
    return top.set_index("author_id").country


def author_years(df, country):
    """One row per author-year: the author's most frequent primary topic that year."""
    d = df[df.author_id.isin(country.index)]
    n = d.groupby(["author_id", "year", "topic_id", "subfield_id"]).size().rename("n").reset_index()
    ay = (n.sort_values(["author_id", "year", "n", "topic_id"], ascending=[True, True, False, True])
          .drop_duplicates(["author_id", "year"]).drop(columns="n"))
    ay["country"] = ay.author_id.map(country)
    return ay.sort_values(["author_id", "year"]).reset_index(drop=True)


def add_state(ay, pot, career_start=None):
    # Citation potential: topic level, falling back to subfield, then to the year's median
    ay = ay.merge(pot["topic_id"], on=["topic_id", "year"], how="left")
    ay = ay.merge(pot["subfield_id"], on=["subfield_id", "year"], how="left")
    ay["potential"] = ay.potential_topic_id.fillna(ay.potential_subfield_id)
    ay["potential"] = ay.potential.fillna(ay.groupby("year").potential.transform("median"))
    # Tier: low / middle / high third of potential among all author-years that year
    # (the first years have no earlier window; they are not decision years and get the middle tier)
    pct = ay.groupby("year").potential.rank(method="average", pct=True)
    ay["tier"] = np.clip(np.ceil(pct * 3) - 1, 0, 2).fillna(1).astype(int)

    # Career stage: years since the author's first observed paper, or, with career_start (a Series
    # author_id -> first publication year from the full MAG record), years since the true first paper
    first = ay.groupby("author_id").year.transform("min")
    if career_start is not None:
        first = np.minimum(ay.author_id.map(career_start), first)
    ay["career_years"] = ay.year - first
    ay["career"] = np.select([ay.career_years <= 5, ay.career_years <= 15], [0, 1], 2)

    # Time in topic: consecutive active years in the same topic
    same_author = ay.author_id.eq(ay.author_id.shift())
    gap = ay.year - ay.year.shift()
    same_topic = same_author & ay.topic_id.eq(ay.topic_id.shift()) & (gap <= config.MAX_GAP)
    run = (~same_topic).cumsum()
    ay["years_in_topic"] = ay.groupby(run).cumcount() + 1
    ay["tenure"] = np.select([ay.years_in_topic == 1, ay.years_in_topic <= 3], [0, 1], 2)
    return ay


def topic_neighbours(df, k, years=(1998, 2003)):
    """Each topic's k most similar topics, by cosine similarity of the sets of scientists
    publishing in them in `years` (before the decision years, so unaffected by the reform)."""
    d = df[df.year.between(*years)][["author_id", "topic_id"]].drop_duplicates()
    a_codes, _ = pd.factorize(d.author_id)
    t_codes, topics = pd.factorize(d.topic_id)
    from scipy.sparse import csr_matrix
    M = csr_matrix((np.ones(len(d)), (a_codes, t_codes)))
    C = (M.T @ M).toarray()
    n = np.sqrt(np.diag(C))
    S = C / np.outer(n, n)
    np.fill_diagonal(S, -1)
    nb = {topics[i]: set(topics[np.argsort(-S[i])[:k]]) for i in range(len(topics))}
    same_sub = df.drop_duplicates("topic_id").set_index("topic_id").subfield_id
    overlap = np.mean([np.mean([same_sub.get(j) == same_sub.get(t) for j in v]) for t, v in nb.items()])
    print(f"Topic neighbours: {len(topics)} topics, k={k}; share of neighbours in the same subfield {overlap:.2f}")
    return nb


def make_choices(ay, neighbours=None):
    nxt = ay.groupby("author_id").shift(-1)
    ok = nxt.year.notna() & ((nxt.year - ay.year) <= config.MAX_GAP)
    if neighbours is None:   # default: nearby = same subfield
        is_near = nxt.subfield_id == ay.subfield_id
    else:                    # alternative: nearby = among the current topic's most similar topics
        is_near = pd.Series([n in neighbours.get(t, ()) for t, n in zip(ay.topic_id, nxt.topic_id)], index=ay.index)
    action = np.where(nxt.topic_id == ay.topic_id, "stay", np.where(is_near, "near", "far"))
    out = pd.DataFrame({
        "author_id": ay.author_id, "country": ay.country,
        "group": np.where(ay.country == config.TREATED, "IT", "CTRL"),
        "year": ay.year, "s_tier": ay.tier, "s_tenure": ay.tenure, "s_career": ay.career,
        "action": action,
        "ns_tier": nxt.tier, "ns_tenure": nxt.tenure, "ns_career": nxt.career,
    })[ok]
    for c in ("ns_tier", "ns_tenure", "ns_career"):
        out[c] = out[c].astype(int)
    return out.reset_index(drop=True)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--max-team", type=int, default=None,
                    help="ignore papers with more listed authors than this when assigning topics")
    ap.add_argument("--tag", default="", help="suffix for output files, e.g. team20")
    ap.add_argument("--controls", nargs="+", default=None,
                    help="control countries (default config.CONTROLS), e.g. FR DE ES")
    ap.add_argument("--world", action="store_true",
                    help="citation potential from world-wide counts (fetch_world_citations.py)")
    ap.add_argument("--near-k", type=int, default=None,
                    help="define 'near' as the k most similar topics (author co-occurrence, 1998-2003)")
    ap.add_argument("--career-start", default=None,
                    help="career_start.tsv.gz from the SciSciNet match: career age from the true first "
                         "publication year; unmatched scientists are dropped")
    ap.add_argument("--treated", default=None,
                    help="treated country instead of Italy, e.g. PL or RO (Italy is then left out); "
                         "it is labelled IT in the output so the estimation scripts run unchanged")
    args = ap.parse_args()
    suffix = f"_{args.tag}" if args.tag else ""
    if args.treated:
        config.TREATED = args.treated
        config.COUNTRIES = [config.TREATED] + config.CONTROLS
    if args.controls:
        config.CONTROLS = args.controls
        config.COUNTRIES = [config.TREATED] + args.controls
    print(f"Treated: {config.TREATED}; controls: {', '.join(config.CONTROLS)}")

    df = load_raw()
    # citation potential always uses every paper (world-wide with --world)
    pot = citation_potential_world(df) if args.world else citation_potential(df)
    country = assign_countries(df)
    print(f"Authors with a clear home country: {len(country):,}")

    if args.max_team:
        team = df.groupby("work_id").author_id.transform("size")   # OpenAlex lists at most 100 authors
        df = df[team <= args.max_team]
        print(f"Keeping papers with at most {args.max_team} authors: {df.work_id.nunique():,} papers")

    ay = author_years(df, country)
    active = ay.groupby("author_id").year.transform("size")
    ay = ay[active >= config.MIN_ACTIVE_YEARS].reset_index(drop=True)
    print(f"Authors with at least {config.MIN_ACTIVE_YEARS} active years: {ay.author_id.nunique():,}")

    start = None
    if args.career_start:
        cs = pd.read_csv(args.career_start, sep="\t").dropna(subset=["mag_first_year"])
        cs = cs[cs.mag_first_year >= 1960]   # earlier first years are MAG date errors or wrong merges
        start = cs.set_index("author_id").mag_first_year.astype(int)
        matched = ay.author_id.isin(start.index)
        rate = matched.groupby(ay.country).mean()
        print("Share of author-years matched to a MAG career start, by country:\n", rate.round(3).to_string())
        ay = ay[matched].reset_index(drop=True)
    ay = add_state(ay, pot, start)
    choices = make_choices(ay, topic_neighbours(df, args.near_k) if args.near_k else None)
    choices = choices[choices.year >= min(config.PRE_YEARS)]

    os.makedirs(config.DATA_DIR, exist_ok=True)
    out = os.path.join(config.DATA_DIR, f"trajectories{suffix}.csv")
    choices.to_csv(out, index=False)

    os.makedirs(config.RESULTS_DIR, exist_ok=True)
    desc = (choices.assign(period=np.select([choices.year.isin(config.PRE_YEARS),
                                             choices.year.isin(config.POST_YEARS)],
                                            ["before", "after"], "transition"))
            .groupby(["country", "period"])
            .agg(scientists=("author_id", "nunique"), choices=("action", "size"),
                 share_stay=("action", lambda a: (a == "stay").mean()),
                 share_near=("action", lambda a: (a == "near").mean()),
                 share_far=("action", lambda a: (a == "far").mean())))
    desc.to_csv(os.path.join(config.RESULTS_DIR, f"descriptives{suffix}.csv"))
    print("\n", desc.round(3).to_string())
    print(f"\nWrote {len(choices):,} choices to {out}\nNext step: python estimate.py")


if __name__ == "__main__":
    main()
