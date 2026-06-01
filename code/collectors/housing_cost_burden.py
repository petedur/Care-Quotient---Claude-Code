"""
Collector: Housing Cost Burden (Census ACS)
Measures % of households NOT spending >30% of income on housing costs.
Scored as an affordability rate (higher = better) so it integrates cleanly
with absolute benchmark normalization.

Framing: acts as a counter-weight to residential stability —
high stability + high cost burden = forced immobility, not embedded networks.
See methodology.md Section 9, limitation 7.

Geography: ZCTA-level aggregation within the city's Census place boundary
(>= 40% of ZCTA land area within the city). Replaces county-level queries
to eliminate county-sharing inflation.

Data source: Census Bureau ACS 5-year estimates
  - B25070: Gross rent as % of household income (renters)
  - B25091: Selected monthly owner costs as % of household income (owners)
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

RENTER_VARS = {
    "total":         "B25070_001E",
    "not_computed":  "B25070_011E",
    "burden_30_34":  "B25070_007E",
    "burden_35_39":  "B25070_008E",
    "burden_40_49":  "B25070_009E",
    "burden_50plus": "B25070_010E",
}

OWNER_MTG_VARS = {
    "total":         "B25091_002E",
    "not_computed":  "B25091_012E",
    "burden_30_34":  "B25091_008E",
    "burden_35_39":  "B25091_009E",
    "burden_40_49":  "B25091_010E",
    "burden_50plus": "B25091_011E",
}

OWNER_NO_MTG_VARS = {
    "total":         "B25091_013E",
    "not_computed":  "B25091_023E",
    "burden_30_34":  "B25091_019E",
    "burden_35_39":  "B25091_020E",
    "burden_40_49":  "B25091_021E",
    "burden_50plus": "B25091_022E",
}

ALL_VARS = list(dict.fromkeys(
    list(RENTER_VARS.values()) +
    list(OWNER_MTG_VARS.values()) +
    list(OWNER_NO_MTG_VARS.values())
))


def _compute_burden(agg: dict) -> tuple[int, int]:
    """
    Returns (burdened_households, total_valid_households) from an aggregated
    dict of variable_code: summed_int_value.
    'Valid' excludes households where cost ratio was 'not computed'.
    """
    burdened = (
        agg.get(RENTER_VARS["burden_30_34"],      0) +
        agg.get(RENTER_VARS["burden_35_39"],      0) +
        agg.get(RENTER_VARS["burden_40_49"],      0) +
        agg.get(RENTER_VARS["burden_50plus"],     0) +
        agg.get(OWNER_MTG_VARS["burden_30_34"],   0) +
        agg.get(OWNER_MTG_VARS["burden_35_39"],   0) +
        agg.get(OWNER_MTG_VARS["burden_40_49"],   0) +
        agg.get(OWNER_MTG_VARS["burden_50plus"],  0) +
        agg.get(OWNER_NO_MTG_VARS["burden_30_34"], 0) +
        agg.get(OWNER_NO_MTG_VARS["burden_35_39"], 0) +
        agg.get(OWNER_NO_MTG_VARS["burden_40_49"], 0) +
        agg.get(OWNER_NO_MTG_VARS["burden_50plus"], 0)
    )
    total = (
        (agg.get(RENTER_VARS["total"],        0) - agg.get(RENTER_VARS["not_computed"],        0)) +
        (agg.get(OWNER_MTG_VARS["total"],     0) - agg.get(OWNER_MTG_VARS["not_computed"],     0)) +
        (agg.get(OWNER_NO_MTG_VARS["total"],  0) - agg.get(OWNER_NO_MTG_VARS["not_computed"],  0))
    )
    return burdened, max(total, 0)


def collect(city_key: str = "nyc") -> dict:
    city = CITIES[city_key]
    print(f"\n=== Housing Cost Burden — {city['name']} ===")

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

    # Build per-ZCTA rows and aggregate for city-wide total
    rows = []
    agg = {v: 0 for v in ALL_VARS}

    for r in zcta_rows:
        burdened, total = _compute_burden(r)
        pct_burdened     = round(burdened / total * 100, 2) if total else 0
        pct_not_burdened = round(100 - pct_burdened, 2)
        rows.append({
            "zcta":            r["zcta"],
            "burdened":        burdened,
            "total":           total,
            "pct_burdened":    pct_burdened,
            "pct_not_burdened": pct_not_burdened,
        })
        for v in ALL_VARS:
            agg[v] += r.get(v, 0)

    total_burdened, total_hh = _compute_burden(agg)
    city_pct_burdened    = round(total_burdened / total_hh * 100, 2) if total_hh else 0
    city_pct_not_burdened = round(100 - city_pct_burdened, 2)

    print(f"  City-wide: {city_pct_burdened}% cost-burdened "
          f"({city_pct_not_burdened}% not burdened)")

    df = pd.DataFrame(rows)
    out_dir = DATA_RAW / city_key
    out_dir.mkdir(parents=True, exist_ok=True)
    df.to_csv(out_dir / "housing_cost_burden.csv", index=False)
    print(f"  Raw data saved to {out_dir / 'housing_cost_burden.csv'}")

    return {
        "city":   city_key,
        "metric": "housing_cost_burden",
        "data": {
            "city_pct_burdened":     city_pct_burdened,
            "city_pct_not_burdened": city_pct_not_burdened,
            "total_households":      int(total_hh),
            "zcta_count":            len(rows),
        },
    }


if __name__ == "__main__":
    city_key = sys.argv[1] if len(sys.argv) > 1 else "nyc"
    result = collect(city_key)
    print(json.dumps(result, indent=2))
