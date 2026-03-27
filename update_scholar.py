#!/usr/bin/env python3
"""Fetch citation count and H-index from Google Scholar and write to scholar_stats.json."""

import json
import sys
from datetime import datetime

try:
    from scholarly import scholarly
except ImportError:
    print("scholarly not installed", file=sys.stderr)
    sys.exit(1)

SCHOLAR_ID = "CieheMcAAAAJ"

def main():
    print(f"Fetching Google Scholar profile: {SCHOLAR_ID}")
    try:
        author = scholarly.search_author_id(SCHOLAR_ID)
        author = scholarly.fill(author, sections=["basics", "indices"])

        citations = author.get("citedby", 0)
        h_index   = author.get("hindex",   0)
        i10_index = author.get("i10index",  0)

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
        print(f"  Saved to scholar_stats.json")

    except Exception as e:
        print(f"Error fetching Scholar data: {e}", file=sys.stderr)
        # If fetch fails, keep existing file untouched
        sys.exit(1)

if __name__ == "__main__":
    main()
