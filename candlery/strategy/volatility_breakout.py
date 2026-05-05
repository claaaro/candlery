"""Volatility-contraction breakout strategy.

This strategy looks for:
1) Volatility contraction (ATR percentage below a threshold)
2) Breakout above the previous N-bar high with volume confirmation
"""

from __future__ import annotations

from candlery.core.candle import Candle
from candlery.core.types import Signal, TradeAction
from candlery.strategy.base import Strategy


class VolatilityBreakout(Strategy):
    def __init__(
        self,
        breakout_lookback: int = 20,
        atr_period: int = 14,
        max_atr_pct: float = 3.0,
        volume_lookback: int = 20,
        min_volume_ratio: float = 1.2,
    ) -> None:
        if breakout_lookback <= 1:
            raise ValueError("breakout_lookback must be > 1")
        if atr_period <= 0:
            raise ValueError("atr_period must be positive")
        if max_atr_pct < 0:
            raise ValueError("max_atr_pct must be non-negative")
        if volume_lookback <= 0:
            raise ValueError("volume_lookback must be positive")
        if min_volume_ratio < 0:
            raise ValueError("min_volume_ratio must be non-negative")

        self._breakout_lookback = breakout_lookback
        self._atr_period = atr_period
        self._max_atr_pct = max_atr_pct
        self._volume_lookback = volume_lookback
        self._min_volume_ratio = min_volume_ratio

    @property
    def name(self) -> str:
        return "VolatilityBreakout"

    def required_history(self) -> int:
        return max(self._breakout_lookback + 1, self._atr_period + 1, self._volume_lookback + 1)

    def evaluate(self, symbol: str, candles: list[Candle]) -> TradeAction | None:
        if len(candles) < self.required_history():
            return None

        last = candles[-1]

        # Exit on downside breakdown below prior N-bar low.
        prior_lows = [c.low for c in candles[-self._breakout_lookback - 1 : -1]]
        if last.close < min(prior_lows):
            return TradeAction(symbol=symbol, signal=Signal.SELL, reason="Breakdown below range low")

        atr_pct = _atr_pct(candles, self._atr_period)
        if atr_pct > self._max_atr_pct:
            return None

        prior_highs = [c.high for c in candles[-self._breakout_lookback - 1 : -1]]
        breakout_level = max(prior_highs)
        if last.close <= breakout_level:
            return None

        avg_vol = _avg_volume(candles[-self._volume_lookback - 1 : -1])
        if avg_vol <= 0:
            return None
        vol_ratio = last.volume / avg_vol
        if vol_ratio < self._min_volume_ratio:
            return None

        return TradeAction(symbol=symbol, signal=Signal.BUY, reason="Volatility contraction breakout")


def _avg_volume(candles: list[Candle]) -> float:
    return sum(c.volume for c in candles) / len(candles)


def _atr_pct(candles: list[Candle], period: int) -> float:
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
    if candles[-1].close <= 0:
        return 0.0
    return (atr / candles[-1].close) * 100.0
