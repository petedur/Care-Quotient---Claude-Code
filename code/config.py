"""
Configuration and constants for Care Capacity Index collectors.
API keys are loaded from the .env file in the project root — never hardcoded.
"""

import os
from pathlib import Path
from dotenv import load_dotenv
import pandas as pd

# Load .env from the project root (one level above /code)
_PROJECT_ROOT = Path(__file__).resolve().parent.parent
load_dotenv(_PROJECT_ROOT / ".env")

# ── Paths ─────────────────────────────────────────────────────────────────────

PROJECT_ROOT = _PROJECT_ROOT

# DOWNLOADED_DATA: override via env var CCI_DATA_DIR, else default to a sibling
# "Downloaded Data" folder next to the project root.
# Set CCI_DATA_DIR in your .env or shell to point at your local downloads folder.
_data_dir_env = os.environ.get("CCI_DATA_DIR")
DOWNLOADED_DATA = Path(_data_dir_env) if _data_dir_env else (
    _PROJECT_ROOT.parent / "Downloaded Data"
)

DATA_RAW            = PROJECT_ROOT / "data" / "raw"
DATA_PROCESSED      = PROJECT_ROOT / "data" / "processed"
DB_PATH             = PROJECT_ROOT / "data" / "care_capacity.duckdb"

IRS_DATA_PATH       = DOWNLOADED_DATA / "IRS EO BMF"

# IRS EO BMF files are split by region, not by state.
# Maps state abbreviation → which regional CSV to use.
IRS_STATE_TO_REGION = {
    # Region 1 — Northeast
    **{s: "Region 1_Northeast" for s in ["CT","ME","MA","NH","NJ","NY","RI","VT"]},
    # Region 2 — Mid-Atlantic & Great Lakes
    **{s: "Region 2_Mid-Atlantic and Great Lakes" for s in
       ["DE","DC","IL","IN","IA","KY","MD","MI","MN","NE","NC","ND","OH","PA","SC","SD","VA","WV","WI"]},
    # Region 3 — Gulf Coast & Pacific
    **{s: "Region 3_Gulf Coast and Pacific Coast" for s in
       ["AL","AK","AR","AZ","CA","CO","FL","GA","HI","ID","KS","LA","MS","MO","MT","NV","NM","OK","OR","TX","TN","UT","WA","WY"]},
}
IMLS_DATA_PATH      = DOWNLOADED_DATA / "Public Libraries Survey (PLS)"
HRSA_DATA_PATH      = DOWNLOADED_DATA / "Health_Center_Service_Delivery_and_LookAlike_Sites.xlsx"

# ── API Keys ──────────────────────────────────────────────────────────────────

# Lazy accessor — raises only when actually called by a collector, not at import.
# score.py and etl.py import config but don't need the Census key, so this avoids
# breaking those scripts when running without a .env file.
def get_census_api_key() -> str:
    key = os.environ.get("CENSUS_API_KEY")
    if not key:
        raise EnvironmentError(
            "CENSUS_API_KEY not set. Copy .env.example to .env and add your key."
        )
    return key

# ── City definitions ──────────────────────────────────────────────────────────
# Cities are loaded from data/cities.csv, which contains one row per city with
# pipe-separated 5-digit county FIPS codes (e.g. "36061|36005|36047").
#
# The resulting CITIES dict has this shape per entry:
#   {
#     "name":        str,           # display name
#     "state":       str,           # state abbreviation e.g. "NY"
#     "state_fips":  str,           # 2-digit state FIPS e.g. "36"
#     "population":  int,
#     "county_fips": set[str],      # set of 5-digit county FIPS strings
#   }
#
# Collectors use county_fips to look up the matching ZIP codes via
# geo.zip_fips.county_to_zips(), then filter datasets by ZIP.

_CITIES_CSV = PROJECT_ROOT / "data" / "cities.csv"


def _load_cities() -> dict:
    if not _CITIES_CSV.exists():
        raise FileNotFoundError(
            f"cities.csv not found at {_CITIES_CSV}. "
            "Ensure care-capacity-index/data/cities.csv is present."
        )
    df = pd.read_csv(_CITIES_CSV, dtype=str)
    cities = {}
    for _, row in df.iterrows():
        fips_set = set(row["county_fips"].split("|"))
        # place_fips: 5-digit Census incorporated place code.
        # Used by geo.city_zips.city_to_zips() for ZCTA-based geographic filtering.
        # Run setup/lookup_place_fips.py to populate this column.
        place_fips = row.get("place_fips", "")
        if pd.isna(place_fips):
            place_fips = ""
        cities[row["city_key"]] = {
            "name":        row["name"],
            "state":       row["state"],
            "state_fips":  row["state_fips"].zfill(2),
            "population":  int(row["population"]),
            "county_fips": fips_set,
            "place_fips":  str(place_fips).strip().zfill(5) if place_fips else "",
            "lat":         float(row["lat"]) if "lat" in row and not pd.isna(row.get("lat")) else None,
            "lng":         float(row["lng"]) if "lng" in row and not pd.isna(row.get("lng")) else None,
        }
    return cities


CITIES = _load_cities()

# ── NTEE codes ────────────────────────────────────────────────────────────────
# Values can be single-character (match first letter only) or multi-character
# (matched as a prefix). E.g. "X3" matches X30, X31, etc.
#
# Pillar 1 — Social Support & Connection
# P = Human Services: community centers, mutual aid, social services.
# NOTE: A (Arts/Culture) and B (Education) deliberately excluded — they
# correlate with affluence, not care capacity, and would bias the index.
NTEE_SOCIAL_SUPPORT = ["P"]

# Pillar 2 — Institutions of Care
# E = Health (hospitals, clinics, health services)
# F = Mental Health & Crisis Intervention
# K = Food, Agriculture & Nutrition (food banks, food pantries)
NTEE_CARE_INSTITUTIONS = ["E", "F", "K"]

# Combined scored nonprofit metric (V3): P + E + F + K without faith-based.
# Factor analysis showed NTEE P and NTEE E/F/K correlate at r=0.85 across
# 71 cities — they measure the same underlying dimension (nonprofit density)
# rather than distinct pillar-level constructs. Combined into one scored metric
# in Pillar 2; individual P and E/F/K counts retained as diagnostics.
NTEE_COMBINED_CARE = ["P", "E", "F", "K"]

# Faith-based human services only — NOT all religious organizations.
# X3x = Faith-Based Human Services & Issues (NTEE X30 category).
# Narrowed from all X codes to avoid counting purely devotional orgs
# (churches, synagogues, mosques) as care infrastructure. This understates
# faith-based care since many congregations doing real service work file
# under P or E rather than X — documented limitation.
NTEE_FAITH_BASED = ["X3"]

# All care-relevant codes combined (used for broad diagnostic counts only)
NTEE_ALL_CARE = list(set(NTEE_SOCIAL_SUPPORT + NTEE_CARE_INSTITUTIONS + NTEE_FAITH_BASED))

# ── Census ACS variables ──────────────────────────────────────────────────────
CENSUS_ACS_VARIABLES = {
    # Residential stability (B07003)
    "same_house_1yr":   "B07003_004E",  # Population in same house 1 year ago
    "total_population": "B01003_001E",

    # Housing cost burden — renters (B25070)
    "renter_total":           "B25070_001E",
    "renter_not_computed":    "B25070_011E",
    "renter_burden_30_34":    "B25070_007E",
    "renter_burden_35_39":    "B25070_008E",
    "renter_burden_40_49":    "B25070_009E",
    "renter_burden_50plus":   "B25070_010E",
    # Housing cost burden — owners with mortgage (B25091)
    "owner_mtg_total":        "B25091_002E",
    "owner_mtg_not_computed": "B25091_012E",
    "owner_mtg_burden_30_34": "B25091_008E",
    "owner_mtg_burden_35_39": "B25091_009E",
    "owner_mtg_burden_40_49": "B25091_010E",
    "owner_mtg_burden_50plus": "B25091_011E",
    # Housing cost burden — owners without mortgage (B25091)
    "owner_no_mtg_total":        "B25091_013E",
    "owner_no_mtg_not_computed": "B25091_023E",
    "owner_no_mtg_burden_30_34": "B25091_019E",
    "owner_no_mtg_burden_35_39": "B25091_020E",
    "owner_no_mtg_burden_40_49": "B25091_021E",
    "owner_no_mtg_burden_50plus": "B25091_022E",

    # SNAP participation (B22001, C17002)
    # Denominator uses C17002 (0–149% FPL) to approximate 130% FPL SNAP eligibility.
    # Prior version used B17001 (100% FPL) which understated eligibility.
    "snap_total_households": "B22001_001E",
    "snap_households":       "B22001_002E",
    "snap_total_pop":        "C17002_001E",   # C17002 universe
    "fpl_under_50":          "C17002_002E",   # under 0.50 FPL
    "fpl_50_99":             "C17002_003E",   # 0.50–0.99 FPL
    "fpl_100_124":           "C17002_004E",   # 1.00–1.24 FPL
    "fpl_125_149":           "C17002_005E",   # 1.25–1.49 FPL

    # Health insurance coverage (B27001) — total + 18 uninsured cells
    "health_ins_total_pop":  "B27001_001E",
}
