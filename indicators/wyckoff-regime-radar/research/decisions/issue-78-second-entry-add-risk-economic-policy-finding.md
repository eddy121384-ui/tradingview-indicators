# Issue #78 — Second-Entry / Add-Risk Economic Policy Finding

## Scope

This finding executes the preregistered second-entry / add-risk economic policy study after definition-only Resume research was stopped.

The question is economic:

> For healthy P1 / P2 breakout paths, is it better to add the extra 75 percentage points of exposure immediately at t+3, or wait for R5 / R1 / R4 confirmation?

Frozen candidates:

- R0 Immediate — add from 25% Probe to 100% Full at t+3 once P1 / P2 is known.
- R5 Local Close — wait for the frozen retest-segment favorable close break.
- R1 Close Extreme — wait for the frozen full favorable close extreme break.
- R4 Progress +0.5 ATR — conservative momentum benchmark.

P0 adds at t+3 for every candidate. P3 never adds. No-trigger P1 / P2 episodes remain at Probe and stay in the economics. No deterioration overlay is used.

All returns remain normalized underlying-move units, not executable futures / cash PnL.

## Frozen sample reproduced exactly

The accepted Issue #76 logger files reconstruct:

- 68,118 events;
- 1,624 completed Markup / Markdown episodes;
- 997 B3 breakout events;
- 236 P1 / P2 Resume-eligible events.

Path counts:

- P0 No-touch: 411
- P1 Wick Hold: 110
- P2 Reclaim: 126
- P3 Failed Acceptance: 350

Maximum OHLC reconstruction error is approximately 5.6e-14.

The economic pass therefore uses the same frozen event population as the prior breakout / retest / Resume studies.

## 1. Whole-system result: delayed Resume does not beat immediate add-risk

Equal-market whole-system results:

| Policy | Ann. return | Ann. vol | Sharpe-like | Max DD | 5% ES | Avg exposure | Ann. turnover |
|---|---:|---:|---:|---:|---:|---:|---:|
| R0 Immediate | 1.4623 | 11.8544 | 0.1187 | 58.03 | -1.8556 | 0.4862 | 5.1400 |
| R5 Local Close | 1.3915 | 11.7234 | 0.1174 | 59.01 | -1.8368 | 0.4714 | 4.9055 |
| R1 Close Extreme | 1.3692 | 11.7106 | 0.1163 | 59.28 | -1.8352 | 0.4701 | 4.8719 |
| R4 +0.5 ATR | 1.4062 | 11.6874 | 0.1191 | 59.27 | -1.8328 | 0.4654 | 4.7783 |

Annualized return delta versus R0:

- R5: -0.0708
- R1: -0.0931
- R4: -0.0561

Each delayed rule beats R0 in only 4/9 markets on annualized return. Median market deltas are also negative:

- R5 vs R0: -0.0920
- R1 vs R0: -0.2022
- R4 vs R0: -0.0476

At R0 volatility, equal-market annualized return remains below R0:

- R0: 1.4623
- R5: 1.4044
- R1: 1.3834
- R4: 1.4229

Therefore lower raw return is not explained only by carrying less exposure. The confirmation tax is not recovered by equal-vol scaling.

## 2. Risk tradeoff

Delayed confirmation does improve the worst daily left tail.

5% ES improves versus R0 in 9/9 markets for R5, R1 and R4:

- R5 ES delta: +0.0188
- R1 ES delta: +0.0205
- R4 ES delta: +0.0229

But complete-path maximum drawdown does not improve.

Max-DD magnitude delta versus R0:

- R5: +0.98
- R1: +1.25
- R4: +1.24

Sharpe-like behavior is essentially flat to slightly worse:

- R5 vs R0: -0.0013
- R1 vs R0: -0.0023
- R4 vs R0: +0.0004

R4's tiny Sharpe improvement is positive in only 4/9 markets.

Interpretation:

> Waiting reduces immediate daily tail exposure, but missed favorable movement does not translate into a better cumulative risk / return path.

## 3. Direct P1 / P2 economics

All 236 eligible P1 / P2 episodes are retained, including no-trigger cases.

| Policy | Trigger rate | Mean add-on return | Mean total return | Foregone add return vs R0 |
|---|---:|---:|---:|---:|
| R0 Immediate | 100.0% | +0.5347 ATR | +1.1496 ATR | 0.0000 |
| R5 Local Close | 84.9% | +0.4159 | +1.0308 | +0.1188 |
| R1 Close Extreme | 82.4% | +0.3892 | +1.0041 | +0.1455 |
| R4 +0.5 ATR | 75.5% | +0.4390 | +1.0539 | +0.0957 |

Cross-market mean add-on delta versus R0:

- R5: -0.1188 ATR, wins 4/9;
- R1: -0.1455 ATR, wins 4/9;
- R4: -0.0957 ATR, wins 4/9.

Median market deltas are also negative:

- R5: -0.1140 ATR
- R1: -0.1954 ATR
- R4: -0.0590 ATR

The economic confirmation tax is therefore real.

## 4. Confirmation protects failed / small trends

For P1 / P2 episodes with MFE < 4 ATR, mean add-on return is:

- R0: -1.4509 ATR
- R5: -1.1265
- R1: -1.0964
- R4: -0.9855

Improvement versus R0:

- R5: +0.3244 ATR, positive in 7/9 markets;
- R1: +0.3545 ATR, positive in 8/9;
- R4: +0.4654 ATR, positive in 6/9.

Resume confirmation is therefore genuinely useful as protection against adding into failed / small trends.

The issue is the price paid when trends are real.

## 5. Large-trend harvest pays for that protection

For P1 / P2 episodes with MFE >= 8 ATR, mean add-on return is:

- R0: +5.5406 ATR
- R5: +4.8303
- R1: +4.6806
- R4: +4.7685

Foregone add-on harvest versus R0:

- R5: 0.7103 ATR
- R1: 0.8600 ATR
- R4: 0.7721 ATR

Cross-market consistency is strong:

- R5 trails R0 in 8/9 markets;
- R1 trails R0 in 9/9;
- R4 trails R0 in 9/9.

The saved failed-trend damage is therefore purchased by systematically surrendering a meaningful part of large-trend harvest.

Across the complete population, the surrendered harvest is larger than the protection recovered.

## 6. Old-box failure diagnostic confirms the mechanism

Among P1 / P2 episodes that re-enter the old box within the next three closes after t+3, mean add-on return is:

- R0: -0.9367 ATR
- R5: -0.2635
- R1: -0.3085
- R4: -0.1580

So delayed confirmation works extremely well when the breakout soon fails.

Among the non-failing group:

- R0: +1.2904 ATR
- R5: +0.7643
- R1: +0.7386
- R4: +0.7145

The box-failure label is ex post and may not be converted into a fitted conditional rule.

The legitimate interpretation is:

> confirmation filters damage, but it also delays profitable continuation too aggressively for the unconditional add-risk policy.

## 7. Mandatory 2015–2019 stress era fails for delayed confirmation

Whole-system annualized-return delta versus R0:

2010–2014:

- R5: +0.1375
- R1: +0.0525
- R4: +0.0907

2015–2019:

- R5: -0.4957
- R1: -0.5962
- R4: -0.6243

Breadth in 2015–2019:

- R5 beats R0 in only 1/9 markets;
- R1 in 1/9;
- R4 in 0/9.

2020–2026:

- R5: +0.0193
- R1: +0.0160
- R4: +0.1790

The required stress era does not merely weaken delayed confirmation; it reverses it broadly across markets.

No delayed Resume policy has temporally stable economic superiority over R0.

## 8. Direction robustness

P1 / P2 mean add-on return remains lower than R0 in both directions.

Markup:

- R0: +0.4810
- R5: +0.3414
- R1: +0.3334
- R4: +0.3411

Markdown:

- R0: +0.4276
- R5: +0.3535
- R1: +0.3188
- R4: +0.3744

The result is not a one-direction artifact and no direction-specific rule is justified.

## 9. R5 does improve the delayed-confirmation frontier versus R1

R5 minus R1:

- whole-system annualized return: +0.0223;
- positive return delta in 7/9 markets;
- Sharpe-like delta: +0.0011, positive in 7/9;
- P1 / P2 mean add-on return: +0.0267 ATR;
- add-on delta positive in 7/9 markets.

On MFE >= 8 ATR episodes, R5 preserves about 0.150 ATR more add-on return than R1 on an equal-market basis.

Decision:

> If a Resume-confirmed challenger is retained for later work, R5 is the more economically efficient delayed frontier point than R1.

This does not make R5 superior to R0.

## 10. Tail dependence remains material

Share of positive P1 / P2 add-on return contributed by the top 1% winning episodes:

- R0: 34.4%
- R5: 38.3%
- R1: 39.0%
- R4: 39.8%

After removing each market's single best P1 / P2 add-on episode, equal-market mean add-on return becomes negative for every candidate:

- R0: -0.0642 ATR
- R5: -0.1477
- R1: -0.1628
- R4: -0.1252

No candidate earns a stable-alpha or production claim.

Delayed confirmation is more, not less, dependent on the largest winners than R0.

## Decision

The preregistered economic admission test does not support requiring Resume confirmation before the primary P1 / P2 add-risk step.

Allowed conclusion:

> On this in-sample nine-market daily discovery set, P1 / P2 acceptance itself is sufficient for the tested second-entry timing decision. Waiting for R5 / R1 / R4 reduces failed-trend damage and improves daily left-tail behavior, but the confirmation tax removes more large-trend harvest than those protections recover. Equal-vol return does not improve, cumulative drawdown does not improve, and delayed policies fail badly in the mandatory 2015–2019 stress era.

### Current discovery baseline

Retain R0 Immediate as the current add-risk baseline:

> once P1 Wick Hold or P2 Reclaim is known at t+3, the tested architecture adds from 25% Probe to 100% Full without requiring a separate Resume trigger.

This remains in-sample and is not a production rule.

### Diagnostic survivor

Retain R5 Local Close as the best delayed-confirmation frontier point and a useful confidence state.

It is not promoted as the default second-entry gate.

### Not promoted

R1 Close Extreme does not earn enough extra risk reduction to compensate for the additional lost harvest.

### Benchmark only

R4 +0.5 ATR protects failed / small trends most strongly, but whole-sample and equal-vol return remain below R0 and 2015–2019 is the worst delayed result.

## Updated state-machine interpretation

The evidence chain is now:

Wyckoff Markup / Markdown
→ 25% Probe
→ Breakout
→ 3-bar Acceptance / Follow-through
→ P0 / P1 / P2 / P3
→ P0: add risk
→ P1 / P2: add risk at t+3 as current discovery baseline
→ P3: do not add
→ R5 / R1 Resume: confidence / diagnostic state rather than required add-risk gate
→ Deterioration / Giveback
→ Reduce Risk / Exit

The result does not say Resume evidence is useless.

It says:

> Resume is informative, but under the tested 25% → 100% second-entry architecture it arrives too late to pay for itself economically.

## Next research gate

Do not invent another Resume definition and do not tune t+3 / ATR thresholds.

The next non-redundant question is composition:

> Given R0 as the current discovery baseline, does combining the already-frozen Warning-First deterioration / giveback logic with this evidence-based add-risk architecture improve the complete system without sacrificing the gross trend edge?

That composition requires a separate preregistration.

A more conservative alternative is to freeze the current architecture first and challenge it on genuinely new data / weekly / prospective samples before further in-sample composition.

PR #80 remains Draft / open / unmerged.

Refs #78, #80, #76.
