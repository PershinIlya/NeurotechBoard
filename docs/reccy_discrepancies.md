# reccy.dev discrepancies

Cases where web research contradicts the reccy.dev listing. We **keep reccy's values** in the CSV as-is (reccy is the authoritative source), but track the disagreement here so we can revisit during v0.2.0+.

## Country / entity mismatches

### Neuromark — listed as USA, actually Ireland (Neurent Medical)

- **reccy says:** Neuromark, USA
- **Web research finds:** "Neuromark" is a product, not a company. The developer is **Neurent Medical**, founded 2015 in Galway, Ireland.
- **Source:** https://www.crunchbase.com/organization/neurent-medical
- **Decision for v0.1.x:** founding_year = 2015 (confidence H, source: Crunchbase). `country` left as USA per reccy. Flagged here for resolution in v0.2.0.
- **Open question:** Should we rename rows in our CSV to match legal entity, or preserve reccy's product-based naming?

## v0.1.0 quality fixes (post-release)

Bugs found in the hardcoded FOUNDING dict's partial-match fallback during pilot research:

| Company | v0.1.0 matched to | v0.1.0 year | Correct |
|---|---|---|---|
| Syndeio Biosciences | `bios` (wrong company) | 2015 (M) | unknown — removed |
| Axo | `muse by interaxon` (wrong) | 2007 (H) | unknown — removed |
| NeuroMind AGI | `neuromind` (France, wrong) | 2022 (M) | unknown — kept as SKIP |

Fix: `lookup_founding` now requires exact key match. Paradromics, Inc. and 株式会社LIFESCAPES added as explicit keys so they still resolve correctly.
