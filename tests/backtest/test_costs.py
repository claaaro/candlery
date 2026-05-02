"""Tests for transaction cost model."""

from __future__ import annotations

import pytest

from candlery.backtest.costs import (
    TransactionCostModel,
    bps_to_fraction,
    transaction_cost_model_from_mapping,
)


def test_bps_to_fraction() -> None:
    assert bps_to_fraction(10) == 0.001
    assert bps_to_fraction(100) == 0.01


def test_from_bps() -> None:
    m = TransactionCostModel.from_bps(
        stt_buy_bps=10,
        stt_sell_bps=10,
        brokerage_buy_bps=3,
        brokerage_sell_bps=3,
    )
    assert m.buy_fees(10_000.0) == pytest.approx(13.0)  # 13 bps of 10k
    assert m.sell_fees(10_000.0) == pytest.approx(13.0)


def test_transaction_cost_model_from_mapping_bps() -> None:
    m = transaction_cost_model_from_mapping(
        {"stt_buy_bps": 10, "brokerage_sell_bps": 5}
    )
    assert m.stt_on_buy == pytest.approx(0.001)
    assert m.brokerage_on_sell == pytest.approx(0.0005)


def test_transaction_cost_model_from_mapping_fractions() -> None:
    m = transaction_cost_model_from_mapping(
        {"stt_on_buy": 0.001, "brokerage_on_sell": 0.0005}
    )
    assert m.buy_fees(1000.0) == pytest.approx(1.0)


def test_transaction_cost_model_from_mapping_none() -> None:
    assert transaction_cost_model_from_mapping(None) == TransactionCostModel()


def test_transaction_cost_model_from_mapping_bad_type() -> None:
    with pytest.raises(TypeError):
        transaction_cost_model_from_mapping("x")
