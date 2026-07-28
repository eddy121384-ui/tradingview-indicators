# Hidden Regime Project Charter

## Mission

Hidden Regime is a practical research-and-product project for learning what Hidden Markov Models can and cannot do in financial markets, then using that knowledge to build a regime-adaptive trading framework.

The long-term objective is not perfect prediction, a universally winning parameter set, or a claim of guaranteed profitability. The objective is to develop a defensible trading system with positive long-run expectancy, controlled maximum drawdown, and evidence that survives chronological out-of-sample and cross-asset testing.

The final work must be usable in TradingView. Research that cannot be translated into a practical indicator or strategy is incomplete for this project.

## What HMM is expected to do

The HMM is the market-regime layer, not the entire trading strategy.

It should estimate latent market conditions from causal observations and provide information such as:

- which market state is currently most probable;
- how concentrated or uncertain the posterior distribution is;
- whether the market is persisting in a state or transitioning;
- which trading logic and risk posture may be appropriate for the current environment.

It is not expected to directly guarantee the next-bar direction, produce perfect entries, or make risk management unnecessary.

The trading edge may come from trend following, momentum, mean reversion, volatility breakout, carry, price structure, or another transparent rule set. The HMM should be judged by whether its regime information improves the use of those rules.

## Intended system architecture

The complete system has four layers.

### 1. Regime engine

- causal feature calculation;
- fixed or explicitly retrained HMM profiles;
- posterior probabilities and dominant-state inference;
- state characterization, persistence, transition, and uncertainty diagnostics;
- auditable data, seed, restart, cutoff, and model provenance.

### 2. Trading logic

- simple baseline strategies that can be understood without the HMM;
- regime-conditioned activation, suppression, or switching of those strategies;
- explicit entry, exit, and holding rules;
- no hidden discretionary relabeling after observing performance.

Possible roles for the regime engine include:

- a trade filter;
- a strategy router;
- a position-size modifier;
- a defensive risk switch;
- a combination of the above.

### 3. Risk engine

- volatility-aware sizing;
- per-trade and total exposure limits;
- drawdown-based de-risking;
- posterior-uncertainty discounts;
- transaction-cost and slippage assumptions;
- strategy-failure and stop-trading conditions.

Stable profitability is defined by long-run expectancy and survivable losses, not by winning every month or avoiding all drawdowns.

### 4. TradingView product layer

The research must ultimately produce two practical outputs that share the same regime core.

#### Hidden Regime indicator

A usable charting and decision-support tool that can show:

- the current regime and posterior probabilities;
- confidence or uncertainty described without presenting it as win probability;
- regime transitions and persistence;
- the trading and risk posture associated with each state;
- supported symbol, timeframe, model-version, and data-feed limitations;
- alerts where they are useful and honest.

#### Hidden Regime strategy

A backtestable and executable TradingView strategy that includes:

- explicit trade rules;
- regime-conditioned behavior;
- realistic fees and slippage;
- position sizing and drawdown controls;
- alerts or automation-compatible signals;
- bounded presets or calibration rules for supported markets.

The strategy is the profitability test bed. The indicator is the human-facing regime product. Neither replaces the other.

## Cross-asset objective

“Works across assets” does not mean one magical model and one parameter set must be copied unchanged onto every market.

The project seeks a common framework that can be applied to different asset classes with limited, predefined, and auditable calibration. Candidate markets should eventually include materially different behaviors, such as:

- equity indices;
- government bonds or rates;
- commodities;
- foreign exchange.

The shared elements should include the research process, feature philosophy, regime architecture, strategy-selection logic, risk rules, validation standards, and TradingView interface. Asset-specific profiles are acceptable when their calibration boundaries are defined before performance is evaluated.

## Evidence standards

A model is not selected because its regimes look persuasive on a chart. A strategy is not accepted because one backtest is profitable.

Evidence should include, as applicable:

- causal features and confirmed-bar inference;
- chronological train and out-of-sample separation;
- walk-forward or rolling re-estimation tests where retraining is part of the design;
- deterministic seeds, restart retention, and reproducible inputs;
- comparison against a no-HMM baseline strategy;
- comparison against simpler regime alternatives;
- transaction costs and slippage;
- annualized return, volatility, Sharpe, Sortino, Calmar, and maximum drawdown;
- trade count, payoff distribution, and dependence on a small number of trades;
- parameter and cutoff sensitivity;
- performance across market periods and asset classes;
- explicit failure cases and unsupported conditions.

The HMM earns a place in the system only if it adds trading or risk-management value out of sample. Statistical elegance alone is insufficient.

## Delivery roadmap

### Phase 1 — Learn HMM through implementation

Understand latent states, emissions, transitions, posterior filtering, state-label ambiguity, local optima, seed and restart sensitivity, state-count selection, data revisions, and non-stationarity by building and testing real models.

### Phase 2 — Establish regime utility

Use transparent baseline strategies to test whether available HMM candidates improve returns, drawdown, or risk-adjusted performance. Model selection should include trading utility rather than relying only on HMM-internal diagnostics.

### Phase 3 — Build the regime-adaptive strategy framework

Determine whether the regime engine works best as a filter, router, sizing layer, defensive switch, or combination. Add an explicit risk engine and realistic execution assumptions.

### Phase 4 — Validate across assets

Apply the same framework to representative equity, rates, commodity, and FX markets. Allow only bounded, documented asset-specific calibration.

### Phase 5 — Ship TradingView products

Release a usable indicator and a backtestable strategy. Preserve model provenance, limitations, and parity checks between research outputs and Pine inference.

### Phase 6 — Commercialize responsibly

Commercialization may include public, invite-only, or paid TradingView products, presets, documentation, and ongoing research updates. Marketing must describe the regime and risk framework accurately and must not promise guaranteed returns.

## Project decision rules

- Do not optimize HMM diagnostics indefinitely without testing trading value.
- Do not relax a guardrail merely because a candidate narrowly fails after the result is observed.
- Do not treat a single asset, cutoff, seed, or backtest as sufficient evidence.
- Do not force one universal parameter set when bounded asset profiles are more defensible.
- Prefer simple, explainable baseline strategies before adding complexity.
- Preserve negative results; they determine whether the HMM belongs in the final system.
- Stop or redirect a research branch when it no longer advances learning, trading utility, risk control, or product delivery.

## Relationship to version-specific work

Existing specifications and issues remain valid within their stated boundaries.

For example, the SPY 1D v0.1 model and Pine parity work are learning and infrastructure milestones. Issue #24 is a bounded SPY 1D user-facing indicator productization task. It is not the full mission of the Hidden Regime project.

Future issues should state which charter objective they advance:

- HMM learning;
- regime utility;
- strategy development;
- risk control;
- cross-asset validation;
- TradingView indicator delivery;
- TradingView strategy delivery;
- commercialization.

This charter is the project-level north star. Version specifications remain the authoritative contracts for their individual deliverables.
