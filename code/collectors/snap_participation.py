"""
Collector: SNAP Coverage Rate (Census ACS)
Measures the extent to which food assistance systems reach the population
in poverty — a proxy for whether care infrastructure connects with those
who need it most.

Metric: (SNAP-receiving households / total households) /
        (population in poverty / total population) * 100

This normalizes SNAP receipt by the underlying poverty rate, approximating
participation among households likely to be eligible. A city where 15% of
households receive SNAP and 15% are in poverty scores ~100%; a city where
15% receive SNAP but 25% are in poverty scores ~60%.

Limitation: SNAP eligibility is technically defined at 130% of FPL; this
metric uses 100% FPL poverty data as an approximation. The result may
overstate coverage in cities with near-poverty (100-130% FPL) populations
that are eligible but not captured in the poverty denominator. Documented
in methodology.md.

Data source: Census Bureau ACS 5-year estimates
  - B22001: Receipt of Food Stamps/SNAP in the past 12 months
  - B17001: Poverty status in the past 12 months
  - API docs: https://api.census.gov/data/2022/acs/acs5/variables.html

Benchmark: 85 — USDA FNS national SNAP participation target (% of eligible
households reached). Strong performers reach 80-90%+ of eligible households.
"""

import sys
import json
import requests
import pandas as pd
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from config import get_census_api_key, DATA_RAW, CITIES

ACS_URL = "https://api.census.gov/data/2022/acs/acs5"

SNAP_VARS = {
    "total_households": "B22001_001E",
    "snap_households":  "B22001_002E",
    "total_pop":        "B17001_001E",
    "poverty_pop":      "B17001_002E",
}

ALL_VARS = list(SNAP_VARS.values())


def _get(variables: list, state_fips: str, county_fips: str) -> list:
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
    print(f"\n=== SNAP Coverage Rate — {city['name']} ===")

    state_fips = city["state_fips"]
    rows = []

    for county_name, county_fips in city["county_fips"].items():
        print(f"  Querying {county_name} (FIPS {state_fips}{county_fips})...")
        try:
            data = _get(ALL_VARS, state_fips, county_fips)
            headers, values = data[0], data[1]
            row = {h: (int(v) if v is not None else 0) for h, v in zip(headers, values)}

            total_hh   = row[SNAP_VARS["total_households"]]
            snap_hh    = row[SNAP_VARS["snap_households"]]
            total_pop  = row[SNAP_VARS["total_pop"]]
            poverty_pop = row[SNAP_VARS["poverty_pop"]]

            snap_rate    = snap_hh / total_hh if total_hh else 0
            poverty_rate = poverty_pop / total_pop if total_pop else 0
            coverage = round(min((snap_rate / poverty_rate) * 100, 100.0), 2) \
                if poverty_rate > 0 else 0.0

            rows.append({
                "county":         county_name,
                "snap_households": snap_hh,
                "total_households": total_hh,
                "poverty_pop":    poverty_pop,
                "total_pop":      total_pop,
                "snap_rate_pct":  round(snap_rate * 100, 2),
                "poverty_rate_pct": round(poverty_rate * 100, 2),
                "coverage_rate":  coverage,
            })
            print(f"    SNAP {snap_rate*100:.1f}% of HH | poverty {poverty_rate*100:.1f}% | "
                  f"coverage {coverage:.1f}%")
        except Exception as e:
            print(f"    ERROR for {county_name}: {e}")

    if not rows:
        raise RuntimeError(f"No data retrieved for {city['name']}")

    df = pd.DataFrame(rows)
    total_snap = df["snap_households"].sum()
    total_hh   = df["total_households"].sum()
    total_pov  = df["poverty_pop"].sum()
    total_pop  = df["total_pop"].sum()

    city_snap_rate    = total_snap / total_hh if total_hh else 0
    city_poverty_rate = total_pov / total_pop if total_pop else 0
    city_coverage = round(min((city_snap_rate / city_poverty_rate) * 100, 100.0), 2) \
        if city_poverty_rate > 0 else 0.0

    print(f"  City-wide: SNAP {city_snap_rate*100:.1f}% | "
          f"poverty {city_poverty_rate*100:.1f}% | coverage {city_coverage:.1f}%")

    out_dir = DATA_RAW / city_key
    out_dir.mkdir(parents=True, exist_ok=True)
    df.to_csv(out_dir / "snap_participation.csv", index=False)
    print(f"  Raw data saved to {out_dir / 'snap_participation.csv'}")

    return {
        "city":   city_key,
        "metric": "snap_participation",
        "data": {
            "city_coverage_rate":  city_coverage,
            "city_snap_rate_pct":  round(city_snap_rate * 100, 2),
            "city_poverty_rate_pct": round(city_poverty_rate * 100, 2),
            "counties": rows,
        },
    }


if __name__ == "__main__":
    city_key = sys.argv[1] if len(sys.argv) > 1 else "nyc"
    result = collect(city_key)
    print(json.dumps(result, indent=2))
