#!/usr/bin/env python3
"""Fetch + normalize recent NSE CM bhavcopy days in one command.

Usage:
  python3 scripts/fetch_and_normalize_recent.py
  python3 scripts/fetch_and_normalize_recent.py 5
  python3 scripts/fetch_and_normalize_recent.py 5 2026-05-04

Args:
  days      Number of weekday dates to process (default: 5)
  end_date  Inclusive YYYY-MM-DD end date (default: today)
"""
from __future__ import annotations

from datetime import date, datetime, timedelta
from pathlib import Path
import subprocess
import sys

REPO_ROOT = Path(__file__).resolve().parent.parent


def _parse_args(argv: list[str]) -> tuple[int, date]:
    days = 5
    end = date.today()
    if len(argv) >= 2:
        days = int(argv[1])
    if len(argv) >= 3:
        end = datetime.strptime(argv[2], "%Y-%m-%d").date()
    if days <= 0:
        raise ValueError("days must be > 0")
    return days, end


def _recent_weekdays(count: int, end: date) -> list[date]:
    d = end
    out: list[date] = []
    while len(out) < count:
        if d.weekday() < 5:
            out.append(d)
        d -= timedelta(days=1)
    out.sort()
    return out


def _run(cmd: list[str]) -> int:
    print("$", " ".join(cmd))
    res = subprocess.run(cmd, cwd=REPO_ROOT)
    return res.returncode


def main() -> int:
    try:
        days, end = _parse_args(sys.argv)
    except Exception as e:
        print(f"Argument error: {e}", file=sys.stderr)
        print("Usage: python3 scripts/fetch_and_normalize_recent.py [days] [YYYY-MM-DD]", file=sys.stderr)
        return 2

    dates = _recent_weekdays(days, end)
    print("Processing dates:", ", ".join(d.isoformat() for d in dates))

    failures: list[str] = []
    for d in dates:
        ds = d.isoformat()
        rc1 = _run(["python3", "scripts/fetch_bhavcopy.py", ds])
        if rc1 != 0:
            failures.append(f"fetch:{ds}")
            continue
        rc2 = _run(["python3", "scripts/normalize_udiff_cm_to_legacy.py", ds])
        if rc2 != 0:
            failures.append(f"normalize:{ds}")

    print("\nSummary:")
    print(f"  total_dates: {len(dates)}")
    print(f"  failures   : {len(failures)}")
    if failures:
        for f in failures:
            print(f"    - {f}")
        return 1
    print("  status     : ok")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
