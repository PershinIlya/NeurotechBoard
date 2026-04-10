#!/bin/sh
# Observable Framework data loader for funding_rounds.csv.
# Only columns used by the dashboard are kept; lead_investors,
# round_type, and reccy_id are stripped at build time.
set -eu
python3 -c "
import csv, sys
keep = ['company_name', 'date', 'amount_usd', 'round_type']
r = csv.DictReader(sys.stdin)
w = csv.DictWriter(sys.stdout, fieldnames=keep, extrasaction='ignore', lineterminator='\n')
w.writeheader()
for row in r:
    w.writerow(row)
" < "$(dirname "$0")/../../../data/processed/funding_rounds.csv"
