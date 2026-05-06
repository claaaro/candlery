# Candlery Constitution

This document defines the stable architecture and scope boundaries.
For AI behavior rules and session boot ritual, see `AGENTS.md` at repo root.

## Grand Vision

Candlery is built as an institutional-grade trading platform that progresses
from deterministic backtesting to controlled live execution.

Target scope includes:
- Multi-asset coverage (NSE equities, F&O, Forex)
- Multi-timeframe support (EOD and intraday)
- Eventual broker connectivity for real-capital execution

## Architecture Invariants

1. Immutability:
   - Core types (such as Candle and Instrument) are frozen dataclasses.

2. Timezone discipline:
   - All internal timestamps are UTC and timezone-aware.

3. Separation of concerns:
   - Strategy: signal generation only.
   - Portfolio: state tracking only.
   - RiskEngine: action validation and limits enforcement only.

4. Deterministic core:
   - No LLM in Strategy -> Risk -> Execution runtime path.

5. Type migration path:
   - Phase 1 uses float for prices.
   - Architecture must preserve a low-friction migration path to Decimal before
     live capital deployment.

## Phase Scope Lock

- Phase 1a: EOD Equity Backtesting MVP (current)
- Phase 1b: Reporting and visualization
- Phase 2: Intraday and derivatives
- Phase 3: Forex integration
- Phase 4: Live execution

Rule: no implementation from a future phase is allowed until the current phase
is verified complete by executable validation gates.

Minimum phase validation gate:
- Unit/integration tests green.
- One baseline end-to-end run producing report artifacts.
- One controlled variation run (single changed variable).
- Outcome comparison and a written conclusion.
