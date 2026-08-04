# Hidden Regime Map v0.3 — SPY 1D K=6 visual prototype

## Decision boundary

This version exists to let Eddy inspect what the HMM is actually classifying on a TradingView chart. It freezes K=6 for the visual experiment, but it does not claim that K=6 is uniquely optimal, that the states predict returns, or that the model adds trading value.

Further state-count optimization, cross-asset expansion, and strategy/PnL work remain paused until the chart review is complete.

## Frozen profile

The prototype uses profile `spy-1d-k6-visual-v0.1`.

- Symbol and timeframe: SPY 1D only.
- Feature set: `baseline_er_downside`.
- State count: K=6.
- Training split: chronological 80/20.
- Reference fit: Run #58 feature-set comparison, group seed 42, selected restart seed 44.
- Source artifact: `hidden-regime-SPY`, artifact ID `8590548073`.
- Frozen OHLC SHA-256: `016448a0492769c527a8dc8e24d60fbda4c4e0e4bbdbcf27506caf30b76dddc4`.
- The retained K=6 candidate passed all unchanged internal guardrails on that frozen input.

The comparison artifact retained emissions, variances, transitions, restart evidence, and diagnostics but not a separate start-probability field. The exporter reconstructs the effective one-hot initial state by maximizing the full training-sequence likelihood under the retained parameters. The resulting R6 initialization reproduces the recorded training log likelihood within `1e-8`; the committed profile records the exact error.

## Features

The Pine implementation reproduces the five causal features used by the frozen profile:

1. 20-bar standardized log return using population variance.
2. 20-bar ATR divided by adjusted close.
3. 20/100 SMA spread divided by ATR.
4. 20-bar signed efficiency ratio.
5. 20-bar downside variance share.

Scaling uses means and scales fitted only on the training segment. Pine performs fixed-parameter causal forward filtering on confirmed bars; it does not train or refit the model.

## State identity

The six states remain `R1` through `R6`. No bull, bear, panic, rebound, or range names are assigned in this version. Descriptive labels may be proposed only after Eddy reviews the chart together with the profile's train/OOS feature means, occupancy, duration, and transition evidence.

State order and colors are stable within this profile. A future refit must create a new profile version and explicitly align states before reusing the color mapping.

## Visual hierarchy

The default main-chart view contains only three layers:

- a subtle background shade for the current dominant state;
- a small marker when the dominant state changes;
- a compact dashboard at the upper right.

The dashboard displays the current state, maximum posterior, top-two posterior margin, current-state duration, all six posterior probabilities, profile ID, and the SPY 1D limitation.

Six posterior series are available only in TradingView's Data Window and are disabled by default. They are not drawn as six lines over the price chart.

## Confidence and opacity

Confidence means posterior concentration only. It is not forecast accuracy, signal quality, or win probability.

Background transparency is fixed before implementation:

- maximum posterior below 55%: transparency 92;
- 55% to below 75%: transparency 78;
- 75% or above: transparency 62.

The dashboard also reports the margin between the largest and second-largest posterior. No smoothing or hysteresis is applied in this prototype because the purpose is to expose, rather than conceal, state instability.

## Transitions and persistence

A transition marker appears only when the confirmed-bar dominant state differs from the preceding confirmed bar. Current-state duration counts consecutive confirmed bars in the same dominant state. Historical states are not relabeled or smoothed after the fact.

## Unsupported use and feed mismatch

The script explicitly supports only SPY on the 1D timeframe. Other symbols or timeframes show a warning rather than plausible-looking output.

Python evidence uses frozen Yahoo Finance adjusted OHLC, while Pine requests TradingView dividend-adjusted standard OHLC. The earlier K=3 experiment established a formal feed mismatch. K=6 checkpoints therefore serve as cross-feed diagnostics; they must not be described as proof of identical-input parity unless a truly identical input fixture is supplied.

## Human review gate

The implementation is not complete merely because Pine compiles. Eddy's visual review must answer:

- Are six regimes visibly distinct, or are some only fragmented copies?
- Do transitions occur early enough to be useful, or mostly after the move?
- Are low-confidence periods appropriately visible as uncertainty?
- Does one state dominate for implausibly long periods?
- Which states, if any, deserve descriptive names?

The review must end with one explicit direction: continue productization, revise the model/features, test another asset, or stop.
