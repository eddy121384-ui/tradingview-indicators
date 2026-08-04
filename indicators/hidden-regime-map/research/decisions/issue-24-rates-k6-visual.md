# Issue #24 — U.S. Rates K=6 visual prototype status

**Status:** generated assets committed; waiting for TradingView compilation and feed-parity validation.

The first human-visible Hidden Regime prototype now observes the U.S. Treasury constant-maturity curve rather than SPY. K=6 is fixed for human inspection and is not presented as a uniquely selected or profitable state count.

The implementation is stacked on PR #52 so it reuses the same checksum-verifiable rates input and the same five economically interpretable curve features. It fits a full-sample descriptive K=6 reference through the frozen July 2026 cutoff, selects one actual fitted medoid model from three deterministic restart groups, and generates Pine from the versioned JSON profile.

Historical colors from this profile are retrospective in-sample descriptions. They are not historical out-of-sample evidence.

## Generated profile

- profile: `us-rates-k6-visual-v0.1`;
- frozen decompressed input SHA-256: `f85a37d574f58ed927c1b490f14d0057a2f1c295c7061cf2a5d08b433995c104`;
- feature period: 2007-02-01 through 2026-07-30;
- feature rows: 4,868;
- representative actual fitted seed: 43;
- full-sample state occupancy: 11.24% / 16.50% / 13.43% / 26.15% / 14.73% / 17.95%.

All six states have material full-sample occupancy. The model is therefore not globally reduced to one or two ghost states.

## Important current diagnostic

The latest feature vector is not beyond the prototype drift threshold: its maximum absolute standardized feature value is approximately `1.775`, below the warning level of `3.0`.

However, the latest 126 valid observations are effectively **100% concentrated in one dominant state**, above the prototype warning level of 90%. This is exactly the static-model concentration failure mode the visual product was designed to expose. It is not hidden or interpreted as strong forecasting confidence.

## Validation

Hidden Regime Rates K6 Visual Run #6 (`30891597699`) completed successfully on the committed generated assets.

- six focused exporter/generator tests passed;
- the frozen K=6 profile regenerated successfully;
- the 12-checkpoint fixture regenerated successfully;
- the Pine v6 source regenerated successfully;
- committed JSON content matched regenerated JSON content;
- committed Markdown and Pine matched regenerated output byte-for-byte;
- workflow artifact upload passed.

## Remaining gates

- resolve and land the stacked PR #52 dependency, then retarget PR #54 to `main`;
- compile the generated Pine script in TradingView on the declared daily FRED rates chart;
- export TradingView values and compare them with the 12 Python/FRED checkpoints;
- complete Eddy's visual review.

No trading-utility, profitability, historical-OOS, or unique-K claim is made.
