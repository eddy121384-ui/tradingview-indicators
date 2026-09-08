# Issue #40 negative-result interpretation

Date: 2026-07-31

## Purpose

Issue #40 found `no_incremental_value` for the current SPY 1D experiment. This note asks what that negative result actually means and what it does **not** mean.

It is a literature synthesis and roadmap decision, not a new backtest. It does not change the frozen experiment, its thresholds, or its final-period result.

## Bounded repo result

The current experiment tested two causal Gaussian HMM candidates on one long-only asset, SPY 1D, using three simple roles:

- favorable-state filter;
- continuous size modifier;
- defensive-state switch.

The HMM variants did not clear the predeclared trading-value or risk-value gates against the no-HMM baselines and a simple SMA200 comparator. The closest case, K8 defensive switching on buy-and-hold, cut maximum drawdown materially but sacrificed too much annualized return and did not beat the simpler comparator consistently.

This result rejects the following narrow proposition:

> The current K3/K8 HMMs add enough value when used mainly as a SPY exposure switch under the frozen Issue #40 rules.

It does **not** establish that HMMs are generally useless in finance, that regime information has no economic value, or that every institutional HMM implementation is invalid.

## What the literature says

### 1. Regime information is harder to exploit inside an all-equity problem

Ang and Bekaert report that regimes with changing correlations and expected returns are difficult to exploit when the investor is restricted mainly to equities. They find substantially more value when the opportunity set includes cash, bonds, and equities, because a persistent bear regime can be expressed as an allocation decision rather than merely a delayed equity exit.

Source:

- Andrew Ang and Geert Bekaert, “How Regimes Affect Asset Allocation,” *Financial Analysts Journal* 60(2), 2004; NBER Working Paper 10080. https://doi.org/10.3386/w10080

This is directly consistent with Issue #40: SPY is both the signal source and the only risky destination, so every defensive action pays the opportunity cost of leaving an asset with a positive long-run risk premium.

### 2. A meaningful share of the equity premium can arrive on a small number of days

Research on the macroeconomic announcement premium finds that a large fraction of aggregate equity returns is realized on a relatively small set of announcement days. A market-timing system that exits late or re-enters late can therefore reduce drawdown while still losing a disproportionate amount of compounded return.

Sources:

- Hengjie Ai, Ravi Bansal, and Hongye Guo, “Macroeconomic Announcement Premium,” NBER Working Paper 31923, 2023. https://doi.org/10.3386/w31923
- Jessica Wachter and Yicheng Zhu, “The Macroeconomic Announcement Premium,” NBER Working Paper 24432, 2018. https://doi.org/10.3386/w24432

This helps explain the Issue #40 pattern: the K8 defensive switch recognized enough stress to reduce drawdown, but not early and precisely enough to preserve SPY’s upside compounding.

### 3. Published HMM applications usually embed regimes inside portfolio construction

The stronger use cases do not treat the HMM state as a direct buy/sell command. They use regime probabilities to alter portfolio weights, scenario distributions, risk budgets, or optimization inputs across several assets or factors.

Examples:

- Bae, Kim, and Mulvey apply an HMM across stock, bond, and commodity markets and feed regime information into stochastic portfolio optimization with rolling-horizon simulation. Their main benefit appears during left-tail events through reduced risky-asset exposure. https://doi.org/10.1016/j.ejor.2013.03.032
- Fons, Dawson, Yau, Zeng, and Keane combine HMM regimes with dynamic smart-beta portfolio construction and feature selection rather than using a single binary market switch. https://doi.org/10.1016/j.eswa.2020.113720
- Werge develops an asset-independent regime model across equity, fixed income, commodity, and currency markets and explicitly introduces sticky features to control turnover. https://doi.org/10.1016/j.eswa.2021.115576
- Collin-Dufresne, Daniel, and Sağlam model expected returns, volatility, and trading costs jointly across regimes. Their out-of-sample evidence attributes the larger gains to volatility and transaction-cost timing, while expected-return timing is more mixed. https://doi.org/10.1016/j.jfineco.2019.09.011

The common pattern is important: HMMs are often used as a **state estimator feeding a control or allocation layer**, not as an alpha oracle.

### 4. Regime-aware allocation is not automatically superior

A 2026 study comparing volatility proxies for HMM-based ETF allocation reports useful loss mitigation and risk-adjusted improvements in some markets, but the dynamic strategy still fails to beat a naive equal-weight benchmark. That is a useful warning against treating model complexity as evidence of economic value.

Source:

- Wanderci Alves Bitencourt and Robert Aldo Iquiapaza, “Comparative analysis of volatility proxies and regime-based asset allocation,” *International Review of Economics & Finance* 109, 2026. https://doi.org/10.1016/j.iref.2026.105366

Recent 2026 preprints also report promising cross-asset HMM allocation results, including SPY/TLT/GLD systems and rolling cross-asset optimization. These are relevant design references but should be treated as exploratory evidence until independently replicated and peer reviewed:

- Verma, Putri, and Lesupi, “Regime-Based Portfolio Allocation Using Hidden Markov Models and Reinforcement Learning,” 2026. https://arxiv.org/abs/2605.27848
- Boukardagha, “Explainable Regime Aware Investing,” 2026. https://arxiv.org/abs/2603.04441

## Diagnosis of Issue #40

The evidence supports the following ranking.

### High-confidence explanations

1. **Task mismatch.** The HMM was asked to time one long-only equity asset rather than allocate among assets with different regime payoffs.
2. **SPY opportunity cost.** Defensive exits compete against a persistent positive equity premium and concentrated rebound/announcement returns.
3. **Weak incremental information.** Price trend, volatility, and downside features overlap materially with information already captured by transparent SMA and momentum rules.

### Plausible secondary explanations

4. **Static translation layer.** One fixed state-risk mapping and three simple roles may discard useful posterior information.
5. **Static fit.** The frozen fit does not test rolling or expanding-window re-estimation, regime-identity tracking, or changing correlations.
6. **Gaussian emissions.** Heavy tails and crash dynamics may be represented imperfectly by a diagonal Gaussian HMM.

### Unsupported conclusions

The current evidence does not support any of the following claims:

- “HMMs do not work.”
- “Hedge funds using HMMs are wrong.”
- “More HMM tuning will necessarily create alpha.”
- “The negative result should be repaired by changing thresholds after seeing the final period.”

## Roadmap decision

Preserve Issue #40 as a valid bounded negative result.

Do not reopen the frozen final period for further K, feature, threshold, or state-mapping search. Doing so would turn the final period into another training set.

Do not advance directly to the current Issue #41 premise as though HMM utility had been proven.

The next justified experiment is a separate, preregistered **cross-asset regime-allocation value test**.

## Recommended next experiment

### Research question

Can causal HMM regime probabilities improve portfolio-level risk-adjusted performance when the decision set includes assets with different regime exposures, rather than only scaling SPY?

### Proposed investable universe

Use a small, liquid, interpretable universe:

- SPY — US equities;
- TLT or an intermediate/long Treasury proxy — duration exposure;
- GLD — gold;
- cash / 3-month Treasury-bill return.

The common sample should begin only after every investable series is available. All total-return inputs must be frozen with checksums before final evaluation.

### Required baselines

The HMM allocation must be compared against strong transparent alternatives:

- SPY buy-and-hold;
- static 60/40 stock-bond allocation;
- equal-weight 1/N portfolio;
- static risk parity or inverse-volatility allocation;
- non-HMM trend or momentum rotation using the same assets;
- volatility-targeted allocation without HMM.

### Preferred first HMM use

Start with the lower-degree-of-freedom application supported most consistently by the literature:

1. estimate regime-conditioned volatility, covariance, and downside risk;
2. use posterior probabilities to blend risk estimates or risk budgets;
3. apply turnover limits and transaction costs;
4. avoid forecasting regime-conditioned mean returns in the first experiment unless separately preregistered.

This ordering follows the evidence that volatility and trading-cost timing are generally more reliable than expected-return timing.

### Validation design

- causal features and confirmed-bar inference;
- expanding or rolling training window fixed in advance;
- stable state-identity alignment between refits;
- one-bar execution lag;
- frozen costs and turnover cap;
- separate model-development, exploratory OOS, and untouched final OOS periods;
- no final-period threshold repair;
- performance attribution by asset, regime, turnover, and concentration;
- comparison with every transparent baseline under identical dates and costs.

### Promotion gate

A cross-asset HMM allocation should advance only if it:

- improves Sharpe or Calmar materially on the untouched final period;
- reduces drawdown without an excessive return sacrifice;
- beats at least two strong non-HMM allocation baselines, not only SPY;
- remains useful after costs and turnover controls;
- does not depend on a few days, one asset, or one fitted seed;
- survives at least one adjacent-window or walk-forward sensitivity check.

### Deliberate exclusions

Do not introduce reinforcement learning in the first cross-asset test. RL adds another optimization layer and many degrees of freedom before the simpler economic question has been answered.

Do not expand to a large asset universe, leverage, options, or short selling in the first test.

## Final interpretation

Issue #40 should be read as a successful falsification:

> The current HMM candidates are not economically justified as a simple SPY timing overlay.

The literature supports one further bounded question:

> Does the same regime information become useful when it controls cross-asset risk allocation, covariance, and turnover rather than merely switching SPY exposure?

That question requires a new frozen experiment. It must not be answered by tuning against the already observed Issue #40 final period.
