"""Abstract base class for all trading strategies.

A strategy receives historical candle data and produces trading signals.
It has no knowledge of position sizing, risk limits, or execution —
those are handled by downstream components.

The contract:
    - Strategy receives: list of Candles (ordered oldest → newest)
    - Strategy returns: list of TradeActions (one per symbol it wants to act on)
    - Strategy is stateless between calls (all state in the candle history)
"""

from __future__ import annotations

from abc import ABC, abstractmethod

from candlery.core.candle import Candle
from candlery.core.types import TradeAction


class Strategy(ABC):
    """Abstract base class for trading strategies.

    Subclasses must implement:
        - name: human-readable strategy identifier
        - evaluate: given candle history, produce trade actions
    """

    @property
    @abstractmethod
    def name(self) -> str:
        """Human-readable name for this strategy."""
        ...

    @abstractmethod
    def evaluate(self, symbol: str, candles: list[Candle]) -> TradeAction | None:
        """Evaluate candle history for a single symbol and return a trade action.

        Args:
            symbol: The instrument symbol being evaluated.
            candles: Historical candles ordered oldest → newest.
                     The last candle is the most recent completed bar.
                     Must contain at least enough bars for the strategy's
                     lookback period.

        Returns:
            A TradeAction if the strategy wants to act, or None if HOLD.

        Rules:
            - MUST NOT look at future data (only candles up to current bar)
            - MUST NOT make external API calls
            - MUST be deterministic (same input → same output)
        """
        ...

    def required_history(self) -> int:
        """Minimum number of candles needed for this strategy to produce a signal.

        Override this if your strategy needs a specific lookback period.
        Default is 1 (can evaluate with a single candle).
        """
        return 1
