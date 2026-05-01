"""Core type definitions for the Candlery trading system.

Defines enums and value types used across strategy, risk, and backtest
modules. These are the shared vocabulary of the system.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum, auto


class Signal(Enum):
    """Trading signal produced by a strategy."""

    BUY = auto()
    SELL = auto()
    HOLD = auto()


class OrderSide(Enum):
    """Side of an order for execution."""

    BUY = auto()
    SELL = auto()


@dataclass(frozen=True)
class TradeAction:
    """A concrete trade action proposed by a strategy.

    The risk engine evaluates this and either approves, modifies,
    or rejects it before execution.
    """

    symbol: str
    signal: Signal
    quantity: int = 0
    reason: str = ""

    def __post_init__(self):
        if not self.symbol:
            raise ValueError("TradeAction symbol cannot be empty")
        if self.quantity < 0:
            raise ValueError("TradeAction quantity cannot be negative")
