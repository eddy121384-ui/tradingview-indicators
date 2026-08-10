# Issue #55 — Feed-sensitive hard-threshold finding

## Status

Confirmed diagnostic finding against the frozen `chase-risk-market-regime-radar-v0.5.2.1.pine` price-only core. This is **not** an economic-validation result and **not** permission to tune the frozen subject.

## Trigger case

- TradingView source: `OANDA:EURUSD`, 1D
- Target / actual bar: `2024-04-16`
- TradingView/OANDA output: Distribution 14.0, Markdown 86.0, Candidate 5, Formal 5
- Yahoo/Python diagnostic: Distribution ~96.343, Markdown ~2.943, Candidate 4, Formal 4

The target-date mismatch hypothesis was ruled out: both engines refer to 2024-04-16.

## Localized mechanism

The frozen Pine contains a binary structural primitive:

```pine
prevAbsLow = ta.lowest(low[1], absorbLen)
noBreakLowScore = close > prevAbsLow ? 100.0 : 0.0
```

with the frozen default `absorbLen = 50`.

`noBreakLowScore` enters both `downsideExhaustion` and `supportHolding`, which in turn enter `markdownContinuationScore` and the anti-absorption term in `markdownContinuationGate`.

### Yahoo side

On 2024-04-16:

- previous 50-bar low: `1.0623606443405151`
- close: `1.0625749826431274`
- close minus previous low: about `+2.143383` pips
- therefore `noBreakLowScore = 100`

Resulting Python/Yahoo path:

- downside exhaustion: ~57.87
- support holding: ~54.23
- markdown continuation: ~76.93
- markdown gate: ~12.64%
- Distribution / Markdown: ~96.34 / ~2.94
- Candidate: 4

### TradingView/OANDA side

The manually captured deep diagnostic on the same target date shows:

- downside exhaustion: 18.3
- support holding: 9.9
- markdown continuation: 92.3
- markdown gate: 100.0%
- Distribution / Markdown: 14.0 / 86.0
- Candidate: 5

Because `supportHolding` gives `noBreakLowScore` at least 35% weight in every relevant branch and all other terms are non-negative, observed `supportHolding = 9.9` mathematically rules out `noBreakLowScore = 100`. Therefore the OANDA/Pine path necessarily had `noBreakLowScore = 0`, i.e. its close was not above its own prior 50-bar low.

## Controlled sensitivity sweep

A diagnostic sweep changed **only the Yahoo target-bar close**, leaving the rest of the Yahoo history and that bar's original high/low/open unchanged.

The binary threshold lies between these two cases:

- close only ~`0.0034` pip **above** the prior 50-bar low → `noBreakLowScore = 100`, markdown gate ~12.64%, Distribution ~96.34 / Markdown ~2.94, Candidate 4.
- close only ~`0.0066` pip **below** the prior 50-bar low → `noBreakLowScore = 0`, markdown gate = 100%, Distribution ~29.18 / Markdown ~70.82, Candidate 5.

Thus a change of roughly **0.01 pip across the hard boundary** can flip the dominant candidate regime in the frozen implementation.

The isolated one-bar counterfactual does not necessarily flip `Formal` immediately because formal-state confirmation/inertia is path-dependent. The key result is the discontinuous score/gate/candidate change.

## Interpretation

This strongly explains the 2024 OANDA-vs-Yahoo disagreement as a **real feed-sensitive discontinuity in the frozen Pine design**, rather than evidence that the Python mirror mistranslated the state machine.

It does **not** prove full Pine/Python parity across all fields and dates. Cross-feed comparison remains diagnostic only.

## Research consequence

1. Keep v0.5.2.1 frozen for Issue #55; do not tune the threshold after observing this case.
2. Use a single canonical market-data feed for the primary OOS utility test so the test subject is well-defined.
3. Add a separate robustness audit that perturbs OHLC by small realistic amounts and/or compares alternate feeds, measuring candidate/formal regime instability.
4. Treat hard 0/100 structural predicates as an explicit robustness risk when interpreting economic results.
5. Any future refactor toward continuous / ATR-scaled / tolerance-band structural gates belongs in a separate follow-up issue, after the frozen-version validation is reported.

## Evidence files

- `fixtures/issue-55-oanda-eurusd-tv-checkpoints-v1.json`
- `fixtures/issue-55-oanda-eurusd-tv-2024-deep-v1.json`
- `diagnose_2024_divergence.py`
- `generated/wyckoff-issue-55-2024-deep-diagnostic.pine`

Boundary: this document records a robustness finding. It does not establish profitability, predictive validity, or final Pine/Python parity.
