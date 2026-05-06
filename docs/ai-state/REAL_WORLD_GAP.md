# REAL-WORLD GAP — Capability Scoreboard

Single source of truth for how far Candlery is from a fully functional, real-world trading system.
Each row's "Next Non-Doc Act" must be an act on the world (a run, a fetch, a contract, a halt).
Docs are a fallback only when no non-doc act is available — and that must be explicit.

| # | Capability | Current | Target | Gap | Next Non-Doc Act |
|---|------------|---------|--------|-----|------------------|
| 1 | Backtest engine | done (validated, deterministic, leakage-checked) | same | none | — |
| 2 | Transaction cost model | done (per-leg STT/brokerage) | same | none | — |
| 3 | Strict validation gate | done (PF, expectancy, min trades, no negative return) | same | none | — |
| 4 | HTML / CSV reporting | done | same | none | — |
| 5 | Paper-execution backend (code) | exists, unit-tested, never executed forward | exercised in real run | **0 forward runs** | execute `candlery paper` once end-to-end (this session) |
| 6 | Scheduler abstraction | exists, never driven outside tests | drives daily ticks of a real run | unused | same as row 5 |
| 7 | Run journal + resume | code exists, never used outside tests | journals every paper day, supports crash-resume | unused | same as row 5 + then `--resume` once |
| 8 | Live daily data ingestion | none — only static historical bhavcopy CSVs | automated daily fetch dropping one file into `data/` | no fetcher | write a one-shot bhavcopy fetch script (separate session) |
| 9 | Continuous forward paper run | nothing running | `candlery paper --resume` invoked every trading day | no schedule | manual daily invocation, then cron/launchd (after row 8) |
| 10 | Signal source plugged in | none — first attempt (forward interpretation contract) INVALIDATED 2026-05-06 due to statistically vacuous discrimination test (P~2/3 under null at N=3); replaced by signal_discovery registration template + canary plumbing | ≥1 signal source under forward observation | no candidate registered | register first candidate under `reports/signal_discovery/` per `SIGNAL_DISCOVERY_NOTE.md` (with cargo-cult check + real power calc), OR do nothing — picking under fatigue is forbidden |
| 11 | Promotion protocol (paper → live) | none | written, binding, includes forward-time minimum, DD cap, trade count | undefined standard | (no non-doc act available — doc fallback justified once row 9 is real) |
| 12 | Broker integration | none — no account, no API plan | one read-only / dry-run broker connection | unaddressed | pick broker, open account, generate API token, read-only test |
| 13 | Operator routine | none | daily review checklist + halt rules | unaddressed | (defer; only meaningful once row 9 is live) |
| 14 | Capital sizing rules beyond engine | none | conservative position % + DD halt at portfolio level | undefined | (defer; only meaningful once row 11 exists) |

## Reading rules

- A row whose Next Act is a doc is **incomplete**. Rows 11/13/14 are docs only because the corresponding world act is blocked by a prior row.
- A row counts as "done" only after the Next Act has been executed at least once with a real artifact. Code passing tests is **not** "done."
- Any new code/abstraction added to Candlery must close at least one gap in this table. If it does not, it is over-engineering — reject.

## Binding rules from forensic audit (locked in)

These rules govern future agent behavior on this project. They are not aspirational.

- R1. Edits to `docs/ai-state/*` are bookkeeping, not progress.
- R2. No subsystem is "done" until exercised forward at least once.
- R3. No new abstraction unless ≥2 concrete implementations are required today.
- R4. When user uses words "over-engineer", "challenge", or "don't default to", produce a binding constraint, not a reflection.
- R5. Reviewer-mode responses end with ≤3 enforced rules; check them next turn.
- R6. A "stop" decision is binding for the session; reversal must be explicit.
- R7. "Minimal next step" defaults to a world-changing act; doc is fallback only.
- R8. On user "yes/proceed", if the next act is a doc, pause and re-ask whether a non-doc act exists.
- R9. ≤1 closeout memo per phase; phase incomplete without an operational artifact.
- R10. Every recommendation must be justified against the row in this scoreboard it closes.

## Phase status check

- Operational frontier crossed: **pending — see row 5/6/7 act in this session.**
- Live data ingestion: **not started** — row 8.
- Promotion protocol: **not started** — row 11, blocked on row 9.
