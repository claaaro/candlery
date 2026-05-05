# Candlery

Institutional-grade algorithmic trading platform under phased delivery:
Backtest -> Reporting -> Complex Markets -> Forex -> Live Execution.

## Current Scope

- Phase 1 foundation (EOD backtesting + reporting + costs + strict validation gate): **complete**
- Phase 2 strategy research on current daily dataset: **closed with null result** (see `docs/ai-state/PHASE2_NULL_RESULT_NOTE.md`)
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

On GitHub, the same checks run via **Actions** on pushes and pull requests to `main` (see `.github/workflows/ci.yml`). If your PAT rejected workflow file updates when pushing, grant the **`workflow`** scope once or push this file via SSH.

Backtest report outputs:

- HTML tear sheet: `candlery backtest --config config/example_backtest.yaml --html reports/run.html`
- CSV bundle: `candlery backtest --config config/example_backtest.yaml --csv reports/run1`
  - writes `reports/run1_summary.csv`, `reports/run1_trades.csv`, `reports/run1_equity.csv`

Paper-mode (journaled, resumable) output:

- `candlery paper --config config/example_backtest.yaml --data-dir data_real --journal reports/paper_run.jsonl --run-id demo --resume --csv reports/paper_demo`

## End-of-Phase Validation Gate

Before marking a phase complete, run this lightweight checklist:

1. Code/test gate:
   - `python3 -m pytest tests/ -q`
   - `make phase1a-smoke` (or phase-equivalent smoke test)
2. Baseline run with artifacts:
   - run backtest with both `--html` and `--csv`
3. One controlled variation:
   - change one variable only (e.g., strategy parameter or cost setting)
   - run again with a different report prefix
4. Compare baseline vs variation:
   - `total_trades`, `total_fees`, return, drawdown, and notable trade rows
5. Record a short conclusion:
   - better / worse / inconclusive and why

Use this gate for system-validation confidence; do not infer production strategy quality from tiny/synthetic datasets.

For full closeout context and decisions:

- `docs/ai-state/VALIDATION_GATE_REPORT.md`
- `docs/ai-state/PHASE2_DECISION_MEMO.md`
- `docs/ai-state/PHASE2_SCOPE_MEMO.md`
- `docs/ai-state/PHASE2_NULL_RESULT_NOTE.md`

## Commit Identity Guardrails

Candlery enforces a single commit identity and blocks co-author/agent attribution text.

Run once per clone:

```bash
make setup-hooks
```

This installs a local `commit-msg` guard (versioned in `.githooks/`) and configures:

- `git config core.hooksPath .githooks`

Manual check:

```bash
make check-identity
```

CI also enforces these rules on pushed commits via `scripts/check_commit_identity.sh`.

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
