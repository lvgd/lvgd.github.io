#!/usr/bin/env python3
"""Daily Google Scholar snapshot scraper.

Reads data/citations.json, fetches each profile's Scholar page, parses
total citations / h-index / i10-index, and appends today's snapshot.
Stdlib-only; no pip install needed in CI.
"""

from __future__ import annotations

import datetime as dt
import json
import re
import sys
import urllib.error
import urllib.request
from pathlib import Path

DATA_FILE = Path(__file__).resolve().parent.parent / "data" / "citations.json"

USER_AGENT = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/121.0.0.0 Safari/537.36"
)

VALUE_RE = re.compile(r'class="gsc_rsb_std">(\d+)</td>')


def fetch(url: str) -> str:
    req = urllib.request.Request(
        url,
        headers={
            "User-Agent": USER_AGENT,
            "Accept-Language": "en-US,en;q=0.9",
        },
    )
    with urllib.request.urlopen(req, timeout=20) as resp:
        if resp.status != 200:
            raise RuntimeError(f"HTTP {resp.status} for {url}")
        return resp.read().decode("utf-8", errors="replace")


def parse_metrics(html: str) -> tuple[int, int, int]:
    """Return (citations_all, h_index_all, i10_index_all).

    Scholar emits six <td class="gsc_rsb_std"> values, ordered:
        citations_all, citations_recent,
        h_index_all,   h_index_recent,
        i10_index_all, i10_index_recent.
    """
    nums = [int(m) for m in VALUE_RE.findall(html)]
    if len(nums) < 6:
        raise RuntimeError(
            f"Expected 6 gsc_rsb_std values, got {len(nums)} — "
            "page may be a CAPTCHA challenge or layout changed."
        )
    return nums[0], nums[2], nums[4]


def main() -> int:
    data = json.loads(DATA_FILE.read_text())
    today = dt.datetime.now(dt.timezone.utc).date().isoformat()

    snapshots: list[tuple[dict, dict]] = []
    for profile in data["profiles"]:
        try:
            html = fetch(profile["url"])
            citations, h_index, i10_index = parse_metrics(html)
        except (urllib.error.URLError, RuntimeError, ValueError) as exc:
            print(
                f"[error] {profile['name']} ({profile['id']}): {exc}",
                file=sys.stderr,
            )
            return 1
        snapshots.append(
            (
                profile,
                {
                    "date": today,
                    "citations": citations,
                    "h_index": h_index,
                    "i10_index": i10_index,
                },
            )
        )

    # All fetches succeeded — commit the snapshots to the data structure.
    for profile, entry in snapshots:
        history = profile.setdefault("history", [])
        if history and history[-1]["date"] == today:
            history[-1] = entry
        else:
            history.append(entry)
        print(
            f"[ok] {profile['name']}: "
            f"citations={entry['citations']} "
            f"h={entry['h_index']} "
            f"i10={entry['i10_index']}"
        )

    DATA_FILE.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
