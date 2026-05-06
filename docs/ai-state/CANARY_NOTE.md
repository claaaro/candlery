# CANARY — operational plumbing only

Status: defined, NOT started.
Created: 2026-05-06.

## Purpose

Detect alpha-independent operational decay (NSE format drift, holiday/calendar
edges, journal corner cases over real wall-clock time, fetcher auth/URL
failures, scheduler drift, file-system edges).

The canary is **plumbing**. It is not a strategy under evaluation.

## What it runs

The existing daily pipeline:

```
fetch_bhavcopy.py <date>
normalize_udiff_cm_to_legacy.py <date>
candlery paper  (one rolling config on SMA crossover, frozen params)
```

Outputs go under `reports/canary/<date>/`. SMA is fungible plumbing — used
because it produces some trades reliably. It is **not** the signal candidate.

## Hard rules (binding)

1. **No strategy claims.** Any claim about edge, regime, profit, or signal
   quality based on canary output is a contract violation. The AI must
   inline the path to a `reports/signal_discovery/...` artifact next to any
   strategy claim. No path = no claim. (See AUDIT RULE.)

2. **Re-approval every 10 trading days.** Default = STOP. Continuation
   requires BOTH of the following in the same period:

   a. **Concrete operational evidence**, one of:
      - a path to a log/file/error with timestamp, OR
      - a measurable claim with concrete numbers and baseline
        (e.g. "fetch latency 4.2s vs baseline 1.1s on 2026-05-12").

      Free-form narrative ("I think holiday handling was tested") does NOT
      count.

   b. **Active signal-research evidence**, one of:
      - a fresh pre-registered hypothesis under
        `reports/signal_discovery/` (with power calc + cargo-cult check), OR
      - a fresh kill/keep decision on a prior candidate.

      An empty `reports/signal_discovery/` directory automatically fails
      this requirement.

   If either (a) or (b) is missing, canary auto-stops on day 11.

3. **Retention cap: 30 days.** Canary outputs older than 30 days are
   deleted. No sunk-cost narrative possible.

4. **Hard ceiling: 60 trading days total.** After 60 days the canary cannot
   be re-approved without explicit operator-led redesign of this note. Not
   a soft target — a stop.

5. **No alpha decisions ever.** Even a "successful" 60-day canary run
   contributes zero evidence about strategy promotion. It only retires the
   operational-entropy uncertainty.

## Anti-Risk-#5 caveat (governance becoming identity)

The largest residual risk is that anti-drift mechanisms (this note, the
discovery note, the audit rule) become the emotionally rewarding work and
displace the actual goal (find alpha, trade real markets).

The structural fix is rule 2(b) above: canary auto-dies if no signal-research
artifact appears in a 10-day period. Governance without research collapses
on itself within ~2 weeks. There is no separate governance-meta-review.

Adding more meta-rules to govern this risk would BE this risk. Resist.

## How to start

Operator types: "start canary".
On that day:
- Write `reports/canary/STARTED_<date>.txt` with: start date, day-1 trading
  date, expected first re-approval date (start + 10 trading days).
- Begin daily fetch+normalize+paper loop manually or via scheduler.

## How to stop

Any of:
- Day-11 re-approval missing either (a) or (b) above.
- Operator types: "stop canary".
- 60-trading-day hard ceiling reached.

On stop, canary outputs may be retained for 30 more days, then deleted.
