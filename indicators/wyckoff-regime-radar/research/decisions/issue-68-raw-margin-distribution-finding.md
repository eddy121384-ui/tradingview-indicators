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

The preregistered hypothesis that FR might fail because S2 only wins in isolated RAW spikes while DE obtains durable positive `S2-S1` RAW stretches is rejected.

In both markets, S1 dominates S2 at RAW essentially throughout the entire shared Bull-yield window, with no meaningful leader churn. More importantly, FR is actually closer to S2/S1 RAW parity than DE: FR has higher average S2 RAW (59.1 vs 54.1), slightly lower average S1 RAW (75.1 vs 76.1), and far more mass in the near-zero negative margin band.

This is not evidence against post-RAW gating. It is the opposite. Earlier Bull-source attribution already falsified S3 rescue and showed final Bull TOP is almost entirely S2 Markup: FR S2 TOP ~21.1% vs DE ~36.1%, while S3 is ~0.1% in both. Because the gamma transform and common normalization are monotonic, they cannot reverse S1/S2 ordering. Therefore, if S1 RAW leads S2 RAW essentially 100% of the time but S2 still becomes final TOP on 21–36% of bars, the decisive ordering reversal must occur at the RAW × gate -> effective-score layer.

The prior focus on `RAW S2 > S1 -> EFF S1` was the wrong flip direction for this population: there are essentially no RAW S2-leading bars to flip. The relevant event is `RAW S1 >= S2 -> EFF S2 > S1`.

The contrast is especially strong because FR starts from the more favorable RAW ratio for S2 yet ends with much lower S2 TOP occupancy than DE. That implies DE receives a materially stronger *relative gate advantage* for S2 versus S1.

## Next step

Preregister and measure the relative-gate crossing directly.

For each bar define:

- required gate ratio to reverse RAW ordering: `S1 RAW / S2 RAW`;
- observed relative gate ratio: `S2 gate / S1 gate`;
- gate surplus: `observed ratio - required ratio`;
- flip condition: `S2 RAW * S2 gate > S1 RAW * S1 gate`.

Then compare FR10Y and DE10Y on:

1. `RAW S1 -> EFF S2` occupancy and run persistence;
2. average required ratio vs observed gate ratio;
3. gate-surplus distribution;
4. S1 binding sub-gate on flip vs non-flip bars;
5. S2 dominant gate source on flip vs non-flip bars.

This is a causal attribution audit only. No tuning, no PnL, and no production change is authorized by this finding.