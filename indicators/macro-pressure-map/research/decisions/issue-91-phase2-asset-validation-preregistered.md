# Issue #91 Phase 2 preregistration — long-history state → asset payoff

Phase 2 opens the asset-outcome envelope **only after this file is committed**.

## Evidence order

1. Same-year structural association: `HMRA state_t ↔ return_t`.
2. Cross-era sign / leader stability.
3. Same HMRA cell under absolute CPI inflation below 4% versus >=4%.
4. Leave-one-era-out concentration.
5. Strict causal information test: `state_t → return_{t+2}`.
6. Independent JST equity/bond cross-check.

Portfolio-policy performance is explicitly out of scope until a later phase.

## Primary asset outcome source

Damodaran's frozen 1928–2025 annual U.S. return table, using only the first annual-return columns:

- S&P 500 total return including dividends;
- 3-month T-bill;
- 10-year U.S. Treasury total return;
- Gold.

No ETF data is permitted.

JST R6 is an independent equity/bond cross-check. It is not an alternate source that can be selected when the primary result is inconvenient.

## Core questions

The main object is not CAGR. It is the sign and stability of:

- Equity − Treasury
- Treasury − T-bill
- Equity − Gold
- Treasury − Gold

within the same HMRA cell across predeclared historical eras.

A central diagnostic is whether the same HMRA cell changes payoff when absolute December-to-December CPI inflation is below 4% versus >=4%.

## Gold interpretation

Gold is visible across the long history, but:

- 1928–1970: monetary-history context only;
- 1971–1974: floating-price transition context;
- 1975+: primary investable-gold structural window.

Phase 2 may show all-year gold spreads with these labels, but pre-1975 observations cannot support modern investable-gold allocation claims.

## Statistics

For each asset/spread: n, mean, median, sample standard deviation, positive fraction and a 10,000-resample percentile bootstrap 95% CI of the mean. Asset returns additionally get a geometric mean where mathematically valid.

Minimum sample interpretation:

- n<3: insufficient;
- 3–4: very sparse;
- 5–9: sparse;
- >=10: regular.

No composite ranking and no parameter selection from p-values.

## Causal timing

Same-year results are descriptive only.

The forward test uses the already frozen conservative mapping:

> state_t → full-calendar-year return_{t+2}

This is an information-timing-safe predictive association, not proof of structural causality.

## Verdict discipline

The Phase 2 structural verdict must be exactly one of:

- `structurally_stable_mapping`
- `inflation_regime_dependent_mapping`
- `monetary_regime_dependent_mapping`
- `asset_mapping_unstable`
- `inconclusive_long_history_evidence`

The verdict is structural only. Portfolio/allocation-policy verdicts belong to a later phase.
