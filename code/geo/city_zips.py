"""
City-to-ZCTA crosswalk utility.

Maps a Census incorporated place (city) to the ZIP Code Tabulation Areas
(ZCTAs) that predominantly fall within its boundaries, using the Census 2020
ZCTA-to-Place relationship file.

A ZCTA is included if >= threshold (default 40%) of its land area falls within
the city's Census place boundary. The 40% threshold captures near-boundary ZCTAs
that genuinely serve city residents without including truly suburban ZCTAs. This produces a consistent geographic
definition of "the city" across all data sources: IRS, IMLS, HRSA, and ACS.

Fallback for CDPs and unincorporated places (e.g. Honolulu, HI):
  Hawaii has no incorporated municipalities — cities like Honolulu are Census
  Designated Places (CDPs) and are absent from the ZCTA-to-Place file. When
  the place-based lookup returns no entries, city_to_zips() falls back to the
  ZCTA-to-County crosswalk, using the city's county_fips. This is a slightly
  broader geography (county vs. city boundary) but is the best available for
  CDP cities.

Sources:
  https://www2.census.gov/geo/docs/maps-data/data/rel2020/zcta520/
  tab20_zcta520_place20_natl.txt   (incorporated places)
  tab20_zcta520_county20_natl.txt  (counties — fallback)

Typical usage:
    from geo.city_zips import city_to_zips
    zips = city_to_zips("los_angeles")   # → set of 5-digit ZIP strings
    zips = city_to_zips("honolulu")      # → county fallback
"""

import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from config import PROJECT_ROOT, CITIES

# ── Place crosswalk ────────────────────────────────────────────────────────
_PLACE_URL  = (
    "https://www2.census.gov/geo/docs/maps-data/data/rel2020/zcta520/"
    "tab20_zcta520_place20_natl.txt"
)
_PLACE_PATH = PROJECT_ROOT / "data" / "geo" / "zcta_place.csv"

# ── County crosswalk (fallback for CDPs / unincorporated places) ───────────
_COUNTY_URL  = (
    "https://www2.census.gov/geo/docs/maps-data/data/rel2020/zcta520/"
    "tab20_zcta520_county20_natl.txt"
)
_COUNTY_PATH = PROJECT_ROOT / "data" / "geo" / "zcta_county.csv"

# Module-level caches
_place_cw:  pd.DataFrame | None = None
_county_cw: pd.DataFrame | None = None


def _load_crosswalk(url: str, path: Path, geoid_col: str) -> pd.DataFrame:
    """Download (if needed) and return a ZCTA relationship file as a DataFrame."""
    if path.exists():
        df = pd.read_csv(path, dtype={"zip": str, "geoid": str})
    else:
        print(f"  Downloading {path.name} from Census Bureau...")
        # Read all columns to avoid usecols ordering issues, then select
        raw = pd.read_csv(url, sep="|", dtype=str)
        raw.columns = [c.strip() for c in raw.columns]
        df = raw[["GEOID_ZCTA5_20", geoid_col, "AREALAND_ZCTA5_20", "AREALAND_PART"]].copy()
        df = df.rename(columns={
            "GEOID_ZCTA5_20":    "zip",
            geoid_col:           "geoid",
            "AREALAND_ZCTA5_20": "arealand_zcta",
            "AREALAND_PART":     "arealand_part",
        })
        df = df.dropna(subset=["zip", "geoid"])
        path.parent.mkdir(parents=True, exist_ok=True)
        df.to_csv(path, index=False)
        print(f"  Cached at {path} ({len(df):,} rows)")

    df["arealand_zcta"] = pd.to_numeric(df["arealand_zcta"], errors="coerce").fillna(0)
    df["arealand_part"] = pd.to_numeric(df["arealand_part"], errors="coerce").fillna(0)
    return df[df["arealand_zcta"] > 0].copy()


def _place_crosswalk() -> pd.DataFrame:
    global _place_cw
    if _place_cw is None:
        _place_cw = _load_crosswalk(_PLACE_URL, _PLACE_PATH, "GEOID_PLACE_20")
    return _place_cw


def _county_crosswalk() -> pd.DataFrame:
    global _county_cw
    if _county_cw is None:
        _county_cw = _load_crosswalk(_COUNTY_URL, _COUNTY_PATH, "GEOID_COUNTY_20")
    return _county_cw


def _zips_from_crosswalk(cw: pd.DataFrame, geoid: str, threshold: float) -> set:
    """Extract ZCTAs from a crosswalk DataFrame for a given GEOID."""
    subset = cw[cw["geoid"] == geoid].copy()
    if subset.empty:
        return set()
    subset["pct"] = subset["arealand_part"] / subset["arealand_zcta"]
    return set(subset.loc[subset["pct"] >= threshold, "zip"].str.zfill(5))


def city_to_zips(city_key: str, threshold: float = 0.4) -> set:
    """
    Return 5-digit ZCTAs (zero-padded strings) where at least `threshold`
    fraction of the ZCTA's land area falls within the city boundary.

    Default threshold is 0.40 (40% land area overlap). This captures near-boundary
    ZCTAs that genuinely serve city residents (the 40-49% band are near-urban-core
    ZCTAs, not suburban fringe). A 50% threshold was found to systematically miss
    FQHCs in cities like Raleigh (ZIP 27610 at 48.9%) and Fort Worth (ZIP 76114 at
    41.2%) — sites explicitly named for those cities.

    Primary lookup: Census incorporated place boundary (ZCTA-to-Place file).
    Fallback:       County boundary (ZCTA-to-County file), used when the city
                    is a CDP or unincorporated place absent from the place file
                    (e.g. Honolulu, HI).

    Args:
        city_key:  Key from CITIES config (e.g. "los_angeles")
        threshold: Minimum fraction of ZCTA land area within city (default 0.4)

    Returns:
        Set of zero-padded 5-digit ZIP strings, e.g. {"90001", "90002", ...}
    """
    city = CITIES[city_key]

    # ── Primary: place-based lookup ────────────────────────────────────────
    place_fips = city.get("place_fips", "")
    if place_fips:
        geoid_place = city["state_fips"].zfill(2) + str(place_fips).zfill(5)
        zips = _zips_from_crosswalk(_place_crosswalk(), geoid_place, threshold)
        if zips:
            return zips
        print(f"  [{city_key}] No place crosswalk match for GEOID {geoid_place} "
              f"— falling back to county crosswalk.")

    # ── Fallback: county-based lookup ──────────────────────────────────────
    county_fips_set = city.get("county_fips", set())
    if not county_fips_set:
        raise RuntimeError(
            f"No place OR county crosswalk entries found for '{city_key}'. "
            "Check place_fips and county_fips in cities.csv."
        )

    cw = _county_crosswalk()
    zips = set()
    for cf in county_fips_set:
        # county_fips entries are stored as 5-digit strings (e.g. "15003")
        geoid_county = str(cf).zfill(5)
        zips |= _zips_from_crosswalk(cw, geoid_county, threshold)

    if not zips:
        raise RuntimeError(
            f"No ZCTAs meet the {threshold:.0%} overlap threshold for '{city_key}' "
            f"via either place or county crosswalk. "
            "Verify place_fips and county_fips in cities.csv."
        )

    return zips
