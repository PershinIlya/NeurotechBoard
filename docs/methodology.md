# Methodology

## Source

Primary source: [reccy.dev companies list](https://app.reccy.dev/companies), a curated directory of neurotech companies. Snapshot taken 2026-04-09, 395 companies visible in the UI.

Extraction method: reccy.dev is a Next.js SPA with no export button. Used Claude in Chrome to traverse the React fiber tree and pull `memoizedProps.companies` directly from the component state, bypassing pagination. Dumped to a pipe-delimited textarea inside the `<main>` element to work around tool output size limits.

Fields captured from reccy: `name`, `industries` (list), `headcount` bucket, `lastFundingType`, `website`, `location` (city/country string), `jobCount`.

Dedup: 2 rows were collapsed due to duplicate entries in reccy (same company listed twice with slightly different metadata). Final row count: 393.

## Derived fields

All derivations live in `src/build_dataset.py` and are deterministic — re-running the pipeline produces identical output.

### country, region
Extracted from the `location` string via a lookup table of known cities. Unknown cities fall through. Region mapping groups countries into North America, Europe, MENA, Asia, Oceania, Latin America, Africa.

### primary_modality
Heuristic classification from reccy's `industries` tags into: EEG, TMS, implant, fNIRS, optical, software, other. **Not manually verified.** Tags like "BCI" map to implant only if paired with invasive markers; otherwise to software. This is noisy and should be treated as a starting point, not ground truth.

### application
Grouped into: clinical (therapeutic/diagnostic), consumer, research_tools, enterprise, other. Same heuristic caveat.

### invasiveness
Three buckets: invasive, non_invasive, na. Derived from modality and industry tags.

### headcount_bucket
Passed through from reccy's own buckets (e.g., "11-50", "51-200").

### decade, half_year
Derived from `founding_year` when available, else blank. `half_year` format: "2016-H1", "2016-H2".

## Founding year

The most fragile field in the dataset. Current v0.1.0 strategy:

1. Hardcoded dictionary in `build_dataset.py` (~180 entries) from training knowledge.
2. Confidence tiers: H (well-known public info, high confidence), M (reasonable estimate from training), L (rough guess, treat with suspicion).
3. Companies not in the dictionary have blank `founding_year` and are excluded from timeline aggregations.

**Coverage: 188/393 = 47.8%.** The skew matters: well-known companies (Neuralink, Synchron, Medtronic) are covered; long-tail smaller companies are not. This biases timeline charts toward the "famous" subset.

**Planned remediation (v0.2.0):** Web-search the remaining ~205 companies for founding years. Target: 85%+ coverage with all results tagged confidence M unless a primary source (Crunchbase, LinkedIn, company About page) confirms.

## Lifecycle tracking (v0.2.0)

We track company lifecycle state with four columns: `lifecycle_status`, `lifecycle_as_of`, `lifecycle_confidence`, `lifecycle_source`. The structure mirrors `founding_year` — status + date + confidence tier + provenance URL.

### Why not a single `death_date` column

Real company death is multi-modal. A single `death_date` column forces you to sort these scenarios into "alive/dead" binary, and you lose important nuance in both directions:

- **Acquired** (e.g. Bioness → Bioventus 2021) — not dead, just different parent
- **Merged** (e.g. Kandu Health + Neurolutions 2025) — lives under new entity
- **Dissolved** — formally liquidated, has a real date from a registry
- **Dormant/zombie** — website exists, no news in 2+ years, team scattered; no clean date
- **Stealth-again** — briefly silent, will resurface
- **Pivoted out of neurotech** — alive but off-topic
- **Renamed** (e.g. Joy Ventures → Corundum → CNS Fund) — same entity, new identity
- **Parked domain** — proxy for wind-down but not conclusive

A binary `is_dead` + `death_date` model forces false precision on all of these except formal dissolution. The multi-state model keeps the honest shape of the data.

### Status taxonomy

| Status | Meaning | Typical source |
|---|---|---|
| `active` | Website responds 200, content present, not parked | Automated domain check |
| `dormant` | Website down (timeout, 4xx, 5xx, SSL error) — ambiguous signal | Automated domain check |
| `dead_domain` | DNS NXDOMAIN, domain parked, or for-sale landing page | Automated domain check |
| `acquired` | Absorbed by another entity, still operating as division | Manual research |
| `merged` | Two entities combined into new one | Manual research |
| `dissolved` | Formally liquidated via registry | Manual research |
| `pivoted` | Still alive but no longer neurotech | Manual research |
| `renamed` | Same entity, different brand | Manual research |
| `unknown` | No website in reccy, or automated check couldn't classify | Default |

### Confidence tiers

- **H** — hard signal (NXDOMAIN, parked marker, primary registry record, dated press release)
- **M** — soft signal (live HTTP 200, SSL error, transient 5xx — website state is indicative but not conclusive)
- **L** — weak signal (bot-blocked 401/403 — server alive but we couldn't verify content, so lifecycle is a guess based on "something is answering the phone")

### The `lifecycle_as_of` field

**NOT** "when the company died". It's the most recent date we verified *something* about the lifecycle status. For automated checks this is the check run date; for manual entries it's the date in the source document.

For `active` status, `as_of` = last day we confirmed a live website. A row marked `active (M) as_of 2026-04-09` says "on that date, site responded". It does not claim the company is active *today*. For ongoing monitoring, re-run the domain checker periodically and rebuild the CSV.

### Step 1 — automated domain check (`src/check_domains.py`)

Step 1 is a stdlib-only script that probes each company's website concurrently (20 workers, ~60s total). For each row it records HTTP status, final URL after redirect, page title, and a list of flags, then classifies into one of `active / dormant / dead_domain / unknown`.

Classification rules (first match wins):
1. Malformed website field (no dot, spaces) → `unknown` + `malformed_website` flag
2. DNS NXDOMAIN → `dead_domain (H)` + `nxdomain` flag
3. HTTP 200 with a parked-domain marker in body → `dead_domain (H)` + `parked` flag
4. HTTP 401/403 → retry with browser User-Agent; if still blocked → `active (L)` + `bot_blocked` flag
5. HTTP 4xx (non-401/403) or 5xx → if reccy URL had a path, retry the root; on success → `active (M)` + `path_lost_root_ok` flag; else → `dormant (M)`
6. SSL handshake error or connection refused → `dormant (M)`
7. Timeout → `dormant (M)`
8. HTTP 200, no parked markers → `active (M)`

Output lands in `data/processed/domain_checks.json` with a `checked_at` timestamp at the top level (applies to all rows in that run). The build script reads this file and joins by lowercased company name.

### Manual overrides (`LIFECYCLE_OVERRIDES` dict)

The `src/build_dataset.py` dict `LIFECYCLE_OVERRIDES` takes precedence over the auto-check results. Populate it from Crunchbase passes, press releases, and registry lookups for entries that need the `acquired / merged / dissolved / pivoted / renamed` statuses — the auto-checker cannot emit those, it only sees HTTP signals.

Empty at v0.2.0 release. Later passes fill it.

### Coverage expectations and caveats

From the first full run (2026-04-09, 393 rows):
- `active`: ~97% (most companies have live sites)
- `dead_domain`: ~1-2% (hard signal)
- `dormant`: ~1% (transient, re-check to disambiguate)
- `unknown`: ~0.5% (no website in reccy)

**What automated checks CAN'T see:**
- Acquisition when the subsidiary page is still live (Bioness/Bioventus looks "active" to us but is legally inside Bioventus since 2021)
- Pivot when the company is alive but out of neurotech
- Long stealth periods distinguishable from dormancy
- Any `as_of` date earlier than the check run — automated probes can only report "alive now"

That's why `active (M)` is a floor, not a ceiling. High-confidence `active` requires additional signals (recent funding, press, job postings, Crunchbase `Operating` status) that will come in later steps.

### Roadmap

- **v0.2.0** (this release): schema + automated domain checker. Baseline lifecycle data for 393 rows.
- **v0.2.x**: Crunchbase pass over the 187 URLs in `SOURCES` to harvest explicit `Operating / Closed / Acquired` statuses and upgrade many rows from `M` to `H`.
- **v0.3.0**: Manual top-50 lifecycle verification, `successor_entity` column, `acquired / merged / renamed` statuses populated.
- **v0.4.0+**: Reccy-delta monitoring (compare new scrapes against the 2026-04-09 baseline — companies that disappear from reccy are a weak lifecycle signal).

## Known limitations

1. **Founding year coverage bias.** Timeline charts over-represent well-known companies. Do not make claims like "neurotech company formation peaked in 2020" from v0.1.0 data.

2. **Modality/application are heuristic.** A company tagged "neurostimulation" could be anything from a clinical TMS device to a consumer wellness headband. Manual review needed for any analytical claims.

3. **reccy dedup gap.** 2 companies missing vs reccy's headline 395. Not critical (99.5% recall) but noted for full transparency.

4. **Snapshot recency.** reccy.dev is a moving target. v0.1.0 freezes the 2026-04-09 snapshot. Future versions should track the snapshot date per row if we start merging multiple dumps.

5. **No primary source verification.** Everything is either from reccy or from training knowledge. No manual verification of any individual row in v0.1.0.

6. **No comparison with existing datasets.** CFG Neurotech Market Atlas (271 companies) has overlap and should be cross-referenced to find (a) companies CFG has that reccy misses, (b) disagreements on founding year or sector.

## Open questions

- What counts as a "neurotech company"? reccy's inclusion criteria are not fully transparent. Medtronic (1949, deeply diversified) is in; is a general-purpose medical device company with one neuro product line neurotech? We currently defer to reccy's judgment.
- How should we handle spin-offs and acquisitions? E.g., if company A was acquired by B in 2020, does A still exist in the dataset? v0.1.0 keeps them as separate rows.
- How to version the raw snapshot over time? Current plan: new dated file in `data/raw/`, old ones stay. At some point we'll need a merge strategy.
