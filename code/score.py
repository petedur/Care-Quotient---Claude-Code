"""
Scoring: normalize raw metrics -> pillar scores -> overall Care Capacity Index.

Reads from DuckDB (populated by etl.py) and writes a scored results table
back into the same database, plus a CSV summary to outputs/.

Normalization method: min-max scaling across the configured city set,
where higher values = better care capacity (score 0-100).
For residential_stability, higher = better (more embedded networks).
All density metrics: higher = better.

Usage:
    python code/score.py
"""

import sys
import json
import pandas as pd
import duckdb
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from config import DB_PATH, PROJECT_ROOT

OUTPUTS_DIR = PROJECT_ROOT / "outputs"
OUTPUTS_DIR.mkdir(exist_ok=True)

# ── Metric definitions ────────────────────────────────────────────────────────
# Each entry: (metric, sub_metric, pillar, weight)
# Weights within a pillar sum to 1.0.
# "higher is better" is assumed for all metrics here.

SCORED_METRICS = [
    # Pillar 1 — Social Support & Connection
    ("residential_stability",  "pct_same_house",    "pillar1", 0.30),
    ("nonprofit_density",      "care_institutions", "pillar1", 0.40),
    ("library_density",        "density_per_100k",  "pillar1", 0.15),
    ("library_density",        "visits_per_capita", "pillar1", 0.15),

    # Pillar 2 — Institutions of Care
    ("health_center_density",  "density_per_100k",  "pillar2", 0.40),
    ("nonprofit_density",      "faith_based",       "pillar2", 0.30),
    ("nonprofit_density",      "care_institutions", "pillar2", 0.30),
]

PILLAR_WEIGHTS = {
    "pillar1": 0.50,
    "pillar2": 0.50,
}

PILLAR_LABELS = {
    "pillar1": "Social Support & Connection",
    "pillar2": "Institutions of Care",
}


def load_metrics(conn) -> pd.DataFrame:
    return conn.execute(
        "SELECT city, metric, sub_metric, value FROM metrics WHERE value IS NOT NULL"
    ).fetchdf()


def normalize(series: pd.Series) -> pd.Series:
    """Min-max normalize a series to 0-100. Returns 50 for all if no variation."""
    lo, hi = series.min(), series.max()
    if hi == lo:
        return pd.Series([50.0] * len(series), index=series.index)
    return (series - lo) / (hi - lo) * 100


def score(df: pd.DataFrame) -> pd.DataFrame:
    """
    Returns a DataFrame with columns:
      city, pillar1, pillar2, overall, plus one column per scored metric.
    """
    # Pivot to wide: rows=city, columns=(metric, sub_metric)
    df["key"] = df["metric"] + "." + df["sub_metric"]
    wide = df.pivot(index="city", columns="key", values="value")

    results = pd.DataFrame(index=wide.index)

    # Normalize each scored metric
    for metric, sub_metric, pillar, weight in SCORED_METRICS:
        key = f"{metric}.{sub_metric}"
        if key not in wide.columns:
            print(f"  WARNING: missing metric '{key}' — skipping")
            continue
        col = f"norm_{key}"
        results[col] = normalize(wide[key])

    # Compute weighted pillar scores
    for pillar in ["pillar1", "pillar2"]:
        pillar_metrics = [(m, s, w) for m, s, p, w in SCORED_METRICS if p == pillar]
        cols = [f"norm_{m}.{s}" for m, s, w in pillar_metrics if f"norm_{m}.{s}" in results.columns]
        weights = [w for m, s, w in pillar_metrics if f"norm_{m}.{s}" in results.columns]

        if not cols:
            results[pillar] = float("nan")
            continue

        # Renormalize weights in case some metrics were missing
        total_w = sum(weights)
        results[pillar] = sum(
            results[c] * (w / total_w) for c, w in zip(cols, weights)
        )

    # Overall score
    results["overall"] = sum(
        results[p] * w for p, w in PILLAR_WEIGHTS.items()
        if p in results.columns
    )

    return results.round(1)


def write_results(conn, results: pd.DataFrame):
    """Save scored results to DuckDB and CSV."""
    # DuckDB
    conn.execute("DROP TABLE IF EXISTS scores")
    conn.execute("""
        CREATE TABLE scores AS SELECT * FROM results
    """)

    # CSV summary (just pillar scores + overall)
    summary_cols = ["pillar1", "pillar2", "overall"]
    available = [c for c in summary_cols if c in results.columns]
    summary = results[available].copy()
    summary.index.name = "city"
    summary.columns = [PILLAR_LABELS.get(c, c) for c in summary.columns[:-1]] + ["Overall"]
    summary = summary.sort_values("Overall", ascending=False)

    out_path = OUTPUTS_DIR / "care_capacity_scores.csv"
    summary.to_csv(out_path)
    print(f"\n  Scores saved to {out_path}")

    return summary


def run():
    conn = duckdb.connect(str(DB_PATH))

    print("Loading metrics from DuckDB...")
    df = load_metrics(conn)

    cities_with_data = df["city"].unique()
    print(f"Cities with data: {list(cities_with_data)}")

    if len(cities_with_data) < 2:
        print("\n  NOTE: Only one city has data. Scores require 2+ cities for normalization.")
        print("  Run the pipeline for additional cities first.")
        conn.close()
        return

    print("\nScoring...")
    results = score(df)

    # Register as a view for the SQL write
    conn.register("results", results.reset_index())
    summary = write_results(conn, results)

    print("\n-- Care Capacity Index --")
    print(summary.to_string())

    # Also write full metric dict to JSON
    metric_dict = {}
    for city in results.index:
        metric_dict[city] = {
            "overall": results.loc[city, "overall"],
            "pillar1_social_support": results.loc[city, "pillar1"],
            "pillar2_institutions_of_care": results.loc[city, "pillar2"],
        }

    json_path = OUTPUTS_DIR / "care_capacity_scores.json"
    with open(json_path, "w") as f:
        json.dump(metric_dict, f, indent=2)
    print(f"  JSON saved to {json_path}")

    conn.close()


if __name__ == "__main__":
    run()
