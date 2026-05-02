"""Tests for static HTML report generation."""

from __future__ import annotations

from datetime import date
from pathlib import Path

from candlery.backtest.metrics import BacktestMetrics
from candlery.backtest.portfolio import Portfolio
from candlery.backtest.runner import BacktestResult
from candlery.core.types import Signal
from candlery.journal.store import ExecutedTrade
from candlery.reporting.html import render_html_report, write_html_report


def test_render_html_includes_metrics_and_escapes_symbol() -> None:
    portfolio = Portfolio(initial_capital=10_000.0)
    metrics = BacktestMetrics(
        total_return_pct=5.5,
        max_drawdown_pct=2.0,
        win_rate_pct=60.0,
        sharpe_ratio=1.25,
        total_trades=2,
    )
    trades = [
        ExecutedTrade(
            date=date(2026, 1, 2),
            symbol="<script>evil</script>",
            signal=Signal.BUY,
            quantity=10,
            price=100.0,
            realized_pnl=0.0,
        ),
    ]
    result = BacktestResult(
        portfolio=portfolio,
        trades=trades,
        daily_equity_curve=[10_000.0, 10_500.0],
        metrics=metrics,
    )
    html_out = render_html_report(
        result,
        title="smoke",
        start_date=date(2026, 1, 1),
        end_date=date(2026, 1, 3),
        universe_size=1,
    )
    assert "5.50%" in html_out or "5.5" in html_out
    assert "<script>evil</script>" not in html_out
    assert "&lt;script&gt;evil&lt;/script&gt;" in html_out
    assert "Equity curve" in html_out


def test_write_html_report_creates_file(tmp_path: Path) -> None:
    portfolio = Portfolio(initial_capital=100.0)
    result = BacktestResult(
        portfolio=portfolio,
        trades=[],
        daily_equity_curve=[100.0],
        metrics=BacktestMetrics(0.0, 0.0, 0.0, 0.0, 0),
    )
    out = tmp_path / "nested" / "out.html"
    write_html_report(out, result, title="t")
    assert out.exists()
    text = out.read_text(encoding="utf-8")
    assert "<!DOCTYPE html>" in text
    assert "Not enough equity observations" in text or "Performance" in text


def test_equity_chart_requires_two_points_message() -> None:
    portfolio = Portfolio(initial_capital=100.0)
    result = BacktestResult(
        portfolio=portfolio,
        trades=[],
        daily_equity_curve=[100.0],
        metrics=BacktestMetrics(0.0, 0.0, 0.0, 0.0, 0),
    )
    html_out = render_html_report(result, title="one-point")
    assert "Not enough equity observations" in html_out
