"""
Scoring: normalize raw metrics -> per-metric scores -> pillar groupings.

Reads from DuckDB (populated by etl.py) and writes scored results back into
the same database, plus a CSV and JSON summary to outputs/.

Normalization method: absolute benchmark normalization.
Each metric is scored against a theoretical ideal (score = value / benchmark * 100,
capped at 100). Benchmarks represent the level at which a city would be considered
to fully meet that dimension of care need. See methodology.md for full rationale.

Benchmarks:
  residential_stability   95%      — near-zero involuntary displacement
  social_support (NTEE P) 10/10k   — organizational saturation across all human service sub-categories
  fqhc_density            15/100k  — eliminates HRSA shortage designation + geographic redundancy
  care_institutions (EFK) 8/10k    — saturation of health, mental health, and food org coverage

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
# Each entry: (metric, sub_metric, pillar, benchmark)
# benchmark: the raw value that earns a score of 100.
# Scores are computed as min(value / benchmark * 100, 100).
# "higher is better" is assumed for all metrics here.
#
# ── Scored metrics with literature-based benchmarks ──────────────────────────
#
# Pillar 1: Social Support & Connection
#
#   Residential stability — benchmark 95%
#   95% represents near-zero involuntary displacement: ~5% annual mobility
#   accounts for natural/voluntary movement (employment, life transitions).
#   Stable, low-poverty US neighborhoods regularly achieve 93-95% in ACS data.
#   Putnam (2000) and Sampson et al. (1997) establish stability as the primary
#   structural driver of collective efficacy and care network formation.
#
#   Human services nonprofit density (NTEE P) — benchmark 10 per 10,000
#   1 organization per 1,000 residents — a density at which every major
#   sub-category of human services (housing, food, youth, elderly, disability,
#   immigrant services) would be covered with meaningful redundancy.
#   Judgment threshold; no policy standard exists. Documented as such.
#   Salamon & Anheier (1998); Boris & Steuerle (2006).
#
# Pillar 2: Institutions of Care
#
#   FQHC density — benchmark 15 per 100,000
#   Derived from HRSA Health Professional Shortage Area (HPSA) criteria:
#   shortage designation requires population:physician ratio > 3,500:1.
#   HRSA UDS data shows average FQHC site capacity at ~3,500-5,000 patients/yr
#   with 2-3 FTE physicians/site. Eliminating shortage designation requires
#   ~9.5-14 FQHCs per 100k. Benchmark set at 15 to add geographic redundancy
#   within large cities. Rosenbaum et al. (2011); Shi et al. (multiple years).
#
#   Health/mental health/food nonprofit density (NTEE E/F/K) — benchmark 8/10k
#   Slightly lower than NTEE P because E/F/K orgs operate at larger scale
#   (hospital systems, regional food banks) — fewer orgs needed per capita for
#   coverage saturation. Judgment threshold; documented as such.
#   Kim & Jennings (2012); Pettijohn & Boris (2013).
#
#   Faith-based (NTEE X3x) — DIAGNOSTIC ONLY (not scored in V1)
#   IRS X30 is a catch-all that captures congregations alongside human-service
#   orgs, making it an unreliable scored metric. V2 will explore combining X3x
#   with faith-affiliated P/E/K registrations. See methodology.md.

SCORED_METRICS = [
    # (metric, sub_metric, pillar, benchmark)
    # Pillar 1 — Social Support & Connection
    ("residential_stability", "pct_same_house",    "pillar1", 95.0),
    ("nonprofit_density",     "social_support",    "pillar1", 10.0),

    # Pillar 2 — Institutions of Care
    ("health_center_density", "density_per_100k",  "pillar2", 15.0),
    ("nonprofit_density",     "care_institutions", "pillar2",  8.0),
]

# Diagnostic metrics — collected and reported, not scored
DIAGNOSTIC_METRICS = [
    ("library_density",   "density_per_100k",  "Libraries per 100k residents"),
    ("library_density",   "visits_per_capita", "Library visits per capita"),
    ("nonprofit_density", "all_care",          "All care-related nonprofits per 10k (diagnostic)"),
    # Faith-based: X30 captures congregations, not specifically care orgs.
    ("nonprofit_density", "faith_based",       "Faith-based orgs per 10k (X3x, diagnostic only)"),
]

PILLAR_LABELS = {
    "pillar1": "Social Support & Connection",
    "pillar2": "Institutions of Care",
}

# Human-readable metric labels for output
METRIC_LABELS = {
    "residential_stability.pct_same_house":    "Residential Stability",
    "nonprofit_density.social_support":        "Human Services Nonprofits (per 10k)",
    "health_center_density.density_per_100k":  "FQHCs (per 100k)",
    "nonprofit_density.care_institutions":     "Health/MH/Food Nonprofits (per 10k)",
}


def load_metrics(conn) -> pd.DataFrame:
    return conn.execute(
        "SELECT city, metric, sub_metric, value FROM metrics WHERE value IS NOT NULL"
    ).fetchdf()


def normalize_to_benchmark(value: float, benchmark: float) -> float:
    """Score a raw value against its absolute benchmark. Capped at 100."""
    return min(round(value / benchmark * 100, 1), 100.0)


def score(df: pd.DataFrame) -> pd.DataFrame:
    """
    Returns a DataFrame with one column per scored metric (normalized 0-100),
    plus pillar average columns for grouping context.
    """
    df["key"] = df["metric"] + "." + df["sub_metric"]
    wide = df.pivot(index="city", columns="key", values="value")

    results = pd.DataFrame(index=wide.index)

    # Score each metric against its absolute benchmark
    for metric, sub_metric, pillar, benchmark in SCORED_METRICS:
        key = f"{metric}.{sub_metric}"
        if key not in wide.columns:
            print(f"  WARNING: missing metric '{key}' — skipping")
            continue
        col = f"score_{key}"
        results[col] = wide[key].apply(lambda v: normalize_to_benchmark(v, benchmark))

    # Pillar averages (simple mean of constituent metric scores — for context only)
    for pillar in ["pillar1", "pillar2"]:
        pillar_cols = [
            f"score_{m}.{s}"
            for m, s, p, _ in SCORED_METRICS
            if p == pillar and f"score_{m}.{s}" in results.columns
        ]
        if pillar_cols:
            results[pillar] = results[pillar_cols].mean(axis=1).round(1)

    return results


def write_results(conn, results: pd.DataFrame, raw_df: pd.DataFrame):
    """Save scored results to DuckDB, CSV, and JSON."""
    conn.execute("DROP TABLE IF EXISTS scores")
    conn.register("results", results.reset_index())
    conn.execute("CREATE TABLE scores AS SELECT * FROM results")

    # ── Terminal summary ──────────────────────────────────────────────────────
    print("\n-- Care Capacity Index: Per-Metric Scores (0-100 vs. benchmark) --\n")

    pillar_groups = {}
    for metric, sub_metric, pillar, benchmark in SCORED_METRICS:
        pillar_groups.setdefault(pillar, []).append((metric, sub_metric, benchmark))

    for pillar, metrics in pillar_groups.items():
        print(f"  {PILLAR_LABELS[pillar]}")
        for metric, sub_metric, benchmark in metrics:
            key = f"score_{metric}.{sub_metric}"
            label = METRIC_LABELS.get(f"{metric}.{sub_metric}", f"{metric}.{sub_metric}")
            if key not in results.columns:
                continue
            col = results[key].sort_values(ascending=False)
            print(f"    {label} (benchmark: {benchmark})")
            for city, val in col.items():
                raw_val = raw_df[
                    (raw_df["metric"] == metric) & (raw_df["sub_metric"] == sub_metric)
                    & (raw_df["city"] == city)
                ]["value"].values
                raw_str = f"{raw_val[0]:.2f}" if len(raw_val) else "n/a"
                print(f"      {city:<15} {val:>5.1f}  (raw: {raw_str})")
        print()

    # ── CSV ───────────────────────────────────────────────────────────────────
    score_cols = [f"score_{m}.{s}" for m, s, p, _ in SCORED_METRICS
                  if f"score_{m}.{s}" in results.columns]
    csv_out = results[score_cols].copy()
    csv_out.index.name = "city"
    csv_out.columns = [METRIC_LABELS.get(c.replace("score_", ""), c) for c in csv_out.columns]
    csv_path = OUTPUTS_DIR / "care_capacity_scores.csv"
    csv_out.to_csv(csv_path)
    print(f"  Scores saved to {csv_path}")

    # ── JSON ──────────────────────────────────────────────────────────────────
    output = {}
    for city in results.index:
        output[city] = {
            "pillar1_social_support": results.loc[city, "pillar1"] if "pillar1" in results.columns else None,
            "pillar2_institutions_of_care": results.loc[city, "pillar2"] if "pillar2" in results.columns else None,
            "metrics": {},
        }
        for metric, sub_metric, pillar, benchmark in SCORED_METRICS:
            key = f"score_{metric}.{sub_metric}"
            label = METRIC_LABELS.get(f"{metric}.{sub_metric}", f"{metric}.{sub_metric}")
            raw_val = raw_df[
                (raw_df["metric"] == metric) & (raw_df["sub_metric"] == sub_metric)
                & (raw_df["city"] == city)
            ]["value"].values
            output[city]["metrics"][label] = {
                "score": results.loc[city, key] if key in results.columns else None,
                "raw_value": round(float(raw_val[0]), 2) if len(raw_val) else None,
                "benchmark": benchmark,
                "pillar": PILLAR_LABELS[pillar],
            }

    json_path = OUTPUTS_DIR / "care_capacity_scores.json"
    with open(json_path, "w") as f:
        json.dump(output, f, indent=2)
    print(f"  JSON saved to {json_path}")


def run():
    conn = duckdb.connect(str(DB_PATH))

    print("Loading metrics from DuckDB...")
    df = load_metrics(conn)

    cities_with_data = df["city"].unique()
    print(f"Cities with data: {list(cities_with_data)}")

    print("\nScoring against absolute benchmarks...")
    results = score(df)

    write_results(conn, results, df)

    # ── Diagnostic metrics ────────────────────────────────────────────────────
    print("\n-- Diagnostic Metrics (not scored) --")
    for metric, sub_metric, label in DIAGNOSTIC_METRICS:
        diag = df[(df["metric"] == metric) & (df["sub_metric"] == sub_metric)][["city", "value"]]
        if not diag.empty:
            diag = diag.set_index("city").sort_values("value", ascending=False)
            print(f"\n  {label}:")
            for city, row in diag.iterrows():
                print(f"    {city:<15} {row['value']:.2f}")

    conn.close()


if __name__ == "__main__":
    run()
