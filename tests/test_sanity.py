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
        'founding_confidence', 'founding_year_source', 'decade', 'half_year',
        # v0.2.0 lifecycle columns
        'lifecycle_status', 'lifecycle_as_of', 'lifecycle_confidence',
        'lifecycle_source',
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


def test_founding_year_source_invariants():
    """founding_year_source must be empty iff founding_year is empty.
    When set, must be 'training_knowledge' or an http(s) URL."""
    rows = load_rows()
    for r in rows:
        year = r['founding_year']
        src = r['founding_year_source']
        if not year:
            assert not src, f"{r['name']}: has source {src!r} but no year"
            continue
        assert src, f"{r['name']}: year {year} but no source"
        assert src == 'training_knowledge' or src.startswith(('http://', 'https://')), \
            f"{r['name']}: bad source {src!r}"


def test_lifecycle_status_values():
    """lifecycle_status must be in the fixed taxonomy."""
    valid = {'active', 'dormant', 'dead_domain', 'acquired', 'merged',
             'dissolved', 'pivoted', 'renamed', 'unknown'}
    for r in load_rows():
        assert r['lifecycle_status'] in valid, \
            f"{r['name']}: bad lifecycle_status {r['lifecycle_status']!r}"


def test_lifecycle_invariants():
    """Rules:
    - unknown status → confidence must be empty (we can't grade ignorance)
    - unknown status → source may be empty (never checked) OR
      'auto:domain_check' (checker ran but couldn't classify, e.g. no URL)
    - non-unknown status → confidence must be H/M/L and source must be set
    """
    for r in load_rows():
        status = r['lifecycle_status']
        if status == 'unknown':
            assert not r['lifecycle_confidence'], \
                f"{r['name']}: unknown status but confidence {r['lifecycle_confidence']!r}"
            assert r['lifecycle_source'] in ('', 'auto:domain_check'), \
                f"{r['name']}: unknown with unexpected source {r['lifecycle_source']!r}"
        else:
            assert r['lifecycle_confidence'] in {'H', 'M', 'L'}, \
                f"{r['name']}: bad confidence {r['lifecycle_confidence']!r}"
            assert r['lifecycle_source'], \
                f"{r['name']}: status {status} but no source"


def test_lifecycle_as_of_format():
    """lifecycle_as_of must be empty or match YYYY-MM-DD."""
    import re
    pattern = re.compile(r'^(\d{4}-\d{2}-\d{2})?$')
    for r in load_rows():
        assert pattern.match(r['lifecycle_as_of']), \
            f"{r['name']}: bad lifecycle_as_of {r['lifecycle_as_of']!r}"


def test_half_year_format():
    """half_year must be blank or match YYYY-H[12]."""
    import re
    rows = load_rows()
    pattern = re.compile(r'^(\d{4}-H[12])?$')
    for r in rows:
        assert pattern.match(r['half_year']), \
            f"{r['name']}: bad half_year {r['half_year']!r}"


# --- v0.3.0 funding / detail tests ---

ROUNDS_CSV_PATH = ROOT / 'data' / 'processed' / 'funding_rounds.csv'


def test_funding_rounds_csv_exists():
    """funding_rounds.csv must exist after build_funding.py runs."""
    assert ROUNDS_CSV_PATH.exists(), f"Missing {ROUNDS_CSV_PATH}"


def test_funding_rounds_csv_columns():
    with open(ROUNDS_CSV_PATH, newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        cols = set(reader.fieldnames or [])
    required = {'company_name', 'reccy_id', 'round_type', 'date', 'amount_usd', 'lead_investors'}
    assert required.issubset(cols), f"Missing columns in funding_rounds.csv: {required - cols}"


def test_v030_columns_present():
    """After build_funding.py, enriched CSV must have the new v0.3.0 columns."""
    rows = load_rows()
    required = {
        'reccy_id', 'official_name', 'description', 'crunchbase_slug',
        'location_full', 'total_funding_usd', 'funding_round_count',
        'last_round_type', 'last_round_date', 'investor_count',
        'has_undisclosed', 'news_count', 'latest_news_date',
        'detail_source', 'detail_confidence',
    }
    assert required.issubset(set(rows[0].keys())), \
        f"Missing v0.3.0 columns: {required - set(rows[0].keys())}"


def test_funding_round_count_non_negative():
    """funding_round_count must be a non-negative integer where present."""
    for r in load_rows():
        v = r.get('funding_round_count', '')
        if v != '':
            assert v.isdigit(), f"{r['name']}: bad funding_round_count {v!r}"


def test_last_round_date_format():
    """last_round_date must be empty or YYYY-MM-DD."""
    import re
    pattern = re.compile(r'^(\d{4}-\d{2}-\d{2})?$')
    for r in load_rows():
        v = r.get('last_round_date', '')
        assert pattern.match(v), f"{r['name']}: bad last_round_date {v!r}"


def test_total_funding_non_negative():
    """total_funding_usd must be empty or a non-negative integer."""
    for r in load_rows():
        v = r.get('total_funding_usd', '')
        if v != '':
            assert v.lstrip('-').isdigit() and int(v) >= 0, \
                f"{r['name']}: bad total_funding_usd {v!r}"


def test_detail_confidence_values():
    """detail_confidence must be H, M, L, or empty."""
    valid = {'H', 'M', 'L', ''}
    for r in load_rows():
        v = r.get('detail_confidence', '')
        assert v in valid, f"{r['name']}: bad detail_confidence {v!r}"


def test_known_funding_spot_checks():
    """Well-known companies that should have at least some funding data."""
    rows = load_rows()
    # Companies that definitely raised money and should show rounds
    funded = ['synchron', 'neuralink', 'precision neuroscience', 'blackrock neurotech']
    for name in funded:
        row = find(rows, name)
        if row is None:
            continue
        rc = row.get('funding_round_count', '')
        assert rc != '' and int(rc) > 0, \
            f"{name}: expected funding rounds, got funding_round_count={rc!r}"
