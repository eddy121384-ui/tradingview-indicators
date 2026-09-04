# Issue #68 — FR10Y vs DE10Y Downside-Exhaustion Component Finding

Status: discovery-only finding. Production C-2 remains frozen.

Window: 2022-01-03 through 2023-12-29, daily.

## Observed TradingView results

### DE10Y

Population = 512; RAW-S1 -> EFF-S2 flip = 185; no-flip = 327.

- Downside-exhaustion score: all 54.29; flip 52.01; no-flip 55.58.
- Downside-exhaustion gate: all 0.75; flip 0.69; no-flip 0.79.
- NoBreakLow 30%: raw/weighted-deficit all 97.56 / 0.73; flip 98.82 / 0.35; no-flip 96.85 / 0.95.
- NegSlopeDull 25%: all 7.16 / 23.21; flip 0.41 / 24.90; no-flip 10.97 / 22.26.
- PanicDull 20%: all 9.15 / 18.17; flip 7.36 / 18.53; no-flip 10.16 / 17.97.
- LowVol 15%: all 98.13 / 0.28; flip 99.18 / 0.12; no-flip 97.54 / 0.37.
- LowZoneStable 10%: all 66.82 / 3.32; flip 59.09 / 4.09; no-flip 71.20 / 2.88.
- Largest weighted deficit: NegSlopeDull in all / flip / no-flip populations.
- DownEx >= full: all 13.09%; flip 0%; no-flip 20.49%.
- Flip runs / max: 19 / 82.

### FR10Y

Population = 512; RAW-S1 -> EFF-S2 flip = 110; no-flip = 402.

- Downside-exhaustion score: all 58.84; flip 54.76; no-flip 59.96.
- Downside-exhaustion gate: all 0.85; flip 0.76; no-flip 0.87.
- NoBreakLow 30%: raw/weighted-deficit all 97.62 / 0.71; flip 97.79 / 0.66; no-flip 97.57 / 0.73.
- NegSlopeDull 25%: all 22.84 / 19.29; flip 10.42 / 22.40; no-flip 26.24 / 18.44.
- PanicDull 20%: all 13.10 / 17.38; flip 11.64 / 17.67; no-flip 13.50 / 17.30.
- LowVol 15%: all 96.85 / 0.47; flip 95.62 / 0.66; no-flip 97.19 / 0.42.
- LowZoneStable 10%: all 66.97 / 3.30; flip 61.46 / 3.85; no-flip 68.48 / 3.15.
- Largest weighted deficit: NegSlopeDull in all / flip / no-flip populations.
- DownEx >= full: all 36.13%; flip 4.55%; no-flip 44.78%.
- Flip runs / max: 20 / 27.

## Interpretation

The component audit materially localizes the DE-vs-FR relative-gate difference to `NegSlopeDull`.

`NoBreakLow` and `LowVol` are near-saturated in both markets and cannot explain the split. `LowZoneStable` is a secondary difference and `PanicDull` contributes some deficit, but neither is remotely as large as the `NegSlopeDull` deficit.

The production formula is:

`negSlopeDullScore = f_gate(speedRank, 15.0, 55.0) * 100`

with:

- `speedRank = ta.percentrank(speedZ, rankLen)`;
- `speedZ = f_slopeZ(logPrice, speedLen, vol)`;
- `logPrice = log(close)` only when `close > 0`;
- `vol = stdev(log(close/close[1]), volLen)`;
- default `speedLen=20`, `volLen=60`, `rankLen=756`.

Thus the next causal question is not whether downside exhaustion matters; it does. The question is why visually similar 2022-2023 yield paths produce materially lower `speedRank` / `NegSlopeDull` in DE10Y than FR10Y, especially on RAW-S1 -> EFF-S2 flip bars.

## Next step

Run a frozen transformation-chain audit from economic bp slope through log-domain slope, volatility normalization, historical percentile rank, and finally `NegSlopeDull`.

The audit must distinguish:

1. genuine 20D bp-path difference;
2. positive-domain / negative-rate history coverage effect;
3. log-level transformation effect;
4. log-return volatility normalization effect;
5. 756-bar percentile-history effect.

No tuning, no PnL, and no production change is authorized by this finding.