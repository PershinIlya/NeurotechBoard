"""
patch_v032.py  —  v0.3.2 data patch

Applies corrections from the full live re-scrape (live_all_deduped.json) to the
stored raw dump (reccy_detail_dump_2026-04-09.json), producing a patched dump
that build_funding.py will then use to regenerate the processed CSV.

Patch rules (conservative — only fill gaps, never destroy good data):
  official_name  : stored len ≤ 1  → replace with live value if live len > 1
  location_full  : stored empty     → fill from live if non-empty
  crunchbase_slug: stored empty     → fill from live if non-empty
  description    : stored len ≤ 5  → fill from live if non-empty (live is 150-char excerpt)
  funding_rounds : stored count = 0 AND live count > 0  →  add live rounds
                   (stored count > 0  →  unchanged; stored data has higher recall)

Live rounds format:  {"t": "RoundType", "a": amount_or_null}
Stored rounds format: {"type": "...", "date": "", "amount_usd": ..., "lead_investors": []}

Output:
  data/raw/reccy_detail_dump_v032_patched.json   (new patched dump)

Usage:
    python src/patch_v032.py
    python src/patch_v032.py --live /path/to/live.json
    python src/patch_v032.py --dry-run
"""

import argparse
import json
import copy
from pathlib import Path

ROOT       = Path(__file__).resolve().parent.parent
STORED     = ROOT / "data" / "raw" / "reccy_detail_dump_2026-04-09.json"
LIVE_JSON  = Path("/sessions/sleepy-dazzling-feynman/live_all_deduped.json")
OUT_DUMP   = ROOT / "data" / "raw" / "reccy_detail_dump_v032_patched.json"


def convert_live_round(lr: dict) -> dict:
    """Convert live compact round {t, a} → stored round format."""
    amt = lr.get("a")
    if isinstance(amt, float):
        amt = int(round(amt))  # scraper sometimes produces float due to JS arithmetic
    return {
        "type":         lr.get("t") or "",
        "date":         "",
        "amount_usd":   amt,
        "lead_investors": [],
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--live", type=Path, default=LIVE_JSON)
    parser.add_argument("--stored", type=Path, default=STORED)
    parser.add_argument("--out", type=Path, default=OUT_DUMP)
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    print(f"Loading stored dump: {args.stored}")
    with open(args.stored, encoding="utf-8") as f:
        stored_data = json.load(f)

    print(f"Loading live data:   {args.live}")
    with open(args.live, encoding="utf-8") as f:
        live_data = json.load(f)

    # Index live records by id
    live_by_id = {r["id"]: r for r in live_data}
    print(f"  stored: {len(stored_data)} records")
    print(f"  live:   {len(live_data)} records")

    # Counters
    n_official_name  = 0
    n_location       = 0
    n_slug           = 0
    n_description    = 0
    n_rounds_added   = 0
    n_ok             = 0
    n_err            = 0

    patched = []
    for rec in stored_data:
        if rec.get("_err"):
            n_err += 1
            patched.append(copy.deepcopy(rec))
            continue

        n_ok += 1
        r = copy.deepcopy(rec)
        lid = r.get("id", "")
        live = live_by_id.get(lid)

        # --- ensure name field exists (52 records use only official_name) ---
        if not r.get("name", "").strip():
            r["name"] = r.get("official_name", "") or (live.get("on", "") if live else "")

        if live is None:
            # No live match — keep as-is
            patched.append(r)
            continue

        # --- official_name ---
        stored_on = r.get("official_name", "")
        live_on   = live.get("on", "")
        if len(stored_on) <= 1 and len(live_on) > 1:
            r["official_name"] = live_on
            n_official_name += 1

        # --- location_full ---
        stored_lf = r.get("location_full", "").strip()
        live_lf   = (live.get("lf") or "").strip()
        if not stored_lf and live_lf:
            r["location_full"] = live_lf
            n_location += 1

        # --- crunchbase_slug ---
        stored_cs = r.get("crunchbase_slug", "").strip()
        live_cs   = (live.get("cs") or "").strip()
        if not stored_cs and live_cs:
            r["crunchbase_slug"] = live_cs
            n_slug += 1

        # --- description ---
        stored_desc = r.get("description", "").strip()
        live_desc   = (live.get("desc") or "").strip()
        if len(stored_desc) <= 5 and live_desc:
            r["description"] = live_desc
            n_description += 1

        # --- funding_rounds ---
        stored_rounds = r.get("funding_rounds") or []
        live_rounds   = live.get("fr") or []
        live_frc      = live.get("frc", 0)
        if len(stored_rounds) == 0 and live_frc > 0 and live_rounds:
            r["funding_rounds"] = [convert_live_round(lr) for lr in live_rounds]
            n_rounds_added += 1

        patched.append(r)

    print(f"\nPatch summary:")
    print(f"  ok records processed  : {n_ok}")
    print(f"  error records skipped : {n_err}")
    print(f"  official_name fixed   : {n_official_name}")
    print(f"  location_full filled  : {n_location}")
    print(f"  crunchbase_slug filled: {n_slug}")
    print(f"  description filled    : {n_description}")
    print(f"  rounds added (0→n)    : {n_rounds_added}")

    if args.dry_run:
        print("\n(dry-run — no files written)")
        return

    with open(args.out, "w", encoding="utf-8") as f:
        json.dump(patched, f, ensure_ascii=False, indent=2)
    print(f"\nWrote patched dump → {args.out}")


if __name__ == "__main__":
    main()
