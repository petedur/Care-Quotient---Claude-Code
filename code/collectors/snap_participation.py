"""
Collector: SNAP Coverage Rate (Census ACS)
Measures the extent to which food assistance systems reach the population
likely eligible for SNAP — a proxy for whether care infrastructure connects
with those who need it most.

Metric: (SNAP-receiving households / total households) /
        (population at 0–149% FPL / total population) * 100

This normalizes SNAP receipt by an approximation of the SNAP-eligible
population. SNAP eligibility is defined at 130% of FPL; C17002 provides
income-to-poverty ratio bands from which we sum the 0–149% FPL population
(under 0.50 + 0.50–0.99 + 1.00–1.24 + 1.25–1.49) as the best Census
approximation of the eligible denominator.

Geography: ZCTA-level aggregation within the city's Census place boundary
(>= 50% of ZCTA land area within the city). Replaces county-level queries
to eliminate county-sharing inflation.

Data source: Census Bureau ACS 5-year estimates
  - B22001: Receipt of Food Stamps/SNAP in the past 12 months
  - C17002: Ratio of income to poverty level in the past 12 months
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

SNAP_VARS = {
    "total_households": "B22001_001E",
    "snap_households":  "B22001_002E",
    "total_pop":        "C17002_001E",
    "fpl_under_50":     "C17002_002E",
    "fpl_50_99":        "C17002_003E",
    "fpl_100_124":      "C17002_004E",
    "fpl_125_149":      "C17002_005E",
}

ALL_VARS = list(SNAP_VARS.values())


def collect(city_key: str = "nyc") -> dict:
    city = CITIES[city_key]
    print(f"\n=== SNAP Coverage Rate — {city['name']} ===")

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
        total_hh    = r[SNAP_VARS["total_households"]]
        snap_hh     = r[SNAP_VARS["snap_households"]]
        total_pop   = r[SNAP_VARS["total_pop"]]
        eligible_pop = (
            r[SNAP_VARS["fpl_under_50"]] +
            r[SNAP_VARS["fpl_50_99"]]    +
            r[SNAP_VARS["fpl_100_124"]]  +
            r[SNAP_VARS["fpl_125_149"]]
        )
        snap_rate     = snap_hh / total_hh if total_hh else 0
        eligible_rate = eligible_pop / total_pop if total_pop else 0
        coverage = round(min((snap_rate / eligible_rate) * 100, 100.0), 2) \
            if eligible_rate > 0 else 0.0

        rows.append({
            "zcta":                      r["zcta"],
            "snap_households":           snap_hh,
            "total_households":          total_hh,
            "eligible_pop_0_149pct_fpl": eligible_pop,
            "total_pop":                 total_pop,
            "snap_rate_pct":             round(snap_rate * 100, 2),
            "eligible_rate_pct":         round(eligible_rate * 100, 2),
            "coverage_rate":             coverage,
        })

    df = pd.DataFrame(rows)
    total_snap     = df["snap_households"].sum()
    total_hh       = df["total_households"].sum()
    total_eligible = df["eligible_pop_0_149pct_fpl"].sum()
    total_pop      = df["total_pop"].sum()

    city_snap_rate     = total_snap / total_hh if total_hh else 0
    city_eligible_rate = total_eligible / total_pop if total_pop else 0
    city_coverage = round(min((city_snap_rate / city_eligible_rate) * 100, 100.0), 2) \
        if city_eligible_rate > 0 else 0.0

    print(f"  City-wide: SNAP {city_snap_rate*100:.1f}% | "
          f"eligible (0-149% FPL) {city_eligible_rate*100:.1f}% | coverage {city_coverage:.1f}%")

    out_dir = DATA_RAW / city_key
    out_dir.mkdir(parents=True, exist_ok=True)
    df.to_csv(out_dir / "snap_participation.csv", index=False)
    print(f"  Raw data saved to {out_dir / 'snap_participation.csv'}")

    return {
        "city":   city_key,
        "metric": "snap_participation",
        "data": {
            "city_coverage_rate":     city_coverage,
            "city_snap_rate_pct":     round(city_snap_rate * 100, 2),
            "city_eligible_rate_pct": round(city_eligible_rate * 100, 2),
            "zcta_count":             len(rows),
        },
    }


if __name__ == "__main__":
    city_key = sys.argv[1] if len(sys.argv) > 1 else "nyc"
    result = collect(city_key)
    print(json.dumps(result, indent=2))
