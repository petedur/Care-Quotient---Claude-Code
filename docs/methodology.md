# Community Care Capacity Index: Methodology

**Version**: 1.0  
**Date**: April 2026  
**Author**: Peter Durand

---

## 1. What This Index Measures

The Community Care Capacity Index (CCCI) measures **care capacity** — the extent to which a community has the social ties, institutions, and responsive systems needed to support people in moments of vulnerability.

This is explicitly **not** a quality-of-life index. A city can score well on income, safety, and health outcomes while having thin care infrastructure for its most vulnerable residents. The inverse is also true. The CCCI separates these two dimensions and measures only the latter.

The motivating question is whether communities have what it takes to *show up* — through networks, institutions, and responsiveness — when people need help.

---

## 2. Two Scored Pillars

### Pillar 1: Social Support and Connection (50% of overall score)
The relational layer: whether people are embedded in networks that can provide support.

### Pillar 2: Institutions of Care (50% of overall score)
The organizational layer: whether institutions exist that are specifically designed to absorb distress.

A third pillar — **Responsiveness** (whether systems act when people reach out) — is part of the conceptual framework but deferred from the V1 scored baseline. No clean national, cross-city source for responsiveness data (e.g., 311 closure times) has been identified. It will be incorporated in V2.

---

## 3. Scored Metrics, Data Sources, and Weight Rationale

### Pillar 1: Social Support and Connection

#### 3.1 Residential Stability
**Definition**: Percentage of population living in the same home for one or more years (Census ACS variable B07003_004E).  
**Source**: U.S. Census Bureau, American Community Survey 5-year estimates (2022).  
**Unit**: % of population (higher = more stable = better).  
**Weight within Pillar 1**: **60%**

**Rationale**: Residential stability is one of the most consistently documented predictors of social capital in the social science literature. Putnam (2000) identifies it as a primary structural driver of civic engagement, community trust, and collective action. Sampson, Raudenbush & Earls (1997) demonstrate that stable residential communities develop "collective efficacy" — a shared capacity and willingness to intervene on behalf of neighbors — which directly predicts mutual support behaviors. Briggs (1998) shows that stable residents maintain significantly stronger social networks and are far more likely to provide and receive informal care. The mechanism is straightforward: you cannot be embedded in a care network you have not had time to form.

This metric receives the highest weight in Pillar 1 because the evidence is both theoretically robust and empirically consistent across study designs.

#### 3.2 Human Services Nonprofit Density
**Definition**: Registered 501(c)(3) organizations with NTEE major group P (Human Services: community centers, mutual aid, social services, volunteer programs) per 10,000 residents.  
**Source**: IRS Exempt Organizations Business Master File (EO BMF), filtered by NTEE first character "P" and city name.  
**Unit**: orgs per 10,000 residents (higher = better).  
**Weight within Pillar 1**: **40%**

**Rationale**: Salamon & Anheier (1998) establish nonprofit density as a structural indicator of civil society capacity. Boris & Steuerle (2006) document the direct link between human-service nonprofit presence and care provision for low-income and vulnerable populations. However, density does not guarantee accessibility, utilization, or quality. An org registered in a city may be inactive or serve limited populations. This metric receives a lower weight than residential stability to reflect the indirect nature of the connection between organizational presence and actual care.

**Exclusions**: Arts/culture (NTEE A) and education (NTEE B) organizations are excluded. Both categories correlate strongly with urban affluence — a city with many museums and private schools would score high without that reflecting care capacity. Their inclusion would bias the index toward wealthy cities.

---

### Pillar 2: Institutions of Care

#### 3.3 Community Health Center Density (FQHCs)
**Definition**: Active Federally Qualified Health Center service delivery sites per 100,000 residents.  
**Source**: HRSA Health Center Service Delivery and Look-Alike Sites dataset, filtered to active FQHCs (excluding Look-Alike sites) with service delivery functions.  
**Unit**: FQHCs per 100,000 residents (higher = better).  
**Weight within Pillar 2**: **50%**

**Rationale**: FQHCs carry the strongest evidence base of any metric in this index. Rosenbaum et al. (2011) demonstrate that FQHC access significantly reduces emergency room utilization among low-income and uninsured patients. Shi and colleagues (multiple studies, 2001–2017) link FQHC access to reduced mortality from chronic disease, improved preventive care uptake, and reduced health disparities across racial and income lines. Congressional Budget Office analyses consistently find that FQHCs save approximately $2,371 per user in avoided emergency care costs. Unlike density measures for nonprofits or faith organizations, FQHCs have federal funding and reporting requirements that make their service delivery more verifiable. Evidence derives primarily from quasi-experimental designs.

#### 3.4 Health, Mental Health, and Food Nonprofit Density
**Definition**: Registered 501(c)(3) organizations with NTEE major groups E (Health), F (Mental Health and Crisis Intervention), or K (Food, Agriculture, and Nutrition) per 10,000 residents.  
**Source**: IRS EO BMF, filtered by NTEE first characters E, F, or K.  
**Unit**: orgs per 10,000 residents (higher = better).  
**Weight within Pillar 2**: **30%**

**Rationale**: Kim & Jennings (2012) find that nonprofit human service density at the county level correlates with lower poverty rates and better health outcomes, with particularly strong effects for health and food organizations serving low-income populations. Pettijohn & Boris (2013) document the direct care role of these nonprofits for populations that cannot access formal healthcare or government food programs. The weight is moderate because, as with all IRS-based measures, registration does not guarantee activity or impact.

#### 3.5 Faith-Based Human Services Density
**Definition**: Registered 501(c)(3) organizations with NTEE prefix X3 (Faith-Based Human Services and Issues) per 10,000 residents.  
**Source**: IRS EO BMF, filtered by NTEE prefix "X3".  
**Unit**: orgs per 10,000 residents (higher = better).  
**Weight within Pillar 2**: **20%**

**Rationale**: Faith-based organizations are a meaningful component of care infrastructure, particularly for food security, crisis response, and social connection. Cnaan et al. (2006) estimate that active service-providing congregations contribute $140,000–$265,000 in annual social services per congregation. Johnson, Tompkins & Webb (2002) find faith-based programs effective across multiple domains of care. Chaves & Tsitsos (2001) document that a meaningful portion of congregations provide direct social services beyond worship.

The weight is intentionally the lowest of the three Pillar 2 metrics for two reasons:

1. **Methodological limitation**: This metric almost certainly *understates* faith-based care. Many faith organizations that primarily deliver social services register under NTEE P (Human Services) or E/K rather than X, because those codes better describe their primary activity. Filtering to X30 captures only organizations that self-identify their primary purpose as faith-based human services. The true contribution of faith-based institutions is larger than this metric reflects.

2. **Evidence generalizability**: The evidence for faith-based programs is compelling in specific contexts (disaster relief, food provision, addiction recovery) but less consistent than the evidence for FQHCs or residential stability effects.

This limitation is documented explicitly rather than hidden. Future versions will explore whether combining X3x with faith-affiliated organizations registered under other NTEE codes produces a more complete picture.

---

## 4. Normalization Method

Raw metric values are normalized to a 0–100 scale using min-max scaling across the configured city set:

```
normalized = (value - min_across_cities) / (max_across_cities - min_across_cities) * 100
```

The city with the highest value on a given metric receives 100; the lowest receives 0. All cities fall between these bounds.

**Implication**: Scores are relative to the current city set, not absolute. Adding or removing cities will shift scores. This is a known limitation of V1 and a primary motivation for the planned 100-city expansion.

**Special case**: If all cities have the same value on a metric (no variation), every city receives 50.

---

## 5. Pillar and Overall Score Calculation

Pillar scores are weighted averages of normalized metric scores:

```
Pillar 1 = (residential_stability_norm * 0.60) + (social_support_density_norm * 0.40)
Pillar 2 = (fqhc_density_norm * 0.50) + (care_institution_density_norm * 0.30) + (faith_based_density_norm * 0.20)
Overall  = (Pillar 1 * 0.50) + (Pillar 2 * 0.50)
```

Pillars are weighted equally (50/50) in V1. Neither pillar has theoretical priority over the other: social networks and direct institutional care are both necessary conditions for care capacity, and the literature does not establish one as more predictive than the other at the city level.

---

## 6. Diagnostic Metrics (Not Scored)

The following metrics are collected and reported but excluded from pillar scores:

| Metric | Rationale for exclusion |
|--------|-------------------------|
| Library density (per 100k) | Libraries are valuable community infrastructure but not primarily care institutions. Including them would conflate general civic amenity with care capacity. |
| Library visits per capita | Same rationale as above. Reported as a supplementary community engagement signal. |
| All care-related nonprofit density | Broad diagnostic count across all NTEE care codes. Useful for context but too aggregated to score; double-counts organizations already captured in the scored sub-metrics. |

---

## 7. What Is Excluded and Why

| Category | NTEE | Reason for exclusion |
|----------|------|----------------------|
| Arts & culture | A | Correlates with affluence, not care. Would reward wealthy cities. |
| Education | B | Same — private schools, universities inflate this in high-income cities. |
| All religious orgs | X (broad) | Too noisy; includes purely devotional organizations with no care function. |
| General health outcomes | — | Outcome metric, not capacity metric. Measuring life expectancy would turn this into a conditions index. |
| Economic conditions | — | Out of scope by design; care capacity is distinct from prosperity. |

---

## 8. Data Sources

| Source | Coverage | Update frequency | Access |
|--------|----------|-----------------|--------|
| IRS EO BMF | All 50 states | Periodic (check IRS site) | Public download |
| Census ACS 5-year | All counties | Annual | Free API |
| IMLS Public Libraries Survey | National | Annual | Public download |
| HRSA Health Center Service Delivery | National | Periodic | Public download |

All four sources are national, free, and scriptable. No city-specific open data portals are required for the V1 scored baseline, which enables direct comparison across cities.

---

## 9. Known Limitations

1. **Relative scoring**: Min-max normalization means scores are relative to the current 5-city set. Adding cities will change scores.

2. **IRS data lag**: EO BMF data may lag registrations by 1–2 years. Inactive organizations may remain registered.

3. **City-name matching**: IRS city-name filtering uses known borough/neighborhood variants for each configured city. Less common organizational addresses may be missed.

4. **Faith-based undercount**: X3x-coded organizations underrepresent total faith-based care (see Section 3.5).

5. **No Pillar 3**: Responsiveness is not scored in V1. This is the most significant conceptual gap.

6. **Density vs. access**: Per-capita density measures presence, not accessibility. A health center in one part of a large city does not serve all residents equally.

---

## 10. Planned V2 Improvements

- **Regression-based weighting**: With 100 cities, derive weights empirically from their relationship to a care outcome variable (e.g., ER utilization rates, social isolation survey data).
- **Pillar 3 Responsiveness**: Identify a clean national cross-city source for responsiveness data.
- **Faith-based measurement**: Explore combining X3x with faith-affiliated P/E/K organizations for a more complete measure.
- **Geographic precision**: Move from city-name filtering to FIPS-code-based filtering for all metrics.

---

## 11. References

- Boris, E.T. & Steuerle, C.E. (2006). *Nonprofits and Government: Collaboration and Conflict*. Urban Institute Press.
- Briggs, X. de S. (1998). Brown kids in white suburbs: Housing mobility and the many faces of social capital. *Housing Policy Debate*, 9(1), 177–221.
- Chaves, M. & Tsitsos, W. (2001). Congregations and social services: What they do, how they do it, and with whom. *Nonprofit and Voluntary Sector Quarterly*, 30(4), 660–683.
- Cnaan, R.A. et al. (2006). *The Other Philadelphia Story: How Local Congregations Support Quality of Life in Urban America*. University of Pennsylvania Press.
- Congressional Budget Office. (multiple years). *Federally Qualified Health Centers: Quality and Costs*.
- Johnson, B.R., Tompkins, R.B., & Webb, D. (2002). *Objective Hope: Assessing the Effectiveness of Faith-Based Organizations*. Center for Research on Religion and Urban Civil Society.
- Kim, M. & Jennings, E.T. (2012). Effects of nonprofit human service organizations on well-being in US counties. *Administration & Society*, 44(4), 424–451.
- Pettijohn, S.L. & Boris, E.T. (2013). *Nonprofit-Government Contracts and Grants*. Urban Institute.
- Putnam, R.D. (2000). *Bowling Alone: The Collapse and Revival of American Community*. Simon & Schuster.
- Rosenbaum, S. et al. (2011). *Health Centers: An American Success Story*. George Washington University.
- Salamon, L.M. & Anheier, H.K. (1998). Social origins of civil society. *Voluntas*, 9(3), 213–248.
- Sampson, R.J., Raudenbush, S.W., & Earls, F. (1997). Neighborhoods and violent crime: A multilevel study of collective efficacy. *Science*, 277(5328), 918–924.
- Shi, L. et al. (multiple years). *Community Health Centers and Vulnerable Populations*. Various journals.
