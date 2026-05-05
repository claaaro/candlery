# Phase 3 Operational Spine Memo — Minimum Execution/Scheduler/Journal Design

## Purpose

Phase 1 and Phase 2 closed with the following durable conclusion:

- The Candlery backtester, costs, reporting, validation gate, and integrity checks are correct.
- No strategy passed the strict gate on the current dataset.
- The project's stated long-term goal is **a strong, proven, working, automated, full-time trader.**

That goal cannot be reached by more research alone. It requires an **operational spine**: the minimum scaffolding that turns a hypothetical strategy into something that can actually run forward in time, persist its own state, recover from interruption, and be audited.

This memo defines the **smallest possible** such spine. It is **design only** — no code, no data acquisition, no strategy work.

---

## Guiding Principles

- **Strategy-agnostic.** The spine must not assume SMA, momentum, breakout, or any specific class.
- **Paper first, always.** No real broker integration in this phase.
- **Deterministic and replayable.** Same inputs and same time produce same outputs.
- **Crash-safe by construction.** Restart must not corrupt state or duplicate trades.
- **Boring on purpose.** No microservices, no dashboards, no plugin systems.
- **Reuse Phase 1 contracts.** `Strategy`, `TransactionCostModel`, `ExecutedTrade`, reports — unchanged.

---

## Explicit Non-Goals

- No new strategy logic or new indicators.
- No data acquisition (intraday, fundamentals, events).
- No live broker integration.
- No alerting, dashboards, or web UI.
- No multi-tenancy, queues, or distributed components.
- No premature abstraction (e.g., generic event bus, plugin loaders, config DSLs).
- No portfolio optimizer, no allocator framework.

If a feature is not strictly required for "run a strategy forward in time, paper, deterministically, with persistent state," it does not belong in this phase.

---

## Scope (Three Thin Abstractions Only)

### 1. ExecutionBackend (paper-only)

A single interface representing "where orders go and where fills come from."

- One concrete implementation: `PaperExecutionBackend`.
- Inputs: a normalized order request (symbol, side, qty, intended fill rule).
- Output: a deterministic fill (or rejection) using the same cost model as backtests.
- Fill model: must be **explicit and documented** (e.g., next-bar-open, same-day-close, or a configurable choice). Whatever is chosen must match an assertion test.
- No retries, no rate limits, no partial-fill simulation beyond what the backtester already does.
- The **only** seam where a future live broker would plug in.

### 2. Scheduler (daily, deterministic, replayable)

A loop that walks calendar time forward and triggers strategy evaluation + execution at known points.

- Driven by `TradingCalendar` (already exists).
- One configurable trigger time per session (e.g., end-of-day evaluation).
- Replayable: given a "today" (real or simulated), the scheduler must produce the same sequence of evaluations as a backtest covering the same dates.
- Two run modes:
  - **Backtest mode**: walks all historical dates (already exists; this just formalizes the seam).
  - **Forward-paper mode**: walks dates one at a time as real time advances, never reading future data.
- Forward mode must refuse to evaluate a day whose required data is not yet available (no peeking).

### 3. RunJournal (persistent state store)

A small, file-based persistence layer that lets a paper run survive process restarts and stay auditable.

- Stores, per run:
  - resolved configuration snapshot,
  - per-day evaluation outcome,
  - submitted orders,
  - confirmed fills,
  - current positions and cash,
  - last successfully completed simulated/real day.
- Format: append-only JSONL or SQLite-single-file. Choice deferred to implementation phase, but must be:
  - human-readable or trivially dumpable to text,
  - safe under crash mid-write,
  - replayable to reconstruct full state.
- Crash semantics:
  - Restart reads the journal and resumes from the last fully-written day boundary.
  - It must never re-execute a day already journaled as completed.
  - It must never silently drop a day.

That is the entire scope. Three abstractions. One concrete implementation each. No more.

---

## Acceptance Gate (Phase 3 Strict Gate)

Operational, not edge-based. All must pass before Phase 3 closes.

- **G1 — Determinism**: identical inputs and identical "today" produce identical journal entries (byte-equality where reasonable, numeric-equality otherwise).
- **G2 — No leakage**: forward-paper mode must reproduce backtest results to within numerical tolerance over the same date range, with no future-data access (asserted by tests).
- **G3 — Crash safety**: a forced kill mid-day during a paper run must, on restart, produce the same final state as an uninterrupted run of the same scenario.
- **G4 — Strategy agnosticism**: the spine must run end-to-end with at least two structurally different stub strategies (e.g., always-buy and always-flat) without any spine-side branching on strategy type.
- **G5 — No silent days**: every scheduled trading day either completes normally or raises a clearly-typed error; no skipped or partial-completed days are tolerated.

Failure of any single gate item blocks Phase 3 closeout.

---

## Sequencing (Inside Phase 3, When We Implement)

Each step is independently shippable and testable. Each ends with a green-or-red status, never partial.

1. **3A — ExecutionBackend (paper)**: implement `PaperExecutionBackend`, port backtester's existing fill+cost logic behind this interface.
2. **3B — Scheduler seam**: refactor (do not rewrite) the existing backtest loop to drive through the scheduler abstraction, and add forward-paper mode that runs day-by-day from a "today" cursor.
3. **3C — RunJournal**: add the persistence layer and crash-resume semantics; assert via tests.
4. **3D — Closure**: assemble everything into a single `candlery paper` CLI command that runs forward, persists, and resumes — using existing strategies as stubs.

No phase ends without its corresponding gate items green.

---

## Risks and Mitigations

- **Mission creep into strategy work**:
  Mitigation: any commit touching `candlery/strategy/*` or introducing new indicators is out of Phase 3 scope and requires explicit re-approval.
- **Premature abstraction**:
  Mitigation: each of the three abstractions has exactly one implementation and exactly one consumer in this phase. No interfaces "for future flexibility."
- **Quietly redesigning the backtester**:
  Mitigation: the backtester behavior is treated as the source of truth. Phase 3 wraps it; it does not rewrite it. G2 is the enforcement test.
- **Building monitoring before there is anything worth monitoring**:
  Mitigation: alerts/dashboards are explicitly excluded; we will revisit only after a real strategy is paper-running.

---

## What Phase 3 Does Not Decide

- Whether a real strategy edge exists.
- Whether/when to acquire new data classes.
- Live broker selection or integration design.
- Position sizing, portfolio construction, or risk overlays beyond what already exists in `RiskEngine`.

These remain explicit Phase 4+ decisions.

---

## Sign-Off Conditions for This Memo

This memo is approved if and only if:

- The three abstractions above are accepted as the entire scope of Phase 3.
- The non-goals list is accepted as binding.
- The acceptance gate (G1–G5) is accepted as the closeout standard.

If any of these are rejected, **do not begin implementation** — revise this memo first.

---

## Honest End-State Statement

Phase 3, done minimally, leaves Candlery with: a strategy-agnostic, deterministic, crash-safe, paper-only execution spine that mirrors backtest behavior and can run forward in calendar time without supervision.

That is the smallest concrete step toward the stated end-goal — a working automated full-time trader — that does not depend on first finding an edge. Edge can come later, from new data or new hypotheses, and will plug in without redesign.
