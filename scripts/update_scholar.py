#!/usr/bin/env python3
"""Wrapper run by launchd (com.lvgd.scholar): fetch scholar metrics, commit
+ push if changed. Idempotent — safe to call manually.

Lives in a Python script (not bash) because macOS TCC blocks launchd→bash
from reading ~/Documents, but the miniconda python binary is already
TCC-granted (Job_finder uses it daily).
"""
from __future__ import annotations

import datetime as dt
import os
import subprocess
import sys
from pathlib import Path

REPO = Path("/Users/lvgd/Documents/lvgd.github.io")
LOG = REPO / "logs" / "scholar.log"
FETCH = REPO / "scripts" / "fetch_scholar.py"
DATA_REL = "data/citations.json"


def ts() -> str:
    return dt.datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def log(line: str) -> None:
    LOG.parent.mkdir(parents=True, exist_ok=True)
    with LOG.open("a", encoding="utf-8") as f:
        f.write(f"[{ts()}] {line}\n")


def git(args: list[str], *, timeout: int = 120) -> subprocess.CompletedProcess:
    env = os.environ.copy()
    env["GIT_TERMINAL_PROMPT"] = "0"
    env.setdefault("GIT_ASKPASS", "/usr/bin/true")
    return subprocess.run(
        ["git", "-C", str(REPO), *args],
        capture_output=True, text=True, timeout=timeout, env=env,
    )


def main() -> int:
    log("=== scholar update starting ===")

    # 1. Fetch
    try:
        r = subprocess.run(
            [sys.executable, str(FETCH)],
            cwd=REPO, capture_output=True, text=True, timeout=180,
        )
    except subprocess.TimeoutExpired:
        log("fetch_scholar.py timed out — will retry next cycle")
        return 0
    if r.returncode != 0:
        log(f"fetch_scholar.py FAILED (likely CAPTCHA): "
            f"{(r.stderr or r.stdout).strip()[:300]}")
        return 0
    for line in (r.stdout or "").strip().splitlines():
        log(line)

    # 2. Anything change?
    r = git(["status", "--porcelain", "--", DATA_REL])
    if r.returncode != 0:
        log(f"git status failed: {r.stderr.strip()[:200]}")
        return 0
    if not r.stdout.strip():
        log("no changes to citations.json")
        return 0

    # 3. Commit + push (with rebase to absorb Job-W's commits).
    today = dt.datetime.now(dt.timezone.utc).date().isoformat()
    r = git(["add", "--", DATA_REL])
    if r.returncode != 0:
        log(f"git add failed: {r.stderr.strip()[:200]}")
        return 0

    r = git(["commit", "-m", f"chore(data): scholar snapshot {today}", "--", DATA_REL])
    if r.returncode != 0:
        log(f"git commit failed: {r.stderr.strip()[:200]}")
        return 0

    r = git(["fetch", "origin"])
    if r.returncode != 0:
        log(f"git fetch failed: {r.stderr.strip()[:200]} — trying push anyway")
    else:
        br = git(["branch", "--show-current"])
        branch = (br.stdout or "main").strip() or "main"
        r = git(["rebase", "--autostash", f"origin/{branch}"])
        if r.returncode != 0:
            log(f"rebase failed: {(r.stderr or r.stdout).strip()[:200]} — aborting")
            git(["rebase", "--abort"])
            return 0

    r = git(["push"], timeout=180)
    if r.returncode != 0:
        log(f"git push FAILED: {(r.stderr or r.stdout).strip()[:300]}")
        return 0

    log(f"pushed snapshot {today}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
