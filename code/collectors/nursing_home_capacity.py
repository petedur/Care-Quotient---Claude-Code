"""
Collector: Nursing Home Capacity (CMS Care Compare)
Counts certified nursing home beds per 1,000 residents aged 65+.

Metric: total_certified_beds / (population_65plus / 1000)

Geography: ZCTA-based — facilities are filtered by ZIP code using
city_to_zips() (the same 40% land area threshold as all other ZCTA-based
collectors). The 65+ population denominator is aggregated from ACS B01001
across the same city ZCTAs.

Data sources:
  1. CMS Care Compare — Nursing Home Provider Information
     https://data.cms.gov/provider-data/dataset/4pq5-n9py
     Queried live via DKAN API; no API key required.
     Field names as of 2025: state, zip_code, number_of_certified_beds,
     average_number_of_residents_per_day, provider_type.
  2. Census ACS 5-year 2022 — B01001 sex-by-age, 65+ groups, by ZCTA.

Output: data/raw/{city_key}/nursing_homes_meta.json
  beds_per_1k_65plus   — scored metric (benchmark: 50)
  avg_daily_residents  — average daily census across facilities (diagnostic)
  facility_count       — number of facilities matched to city ZCTAs
  population_65plus    — ACS 65+ population used as denominator
"""

import sys
import json
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from config import get_census_api_key, DATA_RAW, CITIES
from collectors.utils import census_get_zctas, http_get_with_retry
from geo.city_zips import city_to_zips

CMS_NH_URL = "https://data.cms.gov/provider-data/api/1/datastore/query/4pq5-n9py/0"
CMS_PAGE_SIZE = 500
ACS_URL = "https://api.census.gov/data/2022/acs/acs5"

# ACS B01001 variables covering all age groups 65+ (male then female)
_65PLUS_VARS = [
    "B01001_020E", "B01001_021E", "B01001_022E",   # Male: 65-66, 67-69, 70-74
    "B01001_023E", "B01001_024E", "B01001_025E",   # Male: 75-79, 80-84, 85+
    "B01001_044E", "B01001_045E", "B01001_046E",   # Female: 65-66, 67-69, 70-74
    "B01001_047E", "B01001_048E", "B01001_049E",   # Female: 75-79, 80-84, 85+
]


def _get_cms_facilities(state_abbr: str) -> list[dict]:
    """Fetch all CMS nursing home facilities for a state, paginating as needed."""
    all_rows = []
    offset = 0
    while True:
        url = (
            f"{CMS_NH_URL}"
            f"?conditions[0][property]=state"
            f"&conditions[0][value]={state_abbr}"
            f"&conditions[0][operator]=%3D"
            f"&limit={CMS_PAGE_SIZE}&offset={offset}"
        )
        resp = http_get_with_retry(url, timeout=30, label=f"CMS NH {state_abbr} offset={offset}")
        data = resp.json()
        results = data.get("results", [])
        if not results:
            break
        all_rows.extend(results)
        if len(results) < CMS_PAGE_SIZE:
            break
        offset += CMS_PAGE_SIZE
    return all_rows


def _normalize_zip(z) -> str:
    if not z:
        return ""
    return str(z).strip().zfill(5)[:5]


def _int_safe(v) -> int:
    try:
        return int(float(str(v))) if v else 0
    except (ValueError, TypeError):
        return 0


def _float_safe(v) -> float:
    try:
        return float(str(v)) if v else 0.0
    except (ValueError, TypeError):
        return 0.0


def _get_pop_65plus(city_key: str, api_key: str) -> int:
    """Sum the 65+ population across the city's ZCTAs from ACS B01001."""
    city = CITIES[city_key]
    city_zctas = city_to_zips(city_key)
    rows = census_get_zctas(
        ACS_URL, _65PLUS_VARS, city["state_fips"], city_zctas, api_key
    )
    total = 0
    for r in rows:
        for var in _65PLUS_VARS:
            val = r.get(var, 0)
            if val and val > 0:
                total += int(val)
    return total


def collect(city_key: str = "nyc") -> dict:
    city = CITIES[city_key]
    print(f"\n=== Nursing Home Capacity — {city['name']} ===")

    api_key    = get_census_api_key()
    city_zctas = city_to_zips(city_key)
    state_abbr = city["state"].upper()
    print(f"  City ZCTAs: {len(city_zctas)}")

    # 1. Fetch and filter CMS facilities
    print(f"  Fetching CMS Care Compare facilities for {state_abbr}...")
    facilities = _get_cms_facilities(state_abbr)
    print(f"  {len(facilities)} active facilities statewide")

    city_facilities = [
        f for f in facilities
        if _normalize_zip(f.get("zip_code")) in city_zctas
    ]
    print(f"  {len(city_facilities)} facilities within city ZCTAs")

    if not city_facilities:
        raise RuntimeError(
            f"No nursing home facilities found for {city['name']} ({state_abbr}). "
            "Check CMS API or city ZCTA list."
        )

    # 2. Sum certified beds and average daily residents
    total_beds    = sum(_int_safe(f.get("number_of_certified_beds")) for f in city_facilities)
    total_daily   = sum(_float_safe(f.get("average_number_of_residents_per_day")) for f in city_facilities)
    avg_daily     = round(total_daily / len(city_facilities), 1) if city_facilities else 0.0

    # 3. 65+ population from ACS
    print(f"  Fetching ACS 65+ population by ZCTA...")
    pop_65plus = _get_pop_65plus(city_key, api_key)
    if pop_65plus <= 0:
        pop_65plus = int(city["population"] * 0.149)  # national avg ~14.9% (2022)
        print(f"  WARN: ACS returned 0; using 14.9% estimate = {pop_65plus:,}")

    # 4. Compute density
    beds_per_1k = round(total_beds / pop_65plus * 1_000, 2) if pop_65plus else 0.0
    print(f"  Certified beds: {total_beds:,} | 65+ pop: {pop_65plus:,} | "
          f"Density: {beds_per_1k}/1k 65+")

    result = {
        "facility_count":       len(city_facilities),
        "total_certified_beds": total_beds,
        "avg_daily_residents":  avg_daily,
        "population_65plus":    pop_65plus,
        "beds_per_1k_65plus":   beds_per_1k,
    }

    out_dir = DATA_RAW / city_key
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "nursing_homes_meta.json").write_text(json.dumps(result, indent=2))
    print(f"  Saved to {out_dir / 'nursing_homes_meta.json'}")

    return {"city": city_key, "metric": "nursing_home_capacity", "data": result}


if __name__ == "__main__":
    city_key = sys.argv[1] if len(sys.argv) > 1 else "nyc"
    result = collect(city_key)
    print(json.dumps(result, indent=2))
