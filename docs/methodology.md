# Care Quotient: Methodology

**Version**: 5.0 (V5)
**Date**: April 2026  
**Author**: Peter Durand

---

## 1. What This Index Measures

The Care Quotient (CQ) measures **care capacity** — the extent to which a community has the social ties, institutions, and systems needed to support people in moments of vulnerability.

This is explicitly **not** a quality-of-life index. A city can score well on income, safety, and health outcomes while having thin care infrastructure for its most vulnerable residents. The inverse is also true. The CQ separates these two dimensions and measures only the latter.

The motivating question is whether communities have what it takes to *show up* — through networks, institutions, and reach — when people need help.

**V5 scope**: This document describes V5, covering 68 US cities across 8 scored metrics organized into 3 theoretically-grounded pillars. V5 restructures the pillar architecture based on care ethics theory (Tronto 1993, Putnam 2000, Sampson et al. 1997): Social & Relational Care (40%), Institutional Care (35%), Economic Access to Care (25%). Library density is promoted from diagnostic to scored metric; combined care nonprofit density moves from Pillar 2 to Pillar 1; housing cost burden moves from Pillar 1 to Pillar 3. V4 added nursing home capacity. V3 scaled from 5 to 68 cities via ZCTA-to-place crosswalk filtering, corrected the SNAP eligibility denominator, and collapsed NTEE P and E/F/K into a single combined care metric (r=0.85 correlation). V3.2 lowered the ZCTA overlap threshold from 50% to 40% after a geographic audit confirmed FQHCs in Raleigh and Fort Worth were excluded by the stricter cutoff. V2 covered 5 cities; V1 covered 4 metrics and 2 pillars. Scores should be read as "this city has stronger or weaker care capacity than the benchmark" rather than as definitive rankings.

---

## 2. Three Scored Pillars

The pillar structure is grounded in Joan Tronto's (1993) four phases of care — attentiveness, responsibility, competence, and responsiveness — and in the social capital and collective efficacy research of Putnam (2000) and Sampson et al. (1997). Each pillar represents a distinct layer of what it means for a city to be capable of care. See the "What is Care?" theory page for the full theoretical foundation.

### Pillar 1: Social & Relational Care (40% of CQ)
The relational layer: whether the social infrastructure for care exists — stable communities that allow relationships to form and persist, organized community responses to need, and accessible public spaces that hold communities together.

*Metrics: Residential stability (50%), Care nonprofit density (35%), Library density (15%)*

### Pillar 2: Institutional Care (35% of CQ)
The organizational layer: whether formal institutions exist to absorb distress at scale — safety-net primary care centers that serve patients regardless of ability to pay, and elder care infrastructure.

*Metrics: FQHC density (55%), Nursing home capacity (45%)*

### Pillar 3: Economic Access to Care (25% of CQ)
The enabling conditions layer: whether economic circumstances allow care to reach people who need it — coverage to enter the care system, housing stability that makes care possible, and food security program reach.

*Metrics: Healthcare coverage (40%), Housing affordability (35%), SNAP coverage (25%)*

**Inter-pillar weight rationale (40/35/25)**: Relational infrastructure is theoretically prior — Tronto's attentiveness phase (the moral achievement of *noticing* need) and Putnam's bridging capital (networks that generate care behavior) are preconditions for institutional care to function. You cannot have genuine care at scale without the social fabric that generates attentiveness. Institutional infrastructure (Pillar 2) is necessary but second. Economic access (Pillar 3) is an enabling condition that determines whether the above reaches those who need it. The 40/35/25 split reflects this causal ordering.

**V5 structural changes**: V4 had Pillar 1 as Social Fabric (residential stability + housing cost burden) and Pillar 2 as Institutions of Care (combined_care + FQHCs + nursing homes). V5 restructures based on theoretical grounding from care ethics (Tronto, Gilligan, Noddings, Putnam, Sampson) and peer reviewer feedback: (1) Library density promoted from diagnostic to scored metric in Pillar 1 — public libraries are explicitly named by care theory as institutions of care that absorb community distress; (2) Combined care nonprofit density moved from Pillar 2 to Pillar 1 — nonprofits represent organized community response (Tronto: responsibility), which is relational before it is institutional; (3) Housing cost burden moved from Pillar 1 to Pillar 3 — it measures an economic access barrier, not a relational capacity; (4) Pillar 3 expanded from two to three metrics with housing joining healthcare coverage and SNAP; (5) Pillar 2 simplified to the two directly institutional metrics (FQHCs and nursing homes), with within-weights revised to 55/45.

---

## 3. Scored Metrics, Data Sources, and Weight Rationale

### Pillar 1: Social & Relational Care

#### 3.1 Residential Stability
**Definition**: Percentage of population living in the same home for one or more years (Census ACS variable B07003_004E).  
**Source**: U.S. Census Bureau, American Community Survey 5-year estimates (2022).  
**Unit**: % of population (higher = more stable = better).  
**Weight within Pillar 1**: **50%**

**Rationale**: Residential stability is one of the most consistently documented predictors of social capital in the social science literature. Putnam (2000) identifies it as a primary structural driver of civic engagement, community trust, and collective action. Sampson, Raudenbush & Earls (1997) demonstrate that stable residential communities develop "collective efficacy" — a shared capacity and willingness to intervene on behalf of neighbors — which directly predicts mutual support behaviors. Briggs (1998) shows that stable residents maintain significantly stronger social networks and are far more likely to provide and receive informal care.

This metric receives the highest weight in Pillar 1 because it is the structural precondition for all other forms of social caring. V3 factor analysis confirmed this as the dominant signal in the Social Fabric dimension (loading 0.70). Weight reduced from 65% (V4) to 50% to accommodate nonprofit density and library density as co-equal Pillar 1 signals in V5.

**Measurement boundary**: ACS B07003_004E measures residential stability among *current* residents only — it records whether people living in a city now lived in the same home one year ago. People who left the metropolitan area entirely in the prior year are not in the sampling frame. This means the metric captures "stability among those who stayed" rather than citywide retention. If a city loses many residents to out-migration, this variable does not reflect that churn; it measures only the stable subset of current residents. This is a structural limitation of the variable that cannot be resolved with currently available national data, and it means the metric may modestly overstate community embeddedness in cities with high out-migration.

#### 3.2 Combined Care Nonprofit Density (NTEE P + E + F + K)
**Definition**: Registered 501(c)(3) organizations with NTEE major groups P (Human Services), E (Health), F (Mental Health and Crisis Intervention), or K (Food, Agriculture, and Nutrition) per 10,000 residents.  
**Source**: IRS Exempt Organizations Business Master File (EO BMF), filtered by NTEE first characters P, E, F, or K.  
**Unit**: orgs per 10,000 residents (higher = better).  
**Weight within Pillar 1**: **35%**

**Rationale**: In V2, NTEE P (Human Services) and NTEE E/F/K (Health, Mental Health, Food) were scored as separate metrics in separate pillars. V3 factor analysis across 68 cities showed these two metrics correlate at r=0.85 and load on the same empirical factor — cities with high NTEE P density also have high NTEE E/F/K density. The pillar distinction was unsupported by the data. V3 collapses them into a single combined metric.

Salamon & Anheier (1998) establish nonprofit density as a structural indicator of civil society capacity. Kim & Jennings (2012) find that nonprofit human service density correlates with lower poverty rates and better health outcomes. Boris & Steuerle (2006) document the direct link between human-service nonprofit presence and care provision for vulnerable populations.

**Exclusions**: Arts/culture (NTEE A), education (NTEE B), and broad religious organizations (NTEE X, except X3x) are excluded. These categories correlate with affluence rather than care capacity. The individual NTEE P and E/F/K sub-components are retained as diagnostic metrics.

**Denominator choice and shadow diagnostic**: The total-population denominator measures citywide supply per resident. This creates a scale effect for large cities: a city where care nonprofits are concentrated in lower-income areas may appear under-resourced on a per-capita basis simply because its total population is large. NYC and Chicago, for example, have roughly similar absolute counts of low-income residents (~1.3M and ~1M respectively), but NYC's low-income population is only ~16% of its total population while Chicago's is ~40% — so a total-population denominator structurally disadvantages NYC relative to need. V5 adds care nonprofit density per 10,000 residents at 0–150% of the Federal Poverty Level as a shadow diagnostic metric, allowing direct comparison between the total-population and need-adjusted framings. This diagnostic is reported on city pages but not scored, pending validation that the ranking changes are interpretively meaningful rather than artifacts of poverty-rate geography.

**Benchmark**: 25 per 10,000 residents. Raised from 15/10k (V2) after 50%+ of cities hit the ceiling under county-based geographic filtering. ZCTA-based filtering reduces raw counts; 25/10k maintains meaningful discrimination for top performers.

**V5 note**: Moved from Pillar 2 (Institutions of Care) to Pillar 1 (Social & Relational Care). Nonprofits represent organized community response — the translation of social will into action (Tronto: responsibility phase). This is relational before it is institutional; the same organizations show up in relational space before they scale into formal institutions.

#### 3.3 Library Density
**Definition**: Public library service outlets (main libraries and branches) per 100,000 residents.  
**Source**: Institute of Museum and Library Services (IMLS), Public Libraries Survey, most recent available year.  
**Unit**: libraries per 100,000 residents (higher = better).  
**Weight within Pillar 1**: **15%**  
**Benchmark**: 5 libraries per 100,000 residents (P90 across 68 cities; aspirational but achievable).

**Rationale**: Public libraries are among the most underappreciated institutions of community care. They provide free access to information, technology, and programming regardless of income or housing status. In practice, they function as de facto distress absorption sites — providing warming/cooling centers, social service referrals, spaces for unhoused residents, and programming for isolated elderly and youth populations. Mentor feedback for this project explicitly named libraries alongside nonprofits and health centers as institutions of care. The 15% within-pillar weight reflects their secondary role relative to nonprofit networks (35%) and residential stability (50%) while acknowledging their direct presence in the community care ecosystem.

The library density benchmark (5/100k) represents a standard achieved by roughly 10% of cities in our dataset. Cities at the median (2.8/100k) score approximately 56; the lowest-density cities (Phoenix: 1.1/100k) score 22. This spread gives the metric meaningful discriminating power.

**Measurement note**: IMLS reports service outlets rather than full library systems — a city with one central library and eight branches counts as nine outlets. This more accurately reflects community access than counting systems. Rural-service libraries that operate in a city's ZCTAs are included where applicable.

---

### Pillar 2: Institutional Care

#### 3.4 Community Health Center Density (FQHCs)
**Definition**: Active Federally Qualified Health Center service delivery sites per 100,000 residents.  
**Source**: HRSA Health Center Service Delivery and Look-Alike Sites dataset, filtered to active FQHCs (excluding Look-Alike sites) with service delivery functions.  
**Unit**: FQHCs per 100,000 residents (higher = better).  
**Weight within Pillar 2**: **55%**

**Rationale**: FQHCs carry the strongest evidence base of any metric in this index. Rosenbaum et al. (2011) demonstrate that FQHC access significantly reduces emergency room utilization among low-income and uninsured patients. Shi and colleagues (multiple studies, 2001–2017) link FQHC access to reduced mortality from chronic disease, improved preventive care uptake, and reduced health disparities across racial and income lines. Congressional Budget Office analyses consistently find that FQHCs save approximately $2,371 per user in avoided emergency care costs. Unlike density measures for nonprofits, FQHCs have federal funding and reporting requirements that make their service delivery more verifiable.

**Relationship to health insurance coverage (Section 3.8)**: FQHC density and health insurance coverage are kept as separate metrics in separate pillars because their interaction is interpretively informative rather than redundant. FQHCs are specifically designed to serve Medicaid and uninsured populations — their federal mandate and funding model is built around exactly the populations that lack private insurance. A proposal to adjust FQHC density by the insurance rate would therefore penalize cities for serving uninsured residents, inverting the metric's intent.

The two metrics are best read together as a diagnostic pair. Four patterns are possible:

| FQHC density | Health insurance | Interpretation |
|---|---|---|
| High | High | Strong safety-net infrastructure with broad coverage reach — the most complete care access picture |
| High | Low | Safety-net infrastructure is present and doing its intended work; the gap is upstream coverage, typically reflecting state Medicaid non-expansion |
| Low | High | Coverage is strong but federally-supported physical infrastructure is thin; access depends on private providers and may be geographically uneven |
| Low | Low | Compounded access problem — neither coverage nor safety-net infrastructure is adequate |

City pages flag notable mismatch patterns where the FQHC and insurance scores diverge significantly.

#### 3.5 Nursing Home Capacity
**Definition**: Certified nursing home beds per 1,000 residents aged 65 and older.  
**Source**: CMS Care Compare — Nursing Home Provider Information (dataset ID: 4pq5-n9py), April 2026 data. Filtered to Medicare- and/or Medicaid-certified facilities within each city's ZCTA boundary (≥40% land-area overlap). Denominator is ACS 5-year (2022) population 65+ (B01001 age-by-sex variables).  
**Unit**: certified beds per 1,000 residents 65+ (higher = more elder care capacity).  
**Weight within Pillar 2**: **45%**  
**Benchmark**: 50 beds per 1,000 residents 65+.

**Benchmark rationale**: This threshold represents approximately 5% of the elderly population in skilled nursing care at any one time — consistent with national occupancy patterns. The CMS national average is approximately 42 beds per 1,000 residents 65+; 50/1k is set modestly above the national average to represent a well-supplied but achievable standard. The metric deliberately scores most cities in the 40–80 range rather than at ceiling, preserving discrimination across the distribution.

**Rationale**: Nursing homes are the primary formal institution for elder care requiring daily skilled nursing support. Certified bed counts are an established supply measure used in health services research (Bowblis, 2011; Grabowski, 2001) and CMS policy evaluation. Unlike community-based care metrics, nursing homes are covered under uniform federal Medicare/Medicaid certification standards, making cross-city comparisons methodologically clean.

V4 factor analysis shows nursing home capacity loads 0.91 on its own isolated factor (Factor 3), completely independent of combined care nonprofit density (F1: 0.51) and FQHC density (F1: 0.59). This indicates that nursing home infrastructure is a genuinely distinct dimension of elder care that is not predicted by broader institutional care density. The 35/35/30 within-Pillar 2 weights are a theoretical choice: nonprofits and FQHCs receive slightly higher weight because they serve the full community age distribution, while nursing homes serve specifically the elderly. V5 should revisit this when home health capacity is added.

**Scope and limitations**: Covers only Medicare- and/or Medicaid-certified facilities. Private-pay only facilities are not included (a small minority nationally). Facilities are assigned to cities using the same ZCTA crosswalk as all other collectors — facilities headquartered in suburban ZCTAs just outside city limits may be missed if those ZCTAs fall below the 40% land-area threshold. Bed counts are certified-bed totals, not operational beds or daily census; actual occupancy typically runs at 80–90% of certified capacity. The denominator is the 65+ resident population of the city as measured by ACS, not the population actually at risk of needing nursing home care, which is concentrated in the 80+ cohort.

**Home health (V5 note)**: Home health agencies represent the other major formal elder care modality. CMS Care Compare includes a home health dataset (dataset ID: 6jpm-sxkc) with episode volume data, but CMS attributes episodes to the agency headquarters ZIP, not the patient's location. Agencies operating statewide report all episodes at a single HQ, making city-level attribution unreliable. Home health is deferred to V5 pending a clean geographic attribution method.

---

#### 3.6 Faith-Based Human Services — Diagnostic Only (Not Scored)
**Definition**: Registered 501(c)(3) organizations with NTEE prefix X3 per 10,000 residents.  
**Source**: IRS EO BMF, filtered by NTEE prefix "X3".  
**Unit**: orgs per 10,000 residents (reported, not scored).

**Why excluded**: IRS NTEE code X30 functions as a catch-all that captures congregations alongside human-service providers. The category is dominated by congregations whose primary identity is devotional rather than service-oriented. Many faith organizations that *do* primarily deliver social services register under P or E/K instead. V4 will explore combining X3x with faith-affiliated P/E/K registrations for a more complete measure.

---

### Pillar 3: Economic Access to Care

#### 3.6 Healthcare Coverage Rate (Medicaid/CHIP)
**Definition**: Fraction of the likely-eligible population actually enrolled in Medicaid or means-tested public health coverage, expressed as a rate 0–100.  
**Formula**: min( medicaid_enrolled / eligible_pop_0–149%_FPL × 100, 100 )  
**Source**: U.S. Census Bureau, ACS 5-year estimates (2022). C27007 (Medicaid/means-tested public coverage by sex by age) for enrollment; C17002 (ratio of income to poverty level) for the 0–149% FPL eligibility denominator.  
**Unit**: % coverage rate (higher = better).  
**Weight within Pillar 3**: **40%**  
**Benchmark**: 100% — the score equals the raw coverage rate directly. A city where enrolled = eligible scores 100; cities below that score their literal percentage.

**Rationale**: Healthcare coverage measures whether people can enter the care system when they need it. The metric isolates the public safety net signal: it counts Medicaid and CHIP enrollees (the deliberate care system for vulnerable people) rather than all insurance (which includes employer-sponsored coverage that reflects labor market conditions, not care infrastructure). A tech-industry city where 95% of residents have employer insurance scores no differently on this metric than a city where 95% of residents couldn't afford care at all — both would score 0 on Medicaid reach if none of their low-income residents were enrolled. Conversely, cities in generous Medicaid expansion states score high because the system is actually reaching the people it was designed to serve.

The eligibility-rate denominator (0–149% FPL, using ACS C17002) mirrors the SNAP coverage formula. This means non-expansion states score lower for the right reason: people who would be eligible for Medicaid in an expansion state are in the denominator but can't enroll, directly penalizing the policy failure. It also means wealthy cities with few low-income residents score neither inflated nor penalized — what matters is whether the people who could use Medicaid are actually enrolled.

**V6 note**: Previous versions used B27001 (any health insurance), which bundled employer-sponsored coverage with Medicaid/CHIP and inflated scores for prosperous cities. V6 switches to C27007, which isolates the public program signal. Benchmark lowered from 95% (B27001 basis) to 85% (C27007 coverage-rate basis).

**Relationship to FQHC density**: See Section 3.4 for the FQHC/coverage mismatch interpretation table. The two metrics are kept separate because FQHCs are specifically designed to serve Medicaid and uninsured populations — combining them would invert FQHC's intent.

#### 3.7 Housing Affordability (% Not Cost-Burdened)
**Definition**: Percentage of households NOT spending more than 30% of income on housing costs, combining renter-occupied (Census B25070) and owner-occupied (Census B25091) units.  
**Source**: U.S. Census Bureau, American Community Survey 5-year estimates (2022).  
**Unit**: % of households not cost-burdened (higher = better).  
**Weight within Pillar 3**: **35%**  
**Benchmark**: 90% not burdened (10% burdened ceiling).

**Rationale**: Housing cost burden is an enabling condition for care — financial stress suppresses community participation, network formation, and the capacity to provide or receive care. Agha et al. (2024) demonstrate that housing cost burden's effect on social capital is mediated through residential stability. Desmond's research establishes that high cost burden triggers eviction risk, forced moves, and erosion of care networks.

**V5 note**: Moved from Pillar 1 (Social Fabric) to Pillar 3 (Economic Access to Care). Housing cost burden measures an economic access barrier, not a relational capacity. Its theoretical home is among the enabling conditions that determine whether care infrastructure reaches people, not among the relational signals that constitute the social fabric.

**Forced-immobility interaction**: Cities that score high on residential stability (Section 3.1) but low here are candidates for forced-immobility bias — apparent social fabric may reflect constrained mobility rather than chosen rootedness. The two metrics should be read jointly: stability co-occurring with affordability signals genuine embeddedness; stability co-occurring with high cost burden is ambiguous.

**Measurement note**: Households with zero or negative income are excluded as "not computed" by Census. Relative city rankings remain valid; absolute percentages should not be compared to external sources without this caveat.

#### 3.8 SNAP Coverage Rate
**Definition**: Ratio of SNAP-receiving households to estimated eligible households, normalized to 0–100.  
**Formula**: (SNAP households / total households) ÷ (population at 0–149% FPL / total population) × 100, capped at 100.  
**Source**: U.S. Census Bureau, ACS 5-year estimates (2022). B22001 (SNAP receipt), C17002 (ratio of income to poverty level by band).  
**Unit**: % coverage (higher = better).  
**Weight within Pillar 3**: **25%**  
**Benchmark**: 85% — USDA FNS national SNAP participation target among eligible households.

**Rationale**: SNAP coverage rate measures whether food assistance infrastructure actually reaches the likely-eligible population — a direct measure of care system reach for food security specifically. Normalized by an approximated eligibility rate to avoid rewarding cities with high poverty for high SNAP volume. Weight reduced from 35% (V4) to 25% in V5 as Pillar 3 expanded to three metrics and housing cost burden was added as a more primary access signal.

**Eligibility denominator**: SNAP eligibility is federally defined at 130% FPL. Census C17002 provides the closest approximation: summing bands under 0.50, 0.50–0.99, 1.00–1.24, and 1.25–1.49 FPL yields the 0–149% FPL population. This replaces the V2 method using B17001 (100% FPL only), which overstated coverage rates in cities with large near-poverty populations.

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
| Care nonprofits (NTEE P+E+F+K) | 25 per 10,000 | Factor analysis showed NTEE P and E/F/K load on one dimension (r=0.85); collapsed into a single combined metric. 25/10k raised from 15/10k to restore discrimination after ZCTA-based filtering reduced county inflation |
| Library density | 5 per 100,000 | P90 across 68 cities; aspirational but achievable. Cities at median (~2.8/100k) score ~56; lowest-density cities score ~22 |
| FQHC density | 15 per 100,000 | Eliminates HRSA shortage designation plus geographic redundancy |
| Nursing home capacity | 50 per 1,000 residents 65+ | ~5% of elderly in skilled nursing at any one time; modestly above CMS national average (~42/1k) |
| Healthcare coverage (Medicaid/CHIP) | 100% | Score equals raw coverage rate directly (no benchmark normalization) |
| Housing affordability | 90% not burdened | 10% cost-burden ceiling; only the least-burdened US cities achieve this |
| SNAP coverage rate | 85% | USDA FNS national SNAP participation target among eligible households |

**Advantage over min-max scaling**: Scores are absolute — adding or removing cities does not change existing scores. A city's score reflects its performance against a standard, not against whoever else is in the comparison set.

**Benchmark sensitivity**: A shift of ±10% in any single benchmark changes that metric's score proportionally for all cities below the ceiling. For the combined care nonprofit benchmark (25/10k): raising it 10% to 27.5/10k reduces most city scores on that metric by roughly 4–8 points; lowering it 10% to 22.5/10k raises them by a similar amount. Because Pillar 1 is 40% of CQ and combined care nonprofits are 35% of Pillar 1, a 10% shift on this benchmark changes the final CQ by at most 1–2 points for most cities. The healthcare coverage and residential stability benchmarks have the largest CQ leverage because they sit in higher-weight positions; a ±10% shift there can move CQ by 2–4 points. Benchmark choices are documented and revisable; the absolute benchmark architecture makes these sensitivities explicit rather than hiding them in a relative scaling procedure.

---

## 5. Care Quotient Calculation

The Care Quotient (CQ) is a weighted composite of eight scored metrics, computed in two steps.

**Step 1 — Pillar scores** (weighted averages of constituent metrics):

```
Pillar 1 (Social & Relational Care) = (residential_stability × 0.50) + (combined_care × 0.35) + (library_density × 0.15)
Pillar 2 (Institutional Care)       = (fqhc_density × 0.55)          + (nursing_home_capacity × 0.45)
Pillar 3 (Economic Access to Care)  = (healthcare_coverage × 0.40)   + (housing_affordability × 0.35) + (snap_coverage × 0.25)
```

**Step 2 — Care Quotient**:

```
CQ = (Pillar 1 × 0.40) + (Pillar 2 × 0.35) + (Pillar 3 × 0.25)
```

All metric scores are on a 0–100 scale against absolute benchmarks (Section 4), so the CQ is also 0–100.

**Weight rationale (V5)**: Within-pillar weights reflect both empirical signals and theoretical commitments. Within Pillar 1, residential stability (50%) is the structural precondition — V3 factor analysis confirmed it as the dominant signal (loading 0.70). Combined care nonprofit density (35%) represents organized community response. Library density (15%) is newly scored in V5 and receives a smaller weight reflecting its role as a supportive rather than primary care institution. Within Pillar 2, V5 revises weights to 55/45 (FQHC/nursing homes) from the V4 35/35/30 split, reflecting the simplification from three to two institutional metrics. V4 factor analysis showed nursing homes load 0.91 on their own isolated factor — confirming elder care is a genuinely distinct institutional dimension. FQHCs receive slightly higher weight because they serve the full community age distribution under open-access mandate. Within Pillar 3, healthcare coverage (40%) is the primary access gate; housing affordability (35%) is the largest structural enabler of care engagement; SNAP coverage (25%) is more narrowly scoped to food security. NTEE P and E/F/K collapsed into a single combined metric after confirming r=0.85 correlation (V3 change retained).

**Inter-pillar weights: theory over data (deliberate)**: Factor analysis across 68 cities yields empirical inter-pillar weights of approximately pillar2: 0.48 / pillar1: 0.35 / pillar3: 0.17 — placing Institutional Care as the dominant empirical signal. V5 retains the theory-based 40/35/25 split instead, for a specific reason: the factor analysis identifies where variance *is* in the data, not necessarily where weight *should* be. Care ethics theory (Tronto 1993, Gilligan 1982) holds that the relational layer — the social fabric that generates attentiveness and responsibility — is the necessary precondition for institutional care to be meaningful. Communities without stable networks cannot absorb what institutions offer. Giving the relational pillar primary weight is a normative commitment, not an empirical claim. V6 will revisit with outcome validation.

**Individual metric scores remain the primary diagnostic output.** The CQ is a useful summary for comparison, but it compresses variation — a city can score at the CQ average while being strong on one pillar and weak on another.

---

## 6. Diagnostic Metrics (Not Scored)

The following metrics are collected and reported but excluded from pillar scores:

| Metric | Rationale for exclusion |
|--------|-------------------------|
| Library visits per capita | Supplementary engagement signal; collected alongside library density but not scored. |
| All care-related nonprofit density | Broad diagnostic count across all NTEE care codes. Useful for context but too aggregated to score; double-counts organizations captured in the scored sub-metrics. |
| Care nonprofits per 10k distressed (0–150% FPL) | Need-adjusted shadow diagnostic for combined care nonprofit density. Reported on city pages; not scored pending validation that ranking changes are interpretively meaningful. See Section 3.2. |
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

1. **Per-capita density systematically disadvantages large cities**: NYC has 437 FQHCs and thousands of nonprofits — enormous absolute capacity — but scores below the median on both density metrics because its population of 8.3M dilutes per-capita ratios. A city of 180k with 44 FQHCs scores higher per capita than a city of 8M with 437 FQHCs, even though the latter has roughly 10x the infrastructure. Whether this is correct depends on how access scales with density: in a compact, transit-connected city, per-capita ratios may overstate deprivation if geographic proximity compensates. This is not unique to NYC — all large dense cities (Chicago, Philadelphia, Los Angeles) face the same structural penalty. V4 will explore supplementing per-capita density with geographic access metrics (% of population within X distance of a facility). For now, scores for cities above ~1M population should be read with this caveat in mind.

2. **Benchmark judgment**: Nonprofit density benchmark (combined P+E+F+K at 25/10k) and SNAP/health insurance benchmarks are reasoned thresholds without a policy-derived standard. The FQHC and residential stability benchmarks are more firmly grounded. All benchmarks are documented explicitly and subject to revision.

3. **IRS EO BMF scope**: The BMF is filtered to active 501(c)(3) organizations (SUBSECTION=03, STATUS=01/02). 501(c)(4) social welfare organizations and 501(c)(6) business leagues that carry P/E/F/K NTEE codes are excluded (~2% of care-NTEE organizations nationally). The methodology commits to measuring charitable nonprofits specifically; social welfare and business organizations are excluded even when their stated activities overlap with care provision.

4. **Geographic filtering**: All data sources use the Census 2020 ZCTA-to-Place relationship file to define city boundaries. A ZCTA is assigned to a city if ≥40% of its land area falls within the Census incorporated place boundary. This threshold was lowered from 50% (used in V3.0–V3.1) after auditing confirmed that several FQHCs serving Raleigh and Fort Worth residents were in ZCTAs with 41–49% land-area overlap with the city boundary — near-urban-core locations excluded by the stricter cutoff. The 40% threshold includes ZCTAs where a meaningful plurality of land is within the city; all ZCTAs added by this change fell in the 40–49% band. Land-area overlap is an imperfect proxy for population served; ZCTAs at the urban fringe often have their population concentrated in the urban portion. This methodology may still undercount services for cities with irregular boundaries or large rural annexations.

5. **Honolulu geography**: Hawaii has no incorporated municipalities — Honolulu is a Census Designated Place (CDP) absent from the ZCTA-to-Place crosswalk. The pipeline falls back to a county-based boundary (Honolulu County, ~1M residents), which is substantially larger than the urban core (~350k). All per-capita density metrics for Honolulu use city population as the denominator while org/facility counts reflect the broader county geography. Honolulu's scores should be interpreted with this caveat: density metrics may be modestly overstated relative to incorporated cities of similar size. Honolulu is the only city in V3 affected by this fallback.

6. **Faith-based measurement**: X30 codes capture congregations, not specifically human-service providers. Faith-based density is reported as a diagnostic metric rather than scored (see Section 3.6).

7. **Density vs. access**: Per-capita density measures presence, not accessibility. A health center in one part of a large city does not serve all residents equally.

8. **Residential stability: chosen vs. forced immobility and survivorship bias**: High residential stability can reflect embedded social networks (Putnam 2000; Sampson et al. 1997), but it can equally reflect economic immobility — poverty traps and exclusionary housing markets that prevent people from leaving even when conditions are poor. The housing affordability counter-weight (Section 3.7) partially addresses forced immobility, but ACS data cannot fully distinguish chosen from forced stability. Additionally, the ACS stability variable is a survivorship measure: it captures only current residents, so people who left the metropolitan area entirely are absent from the frame. The metric measures stability among those who stayed, not citywide retention. Both limitations are known and documented; neither is sufficient reason to drop the metric, but both counsel against over-reading small differences in residential stability scores between cities.

9. **Housing cost burden undercount**: The Census B25070/B25091 methodology excludes households with zero or negative income ("not computed"), which can understate true cost burden rates compared to HUD CHAS figures. Relative city rankings are valid; absolute percentages should not be compared to external sources without this caveat.

10. **Health insurance and state policy**: Health insurance coverage reflects state-level Medicaid expansion decisions as much as local care infrastructure. Texas (Houston) did not expand Medicaid under the ACA, which contributes significantly to its lower score on this metric. This is treated as a real care access failure attributable to the state — see Section 3.7 rationale.

11. **SNAP eligibility approximation**: The SNAP formula divides a household receipt rate (SNAP households / total households) by a population poverty rate (0–149% FPL population / total population). These are different universe denominators — household vs. person — introducing a structural approximation. This is the best available approach with Census ACS data; the coverage rate should be interpreted as an index rather than a precise participation percentage. The V2 formula additionally used B17001 (100% FPL) as the denominator; V3 corrects this to C17002 (0–149% FPL), which more accurately approximates the 130% FPL SNAP eligibility threshold.

12. **ACS 5-year estimate smoothing**: The 2022 ACS 5-year estimates pool survey responses from 2018–2022, smoothing rapid demographic shifts. Cities undergoing rapid population change (fast-growing Sun Belt metros, post-pandemic migration destinations) may have metrics that lag current conditions by 1–3 years. Close rankings — cities within 3–4 points of each other — should not be over-read; differences of that size can fall within ACS estimation variance, particularly for smaller cities where the survey sample is thinner.

13. **Total-population vs. need-adjusted denominator**: All per-capita density metrics use total city population as the denominator. An alternative framing normalizes by the population most likely to need care-related services — residents below 150% of the Federal Poverty Level. These two denominators tell different stories: the total-population denominator measures citywide supply per resident, while a need-adjusted denominator measures supply relative to likely demand. Large cities with concentrated poverty (where the total population is high but the low-income population represents a smaller share) tend to score lower under total-population normalization than under need-adjusted normalization. V5 reports care nonprofit density per 10,000 residents at 0–150% FPL as a shadow diagnostic to test whether rankings diverge materially between the two framings.

---

## 10. V3 Changes (Implemented)

The following improvements were implemented in V3:

- **Scale to 68 cities**: ZCTA-to-place crosswalk filtering replaces city-name matching across IRS, IMLS, and HRSA datasets. Eliminates name-matching errors and county-sharing inflation.
- **ZCTA-based geographic filtering**: All data sources (IRS EO BMF, IMLS, HRSA, Census ACS) now use the Census 2020 ZCTA-to-Place relationship file to define city boundaries consistently. A ZCTA is assigned to a city if ≥40% of its land area falls within the Census incorporated place boundary. (V3.0–V3.1 used a 50% threshold; lowered in V3.2 after confirming the stricter cutoff was excluding FQHCs in near-urban-core ZCTAs for Raleigh and Fort Worth.)
- **SNAP eligibility denominator corrected**: C17002 (0–149% FPL) replaces B17001 (100% FPL) as the SNAP coverage denominator. See Section 3.6.
- **Nonprofit metrics collapsed**: Factor analysis across 68 cities showed NTEE P and NTEE E/F/K correlate at r=0.85 and load on the same factor. Collapsed into a single combined care nonprofit metric (P+E+F+K) in Pillar 2. Sub-components retained as diagnostics.
- **Within-pillar weights revised**: Empirical factor loadings used to update weights. Residential stability raised from 48% to 65%; housing affordability raised from 12% to 35%; health insurance raised from 40% to 65%; SNAP lowered from 60% to 35%.
- **NP benchmark raised**: Combined care NP benchmark raised from 15/10k to 25/10k to restore score discrimination after ZCTA-based filtering reduced county-inflated counts.

## 11. V4 Changes (Implemented)

- **Nursing home capacity added** (Section 3.5): CMS Care Compare Medicare/Medicaid certified nursing homes; certified beds per 1,000 residents 65+. Benchmark: 50/1k. Wired into all 68 cities.
- **Pillar 2 weights revised**: Combined care NPs 50% → 35%, FQHC density 50% → 35%, nursing home capacity added at 30%. The previous 50/50 split is replaced by a 35/35/30 split to accommodate the new metric. Factor analysis confirms nursing home capacity is an independent dimension (loading 0.91 on its own factor) that is not captured by the existing Pillar 2 metrics.
- **7-metric model**: CQ is now a composite of 7 scored metrics (previously 6).

## 12. V5 Changes (Implemented)

- **Pillar restructuring based on care theory**: Three new pillar names grounded in Tronto (1993), Putnam (2000), and Sampson et al. (1997): Social & Relational Care (40%), Institutional Care (35%), Economic Access to Care (25%). See Section 2.
- **Library density promoted to scored metric** (Pillar 1, 15%): Public libraries are de facto community care infrastructure — distress absorption sites, information and service access points, and programming hubs for isolated populations. Benchmark: 5 per 100,000 (P90 across 68 cities). See Section 3.3.
- **Combined care nonprofit density moved from Pillar 2 to Pillar 1**: Nonprofits represent organized community response (Tronto: responsibility phase) — relational before institutional. Within-Pillar 1 weight: 35%.
- **Housing cost burden moved from Pillar 1 to Pillar 3**: Measures an economic access barrier, not a relational capacity. Within-Pillar 3 weight: 35%. See Section 3.7.
- **Pillar 1 weights revised**: Residential stability 65% → 50%; combined care nonprofits 35% (unchanged but now in a 3-metric pillar); library density 15% (new).
- **Pillar 2 simplified to two institutional metrics**: FQHC density (55%) and nursing home capacity (45%). Weights revised from V4's 35/35/30.
- **Pillar 3 expanded to three metrics**: Healthcare coverage (40%), housing affordability (35%), SNAP coverage (25%).
- **Healthcare coverage renamed and regrounded**: "Health Insurance Coverage" (B27001, any coverage) → "Healthcare Coverage Rate" (C27007, Medicaid/CHIP specifically). New metric measures fraction of the 0–149% FPL population enrolled in Medicaid/means-tested public coverage, analogous to the SNAP coverage formula. Benchmark: 85%. This removes the employer-insurance inflation in wealthy cities and penalizes Medicaid non-expansion states for the right reason.
- **Need-adjusted shadow diagnostic added**: Combined care nonprofit density per 10,000 residents at 0–150% FPL reported as a diagnostic metric on city pages. Not scored pending validation.
- **8-metric model**: CQ is now a composite of 8 scored metrics (previously 7 in V4, 6 in V3).

## 13. Planned V6 Improvements

- **Mental health capacity**: HRSA behavioral health shortage area data or SAMHSA treatment facility survey. Candidate metric for a future Pillar 2 expansion.
- **Child care capacity**: HIFLD national childcare facilities dataset. Potential new Pillar 2 metric or standalone pillar.
- **Home health capacity**: CMS Care Compare home health dataset (6jpm-sxkc) — deferred because CMS attributes episodes to agency headquarters ZIP, not patient location. Revisit when a clean geographic attribution method is identified.
- **NYC neighborhood-level pilot**: Borough-level ZCTA crosswalk for sub-city view in New York City. Other cities with clearly-defined sub-city geographies (e.g., Chicago community areas) as secondary candidates.
- **CDC PLACES community wellbeing diagnostics**: Mental distress prevalence, self-rated health, and social isolation measures as diagnostic overlays on city pages (not scored).
- **Scale to 100 cities**: Add the remaining ~32 cities to reach the 100-city target.
- **Faith-based measurement**: Combine X3x with faith-affiliated P/E/K registrations for a more complete measure of congregational social services.
- **FQHC capacity weighting**: Weight health center density by reported patient capacity rather than site count (UDS data).
- **Benchmark sensitivity documentation**: Publish a sensitivity table showing the effect of ±10% shifts on each benchmark on final CQ scores for all 68 cities.
- **Empirical inter-pillar weight review**: Review factor analysis outputs and decide whether to adopt empirically-derived inter-pillar weights or retain the theory-based 40/35/25 split.
- **"What is Care?" theory page**: Dedicated site page citing Tronto, Putnam, Sampson, Kittay, Folbre with full metric-to-theory mapping. Planned as the final V6 addition once the data pipeline is stable.

---

## 14. References

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
