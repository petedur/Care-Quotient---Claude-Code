# NYC Data Audit — Completed

**Date**: April 23, 2026  
**City**: New York City, NY  
**Status**: Audit complete. All V1 sources confirmed and downloaded.

---

## V1 Scored Metrics — Status

| Metric | Source | Status | Notes |
|--------|--------|--------|-------|
| Residential stability (% same home 1+ yr) | Census ACS API (B07003) | **LIVE** | Borough-level via API; 88.47% city-wide |
| Human-services nonprofit density (NTEE P) | IRS EO BMF Region 1 CSV | **LIVE** | City-name filter covers all 5 boroughs |
| Health/mental health/food nonprofit density (NTEE E/F/K) | IRS EO BMF Region 1 CSV | **LIVE** | Same file, filtered by NTEE prefix |
| Faith-based org density (NTEE X) | IRS EO BMF Region 1 CSV | **LIVE** | 7,770 orgs in NYC |
| Library locations per 100k | IMLS PLS FY2023 outlet CSV | **LIVE** | 174 outlets; 2.09 per 100k |
| Library visits per capita | IMLS PLS FY2023 AE CSV | **LIVE** | 2.79 visits/capita |
| Health center density (FQHCs) | HRSA Service Delivery xlsx | **LIVE** | 411 FQHCs; 4.93 per 100k |

---

## Deferred / Out of Scope for V1

| Metric | Status | Notes |
|--------|--------|-------|
| Volunteering rate | Deferred | No reliable city-level national source |
| 311 closure time | Deferred | Not available cross-city from national source |
| Crisis service access | Deferred | Fragmented across agencies; not national |
| Community sentiment | Deferred | Experimental; excluded from scored baseline |
| Senior services count | Deferred | No clean national source identified |
| Child care density | Deferred | State licensing data varies; not national |

---

## Downloaded Data Files

| File | Location |
|------|----------|
| IRS EO BMF Region 1 (Northeast) | `Downloaded Data/IRS EO BMF/Region 1_Northeast_4.21.26.csv` |
| IRS EO BMF Region 2 (Mid-Atlantic/Great Lakes) | `Downloaded Data/IRS EO BMF/Region 2_Mid-Atlantic and Great Lakes_4.21.26.csv` |
| IRS EO BMF Region 3 (Gulf Coast/Pacific) | `Downloaded Data/IRS EO BMF/Region 3_Gulf Coast and Pacific Coast_4.21.26.csv` |
| IMLS Outlet FY2023 | `Downloaded Data/Public Libraries Survey (PLS)/pls_fy23_outlet_pud23i.csv` |
| IMLS Administrative Entity FY2023 | `Downloaded Data/Public Libraries Survey (PLS)/PLS_FY23_AE_pud23i.csv` |
| HRSA Health Centers | `Downloaded Data/Health_Center_Service_Delivery_and_LookAlike_Sites.xlsx` |
| Census API key | Stored in `.env` (not in source control) |
