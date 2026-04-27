# Care Quotient: Methodology

**Version**: 1.0 (V1 Prototype)
**Date**: April 2026  
**Author**: Peter Durand

---

## 1. What This Index Measures

The Care Quotient (CQ) measures **care capacity** — the extent to which a community has the social ties, institutions, and responsive systems needed to support people in moments of vulnerability.

This is explicitly **not** a quality-of-life index. A city can score well on income, safety, and health outcomes while having thin care infrastructure for its most vulnerable residents. The inverse is also true. The CQ separates these two dimensions and measures only the latter.

The motivating question is whether communities have what it takes to *show up* — through networks, institutions, and responsiveness — when people need help.

**V1 scope and framing**: This document describes a V1 prototype covering 5 cities across 4 scored metrics. The CQ in this version measures care *infrastructure* — whether the social fabric and institutional capacity exist — not care *behavior* or *responsiveness*. A city could score well on the CQ while still having systems that respond slowly or inconsistently when people reach out. That dimension (Pillar 3: Responsiveness) is conceptually central but not yet scored; see Section 9. Scores should be read as "this city has stronger or weaker care infrastructure than the benchmark" rather than as definitive rankings of how much cities care for their residents.

---

## 2. Two Scored Pillars

### Pillar 1: Social Support and Connection (55% of CQ)
The relational layer: whether people are embedded in networks that can provide support.

### Pillar 2: Institutions of Care (45% of CQ)
The organizational layer: whether institutions exist that are specifically designed to absorb distress.

The 55/45 inter-pillar split reflects care ethics theory (Gilligan 1982, Noddings 1984), which holds that caring is fundamentally relational — the social fabric is the primary form of caring. Nussbaum's capabilities approach counters that institutional infrastructure is a necessary condition for caring to mean anything at scale. The 55/45 split honors both traditions with a modest tilt toward the relational. These weights are judgment-based in V1; V2 will derive them empirically via regression against care outcomes across 100 cities.

A third pillar — **Responsiveness** (whether systems act when people reach out) — is part of the conceptual framework but deferred from the V1 scored baseline. No clean national, cross-city source for responsiveness data (e.g., 311 closure times) has been identified. It will be incorporated in V2.

---

## 3. Scored Metrics, Data Sources, and Weight Rationale

### Pillar 1: Social Support and Connection

#### 3.1 Residential Stability
**Definition**: Percentage of population living in the same home for one or more years (Census ACS variable B07003_004E).  
**Source**: U.S. Census Bureau, American Community Survey 5-year estimates (2022).  
**Unit**: % of population (higher = more stable = better).  
**Weight within Pillar 1**: **55%**

**Rationale**: Residential stability is one of the most consistently documented predictors of social capital in the social science literature. Putnam (2000) identifies it as a primary structural driver of civic engagement, community trust, and collective action. Sampson, Raudenbush & Earls (1997) demonstrate that stable residential communities develop "collective efficacy" — a shared capacity and willingness to intervene on behalf of neighbors — which directly predicts mutual support behaviors. Briggs (1998) shows that stable residents maintain significantly stronger social networks and are far more likely to provide and receive informal care. The mechanism is straightforward: you cannot be embedded in a care network you have not had time to form.

This metric receives the highest weight in Pillar 1 because it is the structural precondition for all other forms of social caring — you cannot organize mutual aid, sustain nonprofits, or build collective efficacy in a population that isn't there long enough to form those bonds.

#### 3.2 Human Services Nonprofit Density
**Definition**: Registered 501(c)(3) organizations with NTEE major group P (Human Services: community centers, mutual aid, social services, volunteer programs) per 10,000 residents.  
**Source**: IRS Exempt Organizations Business Master File (EO BMF), filtered by NTEE first character "P" and city name.  
**Unit**: orgs per 10,000 residents (higher = better).  
**Weight within Pillar 1**: **45%**

**Rationale**: Salamon & Anheier (1998) establish nonprofit density as a structural indicator of civil society capacity. Boris & Steuerle (2006) document the direct link between human-service nonprofit presence and care provision for low-income and vulnerable populations. However, density does not guarantee accessibility, utilization, or quality. An org registered in a city may be inactive or serve limited populations. This metric receives a lower weight than residential stability to reflect the indirect nature of the connection between organizational presence and actual care.

**Exclusions**: Arts/culture (NTEE A) and education (NTEE B) organizations are excluded. Both categories correlate strongly with urban affluence — a city with many museums and private schools would score high without that reflecting care capacity. Their inclusion would bias the index toward wealthy cities.

---

### Pillar 2: Institutions of Care

#### 3.3 Community Health Center Density (FQHCs)
**Definition**: Active Federally Qualified Health Center service delivery sites per 100,000 residents.  
**Source**: HRSA Health Center Service Delivery and Look-Alike Sites dataset, filtered to active FQHCs (excluding Look-Alike sites) with service delivery functions.  
**Unit**: FQHCs per 100,000 residents (higher = better).  
**Weight within Pillar 2**: **55%**

**Rationale**: FQHCs carry the strongest evidence base of any metric in this index. Rosenbaum et al. (2011) demonstrate that FQHC access significantly reduces emergency room utilization among low-income and uninsured patients. Shi and colleagues (multiple studies, 2001–2017) link FQHC access to reduced mortality from chronic disease, improved preventive care uptake, and reduced health disparities across racial and income lines. Congressional Budget Office analyses consistently find that FQHCs save approximately $2,371 per user in avoided emergency care costs. Unlike density measures for nonprofits or faith organizations, FQHCs have federal funding and reporting requirements that make their service delivery more verifiable. Evidence derives primarily from quasi-experimental designs.

#### 3.4 Health, Mental Health, and Food Nonprofit Density
**Definition**: Registered 501(c)(3) organizations with NTEE major groups E (Health), F (Mental Health and Crisis Intervention), or K (Food, Agriculture, and Nutrition) per 10,000 residents.  
**Source**: IRS EO BMF, filtered by NTEE first characters E, F, or K.  
**Unit**: orgs per 10,000 residents (higher = better).  
**Weight within Pillar 2**: **45%**

**Rationale**: Kim & Jennings (2012) find that nonprofit human service density at the county level correlates with lower poverty rates and better health outcomes, with particularly strong effects for health and food organizations serving low-income populations. Pettijohn & Boris (2013) document the direct care role of these nonprofits for populations that cannot access formal healthcare or government food programs. The weight is slightly lower than FQHCs (45% vs 55%) because, as with all IRS-based measures, registration does not guarantee activity or impact — the organizational density signal is valuable but noisier than the FQHC evidence base, which carries a federal mandate and reporting requirements that make service delivery more verifiable.

#### 3.5 Faith-Based Human Services — Diagnostic Only (Not Scored in V1)
**Definition**: Registered 501(c)(3) organizations with NTEE prefix X3 per 10,000 residents.  
**Source**: IRS EO BMF, filtered by NTEE prefix "X3".  
**Unit**: orgs per 10,000 residents (reported, not scored).

**Why excluded from scoring**: Faith-based organizations are a meaningful component of care infrastructure, and the literature supports their importance (Cnaan et al. 2006; Johnson, Tompkins & Webb 2002; Chaves & Tsitsos 2001). However, IRS NTEE code X30 functions as a catch-all for religious organizations rather than specifically capturing human-service providers. Inspection of X30-coded organizations in V1 cities reveals that the category is dominated by congregations — Orthodox and Hasidic synagogues, churches, mosques — that registered under X30 as their primary identity, not organizations whose primary activity is delivering social services.

This is not a limitation that weighting can correct. Including X30 counts as a scored metric would essentially be scoring the density of congregations, not the density of faith-based care providers — a different and less relevant quantity.

A second compounding limitation: many faith organizations that *do* primarily deliver social services register under NTEE P (Human Services) or E/K rather than X, because those codes better describe their program work. The true contribution of faith-based care infrastructure is both undercounted in X30 and distributed across other NTEE categories.

This metric is retained as a diagnostic indicator and reported alongside scores. **V2 will explore whether combining X3x with faith-affiliated organizations registered under P/E/K produces a more complete and reliable measure.** The intent is to capture faith-based care — the exclusion is methodological, not conceptual.

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
| FQHC density | 15 per 100,000 | Eliminates HRSA shortage designation plus geographic redundancy |
| Health/MH/Food nonprofits (NTEE E/F/K) | 8 per 10,000 | Coverage saturation; lower than NTEE P because orgs operate at larger scale |

**Advantage over min-max scaling**: Scores are absolute — adding or removing cities does not change existing scores. A city's score reflects its performance against a standard, not against whoever else is in the comparison set.

**Benchmark derivation**: Residential stability and FQHC benchmarks are grounded in empirical evidence (ACS data for high-stability neighborhoods; HRSA HPSA elimination criteria). Nonprofit density benchmarks are judgment thresholds without a policy-derived standard. Both types are documented explicitly in Section 3.

**Full rationale for each benchmark**: See Section 3 metric entries.

---

## 5. Care Quotient Calculation

The Care Quotient (CQ) is a weighted composite of the four scored metrics, computed in two steps.

**Step 1 — Pillar scores** (weighted averages of constituent metrics):

```
Pillar 1 = (residential_stability × 0.55) + (social_support × 0.45)
Pillar 2 = (fqhc_density × 0.55)          + (care_institutions × 0.45)
```

**Step 2 — Care Quotient**:

```
CQ = (Pillar 1 × 0.55) + (Pillar 2 × 0.45)
```

All metric scores are on a 0–100 scale against absolute benchmarks (Section 4), so the CQ is also 0–100.

**Weight rationale — inter-pillar (55/45)**: Care ethics theory (Gilligan 1982, Noddings 1984) holds that caring is fundamentally relational — whether people show up for one another is the primary form of caring. Nussbaum's capabilities approach counters that institutional infrastructure is a necessary condition for caring to be meaningful at scale. The 55/45 split honors both traditions with a modest tilt toward the relational dimension. The weights are deliberately narrow-margined to reflect genuine uncertainty.

**Weight rationale — within pillars (both 55/45)**: Within Pillar 1, residential stability receives the slight edge because it is the structural precondition for network formation (Putnam 2000; Sampson et al. 1997). Within Pillar 2, FQHCs receive the slight edge because they carry the strongest evidence base and a federal mandate to serve vulnerable populations (Rosenbaum et al. 2011).

**Important caveat**: These are judgment-based weights in V1. V2 will derive inter-pillar and within-pillar weights empirically via regression against care outcome variables (e.g., ER utilization rates, social isolation survey data) across 100 cities. The V1 weights represent a defensible prior, not an established finding.

**Individual metric scores remain the primary diagnostic output.** The CQ is a useful summary for comparison, but it compresses variation — a city can score at the CQ average while being strong on one pillar and weak on another. Both the summary and the breakdown are reported.

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

1. **Benchmark judgment**: Nonprofit density benchmarks (NTEE P at 10/10k, NTEE E/F/K at 8/10k) are reasoned thresholds without a policy-derived standard. The FQHC and residential stability benchmarks are more firmly grounded. All benchmarks are documented explicitly and subject to revision in V2.

2. **IRS data lag**: EO BMF data may lag registrations by 1–2 years. Inactive organizations may remain registered.

3. **City-name matching**: IRS city-name filtering uses known borough/neighborhood variants for each configured city. Less common organizational addresses may be missed.

4. **Faith-based measurement**: X30 codes capture congregations, not specifically human-service providers. Faith-based density is reported as a diagnostic metric rather than scored (see Section 3.5).

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
