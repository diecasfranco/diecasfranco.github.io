#!/usr/bin/env python3
"""Fetch citation count and H-index from public Google Scholar profile page."""

import argparse
import json
import sys
import time
import re
from datetime import datetime, timezone

try:
    import requests
    from bs4 import BeautifulSoup
except ImportError:
    print("Missing dependencies. Install with: pip install requests beautifulsoup4", file=sys.stderr)
    sys.exit(1)

SCHOLAR_URL = "https://scholar.google.com/citations?user=CieheMcAAAAJ&hl=en"

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "en-US,en;q=0.9",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
}

# Scholar rejects datacenter IPs (GitHub Actions runners) with these codes.
BLOCK_CODES = {403, 429}

def fetch_stats(retries=3, delay=10):
    """Return (citations, h_index, i10_index), or None on failure.

    Sets fetch_stats.blocked when every attempt was rejected by Scholar's
    bot protection rather than failing for some other reason.
    """
    fetch_stats.blocked = False
    block_hits = 0

    for attempt in range(1, retries + 1):
        try:
            print(f"Attempt {attempt}/{retries} — fetching {SCHOLAR_URL}")
            resp = requests.get(SCHOLAR_URL, headers=HEADERS, timeout=20)
            if resp.status_code in BLOCK_CODES:
                block_hits += 1
            resp.raise_for_status()

            soup = BeautifulSoup(resp.text, "html.parser")

            # Stats table: Citations / H-index / i10-index, each row has [all-time, since-year]
            cells = soup.select("td.gsc_rsb_std")
            if len(cells) < 6:
                raise ValueError(f"Expected ≥6 stat cells, got {len(cells)} — page may have changed or been blocked")

            citations  = int(re.sub(r"\D", "", cells[0].text) or 0)
            h_index    = int(re.sub(r"\D", "", cells[2].text) or 0)
            i10_index  = int(re.sub(r"\D", "", cells[4].text) or 0)

            return citations, h_index, i10_index

        except Exception as e:
            print(f"  Error: {e}", file=sys.stderr)
            if attempt < retries:
                print(f"  Retrying in {delay}s…")
                time.sleep(delay)

    fetch_stats.blocked = block_hits == retries
    return None

def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument(
        "--tolerate-block",
        action="store_true",
        help="Exit 0 (instead of 1) when Scholar blocks the request as a bot. "
             "Used in CI, where datacenter IPs are routinely rejected and a red "
             "run would be noise rather than signal.",
    )
    args = ap.parse_args()

    result = fetch_stats()

    if result is None:
        print("All attempts failed — keeping existing scholar_stats.json unchanged.", file=sys.stderr)
        if fetch_stats.blocked and args.tolerate_block:
            print("Cause was Scholar bot-blocking (HTTP 403/429), not a script error; "
                  "treating as a skip.", file=sys.stderr)
            sys.exit(0)
        sys.exit(1)

    citations, h_index, i10_index = result

    data = {
        "citations":  citations,
        "h_index":    h_index,
        "i10_index":  i10_index,
        "updated":    datetime.now(timezone.utc).strftime("%Y-%m-%d"),
    }

    with open("scholar_stats.json", "w") as f:
        json.dump(data, f, indent=2)

    print(f"  Citations : {citations}")
    print(f"  H-index   : {h_index}")
    print(f"  i10-index : {i10_index}")
    print("  Saved to scholar_stats.json")

if __name__ == "__main__":
    main()
