# Candlery — Current State

**Last Updated:** 2026-05-05T17:58:00Z
**Last Platform:** Cursor
**Current Phase:** Phase 3 — Operational Spine (paper-only)
**Phase Status:** In progress (3A/3B/3C/3D implemented, closure doc sync pending)

## Completed Tasks

- [x] T-000: Repo bootstrap (structure, config, docs, ai-state)
- [x] T-001: Instrument model (immutable dataclass, validated, ISIN field)
- [x] T-002: Candle model (OHLCV, timezone-aware timestamps, int volume)
- [x] T-005: TradingCalendar (holiday loading, UTC conversion, trading day logic)
- [x] T-003: Bhavcopy importer (CSV parsing, EQ filter, UTC timestamps, directory scan)
- [x] T-006: Strategy interface (abstract base + core types)
- [x] T-009: SMA crossover strategy (reference implementation)
- [x] T-007: Risk engine (basic limits: exposure, position size, daily cap)
- [x] T-008: Backtest runner (execution loop, portfolio tracking)
- [x] T-010: Performance metrics + journal (Sharpe, MDD, trade logging)
- [x] T-011: CLI entry point (argparse, YAML config loading, execution)
- [x] T-012: Static HTML tear sheet (`candlery backtest --html`, `candlery.reporting.html`)
- [x] T-014: Transaction costs — `TransactionCostModel`, YAML `backtest.costs` (bps per leg), `ExecutedTrade.fees`, HTML fees column
- [x] REPAIR: Phase 1a integration wiring fixed (provider calendar dependency + risk profile mapping)
- [x] REPAIR: Mock-heavy integration tests replaced with real wiring tests
- [x] REPAIR: Phase 1a smoke test gate added (`make phase1a-smoke`)
- [x] T-013: GitHub Actions CI — `.github/workflows/ci.yml` (Python 3.11, `make test` + `make phase1a-smoke` on push/PR to `main`)
- [x] AUDIT: Holiday data completed (2024–2026), type fixes, timezone enforcement
- [x] REFACTOR: Package renamed src/ → candlery/, .gitignore fixed
- [x] RESEARCH: Strict-gate robustness cycle completed on real data (SMA families, filters, exits, breakout, cross-sectional variants)
- [x] RESEARCH: Multi-horizon information-content diagnostics completed (`ret20` signal identified, regime-dependent behavior confirmed)
- [x] DECISION: Pre-committed long-short falsification test executed; acceptance criteria not met; STOP-R&D decision recorded
- [x] DOC: Validation/decision/closeout artifacts added:
  - `docs/ai-state/VALIDATION_GATE_REPORT.md`
  - `docs/ai-state/PHASE2_DECISION_MEMO.md`
  - `docs/ai-state/PHASE2_SCOPE_MEMO.md`
  - `docs/ai-state/PHASE2_NULL_RESULT_NOTE.md`
- [x] PHASE3-A: Added execution seam (`ExecutionBackend`, `PaperExecutionBackend`) with tests.
- [x] PHASE3-B: Added scheduler seam (`Scheduler`, `CalendarScheduler`) and runner injection path.
- [x] PHASE3-C: Added append-only JSONL `RunJournal` with crash/resume day-boundary replay.
- [x] PHASE3-D: Added `candlery paper` CLI command with journal + resume wiring.

## Next Priority

1. Finalize Phase 3 closeout notes and usage docs for `candlery paper`.
2. Curate repository hygiene (remove disposable research artifacts from tracking decisions).
3. Hold strategy R&D stop policy on `data_real` unless explicit re-scope criteria are met.

## Architecture Summary

- Package: `candlery/` (imports: `from candlery.x.y import Z`)
- All timestamps: UTC, timezone-aware
- Data models: frozen dataclasses in `candlery/core/`
- Config: YAML (exchanges) + JSON (holidays) in `config/`
- Tests: `tests/` mirror of `candlery/` — **156 tests passing** + `phase1a-smoke` passing

## Known Issues / Explicit Limits

- Corporate actions not handled (documented gap)
- `float` used for prices (Decimal migration deferred to Phase 2)
- Current strategy research on `data_real` is closed with a documented null result; no robust edge has been validated.
- If **Insights → Contributors** still shows a stale co-author after a history rewrite, the [contributors API](https://api.github.com/repos/claaaro/candlery/contributors) is authoritative (expect **claaaro** only); try a hard refresh or wait for GitHub’s graph cache ([discussion](https://github.com/orgs/community/discussions/186158)).

## Key Files

- `candlery/core/instrument.py` — Instrument dataclass
- `candlery/core/candle.py` — Candle dataclass (OHLCV)
- `candlery/data/calendar.py` — TradingCalendar
- `candlery/data/importers/bhavcopy.py` — NSE Bhavcopy CSV parser
- `candlery/core/types.py` — Signal, OrderSide, TradeAction
- `candlery/strategy/base.py` — Abstract Strategy class
- `candlery/strategy/sma_crossover.py` — SMA crossover (reference impl)
- `candlery/strategy/volatility_breakout.py` — volatility-contraction breakout research implementation
- `candlery/risk/engine.py` — RiskEngine and RiskState
- `candlery/backtest/portfolio.py` — Portfolio and Position tracking
- `candlery/backtest/runner.py` — Core execution loop
- `candlery/backtest/metrics.py` — Performance metrics
- `candlery/backtest/costs.py` — STT/brokerage turnover model (bps or fractions)
- `candlery/journal/store.py` — Trade logging
- `candlery/journal/run_journal.py` — append-only run journal + resume state loader
- `candlery/execution/backend.py` — execution seam interface
- `candlery/execution/paper_backend.py` — paper execution adapter
- `candlery/runtime/scheduler.py` — scheduler seam
- `candlery/cli.py` & `candlery/__main__.py` — CLI entry point (`--html` tear sheet)
- `candlery/reporting/html.py` — static HTML report
- `docs/ai-state/VALIDATION_GATE_REPORT.md` — strict-gate results summary
- `docs/ai-state/PHASE2_DECISION_MEMO.md` — phase direction analysis
- `docs/ai-state/PHASE2_SCOPE_MEMO.md` — platform-scope option memo
- `docs/ai-state/PHASE2_NULL_RESULT_NOTE.md` — final stop decision note
- `candlery/data/provider.py` — Backtest data provider
- `config/exchanges/nse.yaml` — NSE market hours
- `config/holidays/nse_202{4,5,6}.json` — Holiday calendars
- `tests/data/test_calendar.py` — 25 tests
- `tests/data/importers/test_bhavcopy.py` — 19 tests
