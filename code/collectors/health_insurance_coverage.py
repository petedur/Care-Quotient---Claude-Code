"""
Collector: Medicaid/CHIP Coverage Rate (Census ACS C27007 + C17002)

Measures the fraction of the likely-eligible population actually enrolled
in Medicaid or means-tested public health coverage.

Formula (mirrors SNAP coverage rate):
    coverage_rate = min(medicaid_enrolled / eligible_pop_0_149pct_fpl × 100, 100)

Why C27007 instead of B27001 (previous version):
    B27001 counted any health insurance — employer-based, marketplace, Medicaid,
    Medicare, military. That rewarded wealthy cities for high employer insurance,
    which is a labor-market signal rather than a care-system signal. A tech city
    with 97% employer coverage looks identical to an expansion-state city with
    97% Medicaid/CHIP coverage. C27007 isolates public program reach.

    The eligibility-rate denominator (0–149% FPL) ensures non-expansion states
    score lower because fewer adults are eligible, not just because fewer are
    enrolled. This captures the Medicaid expansion policy effect as a genuine
    care access failure, consistent with the methodology's intent.

Geography: ZCTA-level aggregation within city Census place boundary
    (>= 40% of ZCTA land area within the city).

Data sources:
  - C27007: Medicaid/Means-Tested Public Coverage by Sex by Age (ACS 5-year 2022)
  - C17002: Ratio of Income to Poverty Level (ACS 5-year 2022)
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

TOTAL_VAR = "C27007_001E"

# "With Medicaid/means-tested public coverage" cells
# Male:   Under 18 (004), 18–64 (007), 65+ (010)
# Female: Under 18 (014), 18–64 (017), 65+ (020)
MEDICAID_WITH_VARS = [
    "C27007_004E", "C27007_007E", "C27007_010E",
    "C27007_014E", "C27007_017E", "C27007_020E",
]

# C17002: Population ratio of income to poverty level — 0 to 1.49 approximates
# the 0–149% FPL band, matching the SNAP eligibility denominator.
ELIGIBLE_VARS = [
    "C17002_002E",  # under 0.50
    "C17002_003E",  # 0.50–0.99
    "C17002_004E",  # 1.00–1.24
    "C17002_005E",  # 1.25–1.49
]

ALL_VARS = [TOTAL_VAR] + MEDICAID_WITH_VARS + ELIGIBLE_VARS


def collect(city_key: str = "nyc") -> dict:
    city = CITIES[city_key]
    print(f"\n=== Medicaid/CHIP Coverage Rate — {city['name']} ===")

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
        total_pop          = r[TOTAL_VAR]
        medicaid_enrolled  = sum(r.get(v, 0) for v in MEDICAID_WITH_VARS)
        eligible_pop       = sum(r.get(v, 0) for v in ELIGIBLE_VARS)
        pct_medicaid       = round(medicaid_enrolled / total_pop * 100, 2) if total_pop else 0
        rows.append({
            "zcta":                      r["zcta"],
            "total_pop":                 total_pop,
            "medicaid_enrolled":         medicaid_enrolled,
            "eligible_pop_0_149pct_fpl": eligible_pop,
            "pct_medicaid":              pct_medicaid,
        })

    df = pd.DataFrame(rows)
    total_medicaid = df["medicaid_enrolled"].sum()
    total_eligible = df["eligible_pop_0_149pct_fpl"].sum()
    total_pop      = df["total_pop"].sum()
    coverage_rate  = round(min((total_medicaid / total_eligible) * 100, 100.0), 2) \
        if total_eligible > 0 else 0.0

    print(f"  City-wide: {coverage_rate}% coverage rate "
          f"({int(total_medicaid):,} enrolled / {int(total_eligible):,} eligible ~0–149% FPL)")
    print(f"  Raw Medicaid %: {round(total_medicaid / total_pop * 100, 1) if total_pop else 0}% "
          f"of total population ({int(total_pop):,})")

    out_dir = DATA_RAW / city_key
    out_dir.mkdir(parents=True, exist_ok=True)
    df.to_csv(out_dir / "health_insurance.csv", index=False)
    print(f"  Raw data saved to {out_dir / 'health_insurance.csv'}")

    return {
        "city":   city_key,
        "metric": "health_insurance_coverage",
        "data": {
            "coverage_rate":             coverage_rate,
            "medicaid_enrolled":         int(total_medicaid),
            "eligible_pop_0_149pct_fpl": int(total_eligible),
            "total_population":          int(total_pop),
            "zcta_count":                len(rows),
        },
    }


if __name__ == "__main__":
    city_key = sys.argv[1] if len(sys.argv) > 1 else "nyc"
    result = collect(city_key)
    print(json.dumps(result, indent=2))
