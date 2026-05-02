"""Core backtest execution engine."""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from datetime import date
from typing import Any, Optional

from candlery.backtest.costs import TransactionCostModel
from candlery.backtest.metrics import BacktestMetrics, calculate_metrics
from candlery.backtest.portfolio import Portfolio
from candlery.core.candle import Candle
from candlery.core.types import Signal, TradeAction
from candlery.data.calendar import TradingCalendar
from candlery.journal.store import ExecutedTrade
from candlery.risk.engine import RiskEngine, RiskState
from candlery.strategy.base import Strategy

logger = logging.getLogger(__name__)


@dataclass
class BacktestConfig:
    """Configuration for a backtest run."""
    start_date: date
    end_date: date
    initial_capital: float
    universe: set[str]
    cost_model: TransactionCostModel = field(default_factory=TransactionCostModel)


@dataclass
class BacktestResult:
    """Result of a backtest run."""
    portfolio: Portfolio
    trades: list[ExecutedTrade]
    daily_equity_curve: list[float]
    metrics: BacktestMetrics


class BacktestRunner:
    """Orchestrates the backtest loop.

    Coordinates data loading, strategy evaluation, risk checks, and trade execution.
    """

    def __init__(
        self,
        config: BacktestConfig,
        calendar: TradingCalendar,
        importer: Any,  # BhavcopyImporter or generic data provider
        strategy: Strategy,
        risk_engine: RiskEngine,
    ) -> None:
        self.config = config
        self.calendar = calendar
        self.importer = importer
        self.strategy = strategy
        self.risk_engine = risk_engine
        
        self.portfolio = Portfolio(
            initial_capital=config.initial_capital,
            cost_model=config.cost_model,
        )
        self.history: dict[str, list[Candle]] = {s: [] for s in config.universe}
        
        self.trades: list[ExecutedTrade] = []
        self.daily_equity_curve: list[float] = []

    def run(self) -> BacktestResult:
        """Execute the backtest loop from start_date to end_date."""
        trading_days = self.calendar.trading_days_between(
            self.config.start_date, self.config.end_date
        )

        logger.info(f"Starting backtest: {len(trading_days)} trading days.")

        for day in trading_days:
            self._process_day(day)

        logger.info("Backtest complete.")
        
        metrics = calculate_metrics(
            self.config.initial_capital,
            self.daily_equity_curve,
            self.trades
        )
        
        return BacktestResult(
            portfolio=self.portfolio,
            trades=self.trades,
            daily_equity_curve=self.daily_equity_curve,
            metrics=metrics,
        )

    def _process_day(self, day: date) -> None:
        """Process a single trading day."""
        logger.debug(f"Processing day: {day}")
        
        # 1. Load data for the day
        try:
            daily_data = self.importer.get_candles_for_date(day, self.config.universe)
        except Exception as e:
            logger.error(f"Error loading data for {day}: {e}")
            return

        if not daily_data:
            logger.debug(f"No data found for {day}.")
            # Append yesterday's equity if we have no data, 
            # but wait, if it's a valid trading day we should record it.
            # Using current_prices from history would be better, but for MVP:
            return

        # Update price history and prepare current prices for portfolio evaluation
        current_prices: dict[str, float] = {}
        for symbol, candle in daily_data.items():
            self.history[symbol].append(candle)
            current_prices[symbol] = candle.close

        # 2. Reset and update daily portfolio stats
        self.portfolio.reset_daily_stats()
        self.portfolio.update_unrealized_pnl(current_prices)

        # 3. Evaluate strategy and execute trades
        for symbol in self.config.universe:
            symbol_history = self.history[symbol]
            if not symbol_history:
                continue
                
            current_candle = symbol_history[-1]
            current_price = current_candle.close

            # Ask Strategy for a TradeAction
            action: Optional[TradeAction] = self.strategy.evaluate(symbol, symbol_history)
            
            if not action or action.signal == Signal.HOLD:
                continue

            # Prepare RiskState
            risk_state = RiskState(
                current_price=current_price,
                current_position_value=self.portfolio.get_position_value(symbol, current_price),
                total_exposure=self.portfolio.get_total_exposure(current_prices),
                daily_trades_count=self.portfolio.daily_trades_count,
                daily_loss=self.portfolio.daily_loss,
            )

            # Ask RiskEngine to validate the action
            approved_action = self.risk_engine.evaluate(action, risk_state)

            if approved_action:
                # 4. Execute the approved action at today's close price
                exec_qty, pnl, fees = self.portfolio.execute_trade(
                    approved_action, fill_price=current_price
                )

                if exec_qty > 0:
                    trade = ExecutedTrade(
                        date=day,
                        symbol=symbol,
                        signal=approved_action.signal,
                        quantity=exec_qty,
                        price=current_price,
                        realized_pnl=pnl,
                        fees=fees,
                    )
                    self.trades.append(trade)
                
                # Update current_prices and recalculate exposure/PnL after trade
                self.portfolio.update_unrealized_pnl(current_prices)

        # Record daily equity curve after all trades for the day
        self.daily_equity_curve.append(self.portfolio.get_total_equity(current_prices))
