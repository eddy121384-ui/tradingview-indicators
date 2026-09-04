# Issue #68 — FR10Y vs DE10Y RAW Margin Distribution Finding

Status: discovery-only finding. Production C-2 remains frozen.

Window: 2022-01-03 through 2023-12-29, daily.

## Observed TradingView results

### DE10Y

- RAW S2-leading bars: effectively 0 across the window.
- RAW S1-leading structure: one continuous run, ~512 bars; leader flips = 0.
- Fixed `S2 RAW - S1 RAW` bins:
  - `<= -20`: 43.1%
  - `(-20,-10]`: 52.1%
  - `(-10,0]`: 5.1%
  - `(0,10)`: 0.1%
  - `[10,20)`: 0.1%
  - `>=20`: 0.1%
- Conditional RAW levels on S1-leading bars: S2 = 54.1, S1 = 76.1.

### FR10Y

- RAW S2-leading bars: effectively 0 across the window.
- RAW S1-leading structure: one continuous run, ~512 bars; leader flips = 0.
- Fixed `S2 RAW - S1 RAW` bins:
  - `<= -20`: 30.1%
  - `(-20,-10]`: 38.1%
  - `(-10,0]`: 32.1%
  - `(0,10)`: 0.1%
  - `[10,20)`: 0.1%
  - `>=20`: 0.1%
- Conditional RAW levels on S1-leading bars: S2 = 59.1, S1 = 75.1.

Percentages are read from the TradingView audit table and are displayed to one decimal place, so rounded bins need not sum to exactly 100.0%.

## Interpretation

The preregistered hypothesis that FR might fail because S2 only wins in isolated spikes while DE obtains durable positive `S2-S1` stretches is rejected.

In both markets, S1 dominates S2 at RAW essentially throughout the entire shared Bull-yield window, with no meaningful leader churn. More importantly, FR is actually *closer* to S2/S1 parity than DE: FR has higher average S2 RAW (59.1 vs 54.1), slightly lower average S1 RAW (75.1 vs 76.1), and far more mass in the near-zero negative margin band. Therefore the FR-vs-DE semantic split cannot be explained by a uniquely weak FR S2-vs-S1 RAW ordering.

This materially strengthens the localization away from pairwise S1/S2 RAW competition. DE's superior Bull TOP / Formal rescue must come from another part of global stage competition, with S3 Reaccumulation the already-preregistered primary candidate, or from the subsequent ranking / normalization / Strong / Formal path.

## Next step

Run the existing frozen Bull-source / S3 attribution audit on FR10Y and DE10Y using:

`indicators/wyckoff-regime-radar/research/generated/wyckoff-issue68-cross-market-bull-source-s3-attribution-audit.pine`

Interpret under the existing preregistration:

`indicators/wyckoff-regime-radar/research/decisions/issue-68-bull-source-s3-attribution-preregistration.md`

No tuning, no PnL, and no production change is authorized by this finding.