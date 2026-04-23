"""
Collector: Community Health Center Density (HRSA)
Counts Federally Qualified Health Centers (FQHCs) per 100,000 residents.

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


def load_hrsa() -> pd.DataFrame:
    path = Path(HRSA_DATA_PATH)
    if not path.exists():
        raise FileNotFoundError(f"HRSA file not found at {path}")
    print(f"  Loading {path.name}...")
    df = pd.read_excel(path, dtype=str)
    df.columns = [c.strip() for c in df.columns]
    return df


def filter_city(df: pd.DataFrame, city_cfg: dict) -> pd.DataFrame:
    """
    Filter HRSA data to active FQHC sites for a given city.
    Uses state + city name matching; excludes Look-Alike sites (not federally funded).
    """
    state = city_cfg["state"].upper()
    city_names = [n.upper() for n in city_cfg["irs_city_names"]]

    state_mask = df["Site State Abbreviation"].str.upper() == state
    city_mask  = df["Site City"].str.upper().isin(city_names)

    # Active sites only
    status_mask = df["Site Status Description"].str.upper() == "ACTIVE"

    # FQHCs only — exclude Look-Alike sites (not federally funded)
    fqhc_mask = df["Health Center Type"].str.contains("Look-Alike", na=False) == False

    # Service delivery sites only — exclude admin-only locations
    delivery_mask = df["Health Center Type Description"].str.upper().str.contains("SERVICE DELIVERY", na=False)

    return df[state_mask & city_mask & status_mask & fqhc_mask & delivery_mask].copy()


def collect(city_key: str = "nyc") -> dict:
    city = CITIES[city_key]
    pop  = city["population"]
    print(f"\n=== Health Center Density — {city['name']} ===")

    df      = load_hrsa()
    city_df = filter_city(df, city)

    count   = len(city_df)
    density = round(count / pop * 100_000, 2)
    print(f"  {count} FQHCs -> {density} per 100,000")

    # Save
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
