#!/usr/bin/env python3
"""
Domain-check pass for lifecycle tracking (v0.2.0 step 1).

Reads the reccy raw dump, concurrently probes each company's website, and
classifies the result into a lifecycle status tier (active / dormant /
dead_domain / unknown) with an honest confidence tier.

Output: data/processed/domain_checks.json
Schema: see docs/methodology.md → "Lifecycle tracking".

Stdlib only — no new dependency. Uses urllib + ThreadPoolExecutor for ~20
concurrent probes, so the full 393-row pass finishes in roughly a minute.

Usage:
    python3 src/check_domains.py                 # full run, writes JSON
    python3 src/check_domains.py --dry-run       # full run, summary only
    python3 src/check_domains.py --only NAME     # probe one row, no write

The script never raises on a bad URL — every per-row failure is caught and
encoded as a flag, so one broken site can't derail the whole pass.
"""
from __future__ import annotations

import argparse
import json
import socket
import ssl
import sys
import time
import urllib.error
import urllib.request
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parent.parent
RAW = ROOT / 'data' / 'raw' / 'reccy_dump_2026-04-09.txt'
OUT = ROOT / 'data' / 'processed' / 'domain_checks.json'

SCRIPT_VERSION = '0.2.0'
USER_AGENT = (
    f'NeurotechBoard-DomainCheck/{SCRIPT_VERSION} '
    '(+https://github.com/PershinIlya/NeurotechBoard)'
)
# Fallback UA used only on 401/403 retry — many CDNs (Cloudflare, Akamai) block
# unrecognized bot UAs by default. A real browser UA sails through those and
# lets us distinguish "dead" from "bot-blocked".
BROWSER_UA = (
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) '
    'AppleWebKit/537.36 (KHTML, like Gecko) '
    'Chrome/124.0.0.0 Safari/537.36'
)
TIMEOUT = 8  # seconds per HTTP attempt
MAX_WORKERS = 20
BODY_CAP = 10_000  # bytes of body we actually scan

PARKED_MARKERS = [
    'buy this domain',
    'domain is for sale',
    'this domain is for sale',
    'domain for sale',
    'sedoparking',
    'afternic',
    'hugedomains',
    'undeveloped',
    'namebright',
    'bodis',
    'parkingcrew',
    'domainmarket',
    'dan.com',
    'inquire about this domain',
    'make an offer',
]


def parse_raw(path: Path) -> list[tuple[str, str]]:
    """Return list of (name, website) tuples from the reccy dump."""
    out = []
    with path.open() as f:
        for line in f:
            line = line.rstrip('\n')
            if not line:
                continue
            parts = line.split('|')
            if len(parts) < 7:
                parts += [''] * (7 - len(parts))
            name = parts[0].strip()
            website = parts[4].strip()
            out.append((name, website))
    return out


def normalize_url(raw: str) -> Optional[str]:
    """Turn reccy's bare domain into a URL. Return None if empty/invalid.

    Rejects obviously-malformed values: empty, whitespace, no dot, or a space
    in the host portion (reccy sometimes stores the company name verbatim in
    the website column — e.g. "bioness medical" — which is not a URL at all).
    """
    if not raw:
        return None
    raw = raw.strip()
    if not raw:
        return None
    if raw.startswith(('http://', 'https://')):
        candidate = raw
    else:
        candidate = 'https://' + raw
    host = extract_host(candidate)
    if not host or '.' not in host or ' ' in host:
        return None
    return candidate


def root_url(url: str) -> str:
    """Return just scheme://host of a URL (strip path, query, fragment)."""
    p = urlparse(url)
    return f'{p.scheme}://{p.netloc}'


def extract_host(url: str) -> str:
    try:
        return urlparse(url).hostname or ''
    except Exception:
        return ''


def extract_title(body: bytes) -> str:
    """Cheap title extraction — first <title>…</title> in the first ~10 KB."""
    try:
        text = body[:BODY_CAP].decode('utf-8', errors='replace')
    except Exception:
        return ''
    low = text.lower()
    i = low.find('<title')
    if i < 0:
        return ''
    j = low.find('>', i)
    if j < 0:
        return ''
    k = low.find('</title>', j)
    if k < 0:
        return ''
    return text[j + 1:k].strip()[:200]


def parked_flag(body: bytes, title: str) -> bool:
    try:
        blob = (title + ' ' + body[:BODY_CAP].decode('utf-8', errors='replace')).lower()
    except Exception:
        blob = title.lower()
    return any(m in blob for m in PARKED_MARKERS)


def dns_check(host: str) -> bool:
    """True if the host resolves, False on NXDOMAIN / other DNS failure."""
    if not host:
        return False
    try:
        socket.gethostbyname(host)
        return True
    except (socket.gaierror, socket.herror):
        return False
    except Exception:
        return False


def http_get(url: str, user_agent: str = USER_AGENT) -> dict:
    """Perform a single HTTP GET. Return a dict with the outcome.

    Never raises. On any failure returns {'error': <short_tag>}.
    """
    req = urllib.request.Request(url, headers={'User-Agent': user_agent})
    # Permissive SSL context — self-signed certs are common on small-company
    # sites and we'd rather record a 200 than pretend they're dead.
    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE
    try:
        with urllib.request.urlopen(req, timeout=TIMEOUT, context=ctx) as resp:
            body = resp.read(BODY_CAP * 2)  # cap at 20 KB read to be safe
            return {
                'http_status': resp.status,
                'final_url': resp.geturl(),
                'body': body,
                'title': extract_title(body),
            }
    except urllib.error.HTTPError as e:
        return {'http_status': e.code, 'final_url': url, 'body': b'', 'title': ''}
    except urllib.error.URLError as e:
        reason = repr(getattr(e, 'reason', e))
        if 'timed out' in reason.lower() or 'timeout' in reason.lower():
            return {'error': 'timeout'}
        if 'ssl' in reason.lower() or 'certificate' in reason.lower():
            return {'error': 'ssl_error'}
        if 'refused' in reason.lower():
            return {'error': 'connection_refused'}
        if 'nxdomain' in reason.lower() or 'name or service not known' in reason.lower() \
                or 'no address associated' in reason.lower():
            return {'error': 'nxdomain'}
        return {'error': 'connect_error'}
    except socket.timeout:
        return {'error': 'timeout'}
    except Exception as e:
        return {'error': f'other:{type(e).__name__}'}


def classify(name: str, website: str) -> dict:
    """Probe a single company and return a result dict."""
    started = time.monotonic()
    result: dict = {
        'url_input': website,
        'final_url': None,
        'http_status': None,
        'title': None,
        'elapsed_ms': 0,
        'flags': [],
        'status': 'unknown',
        'confidence': '',
    }

    if not website:
        result['flags'].append('no_website')
        result['elapsed_ms'] = 0
        return result

    url = normalize_url(website)
    if url is None:
        result['flags'].append('malformed_website')
        # Honest answer: we never even attempted a real probe, so lifecycle
        # status is unknown — not dead_domain.
        return result

    host = extract_host(url)

    # Quick DNS pre-check — fails fast on typo/dead domains.
    if not dns_check(host):
        result['flags'].append('nxdomain')
        result['status'] = 'dead_domain'
        result['confidence'] = 'H'
        result['elapsed_ms'] = int((time.monotonic() - started) * 1000)
        return result

    # HTTPS first.
    r = http_get(url)

    # If HTTPS failed with connect/SSL/timeout, retry once over HTTP.
    if r.get('error') in ('ssl_error', 'connection_refused', 'connect_error', 'timeout'):
        http_url = 'http://' + url[len('https://'):]
        r2 = http_get(http_url)
        if 'error' not in r2:
            r = r2
            url = http_url
        else:
            # Prefer the more informative error tag.
            r = {'error': r.get('error')}

    # If the default UA hit 401/403, retry once with a browser UA before
    # concluding anything. Many CDNs (Cloudflare, Akamai) block non-browser
    # UAs even for healthy sites — a "dormant" verdict there would be a lie.
    if 'error' not in r and r.get('http_status') in (401, 403):
        r_browser = http_get(url, user_agent=BROWSER_UA)
        if 'error' not in r_browser and r_browser.get('http_status', 0) < 400:
            result['flags'].append('needed_browser_ua')
            r = r_browser

    # If reccy gave us a URL with a path (e.g. "meta.com/reality-labs") and
    # the path itself 404s or 5xxs, retry the domain root. A dead path
    # doesn't mean a dead company — it means the company reshuffled its site.
    if 'error' not in r:
        sc = r.get('http_status', 0)
        path_had_content = bool(urlparse(url).path.strip('/'))
        if (sc == 404 or (500 <= sc < 600)) and path_had_content:
            root = root_url(url)
            r_root = http_get(root)
            if 'error' not in r_root and r_root.get('http_status', 0) in (401, 403):
                r_root = http_get(root, user_agent=BROWSER_UA)
            if 'error' not in r_root and r_root.get('http_status', 0) < 400:
                result['flags'].append('path_lost_root_ok')
                r = r_root

    if 'error' in r:
        err = r['error']
        result['flags'].append(err)
        if err == 'timeout':
            result['status'] = 'dormant'
            result['confidence'] = 'M'
        elif err == 'nxdomain':
            # Very rare fallback — DNS said OK but urllib said nxdomain.
            result['status'] = 'dead_domain'
            result['confidence'] = 'H'
        else:
            result['status'] = 'dormant'
            result['confidence'] = 'M'
    else:
        status_code = r['http_status']
        result['http_status'] = status_code
        result['final_url'] = r['final_url']
        result['title'] = r['title']
        if 500 <= status_code < 600:
            result['flags'].append(f'http_{status_code}')
            result['status'] = 'dormant'
            result['confidence'] = 'M'
        elif status_code in (401, 403):
            # Bot-blocked even after the browser-UA retry — server is
            # definitely *alive*, but we couldn't verify content. Honest
            # answer: active L (something is answering) + flag.
            result['flags'].append(f'http_{status_code}')
            result['flags'].append('bot_blocked')
            result['status'] = 'active'
            result['confidence'] = 'L'
        elif 400 <= status_code < 500:
            result['flags'].append(f'http_{status_code}')
            result['status'] = 'dormant'
            result['confidence'] = 'M'
        else:
            body = r.get('body', b'')
            if parked_flag(body, r['title']):
                result['flags'].append('parked')
                result['status'] = 'dead_domain'
                result['confidence'] = 'H'
            else:
                # Optional flag: host-mismatch redirect onto a tiny body —
                # often a parking-redirect we didn't catch by marker.
                final_host = extract_host(r['final_url'])
                if final_host and final_host != host and len(body) < 500:
                    result['flags'].append('host_mismatch_short_body')
                result['status'] = 'active'
                result['confidence'] = 'M'

    result['elapsed_ms'] = int((time.monotonic() - started) * 1000)
    # Body is discarded — we only persist title + status + flags.
    return result


def probe_many(rows: list[tuple[str, str]], workers: int = MAX_WORKERS) -> dict:
    """Run classify() on many rows concurrently. Returns {key: result}."""
    results: dict = {}
    total = len(rows)
    done = 0
    with ThreadPoolExecutor(max_workers=workers) as ex:
        fut_to_key = {
            ex.submit(classify, name, website): name.lower().strip()
            for name, website in rows
        }
        for fut in as_completed(fut_to_key):
            key = fut_to_key[fut]
            try:
                results[key] = fut.result()
            except Exception as e:
                # Shouldn't happen — classify() catches internally — but just in case.
                results[key] = {
                    'url_input': '',
                    'final_url': None,
                    'http_status': None,
                    'title': None,
                    'elapsed_ms': 0,
                    'flags': [f'worker_crash:{type(e).__name__}'],
                    'status': 'unknown',
                    'confidence': '',
                }
            done += 1
            r = results[key]
            print(
                f'[{done:>3}/{total}] {key[:40]:<40} '
                f'{r["status"]:<12} {r["confidence"] or "-":<2} '
                f'{r["elapsed_ms"]:>5}ms  {",".join(r["flags"]) or "-"}',
                file=sys.stderr,
            )
    return results


def print_summary(results: dict) -> None:
    from collections import Counter
    status_counts = Counter(r['status'] for r in results.values())
    print('\n=== Summary ===')
    for st in ('active', 'dormant', 'dead_domain', 'unknown'):
        print(f'  {st:<12}: {status_counts.get(st, 0)}')
    print(f'  total       : {len(results)}')

    dead = [
        (k, r) for k, r in results.items() if r['status'] == 'dead_domain'
    ]
    if dead:
        print(f'\n=== dead_domain ({len(dead)}) — MUST be eyeballed ===')
        for k, r in sorted(dead):
            print(f'  {k:<40}  {",".join(r["flags"])}  {r["url_input"]}')

    dormant = [
        (k, r) for k, r in results.items() if r['status'] == 'dormant'
    ]
    if dormant:
        print(f'\n=== dormant ({len(dormant)}) — likely transient, eyeball for surprises ===')
        for k, r in sorted(dormant):
            print(f'  {k:<40}  {",".join(r["flags"])}  {r["url_input"]}')

    unknown = [
        (k, r) for k, r in results.items() if r['status'] == 'unknown'
    ]
    if unknown:
        print(f'\n=== unknown ({len(unknown)}) — no website listed or probe failed ===')
        for k, r in sorted(unknown):
            print(f'  {k:<40}  {",".join(r["flags"]) or "no website"}')


def write_output(results: dict, checked_at: str) -> None:
    payload = {
        'checked_at': checked_at,
        'script_version': SCRIPT_VERSION,
        'results': results,
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    with OUT.open('w', encoding='utf-8') as f:
        json.dump(payload, f, indent=2, sort_keys=True, ensure_ascii=False)
        f.write('\n')
    print(f'\nWrote {OUT}')


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--dry-run', action='store_true',
                    help="Probe everything but don't write the JSON output.")
    ap.add_argument('--only', metavar='NAME',
                    help='Probe a single row by (case-insensitive) name match.')
    args = ap.parse_args()

    all_rows = parse_raw(RAW)

    if args.only:
        needle = args.only.lower().strip()
        matches = [(n, w) for n, w in all_rows if needle in n.lower()]
        if not matches:
            print(f'No rows match "{args.only}"', file=sys.stderr)
            sys.exit(1)
        print(f'Probing {len(matches)} row(s) matching "{args.only}":',
              file=sys.stderr)
        for name, website in matches:
            r = classify(name, website)
            print(f'\n{name}')
            print(f'  website  : {website}')
            print(f'  status   : {r["status"]} ({r["confidence"] or "-"})')
            print(f'  http     : {r["http_status"]}')
            print(f'  final_url: {r["final_url"]}')
            print(f'  title    : {r["title"]}')
            print(f'  flags    : {r["flags"]}')
            print(f'  elapsed  : {r["elapsed_ms"]}ms')
        return

    checked_at = datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')
    print(f'Probing {len(all_rows)} rows ({MAX_WORKERS} workers)…',
          file=sys.stderr)
    results = probe_many(all_rows)
    print_summary(results)

    if args.dry_run:
        print('\n(dry-run: not writing output)')
        return

    write_output(results, checked_at)


if __name__ == '__main__':
    main()
