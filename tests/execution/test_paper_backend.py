from __future__ import annotations

from datetime import date

import pytest

from candlery.backtest.costs import TransactionCostModel
from candlery.backtest.portfolio import Portfolio
from candlery.core.types import Signal, TradeAction
from candlery.execution.paper_backend import PaperExecutionBackend


def test_paper_backend_delegates_buy_to_portfolio() -> None:
    costs = TransactionCostModel.from_bps(stt_buy_bps=10, stt_sell_bps=10)

    p1 = Portfolio(initial_capital=10000.0, cost_model=costs)
    p2 = Portfolio(initial_capital=10000.0, cost_model=costs)
    b = PaperExecutionBackend(p2)

    action = TradeAction(symbol="TEST", signal=Signal.BUY, quantity=50)
    exec1 = p1.execute_trade(action, fill_price=100.0)
    exec2 = b.execute(action, fill_price=100.0)

    assert exec1 == exec2
    assert p1.cash == pytest.approx(p2.cash)
    assert p1.positions.keys() == p2.positions.keys()
    assert p1.positions["TEST"].quantity == p2.positions["TEST"].quantity


def test_paper_backend_sell_returns_net_pnl_after_fees() -> None:
    costs = TransactionCostModel.from_bps(stt_buy_bps=10, stt_sell_bps=10, brokerage_buy_bps=3, brokerage_sell_bps=3)

    p_portfolio = Portfolio(initial_capital=10000.0, cost_model=costs)
    b = PaperExecutionBackend(p_portfolio)

    buy = TradeAction(symbol="TEST", signal=Signal.BUY, quantity=50)
    b.execute(buy, fill_price=100.0)

    sell = TradeAction(symbol="TEST", signal=Signal.SELL, quantity=20)
    exec_qty, realized_pnl, fees = b.execute(sell, fill_price=110.0)

    assert exec_qty == 20
    # Fees should be positive on a SELL.
    assert fees > 0
    # Realized PnL for a profitable round-trip should be positive.
    assert realized_pnl > 0

