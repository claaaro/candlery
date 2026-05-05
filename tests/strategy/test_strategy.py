"""Tests for Strategy base class and SMA Crossover implementation."""

from __future__ import annotations

from datetime import datetime, timezone

import pytest

from candlery.core.candle import Candle
from candlery.core.types import Signal, TradeAction
from candlery.strategy.base import Strategy
from candlery.strategy.sma_crossover import SMACrossover


# ---------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------

def _candle(close: float, day: int = 1) -> Candle:
    """Create a minimal candle with the given close price."""
    return Candle(
        timestamp=datetime(2026, 1, day, 3, 45, tzinfo=timezone.utc),
        open=close,
        high=close + 1,
        low=close - 1,
        close=close,
        volume=100000,
    )


def _candle_series(closes: list[float]) -> list[Candle]:
    """Build a list of candles from a list of close prices."""
    return [_candle(c, day=i + 1) for i, c in enumerate(closes)]


# ---------------------------------------------------------------
# Strategy ABC
# ---------------------------------------------------------------

class TestStrategyABC:

    def test_cannot_instantiate_directly(self) -> None:
        with pytest.raises(TypeError):
            Strategy()

    def test_subclass_must_implement_name(self) -> None:
        class BadStrategy(Strategy):
            def evaluate(self, symbol, candles):
                return None

        with pytest.raises(TypeError):
            BadStrategy()

    def test_subclass_must_implement_evaluate(self) -> None:
        class BadStrategy(Strategy):
            @property
            def name(self):
                return "bad"

        with pytest.raises(TypeError):
            BadStrategy()

    def test_valid_subclass_works(self) -> None:
        class MinimalStrategy(Strategy):
            @property
            def name(self):
                return "minimal"

            def evaluate(self, symbol, candles):
                return None

        s = MinimalStrategy()
        assert s.name == "minimal"
        assert s.required_history() == 1
        assert s.evaluate("TEST", []) is None


# ---------------------------------------------------------------
# SMA Crossover — Construction
# ---------------------------------------------------------------

class TestSMACrossoverConstruction:

    def test_default_periods(self) -> None:
        s = SMACrossover()
        assert s.name == "SMA(10/30)"
        assert s.required_history() == 31

    def test_custom_periods(self) -> None:
        s = SMACrossover(fast_period=5, slow_period=20)
        assert s.name == "SMA(5/20)"
        assert s.required_history() == 21

    def test_fast_must_be_less_than_slow(self) -> None:
        with pytest.raises(ValueError, match="fast_period.*must be less than slow_period"):
            SMACrossover(fast_period=30, slow_period=10)

    def test_equal_periods_raises(self) -> None:
        with pytest.raises(ValueError, match="fast_period.*must be less than slow_period"):
            SMACrossover(fast_period=10, slow_period=10)

    def test_zero_period_raises(self) -> None:
        with pytest.raises(ValueError, match="periods must be positive"):
            SMACrossover(fast_period=0, slow_period=10)

    def test_negative_period_raises(self) -> None:
        with pytest.raises(ValueError, match="periods must be positive"):
            SMACrossover(fast_period=-5, slow_period=10)

    def test_invalid_trend_filter_period_raises(self) -> None:
        with pytest.raises(ValueError, match="trend_filter_period must be positive"):
            SMACrossover(fast_period=5, slow_period=20, trend_filter_period=0)

    def test_negative_min_trend_strength_raises(self) -> None:
        with pytest.raises(ValueError, match="min_trend_strength_pct must be non-negative"):
            SMACrossover(fast_period=5, slow_period=20, min_trend_strength_pct=-0.1)

    def test_invalid_atr_filter_period_raises(self) -> None:
        with pytest.raises(ValueError, match="atr_filter_period must be positive"):
            SMACrossover(fast_period=5, slow_period=20, atr_filter_period=0)

    def test_negative_min_atr_raises(self) -> None:
        with pytest.raises(ValueError, match="min_atr_pct must be non-negative"):
            SMACrossover(fast_period=5, slow_period=20, min_atr_pct=-0.1)

    def test_negative_cooldown_raises(self) -> None:
        with pytest.raises(ValueError, match="cooldown_bars must be non-negative"):
            SMACrossover(fast_period=5, slow_period=20, cooldown_bars=-1)

    def test_invalid_trailing_stop_lookback_raises(self) -> None:
        with pytest.raises(ValueError, match="trailing_stop_lookback must be positive"):
            SMACrossover(fast_period=5, slow_period=20, trailing_stop_lookback=0)

    def test_invalid_trailing_stop_atr_period_raises(self) -> None:
        with pytest.raises(ValueError, match="trailing_stop_atr_period must be positive"):
            SMACrossover(fast_period=5, slow_period=20, trailing_stop_atr_period=0)

    def test_negative_trailing_stop_atr_mult_raises(self) -> None:
        with pytest.raises(ValueError, match="trailing_stop_atr_mult must be non-negative"):
            SMACrossover(fast_period=5, slow_period=20, trailing_stop_atr_mult=-1)


# ---------------------------------------------------------------
# SMA Crossover — Signal Logic
# ---------------------------------------------------------------

class TestSMACrossoverSignals:

    def test_not_enough_data_returns_none(self) -> None:
        s = SMACrossover(fast_period=2, slow_period=3)
        candles = _candle_series([100, 101, 102])  # need 4, have 3
        assert s.evaluate("TEST", candles) is None

    def test_buy_signal_on_golden_cross(self) -> None:
        """Fast SMA crosses above slow SMA → BUY."""
        s = SMACrossover(fast_period=2, slow_period=3)
        # Build data where fast crosses above slow:
        # Prices trending up sharply at the end
        candles = _candle_series([100, 100, 100, 110])
        # fast_prev (last 2 of [100,100,100]) = 100, slow_prev (all 3) = 100
        # fast_now (last 2 of [100,100,100,110]) = 105, slow_now = 103.33
        # fast went from <= slow to > slow → BUY
        result = s.evaluate("RELIANCE", candles)
        assert result is not None
        assert result.signal == Signal.BUY
        assert result.symbol == "RELIANCE"

    def test_sell_signal_on_death_cross(self) -> None:
        """Fast SMA crosses below slow SMA → SELL."""
        s = SMACrossover(fast_period=2, slow_period=3)
        # Prices trending down sharply at the end
        candles = _candle_series([100, 100, 100, 90])
        # fast_prev = 100, slow_prev = 100
        # fast_now = 95, slow_now = 96.67
        # fast went from >= slow to < slow → SELL
        result = s.evaluate("TCS", candles)
        assert result is not None
        assert result.signal == Signal.SELL
        assert result.symbol == "TCS"

    def test_no_signal_when_no_crossover(self) -> None:
        """No crossover → None (hold)."""
        s = SMACrossover(fast_period=2, slow_period=3)
        # Flat prices — no crossover possible
        candles = _candle_series([100, 100, 100, 100])
        result = s.evaluate("INFY", candles)
        assert result is None

    def test_no_signal_when_trending_steadily(self) -> None:
        """Steady uptrend with fast already above slow → no new crossover."""
        s = SMACrossover(fast_period=2, slow_period=3)
        # Gradually rising — fast is above slow in both current and previous
        candles = _candle_series([100, 102, 104, 106])
        # fast_prev = (102+104)/2 = 103, slow_prev = (100+102+104)/3 = 102
        # fast_now = (104+106)/2 = 105, slow_now = (102+104+106)/3 = 104
        # fast was already > slow in prev → no crossover
        result = s.evaluate("TEST", candles)
        assert result is None

    def test_result_is_trade_action(self) -> None:
        s = SMACrossover(fast_period=2, slow_period=3)
        candles = _candle_series([100, 100, 100, 110])
        result = s.evaluate("RELIANCE", candles)
        assert isinstance(result, TradeAction)

    def test_reason_contains_period_info(self) -> None:
        s = SMACrossover(fast_period=2, slow_period=3)
        candles = _candle_series([100, 100, 100, 110])
        result = s.evaluate("RELIANCE", candles)
        assert "2" in result.reason
        assert "3" in result.reason

    def test_trend_filter_blocks_buy_when_price_below_trend_sma(self) -> None:
        s = SMACrossover(
            fast_period=2,
            slow_period=3,
            trend_filter_period=4,
            min_trend_strength_pct=0.1,
        )
        candles = _candle_series([100, 95, 95, 98])
        # fast_prev=95, slow_prev=96.67 ; fast_now=96.5, slow_now=96 -> buy cross
        # trend_sma(4)=97, close=98 is above trend and strong enough, so should pass
        result = s.evaluate("TEST", candles)
        assert result is not None
        assert result.signal == Signal.BUY

        blocked = SMACrossover(
            fast_period=2,
            slow_period=3,
            trend_filter_period=4,
            min_trend_strength_pct=5.0,
        )
        blocked_result = blocked.evaluate("TEST", candles)
        assert blocked_result is None

    def test_trend_filter_blocks_sell_when_price_above_trend_sma(self) -> None:
        s = SMACrossover(
            fast_period=2,
            slow_period=3,
            trend_filter_period=4,
            min_trend_strength_pct=0.1,
        )
        candles = _candle_series([100, 105, 105, 102])
        # fast_prev=105, slow_prev=103.33 ; fast_now=103.5, slow_now=104 -> sell cross
        # trend_sma(4)=103, close=102 below trend and strong enough, so should pass
        result = s.evaluate("TEST", candles)
        assert result is not None
        assert result.signal == Signal.SELL

    def test_atr_filter_blocks_signal_when_volatility_too_low(self) -> None:
        candles = _candle_series([100, 100, 100, 110])
        blocked = SMACrossover(
            fast_period=2,
            slow_period=3,
            atr_filter_period=3,
            min_atr_pct=10.0,
        )
        assert blocked.evaluate("TEST", candles) is None

    def test_atr_filter_allows_signal_when_threshold_is_reasonable(self) -> None:
        candles = _candle_series([100, 100, 100, 110])
        allowed = SMACrossover(
            fast_period=2,
            slow_period=3,
            atr_filter_period=3,
            min_atr_pct=1.0,
        )
        result = allowed.evaluate("TEST", candles)
        assert result is not None
        assert result.signal == Signal.BUY

    def test_cooldown_blocks_immediate_flip_signal(self) -> None:
        # BUY cross at day 4, then SELL cross at day 5 should be blocked by cooldown.
        candles = _candle_series([100, 100, 100, 110, 80])
        no_cooldown = SMACrossover(fast_period=2, slow_period=3, cooldown_bars=0)
        assert no_cooldown.evaluate("TEST", candles) is not None
        cooldown = SMACrossover(fast_period=2, slow_period=3, cooldown_bars=2)
        assert cooldown.evaluate("TEST", candles) is None

    def test_cooldown_allows_signal_after_wait_period(self) -> None:
        # Prior crossover is old enough, so current crossover can pass.
        candles = _candle_series([100, 100, 100, 110, 120, 130, 90])
        cooldown = SMACrossover(fast_period=2, slow_period=3, cooldown_bars=2)
        result = cooldown.evaluate("TEST", candles)
        assert result is not None
        assert result.signal == Signal.SELL

    def test_trailing_stop_triggers_sell(self) -> None:
        candles = _candle_series([100, 105, 110, 108, 103])
        s = SMACrossover(
            fast_period=2,
            slow_period=3,
            trailing_stop_lookback=4,
            trailing_stop_atr_period=3,
            trailing_stop_atr_mult=1.0,
        )
        result = s.evaluate("TEST", candles)
        assert result is not None
        assert result.signal == Signal.SELL
        assert "trailing stop" in result.reason.lower()

    def test_trailing_stop_not_triggered_when_above_level(self) -> None:
        candles = _candle_series([100, 105, 110, 108, 109])
        s = SMACrossover(
            fast_period=2,
            slow_period=3,
            trailing_stop_lookback=4,
            trailing_stop_atr_period=3,
            trailing_stop_atr_mult=1.0,
        )
        result = s.evaluate("TEST", candles)
        assert result is not None
        assert "trailing stop" not in result.reason.lower()
