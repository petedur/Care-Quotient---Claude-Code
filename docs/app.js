// ── Utilities ──────────────────────────────────────────────────────────────

function fmt(n, decimals) {
  return Number(n).toFixed(decimals === undefined ? 1 : decimals);
}

function getCitiesSorted() {
  return Object.entries(CITIES)
    .map(([key, city]) => ({ key, ...city }))
    .sort((a, b) => b.cq - a.cq);
}

function getRank(cityKey) {
  return getCitiesSorted().findIndex(c => c.key === cityKey) + 1;
}

function animateBars(containerEl, selector, delay) {
  delay = delay || 80;
  const fills = containerEl.querySelectorAll(selector);
  fills.forEach(function(fill, i) {
    setTimeout(function() {
      fill.style.width = fill.dataset.target + '%';
    }, delay + i * 7);
  });
}

// ── Router ─────────────────────────────────────────────────────────────────

function route() {
  var hash = window.location.hash.slice(1) || '/';
  var app  = document.getElementById('app');

  if (hash === '/' || hash === '') {
    renderHome(app);
  } else if (hash.indexOf('/city/') === 0) {
    renderCity(app, hash.slice(6));
  } else if (hash === '/methodology') {
    renderMethodology(app);
  } else {
    app.innerHTML = [
      '<div class="not-found">',
        '<p>Page not found.</p>',
        '<a href="#/">&#8592; Back to the index</a>',
      '</div>'
    ].join('');
  }

  window.scrollTo(0, 0);
}

window.addEventListener('hashchange', route);
window.addEventListener('DOMContentLoaded', route);

// ── Home ────────────────────────────────────────────────────────────────────

function renderHome(app) {
  var cities = getCitiesSorted();
  var total  = cities.length;

  var rows = cities.map(function(city, i) {
    return [
      '<a class="ranking-row" href="#/city/', city.key, '"',
        ' role="link" tabindex="0"',
        ' aria-label="', city.name, ', Care Quotient ', fmt(city.cq), '">',
        '<span class="r-rank">', i + 1, '</span>',
        '<span class="r-name">',  city.name, '</span>',
        '<span class="r-state">', city.state, '</span>',
        '<div class="r-bar">',
          '<div class="r-bar-fill" data-target="', fmt(city.cq, 1), '"></div>',
        '</div>',
        '<span class="r-score">', fmt(city.cq), '</span>',
      '</a>'
    ].join('');
  }).join('');

  app.innerHTML = [
    // ── Hero ──────────────────────────────────────────────────────────────
    '<section class="hero">',
      '<div class="hero-eyebrow">Care Quotient &mdash; V3 &mdash; 68 American Cities</div>',
      '<h1 class="hero-headline">When someone needs help,<br>can their city show up?</h1>',
      '<div class="hero-rule"></div>',
      '<p class="hero-subhead">',
        'A data-driven index measuring care capacity across 68 American cities &mdash; ',
        'not prosperity, not health outcomes, but the social networks, institutions, ',
        'and systems that determine whether people can get help when they need it.',
      '</p>',
    '</section>',

    // ── Ranking ───────────────────────────────────────────────────────────
    '<section class="section-wrap">',
      '<div class="ranking-header">',
        '<span class="section-label">The Index &mdash; ', total, ' Cities</span>',
        '<input class="city-search" id="city-search" type="search"',
          ' placeholder="Find a city&hellip;" autocomplete="off" spellcheck="false">',
      '</div>',

      '<div class="col-headers">',
        '<span class="col-h right">#</span>',
        '<span class="col-h">City</span>',
        '<span class="col-h">State</span>',
        '<span class="col-h">Care Quotient</span>',
        '<span class="col-h right">Score</span>',
      '</div>',

      '<div id="ranking-table">', rows, '</div>',
      '<div class="no-results" id="no-results">No cities match your search.</div>',
    '</section>',

    // ── Pillars ───────────────────────────────────────────────────────────
    '<section class="section-wrap">',
      '<span class="section-label">How It&rsquo;s Measured</span>',
      '<div class="pillars-grid">',

        '<div class="pillar-card">',
          '<div class="pillar-card-weight">40% of CQ</div>',
          '<div class="pillar-card-name">Social Fabric</div>',
          '<div class="pillar-card-desc">',
            'Whether the conditions for community care exist &mdash; stable residential ',
            'networks and housing markets that allow people to stay embedded in their communities.',
          '</div>',
        '</div>',

        '<div class="pillar-card p2">',
          '<div class="pillar-card-weight">35% of CQ</div>',
          '<div class="pillar-card-name">Institutions of Care</div>',
          '<div class="pillar-card-desc">',
            'Whether institutions specifically designed to absorb distress are present &mdash; ',
            'care-oriented nonprofits and federally qualified health centers.',
          '</div>',
        '</div>',

        '<div class="pillar-card p3">',
          '<div class="pillar-card-weight">25% of CQ</div>',
          '<div class="pillar-card-name">Reach</div>',
          '<div class="pillar-card-desc">',
            'Whether care systems actually connect with the people who need them &mdash; ',
            'measuring health insurance coverage and SNAP participation among likely-eligible households.',
          '</div>',
        '</div>',

      '</div>',
    '</section>',

    renderFooter(),
  ].join('');

  // Animate ranking bars (staggered)
  var rankingTable = document.getElementById('ranking-table');
  setTimeout(function() {
    animateBars(rankingTable, '.r-bar-fill', 80);
  }, 120);

  // Live search
  var searchInput = document.getElementById('city-search');
  var noResults   = document.getElementById('no-results');

  searchInput.addEventListener('input', function() {
    var q = searchInput.value.toLowerCase().trim();
    var visible = 0;
    rankingTable.querySelectorAll('.ranking-row').forEach(function(row) {
      var name  = row.querySelector('.r-name').textContent.toLowerCase();
      var state = row.querySelector('.r-state').textContent.toLowerCase();
      var show  = !q || name.indexOf(q) !== -1 || state.indexOf(q) !== -1;
      row.classList.toggle('hidden', !show);
      if (show) visible++;
    });
    noResults.style.display = visible === 0 ? 'block' : 'none';
  });
}

// ── City page ───────────────────────────────────────────────────────────────

var PILLAR_META = {
  pillar1: { label: 'Social Fabric',        color: 'var(--p1)' },
  pillar2: { label: 'Institutions of Care', color: 'var(--p2)' },
  pillar3: { label: 'Reach',                color: 'var(--p3)' },
};

var METRIC_META = {
  residential_stability: {
    label:  'Residential Stability',
    pillar: 'pillar1',
    desc:   '% of population in same home 1+ years',
  },
  housing_cost_burden: {
    label:  'Housing Affordability',
    pillar: 'pillar1',
    desc:   '% of households not spending >30% of income on housing',
  },
  combined_care: {
    label:  'Care Nonprofits',
    pillar: 'pillar2',
    desc:   'Human services & health orgs per 10,000 residents (NTEE P+E+F+K)',
  },
  fqhc: {
    label:  'Health Centers (FQHCs)',
    pillar: 'pillar2',
    desc:   'Federally Qualified Health Centers per 100,000 residents',
  },
  health_insurance: {
    label:  'Health Insurance Coverage',
    pillar: 'pillar3',
    desc:   '% of population with any health insurance',
  },
  snap_coverage: {
    label:  'SNAP Coverage',
    pillar: 'pillar3',
    desc:   'SNAP participation among likely-eligible households',
  },
};

var METRIC_ORDER = [
  'residential_stability',
  'housing_cost_burden',
  'combined_care',
  'fqhc',
  'health_insurance',
  'snap_coverage',
];

function renderCity(app, key) {
  var city = CITIES[key];
  if (!city) {
    app.innerHTML = [
      '<div class="not-found">',
        '<p>City not found.</p>',
        '<a href="#/">&#8592; Back to the index</a>',
      '</div>'
    ].join('');
    return;
  }

  var rank  = getRank(key);
  var total = Object.keys(CITIES).length;

  // Pillar cards
  var pillarCards = ['pillar1', 'pillar2', 'pillar3'].map(function(pk) {
    var pm    = PILLAR_META[pk];
    var score = fmt(city[pk]);
    return [
      '<div class="city-pillar-box">',
        '<div class="city-pillar-label">', pm.label, '</div>',
        '<div class="city-pillar-score">', score, '</div>',
        '<div class="mini-bar-track">',
          '<div class="mini-bar-fill"',
               ' style="background:', pm.color, '"',
               ' data-target="', score, '"></div>',
        '</div>',
      '</div>',
    ].join('');
  }).join('');

  // Metric rows — group by pillar with a label break
  var currentPillar = null;
  var metricHtml = METRIC_ORDER.map(function(mk) {
    var m    = city.metrics[mk];
    var meta = METRIC_META[mk];
    if (!m || !meta) return '';

    var pm    = PILLAR_META[meta.pillar];
    var color = pm.color;
    var score = fmt(m.score);

    var pillarBreak = '';
    if (meta.pillar !== currentPillar) {
      currentPillar = meta.pillar;
      pillarBreak = [
        '<div class="metrics-label" style="margin-top:1.5rem;margin-bottom:0.5rem;color:',
          color, '">', pm.label, '</div>',
      ].join('');
    }

    var row = [
      '<div class="metric-row">',
        '<div>',
          '<div class="metric-name">', meta.label, '</div>',
          '<div class="metric-detail">',
            m.rawFmt,
            ' &nbsp;&middot;&nbsp; Benchmark: ', m.benchmark,
            ' &nbsp;&middot;&nbsp; ', meta.desc,
          '</div>',
        '</div>',
        '<div class="metric-score-side">',
          '<div class="metric-score-num">', score, '</div>',
          '<div class="metric-bar-track">',
            '<div class="metric-bar-fill"',
                 ' style="background:', color, '"',
                 ' data-target="', score, '"></div>',
          '</div>',
        '</div>',
      '</div>',
    ].join('');

    return pillarBreak + row;
  }).join('');

  // Geography caveat for CDP cities where county fallback was used
  var geoCaveat = '';
  if (key === 'honolulu') {
    geoCaveat = [
      '<div class="geo-caveat">',
        '<strong>Geography note:</strong> Hawaii has no incorporated municipalities. ',
        'Honolulu is a Census Designated Place, so data reflects Honolulu County ',
        'boundaries rather than the urban core. Density metrics may be modestly overstated ',
        'relative to other cities. See <a href="#/methodology">Methodology &sect;9</a>.',
      '</div>',
    ].join('');
  }

  app.innerHTML = [
    '<div class="city-page">',

      '<a href="#/" class="back-link">&#8592; All cities</a>',

      geoCaveat,

      '<div class="city-title">', city.name, '</div>',
      '<div class="city-meta">', city.state, ' &nbsp;&middot;&nbsp; ', city.population, '</div>',

      '<div class="cq-display">',
        '<div class="cq-number">', fmt(city.cq), '</div>',
        '<div class="cq-aside">',
          '<div class="cq-label">Care Quotient</div>',
          '<div class="cq-rank">Ranked ', rank, ' of ', total, ' cities</div>',
        '</div>',
      '</div>',

      '<div class="divider"></div>',

      '<div class="city-pillars">', pillarCards, '</div>',

      '<div class="divider"></div>',

      metricHtml,

    '</div>',
    renderFooter(),
  ].join('');

  // Animate all bars
  var page = app.querySelector('.city-page');
  setTimeout(function() {
    animateBars(page, '.mini-bar-fill',   80);
    animateBars(page, '.metric-bar-fill', 200);
  }, 80);
}

// ── Methodology ─────────────────────────────────────────────────────────────

function renderMethodology(app) {
  app.innerHTML = [
    '<div class="method-page">',

      '<a href="#/" class="back-link">&#8592; All cities</a>',

      '<div class="method-eyebrow">Methodology &mdash; V3</div>',
      '<h1>How the Care Quotient is built</h1>',

      '<p>',
        'The Care Quotient measures <strong>care capacity</strong> &mdash; the extent to which a ',
        'community has the social ties, institutions, and systems needed to support people in ',
        'moments of vulnerability. This is explicitly <em>not</em> a quality-of-life index. A city ',
        'can score well on income, safety, and health outcomes while having thin care infrastructure ',
        'for its most vulnerable residents. The inverse is also true.',
      '</p>',

      '<p>',
        'The motivating question is whether communities have what it takes to <em>show up</em> &mdash; ',
        'through networks, institutions, and reach &mdash; when people need help.',
      '</p>',

      '<h2>Three Pillars</h2>',

      '<p>',
        'The CQ is a weighted composite of six scored metrics organized into three pillars. ',
        'Inter-pillar weights reflect the primacy of the relational layer (care ethics tradition) ',
        'balanced against the institutional layer (capabilities approach). Within-pillar weights ',
        'are informed by factor analysis across 68 cities.',
      '</p>',

      '<table class="method-table">',
        '<thead><tr>',
          '<th>Pillar</th><th>What it measures</th><th>Weight</th>',
        '</tr></thead>',
        '<tbody>',
          '<tr>',
            '<td><span class="ptag ptag-p1">Social Fabric</span></td>',
            '<td>Residential stability &amp; housing affordability &mdash; conditions that allow people to stay embedded in their communities.</td>',
            '<td>40%</td>',
          '</tr>',
          '<tr>',
            '<td><span class="ptag ptag-p2">Institutions of Care</span></td>',
            '<td>Care nonprofit density &amp; FQHC density &mdash; organizations specifically designed to absorb distress.</td>',
            '<td>35%</td>',
          '</tr>',
          '<tr>',
            '<td><span class="ptag ptag-p3">Reach</span></td>',
            '<td>Health insurance coverage &amp; SNAP participation &mdash; whether systems connect with people who need them.</td>',
            '<td>25%</td>',
          '</tr>',
        '</tbody>',
      '</table>',

      '<h2>Benchmarks</h2>',

      '<p>',
        'Each metric is scored against an absolute benchmark representing a theoretical ideal. ',
        '<code>score = min(value / benchmark &times; 100, 100)</code>. ',
        'Scores are absolute &mdash; adding or removing cities does not change existing scores.',
      '</p>',

      '<table class="method-table">',
        '<thead><tr>',
          '<th>Metric</th><th>Benchmark</th><th>Source</th>',
        '</tr></thead>',
        '<tbody>',
          '<tr><td>Residential Stability</td>  <td>95% same house 1+ yr</td>       <td>Census ACS B07003</td></tr>',
          '<tr><td>Housing Affordability</td>  <td>90% not cost-burdened</td>       <td>Census ACS B25070, B25091</td></tr>',
          '<tr><td>Care Nonprofits (P+E+F+K)</td><td>25 per 10,000 residents</td>   <td>IRS EO BMF</td></tr>',
          '<tr><td>FQHC Density</td>           <td>15 per 100,000 residents</td>    <td>HRSA Health Center Data</td></tr>',
          '<tr><td>Health Insurance</td>       <td>95% insured</td>                 <td>Census ACS B27001</td></tr>',
          '<tr><td>SNAP Coverage Rate</td>     <td>85% of likely-eligible</td>      <td>Census ACS B22001, C17002</td></tr>',
        '</tbody>',
      '</table>',

      '<h2>Geographic Boundaries</h2>',

      '<p>',
        'All data sources use the Census 2020 ZCTA-to-Place relationship file to define city ',
        'boundaries consistently. A ZIP Code Tabulation Area is assigned to a city if &#8805;50% ',
        'of its land area falls within the city&rsquo;s Census incorporated place boundary. ',
        'This eliminates county-sharing inflation, where a city appears to have more resources ',
        'than it does because it shares a county with surrounding suburbs.',
      '</p>',

      '<h2>What this index does not measure</h2>',

      '<p>',
        'The CQ intentionally excludes health outcomes, income, safety, and general quality of life. ',
        'These are <em>conditions</em> &mdash; the result of many factors including care capacity, ',
        'but also wealth, history, and policy. Including them would conflate what a city ',
        '<em>has</em> with whether it can <em>show up</em> for its residents.',
      '</p>',

      '<p>',
        'A city in a non-Medicaid-expansion state will score lower on health insurance coverage. ',
        'This is intentional &mdash; a state&rsquo;s decision not to expand Medicaid is a real ',
        'policy barrier to care access, and the index reflects it as such.',
      '</p>',

      '<h3>Version &amp; Data</h3>',
      '<p>',
        'V3 (April 2026). 68 cities. ',
        'Data sources: IRS EO BMF, Census ACS 2022 5-year estimates, ',
        'HRSA Health Center Service Delivery, IMLS Public Libraries Survey FY2023. ',
        'All data collection and scoring code is available in the project repository.',
      '</p>',

    '</div>',
    renderFooter(),
  ].join('');
}

// ── Footer ──────────────────────────────────────────────────────────────────

function renderFooter() {
  return [
    '<footer class="site-footer">',
      '<div class="footer-copy">',
        'Care Quotient V3 &nbsp;&middot;&nbsp; 68 American Cities &nbsp;&middot;&nbsp; April 2026<br>',
        'Data: IRS EO BMF &middot; Census ACS 2022 &middot; HRSA &middot; IMLS',
      '</div>',
      '<div class="footer-links">',
        '<a href="#/methodology">Methodology</a>',
        '<a href="#/">Index</a>',
      '</div>',
    '</footer>',
  ].join('');
}
