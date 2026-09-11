# Issue #76 — Phase B Next Step

The previous next-step note first proposed separate FX/rates exposure maps; that was superseded by the universal cross-asset objective. A second clarification now changes the ordering again: **before freezing any exposure policy, study regime persistence and lifecycle.**

The intended product is a general-purpose, medium/long-horizon regime indicator, not a short-term entry signal. A fixed 10-bar forward return is therefore only one diagnostic and must not become the organizing unit of the research.

Primary next work:

- reconstruct every contiguous formal-regime spell from the accepted nine-market daily logs;
- measure how long each regime survives rather than only what happens 10 bars after entry;
- estimate cross-market equal-weight survival probabilities after 5 / 10 / 20 / 40 / 60 / 120 trading bars;
- report median spell duration and short-lived/churn rates;
- estimate age-conditional persistence: given that a regime has already survived N bars, how likely is it to survive another 5 / 10 / 20 / 40 bars?;
- report exit/transition destinations, including exits to unclassified/no-formal-stage periods;
- treat asset-class slices only as heterogeneity diagnostics, never as policy branches;
- only after persistence is understood, combine persistence with baseline-relative forward distributions to derive a universal exposure posture.

The decision unit for the eventual product should be the **current state and its age**, re-evaluated as the state evolves, not `enter now and hold for 10 bars`.

For longer-horizon analysis, 20 bars is approximately one trading month, 60 bars approximately one quarter, and 120 bars approximately half a year. These are descriptive lifecycle landmarks, not optimized holding periods.

Do not change classifier thresholds, add asset-specific parameters, or optimize a trading policy while doing this lifecycle study.
