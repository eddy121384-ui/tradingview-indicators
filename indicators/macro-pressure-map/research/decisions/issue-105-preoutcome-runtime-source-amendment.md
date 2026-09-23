# Issue #105 — Pre-outcome runtime source amendment

Status: **ENGINEERING TRANSPORT AMENDMENT — BEFORE ANY #105 OUTCOME WAS VIEWED**

## Trigger

The preregistered Pine harness failed at runtime on the user's TradingView account with:

`Permission denied for symbol: ECONOMICS:USCPCEPI`

No #105 policy-validation result, correlation, accuracy, confusion matrix, or pivot outcome was observed before this amendment.

## Frozen conceptual variable

The intended variable remains unchanged:

- concept: U.S. Core PCE Price Index level;
- source concept: U.S. Bureau of Economic Analysis;
- transformation: `100 * (level / level[12] - 1)`;
- frequency: monthly;
- all downstream BCI-10 formulas, weights, thresholds, lags, and outcomes remain unchanged.

## Transport substitution

Original TradingView economic transport:

`request.economic("US", "CPCEPI")`

Runtime replacement:

`request.security("FRED:PCEPILFE", "M", close)`

`PCEPILFE` is the FRED series "Personal Consumption Expenditures Excluding Food and Energy (Chain-Type Price Index)", sourced from the U.S. Bureau of Economic Analysis, monthly, index 2017=100.

This is a transport/source-access amendment for the same Core PCE index construct, not a model repair or result-driven feature change.

## Research boundary

Do not change:
- PMI source definitions;
- CPI definitions;
- 120-month z-score;
- BCI-10 weights;
- R sign repair;
- PS formula;
- ±0.3 / ±1 thresholds;
- two-month information lag;
- 6M primary EFFR outcome;
- sample freeze through 2025-12 realized outcomes.

If `FRED:PCEPILFE` is also unavailable in the user's TradingView runtime, stop and record a second access blocker rather than substituting another series after seeing outcomes.
