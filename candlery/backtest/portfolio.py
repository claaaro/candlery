"""Portfolio state management for the backtester."""

from __future__ import annotations

import logging
from dataclasses import dataclass, field

from candlery.backtest.costs import TransactionCostModel
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
    cost_model: TransactionCostModel = field(default_factory=TransactionCostModel)
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

    def execute_trade(self, action: TradeAction, fill_price: float) -> tuple[int, float, float]:
        """Execute a trade, updating cash and positions.

        Args:
            action: Approved TradeAction (must have positive quantity).
            fill_price: The execution price.
            
        Returns:
            Tuple of (executed_quantity, realized_pnl, fees).

            *Buy*: ``realized_pnl`` is always ``0``; ``fees`` is STT + brokerage on the buy leg.
            *Sell*: ``realized_pnl`` is **net** of sell-side fees; ``fees`` is STT + brokerage
            on the sell leg.
        """
        if action.signal == Signal.HOLD:
            return 0, 0.0, 0.0
        if action.quantity <= 0:
            return 0, 0.0, 0.0

        symbol = action.symbol
        pos = self.positions.get(symbol)
        buy_rate = self.cost_model.buy_fee_fraction()

        if action.signal == Signal.BUY:
            eff_price = fill_price * (1.0 + buy_rate)
            if eff_price <= 0:
                return 0, 0.0, 0.0
            max_affordable = int(self.cash / eff_price)
            if action.quantity > max_affordable:
                if max_affordable <= 0:
                    return 0, 0.0, 0.0
                logger.warning(
                    "Insufficient cash to buy %s %s (incl. fees). Filling %s.",
                    action.quantity,
                    symbol,
                    max_affordable,
                )
                action = TradeAction(
                    symbol=action.symbol,
                    signal=action.signal,
                    quantity=max_affordable,
                    reason=action.reason + " [Partial Fill due to cash]",
                )

            notional = action.quantity * fill_price
            fees = self.cost_model.buy_fees(notional)
            total_out = notional + fees
            if total_out > self.cash + 1e-9:
                return 0, 0.0, 0.0

            if not pos:
                pos = Position(symbol=symbol)
                self.positions[symbol] = pos

            self.cash -= total_out
            pos.add(action.quantity, fill_price)
            self.daily_trades_count += 1
            logger.info(f"Executed BUY {action.quantity} {symbol} @ {fill_price} (fees {fees:.2f})")
            return action.quantity, 0.0, fees

        elif action.signal == Signal.SELL:
            if not pos:
                return 0, 0.0, 0.0
                
            # Can't sell more than we own (no short selling in Phase 1)
            sell_qty = min(action.quantity, pos.quantity)
            if sell_qty <= 0:
                return 0, 0.0, 0.0
                
            notional = sell_qty * fill_price
            fees = self.cost_model.sell_fees(notional)
            gross_pnl = pos.remove(sell_qty, fill_price)
            net_pnl = gross_pnl - fees

            self.cash += notional - fees
            self.daily_realized_pnl += net_pnl
            self.daily_trades_count += 1
            logger.info(
                f"Executed SELL {sell_qty} {symbol} @ {fill_price}. Gross PnL: {gross_pnl}, fees: {fees:.2f}"
            )
            return sell_qty, net_pnl, fees
            
        return 0, 0.0, 0.0
