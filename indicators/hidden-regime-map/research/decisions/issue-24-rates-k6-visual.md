# Issue #24 — U.S. Rates K=6 visual prototype status

**Status:** implementation started; waiting for deterministic CI generation.

The first human-visible Hidden Regime prototype now observes the U.S. Treasury constant-maturity curve rather than SPY. K=6 is fixed for human inspection and is not presented as a uniquely selected or profitable state count.

The implementation is stacked on PR #52 so it reuses the same checksum-verifiable rates input and the same five economically interpretable curve features. It fits a full-sample descriptive K=6 reference through the frozen July 2026 cutoff, selects one actual fitted medoid model from three deterministic restart groups, and generates Pine from the versioned JSON profile.

Historical colors from this profile are retrospective in-sample descriptions. They are not historical out-of-sample evidence. The profile and Pine dashboard expose feature-space drift and rolling state concentration because Issue #50 demonstrated that static rates HMMs can collapse under structural distribution shift.

Completed source components:

- v0.4 rates visual specification;
- deterministic K=6 profile exporter;
- deterministic Pine v6 generator;
- focused exporter and generator tests;
- dedicated CI workflow.

Remaining gates:

- generate and inspect the frozen profile/Pine artifact in CI;
- commit the generated assets and prove regeneration is byte-stable;
- compile in TradingView on the declared daily FRED rates chart;
- compare Pine/FRED outputs with Python checkpoints;
- complete Eddy's visual review.
