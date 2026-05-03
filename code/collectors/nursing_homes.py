"""
Collector: Nursing Home Capacity (CMS Care Compare)
Counts Medicare/Medicaid-certified nursing home beds per 1,000 residents aged 65+.

Geography: ZIP-based filtering using the city's ZCTA boundary (>= 40% of
ZCTA land area within the city), same crosswalk as all other collectors.

Data source: CMS Care Compare — Nursing Home Provider Information
  Dataset ID: 4pq5-n9py
  Updated: monthly/quarterly (April 2026 data used at build time)
  Auto-downloaded and cached at data/cache/cms_nursing_homes.csv

Denominator: Population aged 65+ from ACS 5-year estimates (B01001), summed
across city ZCTAs. Using total population would dilute the metric in cities
with younger demographics — elder care infrastructure should be sized against
the population it plausibly serves.

Limitation: CMS Care Compare covers only Medicare and/or Medicaid certified
skilled nursing facilities. Assisted living, residential care homes, and
private-pay-only facilities are not included in any national flat-file dataset;
they are regulated at the state level. This metric measures public-safety-net
elder care capacity, which is the most relevant dimension for this index.
"""

import sys
import json
import pandas as pd
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from config import PROJECT_ROOT, DATA_RAW, CITIES, get_census_api_key
from collectors.utils import census_get_zctas, http_get_with_retry
from geo.city_zips import city_to_zips
from geo.zip_fips import normalize_zip

# ── CMS data configuration ────────────────────────────────────────────────────

_METASTORE_URL = (
    "https://data.cms.gov/provider-data/api/1/metastore/"
    "schemas/dataset/items/4pq5-n9py"
)
_CACHE_PATH = PROJECT_ROOT / "data" / "cache" / "cms_nursing_homes.csv"

# ── ACS 65+ population variables (B01001) ─────────────────────────────────────

ACS_URL = "https://api.census.gov/data/2022/acs/acs5"

# All male + female age bands from 65 onward
_POP_65_PLUS_VARS = [
    "B01001_020E",  # male 65–66
    "B01001_021E",  # male 67–69
    "B01001_022E",  # male 70–74
    "B01001_023E",  # male 75–79
    "B01001_024E",  # male 80–84
    "B01001_025E",  # male 85+
    "B01001_044E",  # female 65–66
    "B01001_045E",  # female 67–69
    "B01001_046E",  # female 70–74
    "B01001_047E",  # female 75–79
    "B01001_048E",  # female 80–84
    "B01001_049E",  # female 85+
]

# ── CMS download ──────────────────────────────────────────────────────────────

# Columns expected in the normalized (lowercase + underscores) CMS CSV.
# If CMS renames a column the collector will raise a clear error rather than
# silently producing zeros.
_REQUIRED_COLS = {"zip_code", "state", "number_of_certified_beds"}


def _get_cms_csv_url() -> str:
    """Query the CMS metastore API to get the current download URL for the CSV."""
    resp = http_get_with_retry(_METASTORE_URL, timeout=30, label="CMS metastore")
    meta = resp.json()
    for dist in meta.get("distribution", []):
        is_csv = (
            dist.get("format", "").upper() == "CSV"
            or "csv" in dist.get("mediaType", "").lower()
        )
        if is_csv:
            url = dist.get("downloadURL") or dist.get("accessURL", "")
            if url:
                return url
    raise RuntimeError(
        "Could not find CSV download URL in CMS metastore response. "
        f"Distribution entries: {meta.get('distribution', [])}"
    )


_cms_df: pd.DataFrame | None = None


def load_cms_data(force_refresh: bool = False) -> pd.DataFrame:
    """Download and cache CMS nursing home provider data. Re-uses cache if present."""
    global _cms_df
    if _cms_df is not None and not force_refresh:
        return _cms_df

    _CACHE_PATH.parent.mkdir(parents=True, exist_ok=True)

    if not _CACHE_PATH.exists() or force_refresh:
        print("  Fetching CMS nursing home CSV URL from metastore...")
        csv_url = _get_cms_csv_url()
        print(f"  Downloading CMS data from {csv_url[:80]}...")
        resp = http_get_with_retry(csv_url, timeout=120, label="CMS nursing homes CSV")
        _CACHE_PATH.write_bytes(resp.content)
        print(f"  Cached at {_CACHE_PATH} ({_CACHE_PATH.stat().st_size // 1024:,} KB)")
    else:
        print(f"  Using cached CMS data at {_CACHE_PATH}")

    _cms_df = pd.read_csv(_CACHE_PATH, dtype=str, low_memory=False)
    _cms_df.columns = [c.strip().lower().replace(" ", "_") for c in _cms_df.columns]

    missing = _REQUIRED_COLS - set(_cms_df.columns)
    if missing:
        raise RuntimeError(
            f"CMS nursing home CSV is missing expected columns: {sorted(missing)}. "
            "CMS may have changed their schema — check the dataset at "
            "https://data.cms.gov/provider-data/dataset/4pq5-n9py and update "
            "_REQUIRED_COLS in collectors/nursing_homes.py."
        )

    return _cms_df


def filter_city(df: pd.DataFrame, city_key: str) -> pd.DataFrame:
    """Filter CMS data to active nursing home facilities within the city's ZCTAs."""
    valid_zips = city_to_zips(city_key)
    state = CITIES[city_key]["state"].upper()

    zip_mask   = df["zip_code"].apply(normalize_zip).isin(valid_zips)
    state_mask = df["state"].str.upper() == state

    return df[zip_mask & state_mask].copy()


# ── ACS 65+ population ────────────────────────────────────────────────────────

def get_population_65plus(city_key: str) -> tuple[int, int]:
    """
    Return (population_65plus, total_pop_from_acs) for the city's ZCTAs.
    Uses ACS 5-year estimates (2022), same vintage as other collectors.
    """
    city = CITIES[city_key]
    city_zctas = city_to_zips(city_key)

    zcta_rows = census_get_zctas(
        ACS_URL,
        _POP_65_PLUS_VARS,
        city["state_fips"],
        city_zctas,
        get_census_api_key(),
    )

    pop_65plus = sum(
        sum(row.get(v, 0) for v in _POP_65_PLUS_VARS)
        for row in zcta_rows
    )
    return pop_65plus


# ── Main collector ────────────────────────────────────────────────────────────

def collect(city_key: str = "nyc", force_refresh: bool = False) -> dict:
    city = CITIES[city_key]
    print(f"\n=== Nursing Home Capacity — {city['name']} ===")

    df = load_cms_data(force_refresh=force_refresh)
    city_df = filter_city(df, city_key)

    facility_count = len(city_df)

    # Certified beds — convert to numeric, treat missing as 0
    city_df = city_df.copy()
    city_df["beds"] = pd.to_numeric(
        city_df.get("number_of_certified_beds", pd.Series(dtype=str)),
        errors="coerce"
    ).fillna(0).astype(int)

    total_beds = int(city_df["beds"].sum())

    # Residents per day — utilization proxy
    city_df["avg_residents"] = pd.to_numeric(
        city_df.get("average_number_of_residents_per_day", pd.Series(dtype=str)),
        errors="coerce"
    ).fillna(0)
    avg_daily_residents = round(city_df["avg_residents"].sum(), 1)

    print(f"  {facility_count} facilities, {total_beds} certified beds, "
          f"{avg_daily_residents:.0f} avg daily residents")

    # 65+ population denominator
    print(f"  Fetching 65+ population from ACS...")
    pop_65plus = get_population_65plus(city_key)
    print(f"  Population 65+: {pop_65plus:,}")

    # Core metric: certified beds per 1,000 residents 65+
    beds_per_1k_65plus = round(total_beds / pop_65plus * 1_000, 2) \
        if pop_65plus > 0 else 0.0

    # Diagnostic: facilities per 100k residents 65+
    facilities_per_100k_65plus = round(facility_count / pop_65plus * 100_000, 2) \
        if pop_65plus > 0 else 0.0

    print(f"  {beds_per_1k_65plus} beds per 1,000 residents 65+")
    print(f"  {facilities_per_100k_65plus} facilities per 100k residents 65+")

    # Save raw facility-level data
    out_dir = DATA_RAW / city_key
    out_dir.mkdir(parents=True, exist_ok=True)

    keep_cols = [c for c in [
        "cms_certification_number_ccn", "provider_name", "citytown", "state",
        "zip_code", "ownership_type", "provider_type",
        "number_of_certified_beds", "average_number_of_residents_per_day",
        "overall_rating", "beds",
    ] if c in city_df.columns]

    city_df[keep_cols].to_csv(out_dir / "nursing_homes.csv", index=False)

    # Summary metrics for ETL — avoids re-running ACS query at ETL time
    import json as _json
    summary = {
        "facility_count":             facility_count,
        "certified_beds":             total_beds,
        "avg_daily_residents":        avg_daily_residents,
        "population_65plus":          pop_65plus,
        "beds_per_1k_65plus":         beds_per_1k_65plus,
        "facilities_per_100k_65plus": facilities_per_100k_65plus,
    }
    (out_dir / "nursing_homes_meta.json").write_text(_json.dumps(summary))
    print(f"  Raw data saved to {out_dir / 'nursing_homes.csv'}")

    return {
        "city":   city_key,
        "metric": "nursing_homes",
        "data": {
            "facility_count":             facility_count,
            "certified_beds":             total_beds,
            "avg_daily_residents":        avg_daily_residents,
            "population_65plus":          pop_65plus,
            "beds_per_1k_65plus":         beds_per_1k_65plus,
            "facilities_per_100k_65plus": facilities_per_100k_65plus,
        },
    }


if __name__ == "__main__":
    city_key = sys.argv[1] if len(sys.argv) > 1 else "nyc"
    print(json.dumps(collect(city_key), indent=2))
