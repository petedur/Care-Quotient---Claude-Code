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
    destroyHomeMap();
    renderCity(app, hash.slice(6));
  } else if (hash === '/methodology') {
    destroyHomeMap();
    renderMethodology(app);
  } else if (hash === '/theory') {
    destroyHomeMap();
    renderTheory(app);
  } else if (hash === '/compare') {
    destroyHomeMap();
    renderCompare(app);
  } else if (hash === '/chat') {
    destroyHomeMap();
    renderChat(app);
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

// ── Map utilities ───────────────────────────────────────────────────────────

var _homeMap = null;
var _akMap   = null;
var _hiMap   = null;

function destroyHomeMap() {
  if (_homeMap) { _homeMap.remove(); _homeMap = null; }
  if (_akMap)   { _akMap.remove();   _akMap   = null; }
  if (_hiMap)   { _hiMap.remove();   _hiMap   = null; }
}

function cqColor(score) {
  if (score >= 70) return '#2d6a4f';
  if (score >= 62) return '#74c490';
  if (score >= 53) return '#5aaccf';
  return '#1e5799';
}

var TILE_URL  = 'https://server.arcgisonline.com/ArcGIS/rest/services/World_Topo_Map/MapServer/tile/{z}/{y}/{x}';
var TILE_OPTS = { maxZoom: 19 };

function addMarker(map, city) {
  var m = L.circleMarker([city.lat, city.lng], {
    radius: 7, fillColor: cqColor(city.cq),
    color: '#fff', weight: 1.5, opacity: 1, fillOpacity: 0.88,
  }).addTo(map);
  m.bindTooltip('<strong>' + city.name + '</strong><br>CQ&nbsp;' + fmt(city.cq),
    { direction: 'top', offset: [0, -6] });
  m.on('click', function() { location.hash = '#/city/' + city.key; });
}

function makeInsetMap(id, center, zoom) {
  return L.map(id, {
    zoomControl: false, attributionControl: false,
    dragging: false, scrollWheelZoom: false,
    doubleClickZoom: false, boxZoom: false, keyboard: false,
  }).setView(center, zoom);
}

function initHomeMap(cities) {
  if (typeof L === 'undefined') return;
  destroyHomeMap();
  if (!document.getElementById('city-map')) return;

  var continental = cities.filter(function(c) { return c.state !== 'AK' && c.state !== 'HI'; });
  var alaska      = cities.filter(function(c) { return c.state === 'AK'; });
  var hawaii      = cities.filter(function(c) { return c.state === 'HI'; });

  // Main map — set a temporary view so Leaflet has something to render while layout settles
  _homeMap = L.map('city-map', {
    zoomControl: true, scrollWheelZoom: false, attributionControl: true,
  });
  L.tileLayer(TILE_URL, Object.assign({}, TILE_OPTS, {
    attribution: 'Tiles &copy; <a href="https://www.esri.com/">Esri</a>',
  })).addTo(_homeMap);
  _homeMap.setView([39, -98], 4);
  continental.forEach(function(c) { addMarker(_homeMap, c); });

  // Alaska inset — centered on Cook Inlet / Anchorage bowl, zoom 4 shows full state outline
  if (document.getElementById('map-inset-ak')) {
    _akMap = makeInsetMap('map-inset-ak', [62, -150], 4);
    L.tileLayer(TILE_URL, TILE_OPTS).addTo(_akMap);
    alaska.forEach(function(c) { addMarker(_akMap, c); });
  }

  // Hawaii inset — zoom 8 centered on Oahu shows the island shape clearly
  if (document.getElementById('map-inset-hi')) {
    _hiMap = makeInsetMap('map-inset-hi', [21.3, -157.85], 8);
    L.tileLayer(TILE_URL, TILE_OPTS).addTo(_hiMap);
    hawaii.forEach(function(c) { addMarker(_hiMap, c); });
  }

  // Run fitBounds after layout is settled so container dimensions are correct
  setTimeout(function() {
    if (_homeMap) {
      _homeMap.invalidateSize();
      var cityBounds = L.latLngBounds(continental.map(function(c) { return [c.lat, c.lng]; }));
      // Extra left padding shifts the US rightward, matching the desired framing
      _homeMap.fitBounds(cityBounds, { paddingTopLeft: [140, 40], paddingBottomRight: [40, 40] });
    }
    if (_akMap)   _akMap.invalidateSize();
    if (_hiMap)   _hiMap.invalidateSize();
  }, 200);
}

// ── Tier system ─────────────────────────────────────────────────────────────
// Four tiers based on absolute score bands, not relative rank.
// Leading ≥70 | Established ≥62 | Growing ≥53 | Emerging <53

var TIERS = [
  { num: 1, label: 'Leading',     min: 70,  color: '#2d6a4f', textColor: '#fff',    desc: 'Score 70 or above' },
  { num: 2, label: 'Established', min: 62,  color: '#74c490', textColor: '#1a3d28', desc: 'Score 62–69' },
  { num: 3, label: 'Growing',     min: 53,  color: '#5aaccf', textColor: '#0c2d40', desc: 'Score 53–61' },
  { num: 4, label: 'Emerging',    min: 0,   color: '#1e5799', textColor: '#fff',    desc: 'Score below 53' },
];

function cqTier(score) {
  for (var i = 0; i < TIERS.length; i++) {
    if (score >= TIERS[i].min) return TIERS[i];
  }
  return TIERS[TIERS.length - 1];
}

// ── Home ────────────────────────────────────────────────────────────────────

function renderHome(app) {
  var cities = getCitiesSorted();
  var total  = cities.length;

  // Group cities into tiers, preserving global rank within each row
  var tierBuckets = { 1: [], 2: [], 3: [], 4: [] };
  cities.forEach(function(city, i) {
    tierBuckets[cqTier(city.cq).num].push({ city: city, rank: i + 1 });
  });

  var rows = TIERS.map(function(tier) {
    var bucket = tierBuckets[tier.num];
    if (!bucket.length) return '';
    var tierRows = bucket.map(function(item) {
      var city = item.city;
      var overflowCls = item.rank > 5 ? ' ranking-row-overflow' : '';
      return [
        '<a class="ranking-row', overflowCls, '" href="#/city/', city.key, '"',
          ' role="link" tabindex="0"',
          ' aria-label="', city.name, ', Care Quotient ', fmt(city.cq), '">',
          '<span class="r-rank">', item.rank, '</span>',
          '<span class="r-name">', city.name, '</span>',
          '<span class="r-state">', city.state, '</span>',
          '<div class="r-bar">',
            '<div class="r-bar-fill" data-target="', fmt(city.cq, 1), '"></div>',
          '</div>',
          '<span class="r-score">', fmt(city.cq), '</span>',
        '</a>',
      ].join('');
    }).join('');
    var allOverflow = bucket.every(function(item) { return item.rank > 5; });
    return [
      '<div class="tier-group', allOverflow ? ' tier-group-overflow' : '', '" data-tier="', tier.num, '">',
        '<div class="tier-header">',
          '<span class="tier-badge" style="background:', tier.color, ';color:', tier.textColor, '">T', tier.num, '</span>',
          '<span class="tier-header-label">', tier.label, '</span>',
          '<span class="tier-header-desc">', tier.desc, ' &nbsp;&middot;&nbsp; ', bucket.length, ' ', bucket.length === 1 ? 'city' : 'cities', '</span>',
        '</div>',
        tierRows,
      '</div>',
    ].join('');
  }).join('');

  app.innerHTML = [
    // ── Hero ──────────────────────────────────────────────────────────────
    '<section class="hero">',
      '<div class="hero-eyebrow">Care Quotient</div>',
      '<h1 class="hero-headline">When someone needs help,<br>can their city show up?</h1>',
      '<div class="hero-rule"></div>',
      '<p class="hero-subhead">',
        'This is a data-driven index measuring the social ties, institutions, and access conditions ',
        'that determine whether people can get help when they need it.',
      '</p>',
    '</section>',

    // ── Map ───────────────────────────────────────────────────────────────
    '<section class="section-wrap map-section">',
      '<span class="section-label">Cities Mapped</span>',
      '<div id="city-map" class="city-map">',
        '<div id="map-inset-ak" class="map-inset" data-label="Alaska"></div>',
        '<div id="map-inset-hi" class="map-inset" data-label="Hawaii"></div>',
      '</div>',
      '<div class="map-legend">',
        '<span class="map-legend-label">Tier</span>',
        TIERS.map(function(t) {
          return '<span class="legend-swatch" style="background:' + t.color + '"></span>' +
                 '<span class="legend-tier"><span class="legend-tier-badge" style="background:' + t.color + ';color:' + t.textColor + '">T' + t.num + '</span> ' + t.label + '</span>';
        }).join(''),
      '</div>',
    '</section>',

    // ── Ranking ───────────────────────────────────────────────────────────
    '<section class="section-wrap">',
      '<div class="ranking-header">',
        '<span class="section-label">The Index: ', total, ' Cities</span>',
        '<div class="ranking-header-actions">',
          '<a class="compare-link" href="#/compare">Compare cities &rarr;</a>',
          '<input class="city-search" id="city-search" type="search"',
            ' placeholder="Find a city&hellip;" autocomplete="off" spellcheck="false">',
        '</div>',
      '</div>',

      '<div class="col-headers">',
        '<span class="col-h right">Rank</span>',
        '<span class="col-h">City</span>',
        '<span class="col-h">State</span>',
        '<span class="col-h">Care Quotient</span>',
        '<span class="col-h right">Score</span>',
      '</div>',

      '<div id="ranking-table">', rows, '</div>',
      '<div class="no-results" id="no-results">No cities match your search.</div>',
      '<button class="show-all-btn" id="show-all-btn" aria-expanded="false">',
        'See all ', total, ' cities &#8595;',
      '</button>',

      '<p class="bands-note">',
        'Scores are measured against absolute benchmarks, not relative to other cities. ',
        'Cities within 3 to 4 points should be read as rough peers. Small differences ',
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
            'Whether stable communities, active nonprofits, libraries, and faith organizations ',
            'give people something to lean on when life gets hard.',
          '</div>',
        '</div>',

        '<div class="pillar-card p2">',
          '<div class="pillar-card-weight">35% of CQ</div>',
          '<div class="pillar-card-name">Institutional Care</div>',
          '<div class="pillar-card-desc">',
            'Whether formal institutions exist to absorb distress at scale: ',
            'federally qualified health centers serving patients regardless of ability to pay, ',
            'nursing home capacity for the elderly, and licensed child care infrastructure.',
          '</div>',
        '</div>',

        '<div class="pillar-card p3">',
          '<div class="pillar-card-weight">25% of CQ</div>',
          '<div class="pillar-card-name">Economic Access to Care</div>',
          '<div class="pillar-card-desc">',
            'Whether economic conditions allow care to reach those who need it: ',
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
        '</div>',

      '</div>',
    '</section>',

    renderFooter(),
  ].join('');

  // Initialize map
  setTimeout(function() { initHomeMap(cities); }, 0);

  // Animate ranking bars (staggered)
  var rankingTable = document.getElementById('ranking-table');
  setTimeout(function() {
    animateBars(rankingTable, '.r-bar-fill', 80);
  }, 120);

  // Live search
  var searchInput = document.getElementById('city-search');
  var noResults   = document.getElementById('no-results');

  // Expand / collapse
  var showAllBtn = document.getElementById('show-all-btn');
  if (showAllBtn) {
    showAllBtn.addEventListener('click', function() {
      var expanded = rankingTable.classList.toggle('ranking-expanded');
      showAllBtn.setAttribute('aria-expanded', String(expanded));
      showAllBtn.innerHTML = expanded
        ? 'Show fewer &#8593;'
        : 'See all ' + total + ' cities &#8595;';
    });
  }

  searchInput.addEventListener('input', function() {
    var q = searchInput.value.toLowerCase().trim();
    // Auto-expand when searching so results aren't hidden
    if (q) {
      rankingTable.classList.add('ranking-expanded');
      if (showAllBtn) showAllBtn.style.display = 'none';
    } else {
      rankingTable.classList.remove('ranking-expanded');
      if (showAllBtn) { showAllBtn.style.display = ''; showAllBtn.innerHTML = 'See all ' + total + ' cities &#8595;'; }
    }
    var visible = 0;
    rankingTable.querySelectorAll('.ranking-row').forEach(function(row) {
      var name  = row.querySelector('.r-name').textContent.toLowerCase();
      var state = row.querySelector('.r-state').textContent.toLowerCase();
      var show  = !q || name.indexOf(q) !== -1 || state.indexOf(q) !== -1;
      row.classList.toggle('hidden', !show);
      if (show) visible++;
    });
    // Hide tier group headers when all their rows are hidden
    rankingTable.querySelectorAll('.tier-group').forEach(function(group) {
      var anyVisible = group.querySelectorAll('.ranking-row:not(.hidden)').length > 0;
      group.querySelector('.tier-header').classList.toggle('hidden', !anyVisible);
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
      'Honolulu is scored using Honolulu County boundaries (~1M residents) rather than ',
      'the urban core (~350k). Because all density metrics use the county population as the denominator, ',
      'per-capita scores are calculated against a larger base than comparable cities. ',
      'Honolulu&rsquo;s high overall ranking should be read with this in mind — it reflects ',
      'genuine care infrastructure, but the county boundary makes direct comparisons imprecise. ',
      'See <a href="#/methodology">Methodology &sect;9</a>.',
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
      'Decades of economic decline attracted sustained federal investment in FQHCs and social services. ',
      'That infrastructure persists even as the broader economy contracted. Ohio expanded Medicaid, ',
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
      'The health insurance coverage metric reflects this directly: it is a real barrier to care ',
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
      'but care infrastructure (nonprofits, FQHCs, safety-net program reach) has not scaled ',
      'proportionally. A successful economy and strong care capacity are not the same thing. ',
      'Raleigh&rsquo;s SNAP coverage rate also reflects relatively low poverty rates, which compress the score.',
    ].join(''),
  },
  miami: {
    type: 'geo',
    text: [
      '<strong>Scope note:</strong> This score covers the City of Miami (~450k residents), ',
      'the incorporated municipality. Miami Beach, Hialeah, Coral Gables, and other cities ',
      'within Miami-Dade County are separate jurisdictions and are not included. ',
      'Two metrics &mdash; child care and religious density &mdash; use county-level source data (CBP and ARDA). ',
      'Because the City of Miami represents roughly 16% of Miami-Dade County&rsquo;s population, ',
      'those two scores are likely elevated relative to the city&rsquo;s actual capacity. ',
      'Florida has not expanded Medicaid, which directly suppresses the healthcare coverage score. ',
      'See <a href="#/methodology">Methodology &sect;9</a>.',
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
        'are below benchmark, a compounded problem where neither safety-net facilities ',
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
        'density is above threshold and FQHCs are doing their intended work, serving ',
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
  religious_density: {
    label:  'Religious Institutions',
    pillar: 'pillar1',
    desc:   'Congregations per 100,000 residents (all denominations, ARDA 2020 Religion Census)',
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
  child_care: {
    label:  'Child Care Capacity',
    pillar: 'pillar2',
    desc:   'Licensed child care establishments per 1,000 children under 5',
  },
  health_insurance: {
    label:  'Healthcare Coverage',
    pillar: 'pillar3',
    desc:   'Medicaid/CHIP enrollment rate among income-eligible residents (0–138% FPL)',
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
  'religious_density',
  'fqhc',
  'nursing_home',
  'child_care',
  'health_insurance',
  'housing_cost_burden',
  'snap_coverage',
];

var TREND_METRIC_LABELS = {
  residential_stability:    'Residential Stability',
  housing_cost_burden:      'Housing Cost Burden',
  snap_participation:       'SNAP Coverage',
  health_insurance_coverage: 'Medicaid/CHIP Coverage',
};

function renderCityTrend(city) {
  var t = city.trend;
  if (!t || Object.keys(t).length === 0) return '';

  var rows = Object.keys(TREND_METRIC_LABELS).map(function(key) {
    var m = t[key];
    if (!m) return '';
    var delta     = m.delta;
    var deltaStr  = (delta > 0 ? '+' : '') + delta + 'pp';
    var cls       = delta > 0 ? 'trend-delta-up' : (delta < 0 ? 'trend-delta-down' : 'trend-delta-flat');
    return [
      '<div class="trend-row">',
        '<span class="trend-metric-name">', TREND_METRIC_LABELS[key], '</span>',
        '<span class="trend-values">', m.prior, '% → ', m.current, '%</span>',
        '<span class="trend-delta ', cls, '">', deltaStr, '</span>',
      '</div>',
    ].join('');
  }).join('');

  return [
    '<div class="city-trend-section">',
      '<div class="section-label">ACS Trend: 2020 → 2022</div>',
      '<div class="trend-grid">', rows, '</div>',
      '<div class="trend-footnote">',
        'Trend reflects ACS-based metrics only (residential stability, housing cost burden, SNAP, Medicaid/CHIP). ',
        'Nonprofit density, library density, faith institutions, FQHCs, nursing homes, and child care ',
        'are cross-sectional data sources with no prior vintage available.',
      '</div>',
    '</div>',
  ].join('');
}

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

  // Community Wellbeing diagnostics (CDC PLACES — not scored)
  var wellbeingHtml = '';
  var md = city.diagnostic && city.diagnostic.mental_distress;
  var ph = city.diagnostic && city.diagnostic.poor_health;
  var dep = city.diagnostic && city.diagnostic.depression;
  if ((md && md.value !== 'n/a') || (ph && ph.value !== 'n/a') || (dep && dep.value !== 'n/a')) {
    var wellbeingRows = [];
    if (md && md.value !== 'n/a') {
      wellbeingRows.push(
        '<div class="diagnostic-row">',
          '<span class="diagnostic-name">Frequent mental distress</span>',
          '<span class="diagnostic-val">', md.value, '%</span>',
        '</div>'
      );
    }
    if (ph && ph.value !== 'n/a') {
      wellbeingRows.push(
        '<div class="diagnostic-row">',
          '<span class="diagnostic-name">Fair or poor self-rated health</span>',
          '<span class="diagnostic-val">', ph.value, '%</span>',
        '</div>'
      );
    }
    if (dep && dep.value !== 'n/a') {
      wellbeingRows.push(
        '<div class="diagnostic-row">',
          '<span class="diagnostic-name">Diagnosed depression</span>',
          '<span class="diagnostic-val">', dep.value, '%</span>',
        '</div>'
      );
    }
    wellbeingHtml = [
      '<div class="diagnostic-section">',
        '<div class="diagnostic-label">Community Wellbeing Context</div>',
        wellbeingRows.join(''),
        '<p class="diagnostic-note">',
          'These are outcome measures from CDC PLACES (BRFSS-modeled estimates, 2022/2023), ',
          'reported as community need context, not scored. High values indicate greater ',
          'need for care infrastructure, not lesser capacity. ',
          'See <a href="#/methodology">Methodology &sect;4</a>.',
        '</p>',
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
          '<div class="cq-tier">',
            '<span class="tier-badge" style="background:', cqTier(city.cq).color, ';color:', cqTier(city.cq).textColor, '">T', cqTier(city.cq).num, '</span>',
            '<span class="tier-label-text">', cqTier(city.cq).label, '</span>',
          '</div>',
        '</div>',
      '</div>',

      '<div class="divider"></div>',

      '<div class="city-pillars">', pillarCards, '</div>',

      '<div class="divider"></div>',

      metricHtml,

      renderCityTrend(city),

      mismatchHtml,

      distressedHtml,

      wellbeingHtml,

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

  var nameA = cityA ? cityA.name : 'n/a';
  var nameB = cityB ? cityB.name : 'n/a';

  function scoreCell(city, field, color) {
    if (!city) return '<td class="cmp-cell">n/a</td>';
    var val   = field === 'cq' ? city.cq : (city[field] || 0);
    var score = fmt(val);
    var bar   = color
      ? '<div class="cmp-bar-track"><div class="cmp-bar-fill" style="background:' + color + '" data-target="' + score + '"></div></div>'
      : '';
    return '<td class="cmp-cell">' + score + bar + '</td>';
  }

  function metricCell(city, mk) {
    if (!city) return '<td class="cmp-cell">n/a</td>';
    var m = city.metrics[mk];
    if (!m) return '<td class="cmp-cell">n/a</td>';
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
          'Scores are on the same absolute scale, so a direct point difference reflects ',
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

      '<div class="method-eyebrow">Methodology</div>',
      '<h1>How the Care Quotient is built</h1>',

      '<p>',
        'The Care Quotient measures <strong>care capacity</strong>: whether a city has the social ties, ',
        'institutions, and safety-net reach to help people when they need it. ',
        'This is explicitly <em>not</em> a quality-of-life index. A city can score well on income, ',
        'safety, and health outcomes while having thin care infrastructure for its most vulnerable ',
        'residents. The inverse is also true.',
      '</p>',

      '<p>',
        'The question is whether a city can <em>show up</em>. Not on paper &mdash; in practice.',
      '</p>',

      '<h2>Three Pillars</h2>',

      '<p>',
        'The CQ is a weighted composite of ten scored metrics organized into three pillars. ',
        'Pillar weights prioritize the relational layer (care ethics tradition) over the institutional ',
        'and access dimensions &mdash; a normative commitment, not an empirical finding. ',
        'Within-pillar weights draw on factor analysis across the 68 cities.',
      '</p>',

      '<table class="method-table">',
        '<thead><tr>',
          '<th>Pillar</th><th>What it measures</th><th>Weight</th>',
        '</tr></thead>',
        '<tbody>',
          '<tr>',
            '<td><span class="ptag ptag-p1">Social &amp; Relational Care</span></td>',
            '<td>Residential stability, care nonprofit density, library density, and religious organization density &mdash; the conditions under which people actually notice and respond to need.</td>',
            '<td>40%</td>',
          '</tr>',
          '<tr>',
            '<td><span class="ptag ptag-p2">Institutional Care</span></td>',
            '<td>FQHC density, nursing home capacity, and child care capacity: formal institutions designed to absorb distress at scale, serving residents regardless of ability to pay.</td>',
            '<td>35%</td>',
          '</tr>',
          '<tr>',
            '<td><span class="ptag ptag-p3">Economic Access to Care</span></td>',
            '<td>Healthcare coverage, housing affordability, and SNAP participation: whether economic conditions allow care to reach those who need it.</td>',
            '<td>25%</td>',
          '</tr>',
        '</tbody>',
      '</table>',

      '<h2>Benchmarks</h2>',

      '<p>',
        'Each metric is scored against an absolute benchmark representing a meaningful threshold. ',
        '<code>score = min(value / benchmark &times; 100, 100)</code>. ',
        'Scores are absolute. Adding or removing cities does not change existing scores. ',
        'A score of 70 means the city reaches 70% of the benchmark, not that it ranks 70th.',
      '</p>',

      '<table class="method-table">',
        '<thead><tr>',
          '<th>Metric</th><th>Benchmark</th><th>Source</th>',
        '</tr></thead>',
        '<tbody>',
          '<tr><td>Residential Stability</td>       <td>95% same house 1+ yr</td>                          <td>Census ACS B07003</td></tr>',
          '<tr><td>Care Nonprofits (P+E+F+K)</td>   <td>25 per 10,000 residents</td>                      <td>IRS EO BMF</td></tr>',
          '<tr><td>Library Density</td>             <td>5 per 100,000 residents</td>                      <td>IMLS Public Libraries Survey</td></tr>',
          '<tr><td>Religious Org. Density</td>      <td>150 per 100,000 residents</td>                    <td>ARDA 2020</td></tr>',
          '<tr><td>FQHC Density</td>               <td>15 per 100,000 residents</td>                     <td>HRSA Health Center Data</td></tr>',
          '<tr><td>Nursing Home Capacity</td>       <td>50 beds per 1,000 residents 65+</td>              <td>CMS Care Compare</td></tr>',
          '<tr><td>Child Care Capacity</td>         <td>15 establishments per 1,000 children under 5</td><td>Census CBP NAICS 624410</td></tr>',
          '<tr><td>Healthcare Coverage (Medicaid/CHIP)</td><td>100% of income-eligible residents enrolled</td><td>Census ACS C27007</td></tr>',
          '<tr><td>Housing Affordability</td>       <td>90% not cost-burdened</td>                        <td>Census ACS B25070, B25091</td></tr>',
          '<tr><td>SNAP Coverage Rate</td>          <td>85% of likely-eligible</td>                       <td>Census ACS B22001, C17002</td></tr>',
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
        '<strong>Honolulu exception:</strong> Hawaii has no incorporated municipalities. ',
        'Honolulu is a Census Designated Place absent from the ZCTA-to-Place crosswalk. The ',
        'pipeline falls back to Honolulu County boundaries, which are broader than the urban core. ',
        'Density metrics for Honolulu may be modestly overstated as a result.',
      '</p>',

      '<h2>How to read the scores</h2>',

      '<p>',
        'The CQ is designed to be read as a measure against a benchmark, not as a competition. ',
        'Cities within 3 to 4 points should be treated as rough peers. Differences of that ',
        'size may fall within the margin of geographic approximation or a single year&rsquo;s data variance. ',
        'The index is most useful for identifying cities at the extremes, understanding which ',
        '<em>specific</em> metrics drive a city&rsquo;s score, and tracking change over time.',
      '</p>',

      '<h2>What this index does not measure</h2>',

      '<p>',
        'The CQ intentionally excludes health outcomes, income, safety, and general quality of life. ',
        'These are <em>conditions</em>, the result of many factors including care capacity, ',
        'but also wealth, history, and policy. Including them would conflate what a city ',
        '<em>has</em> with whether it can <em>show up</em> for its residents.',
      '</p>',

      '<p>',
        'A city in a non-Medicaid-expansion state will score lower on health insurance coverage. ',
        'This is intentional. A state&rsquo;s decision not to expand Medicaid is a real ',
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
        'May 2026. 68 cities. ',
        'Data sources: IRS EO BMF, Census ACS 2022 5-year estimates, ',
        'HRSA Health Center Service Delivery, IMLS Public Libraries Survey FY2023, ',
        'CMS Care Compare Nursing Home Provider Information, CDC PLACES (2022/2023). ',
        'All data collection and scoring code is available in the ',
        '<a href="https://github.com/petedur/Care-Quotient---Claude-Code" target="_blank" rel="noopener">project repository</a>.',
      '</p>',

    '</div>',
    renderFooter(),
  ].join('');
}

// ── Theory page ─────────────────────────────────────────────────────────────

function renderTheory(app) {
  app.innerHTML = [
    '<div class="method-page">',

      '<a href="#/" class="back-link">&#8592; All cities</a>',

      '<div class="method-eyebrow">Theoretical Foundation</div>',
      '<h1>What is Care?</h1>',

      '<p>',
        'Care is the set of practices and relationships through which people maintain, continue, and ',
        'repair the world so that they can live in it as well as possible. That definition, from ',
        'Joan Tronto, gives this project its basic orientation. The question here is narrower: does a ',
        'city&rsquo;s infrastructure make that kind of living easier or harder?',
      '</p>',

      '<h2>Why care about care?</h2>',

      '<p>We should care about care for two big reasons.</p>',

      '<p>',
        'First, care helps societies do hard things together. Trust and social capital make cooperation ',
        'broader, steadier, and easier to sustain over time. The OECD treats trust as a key ingredient ',
        'of growth, social cohesion, well-being, and governance, and the National Academies describes ',
        'social capital and connectedness as community assets that help communities function and recover ',
        'from shocks. In their 1997 Chicago study, Robert Sampson, Stephen Raudenbush, and Felton Earls ',
        'found that neighborhoods with stronger collective efficacy &mdash; social cohesion combined with ',
        'a willingness to act for the common good &mdash; experienced lower violence, and that some of ',
        'the harms associated with concentrated disadvantage and residential instability ran through weaker ',
        'collective efficacy. The larger lesson is that care helps societies coordinate. It makes it easier ',
        'to build institutions, carry public burdens, and keep working together when life gets difficult.',
      '</p>',

      '<p>',
        'Second, caring seems to be good for the person doing it. There is evidence that prosocial ',
        'behavior is associated with higher well-being, and in some cases seems to improve it directly. ',
        'Lara Aknin and her coauthors, using survey data from 136 countries, found that spending money on ',
        'others was consistently associated with greater happiness, and experiments in both Canada and ',
        'Uganda suggested that the effect was causal. That fits something many people already know from ',
        'experience: responsibility for other people can be heavy, but it can also create meaning, ',
        'connection, and a healthier sense of self.',
      '</p>',

      '<h2>Care starts in relationship</h2>',

      '<p>',
        'People have to be able to notice one another before they can really respond to one another. ',
        'That is harder in places where people are constantly displaced, cut off from neighbors, or ',
        'forced to rebuild their lives every year or two. It is easier in places where people remain ',
        'in contact long enough for trust, habit, and mutual obligation to take shape.',
      '</p>',

      '<p>',
        'Residential stability and local organizations are imperfect but useful ways of seeing whether ',
        'a community can hold together over time. Stable housing can reflect attachment and durable ',
        'social ties, and it can also reflect constraint. Public spaces, like libraries, do not solve ',
        'care on their own, but they help create the civic texture in which care becomes more likely. ',
        'They are among the few institutions that receive people without much sorting or gatekeeping, ',
        'and they offer basic resources ranging from community space to internet access.',
      '</p>',

      '<h2>Care also has to be organized</h2>',

      '<p>Care lives in relationships, and it also has to be built into institutions.</p>',

      '<p>',
        'People need places to go, professionals who can help, and organizations that can absorb ',
        'distress when informal networks are not enough. Federally qualified health centers, nonprofit ',
        'service providers, and elder-care infrastructure matter for exactly this reason. They are the ',
        'difference between a city that hopes someone will step in and a city that has actually built ',
        'capacity for that to happen. A city that relies only on private goodwill will leave the people ',
        'with the fewest resources, the weakest networks, or the greatest needs with too little to fall ',
        'back on.',
      '</p>',

      '<h2>Access matters as much as presence</h2>',

      '<p>Having care infrastructure on paper is one thing. People still need a path to it.</p>',

      '<p>',
        'The index includes measures like health coverage, housing affordability, and safety-net reach ',
        'to reflect this path. These conditions shape whether people can actually receive the care a ',
        'city claims to offer. A city can have good organizations and still fail to reach the people ',
        'who need them. Coverage may be thin. Rent may be crushing. Food assistance may miss eligible ',
        'households. In those cases, the existence of care infrastructure matters less than it should.',
      '</p>',

      '<h2>Why these three pillars</h2>',

      '<p>The index is built around three questions.</p>',

      '<ul class="theory-list">',
        '<li>Does a city have the social fabric that makes people visible to one another?</li>',
        '<li>Does it have institutions that can absorb need when it appears?</li>',
        '<li>Can people actually reach those institutions when they need them?</li>',
      '</ul>',

      '<p>The first pillar is relational. The second is institutional. The third is about access.</p>',

      '<p>',
        'These are practical categories rather than philosophical absolutes. Their job is to make a ',
        'moral idea measurable without flattening it completely.',
      '</p>',

      '<h2>Limits of this index</h2>',

      '<p>',
        'The Care Quotient is a partial measure of care capacity. It captures some of the conditions ',
        'under which care becomes more likely. It leaves a great deal out.',
      '</p>',

      '<p>',
        'It cannot capture love, dignity, informal family labor, or the quality of human attention. ',
        'It also does not try to measure prosperity, public safety, or health outcomes. Those things ',
        'matter, but they answer different questions. A city that looks successful on paper can still ',
        'leave vulnerable people with nowhere to turn.',
      '</p>',

      '<p>',
        'This project makes a narrower claim. It asks whether a city has built the social ties, ',
        'organizations, and access conditions that make it easier for people to get help when they ',
        'need it. The point is to make that capacity easier to see, compare, and find ways to be even better.',
      '</p>',

      '<h2>Theory-to-metric mapping</h2>',

      '<p>The following table shows which theoretical concepts motivate each scored metric.</p>',

      '<table class="method-table theory-table">',
        '<thead><tr>',
          '<th>Metric</th><th>Pillar</th><th>Primary theoretical warrant</th>',
        '</tr></thead>',
        '<tbody>',
          '<tr>',
            '<td>Residential Stability</td>',
            '<td><span class="ptag ptag-p1">Social &amp; Relational</span></td>',
            '<td>Putnam (2000): structural driver of social capital. Sampson et al. (1997): precondition for collective efficacy. Noddings (1984): stability creates conditions for attentiveness and genuine care.</td>',
          '</tr>',
          '<tr>',
            '<td>Care Nonprofit Density</td>',
            '<td><span class="ptag ptag-p1">Social &amp; Relational</span></td>',
            '<td>Tronto (1993): organized responsibility for identified need. Sampson et al. (1997): dense organizational life predicts collective efficacy. Salamon &amp; Anheier (1998): nonprofit density as civil society capacity indicator.</td>',
          '</tr>',
          '<tr>',
            '<td>Library Density</td>',
            '<td><span class="ptag ptag-p1">Social &amp; Relational</span></td>',
            '<td>Held (2006): institutions designed as caring spaces that receive everyone without gatekeeping. Nussbaum (2006): affiliation capability requires spaces where people can be in public community.</td>',
          '</tr>',
          '<tr>',
            '<td>Religious Organization Density</td>',
            '<td><span class="ptag ptag-p1">Social &amp; Relational</span></td>',
            '<td>Putnam (2000): religious participation as a consistent predictor of social capital — congregations generate bridging and bonding ties that underpin informal mutual aid. Chaves &amp; Tsitsos (2001): most US congregations provide at least one social service through informal networks. Scored via ARDA 2020 Religion Census; distinct from IRS-coded faith-based nonprofits.</td>',
          '</tr>',
          '<tr>',
            '<td>FQHC Density</td>',
            '<td><span class="ptag ptag-p2">Institutional</span></td>',
            '<td>Tronto (1993): competent delivery of formal care. Sen (1999): converting right to care into actual capability. Rosenbaum et al. (2011): FQHCs as primary safety-net care infrastructure.</td>',
          '</tr>',
          '<tr>',
            '<td>Nursing Home Capacity</td>',
            '<td><span class="ptag ptag-p2">Institutional</span></td>',
            '<td>Kittay (1999): institutionalized dependency support. Tronto (1993): competence phase for high-dependency populations. Institutional absorption of elder dependency vs. private family burden.</td>',
          '</tr>',
          '<tr>',
            '<td>Child Care Capacity</td>',
            '<td><span class="ptag ptag-p2">Institutional</span></td>',
            '<td>Folbre (2001): care provision is a public good that markets underinvest in; the cost of gaps falls disproportionately on low-income families. Kittay (1999): dependency in early childhood requires organized infrastructure, not only family labor.</td>',
          '</tr>',
          '<tr>',
            '<td>Healthcare Coverage</td>',
            '<td><span class="ptag ptag-p3">Economic Access</span></td>',
            '<td>Folbre (2001): who can access care that nominally exists? Sen (1999): Medicaid/CHIP as the public mechanism for converting care infrastructure into real capability for low-income populations.</td>',
          '</tr>',
          '<tr>',
            '<td>Housing Affordability</td>',
            '<td><span class="ptag ptag-p3">Economic Access</span></td>',
            '<td>Folbre (2001): economic conditions that determine care accessibility. Desmond &amp; Bell (2015); Agha et al. (2024): housing cost burden directly reduces capacity to seek and receive care.</td>',
          '</tr>',
          '<tr>',
            '<td>SNAP Coverage</td>',
            '<td><span class="ptag ptag-p3">Economic Access</span></td>',
            '<td>Nussbaum (2006): bodily health capability requires adequate nourishment. Food security program reach as a measure of whether the state&rsquo;s economic safety net is accessible to those who qualify.</td>',
          '</tr>',
        '</tbody>',
      '</table>',

      '<h2>References</h2>',

      '<ul class="theory-refs">',
        '<li>Agha, G., et al. (2024). Housing cost burden and health care utilization. <em>JAMA Internal Medicine</em>.</li>',
        '<li>Aknin, L.B., et al. (2013). Prosocial spending and well-being: Cross-cultural evidence for a psychological universal. <em>Journal of Personality and Social Psychology</em>, 104(4), 635&ndash;652.</li>',
        '<li>Desmond, M. & Bell, M. (2015). Housing, poverty, and the law. <em>Annual Review of Law and Social Science</em>, 11, 15&ndash;35.</li>',
        '<li>Folbre, N. (2001). <em>The Invisible Heart: Economics and Family Values</em>. New Press.</li>',
        '<li>Held, V. (2006). <em>The Ethics of Care: Personal, Political, and Global</em>. Oxford University Press.</li>',
        '<li>Kittay, E.F. (1999). <em>Love&rsquo;s Labor: Essays on Women, Equality, and Dependency</em>. Routledge.</li>',
        '<li>National Academies of Sciences, Engineering, and Medicine (2017). <em>Communities in Action: Pathways to Health Equity</em>. National Academies Press.</li>',
        '<li>Noddings, N. (1984). <em>Caring: A Relational Approach to Ethics and Moral Education</em>. University of California Press.</li>',
        '<li>Nussbaum, M.C. (2006). <em>Frontiers of Justice: Disability, Nationality, Species Membership</em>. Harvard University Press.</li>',
        '<li>OECD (2017). <em>Trust and Public Policy: How Better Governance Can Help Rebuild Public Trust</em>. OECD Publishing.</li>',
        '<li>Putnam, R.D. (2000). <em>Bowling Alone: The Collapse and Revival of American Community</em>. Simon &amp; Schuster.</li>',
        '<li>Rosenbaum, S., et al. (2011). National security and U.S. child health policy: The origins and continuing role of Medicaid and CHIP. <em>Annual Review of Public Health</em>, 32, 345&ndash;361.</li>',
        '<li>Salamon, L.M. & Anheier, H.K. (1998). Social origins of civil society: Explaining the nonprofit sector cross-nationally. <em>Voluntas</em>, 9(3), 213&ndash;248.</li>',
        '<li>Sampson, R.J., Raudenbush, S.W., & Earls, F. (1997). Neighborhoods and violent crime: A multilevel study of collective efficacy. <em>Science</em>, 277(5328), 918&ndash;924.</li>',
        '<li>Sen, A. (1999). <em>Development as Freedom</em>. Anchor Books.</li>',
        '<li>Tronto, J.C. (1993). <em>Moral Boundaries: A Political Argument for an Ethic of Care</em>. Routledge.</li>',
      '</ul>',

    '</div>',
    renderFooter(),
  ].join('');
}

// ── Chat ─────────────────────────────────────────────────────────────────────

var _chatState = {
  messages: [],
  loading: false,
  cityContext: null,
};

function buildCityContext() {
  if (_chatState.cityContext) return _chatState.cityContext;
  var cities = getCitiesSorted();
  var lines = cities.map(function(c) {
    var mets = METRIC_ORDER.map(function(mk) {
      var m = c.metrics && c.metrics[mk];
      return m ? mk + ':' + fmt(m.score, 0) : '';
    }).filter(Boolean).join(' ');
    return (
      c.name + ', ' + c.state + ' (' + c.key + '): CQ=' + fmt(c.cq, 1) +
      ' [' + cqTier(c.cq).label + '] P1=' + fmt(c.pillar1, 1) +
      ' P2=' + fmt(c.pillar2, 1) + ' P3=' + fmt(c.pillar3, 1) +
      ' | ' + mets
    );
  });
  _chatState.cityContext = lines.join('\n');
  return _chatState.cityContext;
}

function escapeHtml(str) {
  return str
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;');
}

function formatChatContent(text) {
  return escapeHtml(text)
    .replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>')
    .replace(/\*(.+?)\*/g, '<em>$1</em>')
    .replace(/^---$/gm, '<hr>')
    .replace(/\n/g, '<br>');
}

function updateChatMessages() {
  var container = document.getElementById('chat-messages');
  if (!container) return;

  var html = _chatState.messages.map(function(m) {
    return [
      '<div class="chat-msg chat-msg-', m.role, '">',
        '<div class="chat-bubble chat-bubble-', m.role, '">',
          formatChatContent(m.content),
        '</div>',
      '</div>',
    ].join('');
  }).join('');

  if (_chatState.loading) {
    html += [
      '<div class="chat-msg chat-msg-assistant">',
        '<div class="chat-bubble chat-bubble-assistant chat-bubble-loading">',
          '<span class="chat-dots"><span></span><span></span><span></span></span>',
        '</div>',
      '</div>',
    ].join('');
  }

  container.innerHTML = html;
  container.scrollTop = container.scrollHeight;
}

function sendChatMessage(text) {
  var sugg = document.querySelector('.chat-suggestions');
  if (sugg) sugg.remove();

  _chatState.messages.push({ role: 'user', content: text });
  _chatState.loading = true;
  updateChatMessages();

  var msgPayload = _chatState.messages.map(function(m) {
    return { role: m.role, content: m.content };
  });

  fetch('/api/chat', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      messages: msgPayload,
      cityContext: buildCityContext(),
    }),
  }).then(function(res) {
    if (!res.ok) throw new Error('HTTP ' + res.status);

    _chatState.loading = false;
    _chatState.messages.push({ role: 'assistant', content: '' });
    var msgIdx = _chatState.messages.length - 1;
    updateChatMessages();

    var reader = res.body.getReader();
    var decoder = new TextDecoder();
    var buffer = '';

    function pump() {
      return reader.read().then(function(result) {
        if (result.done) {
          updateChatMessages();
          return;
        }
        buffer += decoder.decode(result.value, { stream: true });
        var parts = buffer.split('\n\n');
        buffer = parts.pop();
        parts.forEach(function(part) {
          var line = part.trim();
          if (!line.startsWith('data: ')) return;
          var data = line.slice(6);
          if (data === '[DONE]') return;
          try {
            var parsed = JSON.parse(data);
            if (parsed.text) {
              _chatState.messages[msgIdx].content += parsed.text;
              updateChatMessages();
            }
            if (parsed.error) {
              _chatState.messages[msgIdx].content = parsed.error;
              updateChatMessages();
            }
          } catch (e) { /* skip malformed */ }
        });
        return pump();
      });
    }
    return pump();
  }).catch(function() {
    _chatState.loading = false;
    _chatState.messages.push({ role: 'assistant', content: 'Sorry, something went wrong. Please try again.' });
    updateChatMessages();
  });
}

function renderChat(app) {
  var cities = getCitiesSorted();
  var topCity = cities[0];
  var bottomCity = cities[cities.length - 1];

  var suggestions = [
    'Why does ' + topCity.name + ' rank #1?',
    'Which city has the weakest care infrastructure overall?',
    'What\'s the difference between care capacity and quality of life?',
    'What could ' + bottomCity.name + ' do to improve its score?',
  ];

  var suggestionsHtml = _chatState.messages.length === 0 ? [
    '<div class="chat-suggestions">',
      '<p class="chat-suggestions-label">Try asking:</p>',
      '<div class="chat-suggestion-grid">',
        suggestions.map(function(s) {
          return '<button class="chat-suggestion" data-prompt="' + escapeHtml(s) + '">' + escapeHtml(s) + '</button>';
        }).join(''),
      '</div>',
    '</div>',
  ].join('') : '';

  app.innerHTML = [
    '<div class="chat-page">',
      '<a href="#/" class="back-link">&#8592; All cities</a>',

      '<div class="chat-header">',
        '<div class="chat-eyebrow">Ask the Data</div>',
        '<h1 class="chat-title">Care Quotient Assistant</h1>',
        '<p class="chat-intro">',
          'Ask about any city\'s score, compare two cities, ask about the methodology, ',
          'or discuss what it actually means for a city to show up for its residents.',
        '</p>',
      '</div>',

      '<div class="chat-window">',
        '<div id="chat-messages" class="chat-messages">',
          suggestionsHtml,
        '</div>',

        '<div class="chat-input-area">',
          '<textarea id="chat-input" class="chat-input" placeholder="Ask about any city or topic…" rows="1" maxlength="2000"></textarea>',
          '<button id="chat-send" class="chat-send-btn" aria-label="Send">',
            '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round" width="18" height="18">',
              '<line x1="12" y1="19" x2="12" y2="5"/>',
              '<polyline points="5 12 12 5 19 12"/>',
            '</svg>',
          '</button>',
        '</div>',
      '</div>',

      '<p class="chat-disclaimer">Responses are generated by Claude (Anthropic). Data accuracy depends on current CQ scores.</p>',
    '</div>',
  ].join('');

  if (_chatState.messages.length > 0) {
    updateChatMessages();
  }

  var input  = document.getElementById('chat-input');
  var sendBtn = document.getElementById('chat-send');

  function doSend() {
    var text = input.value.trim();
    if (!text || _chatState.loading) return;
    input.value = '';
    input.style.height = 'auto';
    sendChatMessage(text);
  }

  sendBtn.addEventListener('click', doSend);
  input.addEventListener('keydown', function(e) {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      doSend();
    }
  });
  input.addEventListener('input', function() {
    this.style.height = 'auto';
    this.style.height = Math.min(this.scrollHeight, 140) + 'px';
  });

  document.querySelectorAll('.chat-suggestion').forEach(function(btn) {
    btn.addEventListener('click', function() {
      sendChatMessage(btn.dataset.prompt);
    });
  });
}

// ── Footer ──────────────────────────────────────────────────────────────────

function renderFooter() {
  return [
    '<footer class="site-footer">',
      '<div class="footer-copy">',
        'Care Quotient &nbsp;&middot;&nbsp; 68 American Cities &nbsp;&middot;&nbsp; May 2026<br>',
        'Data: IRS EO BMF &middot; Census ACS 2022 &middot; HRSA &middot; IMLS &middot; CMS Care Compare',
      '</div>',
      '<div class="footer-links">',
        '<a href="#/theory">What is Care?</a>',
        '<a href="#/methodology">Methodology</a>',
        '<a href="#/compare">Compare</a>',
        '<a href="#/">Index</a>',
      '</div>',
    '</footer>',
  ].join('');
}
