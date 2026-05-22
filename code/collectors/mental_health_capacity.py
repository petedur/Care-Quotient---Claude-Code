"""
Collector: Mental Health Provider Capacity

Counts licensed mental health practitioners registered in the NPPES NPI Registry
for each city's ZCTAs. Provider types:
  - Psychiatrists (taxonomy: Psychiatry)
  - Clinical Psychologists (taxonomy: Psychologist)
  - Mental Health Counselors (taxonomy: Mental Health)
  - Licensed Clinical Social Workers (taxonomy: Social Worker)
  - Marriage & Family Therapists (taxonomy: Marriage & Family)

Why NPPES: The NPI Registry is the most complete national dataset of licensed
healthcare providers. It is public, frequently updated, and captures providers
across all payer types (not just Medicare billing providers).

Known limitations:
  1. NPPES results are capped at 200 per query. Large cities or densely populated
     ZCTAs may be undercounted. Cities where any ZCTA hits the cap are flagged.
  2. ZCTAs extend beyond strict city limits; providers in neighboring suburbs with
     overlapping ZCTAs are included. This causes overcounting in cities with many
     nearby suburbs sharing ZIP codes. Observed values (~800-1200/100k) are
     3-4x higher than expected urban norms (~200-400/100k) due to this geographic
     spillover. Unlike FQHCs/nursing homes (which have coordinates for spatial
     filtering), NPPES has no lat/lng — spillover can only be reduced by filtering
     on the provider's listed city name field, which introduces its own noise.

STATUS: Diagnostic only — NOT integrated into CQ scoring.
  The spillover problem makes the raw counts unreliable for scoring. The metric
  is collected and reported on city pages as context only.

V7 paths if this is revisited:
  Option A — Fix collector + recalibrate benchmark:
    Filter results to provider_practice_location_address_city_name == target city.
    Re-run on 10-15 cities, compare to SAMHSA county workforce data, set a benchmark
    that creates meaningful spread post-fix. Note: urban MH provider density is
    genuinely high; the national shortage is rural. The proposed 125/100k benchmark
    will likely leave all cities near 100 even after fixing spillover — benchmark
    may need to be 400-500/100k to discriminate.
  Option B — HRSA shortage-area framing:
    Score cities by % of population NOT in a Mental Health Professional Shortage
    Area (MH-HPSA). Avoids spillover entirely; uses a validated federal designation.
    Downside: HPSA is a shortage flag, not a continuous density measure.

Data source: CMS NPI Registry API (NPPES)
  https://npiregistry.cms.hhs.gov/api/?version=2.1

Benchmark (proposed): 125 MH providers per 100,000 residents.
  Rationale: SAMHSA estimates ~22% of US adults experience mental illness annually.
  At a caseload of ~175 patients per FTE MH practitioner (SAMHSA BHSIS benchmark),
  adequate coverage for a city requires ~126 providers per 100k. Rounded to 125/100k.
  This is an aspirational benchmark — no major US city currently meets it — which
  is consistent with the CQ design principle of measuring against an ideal, not
  against peer cities.

NOTE: Decision made — diagnostic only for V6/V7. See STATUS above for V7 paths.
"""

import sys
import json
import time
import urllib.parse
import pandas as pd
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from config import DATA_RAW, CITIES
from collectors.utils import http_get_with_retry
from geo.city_zips import city_to_zips

NPPES_URL = "https://npiregistry.cms.hhs.gov/api/"

# Taxonomy description strings — NPPES prefix-searches these
TAXONOMY_QUERIES = [
    "Psychiatry",
    "Psychologist",
    "Mental Health",
    "Social Worker",
    "Marriage & Family",
]

NPPES_LIMIT = 200  # max results per call; counts ≥200 are flagged


def _query_nppes(taxonomy_desc: str, postal_code: str) -> list[dict]:
    """Return up to NPPES_LIMIT NPI records for a taxonomy+zip combo."""
    params = urllib.parse.urlencode({
        "version": "2.1",
        "taxonomy_description": taxonomy_desc,
        "postal_code": postal_code,
        "enumeration_type": "NPI-1",  # individual providers only
        "limit": str(NPPES_LIMIT),
    })
    url = f"{NPPES_URL}?{params}"
    try:
        resp = http_get_with_retry(url, timeout=20, label=f"NPPES {postal_code}/{taxonomy_desc[:12]}")
        return resp.json().get("results", [])
    except Exception as e:
        print(f"  WARN: NPPES query failed for {postal_code}/{taxonomy_desc}: {e}")
        return []


def collect(city_key: str = "boston") -> dict:
    city = CITIES[city_key]
    print(f"\n=== Mental Health Provider Capacity — {city['name']} ===")

    city_zctas = sorted(city_to_zips(city_key))
    print(f"  City ZCTAs: {len(city_zctas)}")

    all_npis: set[str] = set()
    capped_zips: list[str] = []

    for zcta in city_zctas:
        zcta_npis: set[str] = set()
        for taxonomy in TAXONOMY_QUERIES:
            results = _query_nppes(taxonomy, zcta)
            for r in results:
                npi = r.get("number")
                if npi:
                    zcta_npis.add(npi)
            time.sleep(0.15)  # gentle rate limiting

        if len(zcta_npis) >= NPPES_LIMIT * len(TAXONOMY_QUERIES) * 0.9:
            capped_zips.append(zcta)
            print(f"  WARN: {zcta} may be undercounted (near cap: {len(zcta_npis)} NPIs)")

        all_npis |= zcta_npis

    pop = city["population"]
    count = len(all_npis)
    density = round(count / pop * 100_000, 1)

    print(f"  Unique MH providers: {count}")
    print(f"  Density per 100k: {density}")
    if capped_zips:
        print(f"  WARN: Possible undercount in ZCTAs: {capped_zips}")

    # Save raw per-city summary
    out_dir = DATA_RAW / city_key
    out_dir.mkdir(parents=True, exist_ok=True)
    summary = {
        "city": city_key,
        "mh_provider_count": count,
        "mh_providers_per_100k": density,
        "capped_zips": capped_zips,
        "zcta_count": len(city_zctas),
    }
    out_path = out_dir / "mental_health_capacity.json"
    out_path.write_text(json.dumps(summary, indent=2))
    print(f"  Saved to {out_path}")

    return {"city": city_key, "metric": "mental_health_capacity", "data": summary}


if __name__ == "__main__":
    city_key = sys.argv[1] if len(sys.argv) > 1 else "boston"
    result = collect(city_key)
    print(json.dumps(result, indent=2))
