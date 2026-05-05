"""Paper-only execution backend.

Phase 3A goal: provide a deterministic execution seam that reuses the
existing backtest Portfolio fill + fee logic.
"""

from __future__ import annotations

from candlery.backtest.portfolio import Portfolio
from candlery.core.types import TradeAction
from candlery.execution.backend import ExecutionBackend


class PaperExecutionBackend(ExecutionBackend):
    def __init__(self, portfolio: Portfolio) -> None:
        self._portfolio = portfolio

    def execute(self, action: TradeAction, *, fill_price: float) -> tuple[int, float, float]:
        # Delegate to the already-validated backtest fill + cost model.
        return self._portfolio.execute_trade(action, fill_price)

