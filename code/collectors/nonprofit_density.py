"""
Collector: IRS Nonprofit Density
Counts care-related nonprofits for a given city and calculates per-capita density.

Data source: IRS Exempt Organizations Business Master File (EO BMF)
  - Download from: https://www.irs.gov/charities-non-profits/exempt-organizations-business-master-file-extract-eo-bmf
  - One CSV per region; place in Downloaded Data/IRS EO BMF/
"""

import os
import sys
import pandas as pd
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from config import IRS_DATA_PATH, DATA_RAW, CITIES, NTEE_ALL_CARE, NTEE_CARE_INSTITUTIONS, NTEE_FAITH_BASED


def find_irs_file(state: str) -> Path:
    """Find the IRS EO BMF CSV for a given state abbreviation."""
    candidates = list(Path(IRS_DATA_PATH).glob("*.csv"))
    for f in candidates:
        if state.lower() in f.name.lower():
            return f
    raise FileNotFoundError(
        f"No IRS EO BMF CSV found for state '{state}' in {IRS_DATA_PATH}.\n"
        f"Available files: {[f.name for f in candidates]}"
    )


def load_irs_data(state: str) -> pd.DataFrame:
    path = find_irs_file(state)
    print(f"  Loading IRS data: {path.name}")
    df = pd.read_csv(path, dtype=str, low_memory=False)
    # Normalise column names — IRS files use uppercase
    df.columns = [c.strip().upper() for c in df.columns]
    return df


def filter_city_nonprofits(df: pd.DataFrame, city_cfg: dict, ntee_codes: list) -> pd.DataFrame:
    """
    Filter IRS data to a specific city and NTEE prefix list.
    Uses all known city-name variants so boroughs / neighbourhoods aren't missed.
    NTEE_CD is a multi-character code; we match on the first letter (the major group).
    """
    city_names = [n.upper() for n in city_cfg["irs_city_names"]]
    state = city_cfg["state"].upper()

    city_mask = (
        df["CITY"].str.upper().isin(city_names) &
        (df["STATE"].str.upper() == state)
    )
    city_df = df[city_mask].copy()

    ntee_prefixes = [c.upper() for c in ntee_codes]
    ntee_mask = city_df["NTEE_CD"].str[0].isin(ntee_prefixes)
    return city_df[ntee_mask].copy()


def collect(city_key: str = "nyc") -> dict:
    city = CITIES[city_key]
    print(f"\n=== Nonprofit Density — {city['name']} ===")

    df = load_irs_data(city["state"])
    pop = city["population"]

    results = {}

    for label, codes in [
        ("care_institutions", NTEE_CARE_INSTITUTIONS),
        ("faith_based",       NTEE_FAITH_BASED),
        ("all_care",          NTEE_ALL_CARE),
    ]:
        subset = filter_city_nonprofits(df, city, codes)
        count = len(subset)
        density = round((count / pop) * 10_000, 2)
        results[label] = {"count": count, "density_per_10k": density}
        print(f"  {label}: {count} orgs → {density} per 10,000")

    # Save raw filtered data
    out_dir = DATA_RAW / city_key
    out_dir.mkdir(parents=True, exist_ok=True)
    all_care_df = filter_city_nonprofits(df, city, NTEE_ALL_CARE)
    all_care_df.to_csv(out_dir / "nonprofits_care.csv", index=False)
    print(f"  Raw data saved to {out_dir / 'nonprofits_care.csv'}")

    return {
        "city": city_key,
        "metric": "nonprofit_density",
        "data": results,
    }


if __name__ == "__main__":
    import json
    city_key = sys.argv[1] if len(sys.argv) > 1 else "nyc"
    result = collect(city_key)
    print(json.dumps(result, indent=2))
