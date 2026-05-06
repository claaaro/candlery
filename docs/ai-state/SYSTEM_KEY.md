# SYSTEM KEY — Candlery Single-File Control

Use this as the single handoff file across any AI platform/model.
If there is any conflict with other docs, follow this file first.

## 0) Project Reality (Current)

- Project: `candlery`
- Goal: fully functional real-world trading system (not just backtests)
- Current truth:
  - backtest + validation system: working
  - strict gate: working; prior strategy research ended in null result
  - paper execution spine (`paper` + scheduler + journal): now exercised in a real run
- Current risk: behavioral drift (doc-first work, over-engineering, weak turn-by-turn enforcement)

## 1) Mandatory Playbook Order (1 to 5)

Every AI session must follow this order exactly.

1. **Start-of-session declaration**
   - AI must first output:
     - `Action type: act|doc`
     - `Gap row: <row number from REAL_WORLD_GAP>`
     - `Non-doc alternative considered: <one line or none>`
   - If action type is `doc`, AI must pause and ask approval before writing.

2. **Approval rule**
   - User only approves if:
     - the action closes a real gap row,
     - it is the smallest reversible step,
     - and a non-doc alternative was considered.

3. **Mid-session drift kill switch**
   - If direction becomes fuzzy, user sends:
     - `Pause. Re-state current goal, action type, gap row, and why this is not over-engineering.`
   - AI must re-anchor before continuing.

4. **End-of-session closure**
   - AI must output:
     - what changed in the world,
     - which gap row moved,
     - which files changed,
     - what remains blocked,
     - next smallest step (approval required).

5. **No silent continuation**
   - AI cannot auto-continue into the next phase/task without explicit user approval.

## 2) Operator Prompt Prefix (Copy/Paste in Any AI Tool)

Use this at the start of every new chat:

`Before any work: read SYSTEM_KEY.md and then state Action type (act/doc), Gap row, and one non-doc alternative considered. If your next step is doc-shaped, stop and ask before writing. Do not proceed until I approve.`

## 3) Handoff Snapshot (Minimal)

- Canonical codebase path: `/Users/charan/Documents/candlery-workspace/candlery`
- Most recent structural additions already in repo: execution backend, scheduler seam, run journal, `candlery paper` CLI.
- For strategy research on current dataset: halted after null result.
- Current emphasis: prevent drift and advance only through measurable gap closure.

## 4) Real-World Gap (Condensed Scoreboard)

Use these row IDs in every session:

- **R5** Paper backend exercised in real runs
- **R6** Scheduler exercised via real runs
- **R7** Journal + resume exercised and verified
- **R8** Live daily data ingestion (missing)
- **R9** Continuous forward paper routine (missing)
- **R10** Signal source plugged into forward observation (missing)
- **R11** Promotion protocol paper -> live (pending; useful after R9 exists)
- **R12** Broker integration path (missing)

Interpretation:
- R5-R7: started and exercised at least once.
- R8-R12: still meaningful blockers toward real-world system.

## 5) Anti-Drift Enforcement Rules

- Do not count edits in `docs/ai-state/*` as progress by default.
- No new abstraction unless at least two concrete consumers are needed now.
- A subsystem is not "done" until it runs in a real operational path at least once.
- If user says "over-engineering", "challenge", or "don't default", AI must switch to constraint mode (specific limits), not narrative mode.
- "Stop" decisions are binding unless explicitly reversed by user.

## 6) Supporting Docs (Optional, Not Required to Start)

- `AGENTS.md` (boot router)
- `docs/CONSTITUTION.md` (architecture invariants)
- `docs/ai-state/REAL_WORLD_GAP.md` (full scoreboard + rules R1-R10)
- `docs/ai-state/HANDOFF.md` (extended continuity details)

## 7) Current Active Mechanisms (as of 2026-05-06)

The W1 forward-interpretation contract is **INVALID** — its discrimination
test was statistically vacuous at N=3 (P≈2/3 under null). Replacement
structure is three small mechanisms, all in `docs/ai-state/`:

- `CANARY_NOTE.md` — operational plumbing only, no strategy claims, dies
  in 10 trading days unless re-approved with concrete operational evidence
  AND fresh signal-research artifact. Hard ceiling 60 days. NOT yet started.
- `SIGNAL_DISCOVERY_NOTE.md` — registration template for actual signal
  candidates. Requires hypothesis + literature + 4-point cargo-cult check
  (decay/cost/regime/crowding) + real power calc. NO CANDIDATE REGISTERED.
- AUDIT RULE (in both notes above): any strategy claim must inline a path
  to a `reports/signal_discovery/` artifact. No path = no claim.

Risk #5 (governance becoming identity): structurally addressed by the
canary's signal-research-coupling. Do NOT add more meta-rules to govern
this — that itself would be Risk #5.

Next concrete decision (separate, not in any current contract):
**pick the first signal candidate to register, or do nothing.**

This file is intentionally compact. Keep it operational, not narrative.
