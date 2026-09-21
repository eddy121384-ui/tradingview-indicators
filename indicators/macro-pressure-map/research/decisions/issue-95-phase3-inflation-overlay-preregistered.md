# Issue #95 Phase 3 preregistration — absolute-inflation allocation overlay

Phase 2 concluded that the Growth × Inflation state→asset mapping is **inflation-regime dependent**, with the cleanest repeated effect in Treasury versus cash when absolute CPI inflation is >=4%.

Phase 3 asks one narrower question:

> Does that structural interaction create allocation-layer value when the existing #89 3×3 policy is left unchanged and only the Treasury sleeve is conditionally redirected toward cash?

## Frozen primary overlay

The base #89 Equity/Treasury/Gold matrix is unchanged.

When the lagged HMRA state-year December-to-December CPI inflation is **>=4%**, redirect **50% of the selected Treasury sleeve** to 3-month T-bills.

No other weight changes.

The 25% and 75% redirect variants are diagnostic sensitivities only. They may not become primary because they look better.

## Timing

Use the already frozen conservative mapping:

`HMRA state_t -> full-calendar-year return_t+2`

The inflation activation variable is also the state-year t CPI inflation. Return-year inflation may not be used.

Primary policy returns are 1975–2025, corresponding to state years 1973–2023.

## Why this design?

Phase 2 did not support a generic “1970s template” for all assets. It supported a narrower finding: high absolute inflation changed the payoff of duration versus cash in both Reflation and Stagflation.

The Phase 3 rule therefore changes only Treasury versus cash. It does not touch Equity or Gold, does not modify HMRA, and does not add a third state axis.

## The most important control

The primary overlay must be compared with a **realized-exposure-matched static four-asset portfolio**.

If the overlay works only because it holds more cash on average, that is allocation-mix value.

Only overlay value that survives versus the matched static control can be called regime-switching/timing value.

## Historical robustness

The result must be reported separately for:

- 1975–1984;
- 1985–1999;
- 2000–2007;
- 2008–2019;
- 2020–2025.

A result that exists only in 2020–2025 is explicitly classified as `recent_era_rescue_only`.

Leave-one-era-out and largest-positive-active-episode leaveout rerun the full strategy and matched control; simple subtraction is forbidden.

## Verdicts

Exactly one:

- `robust_inflation_conditioned_switching_value`
- `historical_risk_management_value_only`
- `recent_era_rescue_only`
- `allocation_mix_only_no_switching_value`
- `no_material_overlay_value`
- `inconclusive_insufficient_evidence`

None authorizes a production V6.6 or allocator change.
