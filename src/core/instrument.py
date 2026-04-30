from dataclasses import dataclass


@dataclass(frozen=True)
class Instrument:
    symbol: str
    exchange: str
    currency: str = "INR"

    def __post_init__(self):
        if not self.symbol:
            raise ValueError("Symbol cannot be empty")
        if not self.exchange:
            raise ValueError("Exchange cannot be empty")
