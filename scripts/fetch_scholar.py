#!/usr/bin/env python3
"""Daily Google Scholar snapshot scraper.

Reads data/citations.json, fetches each profile's Scholar page, parses
total citations / h-index / i10-index, and appends today's snapshot.
Stdlib-only; no pip install needed in CI.
"""

from __future__ import annotations

import datetime as dt
import gzip
import http.cookiejar
import json
import random
import re
import sys
import time
import urllib.error
import urllib.request
import zlib
from pathlib import Path

DATA_FILE = Path(__file__).resolve().parent.parent / "data" / "citations.json"

USER_AGENT = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/121.0.0.0 Safari/537.36"
)

BROWSER_HEADERS = {
    "User-Agent": USER_AGENT,
    "Accept": (
        "text/html,application/xhtml+xml,application/xml;q=0.9,"
        "image/avif,image/webp,*/*;q=0.8"
    ),
    "Accept-Language": "en-US,en;q=0.9",
    "Accept-Encoding": "gzip, deflate",
    "Sec-Fetch-Dest": "document",
    "Sec-Fetch-Mode": "navigate",
    "Sec-Fetch-Site": "none",
    "Sec-Fetch-User": "?1",
    "Upgrade-Insecure-Requests": "1",
}

VALUE_RE = re.compile(r'class="gsc_rsb_std">(\d+)</td>')

MAX_ATTEMPTS = 3


def make_opener() -> urllib.request.OpenerDirector:
    return urllib.request.build_opener(
        urllib.request.HTTPCookieProcessor(http.cookiejar.CookieJar())
    )


def fetch(opener: urllib.request.OpenerDirector, url: str) -> str:
    req = urllib.request.Request(url, headers=BROWSER_HEADERS)
    with opener.open(req, timeout=30) as resp:
        raw = resp.read()
        encoding = resp.headers.get("Content-Encoding", "").lower()
        if encoding == "gzip":
            raw = gzip.decompress(raw)
        elif encoding == "deflate":
            raw = zlib.decompress(raw)
        return raw.decode("utf-8", errors="replace")


def warm_up(opener: urllib.request.OpenerDirector) -> None:
    """Hit Scholar root to seed cookies (GSP, NID, …) before the real query."""
    try:
        fetch(opener, "https://scholar.google.com/")
    except Exception:
        pass


def alt_url(url: str) -> str | None:
    if "scholar.google.co.uk" in url:
        return url.replace("scholar.google.co.uk", "scholar.google.com")
    if "scholar.google.com" in url:
        return url.replace("scholar.google.com", "scholar.google.co.uk")
    return None


def parse_metrics(html: str) -> tuple[int, int, int]:
    nums = [int(m) for m in VALUE_RE.findall(html)]
    if len(nums) < 6:
        raise RuntimeError(
            f"got {len(nums)} gsc_rsb_std values, expected 6 — "
            "page is likely a CAPTCHA challenge"
        )
    return nums[0], nums[2], nums[4]


def fetch_profile(profile: dict) -> tuple[int, int, int]:
    """Try primary URL with cookies + retries; on persistent failure, swap mirror."""
    urls = [profile["url"]]
    if (alt := alt_url(profile["url"])) is not None:
        urls.append(alt)

    last_err = "no attempts made"
    for url in urls:
        opener = make_opener()
        warm_up(opener)
        for attempt in range(1, MAX_ATTEMPTS + 1):
            try:
                return parse_metrics(fetch(opener, url))
            except urllib.error.HTTPError as e:
                last_err = f"HTTP {e.code} on {url} (attempt {attempt}/{MAX_ATTEMPTS})"
                if e.code in (403, 429) and attempt < MAX_ATTEMPTS:
                    time.sleep(random.uniform(8, 22))
                    continue
                break
            except (urllib.error.URLError, RuntimeError, ValueError) as e:
                last_err = f"{type(e).__name__}: {e} on {url} (attempt {attempt}/{MAX_ATTEMPTS})"
                if attempt < MAX_ATTEMPTS:
                    time.sleep(random.uniform(5, 15))
                    continue
                break
    raise RuntimeError(last_err)


def main() -> int:
    data = json.loads(DATA_FILE.read_text())
    today = dt.datetime.now(dt.timezone.utc).date().isoformat()

    snapshots: list[tuple[dict, dict]] = []
    for profile in data["profiles"]:
        try:
            citations, h_index, i10_index = fetch_profile(profile)
        except RuntimeError as exc:
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
