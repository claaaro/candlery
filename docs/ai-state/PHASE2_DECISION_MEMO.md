# Phase 2 Decision Memo

## Purpose

After Phase 1 strict-gate validation, no SMA-family or volatility-breakout strategy passed, and a cross-sectional momentum research probe falsified that hypothesis class as well.

Before writing more strategy code, we must choose Phase 2 direction deliberately.

This memo compares the two remaining serious directions and recommends one.

---

## Current State Snapshot

- Backtest engine: complete, cost-aware, gate-validated.
- Reporting: HTML and CSV outputs functional.
- Validation gate: enforced (multi-fold, min sells per fold, PF/expectancy rules).
- Strategy classes tested and rejected:
  - SMA crossover families
  - SMA + entry filters (trend, ATR, cooldown)
  - SMA + ATR trailing-stop exit
  - Volatility-contraction breakout (single-name)
  - Cross-sectional momentum (long-short, monthly rebalance)
- Conclusion documented in `VALIDATION_GATE_REPORT.md`.

---

## Direction A — Event-Driven Hypothesis Class

### Examples

- Post-earnings announcement drift (PEAD)
- Gap continuation / gap reversal
- Volatility shock follow-through
- Index inclusion/exclusion effect (out of scope without survivorship-clean data)

### Edge rationale

Event-driven edges are some of the most empirically supported in equities because they exploit known information-processing inefficiencies, not just price patterns.

### Engineering cost

- Requires additional data:
  - Earnings calendar
  - Corporate actions
  - Possibly intraday open prices for gap behavior
- New parsers, new universe alignment logic, new feature engineering steps.
- Risk control and execution timing become tighter (event windows are narrow).

### Risk profile

- Pros: real edge density is higher than indicator-based price logic.
- Cons: higher data dependency; small-window-sensitive; needs careful cost/slippage modeling.
- Validation: strict gate still applies, but trade counts per fold may be smaller and noisier.

---

## Direction B — Research Instrumentation Investment

### What this means

Build tools that improve the speed and quality of all future hypothesis testing, before testing more hypotheses. Examples:

- Regime classifier (trend vs range vs high-vol)
- Volatility cohort segmentation
- Factor explorer (returns by characteristic)
- Cross-sectional dispersion and correlation diagnostics
- Trade attribution dashboards (what type of market regime won/lost trades)

### Edge rationale

Better instruments create better questions, which improves the probability of finding real edge per unit research time. This is meta-leverage rather than direct alpha.

### Engineering cost

- All work is on existing data we already have.
- No new external data dependencies.
- Each module is small and shippable independently.

### Risk profile

- Pros: low data risk, low overfitting risk, durable value to all future research.
- Cons: no near-term strategy outcome; success measured indirectly.

---

## Comparison Matrix

| Dimension | Event-Driven (A) | Research Instrumentation (B) |
|---|---|---|
| Probability of finding edge | Medium-High | Indirect (enables future edge) |
| Data requirements | High (new data needed) | Low (existing data suffices) |
| Engineering cost | Medium-High | Low-Medium |
| Risk of overfitting | Medium-High | Low |
| Time to first measurable result | Medium | Short |
| Reusability | Strategy-specific | Cross-strategy leverage |
| Fits Candlery’s current capability | Partial | Full |

---

## Recommendation

**Direction B first, then A.**

### Why B is the right next step

1. **Lowest waste path.**  
   Phase 1 already showed that randomly testing single-name signals is expensive and low-yield. Better instruments will prevent repeating that pattern.
2. **No new data needed.**  
   We already have a clean cost-aware engine and 2 years of NSE bhavcopy data; instrumentation can be built immediately without acquisition risk.
3. **Strict gate becomes more useful.**  
   Regime classification will let us see whether failures were universal or regime-specific — this is direct information we lack today.
4. **Cross-sectional probe results show we don’t yet understand market structure** of our universe well enough to bet on event-driven complexity. Doing A before B is high risk.
5. **Direction A is not blocked**, just sequenced. After B, when we attempt event-driven, we will have proper diagnostics, lower iteration cost, and better falsification quality.

---

## Minimal First Action of Direction B (no implementation now)

A single research module, not a strategy:

- **Regime tagger**:
  - Classify each trading day per symbol or per universe into one of:
    - Trend up / Trend down / Range
    - High vol / Normal vol / Low vol
  - Tag is computed from existing price history only (no extra data).
- **Output**: a CSV/HTML diagnostic report of regime distribution over the 2024–2025 sample.

If this is approved, we then ask: do prior strategies fail uniformly across all regimes, or only specific ones? That single question is more valuable than building any new strategy now.

---

## Decision Required

- Approve Direction B (research instrumentation) as Phase 2 starting point.  
- Defer Direction A (event-driven) to Phase 3 once instrumentation exists.  
- Or override and choose differently.
