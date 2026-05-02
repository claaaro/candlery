"""Trade journaling functionality."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date

from candlery.core.types import Signal


@dataclass(frozen=True)
class ExecutedTrade:
    """Record of a trade that was actually filled in the backtest."""
    
    date: date
    symbol: str
    signal: Signal
    quantity: int
    price: float
    realized_pnl: float
    fees: float = 0.0

    @property
    def value(self) -> float:
        """Total value of the transaction."""
        return self.quantity * self.price
