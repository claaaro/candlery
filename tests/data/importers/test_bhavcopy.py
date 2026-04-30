"""Tests for NSE Bhavcopy importer."""

from __future__ import annotations

import json
from datetime import date, datetime, timezone
from pathlib import Path

import pytest
import yaml

from candlery.data.calendar import TradingCalendar
from candlery.data.importers.bhavcopy import BhavcopyImporter, ImportResult


# ---------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------

SAMPLE_BHAVCOPY_CSV = """\
SYMBOL, SERIES, OPEN, HIGH, LOW, CLOSE, LAST, PREVCLOSE, TOTTRDQTY, TOTTRDVAL, TIMESTAMP, TOTALTRADES, ISIN,
RELIANCE, EQ, 2450.00, 2480.50, 2430.10, 2465.75, 2460.00, 2445.00, 5000000, 12300000000, 29-APR-2026, 150000, INE002A01018,
TCS, EQ, 3800.00, 3850.00, 3780.00, 3825.50, 3820.00, 3790.00, 2000000, 7650000000, 29-APR-2026, 80000, INE467B01029,
INFY, EQ, 1500.00, 1520.00, 1490.00, 1510.00, 1505.00, 1495.00, 3000000, 4530000000, 29-APR-2026, 100000, INE009A01021,
HDFCBANK, EQ, 1600.00, 1620.00, 1585.00, 1610.50, 1608.00, 1595.00, 4000000, 6440000000, 29-APR-2026, 120000, INE040A01034,
RELIANCE, BE, 2450.00, 2450.00, 2450.00, 2450.00, 2450.00, 2445.00, 100, 245000, 29-APR-2026, 1, INE002A01018,
"""

SAMPLE_BAD_DATA_CSV = """\
SYMBOL, SERIES, OPEN, HIGH, LOW, CLOSE, LAST, PREVCLOSE, TOTTRDQTY, TOTTRDVAL, TIMESTAMP, TOTALTRADES, ISIN,
GOODSTOCK, EQ, 100.00, 110.00, 95.00, 105.00, 104.00, 98.00, 50000, 5000000, 29-APR-2026, 1000, INE999Z01010,
BADSTOCK, EQ, 200.00, 150.00, 100.00, 180.00, 175.00, 190.00, 30000, 5400000, 29-APR-2026, 800, INE888Z01010,
"""


@pytest.fixture()
def config_dir(tmp_path: Path) -> Path:
    """Build minimal exchange + holiday config."""
    exchanges_dir = tmp_path / "exchanges"
    exchanges_dir.mkdir()
    (exchanges_dir / "nse.yaml").write_text(
        yaml.dump({
            "exchange": "NSE",
            "timezone": "Asia/Kolkata",
            "has_dst": False,
            "weekend_days": [5, 6],
            "sessions": {
                "continuous": {"start": "09:15", "end": "15:30"},
            },
        })
    )
    holidays_dir = tmp_path / "holidays"
    holidays_dir.mkdir()
    (holidays_dir / "nse_2026.json").write_text(
        json.dumps({
            "exchange": "NSE",
            "year": 2026,
            "holidays": [
                {"date": "2026-01-26", "name": "Republic Day"},
                {"date": "2026-05-01", "name": "Maharashtra Day"},
            ],
        })
    )
    return tmp_path


@pytest.fixture()
def calendar(config_dir: Path) -> TradingCalendar:
    return TradingCalendar("NSE", config_dir=config_dir)


@pytest.fixture()
def importer(calendar: TradingCalendar) -> BhavcopyImporter:
    return BhavcopyImporter(calendar)


# ---------------------------------------------------------------
# Basic import
# ---------------------------------------------------------------

class TestImportCSV:

    def test_imports_equity_rows(self, importer: BhavcopyImporter) -> None:
        # 2026-04-29 is Wednesday — valid trading day
        result = importer.import_csv(SAMPLE_BHAVCOPY_CSV, date(2026, 4, 29))
        assert len(result.candles) == 4  # RELIANCE, TCS, INFY, HDFCBANK
        assert "RELIANCE" in result.candles
        assert "TCS" in result.candles
        assert "INFY" in result.candles
        assert "HDFCBANK" in result.candles

    def test_skips_non_eq_series(self, importer: BhavcopyImporter) -> None:
        result = importer.import_csv(SAMPLE_BHAVCOPY_CSV, date(2026, 4, 29))
        # RELIANCE BE row should be skipped
        assert result.skipped == 1

    def test_candle_values_correct(self, importer: BhavcopyImporter) -> None:
        result = importer.import_csv(SAMPLE_BHAVCOPY_CSV, date(2026, 4, 29))
        reliance = result.candles["RELIANCE"]
        assert reliance.open == 2450.00
        assert reliance.high == 2480.50
        assert reliance.low == 2430.10
        assert reliance.close == 2465.75
        assert reliance.volume == 5000000

    def test_candle_timestamp_is_utc(self, importer: BhavcopyImporter) -> None:
        result = importer.import_csv(SAMPLE_BHAVCOPY_CSV, date(2026, 4, 29))
        ts = result.candles["RELIANCE"].timestamp
        assert ts.tzinfo is not None
        # 09:15 IST = 03:45 UTC
        assert ts.hour == 3
        assert ts.minute == 45

    def test_candle_volume_is_int(self, importer: BhavcopyImporter) -> None:
        result = importer.import_csv(SAMPLE_BHAVCOPY_CSV, date(2026, 4, 29))
        assert isinstance(result.candles["RELIANCE"].volume, int)

    def test_instrument_created_with_isin(self, importer: BhavcopyImporter) -> None:
        result = importer.import_csv(SAMPLE_BHAVCOPY_CSV, date(2026, 4, 29))
        reliance = result.instruments["RELIANCE"]
        assert reliance.symbol == "RELIANCE"
        assert reliance.exchange == "NSE"
        assert reliance.currency == "INR"
        assert reliance.isin == "INE002A01018"

    def test_result_date_matches(self, importer: BhavcopyImporter) -> None:
        result = importer.import_csv(SAMPLE_BHAVCOPY_CSV, date(2026, 4, 29))
        assert result.date == date(2026, 4, 29)


# ---------------------------------------------------------------
# Symbol filtering
# ---------------------------------------------------------------

class TestSymbolFiltering:

    def test_filter_to_specific_symbols(self, importer: BhavcopyImporter) -> None:
        result = importer.import_csv(
            SAMPLE_BHAVCOPY_CSV,
            date(2026, 4, 29),
            symbols={"RELIANCE", "TCS"},
        )
        assert len(result.candles) == 2
        assert "RELIANCE" in result.candles
        assert "TCS" in result.candles
        assert "INFY" not in result.candles

    def test_filter_to_nonexistent_symbol(self, importer: BhavcopyImporter) -> None:
        result = importer.import_csv(
            SAMPLE_BHAVCOPY_CSV,
            date(2026, 4, 29),
            symbols={"DOESNOTEXIST"},
        )
        assert len(result.candles) == 0


# ---------------------------------------------------------------
# Non-trading day handling
# ---------------------------------------------------------------

class TestNonTradingDay:

    def test_weekend_returns_empty(self, importer: BhavcopyImporter) -> None:
        # 2026-05-02 is Saturday
        result = importer.import_csv(SAMPLE_BHAVCOPY_CSV, date(2026, 5, 2))
        assert len(result.candles) == 0
        assert len(result.errors) == 1
        assert "not a trading day" in result.errors[0]

    def test_holiday_returns_empty(self, importer: BhavcopyImporter) -> None:
        # 2026-01-26 is Republic Day
        result = importer.import_csv(SAMPLE_BHAVCOPY_CSV, date(2026, 1, 26))
        assert len(result.candles) == 0
        assert "not a trading day" in result.errors[0]


# ---------------------------------------------------------------
# Error handling
# ---------------------------------------------------------------

class TestErrorHandling:

    def test_bad_ohlcv_data_reported_as_error(self, importer: BhavcopyImporter) -> None:
        # BADSTOCK has high < open (150 < 200), will fail Candle validation
        result = importer.import_csv(SAMPLE_BAD_DATA_CSV, date(2026, 4, 29))
        assert "GOODSTOCK" in result.candles
        assert "BADSTOCK" not in result.candles
        assert result.skipped >= 1
        assert any("BADSTOCK" in e for e in result.errors)

    def test_empty_csv(self, importer: BhavcopyImporter) -> None:
        result = importer.import_csv("SYMBOL, SERIES\n", date(2026, 4, 29))
        assert len(result.candles) == 0
        assert result.skipped == 0


# ---------------------------------------------------------------
# File import
# ---------------------------------------------------------------

class TestImportFile:

    def test_import_from_file(self, importer: BhavcopyImporter, tmp_path: Path) -> None:
        csv_path = tmp_path / "cm29APR2026bhav.csv"
        csv_path.write_text(SAMPLE_BHAVCOPY_CSV)
        result = importer.import_file(csv_path, trading_date=date(2026, 4, 29))
        assert len(result.candles) == 4

    def test_missing_file_raises(self, importer: BhavcopyImporter) -> None:
        with pytest.raises(FileNotFoundError):
            importer.import_file(Path("/nonexistent/file.csv"))

    def test_date_extraction_from_csv(self, importer: BhavcopyImporter, tmp_path: Path) -> None:
        csv_path = tmp_path / "somefile.csv"
        csv_path.write_text(SAMPLE_BHAVCOPY_CSV)
        result = importer.import_file(csv_path)
        # Date extracted from TIMESTAMP column: 29-APR-2026
        assert result.date == date(2026, 4, 29)


# ---------------------------------------------------------------
# Directory import
# ---------------------------------------------------------------

class TestImportDirectory:

    def test_import_multiple_files(self, importer: BhavcopyImporter, tmp_path: Path) -> None:
        # Create two CSV files for different dates
        csv1 = tmp_path / "day1.csv"
        csv1.write_text(SAMPLE_BHAVCOPY_CSV.replace("29-APR-2026", "28-APR-2026"))
        csv2 = tmp_path / "day2.csv"
        csv2.write_text(SAMPLE_BHAVCOPY_CSV)

        results = importer.import_directory(
            tmp_path,
            start=date(2026, 4, 28),
            end=date(2026, 4, 29),
        )
        assert len(results) == 2

    def test_filters_by_date_range(self, importer: BhavcopyImporter, tmp_path: Path) -> None:
        csv1 = tmp_path / "day1.csv"
        csv1.write_text(SAMPLE_BHAVCOPY_CSV)

        # Request a range that excludes the CSV's date
        results = importer.import_directory(
            tmp_path,
            start=date(2026, 1, 1),
            end=date(2026, 1, 31),
        )
        assert len(results) == 0

    def test_nonexistent_directory_raises(self, importer: BhavcopyImporter) -> None:
        with pytest.raises(NotADirectoryError):
            importer.import_directory(Path("/nonexistent"), date(2026, 1, 1), date(2026, 12, 31))
