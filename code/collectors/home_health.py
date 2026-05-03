"""
V5 STUB — NOT WIRED INTO PIPELINE

Home health data cannot be attributed cleanly to a city using public CMS data:
- HQ-ZIP filtering undercounts (agencies in suburbs miss compact-city residents)
- Service-area filtering overcounts (statewide agencies inflate episode totals)
- Episode counts are attributed to the agency HQ, not the patient's city

Revisit in V5 once a clean geographic attribution method is identified.
The collectors and cache files are preserved for reference.

─────────────────────────────────────────────────────────────────────────────

Collector: Home Health Agency Capacity (CMS Care Compare)
Estimates Medicare home health patients per 1,000 residents aged 65+.

Geography: ZIP-based filtering using the city's ZCTA boundary (>= 40% of
ZCTA land area within the city), same crosswalk as all other collectors.

Data source: CMS Care Compare — Home Health Agency Provider Information
  Dataset ID: 6jpm-sxkc
  Updated: monthly/quarterly (April 2026 data used at build time)
  Auto-downloaded and cached at data/cache/cms_home_health.csv

Patient volume estimation:
  CMS home health data does not provide a daily census equivalent. Patient
  volume is derived from the episode count used in the Medicare spending
  comparison measure — the total number of Medicare-certified episodes at
  each agency over the measurement period (approximately 12 months).

  Episodes are converted to a daily-census equivalent using the CMS-published
  national average home health episode length of 35 days:
    daily_equivalent = annual_episodes × 35 / 365

  This conversion is documented as a modelling assumption. The 35-day average
  is drawn from CMS Home Health PPS episode data and is used solely to make
  home health patient volume commensurable with nursing home daily census for
  the combined elder care metric.

Limitation: Covers only Medicare-certified home health agencies. Private-pay
and Medicaid-only agencies are not included. Agencies are filtered by their
office ZIP code, not their service area — agencies headquartered outside a
city but serving it will be missed, and vice versa. This is a known limitation
shared with the nursing homes collector.
"""

import sys
import json
import requests
import pandas as pd
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from config import PROJECT_ROOT, DATA_RAW, CITIES, get_census_api_key
from collectors.utils import census_get_zctas
from geo.city_zips import city_to_zips
from geo.zip_fips import normalize_zip

# ── CMS data configuration ────────────────────────────────────────────────────

_METASTORE_URL = (
    "https://data.cms.gov/provider-data/api/1/metastore/"
    "schemas/dataset/items/6jpm-sxkc"
)
_METASTORE_URL_ZIPS = (
    "https://data.cms.gov/provider-data/api/1/metastore/"
    "schemas/dataset/items/m5eg-upu5"
)
_CACHE_PATH      = PROJECT_ROOT / "data" / "cache" / "cms_home_health.csv"
_CACHE_PATH_ZIPS = PROJECT_ROOT / "data" / "cache" / "cms_home_health_zips.csv"

# CMS-published national average home health episode length (days).
# Source: CMS Home Health Prospective Payment System episode data.
# Used to convert annual episodes → daily-census equivalent.
_EPISODE_LENGTH_DAYS = 35

# Column name after lowercasing + space→underscore normalization
_EPISODES_COL = (
    "no._of_episodes_to_calc_how_much_medicare_spends_per_episode_of_care_"
    "at_agency,_compared_to_spending_at_all_agencies_(national)"
)

# ── ACS 65+ population variables — same as nursing_homes.py ──────────────────

ACS_URL = "https://api.census.gov/data/2022/acs/acs5"

_POP_65_PLUS_VARS = [
    "B01001_020E", "B01001_021E", "B01001_022E",
    "B01001_023E", "B01001_024E", "B01001_025E",
    "B01001_044E", "B01001_045E", "B01001_046E",
    "B01001_047E", "B01001_048E", "B01001_049E",
]

# ── CMS download ──────────────────────────────────────────────────────────────

_hh_df: pd.DataFrame | None = None


def load_cms_data(force_refresh: bool = False) -> pd.DataFrame:
    global _hh_df
    if _hh_df is not None and not force_refresh:
        return _hh_df

    _CACHE_PATH.parent.mkdir(parents=True, exist_ok=True)

    if not _CACHE_PATH.exists() or force_refresh:
        print("  Fetching CMS home health CSV URL from metastore...")
        meta = requests.get(_METASTORE_URL, timeout=30).json()
        csv_url = None
        for dist in meta.get("distribution", []):
            if "csv" in dist.get("mediaType", "").lower() or \
               dist.get("format", "").upper() == "CSV":
                csv_url = dist.get("downloadURL") or dist.get("accessURL", "")
                break
        if not csv_url:
            raise RuntimeError(
                f"Could not find CSV URL in CMS home health metastore response."
            )
        print(f"  Downloading CMS home health data...")
        resp = requests.get(csv_url, timeout=120)
        resp.raise_for_status()
        _CACHE_PATH.write_bytes(resp.content)
        print(f"  Cached at {_CACHE_PATH} ({_CACHE_PATH.stat().st_size // 1024:,} KB)")
    else:
        print(f"  Using cached CMS home health data at {_CACHE_PATH}")

    df = pd.read_csv(_CACHE_PATH, dtype=str, low_memory=False)
    df.columns = [c.strip().lower().replace(" ", "_") for c in df.columns]
    _hh_df = df
    return _hh_df


_zip_df: pd.DataFrame | None = None


def load_service_area(force_refresh: bool = False) -> pd.DataFrame:
    """Load the CMS agency-to-ZIP service area file (one row per agency-ZIP pair)."""
    global _zip_df
    if _zip_df is not None and not force_refresh:
        return _zip_df

    _CACHE_PATH_ZIPS.parent.mkdir(parents=True, exist_ok=True)

    if not _CACHE_PATH_ZIPS.exists() or force_refresh:
        print("  Fetching CMS home health service area ZIP URL from metastore...")
        meta = requests.get(_METASTORE_URL_ZIPS, timeout=30).json()
        csv_url = None
        for dist in meta.get("distribution", []):
            if "csv" in dist.get("mediaType", "").lower() or \
               dist.get("format", "").upper() == "CSV":
                csv_url = dist.get("downloadURL") or dist.get("accessURL", "")
                break
        if not csv_url:
            raise RuntimeError("Could not find CSV URL in CMS home health ZIPs metastore.")
        print("  Downloading CMS home health service area data...")
        resp = requests.get(csv_url, timeout=120)
        resp.raise_for_status()
        _CACHE_PATH_ZIPS.write_bytes(resp.content)
        print(f"  Cached ({_CACHE_PATH_ZIPS.stat().st_size // 1024:,} KB)")
    else:
        print(f"  Using cached service area data at {_CACHE_PATH_ZIPS}")

    df = pd.read_csv(_CACHE_PATH_ZIPS, dtype=str)
    df.columns = [c.strip().lower().replace(" ", "_") for c in df.columns]
    # Normalize ZIP and CCN
    df["zip_code"] = df["zip_code"].apply(normalize_zip)
    df["ccn"] = df["cms_certification_number_(ccn)"].str.strip()
    _zip_df = df
    return _zip_df


def filter_city(provider_df: pd.DataFrame, city_key: str) -> pd.DataFrame:
    """
    Find all agencies that serve any ZIP in the city, using the service area file.
    An agency qualifies if at least one of the ZIPs it serves falls within the
    city's ZCTA boundary — regardless of where the agency is headquartered.
    """
    valid_zips = city_to_zips(city_key)
    state = CITIES[city_key]["state"].upper()

    zip_df = load_service_area()

    # CCNs that serve at least one city ZIP in the correct state
    state_mask   = zip_df["state"].str.upper() == state
    serving_mask = zip_df["zip_code"].isin(valid_zips)
    city_ccns    = set(zip_df.loc[state_mask & serving_mask, "ccn"].unique())

    # Normalize CCN in provider file for join
    provider_df = provider_df.copy()
    provider_df["ccn"] = provider_df["cms_certification_number_(ccn)"].str.strip()

    return provider_df[provider_df["ccn"].isin(city_ccns)].copy()


# ── ACS 65+ population ────────────────────────────────────────────────────────

def get_population_65plus(city_key: str) -> int:
    city = CITIES[city_key]
    city_zctas = city_to_zips(city_key)
    zcta_rows = census_get_zctas(
        ACS_URL, _POP_65_PLUS_VARS, city["state_fips"],
        city_zctas, get_census_api_key(),
    )
    return sum(
        sum(row.get(v, 0) for v in _POP_65_PLUS_VARS)
        for row in zcta_rows
    )


# ── Main collector ────────────────────────────────────────────────────────────

def collect(city_key: str = "nyc") -> dict:
    city = CITIES[city_key]
    print(f"\n=== Home Health Capacity — {city['name']} ===")

    df = load_cms_data()
    city_df = filter_city(df, city_key)

    agency_count = len(city_df)

    # Annual episodes — primary volume measure
    city_df = city_df.copy()
    raw_episodes = city_df[_EPISODES_COL] if _EPISODES_COL in city_df.columns \
        else pd.Series(["0"] * len(city_df))
    city_df["episodes"] = pd.to_numeric(
        raw_episodes.astype(str).str.replace(",", "", regex=False),
        errors="coerce"
    ).fillna(0)

    total_episodes = int(city_df["episodes"].sum())

    # Convert annual episodes → daily census equivalent
    daily_equivalent = round(total_episodes * _EPISODE_LENGTH_DAYS / 365, 1)

    print(f"  {agency_count} agencies, {total_episodes:,} annual episodes, "
          f"~{daily_equivalent:.0f} daily-equivalent patients")

    # 65+ population denominator
    print(f"  Fetching 65+ population from ACS...")
    pop_65plus = get_population_65plus(city_key)
    print(f"  Population 65+: {pop_65plus:,}")

    # Core output: daily-equivalent patients per 1,000 residents 65+
    patients_per_1k_65plus = round(daily_equivalent / pop_65plus * 1_000, 2) \
        if pop_65plus > 0 else 0.0

    # Diagnostic: agencies per 100k residents 65+
    agencies_per_100k_65plus = round(agency_count / pop_65plus * 100_000, 2) \
        if pop_65plus > 0 else 0.0

    print(f"  {patients_per_1k_65plus} home health patients per 1,000 residents 65+")

    # Save raw agency-level data
    out_dir = DATA_RAW / city_key
    out_dir.mkdir(parents=True, exist_ok=True)

    keep_cols = [c for c in [
        "cms_certification_number_(ccn)", "provider_name", "city/town", "state",
        "zip_code", "type_of_ownership", "certification_date",
        "quality_of_patient_care_star_rating", "episodes",
    ] if c in city_df.columns]

    city_df[keep_cols].to_csv(out_dir / "home_health.csv", index=False)
    print(f"  Raw data saved to {out_dir / 'home_health.csv'}")

    return {
        "city":   city_key,
        "metric": "home_health",
        "data": {
            "agency_count":              agency_count,
            "annual_episodes":           total_episodes,
            "daily_equivalent_patients": daily_equivalent,
            "population_65plus":         pop_65plus,
            "patients_per_1k_65plus":    patients_per_1k_65plus,
            "agencies_per_100k_65plus":  agencies_per_100k_65plus,
        },
    }


if __name__ == "__main__":
    city_key = sys.argv[1] if len(sys.argv) > 1 else "nyc"
    print(json.dumps(collect(city_key), indent=2))
