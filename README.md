# NeurotechBoard

Tracking the emergence and trajectory of neurotech companies over time. Source data pulled from [reccy.dev](https://app.reccy.dev/companies), enriched with founding years, geography, modality, and application taxonomy.

## Current state (v0.3.2)

- **393 companies** extracted from reccy.dev (out of 395 listed; 2 lost to dedup).
- **Founding year coverage: 95.4%** (375/393). 188 from training knowledge, 187 web-verified across five batches; 18 empty (SKIPs / no reliable source).
- **Country coverage: 94.4%** (371/393).
- **Lifecycle coverage: 99.5%** (391/393). First automated pass via `src/check_domains.py`: 382 `active` (378 M + 4 L bot-blocked), 5 `dead_domain` (H), 4 `dormant` (M), 2 `unknown`.
- **Funding data: 289 companies, 1139 rounds.** Full re-scrape of all 366 ok companies (2026-04-10). 64 companies newly gained funding rounds (0→n). 24 permanent no-profile errors unchanged.
- **`official_name` bug fixed** — single-character extraction bug corrected for 288/366 companies. All matched rows now have proper legal names.
- **Location coverage: 288 companies** have `location_full` (city + country from reccy detail header), up from ~85.
- **Crunchbase slug coverage: 365/366 ok companies** (99.7%), up from 289.
- **CSV match rate: 91.6%** (360/393), up from 79.6%. Fixed by id-based matching + backfilling missing `name` fields.
- `founding_year_source` column: `'training_knowledge'` for legacy entries, explicit URL for web-verified entries.
- Derived fields: modality, application, invasiveness, region, decade, half_year.

## Repo layout

```
.
├── data/
│   ├── raw/                # immutable source dumps, never edited
│   └── processed/          # single source of truth: neurotech_enriched.csv
│                           # + domain_checks.json (auto lifecycle data)
├── src/
│   ├── build_dataset.py    # raw dump → processed csv
│   ├── build_funding.py    # reccy detail dump → funding_rounds.csv + enriched csv patch
│   ├── build_xlsx.py       # processed csv → local xlsx (for viewing)
│   ├── check_domains.py    # probes websites → domain_checks.json (lifecycle)
│   └── patch_v032.py       # merges live re-scrape corrections into stored dump
├── docs/
│   ├── methodology.md
│   └── changelog.md
├── tests/
│   └── test_sanity.py      # spot-checks on known companies
├── local/                  # git-ignored, personal artifacts (xlsx, exports)
├── requirements.txt
└── README.md
```

## Source of truth

`data/processed/neurotech_enriched.csv` is **the** dataset. Everything else is derived or personal.

- `data/raw/` is immutable — new scrapes create new dated files, old ones stay.
- `local/neurotech_dataset.xlsx` is a personal viewing artifact, regenerated from csv, not versioned.

## Reproducing the pipeline

```bash
pip install -r requirements.txt

# Build enriched csv from raw dump
python src/build_dataset.py

# (Optional) Refresh lifecycle data by re-probing all websites
python src/check_domains.py     # ~60s, writes data/processed/domain_checks.json

# Add funding data (requires reccy detail dump in data/raw/)
python src/build_funding.py

# (Optional) Regenerate local xlsx for viewing
python src/build_xlsx.py

# Run sanity tests
python -m pytest tests/
```

## Versioning

Dataset versions are tagged in git. See `docs/changelog.md` for what changed between versions. To check out a specific version:

```bash
git checkout v0.1.0
```

Semantic versioning applied loosely:
- **patch** (v0.1.x) — fixes to individual rows, no schema changes
- **minor** (v0.x.0) — new enrichment passes, added columns, taxonomy updates
- **major** (v1.0.0) — first fully-verified release, schema stable

## Known limitations

See `docs/methodology.md` for the full list. Top three:

1. Founding years cover less than half the dataset and come from training knowledge, not primary sources.
2. Modality/application fields are derived heuristically from reccy's `industries` tags, not manually verified.
3. 2 companies lost during dedup vs reccy's headline 395.
