"""
Tests for etl.py loaders — each loader is tested against a synthetic CSV/JSON
fixture with known values so results are fully deterministic.
"""

import sys
import json
import pytest
import duckdb
import pandas as pd
from pathlib import Path
from unittest.mock import MagicMock

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import etl


@pytest.fixture
def conn():
    """Fresh in-memory DuckDB connection with the metrics schema."""
    c = duckdb.connect(":memory:")
    c.execute(etl.SCHEMA)
    yield c
    c.close()


# ── residential_stability ─────────────────────────────────────────────────────

def test_load_residential_stability(conn, residential_stability_csv, monkeypatch):
    monkeypatch.setattr(etl, "DATA_RAW", residential_stability_csv.parent)
    # Move file to expected location
    (residential_stability_csv.parent / "testcity").mkdir(exist_ok=True)
    residential_stability_csv.rename(
        residential_stability_csv.parent / "testcity" / "residential_stability.csv"
    )
    etl.load_residential_stability(conn, "testcity")
    row = conn.execute(
        "SELECT value FROM metrics WHERE city='testcity' AND metric='residential_stability'"
    ).fetchone()
    assert row is not None
    # (850+900)/(1000+1000) * 100 = 87.5
    assert row[0] == pytest.approx(87.5, abs=0.01)


# ── housing_cost_burden ───────────────────────────────────────────────────────

def test_load_housing_cost_burden(conn, housing_cost_burden_csv, monkeypatch):
    monkeypatch.setattr(etl, "DATA_RAW", housing_cost_burden_csv.parent)
    (housing_cost_burden_csv.parent / "testcity").mkdir(exist_ok=True)
    housing_cost_burden_csv.rename(
        housing_cost_burden_csv.parent / "testcity" / "housing_cost_burden.csv"
    )
    etl.load_housing_cost_burden(conn, "testcity")
    row = conn.execute(
        "SELECT value FROM metrics WHERE city='testcity' AND metric='housing_cost_burden'"
    ).fetchone()
    assert row is not None
    # burdened=300, total=2000 → not_burdened=85%
    assert row[0] == pytest.approx(85.0, abs=0.01)


# ── snap_participation ────────────────────────────────────────────────────────

def test_load_snap_participation(conn, snap_participation_csv, monkeypatch):
    monkeypatch.setattr(etl, "DATA_RAW", snap_participation_csv.parent)
    (snap_participation_csv.parent / "testcity").mkdir(exist_ok=True)
    snap_participation_csv.rename(
        snap_participation_csv.parent / "testcity" / "snap_participation.csv"
    )
    etl.load_snap_participation(conn, "testcity")
    row = conn.execute(
        "SELECT value FROM metrics WHERE city='testcity' AND metric='snap_participation'"
    ).fetchone()
    assert row is not None
    # snap_rate = 300/1000 = 0.30; eligible_rate = 500/2000 = 0.25
    # coverage = min(0.30/0.25 * 100, 100) = min(120, 100) = 100
    assert row[0] == pytest.approx(100.0, abs=0.01)


# ── health_insurance ──────────────────────────────────────────────────────────

def test_load_health_insurance(conn, health_insurance_csv, monkeypatch):
    monkeypatch.setattr(etl, "DATA_RAW", health_insurance_csv.parent)
    (health_insurance_csv.parent / "testcity").mkdir(exist_ok=True)
    health_insurance_csv.rename(
        health_insurance_csv.parent / "testcity" / "health_insurance.csv"
    )
    etl.load_health_insurance(conn, "testcity")
    row = conn.execute(
        "SELECT value FROM metrics WHERE city='testcity' AND metric='health_insurance_coverage'"
    ).fetchone()
    assert row is not None
    # total_pop=2000, insured=1890 → 94.5%
    assert row[0] == pytest.approx(94.5, abs=0.01)


# ── nursing_homes ─────────────────────────────────────────────────────────────

def test_load_nursing_homes(conn, nursing_homes_meta, monkeypatch):
    monkeypatch.setattr(etl, "DATA_RAW", nursing_homes_meta.parent)
    (nursing_homes_meta.parent / "testcity").mkdir(exist_ok=True)
    nursing_homes_meta.rename(
        nursing_homes_meta.parent / "testcity" / "nursing_homes_meta.json"
    )
    etl.load_nursing_homes(conn, "testcity")
    row = conn.execute(
        "SELECT value FROM metrics "
        "WHERE city='testcity' AND metric='nursing_home_capacity' "
        "AND sub_metric='beds_per_1k_65plus'"
    ).fetchone()
    assert row is not None
    assert row[0] == pytest.approx(60.0, abs=0.01)


def test_load_nursing_homes_missing_file(conn, tmp_path, monkeypatch, capsys):
    """Missing meta file should skip gracefully, not raise."""
    monkeypatch.setattr(etl, "DATA_RAW", tmp_path)
    etl.load_nursing_homes(conn, "nonexistent_city")
    captured = capsys.readouterr()
    assert "SKIP" in captured.out


# ── validation ────────────────────────────────────────────────────────────────

def test_validation_passes_clean_data(conn, monkeypatch):
    """Clean in-range data should pass all validation checks."""
    for city, metric, sub_metric, value in [
        ("testcity", "residential_stability",     "pct_same_house",   87.5),
        ("testcity", "housing_cost_burden",       "pct_not_burdened", 75.0),
        ("testcity", "nonprofit_density",         "combined_care",    10.0),
        ("testcity", "health_center_density",     "density_per_100k",  5.0),
        ("testcity", "nursing_home_capacity",     "beds_per_1k_65plus", 40.0),
        ("testcity", "health_insurance_coverage", "pct_insured",      92.0),
        ("testcity", "snap_participation",        "coverage_rate",    70.0),
    ]:
        etl.upsert(conn, city, metric, sub_metric, value=value)

    result = etl.validate(conn)
    assert result is True


def test_validation_flags_out_of_range(conn, capsys):
    """A value outside the valid range should trigger a WARNING."""
    etl.upsert(conn, "badcity", "residential_stability", "pct_same_house", value=150.0)
    etl.validate(conn)
    captured = capsys.readouterr()
    assert "OUT-OF-RANGE" in captured.out or "WARNING" in captured.out


def test_validation_flags_missing_required_metric(conn, capsys):
    """A city missing a required scored metric should trigger a WARNING."""
    etl.upsert(conn, "incompletecity", "residential_stability", "pct_same_house", value=85.0)
    etl.validate(conn)
    captured = capsys.readouterr()
    assert "MISSING" in captured.out
