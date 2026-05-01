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

Then run:  make phase1a-smoke

If it fails, fix what's broken. Do not start new features until it passes.

If it passes, pick the first READY task in docs/ai-state/CURRENT_STATE.md (see also docs/ai-state/TASK_QUEUE.md).

Hard constraints:

- You may NOT modify docs/ai-state/SYSTEM_KEY.md and .py files in the same commit.
- You may NOT use MagicMock on a class whose name appears in the test filename.
- You may NOT mark anything "complete" without `make phase1a-smoke` passing.

That's the entire onboarding protocol. No 200-line "strict environment" preamble. The repo enforces the rest.
```

Architecture and phase boundaries: `docs/CONSTITUTION.md`.
