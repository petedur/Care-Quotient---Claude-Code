"""
Factor Analysis — Care Capacity Index
======================================
Tests whether the assumed 3-pillar structure (Social Support, Institutions of
Care, Reach) holds empirically by running PCA on the 7 scored metrics across
all cities with complete data.

Outputs
-------
  1. Correlation matrix of raw metric scores
  2. Scree plot data (variance explained per principal component)
  3. Varimax-rotated factor loadings (3-factor solution)
  4. Proposed empirical weights vs. current theory-based weights
  5. Pillar alignment scores (how well each factor maps to a pillar)
  6. outputs/factor_analysis.csv  — loadings table for inspection
  7. outputs/factor_analysis_weights.json — proposed weights in score.py format

This is a diagnostic tool, not a scoring tool. No scoring changes are made here.
Review the output and decide whether to adopt the empirical weights in V3.

Usage
-----
    python code/analysis/factor_analysis.py

Dependencies (in addition to existing requirements):
    pip install scikit-learn scipy
"""

import sys
import json
import numpy as np
import pandas as pd
import duckdb
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from config import DB_PATH, PROJECT_ROOT

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

# ── Metric definitions (mirrors score.py SCORED_METRICS) ─────────────────────
# (metric, sub_metric, pillar, benchmark, current_within_pillar_weight)
SCORED_METRICS = [
    ("residential_stability",     "pct_same_house",    "pillar1", 95.0,  0.48),
    ("nonprofit_density",         "social_support",    "pillar1", 10.0,  0.40),
    ("housing_cost_burden",       "pct_not_burdened",  "pillar1", 85.0,  0.12),
    ("health_center_density",     "density_per_100k",  "pillar2", 15.0,  0.55),
    ("nonprofit_density",         "care_institutions", "pillar2",  8.0,  0.45),
    ("snap_participation",        "coverage_rate",     "pillar3", 85.0,  0.60),
    ("health_insurance_coverage", "pct_insured",       "pillar3", 95.0,  0.40),
]

# Current inter-pillar weights
CURRENT_PILLAR_WEIGHTS = {"pillar1": 0.40, "pillar2": 0.35, "pillar3": 0.25}

SHORT_LABELS = {
    "residential_stability.pct_same_house":       "Resid. Stability",
    "nonprofit_density.social_support":           "Social Support NPs",
    "housing_cost_burden.pct_not_burdened":       "Housing Affordability",
    "health_center_density.density_per_100k":     "FQHC Density",
    "nonprofit_density.care_institutions":        "Care Institution NPs",
    "snap_participation.coverage_rate":           "SNAP Coverage",
    "health_insurance_coverage.pct_insured":      "Health Insurance",
}

PILLAR_LABELS = {
    "pillar1": "Social Support & Connection",
    "pillar2": "Institutions of Care",
    "pillar3": "Reach",
}

# Expected pillar membership for each metric (for alignment scoring)
PILLAR_MEMBERSHIP = {
    "Resid. Stability":       "pillar1",
    "Social Support NPs":     "pillar1",
    "Housing Affordability":  "pillar1",
    "FQHC Density":           "pillar2",
    "Care Institution NPs":   "pillar2",
    "SNAP Coverage":          "pillar3",
    "Health Insurance":       "pillar3",
}


# ── Varimax rotation ──────────────────────────────────────────────────────────
def varimax(loadings: np.ndarray, tol: float = 1e-6, max_iter: int = 1000) -> np.ndarray:
    """
    Apply varimax rotation to a (n_variables × n_factors) loading matrix.
    Returns the rotated loading matrix.
    """
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
    """
    conn = duckdb.connect(str(DB_PATH), read_only=True)
    df = conn.execute(
        "SELECT city, metric, sub_metric, value FROM metrics WHERE value IS NOT NULL"
    ).fetchdf()
    conn.close()

    if df.empty:
        raise RuntimeError(
            "No data in metrics table. Run pipeline.py first."
        )

    df["key"] = df["metric"] + "." + df["sub_metric"]

    # Build scored wide table
    rows = {}
    for metric, sub_metric, pillar, benchmark, _ in SCORED_METRICS:
        key = f"{metric}.{sub_metric}"
        sub = df[df["key"] == key][["city", "value"]].set_index("city")["value"]
        rows[SHORT_LABELS[key]] = sub.apply(lambda v: min(v / benchmark * 100, 100.0))

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
    corr_matrix, p_values = spearmanr(scores.values)
    if n_metrics == 2:
        # spearmanr returns scalars for 2 vars
        corr_matrix = np.array([[1.0, corr_matrix], [corr_matrix, 1.0]])

    corr_df = pd.DataFrame(corr_matrix, index=metric_names, columns=metric_names)
    print("\n" + corr_df.round(2).to_string())

    # Flag strong cross-pillar correlations (r > 0.6) as potential restructuring signals
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
    print(f"  Current model assumes 3 pillars.")

    # ── 3. 3-Factor PCA + Varimax ─────────────────────────────────────────────
    print("\n" + "─" * 70)
    print("3. 3-FACTOR SOLUTION (VARIMAX ROTATED)")
    print("─" * 70)

    pca3 = PCA(n_components=3)
    pca3.fit(X)
    loadings_raw = pca3.components_.T  # shape: (n_metrics, 3)
    loadings = varimax(loadings_raw)

    var_3f = pca3.explained_variance_ratio_
    print(f"\n  3-factor model explains {sum(var_3f)*100:.1f}% of total variance.")
    print(f"  (Pre-rotation: PC1={var_3f[0]*100:.1f}%, PC2={var_3f[1]*100:.1f}%, PC3={var_3f[2]*100:.1f}%)")

    loadings_df = pd.DataFrame(
        loadings,
        index=metric_names,
        columns=["Factor 1", "Factor 2", "Factor 3"],
    )

    print("\n  Varimax-rotated factor loadings (|loading| ≥ 0.40 shown with **):\n")
    header = f"  {'Metric':<25} {'F1':>8} {'F2':>8} {'F3':>8}   Assigned pillar"
    print(header)
    print("  " + "-" * (len(header) - 2))
    for metric in metric_names:
        row = loadings_df.loc[metric]
        f1, f2, f3 = row["Factor 1"], row["Factor 2"], row["Factor 3"]
        flags = [("**" if abs(v) >= 0.40 else "  ") for v in [f1, f2, f3]]
        assigned = PILLAR_MEMBERSHIP[metric]
        print(f"  {metric:<25} {flags[0]}{f1:>6.2f} {flags[1]}{f2:>6.2f} {flags[2]}{f3:>6.2f}   {assigned}")

    # ── 4. Pillar alignment ───────────────────────────────────────────────────
    print("\n" + "─" * 70)
    print("4. PILLAR ALIGNMENT")
    print("─" * 70)
    print("\n  For each factor, which pillar's metrics load most strongly on it?")

    pillar_metrics = {
        "pillar1": [m for m in metric_names if PILLAR_MEMBERSHIP[m] == "pillar1"],
        "pillar2": [m for m in metric_names if PILLAR_MEMBERSHIP[m] == "pillar2"],
        "pillar3": [m for m in metric_names if PILLAR_MEMBERSHIP[m] == "pillar3"],
    }

    factor_pillar_affinity = {}
    for fi, factor in enumerate(["Factor 1", "Factor 2", "Factor 3"]):
        affinities = {}
        for pillar, metrics in pillar_metrics.items():
            # Mean absolute loading for metrics assigned to this pillar
            affinities[pillar] = np.mean([abs(loadings_df.loc[m, factor]) for m in metrics])
        best_pillar = max(affinities, key=affinities.get)
        factor_pillar_affinity[factor] = best_pillar
        aff_str = "  |  ".join(
            f"{PILLAR_LABELS[p]}: {v:.2f}" for p, v in affinities.items()
        )
        print(f"\n  {factor} → {PILLAR_LABELS[best_pillar]}")
        print(f"    Mean |loading|: {aff_str}")

    all_aligned = len(set(factor_pillar_affinity.values())) == 3
    if all_aligned:
        print("\n  RESULT: Each factor aligns cleanly to a different pillar.")
        print("          The 3-pillar structure is empirically supported.")
    else:
        print("\n  RESULT: Factor-pillar alignment is ambiguous.")
        print("          Some pillars may be measuring the same underlying dimension.")
        print("          Consider merging or restructuring pillars before V3.")

    # ── 5. Empirical weight derivation ────────────────────────────────────────
    print("\n" + "─" * 70)
    print("5. EMPIRICAL WEIGHT DERIVATION")
    print("─" * 70)
    print("""
  Method: for each factor aligned to a pillar, the within-pillar weight of
  each metric is proportional to its squared loading on that factor (communality
  contribution). Inter-pillar weights are proportional to the variance explained
  by each factor after rotation (approximated from pre-rotation eigenvalues
  weighted by factor alignment quality).
""")

    # Map each factor to its best pillar
    factor_to_pillar = factor_pillar_affinity  # Factor N -> pillar key

    # Within-pillar empirical weights
    empirical_within = {}
    for factor, pillar in factor_to_pillar.items():
        metrics_in_pillar = pillar_metrics[pillar]
        sq_loadings = {m: loadings_df.loc[m, factor] ** 2 for m in metrics_in_pillar}
        total = sum(sq_loadings.values())
        if total > 0:
            empirical_within[pillar] = {m: round(v / total, 3) for m, v in sq_loadings.items()}
        else:
            empirical_within[pillar] = {m: 1.0 / len(metrics_in_pillar) for m in metrics_in_pillar}

    # Inter-pillar empirical weights: variance explained by each aligned factor
    # Use pre-rotation explained variance (post-rotation is harder to attribute)
    # The factor that best aligns to each pillar gets that PC's variance share
    pillar_var = {}
    for fi, (factor, pillar) in enumerate(factor_to_pillar.items()):
        pillar_var[pillar] = var_3f[fi]
    total_var = sum(pillar_var.values())
    empirical_inter = {p: round(v / total_var, 3) for p, v in pillar_var.items()}

    # Print comparison
    print(f"  {'Pillar':<35} {'Current':>10} {'Empirical':>12}")
    print("  " + "-" * 60)
    for pillar in ["pillar1", "pillar2", "pillar3"]:
        curr = CURRENT_PILLAR_WEIGHTS.get(pillar, "n/a")
        emp  = empirical_inter.get(pillar, "n/a")
        print(f"  {PILLAR_LABELS[pillar]:<35} {curr:>10.2f} {emp:>12.3f}")

    print()
    for pillar in ["pillar1", "pillar2", "pillar3"]:
        print(f"\n  {PILLAR_LABELS[pillar]} — within-pillar weights:")
        within_curr = {
            SHORT_LABELS[f"{m}.{s}"]: w
            for m, s, p, _, w in [
                ("residential_stability", "pct_same_house", "pillar1", None, 0.48),
                ("nonprofit_density", "social_support", "pillar1", None, 0.40),
                ("housing_cost_burden", "pct_not_burdened", "pillar1", None, 0.12),
                ("health_center_density", "density_per_100k", "pillar2", None, 0.55),
                ("nonprofit_density", "care_institutions", "pillar2", None, 0.45),
                ("snap_participation", "coverage_rate", "pillar3", None, 0.60),
                ("health_insurance_coverage", "pct_insured", "pillar3", None, 0.40),
            ] if p == pillar
        }
        emp_w = empirical_within.get(pillar, {})
        for metric_short, curr_w in within_curr.items():
            emp_w_val = emp_w.get(metric_short, "n/a")
            print(f"    {metric_short:<25}  current: {curr_w:.2f}  empirical: "
                  f"{emp_w_val:.3f}" if isinstance(emp_w_val, float) else
                  f"    {metric_short:<25}  current: {curr_w:.2f}  empirical: {emp_w_val}")

    # ── 6. Outputs ────────────────────────────────────────────────────────────
    print("\n" + "─" * 70)
    print("6. SAVING OUTPUTS")
    print("─" * 70)

    # Loadings CSV
    loadings_csv_path = OUTPUTS_DIR / "factor_analysis_loadings.csv"
    loadings_df.to_csv(loadings_csv_path)
    print(f"\n  Loadings table  → {loadings_csv_path}")

    # Correlation CSV
    corr_csv_path = OUTPUTS_DIR / "factor_analysis_correlations.csv"
    corr_df.round(3).to_csv(corr_csv_path)
    print(f"  Correlation matrix → {corr_csv_path}")

    # Proposed weights JSON
    # Build in score.py SCORED_METRICS format for easy manual adoption
    proposed_weights_output = {
        "meta": {
            "n_cities": n_cities,
            "variance_explained_3f": round(float(sum(var_3f)), 3),
            "kaiser_factors": n_factors_kaiser,
            "pillar_structure_supported": all_aligned,
        },
        "inter_pillar_weights": empirical_inter,
        "within_pillar_weights": {},
    }
    # Flatten within-pillar weights to (metric, sub_metric) key format
    for metric, sub_metric, pillar, benchmark, curr_w in SCORED_METRICS:
        short = SHORT_LABELS[f"{metric}.{sub_metric}"]
        emp_w = empirical_within.get(pillar, {}).get(short, curr_w)
        proposed_weights_output["within_pillar_weights"][f"{metric}.{sub_metric}"] = {
            "pillar": pillar,
            "current_weight":  curr_w,
            "empirical_weight": round(float(emp_w), 3),
        }

    weights_json_path = OUTPUTS_DIR / "factor_analysis_weights.json"
    with open(weights_json_path, "w") as f:
        json.dump(proposed_weights_output, f, indent=2)
    print(f"  Proposed weights    → {weights_json_path}")

    print("\n" + "=" * 70)
    print("  Factor analysis complete.")
    if all_aligned:
        print("  The 3-pillar structure is supported. Review proposed weights")
        print("  in factor_analysis_weights.json before adopting them in score.py.")
    else:
        print("  The 3-pillar structure is NOT clearly supported by the data.")
        print("  Consider reviewing pillar definitions before updating weights.")
    print("=" * 70)


if __name__ == "__main__":
    run()
