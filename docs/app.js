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

function animateBars(containerEl, selector, delay, stagger) {
  delay   = delay   || 80;
  stagger = stagger !== undefined ? stagger : 2;
  var fills = containerEl.querySelectorAll(selector);
  fills.forEach(function(fill, i) {
    setTimeout(function() {
      fill.style.width = fill.dataset.target + '%';
    }, delay + i * stagger);
  });
}

// ── Router ─────────────────────────────────────────────────────────────────

function route() {
  var hash = window.location.hash.slice(1) || '/';
  // Clear any stale prefill if not navigating to chat
  if (hash !== '/chat') _chatPrefill = null;
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
  } else if (hash === '/compare' || hash.indexOf('/compare/') === 0) {
    destroyHomeMap();
    var preselect = hash.indexOf('/compare/') === 0 ? hash.slice(9) : null;
    renderCompare(app, preselect);
  } else if (hash === '/license') {
    destroyHomeMap();
    renderLicense(app);
  } else if (hash === '/findings') {
    destroyHomeMap();
    renderFindings(app);
  } else if (hash === '/chat') {
    destroyHomeMap();
    renderChat(app);
  } else if (hash === '/brief') {
    destroyHomeMap();
    renderBrief(app);
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
  return cqTier(score).color;
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
// Leading ≥68.2 | Established 61.8–68.1 | Growing 54.7–61.7 | Emerging <54.7 (Jenks natural breaks)

var TIERS = [
  { num: 1, label: 'Leading',     min: 68.2, color: '#2d6a4f', textColor: '#fff',    desc: 'Score 68.2 or above' },
  { num: 2, label: 'Established', min: 61.8, color: '#74c490', textColor: '#1a3d28', desc: 'Score 61.8–68.1' },
  { num: 3, label: 'Growing',     min: 54.7, color: '#5aaccf', textColor: '#0c2d40', desc: 'Score 54.7–61.7' },
  { num: 4, label: 'Emerging',    min: 0,    color: '#1e5799', textColor: '#fff',    desc: 'Score below 54.7' },
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
      var p1w = (city.pillar1 * 0.40).toFixed(1);
      var p2w = (city.pillar2 * 0.35).toFixed(1);
      var p3w = (city.pillar3 * 0.25).toFixed(1);
      return [
        '<a class="ranking-row', overflowCls, '" href="#/city/', city.key, '"',
          ' role="link" tabindex="0"',
          ' aria-label="', city.name, ', Care Quotient ', fmt(city.cq), '">',
          '<span class="r-rank">', item.rank, '</span>',
          '<span class="r-name">', city.name, '</span>',
          '<span class="r-state">', city.state, '</span>',
          '<div class="r-bar">',
            '<div class="r-seg r-seg-p1" data-target="', p1w,
              '" data-tip="Social &amp; Relational Care: ', fmt(city.pillar1), '"></div>',
            '<div class="r-seg r-seg-p2" data-target="', p2w,
              '" data-tip="Institutional Care: ', fmt(city.pillar2), '"></div>',
            '<div class="r-seg r-seg-p3" data-target="', p3w,
              '" data-tip="Economic Access to Care: ', fmt(city.pillar3), '"></div>',
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
        'that measure a city\'s capacity to care.',
      '</p>',
      '<p class="hero-meta">V6 &middot; 69 cities &middot; August 2026</p>',
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
        'Scores are measured against absolute benchmarks. ',
        'Cities within 3 to 4 points should be read as rough peers. Small differences ',
        'may fall within data collection variance. Click any city for a full breakdown.',
      '</p>',
    '</section>',

    // ── Chat prompts ──────────────────────────────────────────────────────
    '<section class="section-wrap">',
      '<div class="chat-prompts">',
        '<span class="chat-prompts-label">Ask the Index (AI):</span>',
        '<a class="chat-prompt-pill" href="#/chat"',
          ' data-prefill="Why does Cincinnati rank above New York City?"',
          ' data-autosend="true">Why does Cincinnati rank above NYC?</a>',
        '<a class="chat-prompt-pill" href="#/chat"',
          ' data-prefill="What policies could improve a city\'s Economic Access to Care score?"',
          ' data-autosend="true">What policies improve Economic Access to Care?</a>',
        '<a class="chat-prompt-pill" href="#/chat"',
          ' data-prefill="Which cities lead on Social &amp; Relational Care?"',
          ' data-autosend="true">Which cities lead on Social &amp; Relational Care?</a>',
      '</div>',
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
            '<li>Do stable social networks exist for people to lean on?</li>',
            '<li>Are nonprofits and health centers present relative to population need?</li>',
            '<li>Are safety-net programs reaching the people they&rsquo;re designed for?</li>',
            '<li>Do the organizations, health centers, and systems to support people in difficulty exist at the scale the population needs?</li>',
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
    animateBars(rankingTable, '.r-seg', 80);
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
      if (expanded) {
        // Reset then animate overflow bars that just became visible
        var overflowSegs = rankingTable.querySelectorAll('.ranking-row-overflow .r-seg');
        overflowSegs.forEach(function(seg) { seg.style.width = '0'; });
        setTimeout(function() {
          animateBars(rankingTable, '.ranking-row-overflow .r-seg', 0);
        }, 30);
      }
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
      'Honolulu&rsquo;s high overall ranking should be read with this in mind: it reflects ',
      'genuine care infrastructure, but the county boundary makes direct comparisons imprecise. ',
      'See <a href="#/methodology">Methodology &rarr; Geographic Boundaries</a>.',
    ].join(''),
  },
  nyc: {
    type: 'info',
    text: [
      '<strong>Scale note:</strong> New York City has more nonprofits than almost any city in the country, ',
      'but the Care Quotient measures density per resident. With 8.3 million people, even a large absolute count ',
      'spreads thin on a per-capita basis. New York City&rsquo;s FQHC network is strong; the combined nonprofit score ',
      'reflects this scale effect, not an absence of care infrastructure.',
    ].join(''),
  },
  cleveland: {
    type: 'info',
    text: [
      '<strong>Rust Belt pattern:</strong> Cleveland retains dense care infrastructure relative to its current population. ',
      'Ohio expanded Medicaid, further strengthening the Economic Access pillar. ',
      'High care capacity and low prosperity are not contradictions; the CQ data shows the current pattern, ',
      'but institution-level histories would be needed to explain how that infrastructure developed.',
    ].join(''),
  },
  detroit: {
    type: 'info',
    text: [
      '<strong>Rust Belt pattern:</strong> Detroit retains dense care infrastructure relative to its current population. ',
      'Michigan expanded Medicaid. These cities demonstrate that care capacity and prosperity are genuinely separate dimensions. ',
      'The CQ reflects current conditions; understanding why requires deeper investigation.',
    ].join(''),
  },
  pittsburgh: {
    type: 'info',
    text: [
      '<strong>Rust Belt pattern:</strong> Pittsburgh retains dense care infrastructure relative to its current population. ',
      'Pennsylvania expanded Medicaid, and the city&rsquo;s nonprofit and FQHC density is high relative to its current population size.',
    ].join(''),
  },
  cincinnati: {
    type: 'info',
    text: [
      '<strong>Rust Belt pattern:</strong> Cincinnati retains dense care infrastructure relative to its current population, ',
      'including the highest institutional care score in the dataset. Ohio expanded Medicaid, contributing to strong ',
      'healthcare coverage. High care capacity in economically stressed cities is a recurring finding in this data.',
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
      'This contributes to lower healthcare coverage and SNAP participation rates across Texas cities. ',
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
      'Houston&rsquo;s healthcare coverage score is 66.7, reflecting this state policy gap directly. ',
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
      'Raleigh&rsquo;s SNAP score also reflects a smaller likely-eligible population, ',
      'which can make the SNAP estimate noisier.',
    ].join(''),
  },
  miami: {
    type: 'geo',
    text: [
      '<strong>Scope note:</strong> This score covers the City of Miami (~450k residents), ',
      'the incorporated municipality. Miami Beach, Hialeah, Coral Gables, and other cities ',
      'within Miami-Dade County are separate jurisdictions and are not included. ',
      'Two metrics (child care and religious organization density) use county-level source data (CBP and ARDA). ',
      'Because the City of Miami represents roughly 16% of Miami-Dade County&rsquo;s population, ',
      'those two scores are likely elevated relative to the city&rsquo;s actual capacity. ',
      'Florida has not expanded Medicaid, which contributes to a lower healthcare coverage score. ',
      'See <a href="#/methodology">Methodology &rarr; Geographic Boundaries</a>.',
    ].join(''),
  },
  washington_dc: {
    type: 'info',
    text: [
      '<strong>Scope note:</strong> DC leads the index on care nonprofit density (score: 78.1 out of 100) and healthcare coverage. ',
      'DC is structurally unusual: it hosts a significant concentration of nationally-focused organizations that file under ',
      'the same NTEE P, E, and F codes used to measure locally-serving care nonprofits. The NTEE filter excludes arts and ',
      'education, but cannot distinguish a neighborhood food bank from a national health policy organization headquartered downtown. ',
      'DC&rsquo;s underlying care infrastructure is genuine; its nonprofit density score likely reflects some national-organization ',
      'presence that other cities\' scores do not.',
    ].join(''),
  },
  atlanta: {
    type: 'info',
    text: [
      '<strong>Pillar divergence:</strong> Atlanta has the highest Social &amp; Relational Care score in the dataset (83.9), ',
      'driven by exceptionally dense care nonprofit infrastructure (score: 86.0 out of 100). ',
      'Institutional care is comparatively thin: Pillar 2 scores 45.1, and FQHC density is 32.1 for a city of 500k. ',
      'Atlanta illustrates that relational and institutional care capacity can diverge sharply within the same city.',
    ].join(''),
  },
  salt_lake_city: {
    type: 'info',
    text: [
      '<strong>SNAP coverage note:</strong> Salt Lake City has the lowest SNAP coverage rate in the dataset (34.9). ',
      'The metric estimates participation among likely-eligible households; a score of 34.9 suggests roughly 30% of ',
      'eligible households are enrolled. One plausible explanation is that informal mutual aid networks in Salt Lake City ',
      'partially substitute for formal SNAP participation in ways this index cannot measure. ',
      'See <a href="#/findings">Findings &sect;4</a> for context.',
    ].join(''),
  },
  madison: {
    type: 'info',
    text: [
      '<strong>Last in the dataset:</strong> Madison (46.6) is the lowest-scoring city in the index. ',
      'Healthcare coverage scores 57.1 because Wisconsin has not adopted ACA Medicaid expansion; ',
      'residents who would qualify in expansion states are counted in the denominator but cannot enroll. ',
      'SNAP scores 44.8. Madison&rsquo;s relatively affluent and student-heavy population may also reduce the ',
      'number of likely-eligible households, making the SNAP and coverage estimates less stable than in other cities. ',
      'These scores reflect state policy and demographic composition as much as local care infrastructure.',
    ].join(''),
  },
  anchorage: {
    type: 'info',
    text: [
      '<strong>Regional care hub:</strong> Anchorage has the lowest Institutional Care score in the dataset (14.1), ',
      'driven by thin nursing home capacity (14.9) and sparse FQHC density (9.1) relative to population. ',
      "Part of this reflects Anchorage's role as a regional hub serving a much larger surrounding area.",
      'Facilities here absorb patients from across rural Alaska, making per-capita density measures ',
      'structurally lower than comparably-sized cities elsewhere. ',
      'Healthcare coverage scores 100.0 because Alaska expanded Medicaid, which substantially lifts the overall score, ',
      'but the access infrastructure itself is thin relative to population.',
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
    label:  'Public Coverage Reach Proxy',
    pillar: 'pillar3',
    desc:   'ACS-based Medicaid/CHIP coverage rate among income-eligible residents (0–149% FPL)',
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
  health_insurance_coverage: 'Public Coverage Reach Proxy',
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
          'See <a href="#/methodology">Methodology &rarr; What this index does not measure</a>.',
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
          'most likely to need care-related services. A large gap between the two figures means ',
          'the city looks different under a need-adjusted denominator. It does not by itself prove ',
          'that nonprofits are geographically concentrated in lower-income areas. ',
          'See <a href="#/methodology">Methodology &rarr; Benchmarks</a>.',
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
        ' &nbsp;&middot;&nbsp; <a href="#/compare/', key, '" class="compare-inline-link">Compare with another city</a>',
      '</div>',
      '<div class="ask-city-wrap">',
        '<a class="ask-city-link" href="#/chat"',
          ' data-prefill="Tell me about ', city.name, '\'s care infrastructure — what\'s driving its score and what stands out?"',
          ' data-autosend="false">Ask the Index about ', city.name, ' →</a>',
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

function renderCompare(app, preselect) {
  var defaultA = (preselect && CITIES[preselect]) ? preselect : 'nyc';
  var defaultB = defaultA === 'chicago' ? 'nyc' : 'chicago';
  var backLink = (preselect && CITIES[preselect])
    ? '<a href="#/city/' + preselect + '" class="back-link">&#8592; Back to ' + CITIES[preselect].name + '</a>'
    : '<a href="#/" class="back-link">&#8592; Home</a>';

  app.innerHTML = [
    '<div class="compare-page">',

      backLink,

      '<div class="compare-header">',
        '<div class="compare-eyebrow">Compare</div>',
        '<h1 class="compare-title">City-by-City Comparison</h1>',
        '<p class="compare-intro">',
          'Select two cities to compare their Care Quotient scores and underlying metrics. ',
          'Scores are on the same absolute scale. Cities within 3&ndash;4 points of each other ',
          'should be treated as rough peers. Differences that small may fall within the margin ',
          'of geographic approximation or data variance.',
        '</p>',
      '</div>',

      '<div class="compare-controls">',
        '<div class="compare-picker">',
          '<label class="compare-picker-label" for="compare-a">City A</label>',
          '<select id="compare-a" class="compare-select">',
            buildCityOptions(defaultA),
          '</select>',
        '</div>',
        '<div class="compare-vs">vs</div>',
        '<div class="compare-picker">',
          '<label class="compare-picker-label" for="compare-b">City B</label>',
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

      '<a href="#/" class="back-link">&#8592; Home</a>',

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
        'The question is whether a city can <em>show up</em>.',
      '</p>',

      '<h2>Three Pillars</h2>',

      '<p>',
        'The CQ is a weighted composite of ten scored metrics organized into three pillars. ',
        'Pillar weights prioritize the relational layer (care ethics tradition) over the institutional ',
        'and access dimensions, representing a normative commitment as opposed to an empirical finding. ',
        'Within-pillar weights reflect both factor analysis and theoretical commitments. Inter-pillar weights (40/35/25) are explicitly theory-first, not empirically derived.',
      '</p>',

      '<table class="method-table">',
        '<thead><tr>',
          '<th>Pillar</th><th>What it measures</th><th>Weight</th>',
        '</tr></thead>',
        '<tbody>',
          '<tr>',
            '<td><span class="ptag ptag-p1">Social &amp; Relational Care</span></td>',
            '<td>Residential stability, care nonprofit density, library density, and religious organization density: the conditions under which people notice and respond to need.</td>',
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
          '<tr><td>Healthcare Coverage (Medicaid/CHIP)</td><td>Survey-reported coverage rate among 0–149% FPL residents (benchmark: 100%). <em>Note: 31 of 69 cities (45%) score exactly 100 due to CHIP enrollment exceeding the FPL denominator — the metric is near-binary in expansion states.</em></td><td>Census ACS C27007</td></tr>',
          '<tr><td>Housing Affordability</td>       <td>90% not cost-burdened</td>                        <td>Census ACS B25070, B25091</td></tr>',
          '<tr><td>SNAP Coverage Rate</td>          <td>85% of likely-eligible</td>                       <td>Census ACS B22001, C17002</td></tr>',
        '</tbody>',
      '</table>',

      '<h2>Geographic Boundaries</h2>',

      '<p>',
        'Most data sources use the Census 2020 ZCTA-to-Place relationship file to define city ',
        'boundaries consistently. A ZIP Code Tabulation Area is assigned to a city if &#8805;40% ',
        'of its land area falls within the city&rsquo;s Census incorporated place boundary. ',
        'This threshold captures near-boundary ZCTAs that genuinely serve city residents ',
        'while excluding ZCTAs that are primarily suburban.',
      '</p>',

      '<p>',
        '<strong>County-level exception:</strong> Two metrics use county-level data for both ',
        'numerator and denominator, because their source datasets (Census CBP and ARDA) do not ',
        'report below the county level. Child care capacity uses county CBP establishments and ',
        'county ACS under-5 population. Religious organization density uses county ARDA ',
        'congregation counts and county ARDA 2020 population. For both metrics, the score ',
        'reflects county-wide density rather than city-specific density.',
      '</p>',

      '<p>',
        '<strong>Honolulu exception:</strong> Hawaii has no incorporated municipalities. ',
        'Honolulu is a Census Designated Place absent from the ZCTA-to-Place crosswalk. The ',
        'pipeline falls back to Honolulu County boundaries, which are broader than the urban core. ',
        'Density metrics for Honolulu may be modestly overstated as a result.',
      '</p>',

      '<h2>Tier System</h2>',

      '<p>',
        'Cities are grouped into four tiers based on their CQ score. The tier boundaries are derived from ',
        'Jenks natural breaks applied to the 69-city distribution. The Jenks algorithm ',
        'partitions data into classes by minimizing within-class variance, finding the breakpoints ',
        'where the distribution thins most naturally.',
      '</p>',

      '<table class="method-table">',
        '<thead><tr><th>Tier</th><th>Threshold</th><th>Cities (V6)</th></tr></thead>',
        '<tbody>',
          '<tr><td style="text-align:left"><span style="display:inline-block;background:#2d6a4f;color:#fff;padding:2px 10px;border-radius:4px;white-space:nowrap">Leading</span></td>    <td>&#8805; 68.2</td><td>13</td></tr>',
          '<tr><td style="text-align:left"><span style="display:inline-block;background:#74c490;color:#1a3d28;padding:2px 10px;border-radius:4px;white-space:nowrap">Established</span></td><td>61.8 &ndash; 68.1</td><td>20</td></tr>',
          '<tr><td style="text-align:left"><span style="display:inline-block;background:#5aaccf;color:#0c2d40;padding:2px 10px;border-radius:4px;white-space:nowrap">Growing</span></td>    <td>54.7 &ndash; 61.7</td><td>14</td></tr>',
          '<tr><td style="text-align:left"><span style="display:inline-block;background:#1e5799;color:#fff;padding:2px 10px;border-radius:4px;white-space:nowrap">Emerging</span></td>    <td>&lt; 54.7</td><td>22</td></tr>',
        '</tbody>',
      '</table>',

      '<p>',
        '<strong>Cities near a tier boundary should be treated as peers</strong>, not as categorically different. Tier thresholds ',
        'will shift when cities are added or removed from the index, since Jenks is a relative ',
        'algorithm applied to the current distribution.',
      '</p>',

      '<h2>How to read the scores</h2>',

      '<p>',
        'The CQ is designed to be read as a measure against a benchmark, not as a competition. ',
        'Cities within 3 to 4 points should be treated as rough peers. Differences of that ',
        'size may fall within the margin of geographic approximation or a single year&rsquo;s data variance. ',
        'The index is most useful for identifying cities at the extremes, understanding which ',
        '<em>specific</em> metrics drive a city&rsquo;s score, and tracking change over time.',
      '</p>',

      '<h2>What this index measures, precisely</h2>',

      '<p>',
        'The Care Quotient measures whether a city has the social ties, institutions, and access conditions ',
        'that enable care to reach people.',
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
        'August 2026. 69 cities. ',
        'Data sources: IRS EO BMF &middot; Census ACS 2022 5-year estimates &middot; Census CBP 2022 &middot; ',
        'HRSA Health Center Service Delivery &middot; IMLS Public Libraries Survey FY2023 &middot; ',
        'CMS Care Compare Nursing Home Provider Information &middot; ARDA 2020 Religion Census &middot; CDC PLACES (2022/2023).',
      '</p>',

    '</div>',
    renderFooter(),
  ].join('');
}

// ── Theory page ─────────────────────────────────────────────────────────────

function renderTheory(app) {
  app.innerHTML = [
    '<div class="method-page">',

      '<a href="#/" class="back-link">&#8592; Home</a>',

      '<div class="method-eyebrow">Theoretical Foundation</div>',
      '<h1>What is Care?</h1>',

      '<p>',
        'Care is the set of practices and relationships through which people maintain, continue, and ',
        'repair the world so that they can live in it as well as possible. That definition, from ',
        'Joan Tronto, gives this project its basic orientation. Our question is whether the infrastructure ',
        'exists to enable that kind of care.',
      '</p>',

      '<h2>Why care about care?</h2>',

      '<p>Two reasons.</p>',

      '<p>',
        'First, care enables us to work together. Trust and social capital make cooperation ',
        'broader, steadier, and easier to sustain over time. The OECD treats trust as a key ingredient ',
        'of growth, social cohesion, well-being, and governance, and the National Academies describes ',
        'social capital and connectedness as community assets that help communities function and recover ',
        'from shocks. In their 1997 Chicago study, Robert Sampson, Stephen Raudenbush, and Felton Earls ',
        'found that neighborhoods with stronger collective efficacy (social cohesion combined with ',
        'a willingness to act for the common good) experienced lower violence, and that some of ',
        'the harms associated with concentrated disadvantage and residential instability ran through weaker ',
        'collective efficacy. The larger lesson is that care helps societies coordinate. It makes it easier ',
        'to build institutions, carry public burdens, and keep working together when life gets difficult.',
      '</p>',

      '<p>',
        'Second, caring is good for us. There is evidence that prosocial ',
        'behavior is associated with higher well-being, and in some cases seems to improve it directly. ',
        'Lara Aknin and her coauthors, using survey data from 136 countries, found that spending money on ',
        'others was consistently associated with greater happiness, and experiments in both Canada and ',
        'Uganda suggested that the effect was causal. That fits something many people already know from ',
        'experience: responsibility for other people can be heavy, but it can also create meaning, ',
        'connection, and a healthier sense of self.',
      '</p>',

      '<h2>Care starts with relationships</h2>',

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
        'organizations, and access conditions that enable care to reach people. The point is to make ',
        'care visible and something we can improve on.',
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
            '<td>Putnam (2000): religious participation as a consistent predictor of social capital; congregations generate bridging and bonding ties that underpin informal mutual aid. Chaves &amp; Tsitsos (2001): most US congregations provide at least one social service through informal networks. Scored via ARDA 2020 Religion Census; distinct from IRS-coded faith-based nonprofits.</td>',
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
        '<li>Agha, G., et al. (2024). Housing stability and social capital: Mediation pathways. <em>American Journal of Community Psychology</em>.</li>',
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
        '<li>Rosenbaum, S., et al. (2011). <em>Health Centers: An American Success Story</em>. George Washington University School of Public Health.</li>',
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

// Pre-fill a question when navigating to chat from a prompt pill or city link.
// Set before hash change; renderChat reads and clears it.
var _chatPrefill = null;

document.addEventListener('click', function(e) {
  var el = e.target.closest('[data-prefill]');
  if (!el) return;
  _chatPrefill = {
    text:     el.dataset.prefill,
    autoSend: el.dataset.autosend !== 'false',
  };
});

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

function renderLicense(app) {
  app.innerHTML = [
    '<div class="method-page">',
      '<a href="#/" class="back-link">&#8592; Home</a>',
      '<div class="method-eyebrow">License</div>',
      '<h1>Creative Commons Attribution 4.0</h1>',
      '<p>',
        'The Care Quotient index, methodology, scoring, and compiled dataset are released under ',
        '<a href="https://creativecommons.org/licenses/by/4.0/" target="_blank" rel="noopener">CC BY 4.0</a>. ',
        'You are free to share, adapt, and use the material for any purpose, including commercially, ',
        'provided you give appropriate credit.',
      '</p>',
      '<p>',
        'Suggested citation: <em>Care Quotient</em> (2026). Measuring Care Capacity Across American Cities, V6. care-quotient.vercel.app',
      '</p>',
      '<p>',
        'The underlying government data sources (Census ACS, IRS EO BMF, HRSA, IMLS, CMS, ARDA, CDC PLACES, Census CBP) ',
        'are public domain and are not subject to this license.',
      '</p>',
    '</div>',
    renderFooter(),
  ].join('');
}

function renderFindings(app) {
  app.innerHTML = [
    '<div class="method-page findings-page">',

      '<a href="#/" class="back-link">&#8592; Home</a>',

      '<div class="method-eyebrow">Findings</div>',
      '<h1>What the data shows</h1>',

      '<p>',
        'A consistent theme is that care capacity is not the same as prosperity, population growth, ',
        'prestige, or general quality of life. Wealthy cities can have thin care infrastructure. Growing cities ',
        'can fail to scale it. Older industrial cities can retain institutions and stable social conditions that ',
        'make care more possible.',
      '</p>',

      '<p>',
        'One note on how to read these findings: the Care Quotient (CQ) does not measure compassion, altruism, ',
        'civic virtue, or how much residents emotionally care about one another. It measures care capacity, the ',
        'visible conditions through which care can be organized and delivered. A high score may be consistent with a ',
        'caring civic culture, but it can also come from state policy, historical infrastructure, population decline, ',
        'or denominator effects. A low score does not mean people care less.',
      '</p>',

      '<hr>',

      '<h2>1. The leading tier offers some surprises</h2>',

      '<p>',
        'Washington, DC (75.1) leads the index, followed by Cincinnati (74.4), Honolulu (73.0), Cleveland (73.0), ',
        'and Rochester (72.1). New Orleans, Baton Rouge, and Detroit follow. The full Leading tier extends to 13 cities, ',
        'down to Pittsburgh (68.2).',
      '</p>',

      '<p>',
        'The tier is geographically diverse: DC (federal hub), Honolulu (Pacific), two Gulf South cities (New Orleans, Baton Rouge), ',
        'five Rust Belt cities (Cincinnati, Cleveland, Rochester, Detroit, Pittsburgh), plus Baltimore, Indianapolis, ',
        'Providence, and St. Louis. They are united by a legacy of dense public and nonprofit infrastructure ',
        'built for larger or different populations. The fastest-growing Sun Belt cities are largely absent from the leading tier.',
      '</p>',

      '<p>',
        'One note on Washington, DC specifically. DC\'s care nonprofit density score (78.1 out of 100) is among the highest in the ',
        'dataset, DC also scores solidly on housing affordability (71.0) and healthcare coverage (100.0), so its #1 ranking is not driven by nonprofit density alone. However, DC is structurally unusual in that it hosts ',
        'a significant concentration of nationally-focused organizations (e.g. federal advocacy groups, health policy bodies, ',
        'public interest law firms) that file under the same NTEE P, E, and F codes used to measure locally-serving care ',
        'nonprofits. The NTEE filter excludes arts and education, but it cannot distinguish a neighborhood food bank ',
        'from a national health policy organization headquartered in Dupont Circle. DC\'s care infrastructure is genuine; ',
        'its nonprofit density score likely reflects some share of national-organization presence that other cities\' scores do not.',
      '</p>',

      '<p>',
        "Cincinnati's Pillar 2 score is 79.8, among the highest institutional care scores in the dataset. ",
        'Nursing homes at 100, FQHCs at 81.9. ',
        'One plausible explanation is that some of this reflects legacy infrastructure built for a larger ',
        'historical population: as population shrank, the denominator got smaller while institutions largely stayed. ',
        'To verify that hypothesis, however, we need institution-level histories (when facilities opened, when ',
        'capacity changed, what the trend lines look like, etc). This index reflects the current state of care; ',
        'deeper investigation would be needed to understand how that infrastructure developed.',
      '</p>',

      '<p>',
        'Residential stability is also extremely high, with Detroit at 93.0 and Cleveland at 86.6. ',
        'People stay. Informal care benefits from the social ties that arise when people stay put. ',
        'And Ohio, Michigan, Pennsylvania, and New York all expanded Medicaid.',
      '</p>',

      '<p>',
        'The inverse is also visible. Fast-growing cities, like Austin (51.5), Raleigh (52.0), ',
        'Charlotte (53.8), and Nashville (53.5), are in the bottom third. In this dataset, cities with ',
        'rapid recent growth tend to show thinner per-capita care infrastructure, though causation here is complex.',
      '</p>',

      '<hr>',

      '<h2>2. You can see the Medicaid map in the data</h2>',

      '<p>',
        "Texas didn't expand Medicaid. That decision is visible in every Texas city score:",
      '</p>',

      '<table class="findings-table">',
        '<thead><tr><th>City</th><th>CQ</th><th>Healthcare coverage score</th></tr></thead>',
        '<tbody>',
          '<tr><td>Houston</td><td>50.8</td><td>66.7</td></tr>',
          '<tr><td>Dallas</td><td>51.5</td><td>66.8</td></tr>',
          '<tr><td>Fort Worth</td><td>53.2</td><td>70.5</td></tr>',
          '<tr><td>San Antonio</td><td>52.9</td><td>71.8</td></tr>',
          '<tr><td>Austin</td><td>51.5</td><td>60.2</td></tr>',
          '<tr><td>El Paso</td><td>51.0</td><td>68.1</td></tr>',
        '</tbody>',
      '</table>',

      '<p>',
        'Compare to cities in expansion states with similar demographics: Albuquerque (55.9, coverage 100), ',
        'Fresno (60.2, coverage 100), Stockton (64.8, coverage 100).',
      '</p>',

      '<p>',
        "The starkest number may be Fort Worth's FQHC score: <strong>1.5 out of 100.</strong> ",
        'One of the largest cities in the country has almost no federally-qualified health center capacity per capita. ',
        'The FQHC system is designed to serve the population that lacks Medicaid. ',
        'Texas non-expansion may weaken the financing environment for safety-net primary care, ',
        'but this index cannot establish that causal channel on its own.',
      '</p>',

      '<p>',
        'One caveat on the healthcare coverage metric itself — 31 of 69 cities (45%) score exactly 100.0. ',
        'This is based on the denominator, which is set at the eligibility ceiling. The numerator counts all ',
        'Medicaid and CHIP enrollees, including children covered by CHIP whose household income may be above ',
        'the 150% FPL eligibility ceiling used in the denominator. In high-expansion states with strong CHIP ',
        'enrollment, the numerator can exceed the denominator, producing a raw rate above 100% that is capped at 100. ',
        'The practical effect: in expansion states, healthcare coverage functions as a near-binary indicator rather ',
        'than a continuous measure. Two cities in the same expansion state, both scoring 100.0, may have meaningfully ',
        'different actual enrollment rates; the metric cannot distinguish them. Cities in non-expansion states, where ',
        'the gap between enrolled and eligible is real, are where this metric carries the clearest signal.',
      '</p>',

      '<hr>',

      '<h2>3. Wealth and care capacity diverge</h2>',

      '<p>',
        'The cities gaining population and wealth are largely absent from the top half of this index. ',
        'In this dataset, cities with the strongest care infrastructure tend to be those experiencing long-term population decline, while fast-growing cities tend to score lower.',
      '</p>',

      '<ul class="findings-list">',
        '<li>Austin: <strong>51.5.</strong> Stockton: 64.8. Austin is one of the fastest-growing and most prosperous cities in the country. Stockton is among the poorest large cities in California. Stockton leads by 13 points.</li>',
        '<li>San Francisco: <strong>64.0.</strong> Same tier (Established) as Omaha (63.1). Los Angeles (60.0) is one tier lower in Growing.</li>',
        '<li>New York City: <strong>61.8.</strong> Established, the lowest score in the Established tier. One tier above Fresno (60.2).</li>',
        '<li>Seattle: <strong>62.1.</strong> Milwaukee: 64.0. Milwaukee edges ahead.</li>',
        '<li>Boston: <strong>67.2.</strong> Below Baton Rouge (71.4) and Detroit (70.5).</li>',
      '</ul>',

      '<p>',
        "San Francisco's housing cost burden score is 73.8, meaning 73.8% of households are not cost-burdened, but the inverse (26.2% are burdened) is still among the higher burden rates in the dataset. ",
        'Its religious organization density score is 40.9, among the lowest in the dataset. ',
        'New York City has more FQHCs by absolute count than any city on the list; its per-capita FQHC score is 35.2 ',
        'because the denominator is 8.3 million people.',
      '</p>',

      '<hr>',

      '<h2>4. Program participation gaps</h2>',

      '<p>',
        '<strong>Salt Lake City Supplemental Nutrition Assistance Program (SNAP) score: 34.9.</strong> ',
        'This is the lowest food security program reach in the dataset. ',
        'Because the SNAP benchmark is 85%, a score of 34.9 corresponds to estimated raw SNAP reach of ',
        'roughly 30% of likely-eligible households. The SNAP metric is directional, not a precise participation ',
        'rate; the eligibility denominator is estimated from ACS income data. One plausible explanation for ',
        'low take-up is that informal community and religious mutual aid networks partially substitute for formal SNAP enrollment in ways this index cannot measure. ',
        'This is a real limit of what the index can see.',
      '</p>',

      '<p>',
        'Madison (46.6) is a related case. Madison healthcare coverage scores 57.1 and SNAP scores 44.8. But Wisconsin ',
        'has not adopted ACA Medicaid expansion, so Madison should not be treated as an expansion-state ',
        'counterexample. The more cautious interpretation is that Madison combines a relatively affluent local ',
        'profile with surprisingly low formal safety-net reach in the CQ data. That could reflect state Medicaid ',
        'policy, denominator issues in estimating eligibility, student-population effects, lower formal program ',
        'participation, or some combination of the above.',
      '</p>',

      '<p>',
        'These are situations where the CQ should be read as a diagnostic prompt as opposed to a final verdict.',
      '</p>',

      '<hr>',

      '<h2>5. What the index cannot see</h2>',

      '<p>',
        'The Care Quotient measures care capacity as it appears in public administrative data: ',
        'federal registries, government surveys, and licensed facility records. It cannot measure ',
        'LDS ward welfare systems, immigrant mutual aid networks in Los Angeles and Houston, extended family ',
        'care systems, or informal support that substitutes for enrollment. Cities where such informal care ',
        'is strong and formal program participation is low will score lower than their actual care capacity.',
      '</p>',

      '<hr>',

      '<h2>6. The large-city per-capita penalty</h2>',

      '<p>',
        'NYC has more federally qualified health centers by absolute count than any other city in the dataset. ',
        'Its per-capita FQHC score is 35.2, because the denominator is 8.3 million people. ',
        'Los Angeles (60.0), Chicago (66.3), and Philadelphia (64.5) face the same structural pattern featuring ',
        'large absolute care infrastructure with average-to-below-average per-capita ratios on most density metrics.',
      '</p>',

      '<p>',
        'This index uses total population as the denominator for all density metrics. That is a clear measure of ',
        'supply relative to population but it may understate access in dense, ',
        'transit-connected cities where a resident can reach multiple facilities they nominally &ldquo;share&rdquo; with many others. ',
        'Whether per-capita density or geographic accessibility is the right framing is an open methodological question. ',
        'For cities above roughly 1 million residents, CQ density scores capture supply per resident.',
      '</p>',

    '</div>',
    renderFooter(),
  ].join('');
}

function renderChat(app) {
  var cities = getCitiesSorted();
  var topCity = cities[0];
  var bottomCity = cities[cities.length - 1];

  var suggestions = [
    'Why does ' + topCity.name + ' rank #1?',
    'Which city has the weakest care infrastructure overall?',
    'What\'s the difference between care capacity and quality of life?',
    'What policies could ' + bottomCity.name + ' implement to improve its score?',
  ];

  var willAutoSend = _chatPrefill && _chatPrefill.autoSend;
  var suggestionsHtml = (_chatState.messages.length === 0 && !willAutoSend) ? [
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
      '<a href="#/" class="back-link">&#8592; Home</a>',

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
          '<label for="chat-input" class="sr-only">Ask about any city or topic</label>',
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

  // Handle pre-filled question from prompt pills or city page links
  if (_chatPrefill) {
    var prefill = _chatPrefill;
    _chatPrefill = null;
    if (prefill.autoSend) {
      setTimeout(function() { sendChatMessage(prefill.text); }, 150);
    } else {
      input.value = prefill.text;
      input.dispatchEvent(new Event('input'));
      input.focus();
      input.setSelectionRange(input.value.length, input.value.length);
    }
  }
}

// ── Footer ──────────────────────────────────────────────────────────────────

function renderBrief(app) {
  app.innerHTML = [
    '<div class="method-page">',

      '<a href="#/" class="back-link">&#8592; Home</a>',
      '<div class="method-eyebrow">Reporter Brief</div>',
      '<h1>Care Quotient — Press Overview</h1>',

      '<h2>What it is</h2>',
      '<p>',
        'The Care Quotient (CQ) is a composite index measuring <strong>care capacity</strong> across 69 American cities. ',
        'Care capacity is the presence or absence of the social ties, institutions, and safety-net conditions that determine ',
        'whether people get help when they need it. It is explicitly <em>not</em> a quality-of-life index. ',
        'A city can be prosperous, safe, and growing while scoring poorly on care.',
      '</p>',
      '<p>',
        'The index covers 10 scored metrics across three pillars: Social &amp; Relational Care (40%), ',
        'Institutional Care (35%), and Economic Access to Care (25%). Each metric is scored against an absolute benchmark. ',
        'Source data: IRS EO BMF, Census ACS 2022, Census CBP, HRSA, IMLS, CMS Care Compare, ARDA 2020, CDC PLACES.',
      '</p>',

      '<hr>',

      '<h2>Five key findings</h2>',

      '<p><strong>1. Wealth and care capacity diverge sharply.</strong><br>',
        'Stockton, CA, one of California\'s less affluent cities, outscores Austin, TX by 13 points (64.8 vs. 51.5). ',
        'San Francisco and Omaha land in the same tier. Boston (67.2) scores below Baton Rouge (71.4) and Detroit (70.5).',
      '</p>',

      '<p>',
        '<strong>Why?</strong> First, care infrastructure requires time to develop. Nonprofits, health centers, and libraries are built institutions that accumulate over decades. Fast-growing cities are adding capacity, but population growth outpaces institutional growth. In cities like Detroit (93&percnt; residential stability) and Cleveland (87&percnt;), residents have remained in place long enough for dense organizational ecosystems to develop.',
      '</p>',

      '<p>',
        'Second, the index measures public and nonprofit provision because that is what determines whether cities can show up for all of its residents. When Austin, one of the country&rsquo;s fastest-growing and most prosperous cities, scores 51.5 while Stockton scores 64.8, the gap reflects that Stockton has built and maintained the public infrastructure that Austin has not. Prosperity and care capacity are empirically separate because wealth does not necessarily create public responsibility.',
      '</p>',

      '<p><strong>2. A state\'s Medicaid decision is visible in every city within it.</strong><br>',
        'Texas did not expand Medicaid. That decision shows up directly: Houston scores 50.8, Dallas 51.5, Austin 51.5, El Paso 51.0. ',
        'Fort Worth scores 1.5 out of 100 on federally qualified health center density — one of the largest cities in the country, ',
        'with almost no safety-net primary care per capita. Compare to Albuquerque (55.9) and Fresno (60.2), ',
        'both in Medicaid expansion states with similar demographics.',
      '</p>',

      '<p><strong>3. Fast-growing cities are not building care infrastructure fast enough.</strong><br>',
        'Austin, Raleigh (52.0), Charlotte (53.8), and Nashville (53.5) are all in the bottom third. ',
        'The nonprofits, clinics, and social networks that make care possible accumulate over decades. ',
        'Rapid population growth dilutes per-capita care infrastructure faster than cities can build it.',
      '</p>',

      '<p><strong>4. Older industrial cities retain infrastructure built for larger populations.</strong><br>',
        'Washington DC (75.1), Cincinnati (74.4), Cleveland (73.0), and Detroit (70.5) lead the index. ',
        'These cities demonstrate that high care capacity and low economic prosperity are not contradictions. ',
        'Institutions and stable neighborhoods persist even as populations shrink.',
      '</p>',

      '<p><strong>5. The healthcare coverage metric exposes the Medicaid map directly.</strong><br>',
        '31 of 69 cities (45%) score exactly 100 on healthcare coverage because they are in Medicaid expansion states. ',
        'The metric functions as near-binary: the meaningful variation is between expansion and non-expansion states, ',
        'not within them. Non-expansion state cities carry a structural care access deficit that no local policy can fully offset.',
      '</p>',

      '<hr>',

      '<h2>Five caveats</h2>',

      '<ol class="findings-list">',
        '<li><strong>Per-capita density penalizes large, dense cities.</strong> NYC has more federally qualified health centers than any city in the dataset in absolute terms; its per-capita score is 35.2 because the denominator is 8.3 million people. The index measures supply per resident, not geographic accessibility.</li>',
        '<li><strong>Informal care is invisible.</strong> LDS mutual aid networks in Salt Lake City, immigrant family care networks in LA and Houston, and faith-based informal provision are not captured by federal registries. Cities where informal care substitutes for formal enrollment will score lower than their actual care capacity.</li>',
        '<li><strong>Two metrics use county-level data.</strong> Child care capacity (Census CBP) and religious organization density (ARDA) are only available at the county level. For cities that represent a small share of their county, like Miami at roughly 16% of Miami-Dade, those scores reflect county-wide density, not the city itself.</li>',
        '<li><strong>DC\'s nonprofit score includes nationally-focused organizations.</strong> NTEE codes cannot distinguish a neighborhood food bank from a national health policy organization headquartered downtown. DC\'s #1 ranking reflects genuine local care infrastructure plus some share of national-organization presence that other cities\' scores do not include.</li>',
        '<li><strong>Healthcare coverage is near-binary in expansion states.</strong> 31/69 cities score exactly 100. Two cities in the same expansion state, both at 100, may have meaningfully different actual enrollment rates — the metric cannot distinguish them at the ceiling.</li>',
      '</ol>',

      '<hr>',

      '<h2>Data &amp; reproducibility</h2>',
      '<table class="method-table">',
        '<tbody>',
          '<tr><td>Scores (CSV)</td><td><a href="/care_capacity_scores.csv">care-quotient.vercel.app/care_capacity_scores.csv</a></td></tr>',
          '<tr><td>Full data — raw values, benchmarks, sources, vintages (CSV)</td><td><a href="/care_capacity_data.csv">care-quotient.vercel.app/care_capacity_data.csv</a></td></tr>',
          '<tr><td>Methodology</td><td><a href="#/methodology">care-quotient.vercel.app/#/methodology</a></td></tr>',
          '<tr><td>Source code</td><td><a href="https://github.com/petedur/Care-Quotient---Claude-Code" target="_blank" rel="noopener">github.com/petedur/Care-Quotient---Claude-Code</a></td></tr>',
          '<tr><td>License</td><td><a href="#/license">CC BY 4.0</a> — free to use, adapt, and publish with attribution</td></tr>',
        '</tbody>',
      '</table>',
      '<p><strong>Cite as:</strong> <em>Care Quotient</em> (2026). Measuring Care Capacity Across American Cities, V6. care-quotient.vercel.app</p>',

    '</div>',
    renderFooter(),
  ].join('');
}

function renderFooter() {
  return [
    '<footer class="site-footer">',
      '<div class="footer-copy">',
        'Care Quotient &nbsp;&middot;&nbsp; 69 American Cities &nbsp;&middot;&nbsp; August 2026<br>',
        'Data: IRS EO BMF &middot; Census ACS 2022 &middot; Census CBP &middot; HRSA &middot; IMLS &middot; CMS Care Compare &middot; ARDA 2020 &middot; CDC PLACES<br>',
        'Cite: <em>Care Quotient</em> (2026). Measuring Care Capacity Across American Cities, V6. care-quotient.vercel.app<br>',
        '<a href="#/brief" class="footer-link">Reporter brief</a>',
        ' &nbsp;&middot;&nbsp; ',
        '<a href="/care_capacity_scores.csv" class="footer-link">Download scores (CSV)</a>',
        ' &nbsp;&middot;&nbsp; ',
        '<a href="/care_capacity_data.csv" class="footer-link">Download full data with raw values (CSV)</a>',
        ' &nbsp;&middot;&nbsp; ',
        '<a href="#/license" class="footer-link">CC BY 4.0</a>',
      '</div>',
    '</footer>',
  ].join('');
}
