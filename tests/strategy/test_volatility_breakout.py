from __future__ import annotations

from datetime import datetime, timezone

from candlery.core.types import Signal
from candlery.strategy.volatility_breakout import VolatilityBreakout


def _candle(close: float, volume: int, day: int) -> dict:
    return {
        "timestamp": datetime(2026, 1, day, 3, 45, tzinfo=timezone.utc),
        "open": close,
        "high": close + 1.0,
        "low": close - 1.0,
        "close": close,
        "volume": volume,
    }


def _series(closes: list[float], volumes: list[int]):
    from candlery.core.candle import Candle

    return [Candle(**_candle(c, v, i + 1)) for i, (c, v) in enumerate(zip(closes, volumes))]


def test_breakout_buy_with_volume_and_contraction() -> None:
    s = VolatilityBreakout(
        breakout_lookback=4,
        atr_period=3,
        max_atr_pct=3.0,
        volume_lookback=4,
        min_volume_ratio=1.2,
    )
    closes = [100, 100, 101, 100, 103]
    vols = [100, 100, 100, 100, 200]
    result = s.evaluate("TEST", _series(closes, vols))
    assert result is not None
    assert result.signal == Signal.BUY


def test_no_buy_when_volume_not_confirmed() -> None:
    s = VolatilityBreakout(
        breakout_lookback=4,
        atr_period=3,
        max_atr_pct=3.0,
        volume_lookback=4,
        min_volume_ratio=1.5,
    )
    closes = [100, 100, 101, 100, 103]
    vols = [100, 100, 100, 100, 120]
    assert s.evaluate("TEST", _series(closes, vols)) is None


def test_breakdown_generates_sell() -> None:
    s = VolatilityBreakout(
        breakout_lookback=4,
        atr_period=3,
        max_atr_pct=3.0,
        volume_lookback=4,
        min_volume_ratio=1.2,
    )
    closes = [100, 101, 102, 103, 95]
    vols = [100, 100, 100, 100, 100]
    result = s.evaluate("TEST", _series(closes, vols))
    assert result is not None
    assert result.signal == Signal.SELL
