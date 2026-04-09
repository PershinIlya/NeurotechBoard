# Changelog

All notable changes to the NeurotechBoard dataset are documented here. Format based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/). Dataset follows semver loosely (see README).

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
