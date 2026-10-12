# #188 GPT-6 independent audit — preregistration

## Blindness and scope
- Created from parent #187 final `e61b9a31feb08ab757d34d77cc841fda70c77bcc`, NOT from OC's #188 result branch.
- Never read OC's new #188 code/results/finding until this audit results commit is frozen.
- Source datasets: frozen #174 nine-sleeve research returns, #176 hardened S&P and investable oil, #177 policy tiers, #178 weight-matrix and benchmarks, #180 ETF proxy monthly returns, #183 corrected applied states and returns. Read #186/#187 prior findings only as background.
- Pure research: `production_authorized=false`; no main changes; do not merge.

## Primary audit questions
1. Can independently reproduce original corrected #183 721-month A return sequence, not just its aggregate?
2. Relative to a fixed equal-applied-mean-weight control on identical calendar and return rows, how much is earned by the actual alignment of DH states?
3. Do non-zero circular shifts of the frozen DH state/weight chronology produce similar results? Same common asset availability and costs.
4. Do Growth vs Inflation separate 3-state projections reproduce 9-state risk/reward?
5. Can a simpler fixed 45% Equity plus inflation-driven duration/cash selector reproduce defensive behavior?
6. How much does data availability / benchmark methodology alter long-history conclusions?

## Frozen panels
- P-MAX: intersection with corrected #183 rows (original 721 monthly returns 1966-05 through 2026-08; explicitly disclose 3 omitted calendar months).
- P-ETF: strict 2006-06 through 2026-08, using existing #180 ETF proxy stream, intersect exact #183 timeline and source validity; report actual row count / coverage.
- P-FULL: 2000-09 through 2023-06 where all original research sleeves available.

## Portfolio mechanics
- All comparison legs use same month's asset returns and same month label.
- Baseline A = corrected #183 monthly return, with independently reconstructed #178 matrix+availability engine checked before any candidate outcome.
- Original fixed neutral: 25/12/8/8/14/8/6/4/15 (S&P/Nasdaq/Russell/2Y/10Y/long/gold/oil/cash).
- Equal-availability fixed controls: (i) missing sleeve's target allocated to Cash (cash-fill); (ii) available sleeve weights proportional normalization incl original Cash (pro-rata). Disclose that corrected A availability rule is sometimes distinct and must be reconstructed, not forced to be the same.
- Exposure-matched fixed: time-average actual A applied weights, computed weights-only in each panel (retrospectively calibrated, NOT implementable OOS). Apply exactly the same frozen availability and if needed disclose secondary handling differences. No optimized weights.
- Risk-matched fixed neutral: convex neutral+Cash weight chosen to match *in-sample* annualized volatility of A, explicitly retrospective; include maxdd and CAGR; this is a diagnostic, not fair ex-ante rule.
- Ablations: reduce 9x9 matrix to three Inflation-only states and three Growth-only states by equally averaging all three rows on excluded axis **BEFORE returns**, preserving sum=100 and caps if possible. Monthly B-2 confirmation on one raw axis t-1/t-2; hold previous if unconfirmed; do not tweak weights or compare on missing sample.
- Mechanism model: fixed Equity 25/12/8, defensive baseline 2Y8/10Y14/long8/gold6/oil4/cash15; I_High confirmed -> 2Y10/gold10/oil5/cash30, 10Y/long=0. All rows sum100. Confirmed I-only B-2 logic same timing.
- Circular timing placebo: shift the *applied A state sequence* by ALL k=1..n-1 using modulo over panel (joint Growth/Inflation states); convert shifted states to frozen 9-state weights with the same period-appropriate missing-asset handler, no signal recomputation or optimization. Mark boundary wraps and shifts as dependent placebo, not independent p-values. Report numerical percentile ranks and time/missing-weight exposure mismatch. For strict ETF all proxies exist; P-MAX missing-data comparability must be disclosed.

## Metrics / sensitivity
- CAGR `(product(1+monthly_return))^(12/n)-1`, volatility monthly population sd ×sqrt12, cash-excess Sharpe-like (mean monthly r−cash divided by sd monthly excess ×sqrt12), MaxDD compounded wealth high-watermark, worst month; annual one-way turnover 0.5 sum absolute weight changes ×12/(n−1); 2bp × turnover in strict ETF as frozen #180.
- Evaluate 1966–1979, 1980–2007, 2008–2019, 2020–2026 segments; no threshold retune.
- Exposure attribution from weights-only avg by asset family and Cash.
- Robustness: +1,+2,+3 macro-signal delay where feasible, not true vintage PIT.
- Dynamic A and controls with compatible costs, same valid months; explicitly display gross-to-gross and net-to-net only.
- No confidence significance claims from naive iid Sharpe; bootstrap if feasible, otherwise labeled not performed.
- Prefer decision based on exposure and timing-specific incremental *positive* benefit, not merely "does not hurt". Equal/negative difference is not evidence of added value.

## Prior pitfalls to catch
- #178 old backtest accidentally levers up to 109% and must NEVER be used.
- Original static benchmark vs corrected policy have different missing-asset rules; compare both, do not call the artifact causal superiority.
- 1960s synthetic assets/pre-1971 gold, pre-2000 investable oil, Nasdaq price-only, S&P fallback; ETF strict sample is critical.
- Model weights designed from SAME past outcomes, therefore retrospective and not true OOS.
- t+1 reconstructed DH data does not imply real time observability; vintage PIT still unresolved.

## Sequence
1. Read parent files / check schema, create and commit THIS prereg.
2. Calculate the independent audit from parent artifacts only.
3. Commit finding to this separate branch BEFORE reading OC #188 outputs.
4. Compare independently with OC after their published finding, preserving disagreements.

One failed recomputation means mark that leg inconclusive, never quietly fix based on output tuning.
