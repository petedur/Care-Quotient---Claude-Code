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
      '<div class="hero-eyebrow">Care Quotient &middot; V6</div>',
      '<h1 class="hero-headline">When someone needs help,<br>can their city show up?</h1>',
      '<div class="hero-rule"></div>',
      '<p class="hero-subhead">',
        'A data-driven index measuring care capacity for American cities. ',
        'Not prosperity, not health outcomes, but the social networks, institutions, ',
        'and systems that determine whether people can get help when they need it.',
      '</p>',
    '</section>',

    // ── Map ───────────────────────────────────────────────────────────────
    '<section class="section-wrap map-section">',
      '<span class="section-label">68 Cities Mapped</span>',
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
            'Whether the relational infrastructure for care exists: stable communities, ',
            'the organized nonprofits that show up when people need help, and the public spaces ',
            'that hold communities together.',
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
          '<p class="what-is-note">',
            'A prosperous city is not necessarily a caring one. This index measures one of them.',
          '</p>',
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
  'child_care',
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

      '<div class="method-eyebrow">Methodology &middot; V6</div>',
      '<h1>How the Care Quotient is built</h1>',

      '<p>',
        'The Care Quotient measures <strong>care capacity</strong>: the extent to which a ',
        'community has the social ties, institutions, and systems needed to support people in ',
        'moments of vulnerability. This is explicitly <em>not</em> a quality-of-life index. A city ',
        'can score well on income, safety, and health outcomes while having thin care infrastructure ',
        'for its most vulnerable residents. The inverse is also true.',
      '</p>',

      '<p>',
        'The motivating question is whether communities have what it takes to <em>show up</em> for people, ',
        'through networks, institutions, and reach, when people need help.',
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
            '<td>Residential stability, care nonprofit density, and library density: the relational infrastructure that enables communities to notice and respond to need.</td>',
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
        'V6 (May 2026). 68 cities. ',
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
        'The Care Quotient is not just a data exercise. It is grounded in a half-century of scholarship ',
        'asking what care is, who provides it, and what social structures make it possible or impossible. ',
        'This page traces that intellectual lineage &mdash; both to show what the index is trying to measure ',
        'and to explain why the specific metrics and weights were chosen.',
      '</p>',

      '<p>',
        'The short answer: care is the set of practices and relationships through which people ',
        'maintain, continue, and repair the world so that they can live in it as well as possible. ',
        'That definition, from Tronto (1993), is the index&rsquo;s north star. Everything that follows ',
        'is an attempt to measure whether a city&rsquo;s infrastructure makes that kind of living possible.',
      '</p>',

      '<h2>I. Care Ethics: The Foundation</h2>',

      '<h3>Joan Tronto &mdash; <em>Moral Boundaries</em> (1993)</h3>',
      '<p>',
        'Joan Tronto, building on work with Berenice Fisher, gave care its most influential modern ',
        'definition: &ldquo;On the most general level, we suggest that caring be viewed as a species ',
        'activity that includes everything that we do to maintain, continue, and repair our &lsquo;world&rsquo; ',
        'so that we can live in it as well as possible.&rdquo; This is not a narrowly domestic definition. ',
        'Care for Tronto is political, institutional, and social &mdash; it includes healthcare, ',
        'elder care, childcare, neighborhood mutual aid, and every form of attention to human vulnerability.',
      '</p>',
      '<p>',
        'Tronto identified four phases of caring practice that structure the index&rsquo;s pillar architecture:',
      '</p>',
      '<ul class="theory-list">',
        '<li><strong>Caring about</strong> &mdash; attentiveness to need; the moral achievement of noticing ',
        'that someone requires care. This is the relational precondition. Without stable communities where ',
        'people know their neighbors, attentiveness fails at scale. <em>Pillar 1 is about whether this ',
        'attentiveness infrastructure exists.</em></li>',
        '<li><strong>Taking care of</strong> &mdash; responsibility; the decision to act in response to ',
        'identified need. Nonprofits, public institutions, and community organizations are the organized ',
        'form of this responsibility. <em>Nonprofit density in Pillar 1 measures organized community ',
        'response.</em></li>',
        '<li><strong>Care-giving</strong> &mdash; competence; actually providing care, meeting the physical ',
        'and relational needs of the person being cared for. Formal institutions &mdash; health centers, ',
        'nursing homes &mdash; are the competence layer. <em>Pillar 2 measures institutional competence.</em></li>',
        '<li><strong>Care-receiving</strong> &mdash; responsiveness; whether care actually lands and the ',
        'cared-for can receive it. Economic access barriers determine whether the above reaches those who ',
        'need it. <em>Pillar 3 measures whether these barriers exist.</em></li>',
      '</ul>',
      '<p>',
        'The 40/35/25 inter-pillar weights reflect Tronto&rsquo;s ordering: attentiveness is ',
        'theoretically prior. You cannot have institutional care without social acknowledgment of need. ',
        'The relational layer is not merely important &mdash; it is the precondition for everything else.',
      '</p>',

      '<h3>Carol Gilligan &mdash; <em>In a Different Voice</em> (1982)</h3>',
      '<p>',
        'Gilligan&rsquo;s foundational insight was that an &ldquo;ethic of care&rdquo; &mdash; one grounded in ',
        'responsibility, relationship, and context &mdash; had been systematically excluded from moral ',
        'philosophy. Where the dominant tradition (following Kohlberg) saw mature moral reasoning as ',
        'impartial, rule-based, and abstract, Gilligan documented a different kind of moral reasoning: ',
        'one attentive to particularity, relationship, and context. This ethic asks not &ldquo;what does ',
        'justice require?&rdquo; but &ldquo;how do I respond to this person&rsquo;s need?&rdquo;',
      '</p>',
      '<p>',
        'The Care Quotient is Gilliganian in its animating question. It does not ask whether cities are ',
        'just in the abstract. It asks whether they can respond &mdash; concretely, institutionally, ',
        'relationally &mdash; when specific people need help.',
      '</p>',

      '<h3>Nel Noddings &mdash; <em>Caring: A Feminine Approach to Ethics and Moral Education</em> (1984)</h3>',
      '<p>',
        'Noddings grounded care ethics in the particular relationship between the one-caring and the ',
        'cared-for, arguing that genuine care requires motivational displacement &mdash; the carer sets ',
        'aside their own projects to receive and attend to the cared-for&rsquo;s reality. ',
        'What Noddings describes as &ldquo;engrossment&rdquo; in the other&rsquo;s condition is precisely what ',
        'Tronto calls attentiveness. It requires proximity, time, and familiarity &mdash; all of which ',
        'require residential stability. A community of strangers cannot practice Noddings-style care. ',
        '<em>Residential stability in Pillar 1 is, in part, about whether a city creates the conditions ',
        'for Noddings-style engrossment to be possible at all.</em>',
      '</p>',

      '<h3>Virginia Held &mdash; <em>The Ethics of Care</em> (2006)</h3>',
      '<p>',
        'Held argues that care is not a supplement to justice but an alternative moral paradigm with equal ',
        'philosophical standing. Where justice focuses on equal rights and impartial procedures, care ',
        'focuses on &ldquo;the cultivation of caring relations.&rdquo; Held&rsquo;s framework insists that ',
        'good social institutions must be designed with care relationships at their center, not as an ',
        'afterthought. The CQ&rsquo;s decision to include library density as a scored metric reflects ',
        'Held&rsquo;s argument: libraries are one of the few public institutions specifically designed as ',
        'caring spaces &mdash; places that receive everyone, ask nothing, and offer a resource without ',
        'condition.',
      '</p>',

      '<h2>II. Social Capital and Collective Efficacy</h2>',

      '<h3>Robert Putnam &mdash; <em>Bowling Alone</em> (2000) and <em>Making Democracy Work</em> (1993)</h3>',
      '<p>',
        'Putnam&rsquo;s research documented the decline of social capital &mdash; the networks of ',
        'association and reciprocity that enable collective action &mdash; across late 20th-century ',
        'American communities. His key finding relevant to the CQ: social capital predicts mutual ',
        'support, community trust, civic engagement, and informal care provision. Communities with ',
        'high social capital are literally better at taking care of each other.',
      '</p>',
      '<p>',
        'Putnam distinguishes <em>bonding</em> capital (ties within homogeneous groups) from ',
        '<em>bridging</em> capital (ties across different groups). For care capacity, bridging capital ',
        'is more important: it&rsquo;s the networks that connect residents across lines of class, ',
        'race, and geography that make institutional care accessible to people outside the informal ',
        'networks of their immediate community.',
      '</p>',
      '<p>',
        'Putnam also identifies residential stability as a primary structural driver of social capital. ',
        'His analysis of American cities shows that high-turnover communities consistently develop ',
        'weaker civic infrastructure, lower institutional participation, and less mutual aid behavior. ',
        '<em>This is the primary citation supporting Residential Stability&rsquo;s 50% weight in Pillar 1.</em>',
      '</p>',

      '<h3>Robert Sampson, Stephen Raudenbush & Felton Earls &mdash; &ldquo;Neighborhoods and Violent Crime&rdquo; (1997)</h3>',
      '<p>',
        'Sampson and colleagues introduced the concept of <em>collective efficacy</em> &mdash; the ',
        'combination of social cohesion (the trust and mutual concern that residents feel toward each other) ',
        'and willingness to intervene on behalf of the common good. Their landmark Chicago study demonstrated ',
        'that collective efficacy predicts better health, safety, and community outcomes across neighborhoods ',
        'even after controlling for poverty, race, and other structural factors.',
      '</p>',
      '<p>',
        'Collective efficacy is generalized care capacity in action: it is the community&rsquo;s demonstrated ',
        'willingness and ability to respond when someone needs help. Sampson et al. found that collective ',
        'efficacy is strongest in neighborhoods with residential stability, dense organizational life, ',
        'and strong local institutions. <em>All three Pillar 1 metrics &mdash; residential stability, ',
        'nonprofit density, and library density &mdash; are operationalizations of the structural ',
        'preconditions Sampson et al. identify for collective efficacy to emerge.</em>',
      '</p>',

      '<h2>III. The Political Economy of Care</h2>',

      '<h3>Nancy Folbre &mdash; <em>The Invisible Heart</em> (2001)</h3>',
      '<p>',
        'Folbre brought care into political economy, documenting how care work is systematically ',
        'undervalued, unpaid, and taken for granted by economic and policy systems. Her central argument: ',
        'care provision is a public good that markets underinvest in. When communities have weak care ',
        'infrastructure, the cost falls disproportionately on women, low-income families, and those ',
        'without market access to paid care services.',
      '</p>',
      '<p>',
        'Folbre&rsquo;s work directly motivates the Economic Access to Care pillar. It is not enough to ',
        'have care institutions; those institutions must be reachable. Health coverage (whether public ',
        'programs extend to those who need them), housing affordability (whether people can stay housed ',
        'enough to access care), and SNAP coverage (whether food security programs reach the eligible) ',
        'are all measures of whether the care economy is equitably organized or whether it systematically ',
        'excludes the most vulnerable. <em>Pillar 3 is Folbre&rsquo;s question operationalized: who can ',
        'actually access the care that nominally exists?</em>',
      '</p>',

      '<h3>Eva Feder Kittay &mdash; <em>Love&rsquo;s Labor</em> (1999)</h3>',
      '<p>',
        'Kittay&rsquo;s contribution centers dependency: her argument is that human dependency is not an ',
        'exception to the human condition but its defining feature. We are all dependent at some point ',
        '&mdash; in infancy, illness, old age, crisis &mdash; and any adequate moral and political theory ',
        'must account for this. Kittay introduces the concept of the <em>doulia</em> &mdash; the ',
        'principle that those who provide care should themselves receive support, because dependency is ',
        'relational: care providers need care too.',
      '</p>',
      '<p>',
        'The nursing home capacity metric in Pillar 2 is where Kittay&rsquo;s work is most directly visible. ',
        'Elder care is the most institutionalized form of dependency support we have &mdash; the formal ',
        'manifestation of a society&rsquo;s decision about whether to absorb human dependency into its ',
        'institutional structure or leave it to family members (disproportionately women) to absorb ',
        'privately. A city with higher nursing home capacity has decided, structurally, to support that ',
        'form of dependency with organized infrastructure.',
      '</p>',

      '<h2>IV. The Capabilities Approach</h2>',

      '<h3>Amartya Sen &mdash; <em>Development as Freedom</em> (1999)</h3>',
      '<p>',
        'Sen&rsquo;s capabilities approach shifts the focus of development from income and resources to ',
        'what people are actually able to do and be. Resources matter insofar as they convert into real ',
        'freedoms and capabilities. A person with health insurance who cannot access a doctor due to ',
        'shortage is less capable than the insurance figure suggests. A person with nominally adequate ',
        'income who is cost-burdened on housing has fewer real freedoms than their income implies.',
      '</p>',
      '<p>',
        'The FQHC density metric in Pillar 2 is a direct application of Sen&rsquo;s framework: FQHCs are ',
        'the infrastructure that converts the right to care into an actual capability. They serve patients ',
        'regardless of ability to pay, accept Medicaid, and are specifically designed to ensure that ',
        'care resources reach people who need them rather than people who can afford them.',
      '</p>',

      '<h3>Martha Nussbaum &mdash; <em>Frontiers of Justice</em> (2006)</h3>',
      '<p>',
        'Nussbaum elaborated Sen&rsquo;s capabilities approach into a specific list of &ldquo;central human ',
        'capabilities&rdquo; &mdash; the conditions necessary for a dignified human life. Among them: ',
        '<em>bodily health</em> (being able to have good health, adequate nourishment, adequate shelter) ',
        'and <em>affiliation</em> (being able to live with and for others, having social bases of ',
        'self-respect and non-humiliation). Both require care infrastructure.',
      '</p>',
      '<p>',
        'Nussbaum&rsquo;s affiliation capability is the most direct theoretical warrant for Pillar 1&rsquo;s ',
        'primacy. The ability to live with and for others &mdash; to form care relationships, to be in ',
        'community, to give and receive support &mdash; is not just instrumentally valuable. It is, on ',
        'Nussbaum&rsquo;s account, constitutive of human dignity. Cities that fail at Pillar 1 fail at ',
        'something foundational.',
      '</p>',

      '<h2>V. Theory-to-Metric Mapping</h2>',

      '<p>The following table shows which theoretical concepts motivate each scored metric.</p>',

      '<table class="method-table theory-table">',
        '<thead><tr>',
          '<th>Metric</th><th>Pillar</th><th>Primary theoretical warrant</th>',
        '</tr></thead>',
        '<tbody>',
          '<tr>',
            '<td>Residential Stability</td>',
            '<td><span class="ptag ptag-p1">Social &amp; Relational</span></td>',
            '<td>Putnam (2000): structural driver of social capital. Sampson et al. (1997): precondition for collective efficacy. Noddings (1984): stability creates conditions for engrossment and genuine care.</td>',
          '</tr>',
          '<tr>',
            '<td>Care Nonprofit Density</td>',
            '<td><span class="ptag ptag-p1">Social &amp; Relational</span></td>',
            '<td>Tronto (1993): &ldquo;taking care of&rdquo; phase &mdash; organized responsibility for identified need. Sampson et al. (1997): dense organizational life predicts collective efficacy. Salamon &amp; Anheier (1998): nonprofit density as civil society capacity indicator.</td>',
          '</tr>',
          '<tr>',
            '<td>Library Density</td>',
            '<td><span class="ptag ptag-p1">Social &amp; Relational</span></td>',
            '<td>Held (2006): institutions designed as caring spaces. Nussbaum (2006): affiliation capability &mdash; spaces where people can be in public community. Libraries as institutions of unconditional welcome and equitable access.</td>',
          '</tr>',
          '<tr>',
            '<td>FQHC Density</td>',
            '<td><span class="ptag ptag-p2">Institutional</span></td>',
            '<td>Tronto (1993): &ldquo;care-giving&rdquo; phase &mdash; competent delivery of formal care. Sen (1999): converting right to care into actual capability. Rosenbaum et al. (2011): FQHCs as primary safety-net care infrastructure.</td>',
          '</tr>',
          '<tr>',
            '<td>Nursing Home Capacity</td>',
            '<td><span class="ptag ptag-p2">Institutional</span></td>',
            '<td>Kittay (1999): institutionalized dependency support. Tronto (1993): competence phase for high-dependency populations. Cities absorbing elder dependency into formal infrastructure vs. private family burden.</td>',
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
            '<td>Nussbaum (2006): bodily health capability requires adequate nourishment. Food security program reach as a measure of whether the state&rsquo;s economic safety net is actually accessible to those who qualify.</td>',
          '</tr>',
        '</tbody>',
      '</table>',

      '<h2>VI. What This Index Does Not Measure</h2>',

      '<p>',
        'The Care Quotient deliberately excludes several categories that often appear in related indices.',
      '</p>',
      '<ul class="theory-list">',
        '<li><strong>Health outcomes</strong> (life expectancy, chronic disease rates, mental health diagnoses): ',
        'These are consequences of care capacity, not measures of it. A city with high mental distress rates ',
        'may need <em>more</em> care infrastructure, not less. The CDC PLACES mental distress and depression ',
        'diagnostics are reported on city pages as community need context precisely because they should ',
        'be read against the capacity scores &mdash; not as scores themselves.</li>',
        '<li><strong>Affluence and income measures</strong>: A city&rsquo;s wealth does not determine its ',
        'care capacity. High-income cities sometimes have thin care infrastructure for low-income residents. ',
        'The CQ is designed to expose this gap, not obscure it.</li>',
        '<li><strong>Quality of services</strong>: The CQ measures density and reach, not clinical quality. ',
        'A city with many FQHCs is not necessarily better at medicine than a city with fewer &mdash; it has ',
        'more geographic and financial access to care. Quality measurement requires patient-level data that ',
        'is not available at city level at this time.</li>',
        '<li><strong>Informal care and family networks</strong>: Multigenerational households, neighbor ',
        'networks, and informal mutual aid are core to care capacity in Tronto&rsquo;s framework but are ',
        'not currently measurable at city level with available administrative data. This is an acknowledged ',
        'limitation. The index captures the institutional and organizational surface of care, not its full ',
        'depth.</li>',
      '</ul>',

      '<h2>VII. Why These Three Pillars?</h2>',

      '<p>',
        'The three-pillar structure is not arbitrary. It reflects a causal claim about how care capacity ',
        'works: relational infrastructure is prior; formal institutions are necessary but not sufficient; ',
        'economic access determines whether any of it reaches the most vulnerable.',
      '</p>',
      '<p>',
        'Tronto&rsquo;s four phases map almost exactly: attentiveness (Pillar 1) enables taking care of ',
        '(also Pillar 1, at the organizational level), enables care-giving (Pillar 2), which becomes ',
        'actual care-receiving (Pillar 3). The pillars are not independent dimensions &mdash; they are ',
        'a causal chain. A city that fails at Pillar 1 will fail at Pillars 2 and 3 even if the ',
        'formal infrastructure exists, because attentiveness to need is the moral prerequisite for ',
        'everything else.',
      '</p>',
      '<p>',
        'The empirical pillar weights (factor analysis yields ~48/35/17) and the theoretical weights ',
        '(40/35/25) are close but not identical. The theoretical weights represent a deliberate normative ',
        'commitment: the relational and access layers are given slightly more weight than the raw factor ',
        'loadings suggest, because the theoretical case for their primacy and importance is stronger than ',
        'the empirical correlation structure alone would imply. This is intentional &mdash; the CQ is an ',
        'index grounded in theory, not just in data reduction.',
      '</p>',

      '<h2>References</h2>',

      '<ul class="theory-refs">',
        '<li>Agha, G., et al. (2024). Housing cost burden and health care utilization. <em>JAMA Internal Medicine</em>.</li>',
        '<li>Boris, E.T. & Steuerle, C.E., eds. (2006). <em>Nonprofits and Government</em>. Urban Institute Press.</li>',
        '<li>Briggs, X. de S. (1998). Brown kids in white suburbs: Housing mobility and the many faces of social capital. <em>Housing Policy Debate</em>, 9(1), 177&ndash;221.</li>',
        '<li>Desmond, M. & Bell, M. (2015). Housing, poverty, and the law. <em>Annual Review of Law and Social Science</em>, 11, 15&ndash;35.</li>',
        '<li>Folbre, N. (2001). <em>The Invisible Heart: Economics and Family Values</em>. New Press.</li>',
        '<li>Gilligan, C. (1982). <em>In a Different Voice: Psychological Theory and Women&rsquo;s Development</em>. Harvard University Press.</li>',
        '<li>Held, V. (2006). <em>The Ethics of Care: Personal, Political, and Global</em>. Oxford University Press.</li>',
        '<li>Kim, M. & Jennings, E.T. (2012). Effects of government ideology on public health policy outcomes. <em>Policy Studies Journal</em>, 40(3), 417&ndash;439.</li>',
        '<li>Kittay, E.F. (1999). <em>Love&rsquo;s Labor: Essays on Women, Equality, and Dependency</em>. Routledge.</li>',
        '<li>Noddings, N. (1984). <em>Caring: A Relational Approach to Ethics and Moral Education</em>. University of California Press.</li>',
        '<li>Nussbaum, M.C. (2006). <em>Frontiers of Justice: Disability, Nationality, Species Membership</em>. Harvard University Press.</li>',
        '<li>Putnam, R.D. (1993). <em>Making Democracy Work: Civic Traditions in Modern Italy</em>. Princeton University Press.</li>',
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

// ── Footer ──────────────────────────────────────────────────────────────────

function renderFooter() {
  return [
    '<footer class="site-footer">',
      '<div class="footer-copy">',
        'Care Quotient V6 &nbsp;&middot;&nbsp; 68 American Cities &nbsp;&middot;&nbsp; May 2026<br>',
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
