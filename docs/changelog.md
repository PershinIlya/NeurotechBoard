# Changelog

All notable changes to the NeurotechBoard dataset are documented here. Format based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/). Dataset follows semver loosely (see README).

## [0.3.0] — 2026-04-10

Schema change: introduces **funding and company detail enrichment** from reccy.dev detail pages, scraped in a single browser pass across all 393 companies.

### Added

**`data/raw/reccy_detail_dump_2026-04-09.json`** — raw detail-page scrape: 390 companies (311 ok, 79 errors — timeouts and pages not yet loaded). Each ok record contains: `id`, `name`, `official_name`, `location_full`, `crunchbase_slug`, `description`, `funding_rounds` (array of `{type, date, amount_usd, lead_investors[]}`), `news_count`, `latest_news_date`, `partnerships`, `team_changes`, `awards`.

**`data/processed/funding_rounds.csv`** — one row per funding round: `company_name`, `reccy_id`, `round_type`, `date`, `amount_usd`, `lead_investors`. 868 rows covering 225 companies.

**18 new columns in `neurotech_enriched.csv`** (v0.3.0 schema):
- `reccy_id` — internal reccy company ID
- `official_name` — legal/official name from detail-page header
- `description` — first descriptive paragraph (~500 chars)
- `crunchbase_slug` — slug portion of the Crunchbase URL, if present
- `location_full` — city + state/country from detail-page header
- `total_funding_usd` — sum of disclosed round amounts (empty if none disclosed)
- `funding_round_count` — total rounds scraped (including undisclosed)
- `last_round_type` — round type of most-recent round by date
- `last_round_date` — announced date of most-recent round (YYYY-MM-DD)
- `investor_count` — unique lead-investor names across all rounds
- `has_undisclosed` — 1 if any round has null amount, else 0
- `news_count` — count from reccy News tab
- `latest_news_date` — approximate date of most-recent article (YYYY-MM-DD)
- `partnerships` — partnership-news count
- `team_changes` — team-change-news count
- `awards` — award-news count
- `detail_source` — `reccy_detail_2026-04-09`
- `detail_confidence` — `M` (reccy is a secondary aggregator)

**`src/build_funding.py`** — processes the raw JSON dump into the two output artefacts above. Match strategy: normalised name matching (lowercase, collapse whitespace) with substring fallback for partial names.

**8 new sanity tests:**
- `test_funding_rounds_csv_exists` / `test_funding_rounds_csv_columns`
- `test_v030_columns_present`
- `test_funding_round_count_non_negative`
- `test_last_round_date_format`
- `test_total_funding_non_negative`
- `test_detail_confidence_values`
- `test_known_funding_spot_checks` — Synchron, Neuralink, Precision Neuroscience, Blackrock Neurotech all have funding_round_count > 0

### Metrics (2026-04-10)

| Metric | Value |
|---|---|
| Companies with funding data | 225 / 311 ok (72%) |
| Total funding rounds | 868 |
| Companies with Crunchbase slug | 286 |
| Companies with news activity | 9 |
| Enriched CSV match rate | 310 / 393 (78.9%) |
| Scrape errors (timeouts / empty) | 79 |

**Notable funding data captured:**
- Neuralink: Series A–E + Secondary, most recent Series E ($650M, Dec 2025)
- Synchron: Series A–D, most recent Series D ($200M, Nov 2025)
- Science Corp: Series C ($230M, Mar 2026)
- ONWARD Medical: multiple Post-IPO rounds
- Saluda Medical: $530M+ across 8 rounds

### Known limitations

- 79 companies (20%) have scrape errors — mostly timeouts from rate limiting during the browser pass. A retry pass would recover most of these.
- `official_name` field is unreliable — the regex used during scraping produced single-character values for many rows (extracts the wrong DOM node). Treat as empty for now.
- `location_full` is populated for only a subset — reccy's detail pages don't always show city/country in the header.
- Match rate (78.9%) is below the 85% warning threshold but expected given the 79 error rows; the remaining 4 unmatched rows are name-normalisation mismatches.

## [0.2.0] — 2026-04-09

Schema change: introduces **lifecycle tracking** for all 393 companies, plus the first automated pass that populates it. This is the "are they still alive?" question — distinct from the "when were they born?" question that `founding_year` answers. See `docs/methodology.md` → "Lifecycle tracking" for the full design rationale.

### Added

**Four new CSV columns** (appended after `half_year`):

- `lifecycle_status` — enum: `active`, `dormant`, `dead_domain`, `acquired`, `merged`, `dissolved`, `pivoted`, `renamed`, `unknown`
- `lifecycle_as_of` — date of the most recent verifiable activity signal (YYYY-MM-DD)
- `lifecycle_confidence` — H / M / L / empty, same semantics as `founding_confidence`
- `lifecycle_source` — `auto:domain_check`, an explicit URL, or empty

**`src/check_domains.py`** — a stdlib-only concurrent domain checker that probes all 393 websites via DNS + HTTP, classifies each response, and writes `data/processed/domain_checks.json`. Finishes the full pass in under a minute. Handles:

- NXDOMAIN, SSL handshake errors, timeouts, connection refused
- CDN bot-blocking (Cloudflare / Akamai 401/403) via a browser-UA retry
- Parked domain detection (body markers: "for sale", "sedoparking", "afternic", "dan.com", "hugedomains", etc.)
- Path-only URLs with a root fallback (e.g. `meta.com/reality-labs` returns 404 on the path but 200 on `meta.com` → classified `active` with a `path_lost_root_ok` flag)
- Malformed `website` fields from reccy (values that aren't URLs at all) → honest `unknown` instead of false `dead_domain`

Script interface:
```
python3 src/check_domains.py              # full run, writes JSON
python3 src/check_domains.py --dry-run    # full run, summary only
python3 src/check_domains.py --only NAME  # probe one row for sanity-checking
```

**`data/processed/domain_checks.json`** — snapshot of the first full check run (2026-04-09T13:23Z). Git-tracked like the CSV; regenerate by re-running `check_domains.py`.

**`LIFECYCLE_OVERRIDES`** dict in `build_dataset.py` — manual override layer that takes precedence over auto-check results. Empty at v0.2.0 release; populated in later passes with `acquired / merged / dissolved / pivoted / renamed` statuses that the auto-checker structurally cannot emit.

**Three new sanity tests:**
- `test_lifecycle_status_values` — status must be in the taxonomy
- `test_lifecycle_invariants` — unknown→confidence empty; non-unknown→confidence H/M/L and source set
- `test_lifecycle_as_of_format` — YYYY-MM-DD or empty

### Metrics (first run, 2026-04-09)

| Status | Count | Confidence |
|---|---|---|
| `active` | 382 | 378 M + 4 L (bot-blocked) |
| `dead_domain` | 5 | all H |
| `dormant` | 4 | all M |
| `unknown` | 2 | — |

**dead_domain hits** (all eyeballed and confirmed true positives):
- Envoy Medical (envoymedical.com — domain exists for MX only, no A records)
- Deegtal, Xylo Bio, Ucat Inc. — genuinely NXDOMAIN
- "Spinally.com is for sale" — reccy scraped a parked-domain landing page's title as the company name; the parked marker correctly fired

**Bot-blocked (active L)** — NeuroPace, SPR Therapeutics, Arctop, Wise Neuro. All confirmed operating via other channels but their CDNs reject probes even with browser UAs.

**unknown** — "Stealth BCI Company" (no URL in reccy), "Bioness medical" (reccy stores the literal company name in the website column; flagged `malformed_website`).

### Known limitations

- `active` is a floor, not a ceiling. A live website ≠ a live company — some "active M" rows are probably dormant, acquired, or pivoted. High-confidence active status needs additional signals (recent funding, press, Crunchbase `Operating`) coming in v0.2.x.
- The checker cannot distinguish a long stealth period from dormancy.
- Acquired companies whose subsidiary pages are still live look "active" to us. Bioness should be `acquired (H) 2021-05-27` per the Bioventus acquisition, but until we populate `LIFECYCLE_OVERRIDES` manually it stays `unknown` (only because its reccy website field happens to be malformed — other acquired companies with live URLs currently show as `active M`).
- `lifecycle_as_of` is the **check run date**, not the last-known-alive date. Future runs will overwrite it for rows whose status didn't change.

### Roadmap

v0.2.x will layer a Crunchbase pass over the 187 URLs already in `SOURCES` to harvest explicit `Operating / Closed / Acquired` statuses. v0.3.0 will add `successor_entity` and populate top-50 acquisitions/mergers by hand.

## [0.1.3] — 2026-04-09

Third enrichment round. 90 new web-verified founding years across three parallel batches (~30 each), plus two unicode lookup-key bugs fixed.

### Added
- 90 web-verified founding_year entries spanning the late-alphabet companies (T-Z + early A) and remaining gaps. Notable additions:
  - Older entities: huMannity Medtec (1985, rebrand of Alfred Mann Foundation), Neuros Medical (2008), Neurosigma (2008), Cognision (2003), Vital Connect (2011), Velentium Medical (2012), Sooma Medical (2013), Atlas Wearables (2013), NeuroEM (2013), Wearable Devices Ltd (2014), Aural Analytics (2015), AURIMOD (2015), Arctop (2016), Openwater (2016), Nuro Corp (2016), Epineuron (2016), Tripp (2016).
  - Recent entities: Vivatronix (2025, India), Ability Neurotech (2025, Wyss Geneva spinoff), Axo Neurotech (2025), Cerevia Neurosciences (2025), Ohmbody (2025), Lyeons Neurotech (2024), NeuroX UK (2024), Nudge (2024), Avrwell (2024), Neurodiscovery AI (2023), Neurobionics (2023), Mintneuro (2023), Biotronik Neuro (2023), Ruten (2023), CNS Fund (2023), Aurenar (2023).
- New SOURCES URLs for all 90 entries plus a backfill for `bía neuroscience` (now web-verified at 2021/M).

### Fixed
- **ŌURA lookup bug** — the dict key was `'ŌURA'` (uppercase macron-O), but `lookup_founding` lowercases the input, and `'ŌURA'.lower() == 'ōura'` (lowercase macron). The key never matched. Renamed to `'ōura'`. The duplicate `'oura'` (plain Latin) entry remains as a no-op safety net.
- **Bía Neuroscience lookup bug** — same class of bug. Key was `'bia neuroscience'` (no accent) but raw name `'Bía Neuroscience'.lower() == 'bía neuroscience'`. Renamed and updated value from `(2019, 'L')` (training-knowledge guess) to `(2021, 'M')` (web-verified).
- **huMannity Medtec lookup bug** — third instance of the same class. Key was `'huMannity medtec'` (camelcase) but lookup was case-folded. Removed and re-added as `'humannity medtec'` with the agent's web-verified value `(1985, 'H')`. (1985 is the parent Alfred Mann Foundation founding year — see discrepancies.)

### Metrics
- **Founding year coverage:** 375/393 = 95.4% (+22.9 pp vs v0.1.2)
- **Provenance breakdown:** 188 `training_knowledge`, 187 URL-sourced, 18 empty
- Country coverage, regions, top countries unchanged from v0.1.2.
- Remaining 18 empty rows: SKIPs (no reliable source), parked-domain entities, stealth companies, plus Spiro Medical and the unnamed "Stealth BCI Company" row.

## [0.1.2] — 2026-04-09

Second enrichment round. 75 new web-verified founding years added across three parallel research batches of 30 companies each.

### Added
- 75 web-verified founding_year entries. Notable additions include:
  - Very new entities: Epia Neuro (2026), Gestala (2026), Temple/weartemple (2026), Lotus Neuro (2025 Insightec spinout), Karavela (2025), Syndeio Biosciences (2025), Clee Medical (2024), Hom Neuro (2024).
  - Mid-era: Monteris (1999), EvOn Medics (2013), DIXI Medical (1988), AlphaOmega (1993), Bioness (2004), NeuroNexus (2004), Stratus Neuro (2006), Eyetronic (2007), Holberg EEG (2009), Evoke Neuroscience (2009).
- 15 entries marked SKIP (no reliable source found): NeuroMind AGI, Egra, Neurawear, Insellar GmbH, Horizon Neuro, Kalmoa, TryHealium, Grey Matter Neuropsychology, FluentPlay, Fluent, Deegtal, StimCardio, Synapse TBI, Brain Training International, Spinally.com (parked domain).
- Expanded `docs/reccy_discrepancies.md` with 6 new entries from this round:
  - **Manava** — listed Switzerland, actually Milan, Italy
  - **Mave** — no country listed, actually Bengaluru, India
  - **Journey-frame** — listed USA, actually Cambridge, UK (parent Phantom Technology)
  - **EnterTech** — listed USA, actually Hangzhou, China
  - **Grey Matter Neuropsychology of New York** — listed Canada, actually NYC, USA
  - **Dusq** — listed as neurotech but is actually a sustainable baby clothing brand (probable reccy false positive, candidate for removal in v0.2.0)

### Metrics
- **Founding year coverage:** 285/393 = 72.5% (+19.1 pp vs v0.1.1)
- **Provenance breakdown:** 186 `training_knowledge`, 99 URL-sourced, 108 empty
- First year in the dataset expanded: now 1949–2026 (previously max 2025)
- Country coverage, regions, top countries unchanged from v0.1.1

## [0.1.1] — 2026-04-09

Patch release adding provenance tracking to founding years and first web-verified batch.

### Added
- New CSV column `founding_year_source`:
  - `'training_knowledge'` for legacy entries populated from model training knowledge.
  - Explicit URL (Crunchbase, company About page, Companies House, etc.) for web-verified entries.
- `SOURCES` dict in `src/build_dataset.py` holding per-company source URLs for web-verified founding years.
- 24 new founding-year entries from pilot web research batch (Optohive, Nexalin, Newrotex, Neurobell, Neurode, Neurofenix, Neurofenix, Neurinnov, Neumarker, neu Health, etc.).
- `docs/reccy_discrepancies.md` — log of cases where web research contradicts reccy listings (first entry: Neuromark is actually Neurent Medical, Ireland).

### Fixed
- Removed buggy substring-match fallback in `lookup_founding`. The fallback was producing false hits:
  - `Syndeio Biosciences` was being matched to `bios` (unrelated company, year 2015)
  - `Axo` was being matched to `muse by interaxon` (year 2007)
  - After pilot, `NeuroMind AGI` started matching `neuromind` (France, year 2022)
  - These 3 rows are now correctly empty pending real research.
- Added explicit keys `paradromics, inc.` and `株式会社lifescapes` to preserve the 2 legitimate partial matches that the fallback previously handled.

### Metrics
- **Founding year coverage:** 210/393 = 53.4% (+6.5 percentage points vs v0.1.0 headline; actual net: +22 verified − 2 false positives removed − 3 false positives removed post-pilot = +24 corrections over the 188 baseline)
- **Provenance breakdown:** 186 `training_knowledge`, 24 URL-sourced, 183 empty
- Country coverage, regions, and all other metrics unchanged from v0.1.0.

## [0.1.0] — 2026-04-09

Initial release. First pass at building an independent neurotech company timeline dataset.

### Added
- Scraped 393 companies from reccy.dev via React fiber tree extraction in a Chrome session (source: https://app.reccy.dev/companies).
- `data/raw/reccy_dump_2026-04-09.txt` — pipe-delimited immutable raw dump: `name|industries|headcount|lastFundingType|website|location|jobCount`.
- `data/processed/neurotech_enriched.csv` — enriched dataset with derived fields: country, region, primary_modality, application, invasiveness, headcount_bucket, decade, half_year, founding_year, founding_confidence.
- `src/build_dataset.py` — pipeline script (raw → processed csv) with embedded founding year knowledge base (~180 companies) and country/region heuristics.
- `src/build_xlsx.py` — optional xlsx generator for local viewing (8 sheets: README, companies, timeline_year, timeline_decade, geo, funding, sectors, methodology).
- `docs/methodology.md` — full methodology and limitations.
- `tests/test_sanity.py` — spot-checks on known companies.

### Metrics
- **Companies:** 393 (of 395 on reccy; 2 lost to dedup of duplicate rows)
- **Founding year coverage:** 188/393 = 47.8% (knowledge-based, not web-verified)
- **Country coverage:** 371/393 = 94.4%
- **Top countries:** USA 214, UK 27, Switzerland 18, Canada 15, France 14, Israel 14
- **Regions:** North America 229, Europe 100, MENA 15, Asia 14, Oceania 9

### Known limitations
- Founding year coverage <50%. Remaining ~205 companies need web enrichment to reach 85%+.
- Modality/application/invasiveness derived heuristically from reccy's `industries` tags, not manually verified.
- Dedup logic collapsed 2 duplicate rows in reccy (e.g., Gestala appeared twice).
- No financial metrics yet (total funding, valuation, headcount trend over time).
- No comparison with CFG Neurotech Market Atlas (271 companies) yet.

### Next candidates
- v0.2.0: Web-enriched founding years (target 85%+ coverage)
- v0.3.0: Manually verified modality/application for top 50 companies
- v0.4.0: Financial metrics layer (funding totals from Crunchbase/PitchBook-like sources)
- v1.0.0: Full verification pass, schema frozen
