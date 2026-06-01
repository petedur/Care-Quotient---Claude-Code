"""
Scoring: normalize raw metrics -> per-metric scores -> pillar groupings.

Reads from DuckDB (populated by etl.py) and writes scored results back into
the same database, plus a CSV and JSON summary to outputs/.

Normalization method: absolute benchmark normalization.
Each metric is scored against a theoretical ideal (score = value / benchmark * 100,
capped at 100). Benchmarks represent the level at which a city would be considered
to fully meet that dimension of care need. See methodology.md for full rationale.

Pillar structure grounded in Tronto (1993) phases of care and Putnam/Sampson
social capital and collective efficacy research. See methodology.md §3 and the
"What is Care?" theory page for full theoretical grounding.

Benchmarks:
  Pillar 1 — Social & Relational Care (40% of CQ)
    residential_stability    95%     — near-zero involuntary displacement
    combined_care (PEFK)     25/10k  — combined P+E+F+K nonprofit density
    library_density          5/100k  — P90 across 69 cities; aspirational standard

  Pillar 2 — Institutional Care (35% of CQ)
    fqhc_density             15/100k — eliminates HRSA shortage designation
    nursing_home_capacity    50/1k65 — 5% of 65+ pop in skilled nursing (literature-based)
    child_care_capacity      15/1k_under5 — CCDBG access standard (licensed care for 50% of eligible)

  Pillar 3 — Economic Access to Care (25% of CQ)
    health_insurance         100%    — Medicaid/CHIP coverage rate (C27007; score = raw rate directly)
    housing_cost_burden      90%     — 90% not burdened (10% burdened ceiling)
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
    # Pillar 1 — Social & Relational Care (40% of CQ)
    #   Tronto (1993): attentiveness + responsibility phases; social fabric is the precondition
    #   for all other care — you cannot have institutional care without social acknowledgment
    #   of need. Putnam (2000) bridging capital; Sampson et al. (1997) collective efficacy.
    #
    #   Residential stability:  50% — foundational precondition for relational network
    #     formation. Factor analysis loading 0.70. Putnam (2000); Sampson et al. (1997).
    #   Nonprofit density:      40% — organized community care response (Tronto: competence).
    #     NTEE P+E+F+K. Factor analysis showed r=0.85 across 71 cities; single dimension.
    #   Library density:         5% — public community infrastructure and de facto distress
    #     absorption site. Explicitly mentioned by mentor as an institution of care.
    #   Religious density:       5% — faith institutions as community anchors (all denominations).
    #     ARDA 2020 Religion Census; county-level congregation counts. Low weight reflects
    #     difficulty quantifying care content; presence counted as community anchor (like libraries).
    ("residential_stability",     "pct_same_house",         "pillar1", 95.0, 0.50),
    ("nonprofit_density",         "combined_care",          "pillar1", 25.0, 0.40),
    ("library_density",           "density_per_100k",       "pillar1",  5.0, 0.05),
    ("religious_density",         "congregations_per_100k", "pillar1",150.0, 0.05),

    # Pillar 2 — Institutional Care (35% of CQ)
    #   Tronto (1993): competence phase — does the city have infrastructure to absorb
    #   distress at scale when informal networks are insufficient? Nussbaum capabilities:
    #   bodily health and affiliation require formal institutional backup.
    #
    #   FQHC density:           45% — strongest evidence base; federal safety-net mandate;
    #     most directly serves vulnerable populations regardless of ability to pay.
    #     Rosenbaum et al. (2011); Shi et al.
    #   Nursing home capacity:  35% — certified beds per 1k residents 65+. Benchmark: 50/1k
    #     = 5% of elderly in skilled nursing care (literature-based adequacy threshold).
    #   Child care capacity:    20% — licensed establishments per 1k children under 5.
    #     Benchmark: 15/1k = CCDBG access standard (~50% of income-eligible children covered
    #     in licensed settings). Census CBP NAICS 624410; ACS B01001 under-5 pop denominator.
    ("health_center_density",     "density_per_100k",           "pillar2", 15.0, 0.45),
    ("nursing_home_capacity",     "beds_per_1k_65plus",         "pillar2", 50.0, 0.35),
    ("child_care_capacity",       "establishments_per_1k_under5", "pillar2", 15.0, 0.20),

    # Pillar 3 — Economic Access to Care (25% of CQ)
    #   Enabling conditions — whether care infrastructure can actually reach those who need it.
    #   Folbre (2001) political economy of care; Sen (1999) capability approach: resources
    #   are necessary but not sufficient; access barriers determine whether care lands.
    #
    #   Healthcare coverage:    40% — Medicaid/CHIP reach (C27007; coverage rate vs eligible pop).
    #     Whether vulnerable residents can access formal care systems.
    #   Housing cost burden:    35% — economic conditions that enable or prevent care.
    #     Desmond & Bell; Agha et al. (2024). Moved from Pillar 1 (V4) — belongs in access.
    #   SNAP coverage:          25% — food security reach; narrower scope than other metrics.
    #     Independent signal (r=0.33 with healthcare coverage).
    ("health_insurance_coverage", "coverage_rate",        "pillar3", 100.0, 0.40),
    ("housing_cost_burden",       "pct_not_burdened",    "pillar3", 90.0, 0.35),
    ("snap_participation",        "coverage_rate",       "pillar3", 85.0, 0.25),
]

# Inter-pillar weights for the Care Quotient
# 40/35/25: Pillar 1 primary — relational infrastructure is theoretically prior to
# institutional and access dimensions (Tronto: attentiveness and responsibility precede
# competence; Putnam/Sampson: social fabric is the precondition for all other care).
# Pillar 2 institutional necessity (Nussbaum capabilities). Pillar 3 enabling conditions.
PILLAR_WEIGHTS = {"pillar1": 0.40, "pillar2": 0.35, "pillar3": 0.25}

# Diagnostic metrics — collected and reported, not scored
DIAGNOSTIC_METRICS = [
    # library_density.density_per_100k is now a scored metric (Pillar 1)
    ("library_density",   "visits_per_capita", "Library visits per capita"),
    # NP sub-components retained as diagnostics after collapsing into combined_care
    ("nonprofit_density", "social_support",    "Human services nonprofits per 10k (NTEE P)"),
    ("nonprofit_density", "care_institutions", "Health/MH/food nonprofits per 10k (NTEE E/F/K)"),
    ("nonprofit_density", "all_care",          "All care-related nonprofits per 10k (P+E+F+K+X3x)"),
    # Faith-based: X30 codes capture only formally-registered faith social service orgs.
    # Understates true faith-based care (many congregations file under X20/X21/X22).
    # Retained as diagnostic; not scored due to data quality. See methodology §3.3.
    ("nonprofit_density", "faith_based",       "Faith-based orgs per 10k (X3x, diagnostic only)"),
    # Need-adjusted shadow metric: combined care NPs per 10k residents at 0-150% FPL.
    # Allows comparison between total-pop and need-adjusted framings (see methodology §3.3).
    ("nonprofit_density", "combined_care_per_10k_distressed",
     "Care nonprofits per 10k residents at 0–150% FPL (need-adjusted)"),
]

PILLAR_LABELS = {
    "pillar1": "Social & Relational Care",
    "pillar2": "Institutional Care",
    "pillar3": "Economic Access to Care",
}

# Human-readable metric labels for output
METRIC_LABELS = {
    "residential_stability.pct_same_house":        "Residential Stability",
    "nonprofit_density.combined_care":             "Care Nonprofits (P+E+F+K per 10k)",
    "library_density.density_per_100k":            "Library Density (per 100k residents)",
    "religious_density.congregations_per_100k":    "Religious Institution Density (congregations/100k)",
    "health_center_density.density_per_100k":      "FQHCs (per 100k)",
    "nursing_home_capacity.beds_per_1k_65plus":    "Nursing Home Capacity (beds/1k 65+)",
    "child_care_capacity.establishments_per_1k_under5": "Child Care Capacity (establishments/1k under-5)",
    "health_insurance_coverage.coverage_rate":       "Healthcare Coverage Rate",
    "housing_cost_burden.pct_not_burdened":        "Housing Affordability (% not cost-burdened)",
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
    df = df.copy()
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


# (metric, sub_metric, trend_json_key)
_TREND_METRICS = [
    ("residential_stability",     "pct_same_house",  "residential_stability"),
    ("housing_cost_burden",       "pct_not_burdened", "housing_cost_burden"),
    ("snap_participation",        "coverage_rate",    "snap_participation"),
    ("health_insurance_coverage", "coverage_rate",    "health_insurance_coverage"),
]


def compute_trends(results: pd.DataFrame, raw_df: pd.DataFrame) -> dict:
    """
    For each city that has trend_2020/trend_metrics.json, compute per-metric
    deltas between ACS 2020 and ACS 2022 for the four trendable metrics.

    Falls back to outputs/trend.json if raw per-city files are absent (e.g.
    in CI, where data/raw/ is not committed).

    Returns {city_key: {metric_key: {"prior": float, "current": float, "delta": float}}}
    """
    # Fast path: pre-computed trend.json present and raw files absent
    cached_path = OUTPUTS_DIR / "trend.json"
    raw_trend_present = any(
        (PROJECT_ROOT / "data" / "raw" / city_key / "trend_2020" / "trend_metrics.json").exists()
        for city_key in results.index
    )
    if not raw_trend_present and cached_path.exists():
        try:
            cached = json.loads(cached_path.read_text())
            print("  Using cached outputs/trend.json (raw trend files not present)")
            return cached
        except Exception:
            pass

    trend_data = {}
    for city_key in results.index:
        trend_file = PROJECT_ROOT / "data" / "raw" / city_key / "trend_2020" / "trend_metrics.json"
        if not trend_file.exists():
            continue
        try:
            prior_acs = json.loads(trend_file.read_text())
        except Exception:
            continue

        city_trend = {}
        for metric, sub_metric, trend_key in _TREND_METRICS:
            prior = prior_acs.get(trend_key)
            current_rows = raw_df[
                (raw_df["city"] == city_key) &
                (raw_df["metric"] == metric) &
                (raw_df["sub_metric"] == sub_metric)
            ]["value"].values
            current = float(current_rows[0]) if len(current_rows) else None
            if prior is not None and current is not None:
                city_trend[trend_key] = {
                    "prior":   round(prior, 1),
                    "current": round(current, 1),
                    "delta":   round(current - prior, 1),
                }

        if city_trend:
            trend_data[city_key] = city_trend

    return trend_data


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
    rename = {"care_quotient": "Care Quotient", "pillar1": "Social & Relational Care",
               "pillar2": "Institutional Care", "pillar3": "Economic Access to Care"}
    rename.update({c: METRIC_LABELS.get(c.replace("score_", ""), c) for c in score_cols})
    csv_out.columns = [rename.get(c, c) for c in csv_out.columns]
    csv_path = OUTPUTS_DIR / "care_capacity_scores.csv"
    csv_out.to_csv(csv_path)
    print(f"  Scores saved to {csv_path}")

    # ── JSON ──────────────────────────────────────────────────────────────────
    output = {}
    for city in results.index:
        output[city] = {
            "pillar1_social_relational_care":  results.loc[city, "pillar1"] if "pillar1" in results.columns else None,
            "pillar2_institutional_care":      results.loc[city, "pillar2"] if "pillar2" in results.columns else None,
            "pillar3_economic_access":         results.loc[city, "pillar3"] if "pillar3" in results.columns else None,
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

    # ── Trend deltas ──────────────────────────────────────────────────────────
    print("\nComputing CQ trends (ACS 2020 vs 2022)...")
    trend_data = compute_trends(results, raw_df)
    if trend_data:
        print(f"  Trend data available for {len(trend_data)} cities")
        trend_path = OUTPUTS_DIR / "trend.json"
        with open(trend_path, "w") as f:
            json.dump(trend_data, f, indent=2)
        print(f"  Trend data written to {trend_path}")
    else:
        print("  No trend data found — run code/collectors/acs_trend.py first")

    # ── Dashboard data.js ─────────────────────────────────────────────────────
    # Generates docs/data.js so the site always reflects the latest run.
    # The dashboard loads this file instead of hardcoding city data.
    write_dashboard_data(output, raw_df, trend_data)


# ── Dashboard metric display config ──────────────────────────────────────────
# Maps internal metric keys to the display format expected by the dashboard JS.
DASHBOARD_METRICS = {
    # Pillar 1 — Social & Relational Care
    "residential_stability": {
        "key": "residential_stability",
        "raw_key": ("residential_stability", "pct_same_house"),
        "benchmark": "95%", "unit": "% same house 1+ yr",
        "fmt": lambda v: f"{v:.1f}%",
    },
    "combined_care": {
        "key": "combined_care",
        "raw_key": ("nonprofit_density", "combined_care"),
        "benchmark": "25 / 10k", "unit": "care nonprofits (P+E+F+K) per 10k",
        "fmt": lambda v: f"{v:.2f}",
    },
    "library_density": {
        "key": "library_density",
        "raw_key": ("library_density", "density_per_100k"),
        "benchmark": "5 / 100k", "unit": "public libraries per 100,000 residents",
        "fmt": lambda v: f"{v:.2f}",
    },
    "religious_density": {
        "key": "religious_density",
        "raw_key": ("religious_density", "congregations_per_100k"),
        "benchmark": "150 / 100k", "unit": "congregations per 100,000 residents (all denominations, ARDA 2020)",
        "fmt": lambda v: f"{v:.1f}",
    },
    # Pillar 2 — Institutional Care
    "fqhc": {
        "key": "fqhc",
        "raw_key": ("health_center_density", "density_per_100k"),
        "benchmark": "15 / 100k", "unit": "FQHCs per 100,000 residents",
        "fmt": lambda v: f"{v:.2f}",
    },
    "nursing_home": {
        "key": "nursing_home",
        "raw_key": ("nursing_home_capacity", "beds_per_1k_65plus"),
        "benchmark": "50 / 1k 65+", "unit": "certified beds per 1,000 residents 65+",
        "fmt": lambda v: f"{v:.1f}",
    },
    "child_care": {
        "key": "child_care",
        "raw_key": ("child_care_capacity", "establishments_per_1k_under5"),
        "benchmark": "15 / 1k under-5", "unit": "licensed child care establishments per 1,000 children under 5",
        "fmt": lambda v: f"{v:.2f}",
    },
    # Pillar 3 — Economic Access to Care
    "health_insurance": {
        "key": "health_insurance",
        "raw_key": ("health_insurance_coverage", "coverage_rate"),
        "benchmark": "100%", "unit": "Medicaid/CHIP enrollment rate among income-eligible residents",
        "fmt": lambda v: f"{v:.1f}%",
    },
    "housing_cost_burden": {
        "key": "housing_cost_burden",
        "raw_key": ("housing_cost_burden", "pct_not_burdened"),
        "benchmark": "90%", "unit": "% households not cost-burdened",
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
    # library_density.density_per_100k promoted to scored metric (Pillar 1)
    "lib_visits":       ("library_density",   "visits_per_capita", "library visits per capita"),
    "faith_based":      ("nonprofit_density", "faith_based",       "faith-based orgs per 10k (X3x)"),
    "care_distressed":  ("nonprofit_density", "combined_care_per_10k_distressed",
                         "care nonprofits per 10k residents 0–150% FPL"),
    # CDC PLACES community wellbeing diagnostics (not scored — outcome measures)
    "mental_distress":  ("places_diagnostics", "pct_frequent_mental_distress",
                         "% adults with frequent mental distress (CDC PLACES)"),
    "poor_health":      ("places_diagnostics", "pct_fair_or_poor_health",
                         "% adults with fair or poor self-rated health (CDC PLACES)"),
    "depression":       ("places_diagnostics", "pct_depression",
                         "% adults with diagnosed depression (CDC PLACES)"),
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
    "combined_care":         "score_nonprofit_density.combined_care",
    "library_density":       "score_library_density.density_per_100k",
    "religious_density":     "score_religious_density.congregations_per_100k",
    "fqhc":                  "score_health_center_density.density_per_100k",
    "nursing_home":          "score_nursing_home_capacity.beds_per_1k_65plus",
    "child_care":            "score_child_care_capacity.establishments_per_1k_under5",
    "health_insurance":      "score_health_insurance_coverage.coverage_rate",
    "housing_cost_burden":   "score_housing_cost_burden.pct_not_burdened",
    "snap_coverage":         "score_snap_participation.coverage_rate",
}


def write_dashboard_data(score_output: dict, raw_df: pd.DataFrame,
                         trend_data: dict | None = None):
    """
    Write docs/data.js from the current scored output.
    The dashboard loads this file so city data is never hardcoded in index.html.

    raw_df: the full metrics DataFrame already loaded from DuckDB (avoids
    opening a second connection while the main connection is still open).
    trend_data: optional {city_key: {cq_prior, delta, direction}} from compute_trends().
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
            "lat":        cfg.get("lat"),
            "lng":        cfg.get("lng"),
            "cq":         city_scores.get("care_quotient", 0),
            "pillar1":    city_scores.get("pillar1_social_relational_care", 0),
            "pillar2":    city_scores.get("pillar2_institutional_care", 0),
            "pillar3":    city_scores.get("pillar3_economic_access", 0),
            "metrics":    metrics,
            "diagnostic": {},  # filled below
            "trend":      (trend_data or {}).get(city_key, {}),
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
