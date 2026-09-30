# Macro Pressure Map V6.7 — Reflation Action Layer Shadow Mode

Status: implementation candidate for Issue #129  
Production visibility: **disabled / shadow only**  
Upstream production model: frozen V6.6

## Purpose

V6.7 introduces the smallest productization layer justified by the completed research stack. It does not retune V6.6 and it does not add another research model.

The only implemented Action Layer candidate is:

> Exact V6.6 Regime 3 — Reflation / Inflation Rising  
> Equity +1 / Duration -1  
> Research translation: Equity +5pp / Duration -5pp

Cash and Inflation Hedge remain neutral.

All other V6.6 regimes return a neutral Action Layer vector.

## Frozen trigger

The trigger is exactly the existing V6.6 3x3 state condition:

```text
growthPositive AND inflationPositive
```

where V6.6 defines:

```text
growthPositive = GPI > growthThreshold
inflationPositive = IPI > inflationThreshold
```

No HMRA proxy, alternate threshold, trajectory feature, FCPI modifier, or additional macro variable is allowed to trigger the production shadow signal.

## Shadow contract

The V6.7 Pine source keeps the Action Layer disabled from normal user-facing behavior:

```text
shadowActionLayerEnabled = false
```

The internal vector is:

```text
Regime 3:
  Equity          +1
  Duration        -1
  Cash             0
  Inflation Hedge  0

All other regimes:
  Equity           0
  Duration         0
  Cash             0
  Inflation Hedge  0
```

The associated research translation is fixed at +5 percentage points Equity and -5 percentage points Duration. This is documentation of the tested model translation, not a user-specific allocation recommendation.

## Evidence lineage

Issue #121 revived one long-history relationship:

`Reflation / Inflation Rising -> Equity > Treasury`

Issue #123 translated that relationship into a frozen 5pp Equity/Duration transfer and passed its long-history portfolio gate.

Issue #125 tested the HMRA-to-exact-V6.6 bridge. The preregistered bridge gate was **9/10**, not 10/10. Regime 3 specificity was strong, but the Growth-high confidence interval narrowly crossed zero. This issue must not describe #125 as a full bridge pass.

Issue #127 then tested the exact V6.6 Regime-3 5pp transfer in the modern sample and passed all **11/11** frozen translation gates. Its formal verdict was:

`exact_v66_reflation_translation_candidate`

The research result did not itself authorize user-facing production enablement.

## Non-guarantee boundary

Historical evidence does not guarantee future performance.

The Action Layer is a research-derived tactical model state, not an instruction to buy equities or sell bonds. It must not be described as guaranteed alpha, a proven trade, or an optimal allocation.

## V6.6 preservation rule

`src/macro-pressure-map-v6.6.pine` remains frozen.

`src/macro-pressure-map-v6.7.pine` is intentionally constructed as V6.6 plus only:

1. a V6.7 indicator header; and
2. the Issue #129 shadow Action Layer block.

The automated contract test removes those two allowed deltas and requires the resulting file to match V6.6 exactly.

## Explicitly out of scope

Do not add:

- Gold > Cash;
- Duration > Cash;
- broad commodities;
- trajectory;
- FCPI sizing;
- +2 / -2 intensity;
- leverage or options;
- optimized transfer sizes;
- alternate regime thresholds;
- user-facing Action Layer UI;
- Action Layer alerts.

Any promotion from shadow mode to informational display or visible model tilt requires a separate explicit product decision.

## Research PR boundary

Research PRs #118, #122, #124, #126, and especially #128 remain separate from this production implementation.

PR #128 must remain Draft / Open / Unmerged unless the user explicitly authorizes otherwise.
