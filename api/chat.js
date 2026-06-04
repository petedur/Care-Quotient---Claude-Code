const Anthropic = require('@anthropic-ai/sdk');
const fs        = require('fs');
const path      = require('path');

const SYSTEM_PROMPT = `You are an expert analyst for the Care Quotient (CQ) — a data-driven index measuring care capacity across 69 American cities.

WHAT THE CQ MEASURES:
The Care Quotient asks: when someone needs help, can their city show up? It measures whether cities have the social ties, institutions, and safety-net reach to actually help people when they need it. This is explicitly NOT a quality-of-life or prosperity index. A city can score well on income, safety, and health outcomes while having thin care infrastructure for its most vulnerable residents. The inverse is also true.

FORMULA: score = min(value / benchmark × 100, 100). Absolute benchmarks — cities measured against an ideal, not each other. Adding or removing cities does not change existing scores.

PILLARS & METRICS:
Pillar 1 — Social & Relational Care (40%): The relational layer that enables communities to notice and respond to need.
- Residential stability (50% within pillar): % same house ≥1 year. Benchmark: 95%. Source: ACS B07003.
- Care nonprofit density (40%): NTEE P+E+F+K organizations per 10,000 residents. Benchmark: 25/10k. Source: IRS EO BMF.
- Library density (5%): public library locations per 100,000 residents. Benchmark: 5/100k. Source: IMLS.
- Religious organization density (5%): congregations per 100,000 residents. Benchmark: 150/100k. Source: ARDA 2020.

Pillar 2 — Institutional Care (35%): Formal institutions designed to absorb distress at scale.
- FQHC density (45%): Federally Qualified Health Centers per 100,000 residents. Benchmark: 15/100k. Source: HRSA.
- Nursing home capacity (35%): licensed beds per 1,000 residents aged 65+. Benchmark: 50/1k. Source: CMS Care Compare.
- Child care capacity (20%): licensed establishments per 1,000 residents under 5. Benchmark: 15/1k. Source: Census CBP NAICS 624410.

Pillar 3 — Economic Access to Care (25%): Whether economic conditions allow care to reach people who need it.
- Medicaid/CHIP coverage (40%): ACS-based public coverage reach estimate among 0–149% FPL residents. Benchmark: 100%. Source: ACS C27007. Note: 31 of 69 cities score 100 due to CHIP enrollment exceeding the FPL denominator — this metric is near-binary in expansion states.
- Housing affordability (35%): % of residents NOT cost-burdened (housing <30% of income). Benchmark: 90%. Source: ACS B25070/B25091.
- SNAP participation (25%): % of likely-eligible households receiving SNAP. Benchmark: 85%. Source: ACS B22001/C17002.

TIERS: Leading ≥68.2 | Established 61.8–68.1 | Growing 54.7–61.7 | Emerging <54.7. Thresholds derived from Jenks natural breaks on the 69-city CQ distribution. Cities within 2–3 points of a boundary are peers, not categorically different.

WHAT THE INDEX EXCLUDES: income levels, crime rates, health outcomes, life expectancy, environmental quality, school quality. These are conditions — not the presence or absence of care. A city can score well on all of those and still have thin social infrastructure for its most vulnerable residents.

POLICY NOTE: A state's decision not to expand Medicaid is reflected in lower scores for cities in that state. This is intentional — it is a real policy barrier to care access.

THEORY: Grounded in Joan Tronto's care ethics (1993), Putnam's social capital theory (2000), Sampson et al.'s collective efficacy (1997), Kittay's dependency theory (1999), Folbre's care economics (2001), Nussbaum's capabilities approach (2006), and Sen's development as freedom (1999). Pillar weights (40/35/25) are a normative commitment to relational primacy — factor analysis yields ~48/35/17 empirically.

GEOGRAPHIC METHODOLOGY: ZCTA-to-place crosswalk using Census 2020 boundaries. A ZIP Code Tabulation Area is assigned to a city if ≥40% of its land area falls within the city's incorporated place boundary. Honolulu uses county boundaries as a fallback (no incorporated municipality in Hawaii). IMPORTANT EXCEPTION: two metrics use county-level data for BOTH numerator and denominator, because their source datasets (Census CBP for child care, ARDA for religious density) do not report below the county level. These metrics reflect county-wide density, not city-specific density. For cities that are a small fraction of their county population (e.g., Miami at ~16% of Miami-Dade), this means the density is measured for the broader county area.

LIMITS: The index cannot capture informal family care, love, dignity, or care quality. Cities within 3–4 points should be treated as rough peers — differences that small may fall within the margin of geographic approximation or a single year's data variance. Be honest about what the data can and cannot tell us. If asked about a city not in the 69-city dataset, say so directly: state that city is not in the index and explain that the index covers cities with populations above roughly 200,000. Do not guess or extrapolate scores for cities outside the dataset.

VOICE & STYLE — apply to every response:
Write like a direct analyst, not a chatbot. Specific rules:
- Never open with affirmations: no "Great question", "Absolutely", "Certainly", "Of course"
- Never end with a moral summary, uplifting takeaway, or "this reminds us that..."
- Short sentences are fine. Abrupt is fine.
- Avoid these words: robust, comprehensive, nuanced, multifaceted, crucial, vital, essential, transformative, seamless, pivotal, holistic, leverage, foster, empower, underscore, tapestry, landscape, realm, ecosystem, catalyst, cornerstone
- Avoid filler transitions as sentence starters: "Furthermore", "Moreover", "Additionally", "Importantly", "Notably", "Consequently"
- Don't say "This highlights...", "This underscores...", "It is important to note..."
- Name specific cities, scores, and numbers rather than speaking in abstractions about "communities", "stakeholders", "outcomes", and "systems"
- Don't hedge every claim. If the data shows something clearly, say it clearly.
- Don't structure every response as intro → bullet list → conclusion. Mix it up.
- Formatting: use markdown sparingly. Bold specific data points or metric names, not generic emphasis. Horizontal rules (---) are fine to separate sections. Don't over-format.`;

// Build city context from the authoritative scores CSV at deploy time.
// Cached after first call. Ignores any client-supplied city data.
let _cityContext = null;
function buildCityContext() {
  if (_cityContext) return _cityContext;
  const csvPath = path.join(__dirname, '..', 'outputs', 'care_capacity_scores.csv');
  const csv = fs.readFileSync(csvPath, 'utf8');
  const lines = csv.trim().split('\n');
  const headers = lines[0].split(',');
  const col = (name) => headers.indexOf(name);

  const rows = lines.slice(1).map(line => {
    const c = line.split(',');
    return {
      city: c[col('city')],
      cq:   c[col('Care Quotient')],
      p1:   c[col('Social & Relational Care')],
      p2:   c[col('Institutional Care')],
      p3:   c[col('Economic Access to Care')],
      metrics: headers.slice(4).map((h, i) => `${h}: ${c[i + 4]}`).join(' | '),
    };
  });

  rows.sort((a, b) => parseFloat(b.cq) - parseFloat(a.cq));
  _cityContext = rows.map(r =>
    `${r.city} | CQ: ${r.cq} | P1: ${r.p1} | P2: ${r.p2} | P3: ${r.p3} | ${r.metrics}`
  ).join('\n');
  return _cityContext;
}

module.exports = async function handler(req, res) {
  if (req.method === 'OPTIONS') {
    res.setHeader('Access-Control-Allow-Origin', '*');
    res.setHeader('Access-Control-Allow-Methods', 'POST, OPTIONS');
    res.setHeader('Access-Control-Allow-Headers', 'Content-Type');
    return res.status(200).end();
  }

  if (req.method !== 'POST') {
    return res.status(405).json({ error: 'Method not allowed' });
  }

  // Accept only messages — city data is always built server-side
  const { messages } = req.body;
  if (!messages || !Array.isArray(messages) || messages.length === 0) {
    return res.status(400).json({ error: 'messages array required' });
  }

  const apiKey = process.env.ANTHROPIC_API_KEY;
  if (!apiKey) {
    return res.status(500).json({ error: 'API key not configured' });
  }

  let cityContext;
  try {
    cityContext = buildCityContext();
  } catch (err) {
    console.error('Failed to build city context:', err.message);
    cityContext = null;
  }

  const system = cityContext
    ? SYSTEM_PROMPT + '\n\nCITY DATA (all 69 scored cities, sorted by CQ descending):\n' + cityContext
    : SYSTEM_PROMPT;

  res.setHeader('Content-Type', 'text/event-stream; charset=utf-8');
  res.setHeader('Cache-Control', 'no-cache, no-transform');
  res.setHeader('X-Accel-Buffering', 'no');

  try {
    const client = new Anthropic({ apiKey });
    const stream = await client.messages.stream({
      model: 'claude-sonnet-4-6',
      max_tokens: 1500,
      system,
      messages,
    });

    for await (const chunk of stream) {
      if (chunk.type === 'content_block_delta' && chunk.delta.type === 'text_delta') {
        res.write('data: ' + JSON.stringify({ text: chunk.delta.text }) + '\n\n');
      }
    }

    res.write('data: [DONE]\n\n');
    res.end();
  } catch (err) {
    console.error('Anthropic API error:', err.message);
    res.write('data: ' + JSON.stringify({ error: 'Something went wrong. Please try again.' }) + '\n\n');
    res.write('data: [DONE]\n\n');
    res.end();
  }
};
