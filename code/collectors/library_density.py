"""
Collector: Library Density (IMLS Public Libraries Survey)
Measures library locations per 100,000 residents and visits per capita.

Data source: IMLS Public Libraries Survey
  - Download from: https://www.imls.gov/research-tools/data-collection/public-libraries-survey
  - Place the outlet-level CSV (e.g. pls_fy2022_outlet.csv) in:
    Downloaded Data/Public Libraries Survey (PLS)/
"""

import sys
import pandas as pd
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from config import IMLS_DATA_PATH, DATA_RAW, CITIES


def load_imls(path: Path) -> pd.DataFrame:
    if path.suffix == ".csv":
        df = pd.read_csv(path, dtype=str, low_memory=False)
    elif path.suffix in (".xlsx", ".xls"):
        df = pd.read_excel(path, dtype=str)
    else:
        raise ValueError(f"Unrecognised file type: {path.suffix}")
    df.columns = [c.strip().upper() for c in df.columns]
    return df


def find_imls_file() -> Path:
    base = Path(IMLS_DATA_PATH)
    for pattern in ("*.csv", "**/*.csv", "*.xlsx"):
        files = list(base.glob(pattern))
        if files:
            return files[0]
    raise FileNotFoundError(
        f"No IMLS file found in {IMLS_DATA_PATH}. "
        "Download the outlet-level CSV from https://www.imls.gov"
    )


def _find_col(df: pd.DataFrame, *candidates: str) -> str | None:
    """Return the first column name (case-insensitive) that matches any candidate substring."""
    for cand in candidates:
        for col in df.columns:
            if cand.upper() in col.upper():
                return col
    return None


def collect(city_key: str = "nyc") -> dict:
    city = CITIES[city_key]
    print(f"\n=== Library Density — {city['name']} ===")

    path = find_imls_file()
    print(f"  Loading: {path.name}")
    df = load_imls(path)

    # Identify state and city columns
    state_col = _find_col(df, "STABR", "STATE")
    city_col  = _find_col(df, "CITY")
    if not state_col:
        raise ValueError(f"Cannot find state column. Available: {df.columns.tolist()}")

    # Filter to this state
    state_df = df[df[state_col].str.upper() == city["state"].upper()].copy()
    print(f"  {len(state_df)} libraries in {city['state']}")

    # Filter to this city's known names
    if city_col:
        city_names = [n.upper() for n in city["irs_city_names"]]  # reuse same name list
        city_df = state_df[state_df[city_col].str.upper().isin(city_names)].copy()
    else:
        print("  WARNING: no city column found; using state-wide data")
        city_df = state_df

    pop = city["population"]
    count = len(city_df)
    density = round(count / pop * 100_000, 2)
    print(f"  {count} libraries → {density} per 100,000")

    # Visits per capita (optional — column names vary by survey year)
    visits_col = _find_col(city_df, "VISITS", "VISIT", "TOTVISIT")
    metrics = {"library_count": count, "density_per_100k": density}

    if visits_col:
        total_visits = pd.to_numeric(city_df[visits_col], errors="coerce").sum()
        vpc = round(total_visits / pop, 2)
        metrics["total_visits"]      = int(total_visits)
        metrics["visits_per_capita"] = vpc
        print(f"  Visits per capita: {vpc}")

    # Save
    out_dir = DATA_RAW / city_key
    out_dir.mkdir(parents=True, exist_ok=True)
    city_df.to_csv(out_dir / "libraries.csv", index=False)
    print(f"  Raw data saved to {out_dir / 'libraries.csv'}")

    return {
        "city":   city_key,
        "metric": "library_density",
        "data":   metrics,
    }


if __name__ == "__main__":
    import sys
    city_key = sys.argv[1] if len(sys.argv) > 1 else "nyc"
    import json
    result = collect(city_key)
    print(json.dumps(result, indent=2))
