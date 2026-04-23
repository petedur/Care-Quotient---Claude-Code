"""
Configuration and constants for Care Capacity Index collectors.
API keys are loaded from the .env file in the project root — never hardcoded.
"""

import os
from pathlib import Path
from dotenv import load_dotenv

# Load .env from the project root (one level above /code)
_PROJECT_ROOT = Path(__file__).resolve().parent.parent
load_dotenv(_PROJECT_ROOT / ".env")

# ── Paths ─────────────────────────────────────────────────────────────────────

PROJECT_ROOT        = _PROJECT_ROOT
DOWNLOADED_DATA     = Path(r"C:\Users\peter\OneDrive\Documents\Coding\Vibecoding\VS Code Projects\PP\Downloaded Data")
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

CENSUS_API_KEY = os.environ.get("CENSUS_API_KEY")
if not CENSUS_API_KEY:
    raise EnvironmentError("CENSUS_API_KEY not set. Copy .env.example to .env and add your key.")

# ── City definitions ──────────────────────────────────────────────────────────
# Each city entry contains everything needed to filter national datasets.
# county_fips: list of "SSCCC" strings (state FIPS + county FIPS, zero-padded)
# irs_city_names: all city-name variants that appear in IRS EO BMF for this city
# state_fips: 2-digit string

CITIES = {
    "nyc": {
        "name": "New York City",
        "state": "NY",
        "state_fips": "36",
        "population": 8_335_897,
        "county_fips": {
            "New York (Manhattan)": "061",
            "Bronx":               "005",
            "Kings (Brooklyn)":    "047",
            "Queens":              "081",
            "Richmond (Staten Island)": "001",
        },
        # IRS EO BMF uses city names at the borough level
        "irs_city_names": ["NEW YORK", "BROOKLYN", "BRONX", "QUEENS",
                           "STATEN ISLAND", "FLUSHING", "JAMAICA"],
    },
    "chicago": {
        "name": "Chicago",
        "state": "IL",
        "state_fips": "17",
        "population": 2_696_555,
        "county_fips": {
            "Cook": "031",
        },
        "irs_city_names": ["CHICAGO"],
    },
    "los_angeles": {
        "name": "Los Angeles",
        "state": "CA",
        "state_fips": "06",
        "population": 3_898_747,
        "county_fips": {
            "Los Angeles": "037",
        },
        "irs_city_names": ["LOS ANGELES"],
    },
    "houston": {
        "name": "Houston",
        "state": "TX",
        "state_fips": "48",
        "population": 2_304_580,
        "county_fips": {
            "Harris": "201",
        },
        "irs_city_names": ["HOUSTON"],
    },
    "boston": {
        "name": "Boston",
        "state": "MA",
        "state_fips": "25",
        "population": 675_647,
        "county_fips": {
            "Suffolk": "025",
        },
        "irs_city_names": ["BOSTON"],
    },
}

# ── NTEE codes ────────────────────────────────────────────────────────────────
# Pillar 1 — Social Support & Connection
NTEE_SOCIAL_SUPPORT = ["A", "B", "P"]   # Arts/culture, Education, Human Services
# Pillar 2 — Institutions of Care
NTEE_CARE_INSTITUTIONS = ["D", "E", "F", "K"]  # Health, Mental Health, Substance Abuse, Food
# Faith-based (spans both pillars)
NTEE_FAITH_BASED = ["X"]   # Religion-related

# All care-relevant codes combined
NTEE_ALL_CARE = list(set(NTEE_SOCIAL_SUPPORT + NTEE_CARE_INSTITUTIONS + NTEE_FAITH_BASED))

# ── Census ACS variables ──────────────────────────────────────────────────────
CENSUS_ACS_VARIABLES = {
    "same_house_1yr": "B07003_004E",   # Population in same house 1 year ago (residential stability proxy)
    "total_population": "B01003_001E",
}
