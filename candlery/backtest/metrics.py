"""Performance metrics calculation for backtests."""

from __future__ import annotations

import math
import statistics
from dataclasses import dataclass

from candlery.journal.store import ExecutedTrade


@dataclass(frozen=True)
class BacktestMetrics:
    """Calculated performance metrics for a backtest."""
    total_return_pct: float
    max_drawdown_pct: float
    win_rate_pct: float
    sharpe_ratio: float
    total_trades: int


def calculate_metrics(
    initial_capital: float,
    daily_equity_curve: list[float],
    trades: list[ExecutedTrade]
) -> BacktestMetrics:
    """Calculate performance metrics from equity curve and trades.
    
    Assumes daily equity curve points and a 0% risk-free rate for Sharpe.
    """
    if not daily_equity_curve:
        return BacktestMetrics(0.0, 0.0, 0.0, 0.0, 0)
        
    final_equity = daily_equity_curve[-1]
    total_return_pct = ((final_equity - initial_capital) / initial_capital) * 100.0

    # Max Drawdown
    max_drawdown_pct = 0.0
    peak = initial_capital
    for equity in daily_equity_curve:
        if equity > peak:
            peak = equity
        drawdown = (peak - equity) / peak * 100.0
        if drawdown > max_drawdown_pct:
            max_drawdown_pct = drawdown

    # Win Rate
    # A trade cycle completes on a SELL.
    sells = [t for t in trades if t.signal.name == "SELL"]
    total_sells = len(sells)
    if total_sells > 0:
        winning_sells = sum(1 for t in sells if t.realized_pnl > 0)
        win_rate_pct = (winning_sells / total_sells) * 100.0
    else:
        win_rate_pct = 0.0

    # Sharpe Ratio
    # Calculate daily returns
    daily_returns = []
    prev_equity = initial_capital
    for equity in daily_equity_curve:
        daily_return = (equity - prev_equity) / prev_equity
        daily_returns.append(daily_return)
        prev_equity = equity

    if len(daily_returns) > 1:
        mean_return = statistics.mean(daily_returns)
        std_dev = statistics.stdev(daily_returns)
        if std_dev > 0:
            sharpe_ratio = (mean_return / std_dev) * math.sqrt(252)
        else:
            sharpe_ratio = 0.0
    else:
        sharpe_ratio = 0.0

    return BacktestMetrics(
        total_return_pct=total_return_pct,
        max_drawdown_pct=max_drawdown_pct,
        win_rate_pct=win_rate_pct,
        sharpe_ratio=sharpe_ratio,
        total_trades=len(trades)
    )
