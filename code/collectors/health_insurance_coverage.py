"""
Collector: Health Insurance Coverage Rate (Census ACS)
Measures % of the civilian noninstitutional population with health insurance
coverage — a proxy for whether people can access health systems when they
need care.

Limitation: Coverage reflects a combination of employer-based insurance,
Medicaid/CHIP, ACA marketplace plans, and other sources. Low coverage in
a city may reflect state-level Medicaid non-expansion policy rather than
local care infrastructure failure. This is noted as a limitation and will
be addressed in V3 by separating Medicaid enrollment from private coverage.

Data source: Census Bureau ACS 5-year estimates
  - B27001: Health insurance coverage status by sex by age
  - API docs: https://api.census.gov/data/2022/acs/acs5/variables.html

Benchmark: 95 — near-universal coverage. States with full Medicaid expansion
and strong marketplace enrollment achieve 94-97% coverage. A score of 95
represents a city where essentially all residents who want coverage can
access it.
"""

import sys
import json
import requests
import pandas as pd
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from config import get_census_api_key, DATA_RAW, CITIES

ACS_URL = "https://api.census.gov/data/2022/acs/acs5"

# B27001_001E: Total civilian noninstitutional population
TOTAL_VAR = "B27001_001E"

# "No health insurance coverage" cells (every other row in each age bracket)
# Male: age brackets at positions 005, 008, 011, 014, 017, 020, 023, 026, 029
# Female: age brackets at positions 033, 036, 039, 042, 045, 048, 051, 054, 057
UNINSURED_VARS = [
    "B27001_005E", "B27001_008E", "B27001_011E", "B27001_014E",
    "B27001_017E", "B27001_020E", "B27001_023E", "B27001_026E", "B27001_029E",
    "B27001_033E", "B27001_036E", "B27001_039E", "B27001_042E",
    "B27001_045E", "B27001_048E", "B27001_051E", "B27001_054E", "B27001_057E",
]

ALL_VARS = [TOTAL_VAR] + UNINSURED_VARS


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
    print(f"\n=== Health Insurance Coverage — {city['name']} ===")

    state_fips = city["state_fips"]
    rows = []

    for county_name, county_fips in city["county_fips"].items():
        print(f"  Querying {county_name} (FIPS {state_fips}{county_fips})...")
        try:
            data = _get(ALL_VARS, state_fips, county_fips)
            headers, values = data[0], data[1]
            row = {h: (int(v) if v is not None else 0) for h, v in zip(headers, values)}

            total_pop  = row[TOTAL_VAR]
            uninsured  = sum(row.get(v, 0) for v in UNINSURED_VARS)
            insured    = total_pop - uninsured
            pct_insured = round(insured / total_pop * 100, 2) if total_pop else 0

            rows.append({
                "county":      county_name,
                "total_pop":   total_pop,
                "uninsured":   uninsured,
                "insured":     insured,
                "pct_insured": pct_insured,
            })
            print(f"    {pct_insured}% insured "
                  f"({insured:,} insured / {uninsured:,} uninsured / {total_pop:,} total)")
        except Exception as e:
            print(f"    ERROR for {county_name}: {e}")

    if not rows:
        raise RuntimeError(f"No data retrieved for {city['name']}")

    df = pd.DataFrame(rows)
    total_pop    = df["total_pop"].sum()
    total_insured = df["insured"].sum()
    city_pct_insured = round(total_insured / total_pop * 100, 2) if total_pop else 0

    print(f"  City-wide: {city_pct_insured}% insured")

    out_dir = DATA_RAW / city_key
    out_dir.mkdir(parents=True, exist_ok=True)
    df.to_csv(out_dir / "health_insurance.csv", index=False)
    print(f"  Raw data saved to {out_dir / 'health_insurance.csv'}")

    return {
        "city":   city_key,
        "metric": "health_insurance_coverage",
        "data": {
            "city_pct_insured": city_pct_insured,
            "total_population": int(total_pop),
            "counties": rows,
        },
    }


if __name__ == "__main__":
    city_key = sys.argv[1] if len(sys.argv) > 1 else "nyc"
    result = collect(city_key)
    print(json.dumps(result, indent=2))
