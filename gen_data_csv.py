"""Generate docs/care_capacity_data.csv — journalist-facing long-format data file."""
import json, csv, sys
sys.stdout.reconfigure(encoding='utf-8')

SOURCE_META = {
    "Residential Stability Score (0-100)": {
        "unit": "% of population in same home 1+ year",
        "benchmark": "95%",
        "source": "U.S. Census Bureau, ACS 5-year estimates (B07003)",
        "vintage": "2022 (2018-2022 pooled)",
    },
    "Care Nonprofits Score (0-100)": {
        "unit": "organizations per 10,000 residents (NTEE P+E+F+K)",
        "benchmark": "25 per 10,000",
        "source": "IRS Exempt Organizations Business Master File (EO BMF)",
        "vintage": "April 2026",
    },
    "Library Density Score (0-100)": {
        "unit": "public library outlets per 100,000 residents",
        "benchmark": "5 per 100,000",
        "source": "IMLS Public Libraries Survey",
        "vintage": "FY2023",
    },
    "Religious Institution Density Score (0-100)": {
        "unit": "congregations per 100,000 residents",
        "benchmark": "150 per 100,000",
        "source": "ARDA U.S. Religion Census",
        "vintage": "2020",
    },
    "FQHC Density Score (0-100)": {
        "unit": "Federally Qualified Health Centers per 100,000 residents",
        "benchmark": "15 per 100,000",
        "source": "HRSA Health Center Service Delivery and Look-Alike Sites",
        "vintage": "2025/2026",
    },
    "Nursing Home Capacity Score (0-100)": {
        "unit": "Medicare/Medicaid certified beds per 1,000 residents aged 65+",
        "benchmark": "50 per 1,000 residents 65+",
        "source": "CMS Care Compare — Nursing Home Provider Information",
        "vintage": "April 2026",
    },
    "Child Care Capacity Score (0-100)": {
        "unit": "licensed child care establishments per 1,000 children under 5",
        "benchmark": "15 per 1,000 children under 5",
        "source": "U.S. Census Bureau, County Business Patterns (NAICS 624410)",
        "vintage": "2022",
    },
    "Public Coverage Reach Proxy Score (0-100)": {
        "unit": "ACS-based coverage rate among 0-149% FPL residents (Medicaid/CHIP)",
        "benchmark": "100% (note: 31 of 69 cities hit ceiling due to CHIP enrollment above FPL denominator)",
        "source": "U.S. Census Bureau, ACS 5-year estimates (C27007, C17002)",
        "vintage": "2022 (2018-2022 pooled)",
    },
    "Housing Affordability Score (0-100)": {
        "unit": "% of households not spending >30% of income on housing",
        "benchmark": "90% not cost-burdened",
        "source": "U.S. Census Bureau, ACS 5-year estimates (B25070, B25091)",
        "vintage": "2022 (2018-2022 pooled)",
    },
    "SNAP Coverage Score (0-100)": {
        "unit": "estimated SNAP participation rate among likely-eligible households (0-149% FPL)",
        "benchmark": "85% (USDA FNS national target)",
        "source": "U.S. Census Bureau, ACS 5-year estimates (B22001, C17002)",
        "vintage": "2022 (2018-2022 pooled)",
    },
    # Healthcare Coverage legacy key (if still present in JSON)
    "Healthcare Coverage Score (0-100)": {
        "unit": "ACS-based coverage rate among 0-149% FPL residents (Medicaid/CHIP)",
        "benchmark": "100% (note: 31 of 69 cities hit ceiling due to CHIP enrollment above FPL denominator)",
        "source": "U.S. Census Bureau, ACS 5-year estimates (C27007, C17002)",
        "vintage": "2022 (2018-2022 pooled)",
    },
}

with open('outputs/care_capacity_scores.json', encoding='utf-8') as f:
    data = json.load(f)

rows = []
for city, city_data in data.items():
    cq = city_data.get('cq') or city_data.get('care_quotient')
    p1 = city_data.get('pillar1') or city_data.get('pillar1_social_relational_care')
    p2 = city_data.get('pillar2') or city_data.get('pillar2_institutional_care')
    p3 = city_data.get('pillar3') or city_data.get('pillar3_economic_access')
    for metric_name, metric_data in city_data.get('metrics', {}).items():
        meta = SOURCE_META.get(metric_name, {})
        rows.append({
            'city': city,
            'care_quotient': cq,
            'pillar': metric_data.get('pillar', ''),
            'metric': metric_name,
            'raw_value': metric_data.get('raw_value', ''),
            'raw_unit': meta.get('unit', ''),
            'benchmark': meta.get('benchmark', metric_data.get('benchmark', '')),
            'score_0_100': metric_data.get('score', ''),
            'source': meta.get('source', ''),
            'vintage': meta.get('vintage', ''),
        })

rows.sort(key=lambda r: (-float(r['care_quotient'] or 0), r['city'], r['metric']))

with open('docs/care_capacity_data.csv', 'w', newline='', encoding='utf-8') as f:
    writer = csv.DictWriter(f, fieldnames=['city','care_quotient','pillar','metric','raw_value','raw_unit','benchmark','score_0_100','source','vintage'])
    writer.writeheader()
    writer.writerows(rows)

print(f'Written {len(rows)} rows ({len(data)} cities x {len(rows)//len(data)} metrics)')
