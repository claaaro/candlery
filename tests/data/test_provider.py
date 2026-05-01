"""Tests for data provider."""

from __future__ import annotations

from datetime import date

from candlery.data.importers.bhavcopy import ImportResult
from candlery.data.provider import BhavcopyDataProvider


def test_bhavcopy_data_provider(monkeypatch) -> None:
    # Mock BhavcopyImporter
    class MockImporter:
        def import_directory(self, data_dir: str, start_date: date, end_date: date) -> list[ImportResult]:
            return [
                ImportResult(date(2026, 1, 1), {"TEST": "candle1"}, {}, 0, []),
                ImportResult(date(2026, 1, 2), {"TEST": "candle2", "IGNORE": "candle3"}, {}, 0, []),
            ]
            
    monkeypatch.setattr("candlery.data.provider.BhavcopyImporter", MockImporter)
    
    provider = BhavcopyDataProvider("dummy_dir", date(2026, 1, 1), date(2026, 1, 2))
    
    # Test getting candles for specific date, filtered by universe
    day1_candles = provider.get_candles_for_date(date(2026, 1, 1), {"TEST"})
    assert day1_candles == {"TEST": "candle1"}
    
    day2_candles = provider.get_candles_for_date(date(2026, 1, 2), {"TEST"})
    assert day2_candles == {"TEST": "candle2"}  # IGNORE should be filtered out
    
    # Test date not in cache
    day3_candles = provider.get_candles_for_date(date(2026, 1, 3), {"TEST"})
    assert day3_candles == {}
