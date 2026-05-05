# Task Queue

**Last Updated:** 2026-05-05T18:00:00Z

## Rules
- Work top-to-bottom within each priority level
- Skip BLOCKED tasks, work on next READY
- Verify dependencies are DONE before starting a task
- Mark DONE with date when completed

## P0 — Must Do Next

| ID | Task | Deps | Status |
|---|---|---|---|
| P3-004 | Repo hygiene pass decision (keep/archive/delete disposable research artifacts) | — | READY |

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
| T-014 | Transaction costs (STT + brokerage, YAML `costs`, journal fees) | 2026-05-01 | cursor |
| T-013 | GitHub Actions CI (`pytest` + `phase1a-smoke` on push/PR to `main`) | 2026-05-02 | cursor |
| — | Audit + package rename | 2026-04-30 | antigravity |
| R-001 | Strategy robustness cycle (SMA/filter/exit/breakout) | 2026-05-05 | cursor |
| R-002 | Cross-sectional momentum probe + information-content diagnostics | 2026-05-05 | cursor |
| R-003 | Pre-committed long-short falsification test | 2026-05-05 | cursor |
| D-001 | Validation and closeout documents (`VALIDATION_GATE_REPORT`, `PHASE2_*`) | 2026-05-05 | cursor |
| P2-000 | Preserve research closeout state (docs + STOP policy on `data_real`) | 2026-05-05 | cursor |
| P2-001 | Integrity pass: incremental history, same-day close fill semantics, CSV reproducibility tests | 2026-05-05 | cursor |
| P2-002 | Decision checkpoint resolved: proceed with operational spine path | 2026-05-05 | cursor |
| P3-001 | Execution seam (`ExecutionBackend`, `PaperExecutionBackend`) | 2026-05-05 | cursor |
| P3-002 | Scheduler seam injected into `BacktestRunner` | 2026-05-05 | cursor |
| P3-003 | RunJournal persistence + crash/resume + `candlery paper` CLI | 2026-05-05 | cursor |
