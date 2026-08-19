# Macro Pressure Map V6.6 Research

This folder implements Issue #59: validation of the frozen Macro Pressure Map V6.6 before any V6.7 redesign.

## Final research status

Issue #59 final category:

`descriptive_but_little_incremental_information`

The frozen V6.6 remains useful as an engineering-verified descriptive growth / inflation / financial-stress state map. Issue #59 does not establish robust standalone or joint incremental predictive value beyond simpler / single-axis information.

## Research rule

`macro-pressure-map-v6.6.pine` is the behavioral source of truth. During Issue #59, do not change component definitions, weights, thresholds, lookbacks, smoothing, or regime rules in response to observed historical results.

The Python code here is a research mirror, not a replacement for the TradingView indicator.

## Important V6.6 semantic detail

Dashboard states and Core Regime use **raw unsmoothed** `GPI`, `IPI`, and `FCPI`. The default EMA(5) is only used for displayed plot lines. Do not classify regimes from `plot_GPI`, `plot_IPI`, or `plot_FCPI`.

## Research components

- `v6_6_core.py` — frozen Python calculation mirror.
- `public_data.py` / `build_public_history.py` — optional public Yahoo/FRED approximation layer; public feeds are not TradingView parity evidence.
- `macro-pressure-map-v6.6-parity-sources.pine` and parity comparators — Pine ↔ Python engineering parity.
- `historical_diagnostics.py` — static-state, transition, regime, and horizon diagnostics.
- `incremental_validation.py` — single-axis out-of-component / simple-baseline study with horizon-length event embargoes.
- `joint_holdout_validation.py` — historical filename retained; current semantics are a **post-2019 exploratory reused-era** joint-axis study, not untouched holdout validation.
- `matched_incremental_validation.py` — matched conditional test of whether the second axis adds lift inside a fixed anchor-event universe.

## Reproducibility contract

See `REPRODUCIBILITY.md`.

Machine-generated matched evidence is kept separate from curated research decisions:

- `generated/issue-59-matched-incremental.generated.json`
- `generated/issue-59-matched-incremental.generated.md`

The matched generator refuses to overwrite:

- `decisions/issue-59-matched-incremental.json`
- `decisions/issue-59-matched-incremental.md`

This prevents a rerun from silently replacing the curated synthesis with a structurally different generated report.

The 2020–2026 era is explicitly classified as `exploratory_reused_era_not_untouched_holdout`, because it had already been inspected before the synchronized-transition hypothesis was selected.

## Tests

Core / public-data tests:

```bash
python -m pytest -q test_v6_6_core.py test_public_data.py
```

Review-driven regression tests:

```bash
python -m pytest -q \
  test_incremental_validation.py \
  test_joint_holdout_validation.py \
  test_matched_incremental_validation.py
```

The regression coverage includes:

- Pine-compatible non-`na` rolling semantics;
- weekend / holiday public-data observations preserved before anchor-calendar forward-fill;
- shared event embargoes preventing overlapping forward windows;
- development-tail purge before the post-2019 era;
- generated joint reports preserving the exploratory / reused-era boundary;
- matched inference using one fixed anchor-event universe;
- script-generated matched outputs defaulting outside curated `decisions/` paths;
- refusal to overwrite curated matched decision artifacts.

## Evidence interpretation

Engineering parity is a **PASS**, but it does not imply economic usefulness.

The final research boundary is:

- GPI / IPI / FCPI remain coherent descriptive axes;
- static regime names are descriptive, not deterministic forward calls;
- standalone out-of-component predictive superiority is not demonstrated;
- the post-2019 GPI+IPI Treasury / ZN pattern is exploratory reused-era evidence;
- matched conditional confirmation-lift confidence intervals cross zero, so incremental predictive information from adding the second axis is not demonstrated;
- no production V6.6 parameter should be recalibrated on Issue #59 data.

Any future predictive validation should pre-register the hypothesis and use genuinely unseen observations after the current evidence cutoff.
