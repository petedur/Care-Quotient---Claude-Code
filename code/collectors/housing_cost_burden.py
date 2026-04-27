"""
Collector: Housing Cost Burden (Census ACS)
Measures % of households NOT spending >30% of income on housing costs.
Scored as an affordability rate (higher = better) so it integrates cleanly
with absolute benchmark normalization.

Framing: this metric acts as a counter-weight to residential stability —
high stability + high cost burden = forced immobility, not embedded networks.
See methodology.md Section 9, limitation 7.

Data source: Census Bureau ACS 5-year estimates
  - B25070: Gross rent as % of household income (renters)
  - B25091: Selected monthly owner costs as % of household income (owners)
  - API docs: https://api.census.gov/data/2022/acs/acs5/variables.html

Benchmark: 75 (i.e., 75% of households are NOT cost-burdened — only 25%
are burdened). National average is ~30% burdened; 25% represents a well-
functioning housing market. Agha et al. (2024); Desmond & Bell.
"""

import sys
import json
import requests
import pandas as pd
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from config import get_census_api_key, DATA_RAW, CITIES

ACS_URL = "https://api.census.gov/data/2022/acs/acs5"

# ── Census variables ──────────────────────────────────────────────────────────
# Renters paying 30%+ of income on rent
RENTER_VARS = {
    "total":        "B25070_001E",
    "not_computed": "B25070_011E",
    "burden_30_34": "B25070_007E",
    "burden_35_39": "B25070_008E",
    "burden_40_49": "B25070_009E",
    "burden_50plus": "B25070_010E",
}

# Owners with mortgage paying 30%+
OWNER_MTG_VARS = {
    "total":        "B25091_002E",
    "not_computed": "B25091_012E",
    "burden_30_34": "B25091_008E",
    "burden_35_39": "B25091_009E",
    "burden_40_49": "B25091_010E",
    "burden_50plus": "B25091_011E",
}

# Owners without mortgage paying 30%+
OWNER_NO_MTG_VARS = {
    "total":        "B25091_013E",
    "not_computed": "B25091_023E",
    "burden_30_34": "B25091_019E",
    "burden_35_39": "B25091_020E",
    "burden_40_49": "B25091_021E",
    "burden_50plus": "B25091_022E",
}

ALL_VARS = list({**RENTER_VARS, **OWNER_MTG_VARS, **OWNER_NO_MTG_VARS}.values())
# Remove duplicates while preserving order
ALL_VARS = list(dict.fromkeys(ALL_VARS))


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


def _parse_county(data: list) -> dict:
    """Parse raw Census API response into a dict of variable: int."""
    headers, values = data[0], data[1]
    return {h: (int(v) if v is not None else 0) for h, v in zip(headers, values)}


def _compute_burden(row: dict) -> tuple[int, int]:
    """
    Returns (burdened_households, total_valid_households) for one county.
    'Valid' excludes households where cost ratio was 'not computed'.
    """
    burdened = (
        row.get(RENTER_VARS["burden_30_34"], 0) +
        row.get(RENTER_VARS["burden_35_39"], 0) +
        row.get(RENTER_VARS["burden_40_49"], 0) +
        row.get(RENTER_VARS["burden_50plus"], 0) +
        row.get(OWNER_MTG_VARS["burden_30_34"], 0) +
        row.get(OWNER_MTG_VARS["burden_35_39"], 0) +
        row.get(OWNER_MTG_VARS["burden_40_49"], 0) +
        row.get(OWNER_MTG_VARS["burden_50plus"], 0) +
        row.get(OWNER_NO_MTG_VARS["burden_30_34"], 0) +
        row.get(OWNER_NO_MTG_VARS["burden_35_39"], 0) +
        row.get(OWNER_NO_MTG_VARS["burden_40_49"], 0) +
        row.get(OWNER_NO_MTG_VARS["burden_50plus"], 0)
    )
    total = (
        (row.get(RENTER_VARS["total"], 0) - row.get(RENTER_VARS["not_computed"], 0)) +
        (row.get(OWNER_MTG_VARS["total"], 0) - row.get(OWNER_MTG_VARS["not_computed"], 0)) +
        (row.get(OWNER_NO_MTG_VARS["total"], 0) - row.get(OWNER_NO_MTG_VARS["not_computed"], 0))
    )
    return burdened, max(total, 0)


def collect(city_key: str = "nyc") -> dict:
    city = CITIES[city_key]
    print(f"\n=== Housing Cost Burden — {city['name']} ===")

    state_fips = city["state_fips"]
    rows = []

    for county_name, county_fips in city["county_fips"].items():
        print(f"  Querying {county_name} (FIPS {state_fips}{county_fips})...")
        try:
            data = _get(ALL_VARS, state_fips, county_fips)
            row = _parse_county(data)
            burdened, total = _compute_burden(row)
            pct_burdened = round(burdened / total * 100, 2) if total else 0
            pct_not_burdened = round(100 - pct_burdened, 2)
            rows.append({
                "county":          county_name,
                "burdened":        burdened,
                "total":           total,
                "pct_burdened":    pct_burdened,
                "pct_not_burdened": pct_not_burdened,
            })
            print(f"    {pct_burdened}% burdened ({burdened:,} / {total:,})")
        except Exception as e:
            print(f"    ERROR for {county_name}: {e}")

    if not rows:
        raise RuntimeError(f"No data retrieved for {city['name']}")

    df = pd.DataFrame(rows)
    total_burdened = df["burdened"].sum()
    total_hh       = df["total"].sum()
    city_pct_burdened    = round(total_burdened / total_hh * 100, 2) if total_hh else 0
    city_pct_not_burdened = round(100 - city_pct_burdened, 2)

    print(f"  City-wide: {city_pct_burdened}% cost-burdened "
          f"({city_pct_not_burdened}% not burdened)")

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
            "counties": rows,
        },
    }


if __name__ == "__main__":
    city_key = sys.argv[1] if len(sys.argv) > 1 else "nyc"
    result = collect(city_key)
    print(json.dumps(result, indent=2))
