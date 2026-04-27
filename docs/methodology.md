# Care Quotient: Methodology

**Version**: 2.0 (V2)
**Date**: April 2026  
**Author**: Peter Durand

---

## 1. What This Index Measures

The Care Quotient (CQ) measures **care capacity** — the extent to which a community has the social ties, institutions, and systems needed to support people in moments of vulnerability.

This is explicitly **not** a quality-of-life index. A city can score well on income, safety, and health outcomes while having thin care infrastructure for its most vulnerable residents. The inverse is also true. The CQ separates these two dimensions and measures only the latter.

The motivating question is whether communities have what it takes to *show up* — through networks, institutions, and reach — when people need help.

**V2 scope**: This document describes V2, covering 5 cities across 7 scored metrics organized into 3 pillars. V2 expands on V1 (4 metrics, 2 pillars) by adding Pillar 3 (Reach) — whether care systems actually connect with the people who need them — and a housing affordability counter-weight within Pillar 1. Scores should be read as "this city has stronger or weaker care capacity than the benchmark" rather than as definitive rankings.

---

## 2. Three Scored Pillars

### Pillar 1: Social Support and Connection (40% of CQ)
The relational layer: whether people are embedded in networks that can provide support, and whether the housing market enables stable community formation.

### Pillar 2: Institutions of Care (35% of CQ)
The organizational layer: whether institutions exist that are specifically designed to absorb distress.

### Pillar 3: Reach (25% of CQ)
The access layer: whether care systems actually connect with the people who need them — measuring reach, not just presence.

**Inter-pillar weight rationale (40/35/25)**: Care ethics theory (Gilligan 1982, Noddings 1984) holds that caring is fundamentally relational — the social fabric is the primary form of caring. Nussbaum's capabilities approach counters that institutional infrastructure is a necessary condition for caring to be meaningful at scale. Pillar 3 adds a direct measure of whether infrastructure actually reaches people, which is conceptually the most important dimension — but carries the lowest weight in V2 because it has the most methodological immaturity (2 metrics, one affected by state-level insurance policy). The 40/35/25 split will be revisited empirically in V3.

---

## 3. Scored Metrics, Data Sources, and Weight Rationale

### Pillar 1: Social Support and Connection

#### 3.1 Residential Stability
**Definition**: Percentage of population living in the same home for one or more years (Census ACS variable B07003_004E).  
**Source**: U.S. Census Bureau, American Community Survey 5-year estimates (2022).  
**Unit**: % of population (higher = more stable = better).  
**Weight within Pillar 1**: **48%**

**Rationale**: Residential stability is one of the most consistently documented predictors of social capital in the social science literature. Putnam (2000) identifies it as a primary structural driver of civic engagement, community trust, and collective action. Sampson, Raudenbush & Earls (1997) demonstrate that stable residential communities develop "collective efficacy" — a shared capacity and willingness to intervene on behalf of neighbors — which directly predicts mutual support behaviors. Briggs (1998) shows that stable residents maintain significantly stronger social networks and are far more likely to provide and receive informal care.

This metric receives the highest weight in Pillar 1 because it is the structural precondition for all other forms of social caring. Its weight is slightly reduced from V1 (55% → 48%) to accommodate the housing cost burden counter-weight.

#### 3.2 Human Services Nonprofit Density
**Definition**: Registered 501(c)(3) organizations with NTEE major group P (Human Services: community centers, mutual aid, social services, volunteer programs) per 10,000 residents.  
**Source**: IRS Exempt Organizations Business Master File (EO BMF), filtered by NTEE first character "P" and city name.  
**Unit**: orgs per 10,000 residents (higher = better).  
**Weight within Pillar 1**: **40%**

**Rationale**: Salamon & Anheier (1998) establish nonprofit density as a structural indicator of civil society capacity. Boris & Steuerle (2006) document the direct link between human-service nonprofit presence and care provision for low-income and vulnerable populations. However, density does not guarantee accessibility, utilization, or quality. This metric receives a lower weight than residential stability to reflect the indirect nature of the connection between organizational presence and actual care.

**Exclusions**: Arts/culture (NTEE A) and education (NTEE B) organizations are excluded. Both categories correlate strongly with urban affluence — a city with many museums and private schools would score high without that reflecting care capacity.

#### 3.3 Housing Affordability (% Not Cost-Burdened)
**Definition**: Percentage of households NOT spending more than 30% of income on housing costs, combining renter-occupied (Census B25070) and owner-occupied (Census B25091) units.  
**Source**: U.S. Census Bureau, American Community Survey 5-year estimates (2022).  
**Unit**: % of households not cost-burdened (higher = better).  
**Weight within Pillar 1**: **12%**

**Rationale**: This metric functions as a counter-weight to residential stability rather than an independent dimension. Agha et al. (2024) demonstrate that housing cost burden's effect on social capital is mediated through residential stability — financial stress suppresses community participation and network formation. Desmond's research establishes that high cost burden triggers eviction risk, forced moves, and erosion of care networks. A city with high residential stability but high cost burden is rewarding forced immobility rather than genuine community embeddedness.

The 12% weight reflects the finding (Agha et al. 2024; BRIC framework methodology) that cost burden operates primarily as a modifier of the stability signal rather than an independent predictor of care capacity. BRIC and similar frameworks treat housing-adjacent factors as validity checks rather than primary drivers.

**Measurement note**: This metric uses households where cost-as-percentage-of-income was computable (income > 0). Households with zero or negative income are excluded as "not computed" by Census. This produces lower apparent cost burden rates than commonly cited figures, which typically use different computation methods. Relative city rankings are still valid; absolute percentages should not be compared to external sources without this caveat.

**Benchmark**: 85% not burdened (15% burdened ceiling). This represents a well-functioning housing market. The 25% cost-burden threshold in the research literature; 15% represents a high-performing city.

---

### Pillar 2: Institutions of Care

#### 3.4 Community Health Center Density (FQHCs)
**Definition**: Active Federally Qualified Health Center service delivery sites per 100,000 residents.  
**Source**: HRSA Health Center Service Delivery and Look-Alike Sites dataset, filtered to active FQHCs (excluding Look-Alike sites) with service delivery functions.  
**Unit**: FQHCs per 100,000 residents (higher = better).  
**Weight within Pillar 2**: **55%**

**Rationale**: FQHCs carry the strongest evidence base of any metric in this index. Rosenbaum et al. (2011) demonstrate that FQHC access significantly reduces emergency room utilization among low-income and uninsured patients. Shi and colleagues (multiple studies, 2001–2017) link FQHC access to reduced mortality from chronic disease, improved preventive care uptake, and reduced health disparities across racial and income lines. Congressional Budget Office analyses consistently find that FQHCs save approximately $2,371 per user in avoided emergency care costs. Unlike density measures for nonprofits, FQHCs have federal funding and reporting requirements that make their service delivery more verifiable.

#### 3.5 Health, Mental Health, and Food Nonprofit Density
**Definition**: Registered 501(c)(3) organizations with NTEE major groups E (Health), F (Mental Health and Crisis Intervention), or K (Food, Agriculture, and Nutrition) per 10,000 residents.  
**Source**: IRS EO BMF, filtered by NTEE first characters E, F, or K.  
**Unit**: orgs per 10,000 residents (higher = better).  
**Weight within Pillar 2**: **45%**

**Rationale**: Kim & Jennings (2012) find that nonprofit human service density at the county level correlates with lower poverty rates and better health outcomes, with particularly strong effects for health and food organizations serving low-income populations. Pettijohn & Boris (2013) document the direct care role of these nonprofits for populations that cannot access formal healthcare or government food programs. The weight is slightly lower than FQHCs because IRS registration does not guarantee activity or impact.

#### 3.6 Faith-Based Human Services — Diagnostic Only (Not Scored in V2)
**Definition**: Registered 501(c)(3) organizations with NTEE prefix X3 per 10,000 residents.  
**Source**: IRS EO BMF, filtered by NTEE prefix "X3".  
**Unit**: orgs per 10,000 residents (reported, not scored).

**Why excluded**: IRS NTEE code X30 functions as a catch-all that captures congregations alongside human-service providers. The category is dominated by congregations whose primary identity is devotional rather than service-oriented. Many faith organizations that *do* primarily deliver social services register under P or E/K instead. V3 will explore combining X3x with faith-affiliated P/E/K registrations for a more complete measure.

---

### Pillar 3: Reach

#### 3.7 SNAP Coverage Rate
**Definition**: Ratio of SNAP-receiving households to poverty-level households, normalized to 0–100. Approximates participation among likely-eligible households.  
**Formula**: (SNAP households / total households) ÷ (population in poverty / total population) × 100, capped at 100.  
**Source**: U.S. Census Bureau, ACS 5-year estimates (2022). B22001 (SNAP receipt), B17001 (poverty status).  
**Unit**: % coverage (higher = better).  
**Weight within Pillar 3**: **60%**

**Rationale**: SNAP coverage rate measures whether food assistance infrastructure actually reaches the population in poverty — the most direct measure of care system reach available from national data. A high SNAP rate relative to poverty rate indicates that the system is connecting eligible people to food support. Normalized by local poverty rate to avoid rewarding cities with high poverty (need) for high SNAP volume. The 60% weight reflects SNAP's stronger evidence base: SNAP eligibility rules are federal and consistent, making the coverage denominator more interpretable than health insurance eligibility, which varies by state Medicaid policy.

**Limitation**: SNAP eligibility is technically defined at 130% of FPL; this metric uses 100% FPL as an approximation, potentially overstating coverage rates in cities with large near-poverty (100–130% FPL) populations. V3 will use HHS poverty guidelines at 130% FPL when county-level population estimates at that threshold become available.

#### 3.8 Health Insurance Coverage Rate
**Definition**: Percentage of the civilian noninstitutional population with any health insurance coverage.  
**Source**: U.S. Census Bureau, ACS 5-year estimates (2022). B27001 (health insurance coverage status by sex by age). Computed as (total population − total uninsured) / total population × 100.  
**Unit**: % insured (higher = better).  
**Weight within Pillar 3**: **40%**

**Rationale**: Health insurance coverage is a direct measure of whether people can access health systems when they need care. Low coverage reflects structural barriers to healthcare access that persist regardless of FQHC density. The 40% weight is slightly lower than SNAP because coverage reflects a combination of local care infrastructure and state-level insurance policy (Medicaid expansion status), which introduces confounding: a city in a non-Medicaid-expansion state will score lower due to state policy rather than local care capacity failure. V3 will separate Medicaid enrollment from private coverage to better isolate the local infrastructure signal.

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
| Human services nonprofits (NTEE P) | 10 per 10,000 | 1 org per 1,000 residents; saturation across all sub-categories |
| Housing affordability | 85% not burdened | 15% cost-burden ceiling; well-functioning housing market |
| FQHC density | 15 per 100,000 | Eliminates HRSA shortage designation plus geographic redundancy |
| Health/MH/Food nonprofits (NTEE E/F/K) | 8 per 10,000 | Coverage saturation; lower than NTEE P because orgs operate at larger scale |
| SNAP coverage rate | 85% | USDA FNS national SNAP participation target among eligible households |
| Health insurance coverage | 95% | Near-universal coverage; achievable in Medicaid-expansion states |

**Advantage over min-max scaling**: Scores are absolute — adding or removing cities does not change existing scores. A city's score reflects its performance against a standard, not against whoever else is in the comparison set.

---

## 5. Care Quotient Calculation

The Care Quotient (CQ) is a weighted composite of seven scored metrics, computed in two steps.

**Step 1 — Pillar scores** (weighted averages of constituent metrics):

```
Pillar 1 = (residential_stability × 0.48) + (social_support × 0.40) + (housing_affordability × 0.12)
Pillar 2 = (fqhc_density × 0.55)          + (care_institutions × 0.45)
Pillar 3 = (snap_coverage × 0.60)          + (health_insurance × 0.40)
```

**Step 2 — Care Quotient**:

```
CQ = (Pillar 1 × 0.40) + (Pillar 2 × 0.35) + (Pillar 3 × 0.25)
```

All metric scores are on a 0–100 scale against absolute benchmarks (Section 4), so the CQ is also 0–100.

**Important caveat**: These are judgment-based weights in V2. V3 will derive inter-pillar and within-pillar weights empirically via regression against care outcome variables (e.g., ER utilization rates, social isolation survey data) across 100 cities.

**Individual metric scores remain the primary diagnostic output.** The CQ is a useful summary for comparison, but it compresses variation — a city can score at the CQ average while being strong on one pillar and weak on another.

---

## 6. Diagnostic Metrics (Not Scored)

The following metrics are collected and reported but excluded from pillar scores:

| Metric | Rationale for exclusion |
|--------|-------------------------|
| Library density (per 100k) | Libraries are valuable community infrastructure but not primarily care institutions. Including them would conflate general civic amenity with care capacity. |
| Library visits per capita | Same rationale. Reported as a supplementary community engagement signal. |
| All care-related nonprofit density | Broad diagnostic count across all NTEE care codes. Useful for context but too aggregated to score; double-counts organizations captured in the scored sub-metrics. |
| Faith-based orgs (X3x, per 10k) | NTEE X30 captures congregations, not specifically care providers. See Section 3.6. |

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

1. **Benchmark judgment**: Nonprofit density benchmarks (NTEE P at 10/10k, NTEE E/F/K at 8/10k) and SNAP/health insurance benchmarks are reasoned thresholds without a policy-derived standard. The FQHC and residential stability benchmarks are more firmly grounded. All benchmarks are documented explicitly and subject to revision in V3.

2. **IRS data lag**: EO BMF data may lag registrations by 1–2 years. Inactive organizations may remain registered.

3. **City-name matching**: IRS city-name filtering uses known borough/neighborhood variants for each configured city. Less common organizational addresses may be missed. V3 will move to FIPS-code-based filtering.

4. **Faith-based measurement**: X30 codes capture congregations, not specifically human-service providers. Faith-based density is reported as a diagnostic metric rather than scored (see Section 3.6).

5. **Density vs. access**: Per-capita density measures presence, not accessibility. A health center in one part of a large city does not serve all residents equally.

6. **Residential stability: chosen vs. forced immobility**: High residential stability can reflect embedded social networks (Putnam 2000; Sampson et al. 1997), but it can equally reflect economic immobility — poverty traps and exclusionary housing markets that prevent people from leaving even when conditions are poor. The housing affordability counter-weight (Section 3.3) partially addresses this, but Census ACS data cannot fully distinguish chosen from forced stability. V3 will explore cross-referencing with Chetty et al. Opportunity Atlas economic mobility data.

7. **Housing cost burden undercount**: The Census B25070/B25091 methodology excludes households with zero or negative income ("not computed"), which can understate true cost burden rates compared to HUD CHAS figures. Relative city rankings are valid; absolute percentages should not be compared to external sources without this caveat.

8. **Health insurance and state policy**: Health insurance coverage reflects state-level Medicaid expansion decisions as much as local care infrastructure. Texas (Houston) did not expand Medicaid under the ACA, which contributes significantly to its lower score on this metric. V3 will separate Medicaid enrollment from private coverage.

9. **SNAP eligibility approximation**: SNAP coverage rate uses 100% FPL poverty data as a denominator; true eligibility extends to 130% FPL. This may overstate coverage rates in cities with large near-poverty populations.

---

## 10. Planned V3 Improvements

- **Scale to 100 cities**: FIPS-code-based geographic filtering across all datasets to enable reliable comparison at scale.
- **Regression-based weighting**: With 100 cities, derive weights empirically from their relationship to care outcome variables (ER utilization, social isolation survey data).
- **Separate Medicaid from private insurance**: Isolate state policy effects from local care infrastructure in the health insurance metric.
- **SNAP eligibility at 130% FPL**: Use HHS poverty guidelines at 130% for a more accurate eligibility denominator.
- **Faith-based measurement**: Explore combining X3x with faith-affiliated P/E/K organizations for a more complete measure.
- **Residential stability cross-reference**: Incorporate HUD cost-burden data and Chetty et al. Opportunity Atlas to distinguish chosen from forced stability.

---

## 11. References

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
