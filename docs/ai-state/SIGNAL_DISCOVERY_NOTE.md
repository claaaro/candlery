# SIGNAL DISCOVERY — registration template

Status: NO CANDIDATE REGISTERED.
Created: 2026-05-06.

## Purpose

Track real signal-evaluation work. Output of this track is what closes
gap row R10 (signal source under forward observation).

This is NOT a contract. It is a registration template. Each candidate
gets one file under `reports/signal_discovery/<short-name>/REGISTRATION.md`.

## Registration template (mandatory before any run)

A candidate is "registered" only when ALL of the following are filled in
*before* any data is touched. Skipping any field rejects the candidate.

```
# Candidate: <short-name>

1. Hypothesis (3 sentences max)
   - <plain-English statement of the inefficiency>
   - <expected sign and rough magnitude>
   - <where in the cross-section / time-series it should appear>

2. Literature reference
   - <citation>
   - <market(s) and period(s) studied>
   - Relevance to NSE largecap daily: <plain-English>

3. Cargo-cult check (all four required, no waving)
   - DECAY: has this anomaly weakened since publication? source?
   - POST-COST REALISM: survives Indian retail-broker costs at our
     universe and sizing? approximate cost per round-trip used.
   - REGIME VALIDITY: is the regime that produced the anomaly similar to
     current Indian equity regime? what differs?
   - CROWDING: rough qualitative answer — how much capital is already
     deployed against this anomaly globally / in India?

4. Power calculation
   - Expected effect size (mean monthly return, annualized Sharpe, hit rate)
   - Sample size n (windows or trades) needed to reject null at alpha=0.05
     with power=0.8
   - Time-cost in trading days to obtain that n
   - If power requires more than 3 months of forward observation, re-design
     the test before running anything

5. Pre-registered rejection threshold
   - Numeric, not narrative
   - Stated as "if observed metric < X, kill candidate"

6. Time-box for first analysis
   - Hours, not weeks
   - When this hour count is exceeded without a kill/keep decision,
     candidate is rejected as "indecisive — not actionable"
```

## Strict rules

1. **No literature-only legitimacy.** A citation alone does not justify
   forward time. The cargo-cult check must be answered concretely.
2. **No vacuous tests.** The N=3 perfect-rank-separation error in
   `FORWARD_INTERPRETATION_CONTRACT.md` is the canonical example of what
   this section forbids. Power calculations must use real statistics, not
   intuition.
3. **One candidate at a time.** Until a candidate is killed or kept,
   no second registration is opened.
4. **Kill is the default outcome.** Most candidates fail. A "keep"
   decision must be defended against the same cargo-cult check.

## Audit rule (binding on AI and operator)

Any strategy/signal claim made in conversation or in code commits must
inline the path to the supporting artifact under
`reports/signal_discovery/`. No path = no claim. This is self-enforcing —
the absence of a path is itself the violation signal.

Claims based on `reports/canary/...` outputs are forbidden. Canary is
plumbing, not evidence.
