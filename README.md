# Candlery

Institutional-grade algorithmic trading platform under phased delivery:
Backtest -> Reporting -> Complex Markets -> Forex -> Live Execution.

## Current Scope

- Phase: **Phase 1b (reporting)** — HTML tear sheet from `candlery backtest --html report.html`
- Phase 1a (EOD backtesting MVP): **complete** (CLI + smoke gate)
- Interface: **CLI only**
- Market: **NSE equities (Bhavcopy CSV)**
- Internal time standard: **UTC timezone-aware datetimes**

## Architecture Invariants

- Core models are immutable frozen dataclasses.
- Strategy emits signals only.
- Portfolio tracks state only.
- RiskEngine validates and gates actions only.
- Trading runtime path is deterministic code (no LLM in hot path).
- Prices are `float` in Phase 1 with a planned `Decimal` migration path.

See `docs/CONSTITUTION.md` for the durable architecture and phase-lock rules.

## Repository Layout

```
candlery/               # Python package
  core/                 # Candle, Instrument, types
  data/                 # calendar, importer, provider
  strategy/             # strategy interfaces and implementations
  risk/                 # risk firewall
  backtest/             # runner, portfolio, metrics
  reporting/            # HTML tear sheets
  journal/              # executed trade journal
tests/                  # mirrors package modules + smoke tests
config/                 # exchanges, holidays, risk profiles, universes
docs/                   # constitution and ai-state
```

## Local Development

Run from project root:

```bash
python3 -m pytest tests/ -q
make phase1a-smoke
```

Both commands must pass before treating work as complete.

## Data Notes

- Do not commit raw market data.
- Keep local CSV input under a non-committed data directory.
- `.gitignore` intentionally uses `/data/` (anchored) to avoid hiding `candlery/data/`.

## AI Session Restart

For cross-platform continuation, start with:

- `docs/ai-state/SYSTEM_KEY.md`
- `docs/ai-state/CURRENT_STATE.md`
- `docs/ai-state/TASK_QUEUE.md`

The repository is the source of truth; chat memory is not.
