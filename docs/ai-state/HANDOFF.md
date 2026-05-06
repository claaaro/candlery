# Candlery — handoff prompt (copy below)

Paste **everything inside the fenced block** as the first message on any new platform/model.

```
You are continuing work on Candlery.

Repo root: /Users/charan/Documents/candlery-workspace/candlery
Remote:    https://github.com/claaaro/candlery

Before doing anything, run these four commands and read their output:

  git status
  git log --oneline -10
  cat docs/ai-state/SYSTEM_KEY.md
  cat docs/ai-state/CURRENT_STATE.md
  cat docs/ai-state/CANARY_NOTE.md
  cat docs/ai-state/SIGNAL_DISCOVERY_NOTE.md
  cat docs/ai-state/FORWARD_INTERPRETATION_CONTRACT.md   # marked INVALID — read why

Then run:  make phase1a-smoke

If it fails, fix what's broken. Do not start new features until it passes.

Current state (2026-05-06):
- W1 forward-interpretation contract is INVALID (discrimination test vacuous at N=3, P~2/3 under null).
- Three replacement mechanisms in place: canary (plumbing-only, NOT started), signal_discovery (NO CANDIDATE), audit rule (path-or-no-claim).
- Real NSE data available through 2026-05-06 in data/day_udiff_*.csv.
- W1 pre-window context locked in reports/forward_context/2026-05-04.json (preserved as historical record only — NOT strategic evidence).
- Last decided next move: pick the first signal candidate to register under reports/signal_discovery/, OR do nothing. Either is valid. Picking under fatigue is forbidden.
- Risk #5 (governance becoming identity) is structurally bounded by canary's signal-research-coupling; do NOT add more meta-rules to manage this.

If it passes, pick the first READY task in docs/ai-state/CURRENT_STATE.md (see also docs/ai-state/TASK_QUEUE.md).

Hard constraints:

- You may NOT modify docs/ai-state/SYSTEM_KEY.md and .py files in the same commit.
- You may NOT use MagicMock on a class whose name appears in the test filename.
- You may NOT mark anything "complete" without `make phase1a-smoke` passing.

That's the entire onboarding protocol. No 200-line "strict environment" preamble. The repo enforces the rest.
```

Architecture and phase boundaries: `docs/CONSTITUTION.md`.
