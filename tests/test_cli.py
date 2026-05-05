"""Tests for the CLI."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import pytest
import yaml

from candlery.cli import run_backtest, run_paper


def test_cli_missing_config_raises_system_exit(tmp_path, monkeypatch) -> None:
    # Setup args
    args = argparse.Namespace(config=str(tmp_path / "nonexistent.yaml"), data_dir="dummy")
    
    # Run should exit
    with pytest.raises(SystemExit) as exc:
        run_backtest(args)
    assert exc.value.code == 1


def test_cli_run_success(tmp_path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)

    config_file = tmp_path / "test_bt.yaml"
    config_file.write_text(
        """
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
"""
    )

    universes_dir = tmp_path / "universes"
    universes_dir.mkdir()
    (universes_dir / "test_universe.yaml").write_text(
        """
symbols:
  - TEST
"""
    )

    (tmp_path / "test_defaults.yaml").write_text(
        """
test:
  max_position_size: 1000
  max_total_exposure: 5000
  max_trades_per_day: 5
  daily_loss_cap: 100
"""
    )

    config_dir = tmp_path / "config"
    (config_dir / "exchanges").mkdir(parents=True)
    (config_dir / "holidays").mkdir(parents=True)
    (config_dir / "exchanges" / "nse.yaml").write_text(
        yaml.dump(
            {
                "exchange": "NSE",
                "timezone": "Asia/Kolkata",
                "has_dst": False,
                "weekend_days": [5, 6],
                "sessions": {"continuous": {"start": "09:15", "end": "15:30"}},
            }
        )
    )
    (config_dir / "holidays" / "nse_2026.json").write_text(
        json.dumps({"exchange": "NSE", "year": 2026, "holidays": []})
    )

    data_dir = tmp_path / "data"
    data_dir.mkdir()
    (data_dir / "day1.csv").write_text(
        "\n".join(
            [
                "SYMBOL,SERIES,OPEN,HIGH,LOW,CLOSE,LAST,PREVCLOSE,TOTTRDQTY,TOTTRDVAL,TIMESTAMP,TOTALTRADES,ISIN,",
                "TEST,EQ,100.00,110.00,95.00,105.00,104.00,98.00,50000,5000000,01-JAN-2026,1000,INE999Z01010,",
                "",
            ]
        )
    )
    (data_dir / "day2.csv").write_text(
        "\n".join(
            [
                "SYMBOL,SERIES,OPEN,HIGH,LOW,CLOSE,LAST,PREVCLOSE,TOTTRDQTY,TOTTRDVAL,TIMESTAMP,TOTALTRADES,ISIN,",
                "TEST,EQ,105.00,112.00,101.00,108.00,107.00,105.00,50000,5000000,02-JAN-2026,1000,INE999Z01010,",
                "",
            ]
        )
    )

    csv_prefix = tmp_path / "out" / "candlery_run"
    args = argparse.Namespace(
        config=str(config_file),
        data_dir=str(data_dir),
        csv=str(csv_prefix),
    )
    run_backtest(args)

    assert Path(str(csv_prefix) + "_summary.csv").exists()
    assert Path(str(csv_prefix) + "_trades.csv").exists()
    assert Path(str(csv_prefix) + "_equity.csv").exists()


def test_cli_unsupported_strategy_raises(tmp_path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)

    config_file = tmp_path / "test_bt.yaml"
    config_file.write_text(
        """
backtest:
  name: test
  strategy: unknown_strategy
  universe: test_universe
  start_date: "2026-01-01"
  end_date: "2026-01-10"
  exchange: NSE
  risk_profile: test
  initial_capital: 10000.0
strategy_params: {}
"""
    )

    universes_dir = tmp_path / "universes"
    universes_dir.mkdir()
    (universes_dir / "test_universe.yaml").write_text("symbols:\n  - TEST\n")
    (tmp_path / "test_defaults.yaml").write_text(
        """
test:
  max_position_size: 1000
  max_total_exposure: 5000
  max_trades_per_day: 5
  daily_loss_cap: 100
"""
    )
    config_dir = tmp_path / "config"
    (config_dir / "exchanges").mkdir(parents=True)
    (config_dir / "holidays").mkdir(parents=True)
    (config_dir / "exchanges" / "nse.yaml").write_text(
        yaml.dump(
            {
                "exchange": "NSE",
                "timezone": "Asia/Kolkata",
                "has_dst": False,
                "weekend_days": [5, 6],
                "sessions": {"continuous": {"start": "09:15", "end": "15:30"}},
            }
        )
    )
    (config_dir / "holidays" / "nse_2026.json").write_text(
        json.dumps({"exchange": "NSE", "year": 2026, "holidays": []})
    )
    data_dir = tmp_path / "data"
    data_dir.mkdir()
    (data_dir / "day1.csv").write_text(
        "SYMBOL,SERIES,OPEN,HIGH,LOW,CLOSE,LAST,PREVCLOSE,TOTTRDQTY,TOTTRDVAL,TIMESTAMP,TOTALTRADES,ISIN,\n"
        "TEST,EQ,100.00,110.00,95.00,105.00,104.00,98.00,50000,5000000,01-JAN-2026,1000,INE999Z01010,\n"
    )

    args = argparse.Namespace(config=str(config_file), data_dir=str(data_dir), csv=None)
    with pytest.raises(SystemExit) as exc:
        run_backtest(args)
    assert exc.value.code == 1


def test_cli_paper_run_and_resume_writes_journal(tmp_path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)

    config_file = tmp_path / "test_bt.yaml"
    config_file.write_text(
        """
backtest:
  name: test
  strategy: sma_crossover
  universe: test_universe
  start_date: "2026-01-01"
  end_date: "2026-01-03"
  exchange: NSE
  risk_profile: test
  initial_capital: 10000.0
strategy_params:
  fast_period: 2
  slow_period: 3
"""
    )
    universes_dir = tmp_path / "universes"
    universes_dir.mkdir()
    (universes_dir / "test_universe.yaml").write_text("symbols:\n  - TEST\n")
    (tmp_path / "test_defaults.yaml").write_text(
        """
test:
  max_position_size: 1000
  max_total_exposure: 5000
  max_trades_per_day: 5
  daily_loss_cap: 100
"""
    )
    config_dir = tmp_path / "config"
    (config_dir / "exchanges").mkdir(parents=True)
    (config_dir / "holidays").mkdir(parents=True)
    (config_dir / "exchanges" / "nse.yaml").write_text(
        yaml.dump(
            {
                "exchange": "NSE",
                "timezone": "Asia/Kolkata",
                "has_dst": False,
                "weekend_days": [5, 6],
                "sessions": {"continuous": {"start": "09:15", "end": "15:30"}},
            }
        )
    )
    (config_dir / "holidays" / "nse_2026.json").write_text(
        json.dumps({"exchange": "NSE", "year": 2026, "holidays": []})
    )
    data_dir = tmp_path / "data"
    data_dir.mkdir()
    for day, close in [(1, 100.0), (2, 103.0), (3, 101.0)]:
        (data_dir / f"day{day}.csv").write_text(
            "SYMBOL,SERIES,OPEN,HIGH,LOW,CLOSE,LAST,PREVCLOSE,TOTTRDQTY,TOTTRDVAL,TIMESTAMP,TOTALTRADES,ISIN,\n"
            f"TEST,EQ,{close:.2f},{close+1:.2f},{close-1:.2f},{close:.2f},{close:.2f},{close:.2f},50000,5000000,{day:02d}-JAN-2026,1000,INE999Z01010,\n"
        )

    journal_path = tmp_path / "paper_run.jsonl"
    args_first = argparse.Namespace(
        config=str(config_file),
        data_dir=str(data_dir),
        journal=str(journal_path),
        run_id="paper-test",
        resume=False,
        csv=str(tmp_path / "out" / "paper_first"),
    )
    run_paper(args_first)
    assert journal_path.exists()

    args_resume = argparse.Namespace(
        config=str(config_file),
        data_dir=str(data_dir),
        journal=str(journal_path),
        run_id="paper-test",
        resume=True,
        csv=str(tmp_path / "out" / "paper_resume"),
    )
    run_paper(args_resume)
    assert Path(str(args_resume.csv) + "_summary.csv").exists()
