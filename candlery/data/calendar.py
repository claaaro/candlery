"""Trading calendar for exchange-aware date and time logic.

Loads exchange configuration (timezone, sessions) from YAML and
holiday calendars from JSON. All output times are UTC.
"""

from __future__ import annotations

import json
from datetime import date, datetime, time, timedelta
from pathlib import Path
from zoneinfo import ZoneInfo

import yaml


class TradingCalendar:
    """Determines trading days and market hours for a given exchange.

    All returned datetimes are timezone-aware UTC. The calendar is
    fully deterministic — no external API calls, no system clock
    dependency.
    """

    def __init__(self, exchange: str, config_dir: Path | str = "config") -> None:
        config_dir = Path(config_dir)
        self._exchange = exchange
        self._load_exchange_config(config_dir / "exchanges" / f"{exchange.lower()}.yaml")
        self._holidays: set[date] = set()
        self._load_holidays(config_dir / "holidays")

    # ------------------------------------------------------------------
    # Config loading
    # ------------------------------------------------------------------

    def _load_exchange_config(self, path: Path) -> None:
        if not path.exists():
            raise FileNotFoundError(f"Exchange config not found: {path}")
        with open(path) as f:
            cfg = yaml.safe_load(f)

        self._timezone = ZoneInfo(cfg["timezone"])
        self._weekend_days: set[int] = set(cfg.get("weekend_days", [5, 6]))

        sessions = cfg.get("sessions", {})
        continuous = sessions.get("continuous", {})
        self._market_open_local = time.fromisoformat(continuous["start"])
        self._market_close_local = time.fromisoformat(continuous["end"])

    def _load_holidays(self, holidays_dir: Path) -> None:
        prefix = self._exchange.lower() + "_"
        if not holidays_dir.is_dir():
            return
        for path in sorted(holidays_dir.glob(f"{prefix}*.json")):
            with open(path) as f:
                data = json.load(f)
            for entry in data.get("holidays", []):
                self._holidays.add(date.fromisoformat(entry["date"]))

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def is_trading_day(self, d: date) -> bool:
        """Return True if *d* is a valid trading day (not weekend, not holiday)."""
        if d.weekday() in self._weekend_days:
            return False
        if d in self._holidays:
            return False
        return True

    def trading_days_between(self, start: date, end: date) -> list[date]:
        """Return all trading days in the inclusive range [start, end].

        Raises ValueError if start > end.
        """
        if start > end:
            raise ValueError(f"start ({start}) must be <= end ({end})")
        days: list[date] = []
        current = start
        while current <= end:
            if self.is_trading_day(current):
                days.append(current)
            current += timedelta(days=1)
        return days

    def market_open_utc(self, d: date) -> datetime:
        """Return the market open time for date *d* as a UTC datetime.

        For NSE: 09:15 IST → 03:45 UTC.
        """
        local_dt = datetime.combine(d, self._market_open_local, tzinfo=self._timezone)
        return local_dt.astimezone(ZoneInfo("UTC"))

    def market_close_utc(self, d: date) -> datetime:
        """Return the market close time for date *d* as a UTC datetime.

        For NSE: 15:30 IST → 10:00 UTC.
        """
        local_dt = datetime.combine(d, self._market_close_local, tzinfo=self._timezone)
        return local_dt.astimezone(ZoneInfo("UTC"))

    @property
    def exchange(self) -> str:
        return self._exchange

    @property
    def timezone(self) -> ZoneInfo:
        return self._timezone

    @property
    def holidays(self) -> frozenset[date]:
        return frozenset(self._holidays)
