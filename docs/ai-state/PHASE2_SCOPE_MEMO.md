# Phase 2 Scope Memo — Paper Execution and Monitoring Layer

## Purpose

Phase 1 strict-gate validation rejected all tested strategy classes. Continuing strategy R&D on the current dataset is no longer the highest-value work.

Phase 2 redirects effort to **platform value**: build the paper-trading, execution simulation, and monitoring layer so that when a real strategy edge does emerge (Phase 3+), deployment is fast, safe, and auditable.

This memo defines scope, non-goals, deliverables, and a strict acceptance gate, with **no new strategy code in scope**.

---

## Guiding Principles

- **No alpha promises.** This phase does not aim to produce edge.
- **Operational truth over predicted PnL.** All success criteria are mechanical and verifiable.
- **Reuse Phase 1 contracts.** Strategy interface, cost model, and reporting outputs stay unchanged.
- **Small, shippable modules.** Each deliverable closes independently and is testable.
- **Same auditability standards.** Same validation gate philosophy: results must be reproducible and out-of-sample with respect to the data used.

---

## Explicit Non-Goals

- No new strategy logic.
- No new indicator R&D.
- No parameter tuning of prior strategies.
- No live broker integration in this phase.
- No real-money trading.

---

## Scope (What Phase 2 Will Build)

### 1. Paper Trading Engine (offline)

A deterministic, replayable simulator that consumes Phase 1 strategy output and produces simulated trade fills using realistic mechanics:

- Open-to-execution timing realism (e.g., signal generated EOD, fill at next-day open).
- Fill model:
  - Use next-bar open price.
  - Apply existing cost model unchanged.
  - Optional simple slippage cap.
- Position lifecycle: open, manage, close, mark-to-market.
- Output: trade journal compatible with existing reporting.

### 2. Live-Style Paper Loop (forward simulation)

A loop that runs the strategy on a frozen dataset day-by-day in **forward-only** mode:

- Strict information barrier: no future leakage.
- Deterministic and reproducible from a seed/start-date.
- Generates the same artifacts as backtest (HTML + CSV) for direct comparison.
- This becomes the standard “shadow mode” when a candidate strategy emerges later.

### 3. Monitoring + Telemetry

Operational visibility for any paper or future live deployment:

- Per-day session log (positions, cash, PnL, fees).
- Threshold alerts (text-only, no integrations yet):
  - drawdown breach
  - missing data day
  - unexpected zero-trade days
- Standardized snapshot format for downstream tools.

### 4. Configuration Hardening

Operational reliability of configuration before any live work:

- Strict YAML schema validation for backtest, risk, universes, and costs.
- Clear errors for missing files and missing keys.
- A single startup pre-flight check that loads all configs, validates them, and prints a green/red summary.

### 5. Reproducibility Pack

Each run (backtest or paper) emits a reproducibility bundle:

- Resolved configuration (post-merge, post-defaults).
- Data hash or coverage summary.
- Code revision identifier.
- Cost model and risk profile fingerprint.

---

## Acceptance Gate (Phase 2 Strict Gate)

Phase 2 success is measured operationally, not by edge:

- **G1 — Determinism:** identical inputs produce identical outputs (byte-for-byte where reasonable, or numerically-stable equivalent).
- **G2 — No leakage:** forward-only paper loop must reproduce backtest results to within numerical tolerance.
- **G3 — Telemetry coverage:** required alerts fire on synthetic test scenarios (forced drawdown, missing day, zero-trade window).
- **G4 — Config safety:** invalid YAML or missing keys produce structured errors, not silent defaults or crashes.
- **G5 — Reproducibility:** every run produces a self-contained bundle that can rebuild the same result later.

Failure of any gate item blocks Phase 2 closeout.

---

## Dependencies On Phase 1

- Strategy interface (`Strategy`).
- Cost model (`TransactionCostModel`).
- HTML/CSV reporting modules.
- Validation gate as a reusable measurement standard (carries forward to Phase 3 strategy work).

---

## Phasing Inside Phase 2

The work splits into **four sequential mini-phases**, each independently shippable:

1. **2A — Paper Execution Simulator** (item 1)
2. **2B — Forward-Only Paper Loop** (item 2)
3. **2C — Monitoring + Telemetry** (item 3)
4. **2D — Config Hardening + Reproducibility Pack** (items 4 and 5)

Each mini-phase ends with:
- unit tests passing,
- gate items relevant to it passing,
- short closeout entry in `CURRENT_STATE.md`.

---

## Risks and Mitigations

- **Risk:** mission creep into strategy work during infrastructure builds.  
  **Mitigation:** explicit non-goals above; PRs/edits touching `candlery/strategy/*` are out of scope until Phase 3.
- **Risk:** infrastructure that overfits to one specific strategy assumption.  
  **Mitigation:** all interfaces are strategy-agnostic; tested with at least two strategy stubs.
- **Risk:** invisible regressions in backtest engine while building paper layer.  
  **Mitigation:** require G2 (paper-vs-backtest equivalence) before closing.

---

## What Phase 2 Does Not Decide

- Whether a real edge exists or not.
- Whether/when to acquire new data.
- Whether to pivot universe or timeframe.

These remain open Phase 3 decisions, supported by better tooling delivered in Phase 2.

---

## Decision Required

- Approve Phase 2 scope as defined.
- Approve starting with **mini-phase 2A (Paper Execution Simulator)** as the first concrete deliverable.
- Or override with a different sequencing.
