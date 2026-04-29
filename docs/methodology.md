# Care Quotient: Methodology

**Version**: 3.0 (V3)
**Date**: April 2026  
**Author**: Peter Durand

---

## 1. What This Index Measures

The Care Quotient (CQ) measures **care capacity** — the extent to which a community has the social ties, institutions, and systems needed to support people in moments of vulnerability.

This is explicitly **not** a quality-of-life index. A city can score well on income, safety, and health outcomes while having thin care infrastructure for its most vulnerable residents. The inverse is also true. The CQ separates these two dimensions and measures only the latter.

The motivating question is whether communities have what it takes to *show up* — through networks, institutions, and reach — when people need help.

**V3 scope**: This document describes V3, covering 68 US cities across 6 scored metrics organized into 3 pillars. V3 expands on V2 by: (1) scaling geographic coverage from 5 to 68 cities using ZCTA-to-place crosswalk filtering (Census 2020), (2) correcting the SNAP eligibility denominator from 100% FPL to 0–149% FPL using Census C17002 variables, (3) collapsing the two nonprofit metrics (NTEE P and E/F/K) into a single combined care nonprofit metric after factor analysis showed r=0.85 correlation, and (4) revising within-pillar weights based on empirical factor loadings. V2 covered 5 cities; V1 covered 4 metrics and 2 pillars. Scores should be read as "this city has stronger or weaker care capacity than the benchmark" rather than as definitive rankings.

---

## 2. Three Scored Pillars

### Pillar 1: Social Fabric (40% of CQ)
The relational layer: whether the conditions for community care exist — stable residential networks and a housing market that allows people to stay embedded in their communities.

### Pillar 2: Institutions of Care (35% of CQ)
The organizational layer: whether institutions exist that are specifically designed to absorb distress — care-oriented nonprofits and federally qualified health centers.

### Pillar 3: Reach (25% of CQ)
The access layer: whether care systems actually connect with the people who need them — measuring reach, not just presence.

**Inter-pillar weight rationale (40/35/25)**: Care ethics theory (Gilligan 1982, Noddings 1984) holds that caring is fundamentally relational — the social fabric is the primary form of caring. Nussbaum's capabilities approach counters that institutional infrastructure is a necessary condition for caring to be meaningful at scale. Pillar 3 adds a direct measure of whether infrastructure actually reaches people. The 40/35/25 split is retained from V2; V4 will revisit once the Medicaid/CHIP metric replacement is implemented.

**V3 structural change**: V2 placed Human Services nonprofits (NTEE P) in Pillar 1 and Health/MH/Food nonprofits (NTEE E/F/K) in Pillar 2 as conceptually distinct dimensions. Factor analysis across 71 cities showed these two metrics correlate at r=0.85 and load on the same empirical factor — cities with high NTEE P density also have high NTEE E/F/K density, making the pillar distinction unsupported by the data. V3 collapses them into a single combined care nonprofit density metric (P+E+F+K) in Pillar 2. The individual sub-components are retained as diagnostics. Pillar 1 is simplified to the two housing/stability metrics, which the factor analysis confirmed form a distinct dimension.

---

## 3. Scored Metrics, Data Sources, and Weight Rationale

### Pillar 1: Social Fabric

#### 3.1 Residential Stability
**Definition**: Percentage of population living in the same home for one or more years (Census ACS variable B07003_004E).  
**Source**: U.S. Census Bureau, American Community Survey 5-year estimates (2022).  
**Unit**: % of population (higher = more stable = better).  
**Weight within Pillar 1**: **65%**

**Rationale**: Residential stability is one of the most consistently documented predictors of social capital in the social science literature. Putnam (2000) identifies it as a primary structural driver of civic engagement, community trust, and collective action. Sampson, Raudenbush & Earls (1997) demonstrate that stable residential communities develop "collective efficacy" — a shared capacity and willingness to intervene on behalf of neighbors — which directly predicts mutual support behaviors. Briggs (1998) shows that stable residents maintain significantly stronger social networks and are far more likely to provide and receive informal care.

This metric receives the highest weight in Pillar 1 because it is the structural precondition for all other forms of social caring. V3 factor analysis confirmed this as the dominant signal in the Social Fabric dimension (loading 0.70), supporting the increase from the V2 weight of 48%.

#### 3.2 Housing Affordability (% Not Cost-Burdened)
**Definition**: Percentage of households NOT spending more than 30% of income on housing costs, combining renter-occupied (Census B25070) and owner-occupied (Census B25091) units.  
**Source**: U.S. Census Bureau, American Community Survey 5-year estimates (2022).  
**Unit**: % of households not cost-burdened (higher = better).  
**Weight within Pillar 1**: **35%**

**Rationale**: This metric functions as a counter-weight to residential stability rather than an independent dimension. Agha et al. (2024) demonstrate that housing cost burden's effect on social capital is mediated through residential stability — financial stress suppresses community participation and network formation. Desmond's research establishes that high cost burden triggers eviction risk, forced moves, and erosion of care networks. A city with high residential stability but high cost burden is rewarding forced immobility rather than genuine community embeddedness.

V3 factor analysis showed housing cost burden loads cleanly alongside residential stability as a distinct housing/stability dimension, supporting a weight increase from 12% (V2) to 35% (V3).

**Measurement note**: This metric uses households where cost-as-percentage-of-income was computable (income > 0). Households with zero or negative income are excluded as "not computed" by Census. This produces lower apparent cost burden rates than commonly cited figures, which typically use different computation methods. Relative city rankings are still valid; absolute percentages should not be compared to external sources without this caveat.

**Benchmark**: 90% not burdened (10% burdened ceiling). Only the least cost-burdened US cities achieve this level.

---

### Pillar 2: Institutions of Care

#### 3.3 Combined Care Nonprofit Density (NTEE P + E + F + K)
**Definition**: Registered 501(c)(3) organizations with NTEE major groups P (Human Services), E (Health), F (Mental Health and Crisis Intervention), or K (Food, Agriculture, and Nutrition) per 10,000 residents.  
**Source**: IRS Exempt Organizations Business Master File (EO BMF), filtered by NTEE first characters P, E, F, or K.  
**Unit**: orgs per 10,000 residents (higher = better).  
**Weight within Pillar 2**: **50%**

**Rationale**: In V2, NTEE P (Human Services) and NTEE E/F/K (Health, Mental Health, Food) were scored as separate metrics in separate pillars. V3 factor analysis across 68 cities showed these two metrics correlate at r=0.85 and load on the same empirical factor — cities with high NTEE P density also have high NTEE E/F/K density. The pillar distinction was unsupported by the data. V3 collapses them into a single combined metric.

Salamon & Anheier (1998) establish nonprofit density as a structural indicator of civil society capacity. Kim & Jennings (2012) find that nonprofit human service density correlates with lower poverty rates and better health outcomes. Boris & Steuerle (2006) document the direct link between human-service nonprofit presence and care provision for vulnerable populations.

**Exclusions**: Arts/culture (NTEE A), education (NTEE B), and broad religious organizations (NTEE X, except X3x) are excluded. These categories correlate with affluence rather than care capacity. The individual NTEE P and E/F/K sub-components are retained as diagnostic metrics.

**Benchmark**: 25 per 10,000 residents. Raised from 15/10k (V2) after 50%+ of cities hit the ceiling under county-based geographic filtering. ZCTA-based filtering reduces raw counts; 25/10k maintains meaningful discrimination for top performers.

#### 3.4 Community Health Center Density (FQHCs)
**Definition**: Active Federally Qualified Health Center service delivery sites per 100,000 residents.  
**Source**: HRSA Health Center Service Delivery and Look-Alike Sites dataset, filtered to active FQHCs (excluding Look-Alike sites) with service delivery functions.  
**Unit**: FQHCs per 100,000 residents (higher = better).  
**Weight within Pillar 2**: **50%**

**Rationale**: FQHCs carry the strongest evidence base of any metric in this index. Rosenbaum et al. (2011) demonstrate that FQHC access significantly reduces emergency room utilization among low-income and uninsured patients. Shi and colleagues (multiple studies, 2001–2017) link FQHC access to reduced mortality from chronic disease, improved preventive care uptake, and reduced health disparities across racial and income lines. Congressional Budget Office analyses consistently find that FQHCs save approximately $2,371 per user in avoided emergency care costs. Unlike density measures for nonprofits, FQHCs have federal funding and reporting requirements that make their service delivery more verifiable.

#### 3.5 Faith-Based Human Services — Diagnostic Only (Not Scored)
**Definition**: Registered 501(c)(3) organizations with NTEE prefix X3 per 10,000 residents.  
**Source**: IRS EO BMF, filtered by NTEE prefix "X3".  
**Unit**: orgs per 10,000 residents (reported, not scored).

**Why excluded**: IRS NTEE code X30 functions as a catch-all that captures congregations alongside human-service providers. The category is dominated by congregations whose primary identity is devotional rather than service-oriented. Many faith organizations that *do* primarily deliver social services register under P or E/K instead. V4 will explore combining X3x with faith-affiliated P/E/K registrations for a more complete measure.

---

### Pillar 3: Reach

#### 3.6 SNAP Coverage Rate
**Definition**: Ratio of SNAP-receiving households to estimated eligible households, normalized to 0–100. Approximates participation among the likely-eligible population.  
**Formula**: (SNAP households / total households) ÷ (population at 0–149% FPL / total population) × 100, capped at 100.  
**Source**: U.S. Census Bureau, ACS 5-year estimates (2022). B22001 (SNAP receipt), C17002 (ratio of income to poverty level by band).  
**Unit**: % coverage (higher = better).  
**Weight within Pillar 3**: **35%**

**Rationale**: SNAP coverage rate measures whether food assistance infrastructure actually reaches the population likely eligible for SNAP — the most direct measure of care system reach available from national data. A high SNAP rate relative to the eligible population indicates the system is connecting eligible people to food support. Normalized by an approximated eligibility rate to avoid rewarding cities with high poverty for high SNAP volume. The 35% weight reflects the finding from V3 factor analysis that health insurance is the dominant signal in the Reach dimension (factor loading 0.84), with SNAP as an independent but secondary signal (r=0.33 with health insurance). SNAP eligibility rules are federal and consistent, making the coverage denominator more interpretable than health insurance eligibility.

**Eligibility denominator (V3 update)**: SNAP eligibility is federally defined at 130% of the Federal Poverty Level (FPL). Census ACS does not provide county-level population at exactly 130% FPL, but C17002 provides population counts by income-to-poverty ratio bands. Summing four bands — under 0.50 FPL (C17002_002E), 0.50–0.99 FPL (C17002_003E), 1.00–1.24 FPL (C17002_004E), and 1.25–1.49 FPL (C17002_005E) — yields the 0–149% FPL population, the closest available Census approximation to the 130% FPL eligibility threshold. This replaces the V2 method of using B17001 (population at 100% FPL), which understated the eligible denominator by excluding the 100–130% FPL population and overstated coverage rates in cities with large near-poverty populations.

#### 3.7 Health Insurance Coverage Rate
**Definition**: Percentage of the civilian noninstitutional population with any health insurance coverage.  
**Source**: U.S. Census Bureau, ACS 5-year estimates (2022). B27001 (health insurance coverage status by sex by age). Computed as (total population − total uninsured) / total population × 100.  
**Unit**: % insured (higher = better).  
**Weight within Pillar 3**: **65%**

**Rationale**: Health insurance coverage is a direct measure of whether people can access health systems when they need care. Low coverage reflects structural barriers to healthcare access that persist regardless of FQHC density. The 40% weight is slightly lower than SNAP because coverage reflects a combination of local care infrastructure and state-level insurance policy (Medicaid expansion status): a city in a non-Medicaid-expansion state will score lower due to state policy choices. This is intentional — a state's decision not to expand Medicaid is a real policy failure that meaningfully reduces care access for residents, and the index reflects it as such. Cities are not scored independently of the policy environment in which their residents live.

**Benchmark**: 95% — near-universal coverage. States with full Medicaid expansion and strong marketplace enrollment achieve 94–97% coverage.

---

## 4. Normalization Method

Raw metric values are scored against **absolute benchmarks** representing theoretical ideals — the level at which a city would be considered to fully meet that dimension of care need:

```
score = min(value / benchmark × 100, 100)
```

A city at or above the benchmark receives 100. A city at half the benchmark receives 50. Scores are capped at 100.

| Metric | Benchmark | Rationale |
|--------|-----------|-----------|
| Residential stability | 95% | Near-zero involuntary displacement; ~5% natural annual mobility |
| Housing affordability | 90% not burdened | 10% cost-burden ceiling; only the least-burdened US cities achieve this |
| Care nonprofits (NTEE P+E+F+K) | 25 per 10,000 | Factor analysis showed NTEE P and E/F/K load on one dimension (r=0.85); collapsed into a single combined metric. 25/10k raised from 15/10k to restore discrimination after ZCTA-based filtering reduced county inflation |
| FQHC density | 15 per 100,000 | Eliminates HRSA shortage designation plus geographic redundancy |
| SNAP coverage rate | 85% | USDA FNS national SNAP participation target among eligible households |
| Health insurance coverage | 95% | Near-universal coverage; achievable in Medicaid-expansion states |

**Advantage over min-max scaling**: Scores are absolute — adding or removing cities does not change existing scores. A city's score reflects its performance against a standard, not against whoever else is in the comparison set.

---

## 5. Care Quotient Calculation

The Care Quotient (CQ) is a weighted composite of six scored metrics, computed in two steps.

**Step 1 — Pillar scores** (weighted averages of constituent metrics):

```
Pillar 1 (Social Fabric)        = (residential_stability × 0.65) + (housing_affordability × 0.35)
Pillar 2 (Institutions of Care) = (combined_care_NPs × 0.50)     + (fqhc_density × 0.50)
Pillar 3 (Reach)                = (health_insurance × 0.65)      + (snap_coverage × 0.35)
```

**Step 2 — Care Quotient**:

```
CQ = (Pillar 1 × 0.40) + (Pillar 2 × 0.35) + (Pillar 3 × 0.25)
```

All metric scores are on a 0–100 scale against absolute benchmarks (Section 4), so the CQ is also 0–100.

**Weight rationale (V3)**: Pillar 1 and 2 weights are derived from factor analysis across 68 cities. Within Pillar 1, residential stability dominates (factor loading 0.70); housing burden is a necessary counter-weight (raised from 12% to 35%). Within Pillar 2, NTEE P and E/F/K collapsed into a single combined metric after confirming r=0.85 correlation. Within Pillar 3, health insurance is the dominant signal (factor loading 0.84). V4 will derive inter-pillar weights empirically via regression against care outcome variables.

**Individual metric scores remain the primary diagnostic output.** The CQ is a useful summary for comparison, but it compresses variation — a city can score at the CQ average while being strong on one pillar and weak on another.

---

## 6. Diagnostic Metrics (Not Scored)

The following metrics are collected and reported but excluded from pillar scores:

| Metric | Rationale for exclusion |
|--------|-------------------------|
| Library density (per 100k) | Libraries are valuable community infrastructure but not primarily care institutions. Including them would conflate general civic amenity with care capacity. |
| Library visits per capita | Same rationale. Reported as a supplementary community engagement signal. |
| All care-related nonprofit density | Broad diagnostic count across all NTEE care codes. Useful for context but too aggregated to score; double-counts organizations captured in the scored sub-metrics. |
| Faith-based orgs (X3x, per 10k) | NTEE X30 captures congregations, not specifically care providers. See Section 3.5. |

---

## 7. What Is Excluded and Why

| Category | Reason for exclusion |
|----------|----------------------|
| Arts & culture (NTEE A) | Correlates with affluence, not care. Would reward wealthy cities. |
| Education (NTEE B) | Same — private schools, universities inflate this in high-income cities. |
| All religious orgs (NTEE X broad) | Too noisy; includes purely devotional organizations with no care function. |
| General health outcomes | Outcome metric, not capacity metric. Measuring life expectancy would turn this into a conditions index. |
| Economic conditions | Out of scope by design; care capacity is distinct from prosperity. |

---

## 8. Data Sources

| Source | Coverage | Update frequency | Access |
|--------|----------|-----------------|--------|
| IRS EO BMF | All 50 states | Periodic (check IRS site) | Public download |
| Census ACS 5-year | All counties | Annual | Free API |
| IMLS Public Libraries Survey | National | Annual | Public download |
| HRSA Health Center Service Delivery | National | Periodic | Public download |

All four sources are national, free, and scriptable. No city-specific open data portals are required for the V2 scored baseline.

---

## 9. Known Limitations

1. **Per-capita density systematically disadvantages large cities**: NYC has 437 FQHCs and thousands of nonprofits — enormous absolute capacity — but scores below the median on both density metrics because its population of 8.3M dilutes per-capita ratios. A city of 180k with 44 FQHCs scores higher per capita than a city of 8M with 437 FQHCs, even though the latter has roughly 10x the infrastructure. Whether this is correct depends on how access scales with density: in a compact, transit-connected city, per-capita ratios may overstate deprivation if geographic proximity compensates. This is not unique to NYC — all large dense cities (Chicago, Philadelphia, Los Angeles) face the same structural penalty. V4 will explore supplementing per-capita density with geographic access metrics (% of population within X distance of a facility). For now, scores for cities above ~1M population should be read with this caveat in mind.

2. **Benchmark judgment**: Nonprofit density benchmark (combined P+E+F+K at 25/10k) and SNAP/health insurance benchmarks are reasoned thresholds without a policy-derived standard. The FQHC and residential stability benchmarks are more firmly grounded. All benchmarks are documented explicitly and subject to revision.

3. **IRS data lag**: EO BMF data may lag registrations by 1–2 years. Inactive organizations may remain registered.

4. **Geographic filtering**: All data sources use the Census 2020 ZCTA-to-Place relationship file to define city boundaries. A ZCTA is assigned to a city if ≥50% of its land area falls within the Census incorporated place boundary. This eliminates county-sharing inflation (e.g., Atlanta pulled all of Fulton+DeKalb counties in V2) but may exclude ZCTAs that straddle city limits even when substantially urban.

5. **Faith-based measurement**: X30 codes capture congregations, not specifically human-service providers. Faith-based density is reported as a diagnostic metric rather than scored (see Section 3.5).

6. **Density vs. access**: Per-capita density measures presence, not accessibility. A health center in one part of a large city does not serve all residents equally.

7. **Residential stability: chosen vs. forced immobility**: High residential stability can reflect embedded social networks (Putnam 2000; Sampson et al. 1997), but it can equally reflect economic immobility — poverty traps and exclusionary housing markets that prevent people from leaving even when conditions are poor. The housing affordability counter-weight (Section 3.2) partially addresses this, but Census ACS data cannot fully distinguish chosen from forced stability.

8. **Housing cost burden undercount**: The Census B25070/B25091 methodology excludes households with zero or negative income ("not computed"), which can understate true cost burden rates compared to HUD CHAS figures. Relative city rankings are valid; absolute percentages should not be compared to external sources without this caveat.

9. **Health insurance and state policy**: Health insurance coverage reflects state-level Medicaid expansion decisions as much as local care infrastructure. Texas (Houston) did not expand Medicaid under the ACA, which contributes significantly to its lower score on this metric. This is treated as a real care access failure attributable to the state — see Section 3.7 rationale.

10. **SNAP eligibility approximation**: The V2 SNAP formula used B17001 (100% FPL poverty population) as the eligibility denominator. V3 replaces this with the 0–149% FPL population derived from C17002 bands, which more accurately approximates the 130% FPL SNAP eligibility threshold. Coverage rates will be modestly lower under V3 in cities with large near-poverty populations.

---

## 10. V3 Changes (Implemented)

The following improvements were implemented in V3:

- **Scale to 68 cities**: ZCTA-to-place crosswalk filtering replaces city-name matching across IRS, IMLS, and HRSA datasets. Eliminates name-matching errors and county-sharing inflation.
- **ZCTA-based geographic filtering**: All data sources (IRS EO BMF, IMLS, HRSA, Census ACS) now use the Census 2020 ZCTA-to-Place relationship file to define city boundaries consistently. A ZCTA is assigned to a city if ≥50% of its land area falls within the Census incorporated place boundary.
- **SNAP eligibility denominator corrected**: C17002 (0–149% FPL) replaces B17001 (100% FPL) as the SNAP coverage denominator. See Section 3.6.
- **Nonprofit metrics collapsed**: Factor analysis across 68 cities showed NTEE P and NTEE E/F/K correlate at r=0.85 and load on the same factor. Collapsed into a single combined care nonprofit metric (P+E+F+K) in Pillar 2. Sub-components retained as diagnostics.
- **Within-pillar weights revised**: Empirical factor loadings used to update weights. Residential stability raised from 48% to 65%; housing affordability raised from 12% to 35%; health insurance raised from 40% to 65%; SNAP lowered from 60% to 35%.
- **NP benchmark raised**: Combined care NP benchmark raised from 15/10k to 25/10k to restore score discrimination after ZCTA-based filtering reduced county-inflated counts.

## 11. Planned V4 Improvements

- **Medicaid/CHIP metric**: Evaluate replacing health insurance coverage (B27001) with Medicaid/CHIP enrollment (B27007) to isolate public program reach from employer-based coverage.
- **Empirical inter-pillar weight adoption**: Review factor analysis outputs against the V3 68-city dataset and decide whether to adopt empirically-derived inter-pillar weights (currently judgment-based at 40/35/25).
- **Scale to 100 cities**: Add the remaining ~32 cities to reach the 100-city target.
- **Faith-based measurement**: Explore combining X3x with faith-affiliated P/E/K organizations for a more complete measure.
- **Residential stability cross-reference**: Incorporate Chetty et al. Opportunity Atlas to distinguish chosen from forced stability.
- **FQHC capacity weighting**: Weight health center density by reported patient capacity rather than site count (UDS data).

---

## 12. References

- Agha, G. et al. (2024). Housing stability and social capital: Mediation pathways. *American Journal of Community Psychology*.
- Boris, E.T. & Steuerle, C.E. (2006). *Nonprofits and Government: Collaboration and Conflict*. Urban Institute Press.
- Briggs, X. de S. (1998). Brown kids in white suburbs: Housing mobility and the many faces of social capital. *Housing Policy Debate*, 9(1), 177–221.
- Chaves, M. & Tsitsos, W. (2001). Congregations and social services: What they do, how they do it, and with whom. *Nonprofit and Voluntary Sector Quarterly*, 30(4), 660–683.
- Chetty, R. et al. (multiple years). *Opportunity Atlas*. Opportunity Insights, Harvard University.
- Cnaan, R.A. et al. (2006). *The Other Philadelphia Story: How Local Congregations Support Quality of Life in Urban America*. University of Pennsylvania Press.
- Congressional Budget Office. (multiple years). *Federally Qualified Health Centers: Quality and Costs*.
- Desmond, M. & Bell, M. (multiple years). Housing, poverty, and the law. *Annual Review of Law and Social Science*.
- FEMA. (2023). *Community Resilience Challenges Index: Methodology Report*.
- Johnson, B.R., Tompkins, R.B., & Webb, D. (2002). *Objective Hope: Assessing the Effectiveness of Faith-Based Organizations*. Center for Research on Religion and Urban Civil Society.
- Kim, M. & Jennings, E.T. (2012). Effects of nonprofit human service organizations on well-being in US counties. *Administration & Society*, 44(4), 424–451.
- Pettijohn, S.L. & Boris, E.T. (2013). *Nonprofit-Government Contracts and Grants*. Urban Institute.
- Putnam, R.D. (2000). *Bowling Alone: The Collapse and Revival of American Community*. Simon & Schuster.
- Rosenbaum, S. et al. (2011). *Health Centers: An American Success Story*. George Washington University.
- Salamon, L.M. & Anheier, H.K. (1998). Social origins of civil society. *Voluntas*, 9(3), 213–248.
- Sampson, R.J., Raudenbush, S.W., & Earls, F. (1997). Neighborhoods and violent crime: A multilevel study of collective efficacy. *Science*, 277(5328), 918–924.
- Shi, L. et al. (multiple years). *Community Health Centers and Vulnerable Populations*. Various journals.
- USDA Food and Nutrition Service. (multiple years). *Characteristics of SNAP Households*. Annual report.
