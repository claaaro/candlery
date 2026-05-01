# SYSTEM KEY — Candlery Restart Rules

Use this file as the operational source of truth when resuming work.

## Identity

- Project: Candlery
- Root path: `/Users/charan/Documents/candlery-workspace/candlery`
- Package: `candlery`
- Current phase: Phase 1a (EOD Equity Backtesting MVP)

## Non-Negotiable Architecture

- Core data models are immutable frozen dataclasses.
- All timestamps must be timezone-aware UTC (no naive datetimes).
- Strategy emits signals only; no capital/risk management in strategy code.
- Portfolio tracks state only (cash, positions, equity).
- RiskEngine validates and gates actions only.
- Prices remain `float` in Phase 1; preserve a clean path to `Decimal` migration.

## Phase Lock

- Do not implement Phase 1b+ features until Phase 1a is verified end-to-end.
- "Verified" means the integration smoke test and full test suite both pass.

## Development Rules

- All code stays under the project root; no parallel work directories.
- Import using `from candlery.x.y import Z` only.
- Every new package directory must include `__init__.py`.
- Tests must validate real wiring for the unit under test.
- Do not hide integration bugs behind broad mocks of core contracts.

## Validation Before Marking Work Complete

```bash
cd /Users/charan/Documents/candlery-workspace/candlery
python3 -m pytest tests/ -q
make phase1a-smoke
```

If either command fails, fix code/tests before advancing tasks.
