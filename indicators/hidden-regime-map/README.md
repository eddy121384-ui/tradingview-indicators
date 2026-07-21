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
3. Pine Script later uses those fixed parameters to run forward filtering on each confirmed bar.
4. TradingView displays the three posterior state probabilities and the dominant state.

Training and live inference are deliberately separate. Pine Script will not retrain the model.

## Research prototype

The first executable step is `research/train_hmm.py`. It accepts a chronological OHLC CSV with `Date`, `Open`, `High`, `Low`, and `Close` columns by default.

Create an isolated environment and install the small research dependency set:

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install -r indicators/hidden-regime-map/requirements-research.txt
```

On Windows PowerShell, activate with `.venv\Scripts\Activate.ps1`.

Run the prototype:

```bash
python indicators/hidden-regime-map/research/train_hmm.py \
  --input path/to/ohlc.csv \
  --output-dir path/to/output \
  --symbol SPY \
  --timeframe 1D
```

The script fits the scaler and HMM on the chronological training segment only, then calculates causal forward-filtered probabilities across the full sample. It writes:

- `model-parameters.json` — feature configuration, scaler, transition matrix, emission parameters, metadata, and interpretation checks;
- `state-diagnostics.csv` — occupancy, state characteristics, duration, and persistence;
- `filtered-posteriors.csv` — per-row posterior probabilities and dominant state.

Generated data and model outputs are research artifacts and are not committed by default. A Pine implementation remains blocked until real-market diagnostics show persistent and defensibly interpretable states.

## What v0.1 is not

- It is not a trading strategy or profitability claim.
- It is not a six-stage Wyckoff model.
- It does not use volume, MTF, divergence, RSI, or MACD.
- It does not integrate with the existing Wyckoff indicator.
- It does not add notebooks, Docker, a model registry, or an MLOps framework.

See [`spec/hidden-regime-map-v0.1.md`](spec/hidden-regime-map-v0.1.md) for the current design contract.
