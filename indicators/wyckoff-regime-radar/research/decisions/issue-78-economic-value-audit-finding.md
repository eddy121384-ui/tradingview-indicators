# Issue #78 — Economic Value / Profitability Audit Finding

## Scope

This audit asks whether the already-frozen Issue #78 position-management candidates show positive **risk-normalized directional expectancy** when all completed formal trend episodes are chained together.

The audit was preregistered before the aggregate results at commits `1225d73c167abc383b4e4f3196da0fd75369a901` and `4f7a0d2912cdc1f023ac1a81859d6607b9bfc271`. A secondary calendar-era diagnostic was frozen before viewing era-sliced results at `b7855ea750b1602e081723fbae3fc8d20939de1f`.

Accepted sample remains unchanged:

- 9 daily markets;
- 68,118 accepted Issue #76 formal-stage rows;
- 1,624 completed known-start trend episodes;
- 806 Markup episodes;
- 818 Markdown episodes.

This is in-sample discovery. It is **not** an executable futures / cash PnL backtest. Yield-series movement is yield-direction movement, not bond-price PnL.

## Primary result — gross normalized expectancy is positive, but not temporally stable

The broadest gross result is better than the earlier negative-median episode view suggested.

| Policy | Eq-market mean / episode | Positive-mean markets | Median PF | Bootstrap 95% interval | Eq-market mean MDD |
|---|---:|---:|---:|---:|---:|
| Formal Hold | **+0.521 ATR** | **9/9** | 1.250 | +0.163 to +0.888 | 73.70 ATR |
| Persistence + Gentle | **+0.332** | **8/9** | **1.260** | +0.135 to +0.532 | **37.35** |
| Persistence + Balanced | +0.247 | 7/9 | 1.227 | +0.079 to +0.423 | **36.69** |
| Excursion-Proof + Gentle | +0.275 | 6/9 | 1.215 | +0.004 to +0.524 | 52.19 |
| Excursion-Proof + Balanced | +0.175 | 5/9 | 1.180 | -0.076 to +0.400 | 52.77 |
| Full-at-entry + Gentle | +0.272 | 6/9 | 1.127 | -0.016 to +0.542 | 57.91 |
| Full-at-entry + Balanced | +0.162 | 5/9 | 1.110 | -0.103 to +0.401 | 59.70 |

Interpretation:

- the negative median trade does **not** imply negative expectancy; the payoff is strongly right-skewed, as expected for trend following;
- Formal Hold has the strongest gross expectancy and is positive in all 9 markets, but pays by far the largest sequential drawdown;
- the Persistence ramps preserve positive gross expectancy while roughly halving the mean market drawdown versus Formal Hold;
- Excursion-Proof preserves more of individual large trends, but its aggregate economic robustness is weaker than Persistence in this sample.

## Tail-dependence stress

Trend following should be expected to depend on large winners, so the test is not whether tails matter but whether the entire edge vanishes when the largest tails are stressed.

Equal-market mean episode return after stress:

| Policy | Remove best episode / market | Remove top 1% winners | Cap winners at market 95th pct |
|---|---:|---:|---:|
| Formal Hold | +0.266 | **+0.074** | +0.306 |
| Persistence + Gentle | +0.180 | **+0.050** | +0.219 |
| Persistence + Balanced | +0.119 | **+0.003** | +0.152 |
| Excursion-Proof + Gentle | +0.115 | **-0.029** | +0.154 |
| Excursion-Proof + Balanced | +0.040 | **-0.090** | +0.074 |

The top 1% of winners contribute roughly 21% of gross positive return for Formal Hold, ~25% for Persistence + Gentle, and ~25% for Excursion-Proof + Gentle.

Interpretation:

- Formal Hold and Persistence + Gentle survive the harsh top-1%-winner removal stress on an equal-market aggregate basis;
- Persistence + Balanced only barely survives;
- both Excursion-Proof variants become negative under that stress, so their apparent edge is more tail-dependent despite better large-trend participation in the earlier slice analysis.

## Cross-market detail

Formal Hold has positive mean episode return in 9/9 markets.

Persistence + Gentle is positive in 8/9 markets; GBPUSD is the exception. Persistence + Balanced is positive in 7/9; GBPUSD and AU10Y are negative.

Excursion-Proof + Gentle is positive in 6/9; GBPUSD, FR10Y and JP10Y are negative. Excursion-Proof + Balanced is positive in only 5/9.

Leave-one-market-out equal-market expectancy remains positive in all 9 leave-one-out variants for every frozen policy. This means no single market alone creates the aggregate sign.

## Friction sensitivity

The preregistered friction units are generic entry-ATR penalties per 100% exposure turnover, not real transaction-cost estimates.

At `0.05 ATR` per unit turnover:

- Formal Hold: +0.421 ATR / episode equal-market mean; 7/9 markets positive;
- Persistence + Gentle: +0.233; 8/9 positive;
- Persistence + Balanced: +0.125; 6/9 positive;
- Excursion-Proof + Gentle: +0.166; 5/9 positive;
- Excursion-Proof + Balanced: +0.032; 5/9 positive.

At the deliberately severe `0.10 ATR` stress:

- Formal Hold remains +0.321, 7/9 positive;
- Persistence + Gentle remains +0.134, 6/9 positive;
- Persistence + Balanced is approximately flat at +0.004, 4/9 positive;
- Excursion-Proof + Gentle remains +0.057 but only 4/9 markets are positive;
- Excursion-Proof + Balanced turns negative.

These results are only normalized-friction portability checks. They are not substitutes for instrument-specific bid/ask, slippage, contract size, DV01, carry and financing.

## Secondary temporal stability diagnostic — important failure

The common nine-market period was split, unchanged, into three preregistered eras:

| Policy | 2010–2014 | 2015–2019 | 2020–2026 |
|---|---:|---:|---:|
| Formal Hold | **+1.481** (8/9) | **-0.101** (4/9) | +0.170 (7/9) |
| Persistence + Gentle | **+0.727** (8/9) | **-0.098** (2/9) | +0.098 (5/9) |
| Persistence + Balanced | +0.400 (6/9) | **-0.108** (2/9) | +0.099 (6/9) |
| Excursion-Proof + Gentle | +0.734 (8/9) | **-0.179** (2/9) | +0.087 (6/9) |
| Excursion-Proof + Balanced | +0.396 (6/9) | **-0.186** (2/9) | +0.084 (6/9) |

Every frozen policy loses its equal-market gross edge during 2015–2019.

This prevents any claim of `stable alpha` or `stable profitability` from the current evidence. The aggregate historical expectancy is positive, but it is meaningfully regime-dependent through time.

## Post-hoc directional diagnostic

Not part of the primary preregistration and therefore diagnostic only: the positive aggregate expectancy is materially stronger in Markdown than in Markup.

For example, Persistence + Gentle has equal-market mean episode return of approximately +0.145 ATR in Markup versus +0.496 ATR in Markdown. Excursion-Proof + Gentle is slightly negative in Markup (~-0.036) and strongly positive in Markdown (~+0.548).

Do not turn this into separate long/short parameter sets. It is evidence that realized market opportunity is asymmetric, not authorization to tune the classifier by direction.

## Decision

The correct language is:

> **Gross normalized directional edge is detected and is reasonably broad across markets, but it is not temporally stable and remains in-sample.**

The current evidence rejects the stronger claim that the Issue #78 state machine has already demonstrated stable profitability.

Two architectures merit further validation for different reasons:

- **Formal Hold** — strongest gross edge and tail robustness, but extremely high giveback / drawdown cost;
- **Persistence + Gentle** — weaker gross edge, but much lower drawdown, broad cross-market behavior, positive bootstrap interval and positive top-1%-tail stress.

No production policy is selected. Excursion-Proof remains useful as a visual / large-trend participation candidate, but its economic result is more tail-dependent and less cross-market broad in this sample.

## Next gate

Do **not** tune 2015–2019 away.

Next research should ask why all frozen policies weaken in that era without changing the classifier or policy parameters. Then freeze candidate rules and challenge them on genuinely new heterogeneous evidence:

- equities;
- commodities;
- weekly data;
- later / prospective observations.

For a real profitability claim after that, map the state machine to executable instruments — especially Treasury futures for yield signals — and include contract sizing, DV01, roll, spread, slippage and financing.

Refs #78, #80 and #76.
