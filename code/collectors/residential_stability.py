"""
Collector: Residential Stability (Census ACS)
Measures % of population living in the same home for 1+ years as a proxy
for embedded social networks.

Data source: Census Bureau ACS 5-year estimates, Table B07003
  - API docs: https://api.census.gov/data/2022/acs/acs5/variables.html
"""

import sys
import json
import requests
import pandas as pd
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from config import get_census_api_key, DATA_RAW, CITIES, CENSUS_ACS_VARIABLES

ACS_URL = "https://api.census.gov/data/2022/acs/acs5"


def _get(variables: list, state_fips: str, county_fips: str) -> list:
    """Single Census API request for a list of variables for one county."""
    params = {
        "key": get_census_api_key(),
        "get": ",".join(variables),
        "for": f"county:{county_fips}",
        "in":  f"state:{state_fips}",
    }
    r = requests.get(ACS_URL, params=params, timeout=30)
    r.raise_for_status()
    return r.json()


def collect(city_key: str = "nyc") -> dict:
    city = CITIES[city_key]
    print(f"\n=== Residential Stability — {city['name']} ===")

    same_house_var = CENSUS_ACS_VARIABLES["same_house_1yr"]
    pop_var        = CENSUS_ACS_VARIABLES["total_population"]
    state_fips     = city["state_fips"]

    rows = []
    for county_name, county_fips in city["county_fips"].items():
        print(f"  Querying {county_name} (FIPS {state_fips}{county_fips})...")
        try:
            data = _get([same_house_var, pop_var], state_fips, county_fips)
            # data[0] = headers, data[1] = values
            headers = data[0]
            values  = data[1]
            same_house = int(values[headers.index(same_house_var)])
            total_pop  = int(values[headers.index(pop_var)])
            pct = round(same_house / total_pop * 100, 2) if total_pop else 0
            rows.append({
                "county":      county_name,
                "same_house":  same_house,
                "population":  total_pop,
                "pct_stable":  pct,
            })
            print(f"    {pct}% stable ({same_house:,} / {total_pop:,})")
        except Exception as e:
            print(f"    ERROR for {county_name}: {e}")

    if not rows:
        raise RuntimeError(f"No data retrieved for {city['name']}")

    df = pd.DataFrame(rows)
    total_same  = df["same_house"].sum()
    total_pop   = df["population"].sum()
    city_pct    = round(total_same / total_pop * 100, 2) if total_pop else 0

    print(f"  City-wide: {city_pct}% stable")

    # Save
    out_dir = DATA_RAW / city_key
    out_dir.mkdir(parents=True, exist_ok=True)
    df.to_csv(out_dir / "residential_stability.csv", index=False)
    print(f"  Raw data saved to {out_dir / 'residential_stability.csv'}")

    return {
        "city":   city_key,
        "metric": "residential_stability",
        "data": {
            "city_pct_stable": city_pct,
            "total_population": int(total_pop),
            "counties": rows,
        },
    }


if __name__ == "__main__":
    city_key = sys.argv[1] if len(sys.argv) > 1 else "nyc"
    result = collect(city_key)
    print(json.dumps(result, indent=2))
