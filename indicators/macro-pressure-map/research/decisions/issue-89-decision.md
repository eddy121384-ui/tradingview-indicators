# Issue #89 decision — ex-ante V6.6 regime allocation policy

Final category: **`inconclusive_insufficient_evidence`**

Detailed rationale: **`ex_ante_policy_has_material_full_history_and_pre2020_switching_value_but_switching_value_reverses_post2019_and_full_history_drawdown_is_worse_than_the_exposure_matched_static_control`**

The Growth × Inflation allocation matrix was fixed before Issue #89 portfolio results were viewed. It was not fitted to SPY/TLT/GLD returns and was not retuned after results. V6.6 remained frozen.

At 5 bp, the regime policy produced full-history CAGR **9.90%**, Sharpe **0.966**, max drawdown **-27.35%**, and Calmar **0.362**. It beats fixed 60/40 and fixed 40/40/20 on full-history CAGR and Sharpe, but that comparison alone does not identify switching value. Annualized turnover is about **5.96x/year**, with 916 rebalances and about **5.60%** cumulative transaction-cost drag.

Against a realized-exposure-matched static control, full-history switching adds **+1.71 pp CAGR** and **+0.090 Sharpe**, but worsens maximum drawdown by about **2.00 pp**. Pre-2020 adds **+2.99 pp CAGR** and **+0.229 Sharpe**, with max drawdown improving by about **5.28 pp**. Post-2019 reverses: **-0.43 pp CAGR**, **-0.081 Sharpe**, **-1.80 pp** drawdown delta, and **-0.036** Calmar delta.

The largest full-history positive episode is Slowdown / Disinflation from 2008-10-02 through 2009-01-26 and represents only about **6.3%** of total positive episode contribution. Removing it and rerunning the path with a fresh exposure-matched leaveout control still leaves about **+1.14 pp CAGR** and **+0.022 Sharpe**. Pre-2020 likewise remains positive after removing its largest winner.

Post-2019 is already negative before leaveout. Its largest positive episode is Reflation / Inflation Rising from 2020-11-23 through 2021-05-21; removing it worsens the residual to about **-1.29 pp CAGR** and **-0.143 Sharpe**.

So this is not merely allocation-mix value and not merely one lucky episode. But the same ex-ante switching policy is materially positive before 2020 and negative after 2019. Full-history drawdown is also worse than the exposure-matched static control. That rules out `useful_regime_switching_policy`, `risk_management_value_only`, `allocation_mix_value_only_no_switching_value`, and `no_material_policy_value` as faithful summaries.

The bounded final category is therefore **`inconclusive_insufficient_evidence`**. Do not retune the matrix to rescue recent history. Do not call the result untouched OOS evidence or a validated production allocator.
