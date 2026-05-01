# Candlery — Multi-platform handoff (paste-first message)

Use this as the **first message** when switching AI tools or models (Antigravity, Copilot, Cursor, etc.). Keep it short; the repo is the source of truth.

---

```
You are continuing work on Candlery.

Repo root: /Users/charan/Documents/candlery-workspace/candlery
Remote:    https://github.com/claaaro/candlery

Before doing anything, run these four commands and read their output:

  git status
  git log --oneline -10
  cat docs/ai-state/SYSTEM_KEY.md
  cat docs/ai-state/CURRENT_STATE.md

Then run:

  make phase1a-smoke

If it fails, fix what's broken. Do not start new features until it passes.

If it passes, pick the next task from CURRENT_STATE.md / TASK_QUEUE.md (follow SYSTEM_KEY.md workflow).

Hard constraints:

- You may NOT modify SYSTEM_KEY.md and .py files in the same commit.
- You may NOT use MagicMock on a class whose name appears in the test filename.
- You may NOT mark anything "complete" without `make phase1a-smoke` passing.

That's the entire onboarding protocol. No long "strict environment" preamble — the repo enforces the rest.
```

---

## Optional full verification

After smoke passes:

```bash
python3 -m pytest tests/ -q
```
