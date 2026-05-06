"""NSE Bhavcopy importer.

Downloads and parses NSE equity bhavcopy CSV files into Candle and
Instrument objects. Handles date validation via TradingCalendar and
converts all timestamps to UTC.

Phase 1: Parses from local CSV files (no HTTP downloads).
"""

from __future__ import annotations

import csv
import logging
from dataclasses import dataclass, field
from datetime import date
from io import StringIO
from pathlib import Path

from candlery.core.candle import Candle
from candlery.core.instrument import Instrument
from candlery.data.calendar import TradingCalendar

logger = logging.getLogger(__name__)

# Bhavcopy CSV column names (standard NSE equity format)
_COL_SYMBOL = "SYMBOL"
_COL_SERIES = "SERIES"
_COL_OPEN = "OPEN"
_COL_HIGH = "HIGH"
_COL_LOW = "LOW"
_COL_CLOSE = "CLOSE"
_COL_VOLUME = "TOTTRDQTY"
_COL_ISIN = "ISIN"
_COL_TIMESTAMP = "TIMESTAMP"

# Only import equity series
_EQUITY_SERIES = {"EQ"}


@dataclass(frozen=True)
class ImportResult:
    """Result of importing a single bhavcopy file."""

    date: date
    candles: dict[str, Candle]  # symbol → Candle
    instruments: dict[str, Instrument]  # symbol → Instrument
    skipped: int  # rows skipped (non-EQ series, bad data)
    errors: list[str]  # human-readable error descriptions


class BhavcopyImporter:
    """Parses NSE bhavcopy CSV files into Candle/Instrument objects.

    Usage:
        calendar = TradingCalendar("NSE")
        importer = BhavcopyImporter(calendar)

        # From a file on disk:
        result = importer.import_file(Path("data/raw/nse/cm01JAN2024bhav.csv"))

        # From CSV text:
        result = importer.import_csv(csv_text, date(2024, 1, 1))

        # All files in a directory for a date range:
        results = importer.import_directory(
            Path("data/raw/nse/bhavcopy"),
            start=date(2024, 1, 1),
            end=date(2024, 12, 31),
        )
    """

    def __init__(self, calendar: TradingCalendar) -> None:
        self._calendar = calendar

    def import_csv(
        self,
        csv_text: str,
        trading_date: date,
        symbols: set[str] | None = None,
    ) -> ImportResult:
        """Parse bhavcopy CSV text for a given trading date.

        Args:
            csv_text: Raw CSV content (with headers).
            trading_date: The date this bhavcopy represents.
            symbols: If provided, only import these symbols. None = import all.

        Returns:
            ImportResult with candles, instruments, skip count, errors.
        """
        if not self._calendar.is_trading_day(trading_date):
            return ImportResult(
                date=trading_date,
                candles={},
                instruments={},
                skipped=0,
                errors=[f"{trading_date} is not a trading day"],
            )

        timestamp_utc = self._calendar.market_open_utc(trading_date)
        candles: dict[str, Candle] = {}
        instruments: dict[str, Instrument] = {}
        skipped = 0
        errors: list[str] = []

        reader = csv.DictReader(StringIO(csv_text))

        for row_num, row in enumerate(reader, start=2):  # row 1 = header
            try:
                result = self._parse_row(row, timestamp_utc, symbols)
                if result is None:
                    skipped += 1
                    continue
                symbol, candle, instrument = result
                candles[symbol] = candle
                instruments[symbol] = instrument
            except (ValueError, KeyError) as e:
                skipped += 1
                symbol_val = row.get(_COL_SYMBOL, "UNKNOWN")
                errors.append(f"Row {row_num} ({symbol_val}): {e}")

        return ImportResult(
            date=trading_date,
            candles=candles,
            instruments=instruments,
            skipped=skipped,
            errors=errors,
        )

    def import_file(
        self,
        path: Path,
        trading_date: date | None = None,
        symbols: set[str] | None = None,
    ) -> ImportResult:
        """Parse a bhavcopy CSV file.

        Args:
            path: Path to the CSV file.
            trading_date: If None, attempt to extract from the filename or
                          the TIMESTAMP column in the CSV.
            symbols: If provided, only import these symbols.

        Returns:
            ImportResult.
        """
        if not path.exists():
            raise FileNotFoundError(f"Bhavcopy file not found: {path}")

        text = path.read_text(encoding="utf-8-sig")  # handle BOM

        if trading_date is None:
            trading_date = self._extract_date_from_csv(text)

        return self.import_csv(text, trading_date, symbols)

    def import_directory(
        self,
        directory: Path,
        start: date,
        end: date,
        symbols: set[str] | None = None,
        file_glob: str = "*.csv",
    ) -> list[ImportResult]:
        """Import all CSV files in a directory for the given date range.

        Scans files matching file_glob and attempts to parse each one.
        Only includes results for trading days within [start, end].
        """
        if not directory.is_dir():
            raise NotADirectoryError(f"Not a directory: {directory}")

        results: list[ImportResult] = []
        for csv_path in sorted(directory.glob(file_glob)):
            try:
                result = self.import_file(csv_path, symbols=symbols)
                if start <= result.date <= end:
                    results.append(result)
            except (FileNotFoundError, ValueError) as e:
                logger.warning("Skipping %s: %s", csv_path, e)

        return results

    # ------------------------------------------------------------------
    # Internal
    # ------------------------------------------------------------------

    def _parse_row(
        self,
        row: dict[str, str],
        timestamp_utc,
        symbols: set[str] | None,
    ) -> tuple[str, Candle, Instrument] | None:
        """Parse a single CSV row. Returns None if row should be skipped."""
        # Strip whitespace from all keys and values
        row = {k.strip(): v.strip() for k, v in row.items()}

        series = row.get(_COL_SERIES, "")
        if series not in _EQUITY_SERIES:
            return None

        symbol = row[_COL_SYMBOL]
        if symbols is not None and symbol not in symbols:
            return None

        candle = Candle(
            timestamp=timestamp_utc,
            open=float(row[_COL_OPEN]),
            high=float(row[_COL_HIGH]),
            low=float(row[_COL_LOW]),
            close=float(row[_COL_CLOSE]),
            volume=int(row[_COL_VOLUME]),
        )

        instrument = Instrument(
            symbol=symbol,
            exchange="NSE",
            currency="INR",
            isin=row.get(_COL_ISIN),
        )

        return symbol, candle, instrument

    def _extract_date_from_csv(self, csv_text: str) -> date:
        """Extract the trading date from the TIMESTAMP column of the first data row."""
        reader = csv.DictReader(StringIO(csv_text))
        for row in reader:
            row = {k.strip(): v.strip() for k, v in row.items()}
            ts = row.get(_COL_TIMESTAMP, "")
            if ts:
                # Bhavcopy TIMESTAMP format: "01-JAN-2024" or "2024-01-01"
                for fmt in ("%d-%b-%Y", "%Y-%m-%d"):
                    try:
                        return date.fromisoformat(ts) if "-" in ts and len(ts) == 10 else _parse_date(ts, fmt)
                    except ValueError:
                        continue
                raise ValueError(f"Cannot parse TIMESTAMP: {ts}")
        raise ValueError("No data rows found in CSV")


def _parse_date(text: str, fmt: str) -> date:
    """Parse a date string with the given format."""
    from datetime import datetime as dt
    return dt.strptime(text, fmt).date()
