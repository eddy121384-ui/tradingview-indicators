# Issue #78 — OOS3 local artifact recovery note

Date: 2026-10-02

## Incident

The workstation no longer contained the local untracked `artifacts/` directory used for the completed OOS3 Bloomberg snapshot and policy run.

A repository-wide search for:

- `issue78_equity_proof_policy_oos3_universe_manifest.csv`
- `issue119_bbg_oos2_raw_manifest.json`

returned no local copy under the repository.

This is an engineering / local-artifact-loss event. It does not alter the already-recorded OOS3 economic result.

## Recoverable cohort identity

Before the local artifact loss, the completed OOS3 policy result bundle had already been exported and preserved.

Its `coverage.csv` contains exactly:

- 300 rows;
- 300 unique FIGIs;
- ticker;
- security;
- sector;
- large / mid / small sleeve.

The exact sorted FIGI-set identity is now frozen as:

`017e9360402afa002dc0970088649e7c411c4f02333dec550f2432be3c0dd701`

The original universe-file byte SHA remains:

`9d4a14d163ed308238737647b94e722c62fd023b641e1015e6d97679f9ba3b44`

The original byte representation cannot be reconstructed from `coverage.csv`; therefore recovery validation must distinguish:

1. original manifest byte identity; and
2. exact security-cohort identity.

The Trendability autopsy now requires the exact frozen 300-FIGI set and accepts a reconstructed identity-only universe CSV only when that FIGI-set SHA matches.

No stock may be added, removed, substituted, or resampled.

## Raw-price recovery

If no surviving raw snapshot is found elsewhere on the workstation, Bloomberg OHLCV may be re-downloaded for the exact recovered 300-security cohort using the same frozen:

- 1998-01-01 raw start;
- 2026-08-31 end;
- split adjustment;
- no cash-dividend back-adjustment;
- OHLC normalization contract.

This is data recovery, not a new sample draw.

Any re-downloaded snapshot must pass the normal audit before the Trendability diagnostic runs.

## Research firewall

This recovery does not authorize:

- changing the OOS3 cohort;
- refreshing index membership;
- replacing short-history names;
- changing Trendability parameters;
- changing proof / B3 / WarningFirst policy definitions.

Refs #78, #138, #135.
