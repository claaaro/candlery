# Validation Gate Report (Phase 1 Closeout)

## Scope

This report summarizes Phase 1 strategy validation under the strict promotion gate:

- Cost-aware backtests (STT + brokerage enabled)
- Multi-fold out-of-sample checks
- Minimum trade-count validity filter
- Holdout confirmation on unseen windows

## Gate Rules

A fold is considered valid only if:

- Sell trades >= 10

A strategy passes a valid fold only if:

- Profit Factor > 1.1
- Expectancy > 0

## What Was Tested

- Baseline SMA crossover families (`10/30`, `14/38`, `20/50`)
- Entry filters:
  - trend strength filter
  - ATR volatility filter
  - cooldown logic
- Exit upgrades:
  - ATR trailing-stop variants
- Parameter sweep + out-of-sample confirmation for best candidate

## Results

- Baseline SMA families: failed strict gate.
- Entry filter variants: failed strict gate.
- Exit upgrade sweep found a temporary winner (`14/38` + trailing stop `lookback=40`, `atr_mult=1.5`) in one evaluation set.
- Fresh unseen confirmation windows invalidated that winner (0/3 valid-fold passes).

## Final Decision

- **Live trading:** NO-GO
- **Paper trading for edge validation:** NO-GO
- **Paper mode for infrastructure smoke only:** allowed

## Root Conclusion

No robust statistical edge was found in the SMA-centric design space under realistic costs and strict out-of-sample criteria.

This is a successful risk-control outcome: the validation gate prevented promotion of unstable or regime-fit strategies.

## Recommended Next Phase Direction

Shift from SMA-family tweaks to a different hypothesis class:

- Volatility-contraction breakout with participation confirmation (volume)
- Same strict gate, unchanged acceptance rules
- Minimal baseline implementation first, no broad parameter sweep initially
