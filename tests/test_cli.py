"""Tests for the CLI."""

from __future__ import annotations

import argparse
from unittest.mock import MagicMock

import pytest

from candlery.cli import run_backtest


def test_cli_missing_config_raises_system_exit(tmp_path, monkeypatch) -> None:
    # Setup args
    args = argparse.Namespace(config=str(tmp_path / "nonexistent.yaml"), data_dir="dummy")
    
    # Run should exit
    with pytest.raises(SystemExit) as exc:
        run_backtest(args)
    assert exc.value.code == 1


def test_cli_run_success(tmp_path, monkeypatch) -> None:
    # 1. Create a dummy config structure
    config_file = tmp_path / "test_bt.yaml"
    config_file.write_text('''
backtest:
  name: test
  strategy: sma_crossover
  universe: test_universe
  start_date: "2026-01-01"
  end_date: "2026-01-10"
  exchange: NSE
  risk_profile: test
  initial_capital: 10000.0
strategy_params:
  fast_period: 2
  slow_period: 5
''')

    # Create universe
    universes_dir = tmp_path / "universes"
    universes_dir.mkdir()
    (universes_dir / "test_universe.yaml").write_text('''
symbols:
  - TEST
''')

    # Create risk defaults
    (tmp_path / "test_defaults.yaml").write_text('''
max_position_size: 1000
max_total_exposure: 5000
max_trades_per_day: 5
daily_loss_cap: 100
''')

    args = argparse.Namespace(config=str(config_file), data_dir=str(tmp_path))

    # 2. Mock dependencies
    # We want to mock BacktestRunner to not actually do the heavy lifting,
    # or mock DataProvider to return nothing. Let's just mock BacktestRunner.run
    
    mock_metrics = MagicMock()
    mock_metrics.total_return_pct = 5.0
    mock_metrics.max_drawdown_pct = 2.0
    mock_metrics.win_rate_pct = 50.0
    mock_metrics.sharpe_ratio = 1.2
    mock_metrics.total_trades = 10
    
    mock_result = MagicMock()
    mock_result.metrics = mock_metrics
    mock_result.trades = []
    mock_result.daily_equity_curve = [10000.0, 10500.0]
    
    mock_portfolio = MagicMock()
    mock_portfolio.get_total_equity.return_value = 10500.0
    mock_result.portfolio = mock_portfolio
    
    mock_runner_instance = MagicMock()
    mock_runner_instance.run.return_value = mock_result
    
    monkeypatch.setattr("candlery.cli.BacktestRunner", MagicMock(return_value=mock_runner_instance))
    
    # We also need to mock BhavcopyDataProvider to not scan directories
    monkeypatch.setattr("candlery.cli.BhavcopyDataProvider", MagicMock())
    
    # 3. Execute
    run_backtest(args)
    
    # If we get here without SystemExit, it worked.
    mock_runner_instance.run.assert_called_once()
