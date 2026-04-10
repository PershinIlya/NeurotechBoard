#!/bin/sh
# Observable Framework data loader for funding_rounds.csv
set -eu
cat "$(dirname "$0")/../../../data/processed/funding_rounds.csv"
