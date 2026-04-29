"""
Collector: Library Density (IMLS Public Libraries Survey FY2023)
- Location count + density: from outlet-level file (pls_fy23_outlet_pud23i.csv)
- Visits per capita: from administrative-entity file (PLS_FY23_AE_pud23i.csv)

Data source: https://www.imls.gov/research-tools/data-collection/public-libraries-survey
Place both CSVs in: Downloaded Data/Public Libraries Survey (PLS)/
"""

import sys
import json
import pandas as pd
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from config import IMLS_DATA_PATH, DATA_RAW, CITIES
from geo.zip_fips import normalize_zip
from geo.city_zips import city_to_zips

IMLS_DIR = Path(IMLS_DATA_PATH)


def _load(pattern: str) -> pd.DataFrame:
    files = list(IMLS_DIR.glob(pattern))
    if not files:
        raise FileNotFoundError(f"No file matching '{pattern}' in {IMLS_DIR}")
    df = pd.read_csv(files[0], dtype=str, low_memory=False, encoding="latin-1")
    df.columns = [c.strip().upper() for c in df.columns]
    print(f"  Loaded {files[0].name} ({len(df):,} rows)")
    return df


def _filter_city(df: pd.DataFrame, city_key: str,
                 state_col: str = "STABR", zip_col: str = "ZIP") -> pd.DataFrame:
    """Filter IMLS data to outlets whose ZIP falls within the city's ZCTA boundary."""
    valid_zips = city_to_zips(city_key)
    state_mask = df[state_col].str.upper() == CITIES[city_key]["state"].upper()
    zip_mask   = df[zip_col].apply(normalize_zip).isin(valid_zips)
    return df[state_mask & zip_mask].copy()


def collect(city_key: str = "nyc") -> dict:
    city = CITIES[city_key]
    pop  = city["population"]
    print(f"\n=== Library Density — {city['name']} ===")

    # ── Outlet file: count physical locations ─────────────────────────────────
    outlet_df  = _load("*outlet*.csv")
    city_outlets = _filter_city(outlet_df, city_key)
    count   = len(city_outlets)
    density = round(count / pop * 100_000, 2)
    print(f"  {count} library outlets -> {density} per 100,000")

    metrics = {"library_count": count, "density_per_100k": density}

    # ── AE file: visits per capita ────────────────────────────────────────────
    try:
        ae_df      = _load("*AE*.csv")
        city_ae    = _filter_city(ae_df, city_key)
        total_visits = pd.to_numeric(city_ae["VISITS"], errors="coerce").sum()
        vpc = round(total_visits / pop, 2)
        metrics["total_visits"]      = int(total_visits)
        metrics["visits_per_capita"] = vpc
        print(f"  Visits per capita: {vpc} ({int(total_visits):,} total)")
    except Exception as e:
        print(f"  Visits data unavailable: {e}")

    # ── Save ──────────────────────────────────────────────────────────────────
    out_dir = DATA_RAW / city_key
    out_dir.mkdir(parents=True, exist_ok=True)
    city_outlets.to_csv(out_dir / "libraries.csv", index=False)
    print(f"  Raw data saved to {out_dir / 'libraries.csv'}")

    return {"city": city_key, "metric": "library_density", "data": metrics}


if __name__ == "__main__":
    city_key = sys.argv[1] if len(sys.argv) > 1 else "nyc"
    print(json.dumps(collect(city_key), indent=2))
