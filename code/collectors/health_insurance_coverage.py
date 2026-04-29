"""
Collector: Health Insurance Coverage Rate (Census ACS)
Measures % of the civilian noninstitutional population with health insurance
coverage — a proxy for whether people can access health systems when they
need care.

Limitation: Coverage reflects a combination of employer-based insurance,
Medicaid/CHIP, ACA marketplace plans, and other sources. Low coverage in
a city may reflect state-level Medicaid non-expansion policy rather than
local care infrastructure failure. V4 will evaluate replacing this metric
with Medicaid/CHIP enrollment (B27007) specifically.

Geography: ZCTA-level aggregation within the city's Census place boundary
(>= 50% of ZCTA land area within the city). Replaces county-level queries
to eliminate county-sharing inflation.

Data source: Census Bureau ACS 5-year estimates
  - B27001: Health insurance coverage status by sex by age
"""

import sys
import json
import pandas as pd
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from config import get_census_api_key, DATA_RAW, CITIES
from collectors.utils import census_get_zctas
from geo.city_zips import city_to_zips

ACS_URL = "https://api.census.gov/data/2022/acs/acs5"

TOTAL_VAR = "B27001_001E"

# "No health insurance coverage" cells — every other row in each age bracket
# Male: 005, 008, 011, 014, 017, 020, 023, 026, 029
# Female: 033, 036, 039, 042, 045, 048, 051, 054, 057
UNINSURED_VARS = [
    "B27001_005E", "B27001_008E", "B27001_011E", "B27001_014E",
    "B27001_017E", "B27001_020E", "B27001_023E", "B27001_026E", "B27001_029E",
    "B27001_033E", "B27001_036E", "B27001_039E", "B27001_042E",
    "B27001_045E", "B27001_048E", "B27001_051E", "B27001_054E", "B27001_057E",
]

ALL_VARS = [TOTAL_VAR] + UNINSURED_VARS


def collect(city_key: str = "nyc") -> dict:
    city = CITIES[city_key]
    print(f"\n=== Health Insurance Coverage — {city['name']} ===")

    city_zctas = city_to_zips(city_key)
    print(f"  City ZCTAs: {len(city_zctas)} ZIP codes")

    zcta_rows = census_get_zctas(
        ACS_URL,
        ALL_VARS,
        city["state_fips"],
        city_zctas,
        get_census_api_key(),
    )

    if not zcta_rows:
        raise RuntimeError(
            f"No ZCTA data returned for {city['name']} — "
            "check place_fips in cities.csv."
        )

    rows = []
    for r in zcta_rows:
        total_pop = r[TOTAL_VAR]
        uninsured  = sum(r.get(v, 0) for v in UNINSURED_VARS)
        insured    = total_pop - uninsured
        pct_insured = round(insured / total_pop * 100, 2) if total_pop else 0
        rows.append({
            "zcta":        r["zcta"],
            "total_pop":   total_pop,
            "uninsured":   uninsured,
            "insured":     insured,
            "pct_insured": pct_insured,
        })

    df = pd.DataFrame(rows)
    total_pop     = df["total_pop"].sum()
    total_insured = df["insured"].sum()
    city_pct_insured = round(total_insured / total_pop * 100, 2) if total_pop else 0

    print(f"  City-wide: {city_pct_insured}% insured "
          f"({int(total_insured):,} insured / {int(total_pop):,} total)")

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
            "zcta_count":       len(rows),
        },
    }


if __name__ == "__main__":
    city_key = sys.argv[1] if len(sys.argv) > 1 else "nyc"
    result = collect(city_key)
    print(json.dumps(result, indent=2))
