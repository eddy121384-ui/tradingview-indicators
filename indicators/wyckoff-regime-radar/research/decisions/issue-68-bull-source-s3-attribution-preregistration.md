# Issue #68 — FR10Y vs DE10Y Bull-source / S3 attribution preregistration

Status: discovery-only attribution. Production C-2 remains frozen.

## Trigger

The 2022-01-03 through 2023-12-29 FR10Y and DE10Y path-geometry audit found nearly indistinguishable raw market geometry: equal average absolute 1D move, equal 20D signed move, equal 20D positive share, equal 20D/60D efficiency, equal 20D move/ATR, and only trivial direction-flip differences. Yet DE10Y has materially higher Bull TOP occupancy / average TOP gap / gap-pass share than FR10Y. At the same time, FR10Y has stronger S2 Markup drivers than DE10Y. Therefore the remaining divergence must be localized inside stage competition rather than explained by simple path amplitude or choppiness.

## Primary question

Does DE10Y obtain its Bull TOP advantage primarily through S3 Reaccumulation rather than S2 Markup, and if so, which frozen S3 input or gate creates that rescue that FR10Y does not receive?

## Frozen comparison

- Window: 2022-01-03 through 2023-12-29 inclusive.
- Charts: FR10Y 1D and DE10Y 1D first.
- Expected semantic family: Bull yield regime.
- Frozen C-2 calculations and all production thresholds.
- No PnL, no threshold search, no weight change, no confirmBars change, no TOP-gap change.

## Measurements

1. Final TOP source shares for S2 and S3 separately.
2. Which Bull sibling leads inside the Bull family (`p2` vs `p3`) independent of whether Bull wins globally.
3. S2-TOP vs S3-TOP average gap and gap-pass share.
4. Non-Bull final TOP winner shares for S1/S4/S5/S6.
5. Average `best Bull probability - best non-Bull probability`.
6. Frozen S3 engine attribution: `bullBg`, `rangeScore`, `supportHolding`, `100-panicHeatDn`, `100-upsideExhaustion`, `reaccRaw`, `reaccGate`, `reaccEff`, and final `p3`.

## Preregistered interpretation

- **S3-rescue supported:** DE Bull TOP advantage is primarily S3, while FR lacks comparable S3 occupancy; continue by localizing the largest DE-vs-FR divergence among S3 raw inputs / gate / effective score.
- **S2/S3 mix similar:** reject S3-rescue as primary explanation; localize the divergence to the non-Bull rival that most often wins globally or compresses Bull margin.
- **S3 raw similar but gate/effective diverges:** treat the S3 gate stack / normalization as the primary architecture suspect.
- **S3 raw itself diverges:** treat the largest frozen S3 input divergence as the next attribution target.
- **No material source divergence:** return to probability normalization / ranking transformation rather than altering stage formulas.

## Repair rule

No production repair is authorized by this audit alone. A repair may be proposed only after a specific mechanism explains the FR-vs-DE semantic split and can be expressed as a causal counterfactual. Any repair must then be tested on FR/DE plus JP/GB/US controls before merge consideration.
