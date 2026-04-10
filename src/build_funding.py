"""
build_funding.py  —  v0.3.0

Reads  data/raw/reccy_detail_dump_2026-04-09.json  (scraped from reccy.dev
detail pages) and produces:

  data/processed/funding_rounds.csv        — one row per funding round
  data/processed/neurotech_enriched.csv    — patched in-place with new columns:

    reccy_id             internal reccy company ID
    official_name        legal name from detail-page header  (e.g. "Synchron, Inc.")
    description          first descriptive paragraph (~500 chars)
    crunchbase_slug      slug portion of the Crunchbase URL, if present
    location_full        city + state/country from detail-page header
    total_funding_usd    sum of disclosed round amounts (NULL if none disclosed)
    funding_round_count  total rounds scraped (including undisclosed)
    last_round_type      roundType of most-recent round by date
    last_round_date      announcedOn of most-recent round  (YYYY-MM-DD)
    investor_count       unique lead-investor names across all rounds
    has_undisclosed      1 if any round has amountUsd=null, else 0
    news_count           count from reccy News tab
    latest_news_date     approximate date of most-recent article  (YYYY-MM-DD)
    partnerships         partnership-news count
    team_changes         team-change-news count
    awards               award-news count
    detail_source        always  "reccy_detail_2026-04-09"
    detail_confidence    always  "M"  (reccy is a secondary aggregator)

Usage:
    python src/build_funding.py
    python src/build_funding.py --dump data/raw/reccy_detail_dump_2026-04-09.json
"""

import argparse
import csv
import json
import re
from pathlib import Path
from collections import defaultdict

ROOT = Path(__file__).resolve().parent.parent
DUMP_DEFAULT = ROOT / "data" / "raw" / "reccy_detail_dump_2026-04-09.json"
ENRICHED_CSV = ROOT / "data" / "processed" / "neurotech_enriched.csv"
ROUNDS_CSV   = ROOT / "data" / "processed" / "funding_rounds.csv"

DETAIL_SOURCE     = "reccy_detail_2026-04-09"
DETAIL_CONFIDENCE = "M"

# ---------------------------------------------------------------------------
# helpers
# ---------------------------------------------------------------------------

def _norm(s: str) -> str:
    """Lowercase + collapse whitespace — used for fuzzy name matching."""
    return re.sub(r"\s+", " ", (s or "").strip().lower())


def _parse_amount(amount) -> int | None:
    if amount is None:
        return None
    try:
        return int(amount)
    except (TypeError, ValueError):
        return None


def load_dump(path: Path) -> list[dict]:
    with open(path, encoding="utf-8") as f:
        raw = json.load(f)
    # Accept either a plain list or {"results": [...]}
    if isinstance(raw, list):
        return raw
    if isinstance(raw, dict) and "results" in raw:
        return raw["results"]
    raise ValueError(f"Unexpected dump format in {path}")


def build_company_index(rows: list[dict]) -> dict[str, dict]:
    """Return normalised-name → row dict.  Last writer wins for duplicates."""
    idx: dict[str, dict] = {}
    for r in rows:
        key = _norm(r.get("name") or "")
        if key:
            idx[key] = r
    return idx


# ---------------------------------------------------------------------------
# aggregate per-company fields from raw rounds list
# ---------------------------------------------------------------------------

def aggregate_funding(rounds: list[dict]) -> dict:
    """Compute scalar summary from a list of round dicts."""
    if not rounds:
        return dict(
            total_funding_usd=None,
            funding_round_count=0,
            last_round_type="",
            last_round_date="",
            investor_count=0,
            has_undisclosed=0,
        )

    # sort by date descending (missing dates sort to end)
    def _date_key(r):
        return r.get("date") or "0000-00-00"

    sorted_rounds = sorted(rounds, key=_date_key, reverse=True)
    last = sorted_rounds[0]

    disclosed = [r["amount_usd"] for r in rounds if r.get("amount_usd") is not None]
    total = sum(disclosed) if disclosed else None

    all_investors: set[str] = set()
    for r in rounds:
        for inv in r.get("lead_investors") or []:
            s = str(inv).strip()
            if s:
                all_investors.add(s)

    has_undisclosed = int(any(r.get("amount_usd") is None for r in rounds))

    return dict(
        total_funding_usd=total,
        funding_round_count=len(rounds),
        last_round_type=last.get("type") or "",
        last_round_date=last.get("date") or "",
        investor_count=len(all_investors),
        has_undisclosed=has_undisclosed,
    )


# ---------------------------------------------------------------------------
# write funding_rounds.csv
# ---------------------------------------------------------------------------

def write_rounds_csv(rows: list[dict], out_path: Path) -> int:
    """Write one row per funding round; return total row count written."""
    fieldnames = [
        "company_name", "reccy_id",
        "round_type", "date", "amount_usd", "lead_investors",
    ]
    count = 0
    with open(out_path, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fieldnames)
        w.writeheader()
        for company in rows:
            if company.get("_err"):
                continue
            for rnd in company.get("funding_rounds") or []:
                investors_str = "; ".join(rnd.get("lead_investors") or [])
                w.writerow(dict(
                    company_name=company.get("name", ""),
                    reccy_id=company.get("id", ""),
                    round_type=rnd.get("type", ""),
                    date=rnd.get("date", ""),
                    amount_usd=rnd.get("amount_usd", ""),
                    lead_investors=investors_str,
                ))
                count += 1
    return count


# ---------------------------------------------------------------------------
# patch neurotech_enriched.csv
# ---------------------------------------------------------------------------

NEW_COLS = [
    "reccy_id",
    "official_name",
    "description",
    "crunchbase_slug",
    "location_full",
    "total_funding_usd",
    "funding_round_count",
    "last_round_type",
    "last_round_date",
    "investor_count",
    "has_undisclosed",
    "news_count",
    "latest_news_date",
    "partnerships",
    "team_changes",
    "awards",
    "detail_source",
    "detail_confidence",
]


def patch_enriched_csv(
    csv_path: Path,
    company_index: dict[str, dict],
) -> tuple[int, int]:
    """Patch enriched CSV with new columns.  Returns (matched, total) counts."""
    with open(csv_path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        existing_cols = reader.fieldnames or []
        rows = list(reader)

    # Build output fieldnames: existing cols + any NEW_COLS not already present
    out_cols = list(existing_cols)
    for col in NEW_COLS:
        if col not in out_cols:
            out_cols.append(col)

    matched = 0
    for row in rows:
        key = _norm(row.get("name") or "")
        detail = company_index.get(key)

        if detail is None:
            # Try partial / alias matching: strip common suffixes
            for k in company_index:
                if key and (key in k or k in key):
                    detail = company_index[k]
                    break

        if detail and not detail.get("_err"):
            matched += 1
            rounds = detail.get("funding_rounds") or []
            agg = aggregate_funding(rounds)

            row["reccy_id"]          = detail.get("id", "")
            row["official_name"]     = detail.get("official_name", "")
            row["description"]       = detail.get("description", "")
            row["crunchbase_slug"]   = detail.get("crunchbase_slug", "")
            row["location_full"]     = detail.get("location_full", "")
            row["total_funding_usd"] = "" if agg["total_funding_usd"] is None else agg["total_funding_usd"]
            row["funding_round_count"] = agg["funding_round_count"]
            row["last_round_type"]   = agg["last_round_type"]
            row["last_round_date"]   = agg["last_round_date"]
            row["investor_count"]    = agg["investor_count"]
            row["has_undisclosed"]   = agg["has_undisclosed"]
            row["news_count"]        = detail.get("news_count", "")
            row["latest_news_date"]  = detail.get("latest_news_date", "")
            row["partnerships"]      = detail.get("partnerships", "")
            row["team_changes"]      = detail.get("team_changes", "")
            row["awards"]            = detail.get("awards", "")
            row["detail_source"]     = DETAIL_SOURCE
            row["detail_confidence"] = DETAIL_CONFIDENCE
        else:
            # Ensure new columns exist (empty) for unmatched rows
            for col in NEW_COLS:
                row.setdefault(col, "")

    with open(csv_path, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=out_cols)
        w.writeheader()
        w.writerows(rows)

    return matched, len(rows)


# ---------------------------------------------------------------------------
# main
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--dump", type=Path, default=DUMP_DEFAULT,
        help="Path to raw JSON dump from reccy.dev detail scrape",
    )
    parser.add_argument(
        "--dry-run", action="store_true",
        help="Parse and report without writing any files",
    )
    args = parser.parse_args()

    if not args.dump.exists():
        print(f"ERROR: dump not found at {args.dump}")
        print("Run the browser scraper first, then save the output to that path.")
        raise SystemExit(1)

    print(f"Loading dump from {args.dump} …")
    rows = load_dump(args.dump)
    ok    = [r for r in rows if not r.get("_err")]
    errs  = [r for r in rows if r.get("_err")]
    print(f"  {len(rows)} total rows  ({len(ok)} ok, {len(errs)} errors)")

    # --- stats --
    with_rounds    = [r for r in ok if r.get("funding_rounds")]
    total_rounds   = sum(len(r.get("funding_rounds") or []) for r in ok)
    with_news      = [r for r in ok if r.get("news_count", 0) > 0]
    with_cb        = [r for r in ok if r.get("crunchbase_slug")]

    print(f"  funding_rounds present : {len(with_rounds)} companies, {total_rounds} rounds total")
    print(f"  with news              : {len(with_news)} companies")
    print(f"  crunchbase slug found  : {len(with_cb)} companies")
    if errs:
        print(f"  errors                 : {[(e['name'], e['_err']) for e in errs[:10]]}")

    if args.dry_run:
        print("\n(dry-run — no files written)")
        return

    # --- write rounds CSV ---
    n_rounds = write_rounds_csv(rows, ROUNDS_CSV)
    print(f"\nWrote {n_rounds} rows → {ROUNDS_CSV.relative_to(ROOT)}")

    # --- patch enriched CSV ---
    company_index = build_company_index(ok)
    matched, total = patch_enriched_csv(ENRICHED_CSV, company_index)
    pct = matched / total * 100 if total else 0
    print(f"Patched enriched CSV: {matched}/{total} rows matched ({pct:.1f}%) → {ENRICHED_CSV.relative_to(ROOT)}")

    if matched < total * 0.85:
        print("WARNING: match rate below 85% — check name normalisation in company_index")


if __name__ == "__main__":
    main()
