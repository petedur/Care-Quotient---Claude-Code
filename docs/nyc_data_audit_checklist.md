# NYC Data Audit Checklist

**Date**: [Fill in]  
**City**: New York City, NY  
**Auditor**: Peter Durand  

Use this checklist to verify data availability for each metric. For each metric:
- **Available?**: ✓ (yes), ✗ (no), ? (uncertain - needs investigation)
- **Difficulty**: Low (download/API), Medium (some processing), High (complex/manual)
- **Notes**: URL, access method, any issues

---

## Pillar 1: Social Support & Connection

| Metric | Available? | Difficulty | Notes |
|--------|------------|------------|-------|
| Volunteering rate (% of pop) | ? | Medium | Check Census CEVS or NYC Dept of Youth & Community Development |
| Social-connection nonprofit density | ✓ | Low | IRS EO BMF (filter NTEE A/B/P for NYC) |
| Library usage per capita | ✓ | Low | IMLS Public Libraries Survey (NYC library system data) |
| Residential stability (% in same home ≥2 years) | ✓ | Low | Census ACS API (borough-level) |
| **Community sentiment** (optional) | ? | High | Twitter/X API (keywords: "NYC care", "New York community") |

---

## Pillar 2: Institutions of Care

| Metric | Available? | Difficulty | Notes |
|--------|------------|------------|-------|
| Human-service nonprofit density | ✓ | Low | IRS EO BMF (filter NTEE D/E/F for NYC) |
| Community health center density | ✓ | Low | HRSA directory (search NYC zip codes) |
| Senior services (count or density) | ✓ | Medium | NYC Dept for the Aging (public data portal) |
| Child care/youth services (count) | ✓ | Medium | NYC Dept of Education (child care licensing) |
| Faith-based participation (count/density) | ✓ | Low | IRS EO BMF (filter NTEE P for NYC) |

---

## Pillar 3: Responsiveness

| Metric | Available? | Difficulty | Notes |
|--------|------------|------------|-------|
| 311 closure time (median) | ✓ | Low | NYC Open Data: 311 Service Requests dataset |
| Crisis service access (mental health, DV) | ✓ | Medium | NYC Dept of Health (crisis services data) |
| Service utilization rate | ? | Hard | May need administrative data or surveys |

---

## Key NYC Data Sources to Check

1. **NYC Open Data Portal**: https://opendata.cityofnewyork.us/
   - 311 Service Requests
   - Demographics
   - Permits
   - Health data

2. **IRS EO BMF**: https://www.irs.gov/charities-non-profits/form-990-series-downloads
   - Download latest CSV
   - Filter for New York, NY

3. **Census API**: https://api.census.gov/data.html
   - Get free API key
   - ACS 5-year data for NYC

4. **IMLS Libraries**: https://www.imls.gov/research-tools/data-tools
   - Public Libraries Survey

5. **HRSA Health Centers**: https://findahealthcenter.hrsa.gov/
   - Searchable by location

6. **NYC Government Sites**:
   - Dept for the Aging: https://www.nyc.gov/site/dfta/index.page
   - Dept of Health: https://www.nyc.gov/site/doh/index.page
   - Dept of Education: https://www.nyc.gov/site/education/index.page

---

## Audit Instructions

1. **Visit each data source** listed above
2. **Search for the metric** (e.g., in NYC Open Data, search "311")
3. **Check accessibility**: Can you download/export the data? Is it API-accessible?
4. **Note any barriers**: Login required? Fee? Outdated data?
5. **Estimate difficulty**: How much coding/cleaning needed?

**Goal**: By end of audit, know which metrics are "ready to collect" vs. "need workarounds" vs. "skip for Phase 1"

**Output**: Update this checklist and save as `docs/nyc_data_audit_[date].md`

---

## Next Steps After Audit

- **If most metrics are available**: Proceed to Week 2 (build collectors)
- **If gaps found**: Note workarounds or Phase 2 extensions
- **Share findings**: We'll use this to prioritize which collectors to build first