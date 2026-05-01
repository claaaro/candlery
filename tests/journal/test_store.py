"""Tests for trade journal."""

from __future__ import annotations

from datetime import date

from candlery.core.types import Signal
from candlery.journal.store import ExecutedTrade


def test_executed_trade_value_property() -> None:
    trade = ExecutedTrade(
        date=date(2026, 1, 1),
        symbol="TEST",
        signal=Signal.BUY,
        quantity=150,
        price=10.0,
        realized_pnl=0.0,
    )
    
    assert trade.value == 1500.0
