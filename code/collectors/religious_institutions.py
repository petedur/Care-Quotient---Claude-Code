"""
Collector: Religious Institution Density
Source: 2020 U.S. Religion Census (ASARB), distributed via ARDA.
        data/reference/arda_2020_county.xlsx — County Summary sheet.

Metric: Total congregations across all denominations, per 100,000 residents.
Geography: Summed across all county FIPS codes assigned to each city in config.py.

Why ARDA over IRS EO BMF X3x:
  IRS X3x codes only capture congregations that individually filed with the IRS.
  Baptist and Catholic congregations are predominantly covered under group exemptions
  (national denominational rulings), so they do not appear individually in the BMF.
  The ARDA Religion Census counts every local congregation regardless of filing
  structure, yielding ~35x better coverage at the national level.

Data vintage: 2020 (most recent available; published June 2023).
"""

import json
import sys
import pandas as pd
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT_ROOT / "code"))
from config import CITIES

ARDA_FILE = PROJECT_ROOT / "data" / "reference" / "arda_2020_county.xlsx"
DATA_RAW   = PROJECT_ROOT / "data" / "raw"


def _load_arda() -> pd.DataFrame:
    df = pd.read_excel(ARDA_FILE, sheet_name="2020 County Summary")
    df["fips5"] = df["FIPS"].astype(str).str.zfill(5)
    return df


def collect_religious_institutions(city_key: str, arda: pd.DataFrame) -> dict | None:
    city = CITIES.get(city_key)
    if city is None:
        print(f"  SKIP {city_key}: not found in CITIES config")
        return None

    county_fips = city["county_fips"]
    matched = arda[arda["fips5"].isin(county_fips)]

    if matched.empty:
        print(f"  SKIP {city_key}: no ARDA county matches for FIPS {county_fips}")
        return None

    total_congregations = int(matched["Congregations"].sum())
    population = city["population"]
    per_100k = round(total_congregations / population * 100_000, 2)

    return {
        "city":                   city_key,
        "congregations":          total_congregations,
        "population":             population,
        "congregations_per_100k": per_100k,
        "counties_matched":       len(matched),
        "source":                 "ARDA 2020 U.S. Religion Census",
    }


def collect(city_key: str) -> dict | None:
    """Standard pipeline entry point — loads ARDA file and collects for one city."""
    if not ARDA_FILE.exists():
        raise FileNotFoundError(f"ARDA file not found at {ARDA_FILE}")
    arda = _load_arda()
    result = collect_religious_institutions(city_key, arda)
    if result is None:
        return None
    out_dir = DATA_RAW / city_key
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / "religious_institutions.json"
    out_path.write_text(json.dumps(result, indent=2))
    return result


def main(city_keys: list[str] | None = None):
    if not ARDA_FILE.exists():
        print(f"ERROR: ARDA file not found at {ARDA_FILE}")
        print("Download from: https://www.usreligioncensus.org/node/1639")
        return

    print("Loading ARDA 2020 county data...")
    arda = _load_arda()
    print(f"  {len(arda)} counties loaded")

    targets = city_keys or list(CITIES.keys())

    for city_key in targets:
        result = collect_religious_institutions(city_key, arda)
        if result is None:
            continue

        out_dir = DATA_RAW / city_key
        out_dir.mkdir(parents=True, exist_ok=True)
        out_path = out_dir / "religious_institutions.json"
        out_path.write_text(json.dumps(result, indent=2))
        print(f"  {city_key}: {result['congregations']} congregations, "
              f"{result['congregations_per_100k']}/100k")


if __name__ == "__main__":
    city_args = sys.argv[1:] or None
    main(city_args)
