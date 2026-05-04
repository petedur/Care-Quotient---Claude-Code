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
        "SELECT value FROM metrics "
        "WHERE city='testcity' AND metric='health_insurance_coverage' "
        "AND sub_metric='coverage_rate'"
    ).fetchone()
    assert row is not None
    # medicaid_enrolled=750, eligible_pop=1000 → 750/1000 * 100 = 75.0
    assert row[0] == pytest.approx(75.0, abs=0.01)


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


def test_load_child_care_capacity(conn, child_care_capacity_json, monkeypatch):
    monkeypatch.setattr(etl, "DATA_RAW", child_care_capacity_json.parent)
    (child_care_capacity_json.parent / "testcity").mkdir(exist_ok=True)
    child_care_capacity_json.rename(
        child_care_capacity_json.parent / "testcity" / "child_care_capacity.json"
    )
    etl.load_child_care_capacity(conn, "testcity")
    row = conn.execute(
        "SELECT value FROM metrics "
        "WHERE city='testcity' AND metric='child_care_capacity' "
        "AND sub_metric='establishments_per_1k_under5'"
    ).fetchone()
    assert row is not None
    assert row[0] == pytest.approx(10.5, abs=0.01)


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
        ("testcity", "residential_stability",     "pct_same_house",              87.5),
        ("testcity", "nonprofit_density",         "combined_care",               10.0),
        ("testcity", "library_density",           "density_per_100k",             3.0),
        ("testcity", "health_center_density",     "density_per_100k",             5.0),
        ("testcity", "nursing_home_capacity",     "beds_per_1k_65plus",          40.0),
        ("testcity", "child_care_capacity",       "establishments_per_1k_under5", 8.0),
        ("testcity", "health_insurance_coverage", "coverage_rate",               75.0),
        ("testcity", "housing_cost_burden",       "pct_not_burdened",            75.0),
        ("testcity", "snap_participation",        "coverage_rate",               70.0),
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


# ── distressed-population diagnostic ─────────────────────────────────────────

@pytest.fixture
def nonprofits_and_snap_csvs(tmp_path):
    """Minimal nonprofits_care.csv + snap_participation.csv for one city."""
    city_dir = tmp_path / "testcity"
    city_dir.mkdir()

    # 10 combined-care nonprofits (all NTEE P, active 501(c)(3))
    np_df = pd.DataFrame({
        "NTEE_CD":    ["P20"] * 10,
        "SUBSECTION": ["03"] * 10,
        "STATUS":     ["01"] * 10,
        "EIN":        [str(i) for i in range(10)],
        "NAME":       ["Org " + str(i) for i in range(10)],
        "STATE":      ["NY"] * 10,
        "ZIP":        ["10001"] * 10,
    })
    np_df.to_csv(city_dir / "nonprofits_care.csv", index=False, encoding="latin-1")

    # distressed_pop = 500 + 500 = 1000
    snap_df = pd.DataFrame({
        "snap_households":           [200, 200],
        "total_households":          [1000, 1000],
        "eligible_pop_0_149pct_fpl": [500, 500],
        "total_pop":                 [2000, 2000],
    })
    snap_df.to_csv(city_dir / "snap_participation.csv", index=False)

    return tmp_path


def test_load_nonprofit_density_distressed_diagnostic(conn, nonprofits_and_snap_csvs, monkeypatch):
    """
    When snap_participation.csv is present, load_nonprofit_density should
    compute combined_care_per_10k_distressed = count / distressed_pop * 10_000.

    10 nonprofits / 1000 distressed * 10_000 = 100.0
    """
    monkeypatch.setattr(etl, "DATA_RAW", nonprofits_and_snap_csvs)
    # Monkeypatch CITIES so the function can look up population
    import config
    monkeypatch.setitem(config.CITIES, "testcity", {
        "name": "Test City", "state": "NY", "state_fips": "36",
        "population": 50000, "county_fips": set(), "place_fips": "",
    })
    etl.load_nonprofit_density(conn, "testcity")

    row = conn.execute(
        "SELECT value, notes FROM metrics "
        "WHERE city='testcity' AND sub_metric='combined_care_per_10k_distressed'"
    ).fetchone()
    assert row is not None, "distressed diagnostic should be upserted"
    assert row[0] == pytest.approx(100.0, abs=0.01), \
        f"expected 100.0, got {row[0]}"
    assert "distressed_pop=1000" in row[1]


def test_load_nonprofit_density_no_snap_skips_distressed(conn, tmp_path, monkeypatch):
    """When snap_participation.csv is absent, no distressed diagnostic row is written."""
    city_dir = tmp_path / "testcity"
    city_dir.mkdir()
    np_df = pd.DataFrame({
        "NTEE_CD": ["P20"], "SUBSECTION": ["03"], "STATUS": ["01"],
        "EIN": ["1"], "NAME": ["Org"], "STATE": ["NY"], "ZIP": ["10001"],
    })
    np_df.to_csv(city_dir / "nonprofits_care.csv", index=False, encoding="latin-1")

    monkeypatch.setattr(etl, "DATA_RAW", tmp_path)
    import config
    monkeypatch.setitem(config.CITIES, "testcity", {
        "name": "Test City", "state": "NY", "state_fips": "36",
        "population": 50000, "county_fips": set(), "place_fips": "",
    })
    etl.load_nonprofit_density(conn, "testcity")

    row = conn.execute(
        "SELECT value FROM metrics "
        "WHERE city='testcity' AND sub_metric='combined_care_per_10k_distressed'"
    ).fetchone()
    assert row is None, "distressed diagnostic should not be written without snap data"
