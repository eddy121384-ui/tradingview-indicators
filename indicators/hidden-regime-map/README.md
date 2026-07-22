# Hidden Regime Map

Hidden Regime Map is an experimental market-regime indicator based on a small Gaussian Hidden Markov Model.

The first version asks one narrow question: can three latent states separate persistent upward, downward, and range-like market behavior better than another hand-built threshold stack?

## v0.1 boundary

The model starts with three unnamed states—A, B, and C—and three observations:

- standardized return;
- ATR as a percentage of price;
- MA spread normalized by ATR.

State names are assigned only after training by inspecting each state's return, volatility, trend strength, and persistence. The training process must not force State A to mean Bull in advance.

## Intended workflow

1. Python calculates the observations and trains the HMM on historical data.
2. Python exports the initial probabilities, transition matrix, and emission parameters.
3. Python characterizes each fitted state without changing the model.
4. Pine Script may later use fixed parameters to run forward filtering on confirmed bars.

Training, post-fit characterization, and live inference are deliberately separate. Pine Script will not retrain the model.

## Research prototype

The first executable step is `research/train_hmm.py`. It accepts a chronological OHLC CSV with `Date`, `Open`, `High`, `Low`, and `Close` columns by default.

Create an isolated environment and install the small research dependency set:

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install -r indicators/hidden-regime-map/requirements-research.txt
```

On Windows PowerShell, activate with `.venv\Scripts\Activate.ps1`.

Run the prototype with an existing CSV:

```bash
python indicators/hidden-regime-map/research/train_hmm.py \
  --input path/to/ohlc.csv \
  --output-dir path/to/output \
  --symbol SPY \
  --timeframe 1D
```

The script fits the scaler and HMM on the chronological training segment only, then calculates causal forward-filtered probabilities across the full sample. It writes:

- `model-parameters.json` — feature configuration, scaler, transition matrix, emission parameters, metadata, and the original provisional interpretation check;
- `state-diagnostics.csv` — occupancy, state characteristics, duration, and persistence;
- `filtered-posteriors.csv` — per-row posterior probabilities and dominant state.

## State characterization

`research/characterize_states.py` replaces forced Bull/Bear/Range naming with an auditable post-fit report. It combines:

- posterior-weighted trend and volatility;
- dominant-state occupancy, duration, and self-transition probability;
- train versus out-of-sample behavior;
- 5-day and 20-day forward returns;
- explicit historical event windows from `research/event-windows.json`.

Forward returns and event windows are **ex-post diagnostics only**. They do not alter HMM training, filtering, exported model parameters, or future Pine inputs.

Run characterization after the model outputs exist:

```bash
python indicators/hidden-regime-map/research/characterize_states.py \
  --posteriors path/to/output/filtered-posteriors.csv \
  --diagnostics path/to/output/state-diagnostics.csv \
  --model path/to/output/model-parameters.json \
  --events indicators/hidden-regime-map/research/event-windows.json \
  --output-dir path/to/output \
  --symbol SPY
```

It writes:

- `state-characterization.csv` — state metrics across full, training, and out-of-sample periods;
- `event-window-analysis.csv` — average posterior and dominant-state share in each named event window;
- `characterization.json` — machine-readable descriptions, confidence, thresholds, and contradictions;
- `characterization.md` — a review-ready report.

Descriptions are fit- and asset-specific. Valid outputs include calm advance, downside stress, upside stress, orderly decline, quiet range, volatile range, mixed regime, and ambiguous regime. The report must preserve contradictions instead of hiding them behind a directional label.

## Public-data validation

For research-only validation, `research/download_yfinance.py` downloads one daily Yahoo Finance series into the required CSV shape. Adjusted OHLC is the default so ETF distributions and splits do not create artificial price jumps.

```bash
python indicators/hidden-regime-map/research/download_yfinance.py \
  --ticker SPY \
  --start 2010-01-01 \
  --output /tmp/spy.csv
```

The repository workflow runs the same training and characterization checks for SPY and TLT and uploads temporary artifacts. Yahoo Finance data is suitable for method validation, not the final Bloomberg-calibrated deployment model. yfinance is an unofficial research client and downloaded data remains subject to Yahoo's terms of use.

Generated data and model outputs are research artifacts and are not committed by default. A Pine implementation remains blocked until the state-characterization evidence is reviewed and judged sufficiently stable and interpretable.

## What v0.1 is not

- It is not a trading strategy or profitability claim.
- It is not a six-stage Wyckoff model.
- It does not use volume, MTF, divergence, RSI, or MACD.
- It does not integrate with the existing Wyckoff indicator.
- It does not add notebooks, Docker, a model registry, or an MLOps framework.

See [`spec/hidden-regime-map-v0.1.md`](spec/hidden-regime-map-v0.1.md) for the current design contract.
