"""Tests for core type definitions."""

from __future__ import annotations

import pytest

from candlery.core.types import OrderSide, Signal, TradeAction


class TestSignal:

    def test_signal_values_exist(self) -> None:
        assert Signal.BUY is not None
        assert Signal.SELL is not None
        assert Signal.HOLD is not None

    def test_signals_are_distinct(self) -> None:
        assert Signal.BUY != Signal.SELL
        assert Signal.BUY != Signal.HOLD
        assert Signal.SELL != Signal.HOLD


class TestOrderSide:

    def test_order_sides_exist(self) -> None:
        assert OrderSide.BUY is not None
        assert OrderSide.SELL is not None

    def test_order_sides_distinct(self) -> None:
        assert OrderSide.BUY != OrderSide.SELL


class TestTradeAction:

    def test_basic_creation(self) -> None:
        action = TradeAction(symbol="RELIANCE", signal=Signal.BUY)
        assert action.symbol == "RELIANCE"
        assert action.signal == Signal.BUY
        assert action.quantity == 0
        assert action.reason == ""

    def test_with_quantity_and_reason(self) -> None:
        action = TradeAction(
            symbol="TCS",
            signal=Signal.SELL,
            quantity=100,
            reason="SMA crossover",
        )
        assert action.quantity == 100
        assert action.reason == "SMA crossover"

    def test_immutable(self) -> None:
        action = TradeAction(symbol="INFY", signal=Signal.BUY)
        with pytest.raises(AttributeError):
            action.symbol = "TCS"

    def test_empty_symbol_raises(self) -> None:
        with pytest.raises(ValueError, match="symbol cannot be empty"):
            TradeAction(symbol="", signal=Signal.BUY)

    def test_negative_quantity_raises(self) -> None:
        with pytest.raises(ValueError, match="quantity cannot be negative"):
            TradeAction(symbol="RELIANCE", signal=Signal.BUY, quantity=-1)

    def test_zero_quantity_allowed(self) -> None:
        action = TradeAction(symbol="RELIANCE", signal=Signal.BUY, quantity=0)
        assert action.quantity == 0
