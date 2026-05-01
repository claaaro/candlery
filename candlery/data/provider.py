"""Data provider wrapper for backtesting."""

from __future__ import annotations

from datetime import date
from pathlib import Path

from candlery.core.candle import Candle
from candlery.data.calendar import TradingCalendar
from candlery.data.importers.bhavcopy import BhavcopyImporter


class BhavcopyDataProvider:
    """Provides historical candle data day-by-day for the backtester.
    
    Pre-loads all CSVs from a directory into memory for fast lookup during the simulation.
    """

    def __init__(
        self,
        data_dir: str | Path,
        start_date: date,
        end_date: date,
        calendar: TradingCalendar,
    ) -> None:
        """Initialize and preload data.
        
        Args:
            data_dir: Path to the directory containing Bhavcopy CSVs.
            start_date: Start date of the backtest.
            end_date: End date of the backtest.
            calendar: TradingCalendar used for trading-day validation.
        """
        self.data_dir = Path(data_dir)

        importer = BhavcopyImporter(calendar)
        self.results = importer.import_directory(self.data_dir, start_date, end_date)
        
        # Build an index for fast O(1) lookup by date: date -> dict[symbol, Candle]
        self._cache: dict[date, dict[str, Candle]] = {}
        for res in self.results:
            self._cache[res.date] = res.candles

    def get_candles_for_date(self, day: date, universe: set[str]) -> dict[str, Candle]:
        """Get all candles for a specific day, filtered by universe.
        
        Args:
            day: The trading date to retrieve.
            universe: Set of symbols to include.
            
        Returns:
            Dict mapping symbol to its Candle for the requested date.
        """
        daily_data = self._cache.get(day, {})
        return {symbol: candle for symbol, candle in daily_data.items() if symbol in universe}
