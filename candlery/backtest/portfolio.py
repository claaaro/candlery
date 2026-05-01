"""Portfolio state management for the backtester."""

from __future__ import annotations

import logging
from dataclasses import dataclass, field

from candlery.core.types import Signal, TradeAction

logger = logging.getLogger(__name__)


@dataclass
class Position:
    """A current holding in a specific instrument."""

    symbol: str
    quantity: int = 0
    average_price: float = 0.0

    @property
    def is_active(self) -> bool:
        return self.quantity > 0

    def add(self, quantity: int, price: float) -> None:
        """Add to the position and recalculate average price."""
        if quantity <= 0:
            raise ValueError("Must add a positive quantity")
        if price <= 0:
            raise ValueError("Price must be positive")

        total_value = (self.quantity * self.average_price) + (quantity * price)
        self.quantity += quantity
        self.average_price = total_value / self.quantity

    def remove(self, quantity: int, price: float) -> float:
        """Remove from the position and return the realized PnL.

        Args:
            quantity: Amount to sell.
            price: Execution price.

        Returns:
            Realized Profit and Loss from this sale.
        """
        if quantity <= 0:
            raise ValueError("Must remove a positive quantity")
        if quantity > self.quantity:
            raise ValueError(f"Cannot remove {quantity} shares, only {self.quantity} held")

        realized_pnl = (price - self.average_price) * quantity
        self.quantity -= quantity

        if self.quantity == 0:
            self.average_price = 0.0

        return realized_pnl


@dataclass
class Portfolio:
    """Tracks cash, positions, and performance during a backtest."""

    initial_capital: float
    cash: float = field(init=False)
    positions: dict[str, Position] = field(default_factory=dict, init=False)
    
    # Daily tracking for risk limits
    daily_trades_count: int = field(default=0, init=False)
    daily_realized_pnl: float = field(default=0.0, init=False)
    daily_unrealized_pnl: float = field(default=0.0, init=False)

    def __post_init__(self):
        self.cash = self.initial_capital

    def reset_daily_stats(self) -> None:
        """Reset daily counters at the start of a new trading day."""
        self.daily_trades_count = 0
        self.daily_realized_pnl = 0.0
        self.daily_unrealized_pnl = 0.0

    def update_unrealized_pnl(self, current_prices: dict[str, float]) -> None:
        """Update daily unrealized PnL based on current market prices."""
        pnl = 0.0
        for symbol, pos in self.positions.items():
            if pos.is_active and symbol in current_prices:
                pnl += (current_prices[symbol] - pos.average_price) * pos.quantity
        self.daily_unrealized_pnl = pnl

    @property
    def daily_loss(self) -> float:
        """Calculate total loss today (realized + unrealized). Returns a positive number for loss."""
        total_pnl = self.daily_realized_pnl + self.daily_unrealized_pnl
        return -total_pnl if total_pnl < 0 else 0.0

    def get_position_value(self, symbol: str, current_price: float) -> float:
        """Get the current market value of a position."""
        pos = self.positions.get(symbol)
        if pos and pos.is_active:
            return pos.quantity * current_price
        return 0.0

    def get_total_exposure(self, current_prices: dict[str, float]) -> float:
        """Calculate total market exposure across all active positions."""
        exposure = 0.0
        for symbol, pos in self.positions.items():
            if pos.is_active:
                price = current_prices.get(symbol, pos.average_price)
                exposure += pos.quantity * price
        return exposure

    def get_total_equity(self, current_prices: dict[str, float]) -> float:
        """Calculate total portfolio value (cash + exposure)."""
        return self.cash + self.get_total_exposure(current_prices)

    def execute_trade(self, action: TradeAction, fill_price: float) -> tuple[int, float]:
        """Execute a trade, updating cash and positions.

        Args:
            action: Approved TradeAction (must have positive quantity).
            fill_price: The execution price.
            
        Returns:
            Tuple of (executed_quantity, realized_pnl).
        """
        if action.signal == Signal.HOLD:
            return 0, 0.0
        if action.quantity <= 0:
            return 0, 0.0

        symbol = action.symbol
        pos = self.positions.get(symbol)

        if action.signal == Signal.BUY:
            cost = action.quantity * fill_price
            if cost > self.cash:
                logger.warning(f"Insufficient cash to buy {action.quantity} {symbol}. Cash: {self.cash}, Cost: {cost}")
                # Partial fill
                action = TradeAction(
                    symbol=action.symbol,
                    signal=action.signal,
                    quantity=int(self.cash / fill_price),
                    reason=action.reason + " [Partial Fill due to cash]"
                )
                cost = action.quantity * fill_price
                if action.quantity <= 0:
                    return 0, 0.0

            if not pos:
                pos = Position(symbol=symbol)
                self.positions[symbol] = pos

            self.cash -= cost
            pos.add(action.quantity, fill_price)
            self.daily_trades_count += 1
            logger.info(f"Executed BUY {action.quantity} {symbol} @ {fill_price}")
            return action.quantity, 0.0

        elif action.signal == Signal.SELL:
            if not pos:
                return 0, 0.0
                
            # Can't sell more than we own (no short selling in Phase 1)
            sell_qty = min(action.quantity, pos.quantity)
            if sell_qty <= 0:
                return 0, 0.0
                
            proceeds = sell_qty * fill_price
            pnl = pos.remove(sell_qty, fill_price)
            
            self.cash += proceeds
            self.daily_realized_pnl += pnl
            self.daily_trades_count += 1
            logger.info(f"Executed SELL {sell_qty} {symbol} @ {fill_price}. PnL: {pnl}")
            return sell_qty, pnl
            
        return 0, 0.0
