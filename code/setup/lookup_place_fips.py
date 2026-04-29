"""
One-time helper: look up Census place FIPS codes for every city in cities.csv.

Uses the Census ACS API to fetch all incorporated places in each state, then
fuzzy-matches each city name against place names. Outputs a CSV for review
before you paste the place_fips column into cities.csv.

Usage:
    python code/setup/lookup_place_fips.py

Output:
    data/place_fips_lookup.csv  — review this, then copy place_fips into cities.csv

After updating cities.csv, re-run the full pipeline.
"""

import sys
import json
import difflib
import requests
import pandas as pd
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from config import PROJECT_ROOT, get_census_api_key

ACS_URL  = "https://api.census.gov/data/2022/acs/acs5"
OUT_PATH = PROJECT_ROOT / "data" / "place_fips_lookup.csv"

# ── Special-case overrides ─────────────────────────────────────────────────────
# Cities whose Census place names don't match their common names or whose
# government structure requires a specific place FIPS.
KNOWN_OVERRIDES = {
    # consolidated city-counties / unified governments
    "washington_dc": ("11", "50000", "District of Columbia"),
    "san_francisco": ("06", "67000", "San Francisco city, California"),
    "indianapolis":  ("18", "36003", "Indianapolis city (balance), Indiana"),
    "nashville":     ("47", "52006", "Nashville-Davidson metropolitan government (balance), Tennessee"),
    "louisville":    ("21", "48006", "Louisville/Jefferson County metro government (balance), Kentucky"),
    "lexington":     ("21", "46027", "Lexington-Fayette urban county, Kentucky"),
    "anchorage":     ("02", "03000", "Anchorage municipality, Alaska"),
    "honolulu":      ("15", "17000", "Urban Honolulu CDP, Hawaii"),
}


def fetch_places(state_fips: str, api_key: str) -> pd.DataFrame:
    """Return all Census places in a state as a DataFrame."""
    params = {
        "key": api_key,
        "get": "NAME",
        "for": "place:*",
        "in":  f"state:{state_fips}",
    }
    try:
        r = requests.get(ACS_URL, params=params, timeout=30)
        r.raise_for_status()
        data = r.json()
    except Exception as e:
        print(f"    ERROR fetching places for state {state_fips}: {e}")
        return pd.DataFrame(columns=["name", "state", "place"])
    headers = data[0]
    rows = data[1:]
    return pd.DataFrame(rows, columns=headers)


def normalize_name(name: str) -> str:
    """Strip state suffix and lowercase for matching."""
    # "Chicago city, Illinois" → "chicago city"
    if "," in name:
        name = name.split(",")[0]
    return name.lower().strip()


def best_match(city_name: str, place_df: pd.DataFrame) -> tuple[str, str, float]:
    """
    Return (place_fips, matched_full_name, confidence) for the best-matching
    Census place name. Confidence is 0.0–1.0.
    """
    if place_df.empty:
        return ("", "", 0.0)

    # Normalize target: "New York City" → "new york city"
    target = city_name.lower().strip()

    place_df = place_df.copy()
    place_df["norm"] = place_df["NAME"].apply(normalize_name)

    # 1. Exact match
    exact = place_df[place_df["norm"] == target]
    if not exact.empty:
        row = exact.iloc[0]
        return (row["place"], row["NAME"], 1.0)

    # 2. "city" suffix match: "new york city" → try "new york city"
    # Many Census place names are "X city" (lower-case city)
    target_city = target if target.endswith(" city") else target + " city"
    city_match = place_df[place_df["norm"] == target_city]
    if not city_match.empty:
        row = city_match.iloc[0]
        return (row["place"], row["NAME"], 0.95)

    # 3. Starts-with match (handles "X city (balance)")
    starts = place_df[place_df["norm"].str.startswith(target)]
    if not starts.empty:
        row = starts.iloc[0]
        return (row["place"], row["NAME"], 0.90)

    # 4. Fuzzy match
    norms = place_df["norm"].tolist()
    close = difflib.get_close_matches(target, norms, n=1, cutoff=0.6)
    if close:
        row = place_df[place_df["norm"] == close[0]].iloc[0]
        score = difflib.SequenceMatcher(None, target, close[0]).ratio()
        return (row["place"], row["NAME"], round(score, 2))

    return ("", "", 0.0)


def run():
    api_key = get_census_api_key()
    cities_csv = PROJECT_ROOT / "data" / "cities.csv"
    cities_df  = pd.read_csv(cities_csv, dtype=str)

    # Cache places by state so we only fetch each state once
    places_cache: dict[str, pd.DataFrame] = {}

    results = []
    for _, row in cities_df.iterrows():
        city_key  = row["city_key"]
        city_name = row["name"]
        state     = row["state"]
        state_fips = row["state_fips"].zfill(2)

        # Check hardcoded overrides first
        if city_key in KNOWN_OVERRIDES:
            sf, pf, matched = KNOWN_OVERRIDES[city_key]
            results.append({
                "city_key":       city_key,
                "city_name":      city_name,
                "state":          state,
                "place_fips":     pf,
                "matched_name":   matched,
                "confidence":     "override",
                "needs_review":   "no",
            })
            print(f"  {city_key:<20} {pf}  (override: {matched})")
            continue

        if state_fips not in places_cache:
            print(f"  Fetching all places in state {state_fips} ({state})...")
            places_cache[state_fips] = fetch_places(state_fips, api_key)

        place_df = places_cache[state_fips]
        fips, matched_name, conf = best_match(city_name, place_df)
        needs_review = "YES" if conf < 0.9 else "no"

        results.append({
            "city_key":       city_key,
            "city_name":      city_name,
            "state":          state,
            "place_fips":     fips,
            "matched_name":   matched_name,
            "confidence":     conf,
            "needs_review":   needs_review,
        })
        flag = "  *** REVIEW ***" if needs_review == "YES" else ""
        print(f"  {city_key:<20} {fips or '?????'}  {conf}  {matched_name}{flag}")

    out_df = pd.DataFrame(results)
    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    out_df.to_csv(OUT_PATH, index=False)
    print(f"\nSaved to {OUT_PATH}")

    flagged = out_df[out_df["needs_review"] == "YES"]
    if not flagged.empty:
        print(f"\n{len(flagged)} cities need manual review:")
        for _, r in flagged.iterrows():
            print(f"  {r['city_key']}: matched '{r['matched_name']}' ({r['confidence']})")
        print("\nEdit place_fips in the CSV, then copy the place_fips column into cities.csv.")
    else:
        print("\nAll matches look good. Copy the place_fips column into cities.csv.")
        print("Then re-run the full pipeline: python code/pipeline.py")


if __name__ == "__main__":
    run()
