"""Tests for RiskEngine."""

from __future__ import annotations

import pytest

from candlery.core.types import Signal, TradeAction
from candlery.risk.engine import RiskEngine, RiskState


@pytest.fixture
def base_config() -> dict[str, float]:
    return {
        "max_position_size": 10000.0,
        "max_total_exposure": 50000.0,
        "max_trades_per_day": 3,
        "daily_loss_cap": 1000.0,
    }


@pytest.fixture
def engine(base_config: dict[str, float]) -> RiskEngine:
    return RiskEngine(base_config)


def default_state(
    current_price: float = 100.0,
    current_position_value: float = 0.0,
    total_exposure: float = 0.0,
    daily_trades_count: int = 0,
    daily_loss: float = 0.0,
) -> RiskState:
    return RiskState(
        current_price=current_price,
        current_position_value=current_position_value,
        total_exposure=total_exposure,
        daily_trades_count=daily_trades_count,
        daily_loss=daily_loss,
    )


class TestRiskEngine:
    def test_hold_action_returns_none(self, engine: RiskEngine) -> None:
        action = TradeAction(symbol="TEST", signal=Signal.HOLD)
        result = engine.evaluate(action, default_state())
        assert result is None

    def test_sell_action_passes_through(self, engine: RiskEngine) -> None:
        # Sell passes through even if max trades exceeded (allow exits)
        action = TradeAction(symbol="TEST", signal=Signal.SELL, quantity=50)
        state = default_state(daily_trades_count=10)
        result = engine.evaluate(action, state)
        assert result is not None
        assert result.signal == Signal.SELL
        assert result.quantity == 50

    def test_sell_with_zero_qty_means_full_liquidation(self, engine: RiskEngine) -> None:
        action = TradeAction(symbol="TEST", signal=Signal.SELL, quantity=0)
        state = default_state(current_price=100.0, current_position_value=2350.0)
        result = engine.evaluate(action, state)
        assert result is not None
        assert result.signal == Signal.SELL
        assert result.quantity == 23

    def test_zero_price_rejects_buy(self, engine: RiskEngine) -> None:
        action = TradeAction(symbol="TEST", signal=Signal.BUY)
        result = engine.evaluate(action, default_state(current_price=0))
        assert result is None

    def test_daily_trade_limit_rejects_buy(self, engine: RiskEngine) -> None:
        action = TradeAction(symbol="TEST", signal=Signal.BUY)
        # Config max is 3
        state = default_state(daily_trades_count=3)
        result = engine.evaluate(action, state)
        assert result is None

    def test_daily_loss_cap_rejects_buy(self, engine: RiskEngine) -> None:
        action = TradeAction(symbol="TEST", signal=Signal.BUY)
        # Config cap is 1000
        state = default_state(daily_loss=1000.0)
        result = engine.evaluate(action, state)
        assert result is None

    def test_max_position_size_limits_quantity(self, engine: RiskEngine) -> None:
        action = TradeAction(symbol="TEST", signal=Signal.BUY)
        # max_position_size = 10000. current_price = 100. max qty = 100
        result = engine.evaluate(action, default_state(current_price=100.0))
        assert result is not None
        assert result.quantity == 100

    def test_max_position_size_with_existing_position(self, engine: RiskEngine) -> None:
        action = TradeAction(symbol="TEST", signal=Signal.BUY)
        # max_position_size = 10000. current_price = 100.
        # current_position_value = 8000. available = 2000. max qty = 20
        state = default_state(current_price=100.0, current_position_value=8000.0)
        result = engine.evaluate(action, state)
        assert result is not None
        assert result.quantity == 20

    def test_max_position_size_exceeded_returns_none(self, engine: RiskEngine) -> None:
        action = TradeAction(symbol="TEST", signal=Signal.BUY)
        state = default_state(current_price=100.0, current_position_value=10000.0)
        result = engine.evaluate(action, state)
        assert result is None

    def test_max_total_exposure_limits_quantity(self, engine: RiskEngine) -> None:
        action = TradeAction(symbol="TEST", signal=Signal.BUY)
        # max_position_size = 10000, total_exposure = 45000, max_total_exposure = 50000
        # Position allows 100 (10000 / 100), but exposure only allows 50 (5000 / 100)
        state = default_state(current_price=100.0, total_exposure=45000.0)
        result = engine.evaluate(action, state)
        assert result is not None
        assert result.quantity == 50

    def test_strategy_provided_quantity_is_respected_if_within_limits(self, engine: RiskEngine) -> None:
        # Strategy wants 50. Max position allows 100.
        action = TradeAction(symbol="TEST", signal=Signal.BUY, quantity=50)
        result = engine.evaluate(action, default_state(current_price=100.0))
        assert result is not None
        assert result.quantity == 50

    def test_strategy_provided_quantity_is_capped_if_exceeds_limits(self, engine: RiskEngine) -> None:
        # Strategy wants 150. Max position allows 100.
        action = TradeAction(symbol="TEST", signal=Signal.BUY, quantity=150)
        result = engine.evaluate(action, default_state(current_price=100.0))
        assert result is not None
        assert result.quantity == 100

    def test_reason_is_appended(self, engine: RiskEngine) -> None:
        action = TradeAction(symbol="TEST", signal=Signal.BUY, reason="SMA Cross")
        result = engine.evaluate(action, default_state(current_price=100.0))
        assert result is not None
        assert "SMA Cross" in result.reason
        assert "Risk Check" in result.reason
