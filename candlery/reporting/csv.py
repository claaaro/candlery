"""CSV reporting outputs for backtest results."""

from __future__ import annotations

import csv
from datetime import date
from pathlib import Path

from candlery.backtest.runner import BacktestResult


def _drawdown_series_pct(equity: list[float]) -> list[float]:
    if not equity:
        return []
    peak = equity[0]
    out: list[float] = []
    for v in equity:
        if v > peak:
            peak = v
        dd = ((peak - v) / peak) * 100.0 if peak > 0 else 0.0
        out.append(dd)
    return out


def write_csv_bundle(
    prefix_path: Path | str,
    result: BacktestResult,
    *,
    title: str,
    start_date: date | None = None,
    end_date: date | None = None,
    universe_size: int | None = None,
) -> dict[str, Path]:
    """Write summary, trades and equity CSV files using a shared prefix.

    Example:
      prefix_path='reports/run1' -> run1_summary.csv, run1_trades.csv, run1_equity.csv
    """
    prefix = Path(prefix_path)
    if prefix.suffix.lower() == ".csv":
        prefix = prefix.with_suffix("")
    prefix.parent.mkdir(parents=True, exist_ok=True)

    summary_path = prefix.with_name(prefix.name + "_summary.csv")
    trades_path = prefix.with_name(prefix.name + "_trades.csv")
    equity_path = prefix.with_name(prefix.name + "_equity.csv")

    initial = result.portfolio.initial_capital
    final_eq = result.daily_equity_curve[-1] if result.daily_equity_curve else initial
    total_fees = sum(t.fees for t in result.trades)
    drawdowns = _drawdown_series_pct(result.daily_equity_curve)
    max_drawdown = max(drawdowns) if drawdowns else 0.0

    with summary_path.open("w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["field", "value"])
        w.writerow(["title", title])
        w.writerow(["start_date", str(start_date) if start_date else ""])
        w.writerow(["end_date", str(end_date) if end_date else ""])
        w.writerow(["universe_size", universe_size if universe_size is not None else ""])
        w.writerow(["initial_capital", f"{initial:.6f}"])
        w.writerow(["final_equity", f"{final_eq:.6f}"])
        w.writerow(["total_return_pct", f"{result.metrics.total_return_pct:.6f}"])
        w.writerow(["max_drawdown_pct", f"{result.metrics.max_drawdown_pct:.6f}"])
        w.writerow(["max_drawdown_curve_pct", f"{max_drawdown:.6f}"])
        w.writerow(["win_rate_pct", f"{result.metrics.win_rate_pct:.6f}"])
        w.writerow(["sharpe_ratio", f"{result.metrics.sharpe_ratio:.6f}"])
        w.writerow(["total_trades", result.metrics.total_trades])
        w.writerow(["total_fees", f"{total_fees:.6f}"])

    with trades_path.open("w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["date", "symbol", "signal", "quantity", "price", "realized_pnl", "fees"])
        for t in result.trades:
            w.writerow(
                [
                    str(t.date),
                    t.symbol,
                    t.signal.name,
                    t.quantity,
                    f"{t.price:.6f}",
                    f"{t.realized_pnl:.6f}",
                    f"{t.fees:.6f}",
                ]
            )

    with equity_path.open("w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["index", "equity", "drawdown_pct"])
        for i, eq in enumerate(result.daily_equity_curve):
            dd = drawdowns[i] if i < len(drawdowns) else 0.0
            w.writerow([i, f"{eq:.6f}", f"{dd:.6f}"])

    return {
        "summary": summary_path,
        "trades": trades_path,
        "equity": equity_path,
    }
