# Candlery — Current State

**Last Updated:** 2026-05-01T00:16:00Z
**Last Platform:** Google Antigravity
**Current Phase:** Phase 1a — Backtesting MVP (CLI)
**Phase Status:** In Progress (~45%)

## Completed Tasks

- [x] T-000: Repo bootstrap (structure, config, docs, ai-state)
- [x] T-001: Instrument model (immutable dataclass, validated, ISIN field)
- [x] T-002: Candle model (OHLCV, timezone-aware timestamps, int volume)
- [x] T-005: TradingCalendar (holiday loading, UTC conversion, trading day logic)
- [x] T-003: Bhavcopy importer (CSV parsing, EQ filter, UTC timestamps, directory scan)
- [x] T-006: Strategy interface (abstract base + core types)
- [x] T-009: SMA crossover strategy (reference implementation)
- [x] AUDIT: Holiday data completed (2024–2026), type fixes, timezone enforcement
- [x] REFACTOR: Package renamed src/ → candlery/, .gitignore fixed

## Next Priority

1. **T-007: Risk engine** — READY (T-006 complete)
2. T-008: Backtest runner — WAITING (depends on T-007)
3. T-011: CLI entry point — WAITING (depends on T-008)

## Architecture Summary

- Package: `candlery/` (imports: `from candlery.x.y import Z`)
- All timestamps: UTC, timezone-aware
- Data models: frozen dataclasses in `candlery/core/`
- Config: YAML (exchanges) + JSON (holidays) in `config/`
- Tests: `tests/` mirror of `candlery/` — **71 tests passing**

## Known Issues

- No integration tests yet (unit tests only)
- Corporate actions not handled (documented gap)
- `float` used for prices (Decimal migration deferred to Phase 2)

## Key Files

- `candlery/core/instrument.py` — Instrument dataclass
- `candlery/core/candle.py` — Candle dataclass (OHLCV)
- `candlery/data/calendar.py` — TradingCalendar
- `candlery/data/importers/bhavcopy.py` — NSE Bhavcopy CSV parser
- `candlery/core/types.py` — Signal, OrderSide, TradeAction
- `candlery/strategy/base.py` — Abstract Strategy class
- `candlery/strategy/sma_crossover.py` — SMA crossover (reference impl)
- `config/exchanges/nse.yaml` — NSE market hours
- `config/holidays/nse_202{4,5,6}.json` — Holiday calendars
- `tests/data/test_calendar.py` — 25 tests
- `tests/data/importers/test_bhavcopy.py` — 19 tests
