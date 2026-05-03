"""
Tests for score.py — normalization math, pillar aggregation, CQ calculation.

These tests use synthetic data with known values, so every assertion is
deterministic. No live APIs, no DuckDB file, no large data downloads required.
"""

import sys
import pytest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from score import normalize_to_benchmark, score, SCORED_METRICS, PILLAR_WEIGHTS


# ── normalize_to_benchmark ────────────────────────────────────────────────────

def test_normalize_at_benchmark():
    assert normalize_to_benchmark(95.0, 95.0) == 100.0


def test_normalize_half_benchmark():
    assert normalize_to_benchmark(47.5, 95.0) == 50.0


def test_normalize_zero():
    assert normalize_to_benchmark(0.0, 95.0) == 0.0


def test_normalize_caps_at_100():
    """Values above the benchmark should not exceed 100."""
    assert normalize_to_benchmark(190.0, 95.0) == 100.0


def test_normalize_above_benchmark_stays_100():
    """Double the benchmark → still 100."""
    assert normalize_to_benchmark(50.0, 25.0) == 100.0


def test_normalize_fractional():
    result = normalize_to_benchmark(7.5, 15.0)
    assert result == 50.0


# ── score() — perfect city ────────────────────────────────────────────────────

def test_perfect_city_all_100(synthetic_metrics_df):
    """A city at every benchmark should score 100 on every metric and the CQ."""
    results = score(synthetic_metrics_df[synthetic_metrics_df["city"] == "perfect"])

    for metric, sub_metric, pillar, benchmark, w in SCORED_METRICS:
        col = f"score_{metric}.{sub_metric}"
        assert col in results.columns, f"Missing column {col}"
        assert results.loc["perfect", col] == 100.0, \
            f"{col} should be 100 for perfect city, got {results.loc['perfect', col]}"

    assert results.loc["perfect", "care_quotient"] == 100.0
    assert results.loc["perfect", "pillar1"] == 100.0
    assert results.loc["perfect", "pillar2"] == 100.0
    assert results.loc["perfect", "pillar3"] == 100.0


# ── score() — half city ───────────────────────────────────────────────────────

def test_half_city_all_50(synthetic_metrics_df):
    """A city at 50% of every benchmark should score 50 everywhere."""
    results = score(synthetic_metrics_df[synthetic_metrics_df["city"] == "half"])

    for metric, sub_metric, pillar, benchmark, w in SCORED_METRICS:
        col = f"score_{metric}.{sub_metric}"
        val = results.loc["half", col]
        assert val == pytest.approx(50.0, abs=0.1), \
            f"{col} expected 50.0, got {val}"

    assert results.loc["half", "care_quotient"] == pytest.approx(50.0, abs=0.1)


# ── score() — zero city ───────────────────────────────────────────────────────

def test_zero_city_all_0(synthetic_metrics_df):
    """A city with all-zero metrics should score 0 everywhere."""
    results = score(synthetic_metrics_df[synthetic_metrics_df["city"] == "zero"])

    for metric, sub_metric, pillar, benchmark, w in SCORED_METRICS:
        col = f"score_{metric}.{sub_metric}"
        assert results.loc["zero", col] == 0.0

    assert results.loc["zero", "care_quotient"] == 0.0


# ── score() — over city (ceiling) ────────────────────────────────────────────

def test_over_city_caps_at_100(synthetic_metrics_df):
    """A city exceeding every benchmark should still score 100, not above."""
    results = score(synthetic_metrics_df[synthetic_metrics_df["city"] == "over"])

    for metric, sub_metric, pillar, benchmark, w in SCORED_METRICS:
        col = f"score_{metric}.{sub_metric}"
        val = results.loc["over", col]
        assert val == 100.0, f"{col} should be capped at 100, got {val}"

    assert results.loc["over", "care_quotient"] == 100.0


# ── score() — pillar weights sum to 1 ────────────────────────────────────────

def test_pillar_weights_sum_to_1():
    total = sum(PILLAR_WEIGHTS.values())
    assert total == pytest.approx(1.0, abs=1e-9), \
        f"Pillar weights sum to {total}, expected 1.0"


def test_within_pillar_weights_sum_to_1():
    """Within-pillar weights must sum to 1.0 for each pillar."""
    from collections import defaultdict
    weights = defaultdict(float)
    for _, _, pillar, _, w in SCORED_METRICS:
        weights[pillar] += w
    for pillar, total in weights.items():
        assert total == pytest.approx(1.0, abs=1e-9), \
            f"Within-pillar weights for {pillar} sum to {total}, expected 1.0"


# ── score() — CQ is weighted average of pillars ───────────────────────────────

def test_cq_is_weighted_pillar_average(synthetic_metrics_df):
    """CQ should equal the weighted average of pillar scores."""
    results = score(synthetic_metrics_df)

    for city in results.index:
        expected_cq = round(
            sum(results.loc[city, p] * w for p, w in PILLAR_WEIGHTS.items()), 1
        )
        actual_cq = results.loc[city, "care_quotient"]
        assert actual_cq == pytest.approx(expected_cq, abs=0.15), \
            f"CQ for {city}: expected {expected_cq}, got {actual_cq}"


# ── score() — missing metric ──────────────────────────────────────────────────

def test_missing_metric_handled_gracefully(synthetic_metrics_df):
    """
    If one metric is missing for a city, score() should warn and reweight
    rather than crash. The city should still receive a numeric score.
    """
    import pandas as pd
    partial = synthetic_metrics_df[
        ~(
            (synthetic_metrics_df["city"] == "half") &
            (synthetic_metrics_df["metric"] == "nursing_home_capacity")
        )
    ].copy()

    # Should not raise
    results = score(partial)
    assert "half" in results.index
    assert "care_quotient" in results.columns
