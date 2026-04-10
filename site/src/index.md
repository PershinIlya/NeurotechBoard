---
title: NeurotechBoard
toc: false
---

<style>
  .hero {
    padding: 2rem 0 1rem 0;
    border-bottom: 1px solid var(--theme-foreground-faintest);
    margin-bottom: 1rem;
  }
  .hero h1 {
    font-size: clamp(2rem, 5vw, 3.5rem);
    margin: 0;
    line-height: 1.1;
    background: linear-gradient(135deg, #4f46e5 0%, #06b6d4 50%, #10b981 100%);
    -webkit-background-clip: text;
    background-clip: text;
    -webkit-text-fill-color: transparent;
  }
  .hero p.tagline {
    font-size: 1.15rem;
    color: var(--theme-foreground-muted);
    max-width: 60ch;
    margin: 0.5rem 0 0 0;
  }
  .stat-card {
    padding: 1rem 1.25rem;
    border: 1px solid var(--theme-foreground-faintest);
    border-radius: 8px;
    background: var(--theme-background-alt);
  }
  .stat-card .label {
    font-size: 0.8rem;
    text-transform: uppercase;
    letter-spacing: 0.05em;
    color: var(--theme-foreground-muted);
    margin: 0;
  }
  .stat-card .value {
    font-size: 2rem;
    font-weight: 700;
    margin: 0.25rem 0 0 0;
    color: var(--theme-foreground);
    font-variant-numeric: tabular-nums;
  }
  .stat-card .sub {
    font-size: 0.8rem;
    color: var(--theme-foreground-muted);
    margin: 0.1rem 0 0 0;
  }
  .section-label {
    font-size: 0.75rem;
    text-transform: uppercase;
    letter-spacing: 0.08em;
    color: var(--theme-foreground-muted);
    margin: 2.5rem 0 0.25rem 0;
  }
  h2 {
    margin-top: 0.25rem;
    font-size: 1.5rem;
  }
  .caption {
    color: var(--theme-foreground-muted);
    font-size: 0.9rem;
    max-width: 70ch;
    margin: 0.25rem 0 1rem 0;
  }
  .about-block {
    margin-top: 3rem;
    padding-top: 1.5rem;
    border-top: 1px solid var(--theme-foreground-faintest);
    color: var(--theme-foreground-muted);
    font-size: 0.9rem;
    max-width: 75ch;
  }
  .about-block a { color: var(--theme-foreground); }
</style>

<div class="hero">
  <h1>NeurotechBoard</h1>
  <p class="tagline">
    An open, interactive landscape of the global neurotech industry.
    Tracking company formations, geographies, modalities, and lifecycles —
    with honest confidence tiers and linked sources.
  </p>
</div>

```js
const companies = await FileAttachment("data/companies.csv").csv({typed: true});
```

```js
// ---- Pre-computed summary stats ----
const nCompanies = companies.length;
const nCountries = new Set(companies.map(d => d.country).filter(Boolean)).size;
const nWithYear = companies.filter(d => d.founding_year).length;
const yearCoverage = (nWithYear / nCompanies * 100).toFixed(1);
const years = companies.map(d => d.founding_year).filter(d => d);
const yearMin = d3.min(years);
const yearMax = d3.max(years);
const yearSpan = `${yearMin}–${yearMax}`;
const lifecycleCounts = d3.rollup(
  companies,
  v => v.length,
  d => d.lifecycle_status || "unknown"
);
const nActive = lifecycleCounts.get("active") || 0;
const nDead = lifecycleCounts.get("dead_domain") || 0;
```

<div class="grid grid-cols-4" style="margin-top: 0.5rem;">
  <div class="stat-card">
    <p class="label">Companies tracked</p>
    <p class="value">${nCompanies}</p>
    <p class="sub">from reccy.dev, dedup applied</p>
  </div>
  <div class="stat-card">
    <p class="label">Countries</p>
    <p class="value">${nCountries}</p>
    <p class="sub">across 6 regions</p>
  </div>
  <div class="stat-card">
    <p class="label">Founding years span</p>
    <p class="value">${yearSpan}</p>
    <p class="sub">${yearCoverage}% coverage (${nWithYear}/${nCompanies})</p>
  </div>
  <div class="stat-card">
    <p class="label">Live sites</p>
    <p class="value">${nActive}</p>
    <p class="sub">${nDead} dead domains detected</p>
  </div>
</div>

```js
// ---- Shared chart constants (regions, categories, applications) ----
const regionOrder = ["North America", "Europe", "Asia", "MENA", "Oceania", "LATAM", "Other"];
const regionColors = {
  "North America": "#4f46e5",
  "Europe":        "#06b6d4",
  "Asia":          "#10b981",
  "MENA":          "#f59e0b",
  "Oceania":       "#ec4899",
  "LATAM":         "#8b5cf6",
  "Other":         "#94a3b8",
  "":              "#cbd5e1"
};

const modalityOrder = [
  "Wearable",
  "Medical Device",
  "Therapeutics",
  "Diagnostics",
  "Software/AI",
  "Research Tools",
  "Hardware",
  "Other"
];
const modalityColors = {
  "Wearable":       "#2563eb",
  "Medical Device": "#0891b2",
  "Therapeutics":   "#7c3aed",
  "Diagnostics":    "#ea580c",
  "Software/AI":    "#059669",
  "Research Tools": "#10b981",
  "Hardware":       "#dc2626",
  "Other":          "#64748b",
};

const applicationOrder = [
  "Medical/Therapeutic",
  "Medical/Diagnostic",
  "Medical/Device",
  "Consumer/Wellness",
  "Software/Analytics",
  "Research Tools",
  "Other"
];

// Shared helper: wraps filter inputs in a subtle card border.
// Each argument becomes a row separated by a hairline rule.
function makeControlCard(...rows) {
  const card = document.createElement("div");
  card.style.cssText = "border:1px solid var(--theme-foreground-faintest); border-radius:8px; padding:0.875rem 1.25rem; background:var(--theme-background-alt); margin-bottom:0.75rem;";
  rows.forEach((el, i) => {
    if (i > 0) {
      const sep = document.createElement("div");
      sep.style.cssText = "height:1px; background:var(--theme-foreground-faintest); margin:0.625rem 0;";
      card.appendChild(sep);
    }
    card.appendChild(el);
  });
  return card;
}
```

<p class="section-label">§1 Timeline</p>

## When neurotech companies were founded

<p class="caption">
  Each bar is a year. Colors show regional split. Hover for details;
  click the legend to toggle regions. Most of the dataset is young —
  the modern neurotech wave starts around 2014.
</p>

```js
// Filter to rows with a known year and clip outliers to 1990+ for the main chart
const timelineData = companies.filter(d => d.founding_year && d.founding_year >= 1990);
```

```js
// §1 filter — independent reactive binding (chart renders ALL data once)
const _s1RegionInput = Inputs.checkbox(regionOrder, {value: regionOrder, label: "Regions"});
display(makeControlCard(_s1RegionInput));
```

```js
const s1SelectedRegions = Generators.input(_s1RegionInput);
```

```js
// Render chart ONCE with ALL regions. Animation cell toggles individual
// bar segments via CSS transitions — no re-render needed.
const colorToRegion = {};
regionOrder.forEach(r => { colorToRegion[regionColors[r]] = r; });

const s1Chart = Plot.plot({
  width,
  height: 380,
  marginLeft: 50,
  marginBottom: 40,
  x: {
    label: "Founding year →",
    tickFormat: "d",
    labelAnchor: "right"
  },
  y: {
    label: "↑ Companies founded",
    grid: true,
  },
  color: {
    legend: true,
    domain: regionOrder,
    range: regionOrder.map(r => regionColors[r] || "#94a3b8"),
    label: "Region"
  },
  marks: [
    Plot.rectY(
      timelineData,
      Plot.binX(
        {y: "count"},
        {
          x: "founding_year",
          fill: "region",
          interval: 1,
          order: regionOrder,
          tip: {
            format: {
              x: "d",
              y: true,
              fill: true
            }
          }
        }
      )
    ),
    Plot.ruleY([0])
  ]
});

// Tag each rect with its region and store original geometry for stacking
const s1AllRects = s1Chart.querySelectorAll('[aria-label="rect"] rect');
for (const r of s1AllRects) {
  r.dataset.region = colorToRegion[r.getAttribute("fill")] || "Other";
  r.dataset.origY = r.getAttribute("y");
  r.dataset.origH = r.getAttribute("height");
  r.style.transition = "y 0.35s ease-out, height 0.35s ease-out";
}

const s1Container = display(html`<div id="timeline-chart-container">${s1Chart}</div>`);
```

```js
// Reactive animation: recompute stack positions when checkboxes change.
// Only the toggled region's bars grow/shrink; neighbours shift to fill gaps.
(function animateTimeline() {
  void s1Container;
  const container = document.getElementById("timeline-chart-container");
  if (!container) return;

  const selected = new Set(s1SelectedRegions);
  const rects = container.querySelectorAll('[aria-label="rect"] rect');

  // Group rects by x (each x = one year bin)
  const byX = new Map();
  for (const r of rects) {
    const x = r.getAttribute("x");
    if (!byX.has(x)) byX.set(x, []);
    byX.get(x).push(r);
  }

  for (const binRects of byX.values()) {
    // Sort bottom-up (highest origY = closest to baseline = bottom of stack)
    binRects.sort((a, b) => +b.dataset.origY - +a.dataset.origY);
    // Baseline = bottom edge of the lowest rect in the original layout
    const baseline = Math.max(...binRects.map(r => +r.dataset.origY + +r.dataset.origH));

    let currentY = baseline;
    for (const r of binRects) {
      const origH = +r.dataset.origH;
      if (selected.has(r.dataset.region)) {
        currentY -= origH;
        r.style.y = `${currentY}px`;
        r.style.height = `${origH}px`;
        r.style.pointerEvents = "auto";
      } else {
        r.style.y = `${currentY}px`;
        r.style.height = "0px";
        r.style.pointerEvents = "none";
      }
    }
  }
})();
```

<p class="section-label">§2 Funding trajectories</p>

## How much capital each company has raised

<p class="caption">
  Each curve traces one company's cumulative funding from its founding year
  (starting at $0) to the present. The vertical axis is logarithmic, so a
  $100K seed round and a $1B mega-round both get visual room. Curves are
  built from actual disclosed round data where available (188 companies,
  541 rounds) and smoothly interpolated between data points. Color shows
  the region. Hover to see the company name and total raised. Red ×
  marks companies whose domains are confirmed dead.
</p>

```js
// ---- Build cumulative funding curves from round-level data ----
const fundingRounds = await FileAttachment("data/funding_rounds.csv").csv({typed: true});

// Group rounds by company_name, sorted by date
const roundsByCompany = d3.group(
  fundingRounds.filter(d => d.date && d.amount_usd > 0),
  d => d.company_name
);

// Lookup: company_name → enriched row
const companyLookup = new Map(companies.map(d => [d.name, d]));

// Build curve data: for each company, generate points for a cumulative line
const fundingCurves = [];

for (const [name, rounds] of roundsByCompany) {
  const co = companyLookup.get(name);
  if (!co || !co.founding_year) continue;

  const sorted = rounds.slice().sort((a, b) => d3.ascending(a.date, b.date));
  const startYear = +co.founding_year;
  const region = co.region || "Other";
  const modality = co.primary_modality || "Other";
  const lifecycle = co.lifecycle_status || "unknown";
  const totalFunding = co.total_funding_usd ? +co.total_funding_usd : 0;

  // Point 1: founding year, $0 (can't do log(0), so use a small floor)
  const LOG_FLOOR = 10000; // $10K floor for log scale
  const points = [];
  points.push({
    name,
    region,
    modality,
    lifecycle,
    totalFunding,
    year: startYear,
    cumFunding: LOG_FLOOR,
    label: `${name} — founded ${startYear}`
  });

  // Intermediate points from actual rounds
  let cum = 0;
  for (const r of sorted) {
    cum += r.amount_usd;
    const d = new Date(r.date);
    const yearFrac = d.getFullYear() + d.getMonth() / 12;
    const monthStr = `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}`;
    points.push({
      name,
      region,
      modality,
      lifecycle,
      totalFunding,
      year: yearFrac,
      cumFunding: Math.max(cum, LOG_FLOOR),
      label: `${name} — $${(cum / 1e6).toFixed(1)}M raised by ${monthStr}`
    });
  }

  // Final point: extend to 2026.25 at the total
  const finalVal = totalFunding > 0 ? totalFunding : cum;
  points.push({
    name,
    region,
    modality,
    lifecycle,
    totalFunding,
    year: 2026.25,
    cumFunding: Math.max(finalVal, LOG_FLOOR),
    label: `${name} — $${(finalVal / 1e6).toFixed(1)}M total`
  });

  fundingCurves.push(...points);
}

// Also add companies with total_funding but NO individual rounds
// (synthetic 2-point curve: founding → total at 2026)
for (const co of companies) {
  if (!co.founding_year || !co.total_funding_usd || co.total_funding_usd <= 0) continue;
  if (roundsByCompany.has(co.name)) continue; // already covered above

  const LOG_FLOOR = 10000;
  const startYear = +co.founding_year;
  const total = +co.total_funding_usd;
  const region = co.region || "Other";
  const modality = co.primary_modality || "Other";
  const lifecycle = co.lifecycle_status || "unknown";

  fundingCurves.push(
    {name: co.name, region, modality, lifecycle, totalFunding: total, year: startYear, cumFunding: LOG_FLOOR, label: `${co.name} — founded ${startYear}`},
    {name: co.name, region, modality, lifecycle, totalFunding: total, year: 2026.25, cumFunding: Math.max(total, LOG_FLOOR), label: `${co.name} — $${(total / 1e6).toFixed(1)}M total`}
  );
}

// Dead/dormant endpoints for markers
const fundingEndpoints = Array.from(
  d3.group(fundingCurves, d => d.name),
  ([name, pts]) => pts[pts.length - 1]
);
const deadEndpoints = fundingEndpoints.filter(d => d.lifecycle === "dead_domain");
const dormantEndpoints = fundingEndpoints.filter(d => d.lifecycle === "dormant");

const nFundedCompanies = new Set(fundingCurves.map(d => d.name)).size;
```

```js
// ---- Filters: independent reactive bindings so modality/region changes
// ---- don't re-trigger useLogScale and cause a full chart re-render.
const modalityCounts = d3.rollup(fundingEndpoints, v => v.length, d => d.modality);
const filterOptions = [
  `All (${nFundedCompanies})`,
  ...modalityOrder.filter(m => modalityCounts.has(m)).map(m => `${m} (${modalityCounts.get(m)})`)
];
const regionCounts = d3.rollup(fundingEndpoints, v => v.length, d => d.region);
const regionFilterOptions = [
  `All (${nFundedCompanies})`,
  ...regionOrder.filter(r => regionCounts.has(r)).map(r => `${r} (${regionCounts.get(r)})`)
];

const _modInput = Inputs.radio(filterOptions,       {value: filterOptions[0],       label: "Modality"});
const _regInput = Inputs.radio(regionFilterOptions, {value: regionFilterOptions[0], label: "Region"});
const _logInput = Inputs.toggle({label: "Log scale Y", value: true});

const _logFooter = document.createElement("div");
_logFooter.style.cssText = "display:flex; justify-content:flex-end; padding-top:0.125rem;";
_logFooter.appendChild(_logInput);
display(makeControlCard(_modInput, _regInput, _logFooter));
```

```js
const selectedModRaw = Generators.input(_modInput);
```

```js
const selectedRegRaw = Generators.input(_regInput);
```

```js
const useLogScale = Generators.input(_logInput);
```

```js
const selectedModality = selectedModRaw.startsWith("All") ? null : selectedModRaw.replace(/\s*\(\d+\)$/, "");
const selectedRegion   = selectedRegRaw.startsWith("All") ? null : selectedRegRaw.replace(/\s*\(\d+\)$/, "");
```


```js
// ---- Render the chart ONCE with a single Plot.line for all curves ----
// Plot.line with z:"name" creates one <path> per company inside a single
// <g aria-label="line">. After rendering, we build an index mapping each
// <path> to its company's modality. The reactive animation cell then
// toggles styles on each path via CSS transitions — no re-render needed.

// Sort fundingCurves by company name so path order matches a known sequence.
// d3.group preserves insertion order → we'll get paths in company-name order.
const companyGroups = Array.from(d3.group(fundingCurves, d => d.name), ([name, pts]) => pts[0]);
const companyModalities = companyGroups.map(d => d.modality);
const companyRegions    = companyGroups.map(d => d.region);

const fundingChart = Plot.plot({
  width,
  height: 560,
  marginLeft: 70,
  marginRight: 30,
  marginBottom: 40,
  x: {
    label: "Year →",
    tickFormat: "d",
    domain: [1995, 2027],
    grid: true,
    labelAnchor: "right"
  },
  y: {
    type: useLogScale ? "log" : "linear",
    label: "↑ Cumulative funding (USD)",
    tickFormat: d => {
      if (d >= 1e9) return `$${d / 1e9}B`;
      if (d >= 1e6) return `$${d / 1e6}M`;
      if (d >= 1e3) return `$${d / 1e3}K`;
      return `$${d}`;
    },
    grid: true,
    domain: useLogScale ? [10000, 2e10] : [0, 6e8]
  },
  color: {
    legend: true,
    domain: regionOrder,
    range: regionOrder.map(r => regionColors[r] || "#94a3b8"),
    label: "Region"
  },
  marks: [
    // Reference lines
    Plot.ruleY([1e6], {stroke: "#e2e8f0", strokeDasharray: "2,4"}),
    Plot.ruleY([1e8], {stroke: "#e2e8f0", strokeDasharray: "2,4"}),
    Plot.ruleY([1e9], {stroke: "#e2e8f0", strokeDasharray: "2,4"}),

    // ALL curves in one mark — one <path> per company (z channel)
    Plot.line(fundingCurves, {
      x: "year",
      y: "cumFunding",
      z: "name",
      stroke: "region",
      strokeWidth: 1.2,
      strokeOpacity: 0.45,
      curve: "monotone-x",
      tip: {
        format: { x: "d", y: false, stroke: true }
      },
      channels: {
        Company: "name",
        Category: "modality",
        Raised: d => `$${(d.cumFunding / 1e6).toFixed(1)}M`,
        Status: "lifecycle"
      }
    }),

    // Labels for top companies
    Plot.text(
      fundingEndpoints
        .filter(d => d.totalFunding >= 50e6)
        .sort((a, b) => d3.descending(a.totalFunding, b.totalFunding))
        .slice(0, 20),
      {
        x: "year",
        y: "cumFunding",
        text: d => d.name.length > 22 ? d.name.slice(0, 20) + "…" : d.name,
        textAnchor: "end",
        dx: -6,
        fontSize: 9,
        fill: "currentColor",
        stroke: "var(--theme-background)",
        strokeWidth: 3
      }
    ),

    // Dead domain markers
    deadEndpoints.length > 0
      ? Plot.dot(deadEndpoints, {
          x: "year",
          y: "cumFunding",
          symbol: "times",
          stroke: "#dc2626",
          strokeWidth: 2,
          r: 4,
          tip: true,
          channels: {Company: "name"}
        })
      : null,

    // Dormant markers
    dormantEndpoints.length > 0
      ? Plot.dot(dormantEndpoints, {
          x: "year",
          y: "cumFunding",
          symbol: "circle",
          fill: "#94a3b8",
          stroke: "#475569",
          strokeWidth: 1,
          r: 3
        })
      : null
  ].filter(Boolean)
});

// Tag each <path> in the line group with a data-modality attribute
// and add inline CSS transition so animations work on SVG elements.
// Plot.line creates paths in the same order as d3.group(data, z).
const lineGroup = fundingChart.querySelector('[aria-label="line"]');
if (lineGroup) {
  const paths = lineGroup.querySelectorAll("path");
  paths.forEach((p, i) => {
    if (i < companyModalities.length) {
      p.setAttribute("data-modality", companyModalities[i]);
      p.setAttribute("data-region", companyRegions[i]);
      // Inline transition — CSS transitions on SVG require the property
      // to be set via style (not attribute), AND the transition rule
      // must be on the element. Inline is the only reliable way.
      p.style.transition = "stroke-opacity 0.8s ease-in-out, stroke-width 0.8s ease-in-out";
    }
  });
}

// Tag top-company text labels with modality/region
const labelData = fundingEndpoints
  .filter(d => d.totalFunding >= 50e6)
  .sort((a, b) => d3.descending(a.totalFunding, b.totalFunding))
  .slice(0, 20);
const textGroup = fundingChart.querySelector('[aria-label="text"]');
if (textGroup) {
  const texts = textGroup.querySelectorAll("text");
  texts.forEach((t, i) => {
    if (i < labelData.length) {
      t.setAttribute("data-modality", labelData[i].modality);
      t.setAttribute("data-region", labelData[i].region);
      t.style.transition = "opacity 0.8s ease-in-out";
    }
  });
}

// Tag dead endpoint markers (×) — first dot group
const allDotGroups = Array.from(fundingChart.querySelectorAll('[aria-label="dot"]'));
if (allDotGroups.length >= 1 && deadEndpoints.length > 0) {
  const deadCircles = allDotGroups[0].querySelectorAll("circle");
  deadCircles.forEach((c, i) => {
    if (i < deadEndpoints.length) {
      c.setAttribute("data-modality", deadEndpoints[i].modality);
      c.setAttribute("data-region", deadEndpoints[i].region);
      c.style.transition = "opacity 0.8s ease-in-out";
    }
  });
}
// Tag dormant endpoint markers (●) — second dot group (or first if no dead)
const dormantGroupIdx = deadEndpoints.length > 0 ? 1 : 0;
if (allDotGroups.length > dormantGroupIdx && dormantEndpoints.length > 0) {
  const dormantCircles = allDotGroups[dormantGroupIdx].querySelectorAll("circle");
  dormantCircles.forEach((c, i) => {
    if (i < dormantEndpoints.length) {
      c.setAttribute("data-modality", dormantEndpoints[i].modality);
      c.setAttribute("data-region", dormantEndpoints[i].region);
      c.style.transition = "opacity 0.8s ease-in-out";
    }
  });
}

const chartContainer = display(html`<div id="funding-chart-container">${fundingChart}</div>`);
```

```js
// ---- Reactive animation ----
// Re-runs when selectedModality, selectedRegion, or useLogScale changes.
// void chartContainer ensures this runs AFTER the chart (re-)renders.
//
// When the chart re-renders (e.g. log↔linear toggle), the SVG is brand new.
// We reset paths to their default state, force a reflow so the browser
// registers the "from" values, then set the target styles. This gives
// CSS transitions a valid start→end range to animate.
(function animateFunding() {
  void chartContainer;  // ordering: wait for chart render
  void useLogScale;     // re-run when scale toggles (chart re-renders)
  const container = document.getElementById("funding-chart-container");
  if (!container) return;

  const anyFilter = selectedModality !== null || selectedRegion !== null;

  const paths  = container.querySelectorAll("path[data-modality]");
  const dots   = container.querySelectorAll("circle[data-modality]");
  const labels = container.querySelectorAll("text[data-modality]");

  // 1. Reset every element to the unfiltered default state
  for (const p of paths)  { p.style.strokeOpacity = "0.45"; p.style.strokeWidth = "1.2px"; }
  for (const d of dots)   { d.style.opacity = "1"; }
  for (const l of labels) { l.style.opacity = "1"; }

  if (!anyFilter) return;   // no active filter → stay at default

  // 2. Force reflow so the browser commits the default values
  void container.offsetHeight;

  // 3. Apply the filter target styles — CSS transition animates the change
  for (const path of paths) {
    const mod = path.getAttribute("data-modality");
    const reg = path.getAttribute("data-region");
    const isActive = (selectedModality === null || mod === selectedModality)
                  && (selectedRegion   === null || reg === selectedRegion);
    path.style.strokeOpacity = isActive ? "0.75" : "0.18";
    path.style.strokeWidth   = isActive ? "2.2px" : "0.9px";
  }

  for (const dot of dots) {
    const mod = dot.getAttribute("data-modality");
    const reg = dot.getAttribute("data-region");
    const isActive = (selectedModality === null || mod === selectedModality)
                  && (selectedRegion   === null || reg === selectedRegion);
    dot.style.opacity = isActive ? "1" : "0.1";
  }

  for (const label of labels) {
    const mod = label.getAttribute("data-modality");
    const reg = label.getAttribute("data-region");
    const isActive = (selectedModality === null || mod === selectedModality)
                  && (selectedRegion   === null || reg === selectedRegion);
    label.style.opacity = isActive ? "1" : "0";
  }
})();
```

<p style="color: var(--theme-foreground-muted); font-size: 0.85rem; margin-top: 0.5rem;">
  ${nFundedCompanies} companies with disclosed funding shown.
  Pre-1995 outliers clipped from X axis for readability.
  Dashed lines mark $1M, $100M, and $1B thresholds.
</p>

<p class="section-label">§3 Categories</p>

## What tech the industry is built on

<p class="caption">
  Primary category is derived heuristically from reccy's industry tags —
  wearables, medical devices, therapeutics, diagnostics, software/AI platforms,
  research tools, hardware, and long-tail others. It's a form-factor axis,
  not a technology axis. Hover for exact counts.
</p>

```js
display(Plot.plot({
  width,
  height: 260,
  marginLeft: 100,
  marginRight: 20,
  x: {label: "Companies →", grid: true},
  y: {label: null, domain: modalityOrder},
  color: {
    domain: modalityOrder,
    range: modalityOrder.map(m => modalityColors[m] || "#64748b")
  },
  marks: [
    Plot.barX(
      companies,
      Plot.groupY(
        {x: "count"},
        {
          y: "primary_modality",
          fill: "primary_modality",
          sort: {y: "x", reverse: true},
          tip: true
        }
      )
    ),
    Plot.ruleX([0]),
    Plot.text(
      companies,
      Plot.groupY(
        {x: "count", text: "count"},
        {
          y: "primary_modality",
          textAnchor: "start",
          dx: 6,
          fill: "currentColor"
        }
      )
    )
  ]
}))
```

<p class="section-label">§4 Geography</p>

## Top countries by company count

<p class="caption">
  The top 15 countries — unsurprisingly USA-dominated, with Europe
  fragmented across many smaller hubs. Bar color shows the region
  the country belongs to.
</p>

```js
const countryCounts = d3.rollups(
  companies.filter(d => d.country),
  v => v.length,
  d => d.country
).sort((a, b) => d3.descending(a[1], b[1])).slice(0, 15);

const topCountries = countryCounts.map(([country, count]) => ({
  country,
  count,
  region: companies.find(d => d.country === country)?.region || "Other"
}));
```

```js
display(Plot.plot({
  width,
  height: 400,
  marginLeft: 120,
  marginRight: 40,
  x: {label: "Companies →", grid: true},
  y: {label: null, domain: topCountries.map(d => d.country)},
  color: {
    domain: regionOrder,
    range: regionOrder.map(r => regionColors[r] || "#94a3b8"),
    legend: true,
    label: "Region"
  },
  marks: [
    Plot.barX(topCountries, {
      x: "count",
      y: "country",
      fill: "region",
      tip: true
    }),
    Plot.ruleX([0]),
    Plot.text(topCountries, {
      x: "count",
      y: "country",
      text: d => d.count,
      textAnchor: "start",
      dx: 6,
      fill: "currentColor"
    })
  ]
}))
```

<p class="section-label">§5 Competitive Matrix</p>

## Modality × Region heatmap

<p class="caption">
  Where does each category concentrate geographically? Each cell shows how
  many companies sit at that modality × region intersection. Dark cells =
  crowded niches; empty cells = white-space opportunities (or data gaps).
</p>

```js
display(Plot.plot({
  width,
  height: 380,
  marginLeft: 110,
  marginBottom: 80,
  padding: 0.05,
  x: {label: null, domain: regionOrder, tickRotate: -30},
  y: {label: null, domain: modalityOrder},
  color: {
    type: "linear",
    scheme: "YlGnBu",
    legend: true,
    label: "Companies"
  },
  marks: [
    Plot.cell(
      companies.filter(d => d.region && d.primary_modality),
      Plot.group(
        {fill: "count"},
        {x: "region", y: "primary_modality", tip: true}
      )
    ),
    Plot.text(
      companies.filter(d => d.region && d.primary_modality),
      Plot.group(
        {text: "count"},
        {
          x: "region",
          y: "primary_modality",
          fill: "black",
          stroke: "white",
          strokeWidth: 3,
          fontSize: 11
        }
      )
    )
  ]
}))
```

<p class="section-label">§6 Growth by Modality</p>

## Which categories are rising

<p class="caption">
  Companies founded per year, stacked by modality.
  Wearables and therapeutics dominate the 2018–2024 surge; software/AI
  is a steady but thinner stream. Clipped to 2000+ for readability.
</p>

```js
// Pre-aggregate year × modality counts, filling gaps with 0 so the
// smooth curve doesn't jump over missing years.
const growthFiltered = companies.filter(d => d.founding_year && d.founding_year >= 2000);
const growthYears = d3.range(2000, 2027);
const growthCounts = d3.rollup(growthFiltered, v => v.length, d => d.founding_year, d => d.primary_modality || "Other");
const growthData = growthYears.flatMap(year =>
  modalityOrder.map(mod => ({
    year,
    modality: mod,
    count: growthCounts.get(year)?.get(mod) || 0
  }))
);
```

```js
display(Plot.plot({
  width,
  height: 400,
  x: {label: "Year →", tickFormat: "d"},
  y: {label: "↑ Companies founded", grid: true},
  color: {
    domain: modalityOrder,
    range: modalityOrder.map(m => modalityColors[m] || "#64748b"),
    legend: true,
    label: "Modality"
  },
  marks: [
    Plot.areaY(
      growthData,
      Plot.stackY({
        x: "year",
        y: "count",
        fill: "modality",
        order: modalityOrder,
        curve: "basis"
      })
    ),
    Plot.ruleY([0])
  ]
}))
```

<p style="color: var(--theme-foreground-muted); font-size: 0.85rem; margin-top: 0.5rem;">
  ${growthFiltered.length} companies with known founding year (2000+).
</p>

<p class="section-label">§7 Capital Flow</p>

## Funding volume by year

<p class="caption">
  How much money went into neurotech each year, stacked by round type.
  Only rounds with disclosed amounts are shown. Late-stage rounds
  (Series C+) can dwarf seed in dollar terms even when seed deal count
  is higher. Data from 2010 onward.
</p>

```js
const roundTypeOrder = ["Pre-Seed", "Seed", "Series A", "Series B", "Series C+", "Grant", "Venture Round", "Post-IPO", "Debt/Note", "Other"];

function normalizeRound(t) {
  if (!t) return "Other";
  const lc = t.toLowerCase().trim();
  if (lc.startsWith("pre")) return "Pre-Seed";
  if (lc === "seed") return "Seed";
  if (lc === "series a") return "Series A";
  if (lc === "series b") return "Series B";
  if (/^series [c-z]/.test(lc)) return "Series C+";
  if (lc === "grant") return "Grant";
  if (lc.includes("venture")) return "Venture Round";
  if (lc.includes("ipo")) return "Post-IPO";
  if (lc.includes("debt") || lc.includes("note") || lc.includes("convertible")) return "Debt/Note";
  return "Other";
}

const fundingByYear = fundingRounds
  .filter(d => d.date && d.amount_usd > 0)
  .map(d => ({
    year: new Date(d.date).getFullYear(),
    amount: +d.amount_usd,
    round_type: normalizeRound(d.round_type)
  }))
  .filter(d => d.year >= 2010);
```

```js
display(Plot.plot({
  width,
  height: 420,
  x: {label: "Year →", tickFormat: "d", interval: 1},
  y: {
    label: "↑ Funding volume (USD)",
    grid: true,
    tickFormat: d => d >= 1e9 ? `$${(d / 1e9).toFixed(1)}B` : `$${(d / 1e6).toFixed(0)}M`
  },
  color: {
    domain: roundTypeOrder,
    legend: true,
    label: "Round type"
  },
  marks: [
    Plot.barY(
      fundingByYear,
      Plot.binX(
        {y: "sum"},
        {
          x: "year",
          y: "amount",
          fill: "round_type",
          interval: 1,
          order: roundTypeOrder
        }
      )
    ),
    Plot.ruleY([0])
  ]
}))
```

<p style="color: var(--theme-foreground-muted); font-size: 0.85rem; margin-top: 0.5rem;">
  ${fundingByYear.length} rounds with disclosed amounts (2010+).
</p>

<div class="about-block">

### About the data

This dashboard is powered by two datasets: a company-level table
(${nCompanies} rows) and a funding-rounds table, both derived from
[reccy.dev](https://app.reccy.dev/companies) and enriched in-house.
The raw data is kept in a private repository; only the columns needed
for visualization are served to the browser. Source code is on
[GitHub](https://github.com/PershinIlya/NeurotechBoard).

**Source:** companies scraped from reccy.dev, snapshot 2026-04-09.
${nCompanies} rows after dedup across ${nCountries} countries.

**Enrichment:** founding years are web-verified with H/M/L confidence
tiers and per-row source URLs
([methodology](https://github.com/PershinIlya/NeurotechBoard/blob/main/docs/methodology.md)).
Modality, application, and region fields are derived heuristically from
reccy's industry tags and should be treated as a starting point, not
ground truth.

**Lifecycle tracking** runs an automated domain-check pass over all
${nCompanies} company websites, classifying them into `active` /
`dormant` / `dead_domain` / `unknown` tiers. A live website is a floor,
not a ceiling — it doesn't guarantee the company is still operating,
just that something answers.

**Known limitations:** see the
[discrepancies log](https://github.com/PershinIlya/NeurotechBoard/blob/main/docs/reccy_discrepancies.md).
Reccy has country mismatches, duplicate rows, and occasionally scrapes a
parked-domain title as the company name. We keep reccy's values as-is
and log deltas rather than silently correcting.

This is a personal project. Contributions, corrections, and pull
requests welcome.

</div>
