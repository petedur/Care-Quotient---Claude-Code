"""
Collector: IRS Nonprofit Density
Counts care-related nonprofits by NTEE category for a given city.

Data source: IRS Exempt Organizations Business Master File (EO BMF)
  - Download from: https://www.irs.gov/charities-non-profits/exempt-organizations-business-master-file-extract-eo-bmf
  - One CSV per region; place in Downloaded Data/IRS EO BMF/

NTEE prefix matching:
  - Single-character codes (e.g. "P") match the first letter of NTEE_CD.
  - Multi-character codes (e.g. "X3") match as a prefix of NTEE_CD.
  This lets us distinguish X30 (Faith-Based Human Services) from X21
  (Protestant) without hardcoding every sub-code.
"""

import os
import sys
import json
import pandas as pd
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from config import (
    IRS_DATA_PATH, IRS_STATE_TO_REGION, DATA_RAW, CITIES,
    NTEE_SOCIAL_SUPPORT, NTEE_CARE_INSTITUTIONS, NTEE_FAITH_BASED, NTEE_ALL_CARE,
)
from geo.zip_fips import normalize_zip
from geo.city_zips import city_to_zips


def find_irs_file(state: str) -> Path:
    region_prefix = IRS_STATE_TO_REGION.get(state.upper())
    if not region_prefix:
        raise ValueError(f"No IRS region mapping for state '{state}'")
    candidates = list(Path(IRS_DATA_PATH).glob("*.csv"))
    for f in candidates:
        if f.name.startswith(region_prefix):
            return f
    raise FileNotFoundError(
        f"No IRS file matching '{region_prefix}' in {IRS_DATA_PATH}.\n"
        f"Available files: {[f.name for f in candidates]}"
    )


def load_irs_data(state: str) -> pd.DataFrame:
    path = find_irs_file(state)
    print(f"  Loading IRS data: {path.name}")
    df = pd.read_csv(path, dtype=str, low_memory=False, encoding="latin-1")
    df.columns = [c.strip().upper() for c in df.columns]
    return df


def _ntee_mask(series: pd.Series, codes: list) -> pd.Series:
    """
    Match NTEE codes by prefix.
    Single-char codes match only the first letter (e.g. "P" -> P01, P20...).
    Multi-char codes match as prefix (e.g. "X3" -> X30, X31...).
    """
    mask = pd.Series(False, index=series.index)
    clean = series.str.upper().fillna("")
    for code in codes:
        code = code.upper()
        if len(code) == 1:
            mask |= clean.str[0] == code
        else:
            mask |= clean.str.startswith(code)
    return mask


def filter_city(df: pd.DataFrame, city_key: str) -> pd.DataFrame:
    """Filter IRS data to orgs whose ZIP falls within the city's ZCTA boundary."""
    valid_zips = city_to_zips(city_key)
    state = CITIES[city_key]["state"].upper()
    normalized = df["ZIP"].apply(normalize_zip)
    return df[
        (df["STATE"].str.upper() == state) &
        normalized.isin(valid_zips)
    ].copy()


def collect(city_key: str = "nyc") -> dict:
    city = CITIES[city_key]
    pop  = city["population"]
    print(f"\n=== Nonprofit Density -- {city['name']} ===")

    df      = load_irs_data(city["state"])
    city_df = filter_city(df, city_key)
    print(f"  {len(city_df)} total orgs in city")

    results = {}

    categories = [
        ("social_support",    NTEE_SOCIAL_SUPPORT,    "NTEE P  — Human Services (Pillar 1)"),
        ("care_institutions", NTEE_CARE_INSTITUTIONS, "NTEE E/F/K — Health, Mental Health, Food (Pillar 2)"),
        ("faith_based",       NTEE_FAITH_BASED,       "NTEE X3x — Faith-Based Human Services (Pillar 2)"),
        ("all_care",          NTEE_ALL_CARE,          "All care-relevant codes (diagnostic)"),
    ]

    all_care_df = None
    for label, codes, description in categories:
        subset  = city_df[_ntee_mask(city_df["NTEE_CD"], codes)].copy()
        count   = len(subset)
        density = round(count / pop * 10_000, 2)
        results[label] = {"count": count, "density_per_10k": density}
        print(f"  {label}: {count} orgs -> {density} per 10,000  [{description}]")
        if label == "all_care":
            all_care_df = subset

    # Save raw filtered data for auditability
    out_dir = DATA_RAW / city_key
    out_dir.mkdir(parents=True, exist_ok=True)
    if all_care_df is not None:
        all_care_df.to_csv(out_dir / "nonprofits_care.csv", index=False)
    print(f"  Raw data saved to {out_dir / 'nonprofits_care.csv'}")

    return {
        "city":   city_key,
        "metric": "nonprofit_density",
        "data":   results,
    }


if __name__ == "__main__":
    city_key = sys.argv[1] if len(sys.argv) > 1 else "nyc"
    print(json.dumps(collect(city_key), indent=2))
