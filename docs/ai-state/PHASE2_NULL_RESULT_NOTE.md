# Phase 2 Null Result Note

## Purpose

Document, with full auditability, the result of the cross-sectional research cycle that followed Phase 1 closeout. This note is a deliberate stop signal: no further strategy R&D is to be conducted on this dataset until conditions change (new data, substantively different research framework, or explicit re-scoping).

---

## Summary in One Sentence

A real predictive signal was identified in the data, but it is **regime-bound**, fails the project's strict promotion gate out-of-sample, and does not survive a structural variation (long-short) — the precommitted falsification.

---

## Sequence of Investigations

1. **Phase 1**: tested SMA crossover families, entry filters, exit upgrades, and a single-name volatility breakout. All failed strict gate.
2. **Cross-sectional momentum probe (monthly long-short)**: long-short spread flat-to-negative, sign-unstable across halves. Falsified.
3. **Information-content diagnostic (1-day horizon)**: only `ret20` had statistically meaningful, sign-stable IC (mean ≈ +0.023). All other features were noise.
4. **Multi-horizon IC probe**: `ret20` IC strengthens monotonically from 1d → 5d → 10d (mean +0.025 → +0.049 → +0.066), still sign-stable across halves.
5. **Horizon-aligned long-only ranking strategy** (10d rebalance, top quintile): passed all 2024 folds strongly, failed all 2025 folds. Strict gate FAILED. Regime-bound result.
6. **Pre-committed long-short falsification test**: same strategy structurally extended to long-short, same six folds. All 2024 folds passed strongly, two 2025 folds failed cleanly, third 2025 fold barely positive. Pre-committed acceptance NOT met.

---

## Pre-Committed Acceptance Rule (Step 6)

A pass required:

- every fold valid (closes >= 10),
- every fold individually with PF > 1.1 and Expectancy > 0,
- no fold with negative total return.

**Result**: failed on multiple criteria simultaneously. Verdict: **STOP**.

---

## What Was Proven

- The Candlery backtesting engine, cost model, reporting, and strict validation gate function correctly.
- A statistically meaningful `ret20`-based predictive signal exists in the dataset.
- That signal is **regime-bound**, with strong 2024 performance and weak/negative 2025 performance.
- The regime-bound behavior survives long-only → long-short structural variation; it is not an artifact of position structure.

## What Was Not Proven (and we are not claiming)

- That the signal is permanently dead.
- That a more sophisticated regime-aware variant could not, in principle, work.
- That the dataset is permanently insufficient for any strategy.

We avoid these claims deliberately because they cannot be supported with 24 months of data.

---

## Decision

- **Stop strategy R&D on the current `data_real` daily NSE bhavcopy dataset.**
- Treat this state as the official closeout for the cross-sectional research arc.
- Do **not** attempt regime filters, parameter tuning, or stacked entry/exit refinements as a continuation, because those would be precisely the overfitting moves we pre-committed against after observing the failure pattern.

---

## Conditions Required to Resume Strategy R&D

Strategy R&D may resume only if at least one of the following is true:

1. New data is acquired:
   - intraday data (for short-horizon edges),
   - longer historical span (so regime variation is properly sampled),
   - alternative data (events, fundamentals, or microstructure).
2. A new, falsifiable hypothesis class with pre-committed acceptance rules is documented in advance.
3. The strict validation gate is re-evaluated and explicitly modified with stated reasons (not weakened to fit a desired outcome).

Any resumption must follow the same protocol: pre-commit the experiment, run it once, accept the verdict.

---

## Project State After This Note

- Phase 1 (engine + costs + reporting + gate): complete and validated.
- Phase 2 (post-Phase-1 cross-sectional research arc): **closed with null result**.
- Outstanding artifacts to keep:
  - `docs/ai-state/VALIDATION_GATE_REPORT.md`
  - `docs/ai-state/PHASE2_DECISION_MEMO.md`
  - `docs/ai-state/PHASE2_SCOPE_MEMO.md`
  - this file (`PHASE2_NULL_RESULT_NOTE.md`)
- The Candlery codebase remains a usable strategy validation framework. Its current value is operational discipline (gate enforcement) rather than alpha discovery.

---

## Post-Closeout Integrity Pass (2026-05-05)

After the STOP decision, a **minimal verification pass** was added (tests only; no new execution platform):

- **Incremental history**: strategy evaluation receives candles only through the current simulated day (`tests/backtest/test_runner.py::test_strategy_receives_incremental_history_only`).
- **Fill semantics (documented)**: trades execute at the **same-day close** as implemented in `BacktestRunner` (`tests/backtest/test_runner.py::test_execution_fill_uses_same_day_close`). This is not a next-bar open model; any future “signal EOD / fill next open” behavior would be an explicit product change with matching tests.
- **Report reproducibility**: identical `BacktestResult` inputs produce byte-identical CSV bundles (`tests/reporting/test_csv.py::test_write_csv_bundle_is_reproducible_for_same_input`).

These checks increase auditability of the engine and reporting layer; they do **not** change the null-result conclusion on strategy edge.

---

## Honest Concluding Statement

The most rigorous outcome a research process can produce is a clear, well-documented **null result** that is hard to argue with later. That is the outcome here.

This is not a failure of the project. It is the project's strict gate doing what it was designed to do: refusing to promote regime-fit strategies as if they were robust edges. The right action is to stop and wait for either better data or a fundamentally new hypothesis, not to continue iterating on the same dataset.
