"""
Collector: Residential Stability (Census ACS)
Measures % of population living in the same home for 1+ years as a proxy
for embedded social networks.

Geography: ZCTA-level aggregation within the city's Census place boundary
(>= 50% of ZCTA land area within the city). Replaces county-level queries
to eliminate county-sharing inflation for cities that are a fraction of
their county.

Data source: Census Bureau ACS 5-year estimates, Table B07003
  - API docs: https://api.census.gov/data/2022/acs/acs5/variables.html
"""

import sys
import json
import pandas as pd
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from config import get_census_api_key, DATA_RAW, CITIES, CENSUS_ACS_VARIABLES
from collectors.utils import census_get_zctas
from geo.city_zips import city_to_zips

ACS_URL = "https://api.census.gov/data/2022/acs/acs5"


def collect(city_key: str = "nyc") -> dict:
    city = CITIES[city_key]
    print(f"\n=== Residential Stability — {city['name']} ===")

    same_house_var = CENSUS_ACS_VARIABLES["same_house_1yr"]
    pop_var        = CENSUS_ACS_VARIABLES["total_population"]
    state_fips     = city["state_fips"]

    city_zctas = city_to_zips(city_key)
    print(f"  City ZCTAs: {len(city_zctas)} ZIP codes")

    zcta_rows = census_get_zctas(
        ACS_URL,
        [same_house_var, pop_var],
        state_fips,
        city_zctas,
        get_census_api_key(),
    )

    if not zcta_rows:
        raise RuntimeError(
            f"No ZCTA data returned for {city['name']} — "
            "check place_fips in cities.csv and verify ZCTAs are in state."
        )

    rows = []
    for r in zcta_rows:
        same_house = r[same_house_var]
        total_pop  = r[pop_var]
        pct = round(same_house / total_pop * 100, 2) if total_pop else 0
        rows.append({
            "zcta":       r["zcta"],
            "same_house": same_house,
            "population": total_pop,
            "pct_stable": pct,
        })

    df = pd.DataFrame(rows)
    total_same = df["same_house"].sum()
    total_pop  = df["population"].sum()
    city_pct   = round(total_same / total_pop * 100, 2) if total_pop else 0

    print(f"  City-wide: {city_pct}% stable ({int(total_same):,} / {int(total_pop):,})")

    out_dir = DATA_RAW / city_key
    out_dir.mkdir(parents=True, exist_ok=True)
    df.to_csv(out_dir / "residential_stability.csv", index=False)
    print(f"  Raw data saved to {out_dir / 'residential_stability.csv'}")

    return {
        "city":   city_key,
        "metric": "residential_stability",
        "data": {
            "city_pct_stable":  city_pct,
            "total_population": int(total_pop),
            "zcta_count":       len(rows),
        },
    }


if __name__ == "__main__":
    city_key = sys.argv[1] if len(sys.argv) > 1 else "nyc"
    result = collect(city_key)
    print(json.dumps(result, indent=2))
