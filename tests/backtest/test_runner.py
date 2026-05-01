"""Tests for BacktestRunner."""

from __future__ import annotations

from datetime import date, datetime, timezone

import pytest

from candlery.backtest.portfolio import Portfolio
from candlery.backtest.runner import BacktestConfig, BacktestRunner
from candlery.core.candle import Candle
from candlery.core.types import Signal, TradeAction
from candlery.risk.engine import RiskEngine
from candlery.strategy.base import Strategy


class MockTradingCalendar:
    def trading_days_between(self, start: date, end: date) -> list[date]:
        # Return inclusive list of dates (simplification for test)
        days = []
        d = start
        while d <= end:
            days.append(d)
            d = date.fromordinal(d.toordinal() + 1)
        return days


class MockDataImporter:
    def __init__(self, data: dict[date, dict[str, Candle]]):
        self.data = data

    def get_candles_for_date(self, day: date, universe: set[str]) -> dict[str, Candle]:
        # Return available data for requested day and universe
        if day not in self.data:
            return {}
        return {s: c for s, c in self.data[day].items() if s in universe}


class AlwaysBuyStrategy(Strategy):
    @property
    def name(self) -> str:
        return "AlwaysBuy"

    def evaluate(self, symbol: str, candles: list[Candle]) -> TradeAction | None:
        return TradeAction(symbol=symbol, signal=Signal.BUY, quantity=10, reason="Always")


class AlternatingStrategy(Strategy):
    @property
    def name(self) -> str:
        return "Alternating"

    def evaluate(self, symbol: str, candles: list[Candle]) -> TradeAction | None:
        if len(candles) % 2 == 1:
            return TradeAction(symbol=symbol, signal=Signal.BUY, quantity=10)
        else:
            return TradeAction(symbol=symbol, signal=Signal.SELL, quantity=10)


@pytest.fixture
def risk_engine() -> RiskEngine:
    config = {
        "max_position_size": 10000.0,
        "max_total_exposure": 50000.0,
        "max_trades_per_day": 5,
        "daily_loss_cap": 1000.0,
    }
    return RiskEngine(config)


def make_candle(day: int, price: float) -> Candle:
    return Candle(
        timestamp=datetime(2026, 1, day, 3, 45, tzinfo=timezone.utc),
        open=price,
        high=price,
        low=price,
        close=price,
        volume=100,
    )


class TestBacktestRunner:
    def test_run_executes_trades(self, risk_engine: RiskEngine) -> None:
        # Setup 3 days of data
        data = {
            date(2026, 1, 1): {"TEST": make_candle(1, 100.0)},
            date(2026, 1, 2): {"TEST": make_candle(2, 110.0)},
            date(2026, 1, 3): {"TEST": make_candle(3, 120.0)},
        }
        
        config = BacktestConfig(
            start_date=date(2026, 1, 1),
            end_date=date(2026, 1, 3),
            initial_capital=10000.0,
            universe={"TEST"},
        )
        
        runner = BacktestRunner(
            config=config,
            calendar=MockTradingCalendar(),
            importer=MockDataImporter(data),
            strategy=AlternatingStrategy(),
            risk_engine=risk_engine,
        )
        
        result = runner.run()
        
        # Day 1: Buy 10 @ 100 -> Cash 9000, Pos 10
        # Day 2: Sell 10 @ 110 -> Cash 10100, Pos 0
        # Day 3: Buy 10 @ 120 -> Cash 8900, Pos 10
        
        assert result.portfolio.cash == 8900.0
        assert result.portfolio.positions["TEST"].quantity == 10
        # Total equity = cash (8900) + exposure (10 * 120 = 1200) = 10100
        assert result.portfolio.get_total_equity({"TEST": 120.0}) == 10100.0

    def test_risk_limits_prevent_excessive_trades(self, risk_engine: RiskEngine) -> None:
        # Setup data
        data = {
            date(2026, 1, 1): {"TEST": make_candle(1, 100.0)},
        }
        
        config = BacktestConfig(
            start_date=date(2026, 1, 1),
            end_date=date(2026, 1, 1),
            initial_capital=100000.0,
            universe={"TEST"},
        )
        
        # Override risk engine to allow only 1 trade, but strategy wants 10.
        # Actually, risk engine operates per trade action. 
        # If strategy asks for 200 units, max position is 10000, so it will cap at 100 units.
        runner = BacktestRunner(
            config=config,
            calendar=MockTradingCalendar(),
            importer=MockDataImporter(data),
            strategy=AlwaysBuyStrategy(), # wants 10, but risk allows 100. We will change strategy output to 200.
            risk_engine=risk_engine,
        )
        
        # Monkey patch strategy to request 200 units
        class GreedyStrategy(AlwaysBuyStrategy):
            def evaluate(self, symbol: str, candles: list[Candle]) -> TradeAction | None:
                return TradeAction(symbol=symbol, signal=Signal.BUY, quantity=200)
                
        runner.strategy = GreedyStrategy()
        result = runner.run()
        
        # Expected: Risk limits to 100 shares (10000 / 100).
        assert result.portfolio.positions["TEST"].quantity == 100
        assert result.portfolio.cash == 90000.0
