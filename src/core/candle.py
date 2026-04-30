from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True)
class Candle:
    timestamp: datetime
    open: float
    high: float
    low: float
    close: float
    volume: float

    def __post_init__(self):
        if self.high < self.low:
            raise ValueError("High cannot be less than Low")

        if not (self.low <= self.open <= self.high):
            raise ValueError("Open must be between Low and High")

        if not (self.low <= self.close <= self.high):
            raise ValueError("Close must be between Low and High")

        if self.volume < 0:
            raise ValueError("Volume cannot be negative")
