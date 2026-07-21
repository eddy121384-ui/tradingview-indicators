# Hidden Regime Map v0.1 Specification

## Purpose

Test whether a small Gaussian Hidden Markov Model can produce useful, persistent market-regime probabilities that can later be reproduced in Pine Script with fixed parameters.

v0.1 is a research indicator, not a strategy.

## Latent states

Use exactly three latent states:

- State A
- State B
- State C

The states remain unnamed during training. After training, assign descriptive labels from their measured characteristics:

- mean standardized return;
- mean volatility;
- mean trend strength;
- average persistence or duration.

Expected labels are Bull, Bear, and Range, but the implementation must report when the fitted states do not support that interpretation.

## Observations

Use exactly three observations calculated from confirmed bars:

1. **Standardized return** — log return normalized by a rolling volatility estimate.
2. **Volatility** — realized volatility or ATR as a percentage of price.
3. **Trend strength** — fast/slow moving-average spread normalized by ATR.

Exact lookback lengths and normalization rules belong to the research implementation and must be exported with the fitted model parameters.

## Training contract

The Python research implementation will:

- accept historical OHLC data for one configured symbol and timeframe;
- calculate the three observations without future data;
- fit a three-state Gaussian HMM;
- use a fixed random seed;
- export initial probabilities, the transition matrix, emission means, emission covariance or variance, feature configuration, and training metadata;
- produce a diagnostic summary for each state.

The first implementation may use diagonal covariance unless evidence shows that full covariance materially improves the result.

## Pine inference contract

Pine Script will not train the model. It will use exported fixed parameters and perform forward filtering on each confirmed bar:

1. calculate the current observation vector;
2. project the previous posterior through the transition matrix;
3. calculate each state's emission likelihood;
4. multiply prior probability by likelihood;
5. normalize the three values into a posterior distribution.

The displayed probabilities must sum to 100% within normal floating-point tolerance.

Do not add a separate confirmation-bar or regime-smoothing layer in v0.1. Persistence should come from the transition matrix itself.

## Display target

A later Pine implementation should show:

- the posterior probability of all three states;
- the currently dominant state;
- optional background coloring for the dominant state;
- a compact diagnostic view of the active model version and feature configuration.

The display must call the values posterior probabilities, not generic scores.

## Validation

v0.1 is acceptable only if:

- states show meaningful persistence rather than switching on nearly every bar;
- fitted state characteristics allow a defensible interpretation;
- probabilities change progressively around regime transitions;
- no observation uses future data;
- Python and Pine produce matching posteriors on a shared verification sample within an agreed numerical tolerance;
- results are inspected on at least one out-of-sample period and one additional liquid market.

A profitable backtest is not an acceptance requirement.

## Deliberate non-goals

- six Wyckoff stages;
- trade entries, exits, position sizing, or optimization for returns;
- online retraining inside TradingView;
- volume, MTF, divergence, RSI, MACD, or alternative feature sweeps;
- automatic per-symbol retraining;
- model registry, notebook framework, Docker, cloud training, or scheduled pipelines;
- integration with Chase Risk Market Regime Radar.

## Next implementation step

Build one small Python research script that trains the three-state model, exports its parameters, and produces state diagnostics. Do not create Pine code until the fitted states pass the validation checks above.
