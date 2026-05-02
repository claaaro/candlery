"""Transaction cost model for backtests (STT, brokerage as turnover fractions)."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


def bps_to_fraction(bps: float) -> float:
    """Convert basis points to a fraction of notional (100 bps = 1% = 0.01)."""
    return bps / 10_000.0


@dataclass(frozen=True)
class TransactionCostModel:
    """Per-leg costs as fractions of notional (turnover).

    Defaults are zero (no frictions). Configure via :meth:`from_bps` for typical
    NSE delivery-style backtests: set ``stt_*_bps`` and ``brokerage_*_bps`` in YAML.
    """

    stt_on_buy: float = 0.0
    stt_on_sell: float = 0.0
    brokerage_on_buy: float = 0.0
    brokerage_on_sell: float = 0.0

    @classmethod
    def from_bps(
        cls,
        *,
        stt_buy_bps: float = 0.0,
        stt_sell_bps: float = 0.0,
        brokerage_buy_bps: float = 0.0,
        brokerage_sell_bps: float = 0.0,
    ) -> TransactionCostModel:
        return cls(
            stt_on_buy=bps_to_fraction(stt_buy_bps),
            stt_on_sell=bps_to_fraction(stt_sell_bps),
            brokerage_on_buy=bps_to_fraction(brokerage_buy_bps),
            brokerage_on_sell=bps_to_fraction(brokerage_sell_bps),
        )

    def buy_fee_fraction(self) -> float:
        return self.stt_on_buy + self.brokerage_on_buy

    def sell_fee_fraction(self) -> float:
        return self.stt_on_sell + self.brokerage_on_sell

    def buy_fees(self, notional: float) -> float:
        return notional * self.buy_fee_fraction()

    def sell_fees(self, notional: float) -> float:
        return notional * self.sell_fee_fraction()


def transaction_cost_model_from_mapping(raw: Any) -> TransactionCostModel:
    """Build a :class:`TransactionCostModel` from a ``backtest.costs`` YAML mapping.

    Accepts basis-point keys (preferred): ``stt_buy_bps``, ``stt_sell_bps``,
    ``brokerage_buy_bps``, ``brokerage_sell_bps``.

    For advanced use, exact fractions may be passed as ``stt_on_buy``,
    ``stt_on_sell``, ``brokerage_on_buy``, ``brokerage_on_sell`` (0.001 = 0.1%).
    """
    if raw is None:
        return TransactionCostModel()
    if not isinstance(raw, dict):
        raise TypeError("backtest.costs must be a mapping or omitted")

    if any(
        k in raw
        for k in (
            "stt_buy_bps",
            "stt_sell_bps",
            "brokerage_buy_bps",
            "brokerage_sell_bps",
        )
    ):
        return TransactionCostModel.from_bps(
            stt_buy_bps=float(raw.get("stt_buy_bps", 0.0)),
            stt_sell_bps=float(raw.get("stt_sell_bps", 0.0)),
            brokerage_buy_bps=float(raw.get("brokerage_buy_bps", 0.0)),
            brokerage_sell_bps=float(raw.get("brokerage_sell_bps", 0.0)),
        )

    return TransactionCostModel(
        stt_on_buy=float(raw.get("stt_on_buy", 0.0)),
        stt_on_sell=float(raw.get("stt_on_sell", 0.0)),
        brokerage_on_buy=float(raw.get("brokerage_on_buy", 0.0)),
        brokerage_on_sell=float(raw.get("brokerage_on_sell", 0.0)),
    )
