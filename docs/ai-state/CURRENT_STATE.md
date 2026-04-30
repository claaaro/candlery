# Candlery — Current State

**Last Updated:** 2026-04-30T22:00:00Z
**Last Platform:** Google Antigravity (Claude Opus 4.6)
**Current Phase:** Phase 1a — Backtesting MVP (CLI)
**Phase Status:** In Progress (~20%)

## Completed Tasks

- [x] T-000: Repo bootstrap (structure, config, docs, ai-state)
- [x] T-001: Instrument model (immutable dataclass, validated, ISIN field)
- [x] T-002: Candle model (OHLCV, timezone-aware timestamps, int volume)
- [x] T-005: TradingCalendar (holiday loading, UTC conversion, trading day logic)
- [x] AUDIT: Holiday data completed (2024–2026), type fixes, timezone enforcement
- [x] REFACTOR: Package renamed src/ → candlery/, imports updated

## Next Priority (from TASK_QUEUE.md)

1. T-003: NSE Bhavcopy importer — READY (depends on T-001, T-002, T-005 ✅)
2. T-006: Strategy interface (abstract base) — READY (no dependencies)
3. T-007: Risk engine — WAITING (depends on T-006)

## Architecture Summary

- Package: `candlery/` (imports: `from candlery.x.y import Z`)
- All timestamps: UTC, timezone-aware
- Data models: frozen dataclasses in `candlery/core/`
- Config: YAML (exchanges) + JSON (holidays) in `config/`
- Tests: `tests/` mirror of `candlery/`
- Database: SQLite (Phase 1), deferred to importer

## Known Issues

- No integration tests yet (unit tests only)
- Corporate actions not handled (documented gap)
- `float` used for prices (Decimal migration deferred to Phase 2)

## Key Files

- `candlery/core/instrument.py` — Instrument dataclass
- `candlery/core/candle.py` — Candle dataclass (OHLCV)
- `candlery/data/calendar.py` — TradingCalendar
- `config/exchanges/nse.yaml` — NSE market hours
- `config/holidays/nse_202{4,5,6}.json` — Holiday calendars
- `config/risk_defaults.yaml` — Risk limits
- `tests/data/test_calendar.py` — 25 tests, all passing
