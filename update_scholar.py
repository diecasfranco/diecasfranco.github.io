#!/usr/bin/env python3
"""Fetch citation count and H-index from public Google Scholar profile page."""

import json
import sys
import time
import re
from datetime import datetime

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

def fetch_stats(retries=3, delay=10):
    for attempt in range(1, retries + 1):
        try:
            print(f"Attempt {attempt}/{retries} — fetching {SCHOLAR_URL}")
            resp = requests.get(SCHOLAR_URL, headers=HEADERS, timeout=20)
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

    return None

def main():
    result = fetch_stats()

    if result is None:
        print("All attempts failed — keeping existing scholar_stats.json unchanged.", file=sys.stderr)
        sys.exit(1)

    citations, h_index, i10_index = result

    data = {
        "citations":  citations,
        "h_index":    h_index,
        "i10_index":  i10_index,
        "updated":    datetime.utcnow().strftime("%Y-%m-%d"),
    }

    with open("scholar_stats.json", "w") as f:
        json.dump(data, f, indent=2)

    print(f"  Citations : {citations}")
    print(f"  H-index   : {h_index}")
    print(f"  i10-index : {i10_index}")
    print("  Saved to scholar_stats.json")

if __name__ == "__main__":
    main()
