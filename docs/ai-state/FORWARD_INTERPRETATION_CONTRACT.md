# FORWARD INTERPRETATION CONTRACT (binding pre-commitment)

> **STATUS: INVALID — 2026-05-06.**
>
> The §5 "perfect rank separation" discrimination test is **statistically
> vacuous at N=3 windows**. Under the null hypothesis that pass/fail labels
> are independent of the chosen context features, perfect rank separation
> with one odd-class window occurs ~2/3 of the time by chance. The
> discrimination test cannot distinguish signal from noise.
>
> No verdict ("Conditional candidate", "Archive", "Insufficient evidence")
> may be drawn from any window run under this contract. Any prior text
> below is preserved as a record of how the protocol was constructed and
> how the error was missed at construction time.
>
> Replacement structure: see
> `docs/ai-state/CANARY_NOTE.md` (operational plumbing, no strategy
> verdicts) and `docs/ai-state/SIGNAL_DISCOVERY_NOTE.md` (signal
> evaluation with real power calculations).
>
> The W1 pre-window context record at
> `reports/forward_context/2026-05-04.json` remains valid as a timestamped
> record that this contract existed and was honored up to the moment of
> invalidation. It is not strategic evidence.

---

## Original body (preserved as historical record only)

Status: ACTIVE
Created: 2026-05-05
Authority: locked at creation. No mid-run amendment. Any change voids the run.

This contract governs how forward paper-run windows are *interpreted*. It does
not change strategy, parameters, or system behavior.

## 1. Scope

- Strategy: `sma_crossover`, fast=2, slow=4. Frozen.
- Universe: `nse50_liquid_auto`. Frozen.
- Initial capital: 500,000. Frozen.
- Risk profile: `risk` (current default). Frozen.
- `close_all_at_end: true`. Frozen.
- Window length: 20 trading days. Forced flat at end of each window.
- Number of forward windows: **N = 3** (W1, W2, W3), non-overlapping, consecutive.

## 2. Window timing

- W1 starts on the first NSE trading day strictly after `2026-05-04` for which
  bhavcopy data is fetched and normalized.
- W2 starts on the next trading day after W1 ends.
- W3 starts on the next trading day after W2 ends.
- Windows are defined by **trading-day count**, not calendar dates.

## 3. Per-window result label (frozen)

A window is labeled `pass` iff **all** of:
- total return > 0
- win rate >= 40%
- total trades >= 10

Otherwise: `fail`. No alternative thresholds. No tie-breakers.

## 4. Pre-window context features (frozen)

For each window Wk, compute the following three features **before** Wk begins,
using bhavcopy data through and including the last trading day before Wk
(the "asof" date). Universe-wide aggregates over the 50 symbols, EQ series only,
20 trading days.

- `univ_median_20d_return`
  - For each symbol: `close[asof] / close[asof - 20] - 1`
  - Take median across symbols.
- `univ_median_20d_vol`
  - For each symbol: `stdev(daily log returns over last 20 days) * sqrt(252)`
  - Take median across symbols.
- `univ_breadth_pos_20d`
  - For each symbol: indicator that 20d return > 0
  - Take mean across symbols (fraction in [0,1]).

Output: `reports/forward_context/<asof>.json` with the three numbers, the
asof date, the universe name, and the symbol count actually used.

These three features are the **complete** pre-window context set for this
contract. No additional features may be added during the run.

## 5. Decision rule (frozen, post-W3)

After W3 completes, label W1, W2, W3 as `pass` or `fail` per Section 3.

Discrimination test for each context feature `f`:
- Sort windows by `f`.
- A feature `f` "discriminates" iff the sorted order produces **perfect rank
  separation** between pass and fail labels (all passes contiguous on one
  side, all fails on the other), AND there is at least one window in each
  class.

Promotion verdict:

- **Conditional candidate** (signal usable under a regime cue):
  - Pass count in {1, 2}, AND
  - At least one feature discriminates per the test above.

- **Archive (forward-blind random)**:
  - Pass count in {1, 2}, AND
  - No feature discriminates.

- **Insufficient evidence (extend)**:
  - Pass count in {0, 3} (no separation possible regardless of features).
  - In this case the contract permits **one** extension: run a fourth window
    W4 under identical rules and re-evaluate over W1..W4 with the same test.
    Beyond W4: archive.

- **No other verdict is permitted by this contract.**

## 6. Anti-cheat clauses

- No re-running of any window. The first run of Wk is the result.
- No reordering of windows.
- No swapping of universe, capital, params, risk profile, or thresholds.
- No retrospective re-labeling of a completed window.
- No introduction of additional context features after W1 begins.
- If any of the above is violated, the run is voided and recorded as such.

## 7. What is explicitly NOT decided by this contract

- Whether the strategy is "good".
- Whether to deploy to live capital.
- Sizing, broker selection, capital allocation.

A "conditional candidate" verdict only justifies designing a *next* protocol
(promotion-to-live), not live deployment.

## 8. Self-binding

If this contract leads to "Archive", the SMA-crossover line is closed.
The next decision is *what new signal source to evaluate*, not *what to tweak
on SMA*.

If this contract leads to "Conditional candidate", the discriminating feature
becomes a forward-visible regime gate to be tested, in a separate contract,
on a separate set of windows. It is not retrofitted into this run.
