"""
Pipeline: collect → ETL for all configured cities.

Usage:
    python code/pipeline.py                      # run all cities, use cached data
    python code/pipeline.py nyc chicago          # run specific cities
    python code/pipeline.py --refresh            # force re-download from all APIs
    python code/pipeline.py --auto-only          # skip collectors that need manual downloads
    python code/pipeline.py --auto-only --refresh nyc  # combine flags

Flags:
    --refresh     Force all collectors to re-download from their data sources,
                  ignoring any locally cached files. Useful when source data
                  has been updated upstream.
    --auto-only   Run only collectors that fetch data automatically (Census API
                  and CMS). Skips collectors that require manual file downloads
                  (IRS EO BMF, HRSA, IMLS). Used by the GitHub Actions workflow.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from config import CITIES
from collectors import (
    nonprofit_density, residential_stability, library_density, health_centers,
    housing_cost_burden, snap_participation, health_insurance_coverage,
    nursing_homes,
)
import etl
import score as scorer

# Collectors that fetch data automatically (no manual file download required).
# These can run in CI / GitHub Actions given only a CENSUS_API_KEY secret.
AUTO_COLLECTORS = [
    residential_stability.collect,
    housing_cost_burden.collect,
    snap_participation.collect,
    health_insurance_coverage.collect,
    nursing_homes.collect,
]

# Collectors that require manually downloaded files.
# IRS EO BMF (~200MB), HRSA Excel, and IMLS Excel are too large or not
# scriptable enough to download automatically in CI.
MANUAL_COLLECTORS = [
    nonprofit_density.collect,
    library_density.collect,
    health_centers.collect,
]


def run_city(city_key: str, collectors: list, force_refresh: bool = False):
    print(f"\n{'='*50}")
    print(f"  Collecting: {CITIES[city_key]['name']}")
    print(f"{'='*50}")

    for collector in collectors:
        try:
            # Pass force_refresh to collectors that support it.
            # Collectors that don't accept the kwarg are called without it.
            try:
                collector(city_key, force_refresh=force_refresh)
            except TypeError:
                collector(city_key)
        except FileNotFoundError as e:
            print(f"  SKIPPED — data file missing: {e}")
        except Exception as e:
            print(f"  ERROR in {collector.__module__}: {e}")


def main():
    args = sys.argv[1:]

    force_refresh = "--refresh" in args
    auto_only     = "--auto-only" in args
    args = [a for a in args if not a.startswith("--")]

    collectors = AUTO_COLLECTORS if auto_only else AUTO_COLLECTORS + MANUAL_COLLECTORS

    if auto_only:
        print("Running auto-download collectors only (--auto-only).")
    if force_refresh:
        print("Force-refreshing all data sources (--refresh).")

    target_cities = args if args else list(CITIES.keys())

    for city_key in target_cities:
        if city_key not in CITIES:
            print(f"Unknown city key '{city_key}'. Valid options: {list(CITIES.keys())}")
            continue
        run_city(city_key, collectors, force_refresh=force_refresh)

    print("\n\nRunning ETL -> DuckDB...")
    etl.run()

    print("\n\nScoring...")
    scorer.run()

    print("\nDone.")


if __name__ == "__main__":
    main()
