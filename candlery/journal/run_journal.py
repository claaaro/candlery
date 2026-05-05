"""RunJournal — deterministic, crash-safe-ish journaling for paper/live runs.

Phase 3C minimal scope:
- Persist "day completed" events to an append-only JSONL file.
- Support resume by loading:
  - completed day set
  - portfolio snapshot at the last completed day
  - full trades list and daily equity curve up to that day

This does not implement any scheduler or forward loop; it is a persistence layer
for day-boundary orchestration.
"""

from __future__ import annotations

import json
import os
from dataclasses import dataclass
from datetime import date
from pathlib import Path

from candlery.backtest.portfolio import Position
from candlery.core.types import Signal
from candlery.journal.store import ExecutedTrade


@dataclass(frozen=True)
class PortfolioSnapshot:
    cash: float
    positions: dict[str, Position]


@dataclass(frozen=True)
class JournalState:
    completed_days: set[date]
    portfolio_snapshot: PortfolioSnapshot
    trades: list[ExecutedTrade]
    daily_equity_curve: list[float]


class RunJournal:
    """Append-only JSONL journal for a single run.

    Determinism:
      - We write events with stable key ordering and stable separators.

    Crash safety:
      - On load, we stop at the first JSON decoding failure, assuming it is
        a partially-written tail line.
      - Events must be written as a single line (JSONL).
    """

    _EVENT_VERSION = 1

    def __init__(self, path: Path | str) -> None:
        self._path = Path(path)
        self._path.parent.mkdir(parents=True, exist_ok=True)

    @property
    def path(self) -> Path:
        return self._path

    def append_day_completed(
        self,
        *,
        run_id: str,
        day: date,
        portfolio_snapshot: PortfolioSnapshot,
        trades: list[ExecutedTrade],
        daily_equity_value: float,
    ) -> None:
        event = {
            "version": self._EVENT_VERSION,
            "type": "day_completed",
            "run_id": run_id,
            "day": day.isoformat(),
            "portfolio_snapshot": self._serialize_portfolio_snapshot(
                portfolio_snapshot
            ),
            "trades": [self._serialize_trade(t) for t in trades],
            "daily_equity_value": daily_equity_value,
        }
        line = json.dumps(event, sort_keys=True, separators=(",", ":"), ensure_ascii=True)

        # Write as a single append-only line and force to disk.
        with self._path.open("a", encoding="utf-8") as f:
            f.write(line + "\n")
            f.flush()
            os.fsync(f.fileno())

    def load(self, *, run_id: str) -> JournalState:
        if not self._path.exists():
            # Empty state: caller decides what "resume" means.
            raise FileNotFoundError(str(self._path))

        completed_days: set[date] = set()
        trades: list[ExecutedTrade] = []
        equity_curve: list[float] = []

        last_snapshot: PortfolioSnapshot | None = None

        with self._path.open("r", encoding="utf-8") as f:
            for raw in f:
                raw = raw.strip()
                if not raw:
                    continue
                try:
                    event = json.loads(raw)
                except json.JSONDecodeError:
                    # Treat as partial tail line from a crash.
                    break

                if event.get("run_id") != run_id:
                    continue
                if event.get("type") != "day_completed":
                    continue

                day = date.fromisoformat(event["day"])
                portfolio_snapshot = self._deserialize_portfolio_snapshot(
                    event["portfolio_snapshot"]
                )
                day_trades = [
                    self._deserialize_trade(t) for t in event.get("trades", [])
                ]
                completed_days.add(day)
                trades.extend(day_trades)
                equity_curve.append(float(event["daily_equity_value"]))
                last_snapshot = portfolio_snapshot

        if last_snapshot is None:
            raise ValueError("Journal contains no matching day_completed events")

        return JournalState(
            completed_days=completed_days,
            portfolio_snapshot=last_snapshot,
            trades=trades,
            daily_equity_curve=equity_curve,
        )

    def has_completed_day(self, *, run_id: str, day: date) -> bool:
        if not self._path.exists():
            return False
        try:
            state = self.load(run_id=run_id)
        except Exception:
            return False
        return day in state.completed_days

    @staticmethod
    def _serialize_trade(t: ExecutedTrade) -> dict:
        return {
            "date": t.date.isoformat(),
            "symbol": t.symbol,
            "signal": t.signal.name,
            "quantity": t.quantity,
            "price": t.price,
            "realized_pnl": t.realized_pnl,
            "fees": t.fees,
        }

    @staticmethod
    def _deserialize_trade(d: dict) -> ExecutedTrade:
        return ExecutedTrade(
            date=date.fromisoformat(d["date"]),
            symbol=str(d["symbol"]),
            signal=Signal[d["signal"]],
            quantity=int(d["quantity"]),
            price=float(d["price"]),
            realized_pnl=float(d["realized_pnl"]),
            fees=float(d["fees"]),
        )

    @staticmethod
    def _serialize_portfolio_snapshot(
        snap: PortfolioSnapshot,
    ) -> dict:
        positions = [
            {
                "symbol": sym,
                "quantity": pos.quantity,
                "average_price": pos.average_price,
            }
            for sym, pos in sorted(snap.positions.items(), key=lambda kv: kv[0])
        ]
        return {"cash": snap.cash, "positions": positions}

    @staticmethod
    def _deserialize_portfolio_snapshot(d: dict) -> PortfolioSnapshot:
        positions: dict[str, Position] = {}
        for p in d.get("positions", []):
            sym = str(p["symbol"])
            positions[sym] = Position(
                symbol=sym,
                quantity=int(p["quantity"]),
                average_price=float(p["average_price"]),
            )
        return PortfolioSnapshot(cash=float(d["cash"]), positions=positions)

