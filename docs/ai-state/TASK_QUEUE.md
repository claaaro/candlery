# Task Queue

**Last Updated:** 2026-05-01T22:30:00Z

## Rules
- Work top-to-bottom within each priority level
- Skip BLOCKED tasks, work on next READY
- Verify dependencies are DONE before starting a task
- Mark DONE with date when completed

## P0 — Must Do Next

| ID | Task | Deps | Status |
|---|---|---|---|
| T-014 | Cost model (STT, brokerage) | T-008 | **READY** |

## P1 — Phase 1b

| T-013 | GitHub Actions CI | Phase 1b stable | WAITING |

## Completed

| ID | Task | Date | Session |
|---|---|---|---|
| T-000 | Repo bootstrap | 2026-04-30 | manual |
| T-001 | Instrument model | 2026-04-30 | manual |
| T-002 | Candle model | 2026-04-30 | manual |
| T-005 | TradingCalendar | 2026-04-30 | antigravity |
| T-003 | Bhavcopy importer | 2026-04-30 | antigravity |
| T-006 | Strategy interface + core types | 2026-05-01 | antigravity |
| T-009 | SMA crossover strategy | 2026-05-01 | antigravity |
| T-007 | Risk engine | 2026-05-01 | antigravity |
| T-008 | Backtest runner | 2026-05-01 | antigravity |
| T-010 | Performance metrics | 2026-05-01 | antigravity |
| T-011 | CLI entry point | 2026-05-01 | antigravity |
| T-012 | Static HTML report (`--html`, `candlery.reporting`) | 2026-05-01 | cursor |
| — | Audit + package rename | 2026-04-30 | antigravity |
