"""
Factor Analysis — Care Capacity Index
======================================
Tests whether the assumed 3-pillar structure holds empirically by running PCA
on the scored metrics across all cities with complete data.

Metric definitions are imported directly from score.py so this script can
never drift out of sync with the scoring model.

Outputs
-------
  1. Correlation matrix of raw metric scores
  2. Scree plot data (variance explained per principal component)
  3. Varimax-rotated factor loadings (3-factor solution)
  4. Proposed empirical weights vs. current V3 weights
  5. outputs/factor_analysis_loadings.csv  — loadings table
  6. outputs/factor_analysis_correlations.csv — correlation matrix
  7. outputs/factor_analysis_weights.json  — proposed weights (review before adopting)

Usage
-----
    python code/analysis/factor_analysis.py

Dependencies (in addition to existing requirements):
    pip install scikit-learn scipy
    (Both are pinned in requirements.txt — scikit-learn==1.8.0, scipy==1.17.1)
"""

import sys
import json

# Ensure UTF-8 output on Windows (box-drawing characters used in report)
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
import numpy as np
import pandas as pd
import duckdb
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from config import DB_PATH, PROJECT_ROOT

# ── Import metric definitions directly from score.py ─────────────────────────
# This is the single source of truth. factor_analysis.py never re-declares
# SCORED_METRICS or PILLAR_WEIGHTS — it reads them from the live scoring model.
from score import SCORED_METRICS, PILLAR_WEIGHTS, PILLAR_LABELS

try:
    from sklearn.decomposition import PCA
    from sklearn.preprocessing import StandardScaler
    from scipy.stats import spearmanr
except ImportError:
    print("ERROR: factor_analysis.py requires scikit-learn and scipy.")
    print("Install with:  pip install scikit-learn scipy")
    sys.exit(1)

OUTPUTS_DIR = PROJECT_ROOT / "outputs"
OUTPUTS_DIR.mkdir(exist_ok=True)

# Build derived lookup structures from the imported SCORED_METRICS
SHORT_LABELS = {
    f"{metric}.{sub_metric}": f"{metric.replace('_', ' ').title()} / {sub_metric}"
    for metric, sub_metric, pillar, benchmark, weight in SCORED_METRICS
}
# Override with concise display names
_DISPLAY = {
    "residential_stability.pct_same_house":       "Resid. Stability",
    "housing_cost_burden.pct_not_burdened":       "Housing Affordability",
    "nonprofit_density.combined_care":            "Combined Care NPs",
    "health_center_density.density_per_100k":     "FQHC Density",
    "snap_participation.coverage_rate":           "SNAP Coverage",
    "health_insurance_coverage.pct_insured":      "Health Insurance",
}
SHORT_LABELS.update(_DISPLAY)

PILLAR_MEMBERSHIP = {
    SHORT_LABELS[f"{m}.{s}"]: p
    for m, s, p, _, _ in SCORED_METRICS
}


# ── Varimax rotation ──────────────────────────────────────────────────────────
def varimax(loadings: np.ndarray, tol: float = 1e-6, max_iter: int = 1000) -> np.ndarray:
    """Apply varimax rotation to a (n_variables × n_factors) loading matrix."""
    n_vars, n_factors = loadings.shape
    rotation = np.eye(n_factors)

    for _ in range(max_iter):
        old_rotation = rotation.copy()
        for i in range(n_factors):
            for j in range(i + 1, n_factors):
                x = loadings @ rotation
                u = x[:, i] ** 2 - x[:, j] ** 2
                v = 2 * x[:, i] * x[:, j]
                A = np.sum(u)
                B = np.sum(v)
                C = np.sum(u ** 2 - v ** 2)
                D = 2 * np.sum(u * v)
                num = D - 2 * A * B / n_vars
                den = C - (A ** 2 - B ** 2) / n_vars
                angle = 0.25 * np.arctan2(num, den)
                rot = np.eye(n_factors)
                rot[i, i] = np.cos(angle)
                rot[j, j] = np.cos(angle)
                rot[i, j] = -np.sin(angle)
                rot[j, i] = np.sin(angle)
                rotation = rotation @ rot

        if np.max(np.abs(rotation - old_rotation)) < tol:
            break

    return loadings @ rotation


# ── Data loading ──────────────────────────────────────────────────────────────
def load_scores() -> pd.DataFrame:
    """
    Load raw metric values from DuckDB, normalize against benchmarks,
    and return a city × metric DataFrame of normalized scores (0–100).
    Uses the same benchmarks as score.py.
    """
    conn = duckdb.connect(str(DB_PATH), read_only=True)
    df = conn.execute(
        "SELECT city, metric, sub_metric, value FROM metrics WHERE value IS NOT NULL"
    ).fetchdf()
    conn.close()

    if df.empty:
        raise RuntimeError("No data in metrics table. Run pipeline.py first.")

    df["key"] = df["metric"] + "." + df["sub_metric"]

    rows = {}
    for metric, sub_metric, pillar, benchmark, _ in SCORED_METRICS:
        key = f"{metric}.{sub_metric}"
        label = SHORT_LABELS.get(key, key)
        sub = df[df["key"] == key][["city", "value"]].set_index("city")["value"]
        rows[label] = sub.apply(lambda v: min(v / benchmark * 100, 100.0))

    wide = pd.DataFrame(rows)
    n_before = len(wide)
    wide = wide.dropna()
    n_after = len(wide)

    if n_before != n_after:
        print(f"  Note: dropped {n_before - n_after} cities with incomplete metrics "
              f"({n_after} cities with complete data remain)")

    return wide


# ── Analysis ──────────────────────────────────────────────────────────────────
def run():
    print("=" * 70)
    print("  Care Capacity Index — Factor Analysis")
    print(f"  {len(SCORED_METRICS)} metrics  |  {len(PILLAR_WEIGHTS)} pillars")
    print("=" * 70)

    print("\nLoading and normalizing metric scores from DuckDB...")
    scores = load_scores()
    n_cities, n_metrics = scores.shape
    print(f"  {n_cities} cities × {n_metrics} metrics")

    metric_names = list(scores.columns)

    # ── 1. Correlation matrix ─────────────────────────────────────────────────
    print("\n" + "─" * 70)
    print("1. SPEARMAN CORRELATION MATRIX")
    print("─" * 70)
    corr_matrix, _ = spearmanr(scores.values)
    if n_metrics == 2:
        corr_matrix = np.array([[1.0, corr_matrix], [corr_matrix, 1.0]])

    corr_df = pd.DataFrame(corr_matrix, index=metric_names, columns=metric_names)
    print("\n" + corr_df.round(2).to_string())

    print("\n  Strong correlations (|r| > 0.60):")
    found_strong = False
    for i, m1 in enumerate(metric_names):
        for j, m2 in enumerate(metric_names):
            if j <= i:
                continue
            r = corr_matrix[i, j]
            if abs(r) > 0.60:
                p1 = PILLAR_MEMBERSHIP[m1]
                p2 = PILLAR_MEMBERSHIP[m2]
                same = "same pillar" if p1 == p2 else "CROSS-PILLAR"
                print(f"    {m1} × {m2}: r={r:.2f} ({same})")
                found_strong = True
    if not found_strong:
        print("    None — metrics are relatively independent")

    # ── 2. PCA / Scree ────────────────────────────────────────────────────────
    print("\n" + "─" * 70)
    print("2. PRINCIPAL COMPONENTS — SCREE")
    print("─" * 70)

    scaler = StandardScaler()
    X = scaler.fit_transform(scores.values)

    pca_full = PCA(n_components=min(n_metrics, n_cities))
    pca_full.fit(X)

    print(f"\n  {'PC':<6} {'Eigenvalue':>12} {'Var Expl':>10} {'Cumul':>10}")
    cumul = 0.0
    eigenvalues = pca_full.explained_variance_
    var_ratios  = pca_full.explained_variance_ratio_
    for i, (ev, vr) in enumerate(zip(eigenvalues, var_ratios)):
        cumul += vr
        marker = " <-- Kaiser criterion (eigenvalue > 1)" if ev > 1.0 else ""
        print(f"  PC{i+1:<4} {ev:>12.3f} {vr*100:>9.1f}% {cumul*100:>9.1f}%{marker}")

    n_factors_kaiser = sum(1 for ev in eigenvalues if ev > 1.0)
    print(f"\n  Kaiser criterion suggests {n_factors_kaiser} factor(s).")
    print(f"  Current model assumes {len(PILLAR_WEIGHTS)} pillars.")

    # ── 3. 3-Factor PCA + Varimax ─────────────────────────────────────────────
    n_factors = len(PILLAR_WEIGHTS)
    print("\n" + "─" * 70)
    print(f"3. {n_factors}-FACTOR SOLUTION (VARIMAX ROTATED)")
    print("─" * 70)

    pca3 = PCA(n_components=n_factors)
    pca3.fit(X)
    loadings_raw = pca3.components_.T
    loadings = varimax(loadings_raw)

    var_nf = pca3.explained_variance_ratio_
    print(f"\n  {n_factors}-factor model explains {sum(var_nf)*100:.1f}% of total variance.")

    factor_cols = [f"Factor {i+1}" for i in range(n_factors)]
    loadings_df = pd.DataFrame(loadings, index=metric_names, columns=factor_cols)

    print("\n  Varimax-rotated factor loadings (|loading| ≥ 0.40 shown with **):\n")
    header = f"  {'Metric':<25} " + " ".join(f"{'F'+str(i+1):>8}" for i in range(n_factors)) + "   Pillar"
    print(header)
    print("  " + "-" * (len(header) - 2))
    for metric in metric_names:
        row = loadings_df.loc[metric]
        vals = [row[f] for f in factor_cols]
        flags_vals = " ".join(
            f"{'**' if abs(v) >= 0.40 else '  '}{v:>6.2f}" for v in vals
        )
        assigned = PILLAR_MEMBERSHIP.get(metric, "?")
        print(f"  {metric:<25} {flags_vals}   {assigned}")

    # ── 4. Pillar alignment ───────────────────────────────────────────────────
    print("\n" + "─" * 70)
    print("4. PILLAR ALIGNMENT")
    print("─" * 70)

    pillar_metrics_map = {
        p: [m for m in metric_names if PILLAR_MEMBERSHIP.get(m) == p]
        for p in PILLAR_WEIGHTS
    }

    factor_pillar_affinity = {}
    for fi, factor in enumerate(factor_cols):
        affinities = {}
        for pillar, metrics in pillar_metrics_map.items():
            if metrics:
                affinities[pillar] = np.mean([abs(loadings_df.loc[m, factor]) for m in metrics])
        best_pillar = max(affinities, key=affinities.get)
        factor_pillar_affinity[factor] = best_pillar
        aff_str = "  |  ".join(
            f"{PILLAR_LABELS[p]}: {v:.2f}" for p, v in affinities.items()
        )
        print(f"\n  {factor} → {PILLAR_LABELS[best_pillar]}")
        print(f"    Mean |loading|: {aff_str}")

    all_aligned = len(set(factor_pillar_affinity.values())) == len(PILLAR_WEIGHTS)
    print(f"\n  RESULT: {'Each factor aligns to a distinct pillar — 3-pillar structure supported.' if all_aligned else 'Factor-pillar alignment is ambiguous — consider revising pillar structure.'}")

    # ── 5. Empirical weight derivation ────────────────────────────────────────
    print("\n" + "─" * 70)
    print("5. EMPIRICAL WEIGHT DERIVATION")
    print("─" * 70)

    factor_to_pillar = factor_pillar_affinity

    empirical_within = {}
    for factor, pillar in factor_to_pillar.items():
        metrics_in_pillar = pillar_metrics_map[pillar]
        sq_loadings = {m: loadings_df.loc[m, factor] ** 2 for m in metrics_in_pillar}
        total = sum(sq_loadings.values())
        empirical_within[pillar] = {
            m: round(v / total, 3) for m, v in sq_loadings.items()
        } if total > 0 else {m: 1.0 / len(metrics_in_pillar) for m in metrics_in_pillar}

    pillar_var = {
        pillar: var_nf[fi]
        for fi, (factor, pillar) in enumerate(factor_to_pillar.items())
    }
    total_var = sum(pillar_var.values())
    empirical_inter = {p: round(v / total_var, 3) for p, v in pillar_var.items()}

    print(f"\n  Inter-pillar weights:")
    print(f"  {'Pillar':<35} {'V3 (theory)':>12} {'Empirical':>12}")
    print("  " + "-" * 62)
    for pillar in PILLAR_WEIGHTS:
        curr = PILLAR_WEIGHTS[pillar]
        emp  = empirical_inter.get(pillar, "n/a")
        emp_str = f"{emp:>12.3f}" if isinstance(emp, float) else f"{emp:>12}"
        print(f"  {PILLAR_LABELS[pillar]:<35} {curr:>12.2f} {emp_str}")

    print(f"\n  Within-pillar weights:")
    for pillar in PILLAR_WEIGHTS:
        print(f"\n  {PILLAR_LABELS[pillar]}:")
        emp_w = empirical_within.get(pillar, {})
        for metric, sub_metric, p, _, curr_w in SCORED_METRICS:
            if p != pillar:
                continue
            short = SHORT_LABELS.get(f"{metric}.{sub_metric}", f"{metric}.{sub_metric}")
            emp_val = emp_w.get(short, "n/a")
            emp_str = f"{emp_val:.3f}" if isinstance(emp_val, float) else emp_val
            print(f"    {short:<30}  V3: {curr_w:.2f}  empirical: {emp_str}")

    # ── 6. Save outputs ───────────────────────────────────────────────────────
    print("\n" + "─" * 70)
    print("6. SAVING OUTPUTS")
    print("─" * 70)

    loadings_df.to_csv(OUTPUTS_DIR / "factor_analysis_loadings.csv")
    print(f"\n  Loadings      → {OUTPUTS_DIR / 'factor_analysis_loadings.csv'}")

    corr_df.round(3).to_csv(OUTPUTS_DIR / "factor_analysis_correlations.csv")
    print(f"  Correlations  → {OUTPUTS_DIR / 'factor_analysis_correlations.csv'}")

    weights_out = {
        "meta": {
            "n_cities": n_cities,
            "variance_explained_3f": round(float(sum(var_nf)), 3),
            "kaiser_factors": n_factors_kaiser,
            "pillar_structure_supported": all_aligned,
            "note": "Empirical weights for review only. V3 implements theory-based inter-pillar weights. See methodology.md Section 5.",
        },
        "inter_pillar_note": (
            "V3.1 data (68 cities, 6 metrics, 75.5% variance explained): empirical weights "
            "recommend Institutions of Care as dominant pillar (0.496 vs 0.328 Social Fabric). "
            "V3 retains Social Fabric primary (0.40) per care ethics theory. "
            "Kaiser criterion suggests 2 factors, but 3-factor solution aligns cleanly to "
            "pillars with no cross-pillar correlation above 0.60. V4 will revisit inter-pillar weights."
        ),
        "inter_pillar_weights": {
            "empirical": empirical_inter,
            "v3_implemented": {p: PILLAR_WEIGHTS[p] for p in PILLAR_WEIGHTS},
        },
        "within_pillar_weights": {},
    }

    for metric, sub_metric, pillar, benchmark, curr_w in SCORED_METRICS:
        short = SHORT_LABELS.get(f"{metric}.{sub_metric}", f"{metric}.{sub_metric}")
        emp_w = empirical_within.get(pillar, {}).get(short, curr_w)
        weights_out["within_pillar_weights"][f"{metric}.{sub_metric}"] = {
            "pillar": pillar,
            "v3_weight": curr_w,
            "empirical_weight": round(float(emp_w), 3),
        }

    with open(OUTPUTS_DIR / "factor_analysis_weights.json", "w") as f:
        json.dump(weights_out, f, indent=2)
    print(f"  Weights JSON  → {OUTPUTS_DIR / 'factor_analysis_weights.json'}")

    print("\n" + "=" * 70)
    print("  Factor analysis complete.")
    print("  Review factor_analysis_weights.json before adopting any weight changes.")
    print("=" * 70)


if __name__ == "__main__":
    run()
