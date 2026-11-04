"""Settings shared by every script. Change values here, not inside the scripts."""
import os

# --- OpenAlex access -------------------------------------------------------
# Get a free key at https://openalex.org/settings/api, then in your terminal:
#   export OPENALEX_API_KEY="your-key"        (macOS / Linux)
#   setx OPENALEX_API_KEY "your-key"          (Windows, then reopen the terminal)
OPENALEX_API_KEY = os.environ.get("OPENALEX_API_KEY", "")

# --- Who is compared --------------------------------------------------------
TREATED = "IT"              # Italy: careers judged by citation thresholds from 2010-2012
CONTROLS = ["FR", "DE"]     # France and Germany: no comparable reform
COUNTRIES = [TREATED] + CONTROLS

# OpenAlex field id. 31 = Physics and Astronomy (22 = Engineering).
# fetch_openalex.py prints the field's name so you can confirm it.
# Override without editing: set CT_FIELD_ID=22 (each field gets its own data folder).
FIELD_ID = os.environ.get("CT_FIELD_ID", "31")

# --- Years ------------------------------------------------------------------
FETCH_YEARS = list(range(1998, 2020))   # 1998-2003 only seed career age and topic citation rates
PRE_YEARS = list(range(2004, 2010))     # decision years before the reform
POST_YEARS = list(range(2013, 2019))    # decision years after it (2010-2012 = transition, dropped)

# Event-study windows (two years each) and the reference window
EVENT_WINDOWS = [(2004, 2005), (2006, 2007), (2008, 2009), (2010, 2011),
                 (2012, 2013), (2014, 2015), (2016, 2017)]
EVENT_REFERENCE = (2008, 2009)

# --- Sample rules -------------------------------------------------------------
MIN_ACTIVE_YEARS = 5        # an author needs at least this many years with a paper
MIN_COUNTRY_SHARE = 0.8     # share of an author's affiliations that must be in one country
MAX_GAP = 2                 # two active years further apart than this are not linked as a choice
CITE_WINDOW = 3             # years used to measure a topic's citation potential

# --- Model --------------------------------------------------------------------
GAMMA = 0.9                 # discount per active year (fixed, not estimated)
N_BOOT = 200                # bootstrap draws for confidence intervals
SEED = 42

# --- Folders -------------------------------------------------------------------
HERE = os.path.dirname(os.path.abspath(__file__))
_FIELD_SUFFIX = "" if FIELD_ID == "31" else f"_field{FIELD_ID}"   # Physics keeps the original folders
DATA_DIR = os.path.join(HERE, "data" + _FIELD_SUFFIX)
RAW_DIR = os.path.join(DATA_DIR, "raw")
RESULTS_DIR = os.path.join(HERE, "results" + _FIELD_SUFFIX)
