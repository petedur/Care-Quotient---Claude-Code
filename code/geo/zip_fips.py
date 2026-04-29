"""
ZIP-to-county FIPS crosswalk utility.

Uses the Census 2020 ZCTA-to-county relationship file, cached at
data/geo/zcta_county.csv after first download.

Source:
  https://www2.census.gov/geo/docs/maps-data/data/rel2020/zcta520/
  tab20_zcta520_county20_natl.txt

Typical usage:
    from geo.zip_fips import county_to_zips
    zips = county_to_zips({"36061", "36005", "36047"})   # → set of ZIP strings
"""

import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from config import PROJECT_ROOT

_CROSSWALK_URL = (
    "https://www2.census.gov/geo/docs/maps-data/data/rel2020/zcta520/"
    "tab20_zcta520_county20_natl.txt"
)
_CROSSWALK_PATH = PROJECT_ROOT / "data" / "geo" / "zcta_county.csv"

# Module-level cache so we only read the file once per process
_crosswalk: pd.DataFrame | None = None


def _download() -> pd.DataFrame:
    """Download and cache the ZCTA-to-county relationship file."""
    print(f"  Downloading ZCTA crosswalk from Census Bureau...")
    df = pd.read_csv(
        _CROSSWALK_URL,
        sep="|",
        dtype=str,
        usecols=["GEOID_ZCTA5_20", "GEOID_COUNTY_20"],
    )
    df.columns = ["zip", "county_fips"]
    df = df.dropna().drop_duplicates()
    _CROSSWALK_PATH.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(_CROSSWALK_PATH, index=False)
    print(f"  Cached at {_CROSSWALK_PATH} ({len(df):,} rows)")
    return df


def load_crosswalk() -> pd.DataFrame:
    """Return the ZCTA-to-county crosswalk, downloading if not cached."""
    global _crosswalk
    if _crosswalk is not None:
        return _crosswalk
    if _CROSSWALK_PATH.exists():
        _crosswalk = pd.read_csv(_CROSSWALK_PATH, dtype=str).dropna()
    else:
        _crosswalk = _download()
    return _crosswalk


def county_to_zips(county_fips_set: set) -> set:
    """
    Return all 5-digit ZIP codes (ZCTAs) that fall within any of the given counties.

    Args:
        county_fips_set: set of 5-digit strings, e.g. {"36061", "36005"}

    Returns:
        set of zero-padded 5-digit ZIP strings, e.g. {"10001", "10002", ...}
    """
    cw = load_crosswalk()
    mask = cw["county_fips"].isin(county_fips_set)
    return set(cw.loc[mask, "zip"].str.zfill(5))


def normalize_zip(raw_zip: str) -> str:
    """
    Normalize a raw ZIP string to 5 digits.
    Handles ZIP+4 format ('10001-1234' → '10001') and zero-padding.
    """
    if not isinstance(raw_zip, str):
        return ""
    return raw_zip.split("-")[0].strip().zfill(5)
