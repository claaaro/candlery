"""Risk Engine for Candlery.

Evaluates TradeActions proposed by strategies against configured
risk limits and portfolio state.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Any

from candlery.core.types import Signal, TradeAction

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class RiskState:
    """Current state of the portfolio and symbol needed for risk evaluation."""

    current_price: float
    current_position_value: float
    total_exposure: float
    daily_trades_count: int
    daily_loss: float


class RiskEngine:
    """Evaluates trades against risk limits.

    Limits are typically loaded from config/risk_defaults.yaml.
    """

    def __init__(self, config: dict[str, Any]) -> None:
        """Initialize with a risk configuration dictionary.

        Args:
            config: Dictionary containing risk limits:
                - max_position_size (float)
                - max_total_exposure (float)
                - max_trades_per_day (int)
                - daily_loss_cap (float)
        """
        self.max_position_size = float(config.get("max_position_size", 100000.0))
        self.max_total_exposure = float(config.get("max_total_exposure", 500000.0))
        self.max_trades_per_day = int(config.get("max_trades_per_day", 5))
        self.daily_loss_cap = float(config.get("daily_loss_cap", 25000.0))

    def evaluate(self, action: TradeAction, state: RiskState) -> TradeAction | None:
        """Evaluate a trade action against current risk state.

        Args:
            action: The proposed TradeAction from a Strategy.
            state: Current portfolio and market state.

        Returns:
            A modified TradeAction with approved quantity, or None if rejected.
        """
        if action.signal == Signal.HOLD:
            return None

        if state.current_price <= 0:
            logger.warning(f"RiskEngine: Rejecting {action.symbol} due to zero/negative price {state.current_price}")
            return None

        # Allow liquidations (SELL) without strict risk checks in Phase 1
        # since we want to be able to exit positions even if we are over limits.
        if action.signal == Signal.SELL:
            return action

        # --- BUY Logic ---

        if action.signal == Signal.BUY:
            # 1. Check daily trade count
            if state.daily_trades_count >= self.max_trades_per_day:
                logger.info(f"RiskEngine: Rejecting BUY {action.symbol} — daily trade limit reached ({state.daily_trades_count}/{self.max_trades_per_day})")
                return None

            # 2. Check daily loss cap
            if state.daily_loss >= self.daily_loss_cap:
                logger.info(f"RiskEngine: Rejecting BUY {action.symbol} — daily loss cap breached ({state.daily_loss}/{self.daily_loss_cap})")
                return None

            # 3. Calculate position size room
            available_for_pos = max(0.0, self.max_position_size - state.current_position_value)
            max_qty_for_pos = int(available_for_pos / state.current_price)

            # 4. Calculate total exposure room
            available_exposure = max(0.0, self.max_total_exposure - state.total_exposure)
            max_qty_for_exposure = int(available_exposure / state.current_price)

            # 5. Determine target quantity
            # If strategy suggests a specific quantity > 0, we use it as a target.
            # If 0, we aim for max allowed by position size.
            target_qty = action.quantity if action.quantity > 0 else max_qty_for_pos

            # Final quantity is constrained by position room and total exposure room
            final_qty = min(target_qty, max_qty_for_pos, max_qty_for_exposure)

            if final_qty <= 0:
                logger.info(f"RiskEngine: Rejecting BUY {action.symbol} — insufficient capital or limits (qty={final_qty})")
                return None

            # Create new action with approved quantity
            return TradeAction(
                symbol=action.symbol,
                signal=action.signal,
                quantity=final_qty,
                reason=action.reason + f" [Risk Check: qty={final_qty}]"
            )

        return None
