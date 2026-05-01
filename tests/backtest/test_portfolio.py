"""Tests for backtest portfolio and position models."""

from __future__ import annotations

import pytest

from candlery.backtest.portfolio import Portfolio, Position
from candlery.core.types import Signal, TradeAction


class TestPosition:
    def test_new_position_is_empty(self) -> None:
        pos = Position(symbol="RELIANCE")
        assert pos.symbol == "RELIANCE"
        assert pos.quantity == 0
        assert pos.average_price == 0.0
        assert not pos.is_active

    def test_add_to_empty_position(self) -> None:
        pos = Position(symbol="RELIANCE")
        pos.add(10, 100.0)
        assert pos.quantity == 10
        assert pos.average_price == 100.0
        assert pos.is_active

    def test_add_recalculates_average_price(self) -> None:
        pos = Position(symbol="RELIANCE")
        pos.add(10, 100.0)  # Value: 1000
        pos.add(10, 200.0)  # Value: 2000, Total Value: 3000
        assert pos.quantity == 20
        assert pos.average_price == 150.0  # 3000 / 20

    def test_add_invalid_quantity_raises(self) -> None:
        pos = Position(symbol="TEST")
        with pytest.raises(ValueError):
            pos.add(0, 100.0)
        with pytest.raises(ValueError):
            pos.add(-5, 100.0)

    def test_add_invalid_price_raises(self) -> None:
        pos = Position(symbol="TEST")
        with pytest.raises(ValueError):
            pos.add(10, 0.0)
        with pytest.raises(ValueError):
            pos.add(10, -50.0)

    def test_remove_partial_position(self) -> None:
        pos = Position(symbol="TEST")
        pos.add(20, 100.0)
        
        # Sell 10 at 150. Realized PnL: (150 - 100) * 10 = 500
        pnl = pos.remove(10, 150.0)
        assert pnl == 500.0
        assert pos.quantity == 10
        assert pos.average_price == 100.0  # Avg price doesn't change on sell
        assert pos.is_active

    def test_remove_full_position(self) -> None:
        pos = Position(symbol="TEST")
        pos.add(10, 100.0)
        
        pnl = pos.remove(10, 50.0)  # Sell at loss
        assert pnl == -500.0
        assert pos.quantity == 0
        assert pos.average_price == 0.0  # Resets on full exit
        assert not pos.is_active

    def test_remove_more_than_owned_raises(self) -> None:
        pos = Position(symbol="TEST")
        pos.add(10, 100.0)
        with pytest.raises(ValueError, match="Cannot remove"):
            pos.remove(15, 150.0)

    def test_remove_invalid_quantity_raises(self) -> None:
        pos = Position(symbol="TEST")
        pos.add(10, 100.0)
        with pytest.raises(ValueError):
            pos.remove(0, 150.0)
        with pytest.raises(ValueError):
            pos.remove(-5, 150.0)


class TestPortfolio:
    def test_initial_state(self) -> None:
        pf = Portfolio(initial_capital=100000.0)
        assert pf.cash == 100000.0
        assert len(pf.positions) == 0
        assert pf.daily_trades_count == 0
        assert pf.daily_realized_pnl == 0.0
        assert pf.daily_unrealized_pnl == 0.0
        assert pf.daily_loss == 0.0

    def test_execute_buy_trade(self) -> None:
        pf = Portfolio(initial_capital=10000.0)
        action = TradeAction(symbol="TEST", signal=Signal.BUY, quantity=10)
        
        pf.execute_trade(action, fill_price=100.0)
        
        assert pf.cash == 9000.0  # 10000 - 1000
        assert "TEST" in pf.positions
        assert pf.positions["TEST"].quantity == 10
        assert pf.daily_trades_count == 1

    def test_execute_sell_trade(self) -> None:
        pf = Portfolio(initial_capital=10000.0)
        pf.execute_trade(TradeAction(symbol="TEST", signal=Signal.BUY, quantity=10), fill_price=100.0)
        
        # Reset stats to simulate next day
        pf.reset_daily_stats()
        
        # Sell 5 at 120 (Profit: 5 * 20 = 100)
        pf.execute_trade(TradeAction(symbol="TEST", signal=Signal.SELL, quantity=5), fill_price=120.0)
        
        assert pf.cash == 9600.0  # 9000 + 600
        assert pf.positions["TEST"].quantity == 5
        assert pf.daily_trades_count == 1
        assert pf.daily_realized_pnl == 100.0

    def test_insufficient_cash_causes_partial_fill(self) -> None:
        pf = Portfolio(initial_capital=1000.0)
        # Try to buy 15 shares @ 100 (needs 1500)
        action = TradeAction(symbol="TEST", signal=Signal.BUY, quantity=15)
        
        pf.execute_trade(action, fill_price=100.0)
        
        # Should only buy 10 shares
        assert pf.positions["TEST"].quantity == 10
        assert pf.cash == 0.0

    def test_insufficient_cash_for_even_one_share(self) -> None:
        pf = Portfolio(initial_capital=50.0)
        # Try to buy 1 share @ 100 (needs 100)
        action = TradeAction(symbol="TEST", signal=Signal.BUY, quantity=1)
        
        pf.execute_trade(action, fill_price=100.0)
        
        # Should not buy anything
        assert "TEST" not in pf.positions
        assert pf.cash == 50.0

    def test_sell_more_than_owned_caps_at_position_size(self) -> None:
        pf = Portfolio(initial_capital=10000.0)
        pf.execute_trade(TradeAction(symbol="TEST", signal=Signal.BUY, quantity=10), fill_price=100.0)
        
        # Try to sell 20
        pf.execute_trade(TradeAction(symbol="TEST", signal=Signal.SELL, quantity=20), fill_price=100.0)
        
        # Should sell exactly 10
        assert pf.positions["TEST"].quantity == 0
        assert pf.cash == 10000.0

    def test_unrealized_pnl_and_daily_loss(self) -> None:
        pf = Portfolio(initial_capital=10000.0)
        pf.execute_trade(TradeAction(symbol="TEST", signal=Signal.BUY, quantity=10), fill_price=100.0)
        
        # Price drops to 80
        current_prices = {"TEST": 80.0}
        pf.update_unrealized_pnl(current_prices)
        
        assert pf.daily_unrealized_pnl == -200.0
        assert pf.daily_loss == 200.0  # positive representation of loss

        # Price rises to 120
        current_prices = {"TEST": 120.0}
        pf.update_unrealized_pnl(current_prices)
        
        assert pf.daily_unrealized_pnl == 200.0
        assert pf.daily_loss == 0.0  # gain is 0 loss

    def test_exposure_and_equity(self) -> None:
        pf = Portfolio(initial_capital=10000.0)
        pf.execute_trade(TradeAction(symbol="TEST", signal=Signal.BUY, quantity=10), fill_price=100.0)
        
        current_prices = {"TEST": 150.0}
        
        assert pf.get_position_value("TEST", current_prices["TEST"]) == 1500.0
        assert pf.get_total_exposure(current_prices) == 1500.0
        assert pf.get_total_equity(current_prices) == 10500.0  # 9000 cash + 1500 exposure
