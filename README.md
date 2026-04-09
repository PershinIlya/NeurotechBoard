# NeurotechBoard

Tracking the emergence and trajectory of neurotech companies over time. Source data pulled from [reccy.dev](https://app.reccy.dev/companies), enriched with founding years, geography, modality, and application taxonomy.

## Current state (v0.1.3)

- **393 companies** extracted from reccy.dev (out of 395 listed; 2 lost to dedup).
- **Founding year coverage: 95.4%** (375/393). 188 from training knowledge, 187 web-verified across five batches; 18 empty (SKIPs / no reliable source).
- **Country coverage: 94.4%** (371/393).
- `founding_year_source` column: `'training_knowledge'` for legacy entries, explicit URL for web-verified entries.
- Derived fields: modality, application, invasiveness, region, decade, half_year.

## Repo layout

```
.
├── data/
│   ├── raw/                # immutable source dumps, never edited
│   └── processed/          # single source of truth: neurotech_enriched.csv
├── src/
│   ├── build_dataset.py    # raw dump → processed csv
│   └── build_xlsx.py       # processed csv → local xlsx (for viewing)
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
