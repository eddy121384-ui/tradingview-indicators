# GPT-6 independent blind #188 audit — frozen findings

**Branch:** `research/issue-188-gpt6-independent`
**Parent:** `e61b9a31feb08ab757d34d77cc841fda70c77bcc` (#187 final)
**Prereg SHA:** `b691714349279e18d6220e280f59261b9ca80a00`
**BLIND:** No OC Issue #188 results, prereg or findings were inspected prior to committing this finding. Original parents #160/#174/#176/#177/#178/#180/#183 were source only.
**Scope:** Independent targeted diagnostics in JS connector sandbox, not a full independent packaged test suite; results were not compared to an OC result yet.
`production_authorized=false`. No merge/main/Pine modifications.

## Executive verdict

**The strongest simple-portfolio alternatives tested do not replicate the full historical Deep-History profile.** On fully tradable 2006–2026 ETF proxy history, the actual 9-state weights beat fixed-neutral, same-period fixed mean weights, equal-row 3-state Growth/Inflation projections, and one predeclared fixed-45%-Equity Inflation-defensive selector in BOTH gross-quality CAGR and MaxDD.

**Crucially, actual signal timing ranks unusually well against circular shifts**: ~95.4th percentile post-cost ETF CAGR and ~97–98th percentile Sharpe, MaxDD and Ulcer Index against 239 alternatives. Long-history *pre-cost* separate shift diagnostic similarly ranks ~97–99th percentile against 720 alternatives, subject to serious missing-sleeve confounding.

This is **in-sample descriptive evidence of alignment specificity**, NOT independently tested vintage/OOS alpha. The underlying state→weight map was constructed after observing the same sample; retrospective mean/risk-matched benchmarks are not ex-ante investable.

## Exact source/replay checks

- Corrected #183 structural P-MAX 721 monthly portfolio returns recreated **exactly** from #174 research sleeves + #176 hardened S&P/oil + #177 tiers/bias + #178 frozen matrix and corrected missing-return policy (max abs monthly difference `0`). No buggy leveraged #178 stream.
- Frozen original fixed neutral P-MAX CAGR 8.3310678%, MaxDD −24.04862% reproduced to machine precision.
- ETF strict #180 implementation `impl_post` recreated with max abs monthly error **1.39e−17** over 240 months (2006-06→2026-08, inherited omitted months), 2bp × one-way turnover.
- P-FULL #183 return stream recreated with max abs difference 0.
- This audit did not reproduce all of OC's #188 requested extras; missing items explicitly at bottom.

## Long-history P-MAX (721 applied months, 1966-05→2026-08), hypothetical 2bp cost, common return inputs

| Strategy | CAGR | Vol | Cash excess Sharpe-like | MaxDD |
|---|---:|---:|---:|---:|
| Full DH corrected | **8.7474%** | 7.0847% | **0.5875** | **−17.0513%** |
| Frozen neutral original pro-rata availability | 8.3309% | 8.1299% | 0.4740 | −24.0486% |
| Frozen neutral unavailable-asset → Cash | 8.2167% | 7.4999% | 0.4930 | −24.0486% |
| Constant *actual mean applied* sleeve weights, missing-asset → Cash | 7.8547% | 6.7658% | 0.4897 | −21.1604% |
| Growth-only 3-state equal-mean 9-row projection | 8.0971% | 7.0714% | 0.5030 | −19.5698% |
| Inflation-only 3-state equal-mean 9-row projection | 8.4163% | 6.9365% | 0.5544 | −21.5103% |
| Fixed 45% Equity, inflation-regime defensive-basket switch | 8.2133% | 7.5704% | 0.4894 | −26.8621% |

These three-state projections average the three frozen nine-state target rows in the excluded dimension **equally** (weights-only) and use separate two-consecutive-month *axis-specific* confirmation. In pre-ETF years, candidate missing sleeves go to Cash whereas faithful DH uses the corrected original partial-availability engine. Therefore **P-MAX cross-candidate differences are informative but NOT a perfectly isolated ablation**.

Historical gross corrected DH = 8.754741%, original static neutral = 8.331068% (no costs). Do not confuse with numbers above.

## Research P-FULL (2000-09→2023-06, 274 months), all original sleeves available; hypothetical uniform 2bp

| Strategy | CAGR | MaxDD |
|---|---:|---:|
| Full DH | **5.9269%** | **−17.0513%** |
| Original static neutral | 5.6574% | −24.0486% |
| Fixed P-FULL mean actual exposure | 5.3516% | −23.6888% |
| Growth-only projection | 5.5117% | −19.5698% |
| Inflation-only projection | 5.8433% | −21.5103% |
| Fixed45% Equity + inflation defensive basket | 5.2025% | −26.8621% |

In this 274-month P-FULL panel, full DH minus inflation-only is only +0.0836pp CAGR; caution about claiming Growth's independent increment.

## Strict ETF P-ETF (240 applied months, 2006-06→2026-08), **2bp turnover**, consistent proxy and return semantics

| Strategy | CAGR | Vol | Cash excess Sharpe-like | MaxDD | Ulcer Index |
|---|---:|---:|---:|---:|---:|
| **Full DH** | **8.1583%** | 7.6594% | **0.8528** | **−16.4531%** | **3.3381%** |
| Fixed neutral | 7.5270% | 8.1550% | 0.7350 | −24.1767% | 5.0331% |
| Fixed DH mean target exposure (2006+ weights only) | 7.4805% | 8.0325% | 0.7395 | −24.4759% | 5.0437% |
| Growth-only 3-state projection | 7.4476% | 7.5844% | 0.7746 | −19.5185% | 4.3352% |
| Inflation-only 3-state projection | 7.5944% | 7.5712% | 0.7934 | −21.5555% | 3.9684% |
| Fixed 45% Equity + inflation defensive switch | 7.0787% | 8.4249% | 0.6641 | −27.0674% | 5.3693% |
| In-sample volatility-matched neutral+Cash (93.9028%/6.0972%) | 7.1795% | 7.6594% | -- | -- | -- |

This fixed-Equity defensive candidate is *one particular predeclared basket*, not a proof that all such strategies fail. Its infl.-defensive basket = Equity 25/12/8, 2Y10, 10Y0, Long0, Gold10, Oil5, Cash30; outside inflation High the original neutral basket. In both cases portfolio total=100%.

## Timing shift E0: N−1 tests of FROZEN applied nine-state sequence

All non-zero circular shifts, no favorable subset selection; preserve sequential state ordering except the wrap boundary. ETF all sleeves available, so availability mismatch does not drive the result.

**P-ETF 239 non-zero shifts, 2bp one-way turnover for ALL cases**:

| Metric | Actual | Placebo median | Actual percentile |
|---|---:|---:|---:|
| CAGR | 8.1583% | 7.4396% | **95.40th** |
| Sharpe | 0.8528 | 0.7190 | **97.49th** |
| MaxDD | −16.4531% | −24.8203% | **97.07th** |
| Ulcer Index (lower better) | 3.3381% | 5.2454% | **97.91th** |

P-MAX 720 nonzero shifts **pre-cost** (separate calculation; shifted states put through exact corrected original asset-availability policy):
- CAGR ~97.64th percentile
- Sharpe ~98.47th percentile
- MaxDD ~98.75th percentile
- Ulcer Index ~96.94th percentile.

For P-MAX, state/portfolio interactions with missing sleeves vary by offset. Do NOT treat the P-MAX percentile as an apples-to-apples independent timing test without an explicit exposure-distribution audit. All circular shifts are dependent and *neither* result is a p-value or OOS demonstration.

## ETF bootstrap sensitivity (not genuine OOS)

Stationary block bootstrap on **paired monthly** ETF returns: expected block 24 months; 2,000 resamples; deterministic xorshift32 seed 41861; recompute annualized geometric return of each sampled pair and subtract. This assesses instability within this historical sample; it does NOT correct model-selection bias/vintage bias.

| Contrast (DH − control), CAGR pp/year | Observed | 90% bootstrap interval |
|---|---:|---:|
| vs fixed P-ETF mean applied weights | **+0.6778** | **[−0.0741, +1.4870]** |
| vs inflation-only 3-state projection | **+0.5639** | **[−0.0011, +1.1490]** |
| vs volatility-matched neutral+Cash | **+0.9789** | **[+0.3364, +1.6672]** |

First two intervals **include zero**, narrowly so for inflation. Do not call 90%-CI threshold significant model evidence; many prior issues explored related hypotheses on the same sample.

## Interpretation and disagreements to test against OC (before reading OC result)

1. **CC's most severe simplification claim is not confirmed by these experiments**. Inflation-only captures meaningful improvement vs Growth-only, but 9-state DH beats it on ETF CAGR, Sharpe and drawdown. The particular fixed-45%-Equity inflation-defense proposal is much worse. This does NOT rule out other duration selectors.
2. **Exposure-only explanation is insufficient in the tested sample**: constant exact same-period averaged applied sleeve weights suffer more drawdown and lower returns, especially ETF era. However using 20-year retrospective average benchmark is itself look-ahead calibration.
3. **Calendar alignment is nontrivial within the historical sample**: strong original-vs-shift percentile on ETF history. Still **cannot claim alpha** from post-selected state matrix and reconstructed/revised macro signals.
4. **Cross-era/uncertainty is a central caveat**: P-FULL whole-DH minus Inflation-only CAGR is merely 0.084pp; ETF DH minus Inflation-only 0.564pp. A positive aggregate does not ensure consistent marginal information.
5. **Known data-availability asymmetry affects early-era drawdown conclusions.** Independent gross E1-era static neutral MaxDD −19.01% vs cash-fill neutral −14.16%; DH E1-era MaxDD −6.35%. Under comparable missing-sleeve treatment, part of early neutral disadvantage disappears, but not all.

## Missing / not completed independently

- No packaged local replay source/check-in or second-language mirror tests for this independent audit. The computations ran directly over SHA-pinned GitHub parent CSVs; archived figures + exact construction here. OC's dedicated #188 code can be inspected AFTER blind report frozen.
- Did NOT independently perform a full per-sleeve regime/excess-P&L attribution, factor-by-factor Shapley decomposition, CDaR95 and leave-one-crisis-out on each leg.
- P-MAX placebo is gross; P-ETF placebo is post-cost. Do not mix ranks as same metric.
- Did NOT independently construct true point-in-time macro vintages. All comparisons inherit revised economic data and historical investability limitations.
- Did NOT examine OC's #188 output before committing this report.

## Decision before OC comparison

**Provisional:** `deep_history_evidence_mixed_or_inconclusive` for real-world tradable alpha; **historical alignment specificity is positive and merits additional validation**. Reject stronger assertions of both `no macro edge` and `proven timing alpha`.

Most valuable next work: true vintage/announcement-time validity and strict ETF-era independent out-of-sample / walk-forward policy construction, before changing allocation. Keep #183/#187 frozen.

No deployment authorization.
