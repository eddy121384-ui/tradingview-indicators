# Issue #76 — Phase B Next Step

The previous next-step note proposed separate FX and rates exposure maps. That is now **superseded** after clarification of the intended product objective.

The intended product is a **general-purpose cross-asset regime indicator**, not an asset-specific ruleset. Therefore the next step is NOT to freeze separate FX/rates policies.

Primary Phase-B work must instead:

- aggregate all accepted markets together after event-time ATR normalization;
- compare every market/regime cell with that market's own unconditional baseline;
- give each market equal weight so long-history markets do not dominate;
- measure cross-market sign agreement and leave-one-market-out stability;
- use asset-class slices only as adversarial diagnostics for heterogeneity, never as policy branches;
- downgrade a state that requires asset-specific rescue rather than adding market-specific parameters.

The target output is a universal exposure tilt in chart-variable direction, for example increase positive-direction exposure / reduce positive exposure / neutral / increase negative-direction exposure. Instrument-specific execution translation, such as yield direction to duration, happens downstream and is not a classifier branch.

Do not freeze executable sizing yet. First complete the universal all-market Regime-Conditioned Exposure Map across the already frozen 1/5/10/20-bar horizons and regime-age buckets.

No classifier thresholds, stops, targets, bespoke horizons, market exclusions, asset-specific parameters, or production Pine semantics may be changed in this step.
