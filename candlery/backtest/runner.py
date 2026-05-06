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
from candlery.journal.run_journal import JournalState, PortfolioSnapshot, RunJournal
from candlery.risk.engine import RiskEngine, RiskState
from candlery.strategy.base import Strategy
from candlery.runtime.scheduler import CalendarScheduler, Scheduler

logger = logging.getLogger(__name__)


@dataclass
class BacktestConfig:
    """Configuration for a backtest run."""
    start_date: date
    end_date: date
    initial_capital: float
    universe: set[str]
    cost_model: TransactionCostModel = field(default_factory=TransactionCostModel)
    close_all_at_end: bool = False


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
        *,
        scheduler: Scheduler | None = None,
        journal: RunJournal | None = None,
        run_id: str = "default",
        resume_from_journal: bool = False,
    ) -> None:
        self.config = config
        self.calendar = calendar
        self.scheduler = scheduler or CalendarScheduler(calendar)
        self.importer = importer
        self.strategy = strategy
        self.risk_engine = risk_engine
        self.journal = journal
        self.run_id = run_id
        self.resume_from_journal = resume_from_journal
        
        self.portfolio = Portfolio(
            initial_capital=config.initial_capital,
            cost_model=config.cost_model,
        )
        self.history: dict[str, list[Candle]] = {s: [] for s in config.universe}
        
        self.trades: list[ExecutedTrade] = []
        self.daily_equity_curve: list[float] = []

    def run(self) -> BacktestResult:
        """Execute the backtest loop from start_date to end_date."""
        trading_days = self.scheduler.trading_days_between(
            self.config.start_date, self.config.end_date
        )

        completed_days: set[date] = set()
        if self.journal is not None and self.resume_from_journal:
            state = self.journal.load(run_id=self.run_id)
            completed_days = set(state.completed_days)
            self.portfolio.cash = state.portfolio_snapshot.cash
            # Rehydrate positions into the portfolio.
            self.portfolio.positions = dict(state.portfolio_snapshot.positions)
            self.trades = list(state.trades)
            self.daily_equity_curve = list(state.daily_equity_curve)
        elif self.journal is not None:
            completed_days = set()

        logger.info(f"Starting backtest: {len(trading_days)} trading days.")

        for day in trading_days:
            if day in completed_days and self.journal is not None:
                # Rebuild strategy history only (no execution, no journal duplication).
                try:
                    daily_data = self.importer.get_candles_for_date(
                        day, self.config.universe
                    )
                except Exception as e:
                    logger.error("Error loading data for %s (resume mode): %s", day, e)
                    continue
                if not daily_data:
                    continue
                for symbol, candle in daily_data.items():
                    self.history[symbol].append(candle)
                continue

            trades_before = len(self.trades)
            equity_before = len(self.daily_equity_curve)

            self._process_day(day)

            # If we advanced the equity curve, we consider the day "completed".
            if self.journal is not None and len(self.daily_equity_curve) > equity_before:
                day_trades = self.trades[trades_before:]
                daily_equity_value = self.daily_equity_curve[-1]
                snapshot = PortfolioSnapshot(
                    cash=self.portfolio.cash, positions=self.portfolio.positions
                )
                self.journal.append_day_completed(
                    run_id=self.run_id,
                    day=day,
                    portfolio_snapshot=snapshot,
                    trades=day_trades,
                    daily_equity_value=daily_equity_value,
                )

        if self.config.close_all_at_end and trading_days:
            self._close_all_positions_on_final_day(trading_days[-1])

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

    def _close_all_positions_on_final_day(self, final_day: date) -> None:
        """Force-close all active positions at final day close for realized-only comparisons."""
        current_prices: dict[str, float] = {}
        for symbol, candles in self.history.items():
            if candles:
                current_prices[symbol] = candles[-1].close

        if not current_prices:
            return

        close_trades: list[ExecutedTrade] = []
        for symbol, pos in list(self.portfolio.positions.items()):
            if pos.quantity <= 0:
                continue
            price = current_prices.get(symbol)
            if price is None:
                continue

            action = TradeAction(
                symbol=symbol,
                signal=Signal.SELL,
                quantity=pos.quantity,
                reason="Forced liquidation at end of backtest window",
            )
            exec_qty, pnl, fees = self.portfolio.execute_trade(action, fill_price=price)
            if exec_qty > 0:
                close_trades.append(
                    ExecutedTrade(
                        date=final_day,
                        symbol=symbol,
                        signal=Signal.SELL,
                        quantity=exec_qty,
                        price=price,
                        realized_pnl=pnl,
                        fees=fees,
                    )
                )

        if not close_trades:
            return

        self.trades.extend(close_trades)
        self.portfolio.update_unrealized_pnl(current_prices)
        if self.daily_equity_curve:
            # Replace final-day equity with post-liquidation cash+exposure.
            self.daily_equity_curve[-1] = self.portfolio.get_total_equity(current_prices)

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
