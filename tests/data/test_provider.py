"""Tests for data provider."""

from __future__ import annotations

import json
from datetime import date
from pathlib import Path

import yaml

from candlery.data.calendar import TradingCalendar
from candlery.data.provider import BhavcopyDataProvider


def _write_nse_config(config_dir: Path) -> None:
    exchanges_dir = config_dir / "exchanges"
    exchanges_dir.mkdir(parents=True, exist_ok=True)
    (exchanges_dir / "nse.yaml").write_text(
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

    holidays_dir = config_dir / "holidays"
    holidays_dir.mkdir(parents=True, exist_ok=True)
    (holidays_dir / "nse_2026.json").write_text(
        json.dumps({"exchange": "NSE", "year": 2026, "holidays": []})
    )


def _write_bhavcopy_csv(path: Path, timestamp: str) -> None:
    path.write_text(
        "\n".join(
            [
                "SYMBOL,SERIES,OPEN,HIGH,LOW,CLOSE,LAST,PREVCLOSE,TOTTRDQTY,TOTTRDVAL,TIMESTAMP,TOTALTRADES,ISIN,",
                f"TEST,EQ,100.00,110.00,95.00,105.00,104.00,98.00,50000,5000000,{timestamp},1000,INE999Z01010,",
                f"IGNORE,EQ,200.00,210.00,195.00,205.00,204.00,198.00,50000,5000000,{timestamp},1000,INE998Z01010,",
                "",
            ]
        )
    )


def test_bhavcopy_data_provider_real_importer(tmp_path: Path) -> None:
    _write_nse_config(tmp_path / "config")
    calendar = TradingCalendar("NSE", config_dir=tmp_path / "config")

    data_dir = tmp_path / "data"
    data_dir.mkdir()
    _write_bhavcopy_csv(data_dir / "day1.csv", "01-JAN-2026")
    _write_bhavcopy_csv(data_dir / "day2.csv", "02-JAN-2026")

    provider = BhavcopyDataProvider(
        data_dir=data_dir,
        start_date=date(2026, 1, 1),
        end_date=date(2026, 1, 2),
        calendar=calendar,
    )

    day1_candles = provider.get_candles_for_date(date(2026, 1, 1), {"TEST"})
    assert set(day1_candles.keys()) == {"TEST"}
    assert day1_candles["TEST"].close == 105.0

    day2_candles = provider.get_candles_for_date(date(2026, 1, 2), {"TEST"})
    assert set(day2_candles.keys()) == {"TEST"}

    day3_candles = provider.get_candles_for_date(date(2026, 1, 3), {"TEST"})
    assert day3_candles == {}
