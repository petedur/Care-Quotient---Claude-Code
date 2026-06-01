"""
Collector: Child Care Capacity

Measures licensed child care establishments per city using Census County Business
Patterns (CBP) NAICS code 624410 (Child Day Care Services), then normalizes by
the under-5 population from ACS B01001.

Why CBP: County Business Patterns is the most complete national dataset of licensed
business establishments. NAICS 624410 captures daycare centers, Head Start programs,
family daycare homes, and preschools. It does not capture informal arrangements
(grandparent care, unlicensed home daycare), which is a known limitation.

Data sources:
  1. Census CBP API — establishments by county, NAICS 624410
     https://api.census.gov/data/{year}/cbp?get=ESTAB&for=county:*&NAICS2017=624410
  2. Census ACS 5-year — under-5 population by county (B01001_003E + B01001_027E)
     Uses county geography to match the county-level CBP numerator. Querying by
     Census Place (city boundary) would create a numerator/denominator mismatch for
     cities that represent a small fraction of their county population.

Normalization: establishments per 1,000 children under 5
  This accounts for the natural variation in need (cities with more young children
  need more care establishments).

Benchmark (proposed): 15 child care establishments per 1,000 children under 5.
  Rationale: Nationally, there are ~47k licensed child care centers serving ~12M
  children in center-based care (NSECE 2019). That implies ~3.9 centers per 1k
  children in centers. Family daycare homes add roughly the same count again.
  A city meeting the CCDBG access standard (coverage for 50% of income-eligible
  children) would need roughly 15/1k children in licensed settings. Aspirational
  benchmark; no current city likely meets it at scale.

NOTE: This collector uses county-level establishment data, not city-level.
  Multi-county cities (NYC, Chicago, LA) aggregate across their counties. The
  county-to-city mapping uses the same county_fips from cities.csv as all
  other collectors.
"""

import sys
import json
import pandas as pd
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from config import DATA_RAW, CITIES, get_census_api_key
from collectors.utils import http_get_with_retry

CBP_YEAR = "2021"  # most recent CBP data with complete 624410 coverage


def _get_county_establishments(state_fips: str, county_fips_set: set) -> int:
    """Fetch child care establishment count from CBP for given counties."""
    key = get_census_api_key()
    url = (
        f"https://api.census.gov/data/{CBP_YEAR}/cbp"
        f"?get=ESTAB&for=county:*&in=state:{state_fips}"
        f"&NAICS2017=624410&key={key}"
    )
    resp = http_get_with_retry(url, timeout=30, label=f"CBP {state_fips}")
    rows = resp.json()
    # rows[0] is header: ['ESTAB', 'state', 'county']
    headers = rows[0]
    estab_idx = headers.index("ESTAB")
    county_idx = headers.index("county")
    state_idx = headers.index("state")

    total = 0
    for row in rows[1:]:
        full_fips = row[state_idx].zfill(2) + row[county_idx].zfill(3)
        if full_fips in county_fips_set:
            try:
                total += int(row[estab_idx])
            except (ValueError, TypeError):
                pass
    return total


def _get_under5_pop_county(city_key: str) -> int:
    """Get under-5 population from ACS for city's counties (matching CBP geography)."""
    key = get_census_api_key()
    cfg = CITIES[city_key]
    state_fips = cfg["state_fips"]
    county_fips = cfg["county_fips"]

    # ACS B01001: under-5 = B01001_003E (male) + B01001_027E (female), by county
    url = (
        f"https://api.census.gov/data/2022/acs/acs5"
        f"?get=B01001_003E,B01001_027E"
        f"&for=county:*&in=state:{state_fips}&key={key}"
    )
    try:
        resp = http_get_with_retry(url, timeout=20, label=f"ACS under5 county {city_key}")
        rows = resp.json()
        headers = rows[0]
        male_idx   = headers.index("B01001_003E")
        female_idx = headers.index("B01001_027E")
        county_idx = headers.index("county")
        state_idx  = headers.index("state")

        total = 0
        for row in rows[1:]:
            full_fips = row[state_idx].zfill(2) + row[county_idx].zfill(3)
            if full_fips in county_fips:
                male   = int(row[male_idx])   if row[male_idx]   not in (None, "null") else 0
                female = int(row[female_idx]) if row[female_idx] not in (None, "null") else 0
                total += male + female
        return total if total > 0 else int(cfg["population"] * 0.062)
    except Exception as e:
        print(f"  WARN: ACS under-5 county query failed for {city_key}: {e}")
        return int(cfg["population"] * 0.062)


def collect(city_key: str = "chicago") -> dict:
    city = CITIES[city_key]
    print(f"\n=== Child Care Capacity — {city['name']} ===")

    county_fips = city["county_fips"]
    state_fips = city["state_fips"]

    # 1. Get establishments
    try:
        estab_count = _get_county_establishments(state_fips, county_fips)
    except Exception as e:
        print(f"  ERROR: CBP query failed: {e}")
        return {"city": city_key, "metric": "child_care_capacity", "data": {}}

    # 2. Get under-5 population (county-level to match CBP numerator geography)
    under5 = _get_under5_pop_county(city_key)
    if under5 <= 0:
        print(f"  SKIP: could not get under-5 population")
        return {"city": city_key, "metric": "child_care_capacity", "data": {}}

    # 3. Compute density
    density = round(estab_count / under5 * 1_000, 2)

    print(f"  Child care establishments (NAICS 624410): {estab_count}")
    print(f"  Population under 5: {under5:,}")
    print(f"  Density per 1,000 children under 5: {density}")

    # Save
    out_dir = DATA_RAW / city_key
    out_dir.mkdir(parents=True, exist_ok=True)
    summary = {
        "city": city_key,
        "childcare_establishments": estab_count,
        "population_under_5": under5,
        "childcare_per_1k_under5": density,
    }
    (out_dir / "child_care_capacity.json").write_text(json.dumps(summary, indent=2))

    return {"city": city_key, "metric": "child_care_capacity", "data": summary}


if __name__ == "__main__":
    city_key = sys.argv[1] if len(sys.argv) > 1 else "chicago"
    result = collect(city_key)
    print(json.dumps(result, indent=2))
