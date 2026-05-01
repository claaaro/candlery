"""Core backtest execution engine."""

from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import date
from typing import Any, Optional

from candlery.backtest.portfolio import Portfolio
from candlery.core.candle import Candle
from candlery.core.types import Signal, TradeAction
from candlery.data.calendar import TradingCalendar
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
        
        self.portfolio = Portfolio(initial_capital=config.initial_capital)
        self.history: dict[str, list[Candle]] = {s: [] for s in config.universe}
        
        # We will collect daily equity curves and trade journals later,
        # but for now we execute the loop.

    def run(self) -> Portfolio:
        """Execute the backtest loop from start_date to end_date."""
        trading_days = self.calendar.trading_days_between(
            self.config.start_date, self.config.end_date
        )

        logger.info(f"Starting backtest: {len(trading_days)} trading days.")

        for day in trading_days:
            self._process_day(day)

        logger.info("Backtest complete.")
        return self.portfolio

    def _process_day(self, day: date) -> None:
        """Process a single trading day."""
        logger.debug(f"Processing day: {day}")
        
        # 1. Load data for the day
        try:
            # Importer interface: import_csv or import_date(day)?
            # The BhavcopyImporter has `import_file` and `import_directory`.
            # For backtesting, we assume the data provider has a method to get candles for a date.
            # Let's assume `get_candles_for_date(day, universe)`
            # Wait, BhavcopyImporter returns an ImportResult. We need a clean abstraction.
            # For Phase 1, we expect the caller to wrap the importer into a provider
            # that returns a dict of symbol -> Candle.
            daily_data = self.importer.get_candles_for_date(day, self.config.universe)
        except Exception as e:
            logger.error(f"Error loading data for {day}: {e}")
            return

        if not daily_data:
            logger.debug(f"No data found for {day}.")
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
                # If strategy says HOLD, but we want to sell all if we are out of data? No.
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
                # For Phase 1 MVP, we simulate EOD execution at the closing price.
                self.portfolio.execute_trade(approved_action, fill_price=current_price)
                
                # Update current_prices and recalculate exposure/PnL after trade?
                # The portfolio updates itself during execute_trade, but exposure relies on prices.
                self.portfolio.update_unrealized_pnl(current_prices)
