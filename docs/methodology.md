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
