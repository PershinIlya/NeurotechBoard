#!/bin/sh
# Observable Framework data loader — exposes the neurotech_enriched.csv
# from the main dataset as site data. Runs at build time, output is
# captured to stdout and served as /data/companies.csv.
#
# POSIX sh only: Observable Framework invokes .sh loaders through
# /bin/sh (dash on Ubuntu runners), which ignores the shebang and
# does not support bash-only options like "set -o pipefail".
# A bare `cat` is enough — if the path is wrong, `cat` returns
# non-zero and the loader fails cleanly.
set -eu
cat "$(dirname "$0")/../../../data/processed/neurotech_enriched.csv"
