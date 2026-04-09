# reccy.dev discrepancies

Cases where web research contradicts the reccy.dev listing. We **keep reccy's values** in the CSV as-is (reccy is the authoritative source), but track the disagreement here so we can revisit during v0.2.0+.

## Country / entity mismatches

### Neuromark — listed as USA, actually Ireland (Neurent Medical)

- **reccy says:** Neuromark, USA
- **Web research finds:** "Neuromark" is a product, not a company. The developer is **Neurent Medical**, founded 2015 in Galway, Ireland.
- **Source:** https://www.crunchbase.com/organization/neurent-medical
- **Decision for v0.1.x:** founding_year = 2015 (confidence H, source: Crunchbase). `country` left as USA per reccy. Flagged here for resolution in v0.2.0.
- **Open question:** Should we rename rows in our CSV to match legal entity, or preserve reccy's product-based naming?

### Manava — listed as Switzerland, actually Italy

- **reccy says:** Manava, Switzerland
- **Web finds:** Milan, Italy (spinal cord BCI, founded 2022)
- **Source:** https://www.crunchbase.com/organization/manava-plus
- **Decision:** country kept as Switzerland per reccy, founding_year = 2022 (H).

### Mave — listed with no country, actually India

- **reccy says:** Mave, no country
- **Web finds:** Bengaluru, India (founded 2023)
- **Source:** https://www.crunchbase.com/organization/mave-health
- **Decision:** country left blank (not in COUNTRY_MAP); founding_year = 2023 (H). To backfill in country enrichment pass.

### Journey-frame — listed as USA, actually UK

- **reccy says:** Journey-frame, USA
- **Web finds:** Product of Phantom Technology, Cambridge UK (parent founded 2019)
- **Source:** https://www.crunchbase.com/organization/phantom-technology
- **Decision:** country kept as USA per reccy, founding_year = 2019 (M).

### EnterTech, Inc — listed as USA, actually China

- **reccy says:** EnterTech, Inc, USA
- **Web finds:** Hangzhou, China (Flowtime headband, founded 2014)
- **Source:** https://global.chinadaily.com.cn/a/202512/11/WS693a2979a310d6866eb2e135.html
- **Decision:** country kept as USA per reccy, founding_year = 2014 (M).

### Grey Matter Neuropsychology of New York — listed as Canada, actually NYC USA

- **reccy says:** country Canada
- **Web finds:** NYC-based practice (no reliable founding year found)
- **Decision:** country kept as Canada per reccy, founding_year SKIP.

### Dusq — listed as neurotech, actually sustainable clothing

- **reccy says:** Dusq, neurotech company in Noord-Holland
- **Web finds:** Dusq is a sustainable baby clothing / lifestyle brand, not neurotech at all.
- **Source:** https://dusq.nl/en/about/
- **Decision:** founding_year set to 2018 (M) per their About page, but this row should probably be removed from the dataset entirely in v0.2.0. Logged here as an entity-type mismatch, not just a field mismatch.

## v0.1.0 quality fixes (post-release)

Bugs found in the hardcoded FOUNDING dict's partial-match fallback during pilot research:

| Company | v0.1.0 matched to | v0.1.0 year | Correct |
|---|---|---|---|
| Syndeio Biosciences | `bios` (wrong company) | 2015 (M) | unknown — removed |
| Axo | `muse by interaxon` (wrong) | 2007 (H) | unknown — removed |
| NeuroMind AGI | `neuromind` (France, wrong) | 2022 (M) | unknown — kept as SKIP |

Fix: `lookup_founding` now requires exact key match. Paradromics, Inc. and 株式会社LIFESCAPES added as explicit keys so they still resolve correctly.
