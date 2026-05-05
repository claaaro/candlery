from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime, timezone
from pathlib import Path

import pytest

from candlery.backtest.costs import TransactionCostModel
from candlery.backtest.portfolio import Portfolio
from candlery.backtest.runner import BacktestConfig, BacktestRunner
from candlery.core.candle import Candle
from candlery.core.types import Signal, TradeAction
from candlery.data.calendar import TradingCalendar
from candlery.journal.run_journal import RunJournal
from candlery.risk.engine import RiskEngine
from candlery.strategy.base import Strategy


class MockTradingCalendar:
    def trading_days_between(self, start: date, end: date) -> list[date]:
        days: list[date] = []
        d = start
        while d <= end:
            days.append(d)
            d = date.fromordinal(d.toordinal() + 1)
        return days


class MockDataImporter:
    def __init__(self, data: dict[date, dict[str, Candle]]):
        self.data = data

    def get_candles_for_date(self, day: date, universe: set[str]) -> dict[str, Candle]:
        if day not in self.data:
            return {}
        return {s: c for s, c in self.data[day].items() if s in universe}


def make_candle(day: int, price: float) -> Candle:
    return Candle(
        timestamp=datetime(2026, 1, day, 3, 45, tzinfo=timezone.utc),
        open=price,
        high=price,
        low=price,
        close=price,
        volume=100,
    )


@dataclass
class RiskCfg:
    max_position_size: float = 10000.0
    max_total_exposure: float = 50000.0
    max_trades_per_day: int = 5
    daily_loss_cap: float = 1000.0


def risk_engine() -> RiskEngine:
    cfg = RiskCfg()
    return RiskEngine(
        {
            "max_position_size": cfg.max_position_size,
            "max_total_exposure": cfg.max_total_exposure,
            "max_trades_per_day": cfg.max_trades_per_day,
            "daily_loss_cap": cfg.daily_loss_cap,
        }
    )


class AlwaysBuyStrategy(Strategy):
    @property
    def name(self) -> str:
        return "AlwaysBuy"

    def evaluate(self, symbol: str, candles: list[Candle]) -> TradeAction | None:
        return TradeAction(symbol=symbol, signal=Signal.BUY, quantity=10)


class CrashOnSecondBarStrategy(Strategy):
    @property
    def name(self) -> str:
        return "CrashOnSecondBar"

    def evaluate(self, symbol: str, candles: list[Candle]) -> TradeAction | None:
        if len(candles) >= 2:
            raise RuntimeError("simulated crash")
        return TradeAction(symbol=symbol, signal=Signal.BUY, quantity=10)


def test_crash_resume_matches_uninterrupted(tmp_path: Path) -> None:
    journal_path = tmp_path / "journal.jsonl"
    run_id = "r1"

    data = {
        date(2026, 1, 1): {"TEST": make_candle(1, 100.0)},
        date(2026, 1, 2): {"TEST": make_candle(2, 101.0)},
        date(2026, 1, 3): {"TEST": make_candle(3, 102.0)},
    }

    config = BacktestConfig(
        start_date=date(2026, 1, 1),
        end_date=date(2026, 1, 3),
        initial_capital=10000.0,
        universe={"TEST"},
        cost_model=TransactionCostModel.from_bps(stt_buy_bps=10, stt_sell_bps=10),
    )

    cal = MockTradingCalendar()
    importer = MockDataImporter(data)
    risk = risk_engine()

    # 1) Run and crash on day2 evaluation; ensure only day1 is journaled.
    journal = RunJournal(journal_path)
    runner1 = BacktestRunner(
        config=config,
        calendar=cal,  # type: ignore[arg-type]
        importer=importer,
        strategy=CrashOnSecondBarStrategy(),
        risk_engine=risk,
        journal=journal,
        run_id=run_id,
        resume_from_journal=False,
    )
    with pytest.raises(RuntimeError):
        runner1.run()

    assert journal.has_completed_day(run_id=run_id, day=date(2026, 1, 1)) is True
    assert journal.has_completed_day(run_id=run_id, day=date(2026, 1, 2)) is False

    # 2) Resume into a clean run and compare with uninterrupted baseline.
    runner_resumed = BacktestRunner(
        config=config,
        calendar=cal,  # type: ignore[arg-type]
        importer=importer,
        strategy=AlwaysBuyStrategy(),
        risk_engine=risk,
        journal=journal,
        run_id=run_id,
        resume_from_journal=True,
    )
    result_resumed = runner_resumed.run()

    baseline_journal = RunJournal(tmp_path / "journal_baseline.jsonl")
    runner_baseline = BacktestRunner(
        config=config,
        calendar=cal,  # type: ignore[arg-type]
        importer=importer,
        strategy=AlwaysBuyStrategy(),
        risk_engine=risk,
        journal=baseline_journal,
        run_id="r2",
        resume_from_journal=False,
    )
    result_baseline = runner_baseline.run()

    assert result_resumed.portfolio.cash == pytest.approx(
        result_baseline.portfolio.cash
    )
    assert result_resumed.portfolio.positions.keys() == result_baseline.portfolio.positions.keys()
    assert result_resumed.portfolio.positions["TEST"].quantity == result_baseline.portfolio.positions["TEST"].quantity
    assert result_resumed.portfolio.positions["TEST"].average_price == pytest.approx(
        result_baseline.portfolio.positions["TEST"].average_price
    )

    assert len(result_resumed.trades) == len(result_baseline.trades)
    for t1, t2 in zip(result_resumed.trades, result_baseline.trades):
        assert t1.date == t2.date
        assert t1.symbol == t2.symbol
        assert t1.signal == t2.signal
        assert t1.quantity == t2.quantity
        assert t1.price == pytest.approx(t2.price)
        assert t1.realized_pnl == pytest.approx(t2.realized_pnl)
        assert t1.fees == pytest.approx(t2.fees)

    assert len(result_resumed.daily_equity_curve) == len(result_baseline.daily_equity_curve)
    for e1, e2 in zip(result_resumed.daily_equity_curve, result_baseline.daily_equity_curve):
        assert e1 == pytest.approx(e2)

