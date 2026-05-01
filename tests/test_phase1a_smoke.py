"""Phase 1a smoke test: real CLI wiring over fixture CSV data."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import yaml

from candlery.cli import run_backtest


def _write_file(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content)


def test_phase1a_cli_smoke(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)

    _write_file(
        tmp_path / "smoke.yaml",
        "\n".join(
            [
                "backtest:",
                "  name: phase1a_smoke",
                "  strategy: sma_crossover",
                "  universe: smoke_universe",
                '  start_date: "2026-01-01"',
                '  end_date: "2026-01-03"',
                "  exchange: NSE",
                "  risk_profile: smoke",
                "  initial_capital: 100000.0",
                "strategy_params:",
                "  fast_period: 2",
                "  slow_period: 3",
                "",
            ]
        ),
    )

    _write_file(
        tmp_path / "universes" / "smoke_universe.yaml",
        "symbols:\n  - TEST\n",
    )

    _write_file(
        tmp_path / "smoke_defaults.yaml",
        "\n".join(
            [
                "smoke:",
                "  max_position_size: 100000",
                "  max_total_exposure: 500000",
                "  max_trades_per_day: 5",
                "  daily_loss_cap: 50000",
                "",
            ]
        ),
    )

    _write_file(
        tmp_path / "config" / "exchanges" / "nse.yaml",
        yaml.dump(
            {
                "exchange": "NSE",
                "timezone": "Asia/Kolkata",
                "has_dst": False,
                "weekend_days": [5, 6],
                "sessions": {"continuous": {"start": "09:15", "end": "15:30"}},
            }
        ),
    )
    _write_file(
        tmp_path / "config" / "holidays" / "nse_2026.json",
        json.dumps({"exchange": "NSE", "year": 2026, "holidays": []}),
    )

    data_dir = tmp_path / "data"
    data_dir.mkdir(parents=True, exist_ok=True)
    _write_file(
        data_dir / "day1.csv",
        "\n".join(
            [
                "SYMBOL,SERIES,OPEN,HIGH,LOW,CLOSE,LAST,PREVCLOSE,TOTTRDQTY,TOTTRDVAL,TIMESTAMP,TOTALTRADES,ISIN,",
                "TEST,EQ,100.00,110.00,95.00,105.00,104.00,98.00,50000,5000000,01-JAN-2026,1000,INE999Z01010,",
                "",
            ]
        ),
    )
    _write_file(
        data_dir / "day2.csv",
        "\n".join(
            [
                "SYMBOL,SERIES,OPEN,HIGH,LOW,CLOSE,LAST,PREVCLOSE,TOTTRDQTY,TOTTRDVAL,TIMESTAMP,TOTALTRADES,ISIN,",
                "TEST,EQ,106.00,112.00,104.00,111.00,110.00,105.00,50000,5000000,02-JAN-2026,1000,INE999Z01010,",
                "",
            ]
        ),
    )
    _write_file(
        data_dir / "day3.csv",
        "\n".join(
            [
                "SYMBOL,SERIES,OPEN,HIGH,LOW,CLOSE,LAST,PREVCLOSE,TOTTRDQTY,TOTTRDVAL,TIMESTAMP,TOTALTRADES,ISIN,",
                "TEST,EQ,111.00,113.00,107.00,108.00,109.00,111.00,50000,5000000,03-JAN-2026,1000,INE999Z01010,",
                "",
            ]
        ),
    )

    args = argparse.Namespace(config=str(tmp_path / "smoke.yaml"), data_dir=str(data_dir))
    run_backtest(args)
