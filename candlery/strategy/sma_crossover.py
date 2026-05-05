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

    def __init__(
        self,
        fast_period: int = 10,
        slow_period: int = 30,
        trend_filter_period: int | None = None,
        min_trend_strength_pct: float = 0.0,
        atr_filter_period: int | None = None,
        min_atr_pct: float = 0.0,
        cooldown_bars: int = 0,
        trailing_stop_lookback: int | None = None,
        trailing_stop_atr_period: int | None = None,
        trailing_stop_atr_mult: float = 0.0,
    ) -> None:
        if fast_period <= 0 or slow_period <= 0:
            raise ValueError("SMA periods must be positive")
        if fast_period >= slow_period:
            raise ValueError(
                f"fast_period ({fast_period}) must be less than slow_period ({slow_period})"
            )
        if trend_filter_period is not None and trend_filter_period <= 0:
            raise ValueError("trend_filter_period must be positive when provided")
        if min_trend_strength_pct < 0:
            raise ValueError("min_trend_strength_pct must be non-negative")
        if atr_filter_period is not None and atr_filter_period <= 0:
            raise ValueError("atr_filter_period must be positive when provided")
        if min_atr_pct < 0:
            raise ValueError("min_atr_pct must be non-negative")
        if cooldown_bars < 0:
            raise ValueError("cooldown_bars must be non-negative")
        if trailing_stop_lookback is not None and trailing_stop_lookback <= 0:
            raise ValueError("trailing_stop_lookback must be positive when provided")
        if trailing_stop_atr_period is not None and trailing_stop_atr_period <= 0:
            raise ValueError("trailing_stop_atr_period must be positive when provided")
        if trailing_stop_atr_mult < 0:
            raise ValueError("trailing_stop_atr_mult must be non-negative")
        self._fast_period = fast_period
        self._slow_period = slow_period
        self._trend_filter_period = trend_filter_period
        self._min_trend_strength_pct = min_trend_strength_pct
        self._atr_filter_period = atr_filter_period
        self._min_atr_pct = min_atr_pct
        self._cooldown_bars = cooldown_bars
        self._trailing_stop_lookback = trailing_stop_lookback
        self._trailing_stop_atr_period = trailing_stop_atr_period
        self._trailing_stop_atr_mult = trailing_stop_atr_mult

    @property
    def name(self) -> str:
        return f"SMA({self._fast_period}/{self._slow_period})"

    def required_history(self) -> int:
        # Need slow_period + 1 bars to detect a crossover
        # (current bar's SMAs vs previous bar's SMAs)
        base_required = self._slow_period + 1
        if self._trend_filter_period is not None:
            base_required = max(base_required, self._trend_filter_period)
        if self._atr_filter_period is not None:
            # Need one extra bar for previous-close component of TR.
            base_required = max(base_required, self._atr_filter_period + 1)
        if self._trailing_stop_lookback is not None:
            base_required = max(base_required, self._trailing_stop_lookback)
        if self._trailing_stop_atr_period is not None:
            base_required = max(base_required, self._trailing_stop_atr_period + 1)
        return base_required

    def evaluate(self, symbol: str, candles: list[Candle]) -> TradeAction | None:
        if len(candles) < self.required_history():
            return None

        closes = [c.close for c in candles]
        if not self._passes_volatility_filter(candles):
            return None
        if self._trailing_stop_triggered(candles):
            return TradeAction(
                symbol=symbol,
                signal=Signal.SELL,
                reason="ATR trailing stop triggered",
            )

        # Current bar SMAs
        fast_now = _sma(closes, self._fast_period)
        slow_now = _sma(closes, self._slow_period)

        # Previous bar SMAs (exclude last candle)
        fast_prev = _sma(closes[:-1], self._fast_period)
        slow_prev = _sma(closes[:-1], self._slow_period)

        # Crossover detection
        if fast_prev <= slow_prev and fast_now > slow_now:
            if not self._passes_trend_filter(closes, is_buy=True):
                return None
            if not self._passes_cooldown(closes):
                return None
            return TradeAction(
                symbol=symbol,
                signal=Signal.BUY,
                reason=f"SMA {self._fast_period} crossed above SMA {self._slow_period}",
            )

        if fast_prev >= slow_prev and fast_now < slow_now:
            if not self._passes_trend_filter(closes, is_buy=False):
                return None
            if not self._passes_cooldown(closes):
                return None
            return TradeAction(
                symbol=symbol,
                signal=Signal.SELL,
                reason=f"SMA {self._fast_period} crossed below SMA {self._slow_period}",
            )

        return None

    def _passes_trend_filter(self, closes: list[float], *, is_buy: bool) -> bool:
        if self._trend_filter_period is None:
            return True

        trend_sma = _sma(closes, self._trend_filter_period)
        last_close = closes[-1]
        if trend_sma <= 0:
            return False

        strength_pct = abs((last_close - trend_sma) / trend_sma) * 100.0
        if strength_pct < self._min_trend_strength_pct:
            return False

        if is_buy:
            return last_close > trend_sma
        return last_close < trend_sma

    def _passes_volatility_filter(self, candles: list[Candle]) -> bool:
        if self._atr_filter_period is None:
            return True
        atr_pct = _atr_pct(candles, self._atr_filter_period)
        return atr_pct >= self._min_atr_pct

    def _passes_cooldown(self, closes: list[float]) -> bool:
        if self._cooldown_bars <= 0:
            return True
        n = len(closes)
        latest_prior = n - 2
        earliest_prior = max(self._slow_period, n - 1 - self._cooldown_bars)
        for idx in range(latest_prior, earliest_prior - 1, -1):
            if _crossover_signal_at(closes, idx, self._fast_period, self._slow_period) is not None:
                return False
        return True

    def _trailing_stop_triggered(self, candles: list[Candle]) -> bool:
        if (
            self._trailing_stop_lookback is None
            or self._trailing_stop_atr_period is None
            or self._trailing_stop_atr_mult <= 0
        ):
            return False
        highest_high = max(c.high for c in candles[-self._trailing_stop_lookback :])
        atr_abs = _atr_abs(candles, self._trailing_stop_atr_period)
        stop_level = highest_high - (self._trailing_stop_atr_mult * atr_abs)
        return candles[-1].close <= stop_level


def _sma(values: list[float], period: int) -> float:
    """Simple moving average of the last *period* values."""
    return sum(values[-period:]) / period


def _atr_pct(candles: list[Candle], period: int) -> float:
    """ATR as a percentage of the latest close."""
    if len(candles) < period + 1:
        return 0.0

    start = len(candles) - period
    true_ranges: list[float] = []
    for idx in range(start, len(candles)):
        c = candles[idx]
        prev_close = candles[idx - 1].close
        tr = max(c.high - c.low, abs(c.high - prev_close), abs(c.low - prev_close))
        true_ranges.append(tr)

    atr = sum(true_ranges) / period
    last_close = candles[-1].close
    if last_close <= 0:
        return 0.0
    return (atr / last_close) * 100.0


def _atr_abs(candles: list[Candle], period: int) -> float:
    """Absolute ATR value."""
    if len(candles) < period + 1:
        return 0.0
    start = len(candles) - period
    true_ranges: list[float] = []
    for idx in range(start, len(candles)):
        c = candles[idx]
        prev_close = candles[idx - 1].close
        tr = max(c.high - c.low, abs(c.high - prev_close), abs(c.low - prev_close))
        true_ranges.append(tr)
    return sum(true_ranges) / period


def _crossover_signal_at(
    closes: list[float], idx: int, fast_period: int, slow_period: int
) -> Signal | None:
    """Return crossover signal at candle index idx, else None."""
    if idx < slow_period:
        return None
    window = closes[: idx + 1]
    prev_window = closes[:idx]
    fast_now = _sma(window, fast_period)
    slow_now = _sma(window, slow_period)
    fast_prev = _sma(prev_window, fast_period)
    slow_prev = _sma(prev_window, slow_period)
    if fast_prev <= slow_prev and fast_now > slow_now:
        return Signal.BUY
    if fast_prev >= slow_prev and fast_now < slow_now:
        return Signal.SELL
    return None
