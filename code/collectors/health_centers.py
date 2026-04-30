"""
Collector: Community Health Center Density (HRSA)
Counts Federally Qualified Health Centers (FQHCs) per 100,000 residents.

Geography: ZIP-based filtering using the city's ZCTA boundary (>= 50% of
ZCTA land area within the city). Replaces county FIPS filtering to eliminate
county-sharing inflation for cities that are a fraction of their county.

Data source: HRSA Health Center Service Delivery and Look-Alike Sites
  - Downloaded as: Health_Center_Service_Delivery_and_LookAlike_Sites.xlsx
  - Place in: Downloaded Data/
"""

import sys
import json
import pandas as pd
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from config import HRSA_DATA_PATH, DATA_RAW, CITIES
from geo.zip_fips import normalize_zip
from geo.city_zips import city_to_zips

# HRSA site ZIP column — must be the SITE address ZIP, not the organization HQ ZIP.
# "Site Postal Code" is the correct column in current HRSA exports. Fallback
# candidates included for older file formats.
_ZIP_COL_CANDIDATES = [
    "Site Postal Code",
    "Site Address Zip Code",
    "Site Zip Code",
    "ZIP Code",
    "Zip Code",
    "ZIP",
]


# Module-level cache: HRSA Excel is large — load once per process.
_hrsa_df: pd.DataFrame | None = None


def load_hrsa() -> pd.DataFrame:
    global _hrsa_df
    if _hrsa_df is not None:
        return _hrsa_df
    path = Path(HRSA_DATA_PATH)
    if not path.exists():
        raise FileNotFoundError(f"HRSA file not found at {path}")
    print(f"  Loading {path.name}...")
    _hrsa_df = pd.read_excel(path, dtype=str)
    _hrsa_df.columns = [c.strip() for c in _hrsa_df.columns]
    return _hrsa_df


def _find_zip_col(df: pd.DataFrame) -> str:
    for candidate in _ZIP_COL_CANDIDATES:
        if candidate in df.columns:
            return candidate
    # Fallback: any column with "zip" in the name
    for col in df.columns:
        if "zip" in col.lower():
            return col
    raise KeyError(
        f"No ZIP column found in HRSA data. Columns present: {list(df.columns)}"
    )


def filter_city(df: pd.DataFrame, city_key: str) -> pd.DataFrame:
    """
    Filter HRSA data to active FQHC service-delivery sites within the city's
    ZCTA boundary. Excludes Look-Alike sites (not federally funded) and
    admin-only locations.
    """
    valid_zips = city_to_zips(city_key)
    zip_col    = _find_zip_col(df)
    state      = CITIES[city_key]["state"].upper()

    zip_mask      = df[zip_col].apply(normalize_zip).isin(valid_zips)
    # "Site State Abbreviation" is the correct site-level state column.
    # "Site Address State Abbreviation" was an older column name — check both.
    state_col = "Site State Abbreviation" if "Site State Abbreviation" in df.columns \
                else "Site Address State Abbreviation" if "Site Address State Abbreviation" in df.columns \
                else None
    state_mask    = df[state_col].str.upper() == state \
                    if state_col else pd.Series(True, index=df.index)
    status_mask   = df["Site Status Description"].str.upper() == "ACTIVE"
    fqhc_mask     = df["Health Center Type"].str.contains("Look-Alike", na=False) == False
    delivery_mask = df["Health Center Type Description"].str.upper().str.contains(
        "SERVICE DELIVERY", na=False
    )

    return df[zip_mask & state_mask & status_mask & fqhc_mask & delivery_mask].copy()


def collect(city_key: str = "nyc") -> dict:
    city = CITIES[city_key]
    pop  = city["population"]
    print(f"\n=== Health Center Density — {city['name']} ===")

    df      = load_hrsa()
    city_df = filter_city(df, city_key)

    count   = len(city_df)
    density = round(count / pop * 100_000, 2)
    print(f"  {count} FQHCs -> {density} per 100,000")

    out_dir = DATA_RAW / city_key
    out_dir.mkdir(parents=True, exist_ok=True)
    city_df.to_csv(out_dir / "health_centers.csv", index=False)
    print(f"  Raw data saved to {out_dir / 'health_centers.csv'}")

    return {
        "city":   city_key,
        "metric": "health_center_density",
        "data": {
            "fqhc_count":       count,
            "density_per_100k": density,
        },
    }


if __name__ == "__main__":
    city_key = sys.argv[1] if len(sys.argv) > 1 else "nyc"
    print(json.dumps(collect(city_key), indent=2))
