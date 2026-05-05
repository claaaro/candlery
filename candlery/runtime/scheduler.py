"""Scheduler abstractions.

Phase 3B goal: provide a minimal seam that allows the existing backtest
runner to obtain the sequence of trading days from an injected scheduler,
without changing strategy/risk/execution semantics.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from datetime import date

from candlery.data.calendar import TradingCalendar


class Scheduler(ABC):
    """Provides a sequence of trading days for a given date range."""

    @abstractmethod
    def trading_days_between(self, start_date: date, end_date: date) -> list[date]:
        raise NotImplementedError


class CalendarScheduler(Scheduler):
    """Adapter around the existing TradingCalendar implementation."""

    def __init__(self, calendar: TradingCalendar) -> None:
        self._calendar = calendar

    def trading_days_between(self, start_date: date, end_date: date) -> list[date]:
        return self._calendar.trading_days_between(start_date, end_date)

