"""
Shared fixtures for the Care Capacity Index test suite.

Design: tests use synthetic data with known values so results are
fully deterministic and never depend on live APIs or large data files.
"""

import json
import pytest
import duckdb
import pandas as pd
from pathlib import Path

# ── Synthetic city data ───────────────────────────────────────────────────────
# Three fake cities with hand-crafted metric values.
# "perfect" hits every benchmark exactly (all scores = 100).
# "half"    sits at 50% of every benchmark (all scores = 50).
# "zero"    has zero for every metric (all scores = 0).

SYNTHETIC_METRICS = [
    # (city, metric, sub_metric, value)
    # Pillar structure (V5):
    #   Pillar 1 — Social & Relational Care (40%): residential_stability, combined_care, library_density
    #   Pillar 2 — Institutional Care (35%): health_center_density, nursing_home_capacity
    #   Pillar 3 — Economic Access (25%): health_insurance_coverage, housing_cost_burden, snap_participation

    # perfect city — at-benchmark values (all scores = 100)
    ("perfect", "residential_stability",     "pct_same_house",     95.0),
    ("perfect", "nonprofit_density",         "combined_care",      25.0),
    ("perfect", "library_density",           "density_per_100k",    5.0),
    ("perfect", "health_center_density",     "density_per_100k",   15.0),
    ("perfect", "nursing_home_capacity",     "beds_per_1k_65plus", 50.0),
    ("perfect", "health_insurance_coverage", "coverage_rate",     100.0),
    ("perfect", "housing_cost_burden",       "pct_not_burdened",   90.0),
    ("perfect", "snap_participation",        "coverage_rate",      85.0),

    # half city — 50% of every benchmark (all scores = 50)
    ("half", "residential_stability",     "pct_same_house",     47.5),
    ("half", "nonprofit_density",         "combined_care",      12.5),
    ("half", "library_density",           "density_per_100k",    2.5),
    ("half", "health_center_density",     "density_per_100k",    7.5),
    ("half", "nursing_home_capacity",     "beds_per_1k_65plus", 25.0),
    ("half", "health_insurance_coverage", "coverage_rate",       50.0),
    ("half", "housing_cost_burden",       "pct_not_burdened",   45.0),
    ("half", "snap_participation",        "coverage_rate",      42.5),

    # zero city — all zeros (all scores = 0)
    ("zero", "residential_stability",     "pct_same_house",     0.0),
    ("zero", "nonprofit_density",         "combined_care",      0.0),
    ("zero", "library_density",           "density_per_100k",   0.0),
    ("zero", "health_center_density",     "density_per_100k",   0.0),
    ("zero", "nursing_home_capacity",     "beds_per_1k_65plus", 0.0),
    ("zero", "health_insurance_coverage", "coverage_rate",      0.0),
    ("zero", "housing_cost_burden",       "pct_not_burdened",   0.0),
    ("zero", "snap_participation",        "coverage_rate",      0.0),

    # over city — values exceeding every benchmark (all scores cap at 100)
    ("over", "residential_stability",     "pct_same_house",     99.0),
    ("over", "nonprofit_density",         "combined_care",      50.0),
    ("over", "library_density",           "density_per_100k",   10.0),
    ("over", "health_center_density",     "density_per_100k",   30.0),
    ("over", "nursing_home_capacity",     "beds_per_1k_65plus", 100.0),
    ("over", "health_insurance_coverage", "coverage_rate",      100.0),
    ("over", "housing_cost_burden",       "pct_not_burdened",   99.0),
    ("over", "snap_participation",        "coverage_rate",      99.0),
]


@pytest.fixture
def synthetic_metrics_df():
    """DataFrame of synthetic metrics in the same shape as the DuckDB metrics table."""
    return pd.DataFrame(
        SYNTHETIC_METRICS,
        columns=["city", "metric", "sub_metric", "value"],
    )


@pytest.fixture
def synthetic_duckdb(tmp_path, synthetic_metrics_df):
    """
    In-memory DuckDB populated with synthetic metrics.
    Returns the connection; caller is responsible for closing it.
    """
    conn = duckdb.connect(str(tmp_path / "test.duckdb"))
    conn.execute("""
        CREATE TABLE metrics (
            city        VARCHAR,
            metric      VARCHAR,
            sub_metric  VARCHAR,
            value       DOUBLE
        )
    """)
    conn.register("_syn", synthetic_metrics_df)
    conn.execute("INSERT INTO metrics SELECT * FROM _syn")
    return conn


# ── Synthetic ETL CSV fixtures ────────────────────────────────────────────────

@pytest.fixture
def residential_stability_csv(tmp_path):
    df = pd.DataFrame({
        "same_house": [850, 900],
        "population": [1000, 1000],
    })
    p = tmp_path / "residential_stability.csv"
    df.to_csv(p, index=False)
    return p


@pytest.fixture
def housing_cost_burden_csv(tmp_path):
    df = pd.DataFrame({
        "burdened": [100, 200],
        "total":    [1000, 1000],
    })
    p = tmp_path / "housing_cost_burden.csv"
    df.to_csv(p, index=False)
    return p


@pytest.fixture
def snap_participation_csv(tmp_path):
    df = pd.DataFrame({
        "snap_households":        [300],
        "total_households":       [1000],
        "eligible_pop_0_149pct_fpl": [500],
        "total_pop":              [2000],
    })
    p = tmp_path / "snap_participation.csv"
    df.to_csv(p, index=False)
    return p


@pytest.fixture
def health_insurance_csv(tmp_path):
    # medicaid_enrolled=750, eligible_pop=1000 → coverage_rate = 75.0
    df = pd.DataFrame({
        "total_pop":                 [1000, 1000],
        "medicaid_enrolled":         [400,   350],
        "eligible_pop_0_149pct_fpl": [500,   500],
        "pct_medicaid":              [40.0,  35.0],
    })
    p = tmp_path / "health_insurance.csv"
    df.to_csv(p, index=False)
    return p


@pytest.fixture
def nursing_homes_meta(tmp_path):
    meta = {
        "facility_count":             12,
        "certified_beds":             600,
        "avg_daily_residents":        520.0,
        "population_65plus":          10000,
        "beds_per_1k_65plus":         60.0,
        "facilities_per_100k_65plus": 120.0,
    }
    p = tmp_path / "nursing_homes_meta.json"
    p.write_text(json.dumps(meta))
    return p
