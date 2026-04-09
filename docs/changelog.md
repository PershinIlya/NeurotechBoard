# Changelog

All notable changes to the NeurotechBoard dataset are documented here. Format based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/). Dataset follows semver loosely (see README).

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
