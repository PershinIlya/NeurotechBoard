"""
Sanity tests — spot-checks on known neurotech companies.

These tests protect against regressions when rebuilding the dataset.
If any of these fail, something broke in the pipeline (or a company
was removed from reccy). Run with: python -m pytest tests/
"""
import csv
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CSV_PATH = ROOT / 'data' / 'processed' / 'neurotech_enriched.csv'


def load_rows():
    with open(CSV_PATH, newline='', encoding='utf-8') as f:
        return list(csv.DictReader(f))


def find(rows, name_substring):
    """Find first row whose name contains the substring (case-insensitive)."""
    s = name_substring.lower()
    for r in rows:
        if s in r['name'].lower():
            return r
    return None


# --- Structural invariants ---

def test_csv_exists():
    assert CSV_PATH.exists(), f"Missing {CSV_PATH}"


def test_row_count():
    rows = load_rows()
    # v0.1.0 baseline. Update this when intentionally adding/removing rows.
    assert len(rows) == 393, f"Expected 393 rows, got {len(rows)}"


def test_required_columns():
    rows = load_rows()
    required = {
        'name', 'website', 'location', 'country', 'region', 'industries',
        'primary_modality', 'application', 'invasiveness', 'headcount_bucket',
        'last_funding_stage', 'live_jobs', 'founding_year',
        'founding_confidence', 'decade', 'half_year',
    }
    assert required.issubset(set(rows[0].keys())), \
        f"Missing columns: {required - set(rows[0].keys())}"


def test_founding_year_coverage_floor():
    """v0.1.0: at least 45% coverage. Should only go up."""
    rows = load_rows()
    with_year = sum(1 for r in rows if r['founding_year'])
    coverage = with_year / len(rows)
    assert coverage >= 0.45, f"Founding year coverage dropped to {coverage:.1%}"


def test_country_coverage_floor():
    rows = load_rows()
    with_country = sum(1 for r in rows if r['country'])
    coverage = with_country / len(rows)
    assert coverage >= 0.90, f"Country coverage dropped to {coverage:.1%}"


# --- Known company spot-checks ---
# Each entry: (name_substring, expected_fields_dict)
# Only assert on fields we are highly confident about.

KNOWN_COMPANIES = [
    ('neuralink',           {'founding_year': '2016', 'country': 'USA'}),
    ('synchron',            {'founding_year': '2016'}),
    ('paradromics',         {'founding_year': '2015', 'country': 'USA'}),
    ('blackrock neurotech', {'founding_year': '2008', 'country': 'USA'}),
    ('precision neuroscience', {'founding_year': '2021'}),
    ('neuropace',           {'founding_year': '1997', 'country': 'USA'}),
    ('medtronic',           {'founding_year': '1949'}),
    ('magstim',             {'founding_year': '1985'}),
    ('science corp',        {'founding_year': '2021'}),
]


def test_known_companies_present():
    rows = load_rows()
    for name, _ in KNOWN_COMPANIES:
        assert find(rows, name) is not None, f"Missing expected company: {name}"


def test_known_companies_fields():
    rows = load_rows()
    errors = []
    for name, expected in KNOWN_COMPANIES:
        row = find(rows, name)
        if row is None:
            continue  # caught by previous test
        for field, value in expected.items():
            if row[field] != value:
                errors.append(f"{name}: {field}={row[field]!r}, expected {value!r}")
    assert not errors, "Field mismatches:\n" + "\n".join(errors)


def test_founding_confidence_values():
    """Confidence must be H, M, L, or empty."""
    rows = load_rows()
    valid = {'H', 'M', 'L', ''}
    for r in rows:
        assert r['founding_confidence'] in valid, \
            f"{r['name']}: bad confidence {r['founding_confidence']!r}"


def test_half_year_format():
    """half_year must be blank or match YYYY-H[12]."""
    import re
    rows = load_rows()
    pattern = re.compile(r'^(\d{4}-H[12])?$')
    for r in rows:
        assert pattern.match(r['half_year']), \
            f"{r['name']}: bad half_year {r['half_year']!r}"
