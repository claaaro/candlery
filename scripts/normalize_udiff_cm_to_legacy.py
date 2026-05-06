#!/usr/bin/env python3
"""Normalize NSE CM UDiFF CSV into legacy bhavcopy-style columns.

Supported modes:
1) Date mode (recommended):
   python3 scripts/normalize_udiff_cm_to_legacy.py 2026-05-04
   - reads : data/bhavcopy_2026-05-04.csv
   - writes: data/day_udiff_2026-05-04.csv

2) Explicit path mode (backward compatible):
   python3 scripts/normalize_udiff_cm_to_legacy.py <input_udiff_csv> <output_legacy_csv>
"""
from __future__ import annotations

import csv
import re
import sys
from pathlib import Path


REQUIRED_INPUT_COLUMNS = {
    "TradDt",
    "TckrSymb",
    "SctySrs",
    "OpnPric",
    "HghPric",
    "LwPric",
    "ClsPric",
    "TtlTradgVol",
    "ISIN",
}

LEGACY_COLUMNS = [
    "SYMBOL",
    "SERIES",
    "OPEN",
    "HIGH",
    "LOW",
    "CLOSE",
    "LAST",
    "PREVCLOSE",
    "TOTTRDQTY",
    "TOTTRDVAL",
    "TIMESTAMP",
    "TOTALTRADES",
    "ISIN",
]
REPO_ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = REPO_ROOT / "data"


def normalize(input_path: Path, output_path: Path) -> tuple[int, int]:
    with input_path.open("r", encoding="utf-8-sig", newline="") as src:
        reader = csv.DictReader(src)
        in_cols = set(reader.fieldnames or [])
        missing = REQUIRED_INPUT_COLUMNS - in_cols
        if missing:
            raise ValueError(f"Missing required UDiFF columns: {sorted(missing)}")

        output_path.parent.mkdir(parents=True, exist_ok=True)
        with output_path.open("w", encoding="utf-8", newline="") as dst:
            writer = csv.DictWriter(dst, fieldnames=LEGACY_COLUMNS)
            writer.writeheader()
            total = 0
            kept = 0

            for row in reader:
                total += 1
                if row.get("SctySrs", "").strip() != "EQ":
                    continue

                out = {
                    "SYMBOL": row.get("TckrSymb", "").strip(),
                    "SERIES": row.get("SctySrs", "").strip(),
                    "OPEN": row.get("OpnPric", "").strip(),
                    "HIGH": row.get("HghPric", "").strip(),
                    "LOW": row.get("LwPric", "").strip(),
                    "CLOSE": row.get("ClsPric", "").strip(),
                    # Legacy importer does not require these, keep best-effort values.
                    "LAST": row.get("ClsPric", "").strip(),
                    "PREVCLOSE": row.get("PrvsClsgPric", "").strip(),
                    "TOTTRDQTY": row.get("TtlTradgVol", "").strip(),
                    "TOTTRDVAL": row.get("TtlTrfVal", "").strip(),
                    "TIMESTAMP": row.get("TradDt", "").strip(),
                    "TOTALTRADES": row.get("TtlNbOfTxsExctd", "").strip(),
                    "ISIN": row.get("ISIN", "").strip(),
                }
                writer.writerow(out)
                kept += 1
    return total, kept


def _resolve_paths(argv: list[str]) -> tuple[Path, Path]:
    # Date mode
    if len(argv) == 2 and re.fullmatch(r"\d{4}-\d{2}-\d{2}", argv[1]):
        d = argv[1]
        return DATA_DIR / f"bhavcopy_{d}.csv", DATA_DIR / f"day_udiff_{d}.csv"

    # Explicit path mode
    if len(argv) == 3:
        return Path(argv[1]), Path(argv[2])

    raise ValueError("bad args")


def main() -> int:
    try:
        input_path, output_path = _resolve_paths(sys.argv)
    except ValueError:
        print(
            "Usage:\n"
            "  python3 scripts/normalize_udiff_cm_to_legacy.py <YYYY-MM-DD>\n"
            "  python3 scripts/normalize_udiff_cm_to_legacy.py <input_udiff_csv> <output_legacy_csv>",
            file=sys.stderr,
        )
        return 2

    if not input_path.exists():
        print(f"Input not found: {input_path}", file=sys.stderr)
        return 1

    total, kept = normalize(input_path, output_path)
    print(f"Input : {input_path}")
    print(f"Output: {output_path}")
    print(f"Rows  : total={total}, kept_eq={kept}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

