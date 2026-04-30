# AI Continuation Protocol

**This file MUST be read by every AI agent before starting work.**

---

## What Is This Project?

Candlery is an algorithmic trading platform. Phase 1a builds an equity EOD backtesting engine (CLI only, no UI). The core pipeline is: Strategy → Risk → Execution (deterministic, no LLM in the trading path).

## How to Start a New Session (ANY Platform)

```
Step 1: Open the repository
        → git pull origin main

Step 2: Read these files IN ORDER:
        1. docs/ai-state/CURRENT_STATE.md     (what's done, what's next)
        2. docs/ai-state/TASK_QUEUE.md         (pick next READY task)
        3. This file                           (rules and constraints)

Step 3: Identify the next READY task from TASK_QUEUE.md

Step 4: Announce what you will work on:
        "Resuming Phase 1a. Working on T-XXX: [description]."

Step 5: Implement the task (full module + tests)

Step 6: Verify:
        cd <project_root>
        python3 -m pytest tests/ -v

Step 7: Before ending session, update:
        - docs/ai-state/CURRENT_STATE.md
        - docs/ai-state/TASK_QUEUE.md
```

## Platform-Specific Instructions

### Google Antigravity
- Has file system access and can run commands
- Can generate and write files directly
- Can run pytest to verify
- Ideal for: multi-file tasks, architecture work, debugging

### Cursor
- IDE-integrated, works best with single-file edits
- Use Composer for multi-file changes
- Always verify imports after creating new files
- Ideal for: modifying existing files, quick iterations

### GitHub Copilot
- Best for inline code completion and boilerplate
- Less effective for multi-file architectural work
- Always provide full context (paste CURRENT_STATE.md content)
- Ideal for: writing tests, implementing simple functions

## What to Give the New AI Platform

When switching platforms, paste this into the first message:

```
You are continuing development on the Candlery algorithmic trading platform.

Repository: https://github.com/claaaro/candlery
Local path: /Users/charan/Documents/candlery-workspace/candlery

Before doing anything:
1. Read docs/ai-state/CURRENT_STATE.md
2. Read docs/ai-state/TASK_QUEUE.md
3. Read docs/ai-state/CONTINUATION.md

Then pick the next READY task and implement it.

Package name: candlery (NOT src)
Imports: from candlery.x.y import Z
All timestamps: UTC, timezone-aware
Tests: python3 -m pytest tests/ -v
```

## What MUST NOT Be Relied On

- **No chat memory.** Every session starts fresh. The repo is the only memory.
- **No assumptions about what was done.** Always read CURRENT_STATE.md.
- **No hidden context.** If it's not in the repo, it doesn't exist.
- **No platform-specific features.** Code must work on any platform.

## Coding Rules (ALL Platforms Must Follow)

1. **Package:** `candlery/` — imports are `from candlery.x.y import Z`
2. **Timestamps:** Always `datetime` with `tzinfo` set (UTC)
3. **Data models:** Frozen dataclasses in `candlery/core/`
4. **Config:** YAML for exchange settings, JSON for holidays, YAML for risk/backtest
5. **Tests:** Mirror structure in `tests/`, use `tmp_path` fixtures, no dependency on real config files
6. **Commits:** Use `[T-XXX]` prefix in commit messages
7. **No silent architecture changes.** If you need to change an interface, document in CURRENT_STATE.md first.
8. **No reformatting files you aren't changing.**
9. **Every new directory under `candlery/` must have `__init__.py`.**
10. **After creating any module, verify:** `python3 -c "from candlery.<path> import <name>"`
