"""
Collector: ACS Historical Trend Data (2020 vs 2022)
Fetches ACS 5-year 2020 data for the four metrics that can be trended across
ACS vintages. Saves derived metric values (not raw counts) so score_trend.py
can score a "2020 full CQ" and compute a delta.

Trendable metrics (ACS-based, vintage-parameterizable):
  - residential_stability   → pct_same_house       (B07003)
  - housing_cost_burden     → pct_not_burdened      (B25070 / B25091)
  - snap_participation      → coverage_rate         (B22001 / C17002)
  - health_insurance_coverage → coverage_rate       (C27007 / C17002)

Non-trendable metrics (held at current values in trend scoring):
  - library_density         (IMLS — cross-sectional)
  - nonprofit_density       (IRS BMF snapshot)
  - religious_density       (ARDA 2020 — decennial, no prior vintage)
  - health_center_density   (HRSA — cross-sectional)
  - nursing_home_capacity   (CMS — cross-sectional)
  - child_care_capacity     (CBP — cross-sectional)

Output: data/raw/{city}/trend_2020/trend_metrics.json
  {
    "city": "nyc",
    "acs_year": 2020,
    "residential_stability": 87.5,
    "housing_cost_burden":   65.0,
    "snap_participation":    80.0,
    "health_insurance_coverage": 72.0
  }
"""

import sys
import json
import pandas as pd
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from config import get_census_api_key, DATA_RAW, CITIES
from collectors.utils import census_get_zctas
from geo.city_zips import city_to_zips

ACS_URL_2020 = "https://api.census.gov/data/2020/acs/acs5"

# ── Variable sets (same as current collectors, different year URL) ─────────────

RESID_VARS = {
    "same_house": "B07003_004E",
    "total_pop":  "B01003_001E",
}

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
HOUSING_VARS = list(dict.fromkeys(
    list(RENTER_VARS.values()) +
    list(OWNER_MTG_VARS.values()) +
    list(OWNER_NO_MTG_VARS.values())
))

SNAP_VARS = {
    "total_households": "B22001_001E",
    "snap_households":  "B22001_002E",
    "total_pop":        "C17002_001E",
    "fpl_under_50":     "C17002_002E",
    "fpl_50_99":        "C17002_003E",
    "fpl_100_124":      "C17002_004E",
    "fpl_125_149":      "C17002_005E",
}

HI_TOTAL_VAR = "C27007_001E"
HI_MEDICAID_VARS = [
    "C27007_004E", "C27007_007E", "C27007_010E",
    "C27007_014E", "C27007_017E", "C27007_020E",
]
HI_ELIGIBLE_VARS = [
    "C17002_002E", "C17002_003E", "C17002_004E", "C17002_005E",
]
HI_VARS = [HI_TOTAL_VAR] + HI_MEDICAID_VARS + HI_ELIGIBLE_VARS


def _compute_housing_burden(agg: dict) -> tuple[int, int]:
    burdened = sum(agg.get(v, 0) for v in [
        RENTER_VARS["burden_30_34"], RENTER_VARS["burden_35_39"],
        RENTER_VARS["burden_40_49"], RENTER_VARS["burden_50plus"],
        OWNER_MTG_VARS["burden_30_34"], OWNER_MTG_VARS["burden_35_39"],
        OWNER_MTG_VARS["burden_40_49"], OWNER_MTG_VARS["burden_50plus"],
        OWNER_NO_MTG_VARS["burden_30_34"], OWNER_NO_MTG_VARS["burden_35_39"],
        OWNER_NO_MTG_VARS["burden_40_49"], OWNER_NO_MTG_VARS["burden_50plus"],
    ])
    total = (
        (agg.get(RENTER_VARS["total"], 0)       - agg.get(RENTER_VARS["not_computed"], 0)) +
        (agg.get(OWNER_MTG_VARS["total"], 0)    - agg.get(OWNER_MTG_VARS["not_computed"], 0)) +
        (agg.get(OWNER_NO_MTG_VARS["total"], 0) - agg.get(OWNER_NO_MTG_VARS["not_computed"], 0))
    )
    return burdened, max(total, 0)


def _collect_residential_stability(city_zctas, state_fips, api_key) -> float | None:
    rows = census_get_zctas(
        ACS_URL_2020, list(RESID_VARS.values()),
        state_fips, city_zctas, api_key,
    )
    if not rows:
        return None
    total_same = sum(r.get(RESID_VARS["same_house"], 0) for r in rows)
    total_pop  = sum(r.get(RESID_VARS["total_pop"],  0) for r in rows)
    return round(total_same / total_pop * 100, 2) if total_pop else None


def _collect_housing_cost_burden(city_zctas, state_fips, api_key) -> float | None:
    rows = census_get_zctas(
        ACS_URL_2020, HOUSING_VARS,
        state_fips, city_zctas, api_key,
    )
    if not rows:
        return None
    agg = {v: 0 for v in HOUSING_VARS}
    for r in rows:
        for v in HOUSING_VARS:
            agg[v] += r.get(v, 0)
    burdened, total = _compute_housing_burden(agg)
    if not total:
        return None
    pct_burdened = burdened / total * 100
    return round(100 - pct_burdened, 2)


def _collect_snap(city_zctas, state_fips, api_key) -> float | None:
    rows = census_get_zctas(
        ACS_URL_2020, list(SNAP_VARS.values()),
        state_fips, city_zctas, api_key,
    )
    if not rows:
        return None
    total_snap     = sum(r.get(SNAP_VARS["snap_households"],  0) for r in rows)
    total_hh       = sum(r.get(SNAP_VARS["total_households"], 0) for r in rows)
    total_eligible = sum(
        r.get(SNAP_VARS["fpl_under_50"], 0) + r.get(SNAP_VARS["fpl_50_99"], 0) +
        r.get(SNAP_VARS["fpl_100_124"], 0) + r.get(SNAP_VARS["fpl_125_149"], 0)
        for r in rows
    )
    total_pop = sum(r.get(SNAP_VARS["total_pop"], 0) for r in rows)
    if not total_hh or not total_pop:
        return None
    snap_rate     = total_snap / total_hh
    eligible_rate = total_eligible / total_pop
    if not eligible_rate:
        return None
    return round(min(snap_rate / eligible_rate * 100, 100.0), 2)


def _collect_health_insurance(city_zctas, state_fips, api_key) -> float | None:
    rows = census_get_zctas(
        ACS_URL_2020, HI_VARS,
        state_fips, city_zctas, api_key,
    )
    if not rows:
        return None
    total_medicaid = sum(sum(r.get(v, 0) for v in HI_MEDICAID_VARS) for r in rows)
    total_eligible = sum(sum(r.get(v, 0) for v in HI_ELIGIBLE_VARS) for r in rows)
    if not total_eligible:
        return None
    return round(min(total_medicaid / total_eligible * 100, 100.0), 2)


def collect_trend(city_key: str) -> dict | None:
    city = CITIES.get(city_key)
    if city is None:
        print(f"  SKIP {city_key}: not in CITIES config")
        return None

    print(f"\n=== ACS 2020 Trend Data — {city['name']} ===")
    api_key    = get_census_api_key()
    state_fips = city["state_fips"]
    city_zctas = city_to_zips(city_key)
    print(f"  City ZCTAs: {len(city_zctas)}")

    resid = _collect_residential_stability(city_zctas, state_fips, api_key)
    print(f"  residential_stability: {resid}")

    housing = _collect_housing_cost_burden(city_zctas, state_fips, api_key)
    print(f"  housing_cost_burden:   {housing}")

    snap = _collect_snap(city_zctas, state_fips, api_key)
    print(f"  snap_participation:    {snap}")

    hi = _collect_health_insurance(city_zctas, state_fips, api_key)
    print(f"  health_insurance:      {hi}")

    result = {
        "city":                    city_key,
        "acs_year":                2020,
        "residential_stability":   resid,
        "housing_cost_burden":     housing,
        "snap_participation":      snap,
        "health_insurance_coverage": hi,
    }

    out_dir = DATA_RAW / city_key / "trend_2020"
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / "trend_metrics.json"
    out_path.write_text(json.dumps(result, indent=2))
    print(f"  Saved to {out_path}")
    return result


def main(city_keys: list[str] | None = None):
    targets = city_keys or list(CITIES.keys())
    for city_key in targets:
        try:
            collect_trend(city_key)
        except Exception as e:
            print(f"  ERROR {city_key}: {e}")


if __name__ == "__main__":
    city_args = sys.argv[1:] or None
    main(city_args)
