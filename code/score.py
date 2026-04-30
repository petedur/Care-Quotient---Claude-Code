"""
Scoring: normalize raw metrics -> per-metric scores -> pillar groupings.

Reads from DuckDB (populated by etl.py) and writes scored results back into
the same database, plus a CSV and JSON summary to outputs/.

Normalization method: absolute benchmark normalization.
Each metric is scored against a theoretical ideal (score = value / benchmark * 100,
capped at 100). Benchmarks represent the level at which a city would be considered
to fully meet that dimension of care need. See methodology.md for full rationale.

Benchmarks:
  Pillar 1 — Social Fabric (40% of CQ)
    residential_stability    95%     — near-zero involuntary displacement
    housing_cost_burden      90%     — 90% not burdened (10% burdened ceiling)

  Pillar 2 — Institutions of Care (35% of CQ)
    combined_care (PEFK)     25/10k  — combined P+E+F+K nonprofit density
    fqhc_density             15/100k — eliminates HRSA shortage designation

  Pillar 3 — Reach (25% of CQ)
    health_insurance         95%     — near-universal coverage
    snap_coverage_rate       85%     — USDA FNS national participation target

Usage:
    python code/score.py
"""

import sys
import json
import pandas as pd
import duckdb
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from config import DB_PATH, PROJECT_ROOT, CITIES as CITY_CONFIG

OUTPUTS_DIR = PROJECT_ROOT / "outputs"
OUTPUTS_DIR.mkdir(exist_ok=True)

# ── Metric definitions ────────────────────────────────────────────────────────
# Each entry: (metric, sub_metric, pillar, benchmark, within_pillar_weight)
# benchmark: the raw value that earns a score of 100.
# Scores are computed as min(value / benchmark * 100, 100).
# "higher is better" is assumed for all metrics here.
# See methodology.md for full benchmark rationale and literature citations.

SCORED_METRICS = [
    # Pillar 1 — Social Fabric (40% of CQ)
    #   Residential stability:  65% — foundational precondition for network formation.
    #     Factor analysis confirms this as the dominant signal in its dimension (loading 0.70).
    #     Putnam (2000); Sampson et al. (1997).
    #   Housing cost burden:    35% — counter-weight; flags forced vs. chosen stability.
    #     Agha et al. (2024); Desmond & Bell. Raised from 12% after factor analysis showed
    #     it loads cleanly with stability as a distinct housing/stability dimension.
    ("residential_stability",     "pct_same_house",   "pillar1", 95.0, 0.65),
    ("housing_cost_burden",       "pct_not_burdened", "pillar1", 90.0, 0.35),

    # Pillar 2 — Institutions of Care (35% of CQ)
    #   Combined NP density (NTEE P+E+F+K): 50% — care nonprofit organizational density.
    #     Factor analysis showed NTEE P and NTEE E/F/K correlate at r=0.85 across 71 cities
    #     and load on the same factor — they measure one underlying dimension. Collapsed into
    #     a single metric. Benchmark: 25/10k combined — raised from 15/10k after 50%+ of
    #     cities hit the ceiling using county-based data. ZCTA-based filtering will reduce
    #     raw counts; 25/10k maintains meaningful discrimination for top performers.
    #   FQHC density: 50% — strongest evidence base; federal mandate; most directly serves
    #     vulnerable populations. Rosenbaum et al. (2011); Shi et al.
    ("nonprofit_density",         "combined_care",    "pillar2", 25.0, 0.50),
    ("health_center_density",     "density_per_100k", "pillar2", 15.0, 0.50),

    # Pillar 3 — Reach (25% of CQ)
    #   Health insurance:        65% — dominant signal in Reach dimension (factor loading 0.84).
    #     Whether people can access health systems when they need care.
    #   SNAP coverage rate:      35% — food assistance reach among likely-eligible households.
    #     Independent signal from health insurance (r=0.33); captures a different failure mode.
    ("health_insurance_coverage", "pct_insured",      "pillar3", 95.0, 0.65),
    ("snap_participation",        "coverage_rate",    "pillar3", 85.0, 0.35),
]

# Inter-pillar weights for the Care Quotient
# 40/35/25: Pillar 1 primary (care ethics, relational primacy — social fabric is the
# precondition for all other care); Pillar 2 institutional necessity (Nussbaum capabilities);
# Pillar 3 reach. Retained from V2; V4 will revisit after Medicaid/CHIP metric replacement.
PILLAR_WEIGHTS = {"pillar1": 0.40, "pillar2": 0.35, "pillar3": 0.25}

# Diagnostic metrics — collected and reported, not scored
DIAGNOSTIC_METRICS = [
    ("library_density",   "density_per_100k",  "Libraries per 100k residents"),
    ("library_density",   "visits_per_capita", "Library visits per capita"),
    # NP sub-components retained as diagnostics after collapsing into combined_care
    ("nonprofit_density", "social_support",    "Human services nonprofits per 10k (NTEE P)"),
    ("nonprofit_density", "care_institutions", "Health/MH/food nonprofits per 10k (NTEE E/F/K)"),
    ("nonprofit_density", "all_care",          "All care-related nonprofits per 10k (P+E+F+K+X3x)"),
    # Faith-based: X30 captures congregations, not specifically care orgs.
    ("nonprofit_density", "faith_based",       "Faith-based orgs per 10k (X3x, diagnostic only)"),
]

PILLAR_LABELS = {
    "pillar1": "Social Fabric",
    "pillar2": "Institutions of Care",
    "pillar3": "Reach",
}

# Human-readable metric labels for output
METRIC_LABELS = {
    "residential_stability.pct_same_house":        "Residential Stability",
    "housing_cost_burden.pct_not_burdened":        "Housing Affordability (% not cost-burdened)",
    "nonprofit_density.combined_care":             "Care Nonprofits (P+E+F+K per 10k)",
    "health_center_density.density_per_100k":      "FQHCs (per 100k)",
    "health_insurance_coverage.pct_insured":       "Health Insurance Coverage Rate",
    "snap_participation.coverage_rate":            "SNAP Coverage Rate",
    # Diagnostic only (not scored)
    "nonprofit_density.social_support":            "Human Services Nonprofits (NTEE P, per 10k)",
    "nonprofit_density.care_institutions":         "Health/MH/Food Nonprofits (NTEE E/F/K, per 10k)",
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
    for metric, sub_metric, pillar, benchmark, w in SCORED_METRICS:
        key = f"{metric}.{sub_metric}"
        if key not in wide.columns:
            print(f"  WARNING: missing metric '{key}' — skipping")
            continue
        col = f"score_{key}"
        results[col] = wide[key].apply(lambda v: normalize_to_benchmark(v, benchmark))

    # Weighted pillar scores
    for pillar in ["pillar1", "pillar2", "pillar3"]:
        pillar_metrics = [(m, s, w) for m, s, p, _, w in SCORED_METRICS if p == pillar]
        available = [(m, s, w) for m, s, w in pillar_metrics
                     if f"score_{m}.{s}" in results.columns]
        if not available:
            results[pillar] = float("nan")
            continue
        total_w = sum(w for _, _, w in available)
        results[pillar] = sum(
            results[f"score_{m}.{s}"] * (w / total_w)
            for m, s, w in available
        ).round(1)

    # Care Quotient — weighted average of pillar scores
    available_pillars = [(p, w) for p, w in PILLAR_WEIGHTS.items()
                         if p in results.columns]
    total_pw = sum(w for _, w in available_pillars)
    results["care_quotient"] = sum(
        results[p] * (w / total_pw) for p, w in available_pillars
    ).round(1)

    return results


def _drop_incomplete_cities(results: pd.DataFrame) -> pd.DataFrame:
    """
    Remove cities that are missing any required scored metric.

    When a collector fails, the city still appears in the DB (from a prior run)
    and score() silently reweights available metrics — producing a CQ from
    incomplete data. This function enforces fail-closed behavior: any city
    missing a required score column is excluded from all public outputs.

    Returns the filtered DataFrame and prints a warning for each dropped city.
    """
    required_cols = [f"score_{m}.{s}" for m, s, p, _, w in SCORED_METRICS]
    missing_cols  = [c for c in required_cols if c not in results.columns]

    if missing_cols:
        print(f"\n  WARNING: entire metric columns absent — {missing_cols}")
        print("  Run pipeline.py to collect missing data.")
        return results.iloc[0:0]  # empty — nothing is publishable

    # Per-city check: NaN in any required column = incomplete
    incomplete = results[required_cols].isnull().any(axis=1)
    if incomplete.any():
        bad = results.index[incomplete].tolist()
        print(f"\n  WARNING: {len(bad)} city/cities excluded from output — "
              f"missing required metrics: {bad}")
        print("  Re-run pipeline.py for these cities to restore them.")
        results = results[~incomplete].copy()

    return results


def write_results(conn, results: pd.DataFrame, raw_df: pd.DataFrame):
    """Save scored results to DuckDB, CSV, and JSON."""

    # Fail closed: exclude cities with any missing required scored metric
    results = _drop_incomplete_cities(results)

    conn.execute("DROP TABLE IF EXISTS scores")
    conn.register("results", results.reset_index())
    conn.execute("CREATE TABLE scores AS SELECT * FROM results")

    # ── Terminal summary ──────────────────────────────────────────────────────
    # CQ summary
    if "care_quotient" in results.columns:
        print("\n-- Care Quotient (CQ) --")
        cq_sorted = results["care_quotient"].sort_values(ascending=False)
        for city, cq in cq_sorted.items():
            print(f"  {city:<15} {cq:.1f}")

    print("\n-- Per-Metric Scores (0-100 vs. benchmark) --\n")

    pillar_groups = {}
    for metric, sub_metric, pillar, benchmark, w in SCORED_METRICS:
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
    score_cols = [f"score_{m}.{s}" for m, s, p, _, w in SCORED_METRICS
                  if f"score_{m}.{s}" in results.columns]
    cq_col = ["care_quotient", "pillar1", "pillar2", "pillar3"] + score_cols
    csv_out = results[[c for c in cq_col if c in results.columns]].copy()
    csv_out.index.name = "city"
    csv_out = csv_out.sort_values("care_quotient", ascending=False)
    rename = {"care_quotient": "Care Quotient", "pillar1": "Social Fabric",
               "pillar2": "Institutions of Care", "pillar3": "Reach"}
    rename.update({c: METRIC_LABELS.get(c.replace("score_", ""), c) for c in score_cols})
    csv_out.columns = [rename.get(c, c) for c in csv_out.columns]
    csv_path = OUTPUTS_DIR / "care_capacity_scores.csv"
    csv_out.to_csv(csv_path)
    print(f"  Scores saved to {csv_path}")

    # ── JSON ──────────────────────────────────────────────────────────────────
    output = {}
    for city in results.index:
        output[city] = {
            "pillar1_social_fabric":        results.loc[city, "pillar1"] if "pillar1" in results.columns else None,
            "pillar2_institutions_of_care": results.loc[city, "pillar2"] if "pillar2" in results.columns else None,
            "pillar3_reach":                results.loc[city, "pillar3"] if "pillar3" in results.columns else None,
            "metrics": {},
        }
        for metric, sub_metric, pillar, benchmark, w in SCORED_METRICS:
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
        output[city]["care_quotient"] = float(results.loc[city, "care_quotient"]) \
            if "care_quotient" in results.columns else None

    json_path = OUTPUTS_DIR / "care_capacity_scores.json"
    with open(json_path, "w") as f:
        json.dump(output, f, indent=2)
    print(f"  JSON saved to {json_path}")

    # ── Dashboard data.js ─────────────────────────────────────────────────────
    # Generates docs/data.js so the site always reflects the latest run.
    # The dashboard loads this file instead of hardcoding city data.
    write_dashboard_data(output, raw_df)


# ── Dashboard metric display config ──────────────────────────────────────────
# Maps internal metric keys to the display format expected by the dashboard JS.
DASHBOARD_METRICS = {
    # Pillar 1 — Social Fabric
    "residential_stability": {
        "key": "residential_stability",
        "raw_key": ("residential_stability", "pct_same_house"),
        "benchmark": "95%", "unit": "% same house 1+ yr",
        "fmt": lambda v: f"{v:.1f}%",
    },
    "housing_cost_burden": {
        "key": "housing_cost_burden",
        "raw_key": ("housing_cost_burden", "pct_not_burdened"),
        "benchmark": "90%", "unit": "% households not cost-burdened",
        "fmt": lambda v: f"{v:.1f}%",
    },
    # Pillar 2 — Institutions of Care
    "combined_care": {
        "key": "combined_care",
        "raw_key": ("nonprofit_density", "combined_care"),
        "benchmark": "25 / 10k", "unit": "care nonprofits (P+E+F+K) per 10k",
        "fmt": lambda v: f"{v:.2f}",
    },
    "fqhc": {
        "key": "fqhc",
        "raw_key": ("health_center_density", "density_per_100k"),
        "benchmark": "15 / 100k", "unit": "FQHCs per 100,000 residents",
        "fmt": lambda v: f"{v:.2f}",
    },
    # Pillar 3 — Reach
    "health_insurance": {
        "key": "health_insurance",
        "raw_key": ("health_insurance_coverage", "pct_insured"),
        "benchmark": "95%", "unit": "% population with health insurance",
        "fmt": lambda v: f"{v:.1f}%",
    },
    "snap_coverage": {
        "key": "snap_coverage",
        "raw_key": ("snap_participation", "coverage_rate"),
        "benchmark": "85%", "unit": "% SNAP coverage among likely-eligible households",
        "fmt": lambda v: f"{v:.1f}%",
    },
}

DASHBOARD_DIAGNOSTIC = {
    "libraries":   ("library_density",   "density_per_100k",  "libraries per 100k"),
    "lib_visits":  ("library_density",   "visits_per_capita", "library visits per capita"),
    "faith_based": ("nonprofit_density", "faith_based",       "faith-based orgs per 10k (X3x)"),
}

def _fmt_population(n: int) -> str:
    if n >= 1_000_000:
        return f"{n/1_000_000:.1f}M residents"
    if n >= 1_000:
        return f"{n/1_000:.0f}k residents"
    return f"{n} residents"


# City display metadata — built from cities.csv at import time so it
# automatically covers every city in the file, not just the original 5.
CITY_DISPLAY = {
    city_key: {
        "state":      cfg["state"],
        "population": _fmt_population(cfg["population"]),
    }
    for city_key, cfg in CITY_CONFIG.items()
}

# Score key mapping: dashboard metric key -> score.py results column name
SCORE_COL = {
    "residential_stability": "score_residential_stability.pct_same_house",
    "housing_cost_burden":   "score_housing_cost_burden.pct_not_burdened",
    "combined_care":         "score_nonprofit_density.combined_care",
    "fqhc":                  "score_health_center_density.density_per_100k",
    "health_insurance":      "score_health_insurance_coverage.pct_insured",
    "snap_coverage":         "score_snap_participation.coverage_rate",
}


def write_dashboard_data(score_output: dict, raw_df: pd.DataFrame):
    """
    Write docs/data.js from the current scored output.
    The dashboard loads this file so city data is never hardcoded in index.html.

    raw_df: the full metrics DataFrame already loaded from DuckDB (avoids
    opening a second connection while the main connection is still open).
    """
    dashboard_dir = PROJECT_ROOT / "docs"
    dashboard_dir.mkdir(exist_ok=True)

    cities_js = {}
    for city_key, city_scores in score_output.items():
        display = CITY_DISPLAY.get(city_key, {"state": "", "population": ""})
        cfg = CITY_CONFIG.get(city_key, {})

        metrics = {}
        for dash_key, meta in DASHBOARD_METRICS.items():
            label = METRIC_LABELS.get(
                f"{meta['raw_key'][0]}.{meta['raw_key'][1]}", dash_key
            )
            m = city_scores.get("metrics", {}).get(label, {})
            raw = m.get("raw_value", 0) or 0
            metrics[dash_key] = {
                "score": m.get("score", 0),
                "raw":   raw,
                "rawFmt": meta["fmt"](raw),
                "benchmark": meta["benchmark"],
                "unit": meta["unit"],
            }

        cities_js[city_key] = {
            "name":       cfg.get("name", city_key),
            "state":      display["state"],
            "population": display["population"],
            "cq":         city_scores.get("care_quotient", 0),
            "pillar1":    city_scores.get("pillar1_social_fabric", 0),
            "pillar2":    city_scores.get("pillar2_institutions_of_care", 0),
            "pillar3":    city_scores.get("pillar3_reach", 0),
            "metrics":    metrics,
            "diagnostic": {},  # filled below
        }

    for city_key in cities_js:
        diag = {}
        for dash_key, (metric, sub_metric, unit) in DASHBOARD_DIAGNOSTIC.items():
            rows = raw_df[
                (raw_df["city"] == city_key) &
                (raw_df["metric"] == metric) &
                (raw_df["sub_metric"] == sub_metric)
            ]["value"].values
            diag[dash_key] = {
                "value": f"{rows[0]:.2f}" if len(rows) else "n/a",
                "unit":  unit,
            }
        cities_js[city_key]["diagnostic"] = diag

    # Write data.js
    data_js_path = dashboard_dir / "data.js"
    js_content = (
        "// Auto-generated by score.py — do not edit manually.\n"
        "// Re-run `python code/score.py` (or `python code/pipeline.py`) to update.\n\n"
        f"const CITIES = {json.dumps(cities_js, indent=2)};\n"
    )
    with open(data_js_path, "w", encoding="utf-8") as f:
        f.write(js_content)
    print(f"  Dashboard data written to {data_js_path}")


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
