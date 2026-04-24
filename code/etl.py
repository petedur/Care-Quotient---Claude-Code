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
        NTEE_FAITH_BASED, NTEE_ALL_CARE, CITIES,
    )
    from collectors.nonprofit_density import _ntee_mask

    df  = pd.read_csv(raw, dtype=str, low_memory=False, encoding="latin-1")
    pop = CITIES[city_key]["population"]

    for label, codes in [
        ("social_support",    NTEE_SOCIAL_SUPPORT),
        ("care_institutions", NTEE_CARE_INSTITUTIONS),
        ("faith_based",       NTEE_FAITH_BASED),
        ("all_care",          NTEE_ALL_CARE),
    ]:
        subset  = df[_ntee_mask(df["NTEE_CD"], codes)]
        count   = len(subset)
        density = round(count / pop * 10_000, 2)
        upsert(conn, city_key, "nonprofit_density", label, value=density, count=count)

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


LOADERS = [
    load_nonprofit_density,
    load_residential_stability,
    load_library_density,
    load_health_centers,
]


def run():
    conn = get_conn()
    print(f"DuckDB: {DB_PATH}\n")

    for city_key in CITIES:
        print(f"-- {CITIES[city_key]['name']} --")
        for loader in LOADERS:
            loader(conn, city_key)

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
