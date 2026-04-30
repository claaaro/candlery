"""Tests for TradingCalendar."""

from __future__ import annotations

import json
from datetime import date, datetime, timezone
from pathlib import Path

import pytest
import yaml

from candlery.data.calendar import TradingCalendar


# ---------------------------------------------------------------
# Fixtures — create minimal config files in a temp directory
# ---------------------------------------------------------------

@pytest.fixture()
def config_dir(tmp_path: Path) -> Path:
    """Build a minimal config tree matching the real layout."""
    # Exchange config
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

    # Holidays — mirrors the real nse_2026.json (complete list)
    holidays_dir = tmp_path / "holidays"
    holidays_dir.mkdir()
    (holidays_dir / "nse_2026.json").write_text(
        json.dumps({
            "exchange": "NSE",
            "year": 2026,
            "holidays": [
                {"date": "2026-01-15", "name": "Municipal Corporation Election"},
                {"date": "2026-01-26", "name": "Republic Day"},
                {"date": "2026-03-03", "name": "Holi"},
                {"date": "2026-03-26", "name": "Shri Ram Navami"},
                {"date": "2026-03-31", "name": "Shri Mahavir Jayanti"},
                {"date": "2026-04-03", "name": "Good Friday"},
                {"date": "2026-04-14", "name": "Dr. Ambedkar Jayanti"},
                {"date": "2026-05-01", "name": "Maharashtra Day"},
                {"date": "2026-05-28", "name": "Bakri Id"},
                {"date": "2026-06-26", "name": "Muharram"},
                {"date": "2026-09-14", "name": "Ganesh Chaturthi"},
                {"date": "2026-10-02", "name": "Mahatma Gandhi Jayanti"},
                {"date": "2026-10-20", "name": "Dussehra"},
                {"date": "2026-11-10", "name": "Diwali Balipratipada"},
                {"date": "2026-11-24", "name": "Prakash Gurpurb Sri Guru Nanak Dev"},
                {"date": "2026-12-25", "name": "Christmas"},
            ],
        })
    )
    return tmp_path


@pytest.fixture()
def calendar(config_dir: Path) -> TradingCalendar:
    return TradingCalendar("NSE", config_dir=config_dir)


# ---------------------------------------------------------------
# is_trading_day
# ---------------------------------------------------------------

class TestIsTradingDay:

    def test_regular_weekday_is_trading_day(self, calendar: TradingCalendar) -> None:
        # 2026-04-29 is a Wednesday
        assert calendar.is_trading_day(date(2026, 4, 29)) is True

    def test_saturday_is_not_trading_day(self, calendar: TradingCalendar) -> None:
        # 2026-05-02 is a Saturday
        assert calendar.is_trading_day(date(2026, 5, 2)) is False

    def test_sunday_is_not_trading_day(self, calendar: TradingCalendar) -> None:
        # 2026-05-03 is a Sunday
        assert calendar.is_trading_day(date(2026, 5, 3)) is False

    def test_weekday_holiday_is_not_trading_day(self, calendar: TradingCalendar) -> None:
        # Republic Day — 2026-01-26 is a Monday
        assert calendar.is_trading_day(date(2026, 1, 26)) is False

    def test_another_weekday_holiday(self, calendar: TradingCalendar) -> None:
        # Maharashtra Day — 2026-05-01 is a Friday
        assert calendar.is_trading_day(date(2026, 5, 1)) is False

    def test_day_after_holiday_is_trading_day(self, calendar: TradingCalendar) -> None:
        # Jan 27, 2026 is a Tuesday (day after Republic Day)
        assert calendar.is_trading_day(date(2026, 1, 27)) is True

    def test_regular_friday_is_trading_day(self, calendar: TradingCalendar) -> None:
        # 2026-04-24 is a Friday (not a holiday)
        assert calendar.is_trading_day(date(2026, 4, 24)) is True

    def test_good_friday_is_not_trading_day(self, calendar: TradingCalendar) -> None:
        # 2026-04-03 is Good Friday
        assert calendar.is_trading_day(date(2026, 4, 3)) is False


# ---------------------------------------------------------------
# trading_days_between
# ---------------------------------------------------------------

class TestTradingDaysBetween:

    def test_full_week_no_holidays(self, calendar: TradingCalendar) -> None:
        # Mon Apr 27 to Fri May 1 — but May 1 is Maharashtra Day!
        # So only 4 trading days: Apr 27 (Mon), 28 (Tue), 29 (Wed), 30 (Thu)
        days = calendar.trading_days_between(date(2026, 4, 27), date(2026, 5, 1))
        assert len(days) == 4
        assert days[0] == date(2026, 4, 27)
        assert days[-1] == date(2026, 4, 30)
        assert date(2026, 5, 1) not in days

    def test_clean_full_week(self, calendar: TradingCalendar) -> None:
        # Mon Apr 6 to Fri Apr 10 — no holidays this week
        days = calendar.trading_days_between(date(2026, 4, 6), date(2026, 4, 10))
        assert len(days) == 5

    def test_week_with_weekend(self, calendar: TradingCalendar) -> None:
        # Mon Apr 6 to Sun Apr 12 — still 5 trading days (no holidays)
        days = calendar.trading_days_between(date(2026, 4, 6), date(2026, 4, 12))
        assert len(days) == 5

    def test_week_with_holiday(self, calendar: TradingCalendar) -> None:
        # Week containing Republic Day (Mon Jan 26, 2026)
        days = calendar.trading_days_between(date(2026, 1, 26), date(2026, 1, 30))
        # Jan 26 is holiday, Jan 27-30 are Tue-Fri → 4 trading days
        assert date(2026, 1, 26) not in days
        assert len(days) == 4

    def test_single_day_trading(self, calendar: TradingCalendar) -> None:
        day = date(2026, 4, 29)  # Wednesday
        days = calendar.trading_days_between(day, day)
        assert days == [day]

    def test_single_day_weekend(self, calendar: TradingCalendar) -> None:
        day = date(2026, 5, 2)  # Saturday
        days = calendar.trading_days_between(day, day)
        assert days == []

    def test_start_after_end_raises(self, calendar: TradingCalendar) -> None:
        with pytest.raises(ValueError, match="start.*must be <= end"):
            calendar.trading_days_between(date(2026, 5, 1), date(2026, 4, 1))

    def test_empty_range_all_weekend(self, calendar: TradingCalendar) -> None:
        # Sat May 2 to Sun May 3
        days = calendar.trading_days_between(date(2026, 5, 2), date(2026, 5, 3))
        assert days == []


# ---------------------------------------------------------------
# market_open_utc / market_close_utc
# ---------------------------------------------------------------

class TestMarketTimesUTC:

    def test_market_open_utc(self, calendar: TradingCalendar) -> None:
        # NSE opens 09:15 IST = 03:45 UTC
        dt = calendar.market_open_utc(date(2026, 4, 29))
        assert dt.tzinfo is not None, "must be timezone-aware"
        assert dt.hour == 3
        assert dt.minute == 45
        assert dt.year == 2026
        assert dt.month == 4
        assert dt.day == 29

    def test_market_close_utc(self, calendar: TradingCalendar) -> None:
        # NSE closes 15:30 IST = 10:00 UTC
        dt = calendar.market_close_utc(date(2026, 4, 29))
        assert dt.tzinfo is not None, "must be timezone-aware"
        assert dt.hour == 10
        assert dt.minute == 0

    def test_open_before_close(self, calendar: TradingCalendar) -> None:
        d = date(2026, 4, 29)
        assert calendar.market_open_utc(d) < calendar.market_close_utc(d)

    def test_utc_offset_is_5_30(self, calendar: TradingCalendar) -> None:
        # IST is always UTC+5:30, no DST
        d = date(2026, 1, 15)  # Winter
        open_utc = calendar.market_open_utc(d)
        # 09:15 IST - 5:30 = 03:45 UTC (same all year)
        assert open_utc.hour == 3
        assert open_utc.minute == 45

        d2 = date(2026, 7, 15)  # Summer — should be identical
        open_utc2 = calendar.market_open_utc(d2)
        assert open_utc2.hour == 3
        assert open_utc2.minute == 45


# ---------------------------------------------------------------
# Config loading edge cases
# ---------------------------------------------------------------

class TestConfigLoading:

    def test_missing_exchange_config_raises(self, tmp_path: Path) -> None:
        (tmp_path / "exchanges").mkdir()
        (tmp_path / "holidays").mkdir()
        with pytest.raises(FileNotFoundError, match="Exchange config not found"):
            TradingCalendar("NSE", config_dir=tmp_path)

    def test_multiple_holiday_years(self, config_dir: Path) -> None:
        # Add a second year
        holidays_dir = config_dir / "holidays"
        (holidays_dir / "nse_2025.json").write_text(
            json.dumps({
                "exchange": "NSE",
                "year": 2025,
                "holidays": [
                    {"date": "2025-02-26", "name": "Mahashivratri"},
                ],
            })
        )
        cal = TradingCalendar("NSE", config_dir=config_dir)
        # Both years loaded
        assert date(2025, 2, 26) in cal.holidays
        assert date(2026, 1, 26) in cal.holidays

    def test_no_holidays_dir_loads_empty(self, tmp_path: Path) -> None:
        exchanges_dir = tmp_path / "exchanges"
        exchanges_dir.mkdir()
        (exchanges_dir / "nse.yaml").write_text(
            yaml.dump({
                "timezone": "Asia/Kolkata",
                "weekend_days": [5, 6],
                "sessions": {"continuous": {"start": "09:15", "end": "15:30"}},
            })
        )
        cal = TradingCalendar("NSE", config_dir=tmp_path)
        assert len(cal.holidays) == 0
        # Weekdays still work
        assert cal.is_trading_day(date(2026, 4, 29)) is True

    def test_exchange_property(self, calendar: TradingCalendar) -> None:
        assert calendar.exchange == "NSE"

    def test_holiday_count_2026(self, calendar: TradingCalendar) -> None:
        # Verify all 16 holidays loaded
        assert len(calendar.holidays) == 16
