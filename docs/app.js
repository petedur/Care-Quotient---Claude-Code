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
  var fills = containerEl.querySelectorAll(selector);
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
  } else if (hash === '/compare') {
    renderCompare(app);
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
      '<div class="hero-eyebrow">Care Quotient &mdash; V5</div>',
      '<h1 class="hero-headline">When someone needs help,<br>can their city show up?</h1>',
      '<div class="hero-rule"></div>',
      '<p class="hero-subhead">',
        'A data-driven index measuring care capacity for American cities &mdash; ',
        'not prosperity, not health outcomes, but the social networks, institutions, ',
        'and systems that determine whether people can get help when they need it.',
      '</p>',
    '</section>',

    // ── Ranking ───────────────────────────────────────────────────────────
    '<section class="section-wrap">',
      '<div class="ranking-header">',
        '<span class="section-label">The Index &mdash; ', total, ' Cities</span>',
        '<div class="ranking-header-actions">',
          '<a class="compare-link" href="#/compare">Compare cities &rarr;</a>',
          '<input class="city-search" id="city-search" type="search"',
            ' placeholder="Find a city&hellip;" autocomplete="off" spellcheck="false">',
        '</div>',
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

      '<p class="bands-note">',
        'Scores are measured against absolute benchmarks, not relative to other cities. ',
        'Cities within 3&ndash;4 points should be read as rough peers &mdash; small differences ',
        'may fall within data collection variance. Click any city for a full breakdown.',
      '</p>',
    '</section>',

    // ── Pillars ───────────────────────────────────────────────────────────
    '<section class="section-wrap">',
      '<span class="section-label">How It&rsquo;s Measured</span>',
      '<div class="pillars-grid">',

        '<div class="pillar-card">',
          '<div class="pillar-card-weight">40% of CQ</div>',
          '<div class="pillar-card-name">Social &amp; Relational Care</div>',
          '<div class="pillar-card-desc">',
            'Whether the relational infrastructure for care exists &mdash; stable communities, ',
            'the organized nonprofits that show up when people need help, and the public spaces ',
            'that hold communities together.',
          '</div>',
        '</div>',

        '<div class="pillar-card p2">',
          '<div class="pillar-card-weight">35% of CQ</div>',
          '<div class="pillar-card-name">Institutional Care</div>',
          '<div class="pillar-card-desc">',
            'Whether formal institutions exist to absorb distress at scale &mdash; ',
            'federally qualified health centers serving patients regardless of ability to pay, ',
            'and nursing home capacity for the elderly.',
          '</div>',
        '</div>',

        '<div class="pillar-card p3">',
          '<div class="pillar-card-weight">25% of CQ</div>',
          '<div class="pillar-card-name">Economic Access to Care</div>',
          '<div class="pillar-card-desc">',
            'Whether economic conditions allow care to reach those who need it &mdash; ',
            'healthcare coverage, housing affordability, and food security program reach.',
          '</div>',
        '</div>',

      '</div>',
    '</section>',

    // ── What this is / is not ─────────────────────────────────────────────
    '<section class="section-wrap what-is-section">',
      '<span class="section-label">What This Index Measures</span>',
      '<div class="what-is-grid">',

        '<div class="what-is-col">',
          '<div class="what-is-heading what-is-yes">What the CQ measures</div>',
          '<ul class="what-is-list">',
            '<li>Whether stable social networks exist for people to lean on</li>',
            '<li>Whether nonprofits and health centers are present relative to population need</li>',
            '<li>Whether safety-net programs are reaching the people they&rsquo;re designed for</li>',
            '<li>Whether the organizations, health centers, and systems to support people in difficulty exist at the scale the population needs</li>',
          '</ul>',
        '</div>',

        '<div class="what-is-col">',
          '<div class="what-is-heading what-is-no">What the CQ does not measure</div>',
          '<ul class="what-is-list">',
            '<li>Prosperity, income, or economic growth</li>',
            '<li>Health outcomes (life expectancy, disease rates)</li>',
            '<li>Safety or crime</li>',
            '<li>General quality of life</li>',
          '</ul>',
          '<p class="what-is-note">',
            'A prosperous city is not necessarily a caring one. This index measures one of them.',
          '</p>',
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

// ── City context notes ──────────────────────────────────────────────────────
// Contextual interpretation notes shown on city pages for cases where the score
// requires explanation that the raw numbers alone won't convey.

var CITY_CONTEXT = {
  honolulu: {
    type: 'geo',
    text: [
      '<strong>Geography note:</strong> Hawaii has no incorporated municipalities. ',
      'Honolulu is a Census Designated Place, so data reflects Honolulu County ',
      'boundaries rather than the urban core. Density metrics may be modestly overstated ',
      'relative to other cities. See <a href="#/methodology">Methodology &sect;9</a>.',
    ].join(''),
  },
  nyc: {
    type: 'info',
    text: [
      '<strong>Scale note:</strong> New York City has more nonprofits than almost any city in the country, ',
      'but the Care Quotient measures density per resident. With 8.3 million people, even a large absolute count ',
      'spreads thin on a per-capita basis. NYC&rsquo;s FQHC network is strong; the combined nonprofit score ',
      'reflects this scale effect, not an absence of care infrastructure.',
    ].join(''),
  },
  cleveland: {
    type: 'info',
    text: [
      '<strong>Rust Belt pattern:</strong> Cleveland scores higher than many larger, wealthier cities. ',
      'Decades of economic decline attracted sustained federal investment in FQHCs and social services &mdash; ',
      'infrastructure that persists even as the broader economy contracted. Ohio expanded Medicaid, ',
      'further strengthening the Economic Access pillar. High care capacity and low prosperity are not contradictions.',
    ].join(''),
  },
  detroit: {
    type: 'info',
    text: [
      '<strong>Rust Belt pattern:</strong> Detroit scores higher than many larger, wealthier cities. ',
      'Sustained federal investment in FQHCs and nonprofits during decades of economic difficulty built ',
      'dense care infrastructure relative to the current population. Michigan expanded Medicaid. ',
      'These cities demonstrate that care capacity and prosperity are genuinely separate dimensions.',
    ].join(''),
  },
  pittsburgh: {
    type: 'info',
    text: [
      '<strong>Rust Belt pattern:</strong> Pittsburgh&rsquo;s care infrastructure density reflects a city ',
      'that built robust social services during its industrial decline. Pennsylvania expanded Medicaid, ',
      'and the city&rsquo;s nonprofit and FQHC density is high relative to its current population size.',
    ].join(''),
  },
  cincinnati: {
    type: 'info',
    text: [
      '<strong>Rust Belt pattern:</strong> Cincinnati&rsquo;s high score reflects sustained investment in care ',
      'infrastructure relative to its current population. Ohio expanded Medicaid, contributing to strong ',
      'health insurance coverage. High care capacity in economically stressed cities is a recurring ',
      'finding in this data.',
    ].join(''),
  },
  dallas: {
    type: 'info',
    text: [
      '<strong>Texas and Medicaid:</strong> Texas has not expanded Medicaid under the Affordable Care Act. ',
      'The health insurance coverage metric reflects this directly &mdash; it is a real barrier to care ',
      'access, and the CQ treats it as one. All Texas cities carry a structural disadvantage on the Reach ',
      'pillar as a result of this state policy decision. Rapid population growth also means care ',
      'infrastructure has not scaled proportionally with the population.',
    ].join(''),
  },
  fort_worth: {
    type: 'info',
    text: [
      '<strong>Texas and Medicaid:</strong> Texas has not expanded Medicaid under the Affordable Care Act. ',
      'This directly suppresses health insurance coverage and SNAP participation rates for all Texas cities. ',
      'Fort Worth also has very few FQHC sites within its city limits relative to its population, ',
      'reflecting both the state policy environment and rapid suburban growth outpacing service infrastructure.',
    ].join(''),
  },
  san_antonio: {
    type: 'info',
    text: [
      '<strong>Texas and Medicaid:</strong> Texas has not expanded Medicaid. The health insurance metric ',
      'reflects this state policy directly as a real care access barrier. San Antonio also has a large ',
      'population relative to its nonprofit and FQHC density, a pattern common to fast-growing Sun Belt cities.',
    ].join(''),
  },
  houston: {
    type: 'info',
    text: [
      '<strong>Texas and Medicaid:</strong> Texas has not expanded Medicaid under the Affordable Care Act. ',
      'Houston&rsquo;s health insurance coverage is notably below the national benchmark as a direct result. ',
      'The city&rsquo;s large and fast-growing population also means nonprofit and FQHC density trails ',
      'slower-growing cities with comparable total counts.',
    ].join(''),
  },
  raleigh: {
    type: 'info',
    text: [
      '<strong>Growing city, thin infrastructure:</strong> Raleigh is one of the fastest-growing cities in the US, ',
      'but care infrastructure &mdash; nonprofits, FQHCs, safety-net program reach &mdash; has not scaled ',
      'proportionally. A successful economy and strong care capacity are not the same thing. ',
      'Raleigh&rsquo;s SNAP coverage rate also reflects relatively low poverty rates, which compress the score.',
    ].join(''),
  },
};

// ── City page ───────────────────────────────────────────────────────────────

var PILLAR_META = {
  pillar1: { label: 'Social & Relational Care',    color: 'var(--p1)' },
  pillar2: { label: 'Institutional Care',          color: 'var(--p2)' },
  pillar3: { label: 'Economic Access to Care',     color: 'var(--p3)' },
};

// ── FQHC / insurance mismatch interpretation ────────────────────────────────
// Returns a note object when FQHC density and health insurance scores diverge
// in a way that's interpretively meaningful, or null when both are aligned.
// Thresholds: FQHC < 40 = thin infrastructure; insurance < 88 = coverage gap.

function getFQHCMismatch(city) {
  var fqhc = city.metrics.fqhc ? city.metrics.fqhc.score : null;
  var ins  = city.metrics.health_insurance ? city.metrics.health_insurance.score : null;
  if (fqhc === null || ins === null) return null;

  var thinFQHC    = fqhc < 40;
  var coverageGap = ins  < 88;

  if (thinFQHC && coverageGap) {
    return {
      type: 'warn',
      text: [
        '<strong>Access gap:</strong> Both FQHC infrastructure and health insurance coverage ',
        'are below benchmark — a compounded problem where neither safety-net facilities ',
        'nor coverage reach is adequate.',
      ].join(''),
    };
  } else if (thinFQHC && !coverageGap) {
    return {
      type: 'info',
      text: [
        '<strong>Coverage strong, infrastructure thin:</strong> Health insurance coverage ',
        'is broad, but federally-supported safety-net health centers are sparse. ',
        'Access to care depends primarily on private providers, which may be geographically ',
        'uneven for lower-income residents.',
      ].join(''),
    };
  } else if (!thinFQHC && coverageGap) {
    return {
      type: 'info',
      text: [
        '<strong>Infrastructure present, coverage gap:</strong> Safety-net health center ',
        'density is above threshold and FQHCs are doing their intended work — serving ',
        'uninsured and Medicaid patients. The coverage gap typically reflects state ',
        'Medicaid non-expansion rather than a local infrastructure failure.',
      ].join(''),
    };
  }
  return null;
}

var METRIC_META = {
  residential_stability: {
    label:  'Residential Stability',
    pillar: 'pillar1',
    desc:   '% of population in same home 1+ years',
  },
  combined_care: {
    label:  'Care Nonprofits',
    pillar: 'pillar1',
    desc:   'Human services & health orgs per 10,000 residents (NTEE P+E+F+K)',
  },
  library_density: {
    label:  'Library Density',
    pillar: 'pillar1',
    desc:   'Public libraries per 100,000 residents',
  },
  fqhc: {
    label:  'Health Centers (FQHCs)',
    pillar: 'pillar2',
    desc:   'Federally Qualified Health Centers per 100,000 residents',
  },
  nursing_home: {
    label:  'Nursing Home Capacity',
    pillar: 'pillar2',
    desc:   'Medicare/Medicaid certified beds per 1,000 residents aged 65+',
  },
  health_insurance: {
    label:  'Healthcare Coverage',
    pillar: 'pillar3',
    desc:   '% of population with healthcare coverage',
  },
  housing_cost_burden: {
    label:  'Housing Affordability',
    pillar: 'pillar3',
    desc:   '% of households not spending >30% of income on housing',
  },
  snap_coverage: {
    label:  'SNAP Coverage',
    pillar: 'pillar3',
    desc:   'SNAP participation among likely-eligible households',
  },
};

var METRIC_ORDER = [
  'residential_stability',
  'combined_care',
  'library_density',
  'fqhc',
  'nursing_home',
  'health_insurance',
  'housing_cost_burden',
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

  // Context note (city-specific interpretation)
  var contextNote = '';
  var ctx = CITY_CONTEXT[key];
  if (ctx) {
    contextNote = [
      '<div class="context-note context-note-', ctx.type, '">',
        ctx.text,
      '</div>',
    ].join('');
  }

  // FQHC / insurance mismatch note
  var mismatch = getFQHCMismatch(city);
  var mismatchHtml = '';
  if (mismatch) {
    mismatchHtml = [
      '<div class="context-note context-note-', mismatch.type, '">',
        mismatch.text,
      '</div>',
    ].join('');
  }

  // Need-adjusted diagnostic
  var distressedHtml = '';
  var cd = city.diagnostic && city.diagnostic.care_distressed;
  if (cd && cd.value !== 'n/a') {
    var totalDensity = city.metrics.combined_care ? city.metrics.combined_care.raw : null;
    var totalFmt = totalDensity !== null ? Number(totalDensity).toFixed(2) + ' per 10k residents' : '';
    distressedHtml = [
      '<div class="diagnostic-section">',
        '<div class="diagnostic-label">Need-adjusted care infrastructure</div>',
        '<div class="diagnostic-row">',
          '<span class="diagnostic-name">Care nonprofits (total pop denominator)</span>',
          '<span class="diagnostic-val">', totalFmt, '</span>',
        '</div>',
        '<div class="diagnostic-row">',
          '<span class="diagnostic-name">Care nonprofits per 10k residents at 0&ndash;150% FPL</span>',
          '<span class="diagnostic-val">', cd.value, ' per 10k</span>',
        '</div>',
        '<p class="diagnostic-note">',
          'The 0&ndash;150% FPL denominator normalizes infrastructure against the population ',
          'most likely to need care-related services. A large gap between the two figures ',
          'suggests care nonprofits are concentrated in lower-income areas relative to the ',
          'city&rsquo;s total population. See <a href="#/methodology">Methodology &sect;3.3</a>.',
        '</p>',
      '</div>',
    ].join('');
  }

  app.innerHTML = [
    '<div class="city-page">',

      '<a href="#/" class="back-link">&#8592; All cities</a>',

      contextNote,

      '<div class="city-title">', city.name, '</div>',
      '<div class="city-meta">',
        city.state,
        ' &nbsp;&middot;&nbsp; ', city.population,
        ' &nbsp;&middot;&nbsp; <a href="#/compare" class="compare-inline-link">Compare with another city</a>',
      '</div>',

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

      mismatchHtml,

      distressedHtml,

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

// ── Compare page ────────────────────────────────────────────────────────────

function buildCityOptions(selectedKey) {
  var cities = getCitiesSorted();
  return cities.map(function(c) {
    var sel = c.key === selectedKey ? ' selected' : '';
    return '<option value="' + c.key + '"' + sel + '>' + c.name + ', ' + c.state + '</option>';
  }).join('');
}

function renderCompareTable(keyA, keyB) {
  var cityA = keyA ? CITIES[keyA] : null;
  var cityB = keyB ? CITIES[keyB] : null;

  if (!cityA && !cityB) {
    return '<p class="compare-prompt">Select two cities above to compare their care capacity metrics.</p>';
  }

  var nameA = cityA ? cityA.name : '&mdash;';
  var nameB = cityB ? cityB.name : '&mdash;';

  function scoreCell(city, field, color) {
    if (!city) return '<td class="cmp-cell">&mdash;</td>';
    var val   = field === 'cq' ? city.cq : (city[field] || 0);
    var score = fmt(val);
    var bar   = color
      ? '<div class="cmp-bar-track"><div class="cmp-bar-fill" style="background:' + color + '" data-target="' + score + '"></div></div>'
      : '';
    return '<td class="cmp-cell">' + score + bar + '</td>';
  }

  function metricCell(city, mk) {
    if (!city) return '<td class="cmp-cell">&mdash;</td>';
    var m = city.metrics[mk];
    if (!m) return '<td class="cmp-cell">&mdash;</td>';
    var meta  = METRIC_META[mk];
    var color = PILLAR_META[meta.pillar].color;
    var score = fmt(m.score);
    return [
      '<td class="cmp-cell">',
        score,
        '<div class="cmp-bar-track">',
          '<div class="cmp-bar-fill" style="background:', color, '"',
               ' data-target="', score, '"></div>',
        '</div>',
      '</td>',
    ].join('');
  }

  var pillarRows = [
    ['pillar1', 'Social & Relational Care',  'var(--p1)'],
    ['pillar2', 'Institutional Care',        'var(--p2)'],
    ['pillar3', 'Economic Access to Care',   'var(--p3)'],
  ].map(function(p) {
    return [
      '<tr class="cmp-row-pillar">',
        '<td class="cmp-label">', p[1], '</td>',
        scoreCell(cityA, p[0], p[2]),
        scoreCell(cityB, p[0], p[2]),
      '</tr>',
    ].join('');
  }).join('');

  var metricRows = METRIC_ORDER.map(function(mk) {
    var meta = METRIC_META[mk];
    return [
      '<tr>',
        '<td class="cmp-label cmp-label-metric">', meta.label, '</td>',
        metricCell(cityA, mk),
        metricCell(cityB, mk),
      '</tr>',
    ].join('');
  }).join('');

  return [
    '<table class="compare-table">',
      '<thead>',
        '<tr>',
          '<th class="cmp-label"></th>',
          '<th class="cmp-city-head">', nameA, '</th>',
          '<th class="cmp-city-head">', nameB, '</th>',
        '</tr>',
      '</thead>',
      '<tbody>',
        '<tr class="cmp-row-cq">',
          '<td class="cmp-label">Care Quotient</td>',
          scoreCell(cityA, 'cq', null),
          scoreCell(cityB, 'cq', null),
        '</tr>',
        '<tr class="cmp-divider-row"><td colspan="3"></td></tr>',
        pillarRows,
        '<tr class="cmp-divider-row"><td colspan="3"></td></tr>',
        metricRows,
      '</tbody>',
    '</table>',
  ].join('');
}

function renderCompare(app) {
  var defaultA = 'nyc';
  var defaultB = 'chicago';

  app.innerHTML = [
    '<div class="compare-page">',

      '<a href="#/" class="back-link">&#8592; All cities</a>',

      '<div class="compare-header">',
        '<div class="compare-eyebrow">Compare</div>',
        '<h1 class="compare-title">City-by-City Comparison</h1>',
        '<p class="compare-intro">',
          'Select two cities to compare their Care Quotient scores and underlying metrics. ',
          'Scores are on the same absolute scale &mdash; a direct point difference reflects ',
          'a real difference in measured care capacity.',
        '</p>',
      '</div>',

      '<div class="compare-controls">',
        '<div class="compare-picker">',
          '<label class="compare-picker-label">City A</label>',
          '<select id="compare-a" class="compare-select">',
            buildCityOptions(defaultA),
          '</select>',
        '</div>',
        '<div class="compare-vs">vs</div>',
        '<div class="compare-picker">',
          '<label class="compare-picker-label">City B</label>',
          '<select id="compare-b" class="compare-select">',
            buildCityOptions(defaultB),
          '</select>',
        '</div>',
      '</div>',

      '<div id="compare-results">',
        renderCompareTable(defaultA, defaultB),
      '</div>',

    '</div>',
    renderFooter(),
  ].join('');

  // Animate initial bars
  setTimeout(function() {
    var results = document.getElementById('compare-results');
    animateBars(results, '.cmp-bar-fill', 80);
  }, 120);

  // Re-render on change
  function onChange() {
    var keyA = document.getElementById('compare-a').value;
    var keyB = document.getElementById('compare-b').value;
    var results = document.getElementById('compare-results');
    results.innerHTML = renderCompareTable(keyA, keyB);
    setTimeout(function() {
      animateBars(results, '.cmp-bar-fill', 60);
    }, 40);
  }

  document.getElementById('compare-a').addEventListener('change', onChange);
  document.getElementById('compare-b').addEventListener('change', onChange);
}

// ── Methodology ─────────────────────────────────────────────────────────────

function renderMethodology(app) {
  app.innerHTML = [
    '<div class="method-page">',

      '<a href="#/" class="back-link">&#8592; All cities</a>',

      '<div class="method-eyebrow">Methodology &mdash; V4</div>',
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
        'The CQ is a weighted composite of seven scored metrics organized into three pillars. ',
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
            '<td><span class="ptag ptag-p1">Social &amp; Relational Care</span></td>',
            '<td>Residential stability, care nonprofit density, &amp; library density &mdash; the relational infrastructure that enables communities to notice and respond to need.</td>',
            '<td>40%</td>',
          '</tr>',
          '<tr>',
            '<td><span class="ptag ptag-p2">Institutional Care</span></td>',
            '<td>FQHC density &amp; nursing home capacity &mdash; formal institutions designed to absorb distress at scale, serving patients regardless of ability to pay.</td>',
            '<td>35%</td>',
          '</tr>',
          '<tr>',
            '<td><span class="ptag ptag-p3">Economic Access to Care</span></td>',
            '<td>Healthcare coverage, housing affordability, &amp; SNAP participation &mdash; whether economic conditions allow care to reach those who need it.</td>',
            '<td>25%</td>',
          '</tr>',
        '</tbody>',
      '</table>',

      '<h2>Benchmarks</h2>',

      '<p>',
        'Each metric is scored against an absolute benchmark representing a meaningful threshold. ',
        '<code>score = min(value / benchmark &times; 100, 100)</code>. ',
        'Scores are absolute &mdash; adding or removing cities does not change existing scores. ',
        'A score of 70 means the city reaches 70% of the benchmark, not that it ranks 70th.',
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
          '<tr><td>Nursing Home Capacity</td>  <td>50 beds per 1,000 residents 65+</td><td>CMS Care Compare</td></tr>',
          '<tr><td>Health Insurance</td>       <td>95% insured</td>                 <td>Census ACS B27001</td></tr>',
          '<tr><td>SNAP Coverage Rate</td>     <td>85% of likely-eligible</td>      <td>Census ACS B22001, C17002</td></tr>',
        '</tbody>',
      '</table>',

      '<h2>Geographic Boundaries</h2>',

      '<p>',
        'All data sources use the Census 2020 ZCTA-to-Place relationship file to define city ',
        'boundaries consistently. A ZIP Code Tabulation Area is assigned to a city if &#8805;40% ',
        'of its land area falls within the city&rsquo;s Census incorporated place boundary. ',
        'This threshold captures near-boundary ZCTAs that genuinely serve city residents, ',
        'while excluding ZCTAs that are primarily suburban. It eliminates county-sharing ',
        'inflation, where a city would appear to have more resources than it does because it ',
        'shares a county with surrounding suburbs.',
      '</p>',

      '<p>',
        '<strong>Honolulu exception:</strong> Hawaii has no incorporated municipalities &mdash; ',
        'Honolulu is a Census Designated Place absent from the ZCTA-to-Place crosswalk. The ',
        'pipeline falls back to Honolulu County boundaries, which are broader than the urban core. ',
        'Density metrics for Honolulu may be modestly overstated as a result.',
      '</p>',

      '<h2>How to read the scores</h2>',

      '<p>',
        'The CQ is designed to be read as a measure against a benchmark, not as a competition. ',
        'Cities within 3&ndash;4 points should be treated as rough peers &mdash; differences of that ',
        'size may fall within the margin of geographic approximation or a single year&rsquo;s data variance. ',
        'The index is most useful for identifying cities at the extremes, understanding which ',
        '<em>specific</em> metrics drive a city&rsquo;s score, and tracking change over time.',
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

      '<p>',
        'Nonprofit density is measured per resident, not in absolute terms. A city with many ',
        'nonprofits and a very large population (New York City) can score lower than a smaller ',
        'city with proportionally denser care infrastructure. This is a feature, not a bug: ',
        'what matters for a resident is whether there is care capacity relative to local need.',
      '</p>',

      '<h3>Version &amp; Data</h3>',
      '<p>',
        'V4 (April 2026). 68 cities. ',
        'Data sources: IRS EO BMF, Census ACS 2022 5-year estimates, ',
        'HRSA Health Center Service Delivery, IMLS Public Libraries Survey FY2023, ',
        'CMS Care Compare Nursing Home Provider Information. ',
        'All data collection and scoring code is available in the ',
        '<a href="https://github.com/petedur/Care-Quotient---Claude-Code" target="_blank" rel="noopener">project repository</a>.',
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
        'Care Quotient V4 &nbsp;&middot;&nbsp; 68 American Cities &nbsp;&middot;&nbsp; April 2026<br>',
        'Data: IRS EO BMF &middot; Census ACS 2022 &middot; HRSA &middot; IMLS &middot; CMS Care Compare',
      '</div>',
      '<div class="footer-links">',
        '<a href="#/methodology">Methodology</a>',
        '<a href="#/compare">Compare</a>',
        '<a href="#/">Index</a>',
      '</div>',
    '</footer>',
  ].join('');
}
