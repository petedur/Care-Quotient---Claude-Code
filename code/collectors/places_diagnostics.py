"""
Collector: CDC PLACES Community Wellbeing Diagnostics

Fetches ZCTA-level prevalence estimates from CDC PLACES (Local Data for
Better Health) and aggregates to city level. These metrics are reported
as community wellbeing context on city pages — NOT scored.

Measures collected:
  MHLTH      — Frequent mental distress (≥14 mentally unhealthy days/month, % adults)
  GHLTH      — Fair or poor self-rated general health (% adults)
  DEPRESSION — Diagnosed depression (% adults)

Why not scored: These are outcome measures, not capacity measures. A city
with high mental distress may need more care infrastructure, not less. Scoring
them would penalize cities for having populations that need care. They're
reported as need-context diagnostics alongside the capacity scores.

Data source: CDC PLACES 2025 release (BRFSS-modeled estimates, 2022/2023)
  Dataset ID: qnzd-25i4
  API: https://data.cdc.gov/resource/qnzd-25i4.json (Socrata)

Aggregation: population-weighted average across city ZCTAs.
Missing / suppressed ZCTAs (no Data_Value) are excluded from the weighted mean.
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

PLACES_URL = "https://data.cdc.gov/resource/qnzd-25i4.json"

MEASURES = ["MHLTH", "GHLTH", "DEPRESSION"]

MEASURE_LABELS = {
    "MHLTH":      "pct_frequent_mental_distress",
    "GHLTH":      "pct_fair_or_poor_health",
    "DEPRESSION":  "pct_depression",
}

BATCH_SIZE = 50   # max ZCTAs per API call; stays well within URL limits


def _fetch_batch(zctas: list[str], measures: list[str]) -> list[dict]:
    """Fetch PLACES data for a batch of ZCTAs across all specified measures."""
    zcta_list = "', '".join(zctas)
    measure_list = "', '".join(measures)
    where = f"LocationID in ('{zcta_list}') AND MeasureId in ('{measure_list}')"
    params = urllib.parse.urlencode({
        "$where": where,
        "$select": "LocationID,MeasureId,Data_Value,TotalPopulation",
        "$limit": str(BATCH_SIZE * len(measures) + 10),
    })
    url = f"{PLACES_URL}?{params}"
    resp = http_get_with_retry(url, timeout=30, label=f"PLACES {zctas[0]}–{zctas[-1]}")
    return resp.json()


def collect(city_key: str = "nyc") -> dict:
    city = CITIES[city_key]
    print(f"\n=== CDC PLACES Diagnostics — {city['name']} ===")

    city_zctas = sorted(city_to_zips(city_key))
    print(f"  City ZCTAs: {len(city_zctas)}")

    rows = []
    for i in range(0, len(city_zctas), BATCH_SIZE):
        batch = city_zctas[i:i + BATCH_SIZE]
        try:
            batch_rows = _fetch_batch(batch, MEASURES)
            rows.extend(batch_rows)
        except Exception as e:
            print(f"  WARN: batch {i}–{i+len(batch)} failed: {e}")
        if i > 0:
            time.sleep(0.3)   # gentle rate limiting

    if not rows:
        print(f"  SKIP: no PLACES data returned for {city_key}")
        return {"city": city_key, "metric": "places_diagnostics", "data": {}}

    df = pd.DataFrame(rows)
    df["Data_Value"]    = pd.to_numeric(df["Data_Value"],    errors="coerce")
    df["TotalPopulation"] = pd.to_numeric(df["TotalPopulation"], errors="coerce").fillna(0)

    # Wide format: one row per ZCTA with one column per measure
    wide = df.pivot_table(
        index=["LocationID", "TotalPopulation"],
        columns="MeasureId",
        values="Data_Value",
        aggfunc="first",
    ).reset_index()
    wide.columns.name = None
    wide = wide.rename(columns={"LocationID": "zcta", "TotalPopulation": "total_population"})

    out_dir = DATA_RAW / city_key
    out_dir.mkdir(parents=True, exist_ok=True)
    wide.to_csv(out_dir / "places_diagnostics.csv", index=False)

    # Population-weighted city-level aggregates
    summary = {}
    for measure_id, col_name in MEASURE_LABELS.items():
        if measure_id not in wide.columns:
            continue
        valid = wide.dropna(subset=[measure_id])
        if valid.empty:
            continue
        weighted_sum = (valid[measure_id] * valid["total_population"]).sum()
        total_pop    = valid["total_population"].sum()
        city_val     = round(weighted_sum / total_pop, 1) if total_pop else None
        summary[col_name] = city_val
        print(f"  {col_name}: {city_val}%")

    print(f"  Raw data saved to {out_dir / 'places_diagnostics.csv'}")
    return {"city": city_key, "metric": "places_diagnostics", "data": summary}


if __name__ == "__main__":
    city_key = sys.argv[1] if len(sys.argv) > 1 else "nyc"
    result = collect(city_key)
    print(json.dumps(result, indent=2))
