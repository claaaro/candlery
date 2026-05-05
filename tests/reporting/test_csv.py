"""Tests for CSV reporting bundle."""

from __future__ import annotations

from datetime import date
from pathlib import Path

from candlery.backtest.metrics import BacktestMetrics
from candlery.backtest.portfolio import Portfolio
from candlery.backtest.runner import BacktestResult
from candlery.core.types import Signal
from candlery.journal.store import ExecutedTrade
from candlery.reporting.csv import write_csv_bundle


def test_write_csv_bundle_creates_three_files(tmp_path: Path) -> None:
    result = BacktestResult(
        portfolio=Portfolio(initial_capital=1000.0),
        trades=[
            ExecutedTrade(
                date=date(2026, 1, 1),
                symbol="TEST",
                signal=Signal.BUY,
                quantity=5,
                price=100.0,
                realized_pnl=0.0,
                fees=0.5,
            )
        ],
        daily_equity_curve=[1000.0, 990.0, 1010.0],
        metrics=BacktestMetrics(1.0, 1.0, 0.0, 0.5, 1),
    )
    out = write_csv_bundle(
        tmp_path / "reports" / "run_a",
        result,
        title="run_a",
        start_date=date(2026, 1, 1),
        end_date=date(2026, 1, 3),
        universe_size=1,
    )

    assert out["summary"].exists()
    assert out["trades"].exists()
    assert out["equity"].exists()

    summary_text = out["summary"].read_text(encoding="utf-8")
    trades_text = out["trades"].read_text(encoding="utf-8")
    equity_text = out["equity"].read_text(encoding="utf-8")

    assert "field,value" in summary_text
    assert "total_fees,0.500000" in summary_text
    assert "date,symbol,signal,quantity,price,realized_pnl,fees" in trades_text
    assert "index,equity,drawdown_pct" in equity_text
