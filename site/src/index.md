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
display(Plot.plot({
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
}))
```

<p class="section-label">§2 Lifelines</p>

## Every company as its own line

<p class="caption">
  One horizontal line per company, sorted top-to-bottom by founding year
  (oldest at the bottom, newest at the top). The line runs from the
  year the company was founded to the date of the last lifecycle check
  (2026-04-09). <strong>Color</strong> shows the form-factor category;
  <strong>line thickness</strong> encodes the most recent funding stage —
  thin wisps are pre-seed / seed / grant territory, thick strokes are
  companies that reached Series C+, private equity, or public markets.
  Hover any line to see the company, year, category, and funding stage.
  Red × marks dead domains; gray ○ marks dormant sites. The "fan" shape
  opening to the right is the modern neurotech wave — notice how sparse
  everything before ~2014 looks, and how dense the last decade is.
</p>

```js
// ---- Pre-compute sorted lifeline data with funding tiers ----
// Each company becomes one row. Sort ascending by founding year so the
// oldest entries anchor the bottom of the chart. Companies missing a
// founding year are dropped (can't draw a line without a start).
//
// `end_year` is fixed at the date of the last lifecycle verification
// (domain-check pass, 2026-04-09). For active companies this is honest
// ("last time we checked, they were alive"). For dead_domain rows the
// line still extends to 2026 because we don't know WHEN the domain died,
// only that it was dead by the check date — we add a visual marker at
// the end instead.
//
// `funding_tier` maps reccy's last_funding_stage (~25 values) down to
// 0-5 ordinal buckets, from "unknown" up through "post-IPO / acquired".
// Rendered as stroke width in the chart so mature companies visually
// pop out of the noise of seed-stage wisps.
const LIFELINE_END = 2026.25; // mid-Q2 2026 ≈ check date

// 0=unknown, 1=pre-seed/seed, 2=A/venture, 3=B/C/PE, 4=D-F, 5=IPO/acquired
function fundingTier(stage) {
  if (!stage) return 0;
  const s = stage.toLowerCase().trim();
  if (s === "undisclosed" || s === "non equity assistance" || s === "series unknown") return 0;
  if (s.includes("post-ipo") || s === "ipo" || s === "acquisition" || s === "secondary market") return 5;
  if (s.includes("series f") || s.includes("series e") || s.includes("series d")) return 4;
  if (s.includes("series c") || s.includes("series b") || s === "private equity") return 3;
  if (s.includes("series a") || s === "venture round" || s === "corporate round") return 2;
  if (
    s === "seed" || s === "pre-seed" || s === "pre seed" ||
    s === "grant" || s === "convertible note" || s === "debt financing" ||
    s === "equity crowdfunding" || s === "conventional debt"
  ) return 1;
  return 0;
}

// Stroke width per tier. Baseline at 1.1 so "unknown" is still visible;
// top tier at 2.8 so an IPO line reads as ~2.5x thicker than a seed line
// without overwhelming neighbors at ~2px row spacing.
const TIER_STROKE_WIDTH = [0.7, 1.1, 1.5, 2.0, 2.4, 2.8];

// Human-readable tier name for the tooltip
const TIER_LABEL = [
  "Unknown / undisclosed",
  "Seed / grant / crowdfunding",
  "Series A / venture round",
  "Series B–C / private equity",
  "Series D–F",
  "Post-IPO / acquired"
];

const lifelineData = companies
  .filter(d => d.founding_year)
  .map(d => {
    const tier = fundingTier(d.last_funding_stage);
    return {
      ...d,
      founding_year: +d.founding_year,
      end_year: LIFELINE_END,
      funding_tier: tier,
      funding_tier_label: TIER_LABEL[tier],
      stroke_width: TIER_STROKE_WIDTH[tier]
    };
  })
  .sort((a, b) => d3.ascending(a.founding_year, b.founding_year))
  .map((d, i) => ({...d, rank: i}));

const lifelineDead = lifelineData.filter(
  d => d.lifecycle_status === "dead_domain"
);
const lifelineDormant = lifelineData.filter(
  d => d.lifecycle_status === "dormant"
);
```

```js
display(Plot.plot({
  width,
  height: 820,
  marginLeft: 20,
  marginRight: 30,
  marginTop: 10,
  marginBottom: 40,
  x: {
    label: "Year →",
    tickFormat: "d",
    grid: true,
    labelAnchor: "right"
  },
  y: {
    axis: null,
    label: null,
    domain: [-1, lifelineData.length]
  },
  color: {
    legend: true,
    domain: modalityOrder,
    range: modalityOrder.map(m => modalityColors[m] || "#64748b"),
    label: "Category"
  },
  marks: [
    // Vertical rule at 2014 — the inflection point of the modern wave
    Plot.ruleX([2014], {
      stroke: "#94a3b8",
      strokeDasharray: "3,4",
      strokeWidth: 1
    }),
    // One horizontal line per company, founding_year → end_year.
    // Stroke width varies by funding_tier so mature companies visibly
    // thicken out of the seed-stage noise floor.
    Plot.link(lifelineData, {
      x1: "founding_year",
      x2: "end_year",
      y1: "rank",
      y2: "rank",
      stroke: "primary_modality",
      strokeWidth: d => d.stroke_width,
      strokeOpacity: 0.85,
      strokeLinecap: "round",
      tip: true,
      channels: {
        Company: "name",
        Founded: "founding_year",
        Category: "primary_modality",
        Country: "country",
        "Funding stage": "last_funding_stage",
        "Funding tier": "funding_tier_label",
        Status: "lifecycle_status"
      }
    }),
    // Red × at the end of dead_domain lines
    Plot.dot(lifelineDead, {
      x: "end_year",
      y: "rank",
      symbol: "times",
      stroke: "#dc2626",
      strokeWidth: 2,
      r: 3.5
    }),
    // Gray circle at the end of dormant lines
    Plot.dot(lifelineDormant, {
      x: "end_year",
      y: "rank",
      symbol: "circle",
      fill: "#94a3b8",
      stroke: "#475569",
      strokeWidth: 1,
      r: 3
    })
  ]
}))
```

<p class="section-label">§3 Funding trajectories</p>

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
// ---- Filters: Modality + Region side-by-side, Log scale toggle separated by a divider ----
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

const fundingFilters = view(Inputs.form(
  {modality: _modInput, region: _regInput, logScale: _logInput},
  {
    template: (inputs) => {
      const wrap = document.createElement("div");
      wrap.style.cssText = "display:flex; gap:0; align-items:flex-start; flex-wrap:wrap; margin-bottom:0.25rem;";

      const left = document.createElement("div");
      left.style.cssText = "display:flex; gap:2.5rem; flex-wrap:wrap; flex:1; min-width:0;";
      left.appendChild(inputs.modality);
      left.appendChild(inputs.region);

      const divider = document.createElement("div");
      divider.style.cssText = "width:1px; background:#e2e8f0; margin:0.25rem 2rem 0; align-self:stretch; flex-shrink:0;";

      const right = document.createElement("div");
      right.style.cssText = "display:flex; align-items:flex-start; padding-top:0.25rem; flex-shrink:0;";
      right.appendChild(inputs.logScale);

      wrap.appendChild(left);
      wrap.appendChild(divider);
      wrap.appendChild(right);
      return wrap;
    }
  }
));
```

```js
const selectedModality = fundingFilters.modality.startsWith("All") ? null : fundingFilters.modality.replace(/\s*\(\d+\)$/, "");
const selectedRegion   = fundingFilters.region.startsWith("All")   ? null : fundingFilters.region.replace(/\s*\(\d+\)$/, "");
const useLogScale      = fundingFilters.logScale;
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
      p.style.transition = "stroke-opacity 0.6s ease-in-out, stroke-width 0.6s ease-in-out";
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
      c.style.transition = "opacity 0.6s ease-in-out";
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
      c.style.transition = "opacity 0.6s ease-in-out";
    }
  });
}

const chartContainer = display(html`<div id="funding-chart-container">${fundingChart}</div>`);
```

```js
// ---- Reactive animation ----
// Re-runs when selectedModality, selectedRegion, or useLogScale changes.
// void chartContainer ensures this runs AFTER the chart (re-)renders.
(function animateFunding() {
  void chartContainer;  // ordering: wait for chart render
  void useLogScale;     // re-run when scale toggles (chart re-renders)
  const container = document.getElementById("funding-chart-container");
  if (!container) return;

  const anyFilter = selectedModality !== null || selectedRegion !== null;

  // Animate line paths
  const paths = container.querySelectorAll("path[data-modality]");
  for (const path of paths) {
    const mod = path.getAttribute("data-modality");
    const reg = path.getAttribute("data-region");
    const isActive = (selectedModality === null || mod === selectedModality)
                  && (selectedRegion   === null || reg === selectedRegion);
    path.style.strokeOpacity = !anyFilter ? "0.45" : (isActive ? "0.75" : "0.18");
    path.style.strokeWidth   = !anyFilter ? "1.2px" : (isActive ? "2.2px" : "0.9px");
  }

  // Animate dormant/dead dot markers
  const dots = container.querySelectorAll("circle[data-modality]");
  for (const dot of dots) {
    const mod = dot.getAttribute("data-modality");
    const reg = dot.getAttribute("data-region");
    const isActive = (selectedModality === null || mod === selectedModality)
                  && (selectedRegion   === null || reg === selectedRegion);
    dot.style.opacity = (!anyFilter || isActive) ? "1" : "0.1";
  }
})();
```

<p style="color: var(--theme-foreground-muted); font-size: 0.85rem; margin-top: 0.5rem;">
  ${nFundedCompanies} companies with disclosed funding shown.
  Pre-1995 outliers clipped from X axis for readability.
  Dashed lines mark $1M, $100M, and $1B thresholds.
</p>

<p class="section-label">§4 Categories</p>

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

<p class="section-label">§5 Applications × Categories</p>

## Where the categories land

<p class="caption">
  A heatmap of how the form-factor categories cross-tabulate with
  application domains. Darker cells mean more companies. The
  Medical/Therapeutic × Therapeutics corner is the drug-delivery and
  neurostim cluster; the Consumer/Wellness × Wearable corner is the
  wellness-wearable world.
</p>

```js
display(Plot.plot({
  width,
  height: 320,
  marginLeft: 100,
  marginBottom: 50,
  padding: 0.02,
  x: {label: "Application →", domain: applicationOrder},
  y: {label: "Modality ↑", domain: modalityOrder.slice().reverse()},
  color: {
    type: "linear",
    scheme: "blues",
    legend: true,
    label: "Companies"
  },
  marks: [
    Plot.cell(
      companies,
      Plot.group(
        {fill: "count"},
        {
          x: "application",
          y: "primary_modality",
          tip: true
        }
      )
    ),
    Plot.text(
      companies,
      Plot.group(
        {text: "count"},
        {
          x: "application",
          y: "primary_modality",
          fill: "black",
          stroke: "white",
          strokeWidth: 3
        }
      )
    )
  ]
}))
```

<p class="section-label">§6 Geography</p>

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

<div class="about-block">

### About the data

This dashboard is built from a single, open CSV:
[`data/processed/neurotech_enriched.csv`](https://github.com/PershinIlya/NeurotechBoard/blob/main/data/processed/neurotech_enriched.csv)
in the [NeurotechBoard repository](https://github.com/PershinIlya/NeurotechBoard).

**Source:** companies scraped from [reccy.dev](https://app.reccy.dev/companies),
snapshot 2026-04-09. 393 rows after dedup.

**Enrichment:** founding years are web-verified with H/M/L confidence tiers
and per-row source URLs ([methodology](https://github.com/PershinIlya/NeurotechBoard/blob/main/docs/methodology.md)).
Modality and application fields are derived heuristically from reccy's
industry tags and should be treated as a starting point, not ground truth.

**Lifecycle tracking** runs an automated domain-check pass over all 393
company websites, classifying them into `active` / `dormant` / `dead_domain` /
`unknown` tiers. A live website is a floor, not a ceiling — it doesn't
guarantee the company is still operating, just that something answers.

**Known limitations:** see the
[discrepancies log](https://github.com/PershinIlya/NeurotechBoard/blob/main/docs/reccy_discrepancies.md).
Reccy has country mismatches, duplicate rows, and occasionally scrapes a
parked-domain title as the company name. We keep reccy's values as-is and
log deltas rather than silently correcting.

This is a personal pet project, released under a permissive license.
Contributions, corrections, and pull requests welcome.

</div>
