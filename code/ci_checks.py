"""CI validation checks run by .github/workflows/tests.yml."""
import csv
import sys


def check_csv_headers():
    with open("docs/care_capacity_scores.csv") as f:
        headers = next(csv.reader(f))
    bad = [h for h in headers if "/10k" in h.lower()]
    if bad:
        print("FAIL: Score column has raw unit in header:", bad)
        sys.exit(1)
    print("CSV headers OK")


def check_data_parity():
    paths = ["outputs/care_capacity_scores.csv", "docs/care_capacity_scores.csv"]
    for path in paths:
        with open(path) as f:
            n = sum(1 for line in f if line.strip()) - 1
        if n != 69:
            print(f"FAIL: Expected 69 cities in {path}, got {n}")
            sys.exit(1)
        print(f"{path}: {n} cities OK")


if __name__ == "__main__":
    check_csv_headers()
    check_data_parity()
