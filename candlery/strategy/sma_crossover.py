"""SMA Crossover strategy — sample implementation.

Generates BUY when fast SMA crosses above slow SMA, SELL when it
crosses below. This is the simplest trend-following strategy and
serves as the reference implementation for the Strategy interface.
"""

from __future__ import annotations

from candlery.core.candle import Candle
from candlery.core.types import Signal, TradeAction
from candlery.strategy.base import Strategy


class SMACrossover(Strategy):
    """Simple Moving Average crossover strategy.

    Args:
        fast_period: Number of bars for the fast (short) SMA.
        slow_period: Number of bars for the slow (long) SMA.
    """

    def __init__(self, fast_period: int = 10, slow_period: int = 30) -> None:
        if fast_period <= 0 or slow_period <= 0:
            raise ValueError("SMA periods must be positive")
        if fast_period >= slow_period:
            raise ValueError(
                f"fast_period ({fast_period}) must be less than slow_period ({slow_period})"
            )
        self._fast_period = fast_period
        self._slow_period = slow_period

    @property
    def name(self) -> str:
        return f"SMA({self._fast_period}/{self._slow_period})"

    def required_history(self) -> int:
        # Need slow_period + 1 bars to detect a crossover
        # (current bar's SMAs vs previous bar's SMAs)
        return self._slow_period + 1

    def evaluate(self, symbol: str, candles: list[Candle]) -> TradeAction | None:
        if len(candles) < self.required_history():
            return None

        closes = [c.close for c in candles]

        # Current bar SMAs
        fast_now = _sma(closes, self._fast_period)
        slow_now = _sma(closes, self._slow_period)

        # Previous bar SMAs (exclude last candle)
        fast_prev = _sma(closes[:-1], self._fast_period)
        slow_prev = _sma(closes[:-1], self._slow_period)

        # Crossover detection
        if fast_prev <= slow_prev and fast_now > slow_now:
            return TradeAction(
                symbol=symbol,
                signal=Signal.BUY,
                reason=f"SMA {self._fast_period} crossed above SMA {self._slow_period}",
            )

        if fast_prev >= slow_prev and fast_now < slow_now:
            return TradeAction(
                symbol=symbol,
                signal=Signal.SELL,
                reason=f"SMA {self._fast_period} crossed below SMA {self._slow_period}",
            )

        return None


def _sma(values: list[float], period: int) -> float:
    """Simple moving average of the last *period* values."""
    return sum(values[-period:]) / period
