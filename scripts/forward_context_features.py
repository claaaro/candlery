#!/usr/bin/env python3
"""Compute pre-window universe context features for forward observation.

Read-only. Does not touch the trading runtime. Reads normalized bhavcopy
files (`data/day_udiff_*.csv`) and a universe YAML, and writes a JSON
record to `reports/forward_context/<asof>.json`.

Usage:
  python3 scripts/forward_context_features.py <asof YYYY-MM-DD> [universe_name]

Defaults:
  universe_name: nse50_liquid_auto
  lookback     : 20 trading days (frozen by contract)

The contract that fixes the feature set is in
`docs/ai-state/FORWARD_INTERPRETATION_CONTRACT.md`.
"""
from __future__ import annotations

import csv
import json
import math
import re
import statistics
import sys
from datetime import datetime, date, timezone
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = REPO_ROOT / "data"
UNIVERSE_DIR = REPO_ROOT / "config" / "universes"
OUT_DIR = REPO_ROOT / "reports" / "forward_context"

LOOKBACK = 20  # trading days, frozen
TRADING_DAYS_PER_YEAR = 252

DAY_FILE_RE = re.compile(r"^day_udiff_(\d{4}-\d{2}-\d{2})\.csv$")


def _read_universe(name: str) -> list[str]:
    path = UNIVERSE_DIR / f"{name}.yaml"
    if not path.exists():
        raise FileNotFoundError(f"Universe not found: {path}")
    symbols: list[str] = []
    in_symbols = False
    for raw in path.read_text().splitlines():
        line = raw.rstrip()
        if line.strip().startswith("#") or not line.strip():
            continue
        if line.startswith("symbols:"):
            in_symbols = True
            continue
        if in_symbols:
            m = re.match(r"\s*-\s*(\S+)\s*$", line)
            if m:
                symbols.append(m.group(1))
            elif line and not line.startswith(" "):
                in_symbols = False
    if not symbols:
        raise ValueError(f"Universe {name} has no symbols")
    return symbols


def _list_trading_days_up_to(asof: date) -> list[date]:
    days: list[date] = []
    for p in DATA_DIR.iterdir():
        m = DAY_FILE_RE.match(p.name)
        if not m:
            continue
        d = datetime.strptime(m.group(1), "%Y-%m-%d").date()
        if d <= asof:
            days.append(d)
    days.sort()
    return days


def _load_close_for(day: date, symbols: set[str]) -> dict[str, float]:
    path = DATA_DIR / f"day_udiff_{day.isoformat()}.csv"
    out: dict[str, float] = {}
    with path.open(newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            sym = (row.get("SYMBOL") or "").strip()
            series = (row.get("SERIES") or "").strip()
            if series != "EQ" or sym not in symbols:
                continue
            try:
                close = float(row["CLOSE"])
            except (TypeError, ValueError):
                continue
            out[sym] = close
    return out


def _compute_features(asof: date, universe_name: str) -> dict:
    symbols = _read_universe(universe_name)
    sym_set = set(symbols)

    days = _list_trading_days_up_to(asof)
    if asof not in days:
        raise FileNotFoundError(
            f"No bhavcopy data for asof={asof.isoformat()}; "
            f"latest available: {days[-1].isoformat() if days else 'none'}"
        )
    if len(days) < LOOKBACK + 1:
        raise ValueError(
            f"Need at least {LOOKBACK + 1} trading days, have {len(days)}"
        )

    window_days = days[-(LOOKBACK + 1):]
    start_day = window_days[0]
    end_day = window_days[-1]

    closes_by_day: dict[date, dict[str, float]] = {}
    for d in window_days:
        closes_by_day[d] = _load_close_for(d, sym_set)

    per_symbol_returns: list[float] = []
    per_symbol_vols: list[float] = []
    pos_count = 0
    used_symbols: list[str] = []

    for sym in symbols:
        series = []
        ok = True
        for d in window_days:
            c = closes_by_day[d].get(sym)
            if c is None or c <= 0:
                ok = False
                break
            series.append(c)
        if not ok or len(series) != LOOKBACK + 1:
            continue
        used_symbols.append(sym)

        ret_20d = series[-1] / series[0] - 1.0
        per_symbol_returns.append(ret_20d)
        if ret_20d > 0:
            pos_count += 1

        log_rets = [math.log(series[i] / series[i - 1]) for i in range(1, len(series))]
        if len(log_rets) >= 2:
            sd = statistics.pstdev(log_rets)
            per_symbol_vols.append(sd * math.sqrt(TRADING_DAYS_PER_YEAR))

    if not per_symbol_returns:
        raise ValueError("No usable symbols had complete close history in window")

    median_ret = statistics.median(per_symbol_returns)
    median_vol = statistics.median(per_symbol_vols) if per_symbol_vols else float("nan")
    breadth = pos_count / len(per_symbol_returns)

    return {
        "asof": asof.isoformat(),
        "universe": universe_name,
        "lookback_trading_days": LOOKBACK,
        "window_start": start_day.isoformat(),
        "window_end": end_day.isoformat(),
        "symbols_in_universe": len(symbols),
        "symbols_used": len(per_symbol_returns),
        "univ_median_20d_return": round(median_ret, 6),
        "univ_median_20d_vol": round(median_vol, 6),
        "univ_breadth_pos_20d": round(breadth, 6),
        "contract": "FORWARD_INTERPRETATION_CONTRACT.md",
        "computed_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
    }


def main(argv: list[str]) -> int:
    if len(argv) < 2:
        print(__doc__, file=sys.stderr)
        return 2
    try:
        asof = datetime.strptime(argv[1], "%Y-%m-%d").date()
    except ValueError as e:
        print(f"Invalid asof date: {e}", file=sys.stderr)
        return 2
    universe = argv[2] if len(argv) >= 3 else "nse50_liquid_auto"

    record = _compute_features(asof, universe)

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    out_path = OUT_DIR / f"{asof.isoformat()}.json"
    if out_path.exists():
        existing = json.loads(out_path.read_text())
        if existing.get("univ_median_20d_return") != record["univ_median_20d_return"]:
            print(
                f"Refusing to overwrite differing prior record at {out_path}.\n"
                f"Existing: {existing}\nNew: {record}",
                file=sys.stderr,
            )
            return 3
    out_path.write_text(json.dumps(record, indent=2) + "\n")
    print(json.dumps(record, indent=2))
    print(f"Wrote: {out_path.relative_to(REPO_ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
