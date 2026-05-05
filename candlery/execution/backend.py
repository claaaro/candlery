"""Execution backend interface.

This is the strategy-agnostic seam that Phase 3 will use to separate:
- "what to do" (Strategy) from
- "how it gets filled" (ExecutionBackend).

In Phase 3A we only add the interface and a paper-only implementation; we do
not refactor the existing backtest loop yet.
"""

from __future__ import annotations

from abc import ABC, abstractmethod

from candlery.core.types import TradeAction


class ExecutionBackend(ABC):
    """Turn an approved TradeAction into an execution outcome."""

    @abstractmethod
    def execute(self, action: TradeAction, *, fill_price: float) -> tuple[int, float, float]:
        """Execute and update backend state.

        Returns:
          (executed_quantity, realized_pnl, fees)
        """
        raise NotImplementedError

