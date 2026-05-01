"""Tests for backtest metrics calculation."""

from __future__ import annotations

import math
from datetime import date

from candlery.backtest.metrics import calculate_metrics
from candlery.core.types import Signal
from candlery.journal.store import ExecutedTrade


def test_empty_metrics_returned_if_no_equity_curve() -> None:
    metrics = calculate_metrics(10000.0, [], [])
    assert metrics.total_return_pct == 0.0
    assert metrics.max_drawdown_pct == 0.0
    assert metrics.win_rate_pct == 0.0
    assert metrics.sharpe_ratio == 0.0
    assert metrics.total_trades == 0


def test_total_return_calculation() -> None:
    equity_curve = [10000.0, 10500.0, 11000.0, 15000.0]
    metrics = calculate_metrics(10000.0, equity_curve, [])
    
    assert metrics.total_return_pct == 50.0  # (15000 - 10000) / 10000 * 100


def test_max_drawdown_calculation() -> None:
    # Peak is 15000. Trough is 9000.
    # Drawdown = (15000 - 9000) / 15000 = 6000 / 15000 = 0.40 -> 40%
    equity_curve = [10000.0, 15000.0, 12000.0, 9000.0, 11000.0]
    metrics = calculate_metrics(10000.0, equity_curve, [])
    
    assert metrics.max_drawdown_pct == 40.0


def test_win_rate_calculation() -> None:
    trades = [
        ExecutedTrade(date(2026, 1, 1), "TEST", Signal.BUY, 10, 100.0, 0.0),
        ExecutedTrade(date(2026, 1, 2), "TEST", Signal.SELL, 5, 110.0, 50.0),  # Win
        ExecutedTrade(date(2026, 1, 3), "TEST", Signal.SELL, 5, 90.0, -50.0),   # Loss
        ExecutedTrade(date(2026, 1, 4), "TEST2", Signal.BUY, 10, 100.0, 0.0),
        ExecutedTrade(date(2026, 1, 5), "TEST2", Signal.SELL, 10, 150.0, 500.0), # Win
    ]
    
    metrics = calculate_metrics(10000.0, [10000.0], trades)
    
    # Total sells = 3. Winning sells = 2.
    assert metrics.win_rate_pct == (2 / 3) * 100.0
    assert metrics.total_trades == 5


def test_sharpe_ratio_calculation() -> None:
    # We construct a curve with known daily returns
    # Let initial = 100
    # Day 1: 101 (+1%)
    # Day 2: 102.01 (+1%)
    # Day 3: 103.0301 (+1%)
    # Return series is constant 0.01, std_dev should be 0, sharpe ratio is 0 because std_dev is 0.
    # We need a varied return series to have non-zero std_dev.
    
    # initial = 100
    # day 1: 110 (+10%)
    # day 2: 104.5 (-5%)
    # day 3: 114.95 (+10%)
    # returns: 0.1, -0.05, 0.1
    # mean: 0.05
    # variance: ((0.1-0.05)^2 + (-0.05-0.05)^2 + (0.1-0.05)^2) / 2 = (0.0025 + 0.01 + 0.0025) / 2 = 0.015 / 2 = 0.0075
    # stddev = sqrt(0.0075) = 0.0866025
    
    equity_curve = [110.0, 104.5, 114.95]
    metrics = calculate_metrics(100.0, equity_curve, [])
    
    mean = 0.05
    std_dev = math.sqrt(0.0075)
    expected_sharpe = (mean / std_dev) * math.sqrt(252)
    
    assert math.isclose(metrics.sharpe_ratio, expected_sharpe, rel_tol=1e-5)
