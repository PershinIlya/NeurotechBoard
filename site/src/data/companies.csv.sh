#!/bin/sh
# Observable Framework data loader — exposes a STRIPPED version of
# neurotech_enriched.csv. Only columns required by the dashboard are
# kept; sensitive fields (description, crunchbase_slug, website,
# investor details, etc.) are dropped at build time so they never
# reach the deployed static site.
set -eu
python3 -c "
import csv, sys
keep = [
    'name', 'country', 'region', 'primary_modality',
    'last_funding_stage', 'founding_year', 'lifecycle_status',
    'total_funding_usd',
]
r = csv.DictReader(sys.stdin)
w = csv.DictWriter(sys.stdout, fieldnames=keep, extrasaction='ignore', lineterminator='\n')
w.writeheader()
for row in r:
    w.writerow(row)
" < "$(dirname "$0")/../../../data/processed/neurotech_enriched.csv"
