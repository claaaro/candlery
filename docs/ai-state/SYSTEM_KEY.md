# SYSTEM KEY — Universal AI Restart File

**Read this file FIRST. It contains everything needed to resume work.**

---

## 1. Project Identity

| Field | Value |
|---|---|
| **Name** | Candlery |
| **Purpose** | Algorithmic trading platform — equity EOD backtesting |
| **Phase** | 1a — Backtesting MVP (CLI only) |
| **Repo** | https://github.com/claaaro/candlery |
| **License** | MIT |

## 2. Root Path

```
/Users/charan/Documents/candlery-workspace/candlery
```

ALL files live here. No exceptions. No parallel directories.

## 3. Package Name

```
candlery
```

NOT `src`. NOT `main`. The package directory is `candlery/`.

## 4. Import Rules

```python
# CORRECT
from candlery.core.candle import Candle
from candlery.core.instrument import Instrument
from candlery.data.calendar import TradingCalendar
from candlery.data.importers.bhavcopy import BhavcopyImporter

# WRONG — never use these
from src.core.candle import Candle        # ← old path, removed
from core.candle import Candle            # ← relative, broken
import candlery.core.candle as candle     # ← import the class, not module
```

## 5. Execution Rules

| Rule | Detail |
|---|---|
| **Timestamps** | Always `datetime` with `tzinfo` set. Always UTC. |
| **Data models** | Frozen dataclasses in `candlery/core/`. Immutable. |
| **Config** | YAML for exchanges/risk/backtest. JSON for holidays. |
| **Tests** | Mirror `candlery/` structure under `tests/`. Use `tmp_path` fixtures. |
| **New directories** | MUST contain `__init__.py`. |
| **No LLM in trading path** | Strategy → Risk → Execution is pure code. |
| **Float for prices** | Accepted in Phase 1. Decimal migration at Phase 2. |
| **Volume** | `int` (shares are whole numbers). |

## 6. TEST INTEGRITY RULE (CRITICAL)

Tests are the source of truth.

If a test fails:

* NEVER modify the test to make it pass
* ALWAYS fix the underlying code

Only exception:

* The test is provably incorrect (must explain clearly before changing)

Default behavior:
FAILURE → FIX CODE, NOT TEST

If unsure:
STOP and ask before modifying tests

## 7. INCIDENT REFERENCE — T-008 Portfolio Bug

A failure occurred where a position was created with quantity = 0 when insufficient cash was available.

Initial instinct was to modify the test, but this was incorrect.

Correct resolution:

* Identified bug in portfolio execution logic
* Fixed code to prevent position creation when trade does not execute
* Re-ran tests successfully

Lesson:
Tests define correctness. Code must conform to tests.

## 8. Validation Steps (Run Before Every Commit)

```bash
cd /Users/charan/Documents/candlery-workspace/candlery

# 1. Import check (replace with whatever you just built)
python3 -c "from candlery.<new_module> import <NewClass>"

# 2. Full test suite
python3 -m pytest tests/ -v

# 3. Verify no source files are gitignored
git check-ignore candlery/**/*.py tests/**/*.py

# 4. Stage and check
git add -A && git status
```

## 9. How to Resume Work

```
Step 1: git pull origin main
Step 2: Read docs/ai-state/CURRENT_STATE.md
Step 3: Read docs/ai-state/TASK_QUEUE.md
Step 4: Pick the first READY task
Step 5: Implement full module + tests
Step 6: Run validation (Section 8)
Step 7: Commit with [T-XXX] prefix
Step 8: Update CURRENT_STATE.md and TASK_QUEUE.md
Step 9: Push
```

## 10. What NOT To Do

| Forbidden Action | Why |
|---|---|
| Create files outside project root | Causes drift, files get lost |
| Use `src.*` imports | Package was renamed to `candlery` |
| Skip `__init__.py` in new directories | Breaks Python package resolution |
| Use `datetime.now()` or system clock | Must be deterministic, UTC-aware |
| Add external API calls to core logic | Phase 1 is offline/local only |
| Reformat files you aren't changing | Creates noise in git diff |
| Assume chat memory persists | Repo is the ONLY memory |
| Use `data/` in .gitignore without `/` prefix | Matches `candlery/data/` and hides source code |
| Install package with `pip install -e .` | Not needed — run from project root with `pythonpath = ["."]` |

## 11. Next Task Pointer

**Read `docs/ai-state/TASK_QUEUE.md` for current task list.**

The queue is the authoritative source. This section is a snapshot that may be stale:

```
NEXT READY:  T-006 — Strategy interface (abstract base class)
THEN:        T-007 — Risk engine
THEN:        T-009 — SMA crossover strategy
```

## 12. Project Structure

```
candlery/                          ← project root
├── candlery/                      ← Python package
│   ├── __init__.py
│   ├── core/
│   │   ├── __init__.py
│   │   ├── instrument.py          ← Instrument dataclass
│   │   └── candle.py              ← Candle dataclass (OHLCV)
│   ├── data/
│   │   ├── __init__.py
│   │   ├── calendar.py            ← TradingCalendar
│   │   └── importers/
│   │       ├── __init__.py
│   │       └── bhavcopy.py        ← NSE Bhavcopy CSV parser
│   ├── strategy/                  ← NEXT: T-006
│   ├── risk/                      ← T-007
│   ├── backtest/                  ← T-008
│   └── journal/                   ← T-010+
├── tests/                         ← mirrors candlery/
├── config/
│   ├── exchanges/nse.yaml
│   ├── holidays/nse_202{4,5,6}.json
│   ├── risk_defaults.yaml
│   └── universes/nifty50.yaml
├── docs/ai-state/                 ← AI continuity files
├── pyproject.toml
├── .gitignore
└── README.md
```

## 13. Commit Message Format

```
[T-XXX] Short title

Details:
- What was built
- What was fixed
- Test count and status
```
