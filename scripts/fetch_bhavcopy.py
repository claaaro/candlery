#!/usr/bin/env python3
"""Fetch one NSE bhavcopy CSV and write it into ``data/`` for candlery.

Single-purpose tool. One date in, one CSV out. No date ranges, no retries
across days, no symbol filtering. If you need more than one day, invoke this
script more than once.

Usage:
    python3 scripts/fetch_bhavcopy.py             # defaults to last weekday
    python3 scripts/fetch_bhavcopy.py 2026-05-04  # specific ISO date

On success: writes ``data/bhavcopy_<YYYY-MM-DD>.csv`` (NSE classic format).
On failure: prints the URL to open manually in a browser as fallback.
"""
from __future__ import annotations

import io
import sys
import zipfile
from datetime import date, datetime, timedelta
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

REPO_ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = REPO_ROOT / "data"


def _resolve_date(arg: str | None) -> date:
    if arg:
        return datetime.strptime(arg, "%Y-%m-%d").date()
    d = date.today() - timedelta(days=1)
    while d.weekday() >= 5:  # weekends only; NSE holidays not handled here
        d -= timedelta(days=1)
    return d


def _build_url(d: date) -> str:
    yyyy = d.strftime("%Y")
    mmm = d.strftime("%b").upper()
    dd = d.strftime("%d")
    return (
        "https://nsearchives.nseindia.com/content/historical/EQUITIES/"
        f"{yyyy}/{mmm}/cm{dd}{mmm}{yyyy}bhav.csv.zip"
    )


def _output_path(d: date) -> Path:
    return DATA_DIR / f"bhavcopy_{d.isoformat()}.csv"


def _fetch(url: str) -> bytes:
    req = Request(
        url,
        headers={
            "User-Agent": (
                "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/119.0.0.0 Safari/537.36"
            ),
            "Accept": "*/*",
            "Accept-Language": "en-US,en;q=0.9",
            "Referer": "https://www.nseindia.com/",
        },
    )
    with urlopen(req, timeout=30) as resp:
        return resp.read()


def main() -> int:
    arg = sys.argv[1] if len(sys.argv) > 1 else None
    try:
        d = _resolve_date(arg)
    except ValueError as e:
        print(f"Bad date argument: {e}", file=sys.stderr)
        return 2

    url = _build_url(d)
    out_path = _output_path(d)
    print(f"Target date : {d.isoformat()}")
    print(f"Source URL  : {url}")
    print(f"Output file : {out_path}")

    if out_path.exists():
        print("Already present; not overwriting. Delete it to re-fetch.")
        return 0

    DATA_DIR.mkdir(parents=True, exist_ok=True)
    try:
        payload = _fetch(url)
    except (HTTPError, URLError) as e:
        print(f"Fetch failed: {e}", file=sys.stderr)
        print("Manual fallback:", file=sys.stderr)
        print(
            "  Open the URL above in a browser, save the .zip, extract the .csv,",
            file=sys.stderr,
        )
        print(
            f"  rename it to {out_path.name}, place under {DATA_DIR}.",
            file=sys.stderr,
        )
        return 1

    try:
        with zipfile.ZipFile(io.BytesIO(payload)) as zf:
            names = [n for n in zf.namelist() if n.lower().endswith(".csv")]
            if not names:
                print("Zip contained no CSV file.", file=sys.stderr)
                return 1
            with zf.open(names[0]) as src, out_path.open("wb") as dst:
                dst.write(src.read())
    except zipfile.BadZipFile:
        raw_dump = Path("/tmp/nse_response.bin")
        raw_dump.write_bytes(payload)
        print(
            "Response was not a valid zip. NSE may have changed the URL/format.",
            file=sys.stderr,
        )
        print(f"Raw response saved to {raw_dump} for inspection.", file=sys.stderr)
        return 1

    size = out_path.stat().st_size
    print(f"Wrote {out_path} ({size} bytes)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
