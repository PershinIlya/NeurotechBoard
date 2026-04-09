#!/usr/bin/env bash
# Observable Framework data loader — exposes the neurotech_enriched.csv
# from the main dataset as site data. Runs at build time, output is
# captured to stdout and served as /data/companies.csv.
#
# The loader's cwd is the observable framework project root (./site),
# so the path to the dataset is ../data/processed/...
set -euo pipefail
cat "$(dirname "$0")/../../../data/processed/neurotech_enriched.csv"
