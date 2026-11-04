"""Match sampled OpenAlex scientists to MAG authors in SciSciNet and get their first publication year.

Inputs (in the working folder): author_papers.tsv.gz (author_id, paper_id), author_names.tsv.gz
(author_id, surname, first_initial, first_year_in_data) and the SciSciNet tables in sciscinet/.
A MAG author is a match if they share at least MIN_SHARED of the scientist's papers, share a surname
token and have the same first initial. Several matching MAG ids (MAG splits people) are pooled.
Output: career_start.tsv.gz with one row per scientist.
"""
import polars as pl

S = "sciscinet/"
MIN_SHARED = 2


def tokens(col):
    return (pl.col(col).fill_null("").str.normalize("NFKD").str.to_lowercase()
            .str.replace_all(r"[^a-z ]", " ").str.strip_chars().str.split(" ")
            .list.eval(pl.element().filter(pl.element().str.len_chars() > 0)))


ours = pl.read_csv("author_papers.tsv.gz", separator="\t")
print("our pairs", ours.shape, flush=True)
names = pl.read_csv("author_names.tsv.gz", separator="\t", infer_schema_length=0)
our_ids = ours.select(pl.col("paper_id").unique().alias("PaperID"))

paa = pl.scan_csv(S + "SciSciNet_PaperAuthorAffiliations.tsv", separator="\t",
                  schema_overrides={"PaperID": pl.Int64, "AuthorID": pl.Int64, "AffiliationID": pl.Utf8,
                                    "AuthorSequenceNumber": pl.Utf8})
cand = (paa.select("PaperID", "AuthorID").join(our_ids.lazy(), on="PaperID", how="semi")
        .unique().collect(engine="streaming"))
print("candidate MAG paper-author rows", cand.shape, flush=True)

mag = (pl.scan_csv(S + "SciSciNet_Authors.tsv", separator="\t", quote_char=None,
                   schema_overrides={"AuthorID": pl.Int64, "Author_Name": pl.Utf8}, infer_schema_length=0)
       .select(pl.col("AuthorID").cast(pl.Int64), "Author_Name")
       .join(cand.select("AuthorID").unique().lazy(), on="AuthorID", how="semi").collect(engine="streaming"))
mag = mag.with_columns(tok=tokens("Author_Name"))
mag = mag.with_columns(m_initial=pl.col("tok").list.first().str.slice(0, 1),
                       m_sur=pl.when(pl.col("tok").list.len() > 1).then(pl.col("tok").list.slice(1))
                       .otherwise(pl.col("tok")))
print("candidate MAG authors", mag.height, flush=True)

# our surname tokens: all name tokens after the first (from the exported surname we only have the last
# token, so use the full OpenAlex name again if present)
nm = names.with_columns(tok=tokens("full_name"))
nm = nm.with_columns(tok=pl.when(pl.col("tok").list.len() > 1).then(pl.col("tok").list.slice(1)).otherwise(pl.col("tok")))
our_tok = nm.select("author_id", pl.col("first_initial").alias("o_initial"), "tok").explode("tok") \
            .rename({"tok": "token"}).filter(pl.col("token").is_not_null() & (pl.col("token") != ""))
mag_tok = mag.select("AuthorID", "m_initial", pl.col("m_sur").alias("token")).explode("token")

pairs = (ours.rename({"paper_id": "PaperID"}).join(our_tok, on="author_id")
         .join(cand, on="PaperID").join(mag_tok, on=["AuthorID", "token"])
         .filter(pl.col("o_initial") == pl.col("m_initial"))
         .select("author_id", "AuthorID", "PaperID").unique())
shared = pairs.group_by("author_id", "AuthorID").agg(n_shared=pl.len())
n_our = ours.group_by("author_id").agg(n_papers=pl.len())
good = shared.filter(pl.col("n_shared") >= MIN_SHARED)
print("matched (author, MAG id) pairs", good.height, flush=True)

# first year of each matched MAG id, over its full SciSciNet record
ids = good.select(pl.col("AuthorID").unique())
their = paa.select("PaperID", "AuthorID").join(ids.lazy(), on="AuthorID", how="semi").collect(engine="streaming")
years = (pl.scan_csv(S + "SciSciNet_Papers.tsv", separator="\t", quote_char=None, infer_schema_length=0)
         .select(pl.col("PaperID").cast(pl.Int64), pl.col("Year").cast(pl.Float64).cast(pl.Int64, strict=False))
         .join(their.select(pl.col("PaperID").unique()).lazy(), on="PaperID", how="semi")
         .collect(engine="streaming"))
first = (their.join(years, on="PaperID").filter(pl.col("Year").is_between(1900, 2022))
         .group_by("AuthorID").agg(mag_first=pl.col("Year").min(), mag_n_papers=pl.len()))

out = (good.join(first, on="AuthorID", how="left").group_by("author_id")
       .agg(mag_first_year=pl.col("mag_first").min(), n_mag_ids=pl.len(),
            n_shared=pl.col("n_shared").sum(), mag_n_papers=pl.col("mag_n_papers").sum(),
            top_id_first=pl.col("mag_first").sort_by("n_shared", descending=True).first()))
out = names.select("author_id", "first_year_in_data").join(out, on="author_id", how="left").join(n_our, on="author_id", how="left")
out.write_csv("career_start.tsv.gz".replace(".gz", ""), separator="\t")
print(out.describe(), flush=True)
m = out.filter(pl.col("mag_first_year").is_not_null())
print("matched share", m.height / out.height, flush=True)
print(m.select((pl.col("mag_first_year") < 1998).mean().alias("share_first_before_1998"),
               (pl.col("mag_first_year") <= pl.col("first_year_in_data").cast(pl.Int64)).mean().alias("mag_first_le_ours"),
               (pl.col("n_mag_ids") > 1).mean().alias("share_split_ids")), flush=True)
