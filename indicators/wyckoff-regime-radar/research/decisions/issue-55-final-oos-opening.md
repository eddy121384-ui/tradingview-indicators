# Issue #55 — Final OOS opening record

Status: **FINAL OOS OPENED — ONE SHOT**

Opened on: 2026-08-10

This record marks the irreversible transition from pre-final diagnostics to the one-shot Final-OOS evaluation for the frozen `Chase Risk Market Regime Radar v0.5.2.1` price-only FX experiment.

## Preconditions satisfied before opening

1. Frozen Pine subject and Python mirror are already in PR #56.
2. TradingView/OANDA checkpoints and the 2024 deep diagnostic are recorded.
3. Feed-sensitive hard-threshold behavior is documented and is not tuned away.
4. The canonical static FX input files are committed with checksums and fixed 60/20/20 boundaries.
5. Development and Exploratory-OOS path, occupancy/episode, state-separation, and confidence-calibration reports are committed.
6. The executable response map, baselines, one-bar lag, and 1-pip-per-unit-turnover primary cost were committed before Exploratory trading utility was evaluated.
7. The frozen-rule Exploratory-OOS utility report was committed without changing those rules.
8. Research tests passed before this opening record.

## Frozen Final-OOS window

All four pairs use the same final partition from the canonical manifest:

- start: **2020-04-30**
- end: **2022-03-04**
- 480 daily bars per pair

No date, rule, pair, threshold, confidence cutoff, cost, baseline, or mapping may now be changed for this sample.

## Frozen executable response

Source of truth:

`decisions/issue-55-final-oos-response-map-and-baselines.md`

Primary response:

- 0 No formal state → 0
- 1 Accumulation → 0
- 2 Markup → +1
- 3 Re-accumulation → +1
- 4 Distribution → 0
- 5 Markdown → -1
- 6 Redistribution → -1

Execution: one-bar lag.

Primary transaction cost: 1.0 pip per unit turnover.

Baselines: always-flat, SMA200, 60-day momentum, 55-day Donchian breakout.

## Pre-final evidence already observed

These facts existed before the Final OOS was opened and therefore cannot be used to alter the rules:

- Formal Markup vs Markdown directional sanity was weak/mostly reversed across Development + Exploratory comparisons.
- Stage coverage contracted materially on FX; Re-accumulation and Redistribution had no complete episodes in the pre-final sample.
- Development-to-Exploratory state-return ranking was unstable.
- `Evidence` confidence calibration was poor; `Top Gap` high-vs-low behavior was approximately coin-flip and strict monotonic calibration was rare.
- Under the frozen response map on Exploratory OOS, the equal-weight four-pair Wyckoff response had negative return/Sharpe and trailed the simple baselines.

These findings make a negative Final OOS plausible, but the Final sample is still evaluated exactly as preregistered rather than skipped.

## One-shot rule

The next Final-OOS report is the test result. If it is unattractive, do not retune and rerun this same 2020-04-30 to 2022-03-04 window as though it were independent. Any redesign requires a new follow-up issue and a new independent evaluation sample.
