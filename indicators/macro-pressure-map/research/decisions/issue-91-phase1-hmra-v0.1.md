# Issue #91 Phase 1 — HMRA-v0.1 preregistration

Historical Macro Regime Analogue v0.1 is the long-history structural classifier for Issue #91. It is **not** V6.6.

## Primary inputs

The primary 1928-present study uses one homogeneous pair of official underlying macro series:

- Federal Reserve G.17 `B50001`: total industrial production, seasonally adjusted, monthly, history beginning in 1919.
- BLS `CUUR0000SA0`: CPI-U, U.S. city average, all items, not seasonally adjusted, history beginning in 1913.

This removes the need to splice a post-2020 GDP bridge into the primary classifier.

## Calendar-year state

For each completed calendar year (t):

- Growth rate = 100 × ln(December IP_t / December IP_{t-1})
- Inflation rate = 100 × ln(December CPI_t / December CPI_{t-1})

The primary score compares each rate with the **five completed years strictly before t**. The current observation is excluded from its own reference distribution.

For each axis:

- level_z = current annual rate versus the prior-five-year mean/std;
- acceleration = current annual rate minus prior-year annual rate;
- acceleration_z = current acceleration versus the prior-five-year acceleration mean/std;
- raw = 0.70 × level_z + 0.30 × acceleration_z;
- score = 100 × tanh(raw / 2).

Scores above +10 are High; below -10 are Low; otherwise Neutral. No occupancy-based threshold tuning is permitted.

A ten-year reference window is frozen as a sensitivity for **state stability only**. It may not be selected after results because it produces better asset outcomes.

## Two different meanings of time alignment

Same-year HMRA state (t) versus same-year asset return (t) will later be allowed only as a **descriptive structural association**. It is not a trading claim.

The strict causal annual allocation test will use:

> state_t → full-calendar-year return_{t+2}

because December macro observations for year t are not fully public on January 1 of t+1. This deliberately conservative lag prevents annual-return look-ahead.

## Higher-order inflation regime

Absolute December-to-December CPI inflation is also frozen into diagnostic buckets: deflation, 0–2%, 2–4%, 4–6%, and >=6%.

This overlay does **not** alter the HMRA Growth × Inflation grid. Its purpose is to test whether the same HMRA cell has different asset payoffs under different background inflation regimes.

## No asset outcomes in Phase 1

The Phase 1 implementation may generate macro states, occupancy and transitions. It must not load equity, Treasury, T-bill or gold returns.

The first asset-conditioned result belongs to Phase 2, after this preregistration is durable.
