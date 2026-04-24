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

# ── Scored metrics with literature-based weights ──────────────────────────────
#
# Pillar 1: Social Support & Connection (50% of overall score)
#
#   Residential stability — weight 0.60
#   Strongest predictor of social capital in the literature. Putnam (2000)
#   "Bowling Alone" identifies residential stability as one of the top
#   structural predictors of civic engagement and social trust. Sampson,
#   Raudenbush & Earls (1997) demonstrate that stability enables "collective
#   efficacy" — the shared willingness of residents to intervene for each
#   other. Evidence quality: HIGH.
#
#   Human services nonprofit density (NTEE P) — weight 0.40
#   Salamon & Anheier (1998) establish nonprofit density as an indicator of
#   civil society infrastructure. Boris & Steuerle (2006) link human-service
#   nonprofits directly to care provision for vulnerable populations. Weaker
#   than residential stability because density does not guarantee utilization
#   or accessibility. Evidence quality: MODERATE.
#
# Pillar 2: Institutions of Care (50% of overall score)
#
#   FQHC density — weight 0.50
#   Strongest evidence base of all scored metrics. Rosenbaum et al. (2011)
#   show FQHCs significantly reduce ER utilization among low-income patients.
#   Shi et al. (multiple studies) link FQHC access to reduced mortality from
#   chronic disease and improved preventive care uptake. CBO analyses
#   consistently find FQHCs save ~$2,371/user in avoided ER costs. Evidence
#   derives from quasi-experimental designs. Evidence quality: VERY HIGH.
#
#   Health/mental health/food nonprofit density (NTEE E/F/K) — weight 0.30
#   Kim & Jennings (2012) find nonprofit human service density correlates with
#   lower poverty rates and better health outcomes at the county level.
#   Pettijohn & Boris (2013) document the direct care role of health and food
#   nonprofits for populations unable to access formal services. Evidence
#   quality: MODERATE-HIGH.
#
#   Faith-based human services (NTEE X3x) — weight 0.20
#   Cnaan et al. (2006) "The Other Philadelphia Story" documents meaningful
#   social service provision through congregations, estimating $140k-$265k
#   annual value per active congregation. Johnson, Tompkins & Webb (2002)
#   find faith-based programs effective for food security and crisis response.
#   Weight is intentionally lower than the others: evidence is compelling in
#   specific contexts but harder to generalize, and our X30 filter understates
#   actual faith-based care (many orgs file under P rather than X). Evidence
#   quality: MODERATE.

SCORED_METRICS = [
    # Pillar 1 — Social Support & Connection
    ("residential_stability", "pct_same_house",   "pillar1", 0.60),
    ("nonprofit_density",     "social_support",   "pillar1", 0.40),

    # Pillar 2 — Institutions of Care
    ("health_center_density", "density_per_100k", "pillar2", 0.50),
    ("nonprofit_density",     "care_institutions","pillar2", 0.30),
    ("nonprofit_density",     "faith_based",      "pillar2", 0.20),
]

# Diagnostic metrics — collected and reported, but not included in scored pillars
DIAGNOSTIC_METRICS = [
    ("library_density",   "density_per_100k",  "Libraries per 100k residents"),
    ("library_density",   "visits_per_capita", "Library visits per capita"),
    ("nonprofit_density", "all_care",          "All care-related nonprofits per 10k (diagnostic)"),
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

    # Print diagnostic metrics (not scored, reported separately)
    print("\n-- Diagnostic Metrics (not scored) --")
    raw_df = load_metrics(conn)
    for metric, sub_metric, label in DIAGNOSTIC_METRICS:
        diag = raw_df[(raw_df["metric"] == metric) & (raw_df["sub_metric"] == sub_metric)][["city", "value"]]
        if not diag.empty:
            diag = diag.set_index("city").sort_values("value", ascending=False)
            print(f"\n  {label}:")
            for city, row in diag.iterrows():
                print(f"    {city:<15} {row['value']:.2f}")

    # Write JSON output
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
    print(f"\n  JSON saved to {json_path}")

    conn.close()


if __name__ == "__main__":
    run()
