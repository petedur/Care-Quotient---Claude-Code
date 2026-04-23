"""
Pipeline: collect → ETL for all configured cities.

Usage:
    python code/pipeline.py              # run all cities
    python code/pipeline.py nyc chicago  # run specific cities
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from config import CITIES
from collectors import nonprofit_density, residential_stability, library_density
import etl


def run_city(city_key: str):
    print(f"\n{'='*50}")
    print(f"  Collecting: {CITIES[city_key]['name']}")
    print(f"{'='*50}")

    collectors = [
        nonprofit_density.collect,
        residential_stability.collect,
        library_density.collect,
    ]

    for collector in collectors:
        try:
            collector(city_key)
        except FileNotFoundError as e:
            print(f"  SKIPPED — data file missing: {e}")
        except Exception as e:
            print(f"  ERROR in {collector.__module__}: {e}")


def main():
    target_cities = sys.argv[1:] if len(sys.argv) > 1 else list(CITIES.keys())

    for city_key in target_cities:
        if city_key not in CITIES:
            print(f"Unknown city key '{city_key}'. Valid options: {list(CITIES.keys())}")
            continue
        run_city(city_key)

    print("\n\nRunning ETL → DuckDB…")
    etl.run()
    print("\nDone.")


if __name__ == "__main__":
    main()
