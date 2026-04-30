# Task Queue

**Last Updated:** 2026-04-30T22:00:00Z

## Rules
- Work top-to-bottom within each priority level
- Skip BLOCKED tasks, work on next READY
- Verify dependencies are DONE before starting a task
- Mark DONE with date when completed

## P0 — Must Do Next

| ID | Task | Cat | Deps | Status |
|---|---|---|---|---|
| T-003 | NSE Bhavcopy importer | C3 | T-001, T-002, T-005 | **READY** |
| T-004 | Importer tests | C2 | T-003 | WAITING |
| T-006 | Strategy interface (abstract base) | C4 | None | **READY** |

## P1 — This Phase

| ID | Task | Cat | Deps | Status |
|---|---|---|---|---|
| T-007 | Risk engine (basic limits) | C3 | T-006 | WAITING |
| T-008 | Backtest runner | C3 | T-005, T-006, T-007 | WAITING |
| T-009 | SMA crossover strategy | C2 | T-006 | WAITING |
| T-010 | Performance metrics | C3 | T-008 | WAITING |
| T-011 | CLI entry point | C2 | T-008 | WAITING |

## P2 — Phase 1b

| ID | Task | Cat | Deps | Status |
|---|---|---|---|---|
| T-012 | Static HTML report | C2 | T-010 | WAITING |
| T-013 | GitHub Actions CI | C2 | T-004 | WAITING |
| T-014 | Cost model (STT, brokerage) | C3 | T-008 | WAITING |

## Completed

| ID | Task | Date | Session |
|---|---|---|---|
| T-000 | Repo bootstrap | 2026-04-30 | manual |
| T-001 | Instrument model | 2026-04-30 | manual |
| T-002 | Candle model | 2026-04-30 | manual |
| T-005 | TradingCalendar | 2026-04-30 | antigravity |
| — | Audit fixes (holidays, types) | 2026-04-30 | antigravity |
| — | Package rename (src → candlery) | 2026-04-30 | antigravity |
