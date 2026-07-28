# Hidden Regime Map

Hidden Regime is a research-and-product program for learning what Hidden Markov Models can and cannot do in financial markets, then using that knowledge to build a regime-adaptive trading framework.

The long-term objective is to develop a defensible system with positive long-run expectancy and controlled drawdown, validate it across materially different asset classes, and deliver the work as usable TradingView indicators and strategies for real trading and responsible commercialization. It is not a perfect-prediction or guaranteed-profit project.

The project-level mission, architecture, evidence standards, product outputs, and delivery roadmap are defined in [`PROJECT_CHARTER.md`](PROJECT_CHARTER.md). Version specifications and individual issues remain authoritative for their bounded deliverables.

## Research-core milestone status

Issue #39 records the current research-core assessment:

- [human-readable assessment](research/decisions/issue-39-research-core-assessment.md)
- [machine-readable status](research/decisions/issue-39-research-core-status.json)

Current status: `complete_with_known_limitations`. The causal and reproducible research foundation is sufficient to begin Issue #40's trading-utility comparison, while cutoff sensitivity, data-feed drift, the lack of a final production profile, and the formal Pine `feed mismatch` remain explicit limitations.

## Current research boundary

The repository began with an experimental market-regime indicator based on a small Gaussian Hidden Markov Model.

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

## State-count comparison

`research/compare_state_counts.py` runs the smallest state-count selection check
for SPY daily data. It keeps the existing three observations, 80/20
chronological split, training-only scaler, diagonal Gaussian HMM, and causal
forward filter, while comparing K=3 through K=8 over fixed deterministic seeds.
Each seed group uses the small deterministic restart schedule `seed + [0, 1,
2]`; the highest-likelihood fully converged finite fit represents the group,
while every failed and successful attempt remains in the JSON. This gives all
candidates—including K=7—the same bounded recovery path.
At least two independent seed groups are required. Group seeds must be unique,
and their derived restart-attempt seed sets must not overlap; for example,
`42 43` is invalid because the groups share attempt seeds, while the default
`42 84 126` groups are independent.

```bash
python indicators/hidden-regime-map/research/compare_state_counts.py \
  --input path/to/spy.csv \
  --output-dir path/to/state-count-output \
  --symbol SPY \
  --timeframe 1D
```

The command writes `state-count-comparison.json` with per-fit and aggregate
metrics, plus a concise `state-count-decision.md`. The evidence includes
per-observation train/OOS likelihood, AIC, BIC, occupancy, duration,
self-transition, rare states, train/OOS occupancy drift, pairwise emission
separation, and reproducibility across seeds. Because HMM state numbers are
arbitrary, fits of the same K are aligned by their Gaussian emissions before
state-level reproducibility is measured; raw state indices are never compared.

These diagnostics are selection guardrails, not decorative columns. A candidate
must pass convergence and likelihood-delta checks, OOS likelihood and feature
drift limits, occupancy stability, rare-state, duration/noise, state-separation,
and aligned-seed reproducibility checks. Any incomplete K makes the comparison
inconclusive. Among candidates that pass, AIC, BIC, and OOS likelihood must all
favor the same K; conflicting evidence is also reported as inconclusive. Metric
leaders are determined across every complete K before guardrails are applied,
so filtering a noisy candidate cannot manufacture agreement among the remaining
models. A metric leader that fails a guardrail yields an inconclusive result. The
convergence check rejects an iteration-capped fit whose last positive likelihood
improvement has not reached the configured tolerance. Likelihood and occupancy
drift limits apply to the worst deterministic seed fit, not only their mean, so
stable seeds cannot conceal one unstable fit. Rare-state and separation checks
likewise use the worst seed. The
JSON retains posterior-weighted train/OOS feature means and per-state guardrail
inputs so the decision remains auditable. It also retains posterior-weighted
feature variances, variance-aware drift, mean and median durations, complete
aligned transition matrices, and exposure to the existing SPY event windows.
Event exposure retains coverage status and ratio, actual dates, window return,
average posterior, and dominant-state share.

The deterministic decision explicitly retains K=3, selects K=6, selects another
K, or remains inconclusive. It does not presume K=6.
Downloaded SPY data and generated comparison outputs remain temporary CI/local
artifacts and must not be committed.

## Feature-sufficiency comparison

`research/compare_feature_sets.py` runs the unchanged K=3–8 comparison for
exactly three ordered observation sets: the baseline, baseline plus a 20-bar
signed efficiency ratio, and those four features plus a 20-bar downside
variance share. Both additions are causal; their zero denominators produce
zero rather than non-finite observations.

```bash
python indicators/hidden-regime-map/research/compare_feature_sets.py \
  --input path/to/spy.csv \
  --output-dir path/to/feature-set-output \
  --symbol SPY \
  --timeframe 1D
```

The command writes one complete `feature-set-comparison.json` and one concise
`feature-set-decision.md`. Each variant retains every K=3–8 fit, diagnostic,
guardrail, and internal decision. The final decision prefers the simplest
stable feature set. Cross-feature materiality uses the worst deterministic seed:
minimum separation normalized by the square root of feature count, maximum
train/OOS likelihood drift normalized by feature count, and maximum occupancy
drift (already a dimensionless probability distance). A richer set must improve
normalized separation by at least 10%, improve at least one OOS consistency
diagnostic by at least 10%, and worsen neither consistency diagnostic by more
than 10% versus baseline at the same K. Both raw and normalized diagnostics
remain in the JSON and Markdown. This rule is new cross-feature decision logic
only; it does not change the merged state-count guardrails or treat likelihood
alone as evidence of better regimes. Generated outputs remain temporary research
artifacts.

## Pine parity spike

The first Pine step is intentionally narrow:

- `models/spy-1d-v0.1.json` freezes the approved SPY 1D model profile and provenance;
- `pine/hidden-regime-map-spy-parity.pine` reproduces the fixed-parameter causal filter;
- `research/fixtures/spy-1d-parity-checkpoints.json` provides a small verification fixture;
- `research/compare_pine_export.py` compares a TradingView chart-data export with the fixture.

This spike supports SPY on the one-day timeframe only. It is not a cross-asset release indicator.

Run the comparator after exporting the Pine plots from TradingView:

```bash
python indicators/hidden-regime-map/research/compare_pine_export.py \
  --export path/to/tradingview-export.csv \
  --fixture indicators/hidden-regime-map/research/fixtures/spy-1d-parity-checkpoints.json \
  --output-dir path/to/parity-report
```

Feature errors must be examined before posterior errors. A Yahoo-versus-TradingView adjusted-price difference is a feed mismatch, not permission to loosen the posterior tolerance.

## What v0.1 is not

- It is not a trading strategy or profitability claim.
- It is not a six-stage Wyckoff model.
- It does not use volume, MTF, divergence, RSI, or MACD.
- It does not integrate with the existing Wyckoff indicator.
- It does not add notebooks, Docker, a model registry, or an MLOps framework.

Design contracts:

- [`spec/hidden-regime-map-v0.1.md`](spec/hidden-regime-map-v0.1.md)
- [`spec/hidden-regime-map-v0.2-pine-parity.md`](spec/hidden-regime-map-v0.2-pine-parity.md)
