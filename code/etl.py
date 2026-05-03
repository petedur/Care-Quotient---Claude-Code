"""
ETL: Load raw collector results into a DuckDB analytical database.

After running collectors, call this script to merge everything into
care_capacity.duckdb — a single file you can query with SQL.

Usage:
    python code/etl.py
"""

import json
import sys
import duckdb
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from config import DB_PATH, DATA_RAW, CITIES

# ── Schema ────────────────────────────────────────────────────────────────────
# One row per (city, metric, sub_metric).
# All values are stored as floats; counts stored separately.

SCHEMA = """
CREATE TABLE IF NOT EXISTS metrics (
    city        VARCHAR NOT NULL,
    metric      VARCHAR NOT NULL,
    sub_metric  VARCHAR NOT NULL,
    value       DOUBLE,
    count       INTEGER,
    notes       VARCHAR,
    collected_at TIMESTAMP DEFAULT current_timestamp
);
"""


def get_conn() -> duckdb.DuckDBPyConnection:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = duckdb.connect(str(DB_PATH))
    conn.execute(SCHEMA)
    return conn


def upsert(conn, city: str, metric: str, sub_metric: str,
           value: float = None, count: int = None, notes: str = None):
    """Delete existing row for this (city, metric, sub_metric) then insert fresh."""
    conn.execute(
        "DELETE FROM metrics WHERE city=? AND metric=? AND sub_metric=?",
        [city, metric, sub_metric]
    )
    conn.execute(
        "INSERT INTO metrics (city, metric, sub_metric, value, count, notes) VALUES (?,?,?,?,?,?)",
        [city, metric, sub_metric, value, count, notes]
    )


# ── Loaders — one per collector ───────────────────────────────────────────────

def load_nonprofit_density(conn, city_key: str):
    raw = DATA_RAW / city_key / "nonprofits_care.csv"
    if not raw.exists():
        print(f"  SKIP nonprofit_density for {city_key} (no raw file)")
        return

    import pandas as pd
    from config import (
        NTEE_SOCIAL_SUPPORT, NTEE_CARE_INSTITUTIONS,
        NTEE_COMBINED_CARE, NTEE_FAITH_BASED, NTEE_ALL_CARE, CITIES,
    )
    from collectors.nonprofit_density import _ntee_mask

    df  = pd.read_csv(raw, dtype=str, low_memory=False, encoding="latin-1")
    pop = CITIES[city_key]["population"]

    # Quality filter: 501(c)(3) only (SUBSECTION=03) and active status (01/02).
    # IRS BMF includes 501(c)(4)/(5)/(6) orgs with NTEE P/E/F/K codes (~2% of
    # care orgs). Methodology commits to 501(c)(3) organizations; filter here
    # to match. STATUS 01=unconditional exemption, 02=conditional exemption.
    df = df[df["SUBSECTION"].isin(["03"]) & df["STATUS"].isin(["01", "02"])].copy()

    combined_care_count = 0
    for label, codes in [
        ("social_support",    NTEE_SOCIAL_SUPPORT),
        ("care_institutions", NTEE_CARE_INSTITUTIONS),
        ("combined_care",     NTEE_COMBINED_CARE),   # scored metric: P+E+F+K
        ("faith_based",       NTEE_FAITH_BASED),
        ("all_care",          NTEE_ALL_CARE),
    ]:
        subset  = df[_ntee_mask(df["NTEE_CD"], codes)]
        count   = len(subset)
        density = round(count / pop * 10_000, 2)
        upsert(conn, city_key, "nonprofit_density", label, value=density, count=count)
        if label == "combined_care":
            combined_care_count = count

    # Shadow diagnostic: combined care nonprofits per 10k residents at 0–150% FPL.
    # Uses the distressed population already collected by snap_participation.
    # This allows direct comparison between total-pop and need-adjusted framings
    # without changing the scored metric. See methodology Section 3.3 and 9.13.
    snap_raw = DATA_RAW / city_key / "snap_participation.csv"
    if snap_raw.exists():
        snap_df = pd.read_csv(snap_raw)
        distressed_pop = int(snap_df["eligible_pop_0_149pct_fpl"].sum())
        if distressed_pop > 0:
            distressed_density = round(combined_care_count / distressed_pop * 10_000, 2)
            upsert(conn, city_key, "nonprofit_density", "combined_care_per_10k_distressed",
                   value=distressed_density, count=combined_care_count,
                   notes=f"distressed_pop={distressed_pop}")

    print(f"  nonprofit_density loaded for {city_key}")


def load_residential_stability(conn, city_key: str):
    raw = DATA_RAW / city_key / "residential_stability.csv"
    if not raw.exists():
        print(f"  SKIP residential_stability for {city_key} (no raw file)")
        return

    import pandas as pd
    df = pd.read_csv(raw)
    total_same = df["same_house"].sum()
    total_pop  = df["population"].sum()
    pct = round(total_same / total_pop * 100, 2) if total_pop else 0

    upsert(conn, city_key, "residential_stability", "pct_same_house", value=pct)
    print(f"  residential_stability loaded for {city_key}: {pct}%")


def load_library_density(conn, city_key: str):
    raw = DATA_RAW / city_key / "libraries.csv"
    if not raw.exists():
        print(f"  SKIP library_density for {city_key} (no raw file)")
        return

    import pandas as pd
    from config import CITIES
    df  = pd.read_csv(raw, dtype=str, low_memory=False)
    pop = CITIES[city_key]["population"]

    count   = len(df)
    density = round(count / pop * 100_000, 2)
    upsert(conn, city_key, "library_density", "density_per_100k", value=density, count=count)

    # Visits per capita if column present
    visits_col = next((c for c in df.columns if "VISIT" in c.upper()), None)
    if visits_col:
        total_visits = pd.to_numeric(df[visits_col], errors="coerce").sum()
        vpc = round(total_visits / pop, 2)
        upsert(conn, city_key, "library_density", "visits_per_capita", value=vpc)

    print(f"  library_density loaded for {city_key}: {count} libraries")


# ── Main ──────────────────────────────────────────────────────────────────────

def load_health_centers(conn, city_key: str):
    raw = DATA_RAW / city_key / "health_centers.csv"
    if not raw.exists():
        print(f"  SKIP health_center_density for {city_key} (no raw file)")
        return

    import pandas as pd
    from config import CITIES
    df  = pd.read_csv(raw, dtype=str, low_memory=False)
    pop = CITIES[city_key]["population"]

    count   = len(df)
    density = round(count / pop * 100_000, 2)
    upsert(conn, city_key, "health_center_density", "density_per_100k", value=density, count=count)
    print(f"  health_center_density loaded for {city_key}: {count} FQHCs")


def load_housing_cost_burden(conn, city_key: str):
    raw = DATA_RAW / city_key / "housing_cost_burden.csv"
    if not raw.exists():
        print(f"  SKIP housing_cost_burden for {city_key} (no raw file)")
        return

    import pandas as pd
    df = pd.read_csv(raw)
    total_burdened = df["burdened"].sum()
    total_hh       = df["total"].sum()
    pct_not_burdened = round((1 - total_burdened / total_hh) * 100, 2) if total_hh else 0

    upsert(conn, city_key, "housing_cost_burden", "pct_not_burdened", value=pct_not_burdened)
    print(f"  housing_cost_burden loaded for {city_key}: {pct_not_burdened}% not burdened")


def load_snap_participation(conn, city_key: str):
    raw = DATA_RAW / city_key / "snap_participation.csv"
    if not raw.exists():
        print(f"  SKIP snap_participation for {city_key} (no raw file)")
        return

    import pandas as pd
    df = pd.read_csv(raw)
    total_snap     = df["snap_households"].sum()
    total_hh       = df["total_households"].sum()
    total_eligible = df["eligible_pop_0_149pct_fpl"].sum()
    total_pop      = df["total_pop"].sum()

    snap_rate      = total_snap / total_hh if total_hh else 0
    eligible_rate  = total_eligible / total_pop if total_pop else 0
    coverage = round(min((snap_rate / eligible_rate) * 100, 100.0), 2) \
        if eligible_rate > 0 else 0.0

    upsert(conn, city_key, "snap_participation", "coverage_rate", value=coverage)
    print(f"  snap_participation loaded for {city_key}: {coverage}% coverage rate")


def load_health_insurance(conn, city_key: str):
    raw = DATA_RAW / city_key / "health_insurance.csv"
    if not raw.exists():
        print(f"  SKIP health_insurance_coverage for {city_key} (no raw file)")
        return

    import pandas as pd
    df = pd.read_csv(raw)
    total_pop     = df["total_pop"].sum()
    total_insured = df["insured"].sum()
    pct_insured   = round(total_insured / total_pop * 100, 2) if total_pop else 0

    upsert(conn, city_key, "health_insurance_coverage", "pct_insured", value=pct_insured)
    print(f"  health_insurance_coverage loaded for {city_key}: {pct_insured}% insured")


def load_nursing_homes(conn, city_key: str):
    meta = DATA_RAW / city_key / "nursing_homes_meta.json"
    if not meta.exists():
        print(f"  SKIP nursing_home_capacity for {city_key} (no meta file — run collector first)")
        return

    import json
    d = json.loads(meta.read_text())
    beds_per_1k   = d.get("beds_per_1k_65plus", 0.0)
    daily_res     = d.get("avg_daily_residents", 0.0)
    facility_count = d.get("facility_count", 0)
    pop_65plus    = d.get("population_65plus", 0)

    upsert(conn, city_key, "nursing_home_capacity", "beds_per_1k_65plus",
           value=beds_per_1k, count=facility_count)
    # Diagnostics
    upsert(conn, city_key, "nursing_home_capacity", "avg_daily_residents",
           value=daily_res, count=facility_count)
    upsert(conn, city_key, "nursing_home_capacity", "population_65plus",
           value=float(pop_65plus))
    print(f"  nursing_home_capacity loaded for {city_key}: "
          f"{beds_per_1k} beds/1k 65+ ({facility_count} facilities)")


LOADERS = [
    load_nonprofit_density,
    load_residential_stability,
    load_library_density,
    load_health_centers,
    load_housing_cost_burden,
    load_snap_participation,
    load_health_insurance,
    load_nursing_homes,
]

# ── Validation ────────────────────────────────────────────────────────────────
# Each entry: (metric, sub_metric, min_valid, max_valid)
# Checked after all loaders run. Failures are printed as WARNINGs — the
# pipeline does not abort, but the scoring step will produce unreliable
# results until flagged rows are investigated.

VALIDATION_RULES = [
    # Residential stability: a percentage — must be 0–100
    ("residential_stability", "pct_same_house",    0.0,  100.0),
    # Nonprofit density: per 10k — 0 is possible; 200 would be anomalous
    ("nonprofit_density",     "social_support",    0.0,  200.0),
    ("nonprofit_density",     "care_institutions", 0.0,  200.0),
    ("nonprofit_density",     "faith_based",       0.0,  200.0),
    ("nonprofit_density",     "all_care",          0.0,  500.0),
    # FQHC density: per 100k — 0 is possible; 100 would be anomalous
    ("health_center_density", "density_per_100k",  0.0,  100.0),
    # Library density: per 100k — 0 possible; 50 would be anomalous
    ("library_density",       "density_per_100k",  0.0,   50.0),
    ("library_density",       "visits_per_capita", 0.0, 1000.0),
    # Housing cost burden: % not burdened — must be 0–100
    ("housing_cost_burden",       "pct_not_burdened", 0.0, 100.0),
    # SNAP coverage rate: 0–100 (capped in collector)
    ("snap_participation",        "coverage_rate",    0.0, 100.0),
    # Health insurance: % insured — must be 0–100
    ("health_insurance_coverage", "pct_insured",      0.0, 100.0),
    # Nursing home capacity: beds per 1k residents 65+ — 0 possible; 150 would be anomalous
    ("nursing_home_capacity",     "beds_per_1k_65plus", 0.0, 150.0),
]

# Scored metrics that must be present for every city; missing = pipeline gap.
# V3: combined_care replaces the separate social_support + care_institutions
# scored metrics. Sub-components are retained as diagnostics, not scored.
# V4: nursing_home_capacity added as third Pillar 2 metric.
REQUIRED_SCORED = [
    ("residential_stability",     "pct_same_house"),
    ("nonprofit_density",         "combined_care"),
    ("health_center_density",     "density_per_100k"),
    ("nursing_home_capacity",     "beds_per_1k_65plus"),
    ("housing_cost_burden",       "pct_not_burdened"),
    ("snap_participation",        "coverage_rate"),
    ("health_insurance_coverage", "pct_insured"),
]


def validate(conn) -> bool:
    """
    Run schema and range checks on the loaded metrics table.
    Prints warnings for any anomalies. Returns True if all checks pass.
    """
    import math

    df = conn.execute(
        "SELECT city, metric, sub_metric, value FROM metrics WHERE value IS NOT NULL"
    ).fetchdf()

    issues = []

    # 1. Required scored metrics present for every city that has any data
    cities_with_data = set(df["city"].unique())
    for city_key in cities_with_data:
        for metric, sub_metric in REQUIRED_SCORED:
            rows = df[
                (df["city"] == city_key) &
                (df["metric"] == metric) &
                (df["sub_metric"] == sub_metric)
            ]
            if rows.empty:
                issues.append(
                    f"MISSING  {city_key}: {metric}.{sub_metric} — city will be unscored"
                )

    # 2. Value type and range checks
    for metric, sub_metric, lo, hi in VALIDATION_RULES:
        subset = df[(df["metric"] == metric) & (df["sub_metric"] == sub_metric)]
        for _, row in subset.iterrows():
            v = row["value"]
            city = row["city"]
            if not isinstance(v, (int, float)) or math.isnan(v):
                issues.append(
                    f"NON-NUMERIC  {city}: {metric}.{sub_metric} = {v!r}"
                )
            elif not (lo <= v <= hi):
                issues.append(
                    f"OUT-OF-RANGE  {city}: {metric}.{sub_metric} = {v} "
                    f"(expected {lo}–{hi})"
                )

    # Report
    print("\n-- Validation --")
    if not issues:
        print("  All checks passed.")
        return True
    for msg in issues:
        print(f"  WARNING: {msg}")
    print(f"\n  {len(issues)} issue(s) found. Investigate before scoring.")
    return False


def run():
    conn = get_conn()
    print(f"DuckDB: {DB_PATH}\n")

    for city_key in CITIES:
        print(f"-- {CITIES[city_key]['name']} --")
        for loader in LOADERS:
            loader(conn, city_key)

    validate(conn)

    # Show summary
    print("\n-- Summary --")
    result = conn.execute("""
        SELECT city, metric, sub_metric, value, count
        FROM metrics
        ORDER BY city, metric, sub_metric
    """).fetchdf()
    print(result.to_string(index=False))
    conn.close()


if __name__ == "__main__":
    run()
