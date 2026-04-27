"""
Scoring: normalize raw metrics -> per-metric scores -> pillar groupings.

Reads from DuckDB (populated by etl.py) and writes scored results back into
the same database, plus a CSV and JSON summary to outputs/.

Normalization method: absolute benchmark normalization.
Each metric is scored against a theoretical ideal (score = value / benchmark * 100,
capped at 100). Benchmarks represent the level at which a city would be considered
to fully meet that dimension of care need. See methodology.md for full rationale.

Benchmarks:
  Pillar 1 — Social Support & Connection (40% of CQ)
    residential_stability    95%     — near-zero involuntary displacement
    social_support (NTEE P)  10/10k  — organizational saturation
    housing_cost_burden      75%     — 75% not burdened (25% burdened ceiling)

  Pillar 2 — Institutions of Care (35% of CQ)
    fqhc_density             15/100k — eliminates HRSA shortage designation
    care_institutions (EFK)  8/10k   — saturation of health/MH/food coverage

  Pillar 3 — Reach (25% of CQ)
    snap_coverage_rate       85%     — USDA FNS national participation target
    health_insurance         95%     — near-universal coverage

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
    # (metric, sub_metric, pillar, benchmark, within_pillar_weight)
    #
    # Within-pillar weights reflect the relative strength of evidence and
    # philosophical primacy of each metric within its pillar.
    #
    # Pillar 1 — Social Support & Connection (55% of CQ)
    #   Residential stability: 55% — foundational precondition for network formation.
    #     Putnam (2000) and Sampson et al. (1997) establish it as the primary
    #     structural driver of all other forms of social capital.
    #   Human services nonprofits: 45% — organized expression of civic caring.
    #
    # Pillar 2 — Institutions of Care (45% of CQ)
    #   FQHCs: 55% — strongest evidence base; federal mandate; most directly
    #     serves vulnerable populations. Rosenbaum et al. (2011); Shi et al.
    #   Health/MH/Food nonprofits: 45% — broader institutional coverage,
    #     noisier signal than FQHCs.
    #
    # Inter-pillar weights: 55% Social / 45% Institutional
    #   Care ethics tradition (Gilligan 1982, Noddings 1984) holds caring is
    #   fundamentally relational — the social fabric is primary. But Nussbaum's
    #   capabilities approach demands institutional infrastructure as a necessary
    #   condition. 55/45 honors both with a modest tilt toward the relational.
    #   Weights are judgment-based in V1; V2 will derive empirically via
    #   regression against care outcomes across 100 cities.

    # Pillar 1 — Social Support & Connection (40% of CQ)
    #   Residential stability:  48% — foundational precondition for network formation
    #   Human services nonprofits: 40% — organized expression of civic caring
    #   Housing cost burden:    12% — counter-weight; flags forced vs. chosen stability
    #     (Agha et al. 2024; Desmond & Bell — burden operates via stability, not independently)
    ("residential_stability",     "pct_same_house",    "pillar1", 95.0, 0.48),
    ("nonprofit_density",         "social_support",    "pillar1", 10.0, 0.40),
    ("housing_cost_burden",       "pct_not_burdened",  "pillar1", 85.0, 0.12),

    # Pillar 2 — Institutions of Care (35% of CQ) — unchanged
    ("health_center_density",     "density_per_100k",  "pillar2", 15.0, 0.55),
    ("nonprofit_density",         "care_institutions", "pillar2",  8.0, 0.45),

    # Pillar 3 — Reach (25% of CQ)
    #   SNAP coverage rate:      60% — food assistance reach among poverty households
    #   Health insurance:        40% — whether people can access health systems
    ("snap_participation",        "coverage_rate",     "pillar3", 85.0, 0.60),
    ("health_insurance_coverage", "pct_insured",       "pillar3", 95.0, 0.40),
]

# Inter-pillar weights for the Care Quotient
# 40/35/25: Pillar 1 primary (care ethics, relational primacy); Pillar 2 institutional
# necessity (Nussbaum capabilities); Pillar 3 most direct impact measure but lowest
# data maturity in V2 — weight will rise as methodology matures.
PILLAR_WEIGHTS = {"pillar1": 0.40, "pillar2": 0.35, "pillar3": 0.25}

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
    "pillar3": "Reach",
}

# Human-readable metric labels for output
METRIC_LABELS = {
    "residential_stability.pct_same_house":        "Residential Stability",
    "nonprofit_density.social_support":            "Human Services Nonprofits (per 10k)",
    "housing_cost_burden.pct_not_burdened":        "Housing Affordability (% not cost-burdened)",
    "health_center_density.density_per_100k":      "FQHCs (per 100k)",
    "nonprofit_density.care_institutions":         "Health/MH/Food Nonprofits (per 10k)",
    "snap_participation.coverage_rate":            "SNAP Coverage Rate",
    "health_insurance_coverage.pct_insured":       "Health Insurance Coverage Rate",
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
    for pillar in ["pillar1", "pillar2"]:
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


def write_results(conn, results: pd.DataFrame, raw_df: pd.DataFrame):
    """Save scored results to DuckDB, CSV, and JSON."""
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
    cq_col = ["care_quotient", "pillar1", "pillar2"] + score_cols
    csv_out = results[[c for c in cq_col if c in results.columns]].copy()
    csv_out.index.name = "city"
    csv_out = csv_out.sort_values("care_quotient", ascending=False)
    rename = {"care_quotient": "Care Quotient", "pillar1": "Social Support & Connection",
               "pillar2": "Institutions of Care"}
    rename.update({c: METRIC_LABELS.get(c.replace("score_", ""), c) for c in score_cols})
    csv_out.columns = [rename.get(c, c) for c in csv_out.columns]
    csv_path = OUTPUTS_DIR / "care_capacity_scores.csv"
    csv_out.to_csv(csv_path)
    print(f"  Scores saved to {csv_path}")

    # ── JSON ──────────────────────────────────────────────────────────────────
    output = {}
    for city in results.index:
        output[city] = {
            "pillar1_social_support":      results.loc[city, "pillar1"] if "pillar1" in results.columns else None,
            "pillar2_institutions_of_care": results.loc[city, "pillar2"] if "pillar2" in results.columns else None,
            "pillar3_reach":               results.loc[city, "pillar3"] if "pillar3" in results.columns else None,
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
    # Generates dashboard/data.js so the site always reflects the latest run.
    # The dashboard loads this file instead of hardcoding city data.
    write_dashboard_data(output, raw_df)


# ── Dashboard metric display config ──────────────────────────────────────────
# Maps internal metric keys to the display format expected by the dashboard JS.
DASHBOARD_METRICS = {
    # Pillar 1
    "residential_stability": {
        "key": "residential_stability",
        "raw_key": ("residential_stability", "pct_same_house"),
        "benchmark": "95%", "unit": "% same house 1+ yr",
        "fmt": lambda v: f"{v:.1f}%",
    },
    "social_support": {
        "key": "social_support",
        "raw_key": ("nonprofit_density", "social_support"),
        "benchmark": "10 / 10k", "unit": "human services nonprofits per 10k",
        "fmt": lambda v: f"{v:.2f}",
    },
    "housing_cost_burden": {
        "key": "housing_cost_burden",
        "raw_key": ("housing_cost_burden", "pct_not_burdened"),
        "benchmark": "85%", "unit": "% households not cost-burdened",
        "fmt": lambda v: f"{v:.1f}%",
    },
    # Pillar 2
    "fqhc": {
        "key": "fqhc",
        "raw_key": ("health_center_density", "density_per_100k"),
        "benchmark": "15 / 100k", "unit": "FQHCs per 100,000 residents",
        "fmt": lambda v: f"{v:.2f}",
    },
    "care_institutions": {
        "key": "care_institutions",
        "raw_key": ("nonprofit_density", "care_institutions"),
        "benchmark": "8 / 10k", "unit": "health/MH/food nonprofits per 10k",
        "fmt": lambda v: f"{v:.2f}",
    },
    # Pillar 3
    "snap_coverage": {
        "key": "snap_coverage",
        "raw_key": ("snap_participation", "coverage_rate"),
        "benchmark": "85%", "unit": "% SNAP coverage among poverty households",
        "fmt": lambda v: f"{v:.1f}%",
    },
    "health_insurance": {
        "key": "health_insurance",
        "raw_key": ("health_insurance_coverage", "pct_insured"),
        "benchmark": "95%", "unit": "% population with health insurance",
        "fmt": lambda v: f"{v:.1f}%",
    },
}

DASHBOARD_DIAGNOSTIC = {
    "libraries":   ("library_density",   "density_per_100k",  "libraries per 100k"),
    "lib_visits":  ("library_density",   "visits_per_capita", "library visits per capita"),
    "faith_based": ("nonprofit_density", "faith_based",       "faith-based orgs per 10k (X3x)"),
}

# City display metadata (population string, etc.) not stored in DuckDB
CITY_DISPLAY = {
    "nyc":         {"state": "NY", "population": "8.3M residents"},
    "chicago":     {"state": "IL", "population": "2.7M residents"},
    "los_angeles": {"state": "CA", "population": "3.9M residents"},
    "houston":     {"state": "TX", "population": "2.3M residents"},
    "boston":      {"state": "MA", "population": "676k residents"},
}

# Score key mapping: dashboard metric key -> score.py results column name
SCORE_COL = {
    "residential_stability": "score_residential_stability.pct_same_house",
    "social_support":        "score_nonprofit_density.social_support",
    "housing_cost_burden":   "score_housing_cost_burden.pct_not_burdened",
    "fqhc":                  "score_health_center_density.density_per_100k",
    "care_institutions":     "score_nonprofit_density.care_institutions",
    "snap_coverage":         "score_snap_participation.coverage_rate",
    "health_insurance":      "score_health_insurance_coverage.pct_insured",
}


def write_dashboard_data(score_output: dict, raw_df: pd.DataFrame):
    """
    Write dashboard/data.js from the current scored output.
    The dashboard loads this file so city data is never hardcoded in index.html.

    raw_df: the full metrics DataFrame already loaded from DuckDB (avoids
    opening a second connection while the main connection is still open).
    """
    dashboard_dir = PROJECT_ROOT / "dashboard"
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
            "pillar1":    city_scores.get("pillar1_social_support", 0),
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
