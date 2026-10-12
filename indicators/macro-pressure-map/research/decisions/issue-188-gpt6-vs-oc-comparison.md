# #188 blind independent audit vs OC — AFTER independent findings frozen

## Chronology and firewall

1. GPT-6 independent prereg on separate branch: `b691714349279e18d6220e280f59261b9ca80a00`.
2. GPT-6 independent results **frozen**: `edb9af160acf7aab1b8b27ac8daa8cba63c513c8`, before viewing OC's #188 finding, models or generated results.
3. Only afterward fetched OC `research/issue-188-deep-history-edge-attribution` findings and JSON from final #188 study (OC prereg `0d28ba13b0f37333a954619a043999e252545761`).
4. This file is a post-unblinding comparison. Independent result/parameter choices not retroactively modified.

## Agreement — strong replication

- **Corrected original DH P-MAX 721 months**: GPT-6 and OC both 8.74743266% 2bp-post-cost CAGR, Sharpe 0.5874855, MaxDD −17.0513497%. My row-by-row independent return replay matched #183 exactly pre-cost.
- **ETF P-ETF strict**: both independently 240 months, 8.15831984% post-cost CAGR, Sharpe 0.8528216, MaxDD −16.4530859%. GPT-6 also compared every month to frozen #180 impl_post (max error 1.39e−17).
- **ETF circular shift placebo**, all 239 permutations: results reproduce EXACT OC percentile values — CAGR 95.3975, Sharpe 97.4895, MaxDD 97.0711, Ulcer 97.9079. This is strong independent confirmation of the historical calendar alignment calculation.
- **Long-history circular shift placebo**, 720 shifts: same descriptive gross percentile values as OC's net very nearly/for the reported metric ranks exactly — CAGR 97.6389, Sharpe 98.4722, MaxDD 98.75, Ulcer 96.9444. Important: not OOS; missing-asset policy caveat.
- Static-neutral baseline reproduced 8.3310678% gross / −24.0486% MaxDD. Common Cash-fill benchmark is ~8.2168% gross and performs worse than DH; bootstrap/policy decomposition favor preserving macro information as an *in-sample* hypothesis.
- Both audits find full nine-state DH materially ahead of simple single-axis or fixed-equity inflation-defense strategies on historical ETF data.
- Both audits agree investability and PIT macro-vintage problems remain; no production authorization or merge.

## Non-identical experiments / why some numbers differ

- **Fixed mean-weight control:** GPT-6 used a fixed portfolio calibrated to **average ACTUAL APPLIED sleeve weights** then Cash-fill on missing sleeves. OC used preregistered period-specific target means with **proportional redistribution** for missing sleeves. Hence P-MAX result differs substantially (GPT-6 ~7.855% vs OC D ~8.099% net CAGR) and OC D's mean Equity on early history deviates +1.68pp from DH. ETF results match direction and nearly levels (GPT-6 7.4805% vs OC 7.4773%).
- **Single-axis ablation:** GPT-6 calculated an EQUAL-weight mean of all three frozen matrix rows on the removed axis; OC Growth-only uses HISTORICAL state-frequency weights and inflation-minimal switches Treasury duration to cash. These are not the same strategies! Compare directional robustness, not individual CAGR cells. GPT-6 also tested an equal-row Inflation-only projection while OC has a different median projection labeled nonpolicy. Across both designs, full DH performed better.
- **Defensive basket:** GPT-6 tested separate B-2 confirmation on raw Inflation axis; OC's predeclared gate uses its implementation of frozen I_High confirmation; OC also has different investability/subsetting in its long-history E2. ETF E2 levels therefore differ (7.079% GPT-6 vs 7.385% OC), but both underperform full DH and draw down to ~−27%.
- **Fixed-control transaction costs:** GPT-6 charged 2bp only when fixed TARGET weights changed; this omits monthly turnover necessary to restore unchanged target weights after market drift. OC explicitly models drift-and-rebalance cost every month; thus their fixed-neutral and fixed-mean results are ~0.003pp/yr lower. The independent test **slightly favors controls**, so it does not manufacture DH superiority.
- **Bootstrap comparisons:** GPT-6 ETF 90% stationary-block 24m bootstrap (2,000 reps, xorshift seed 41861) on DH vs period-mean (CAGR Δ+0.6778pp, CI [−0.0741,+1.4870]) and DH vs equal-row Inflation projection (Δ+0.5639pp, CI [−0.0011,+1.1490]) both overlap zero. OC ETF bootstrap is for DH vs nominal fixed-neutral Cash-fill (+0.6346pp, CI [−0.1543,+1.4720]) — different comparator and seed. All support *uncertainty* in the strict ETF-period sample.
- OC completed significantly more formal work: Shapley policy/availability, detailed 2008/cash-rate-equity attribution, stress, 5,000-rep P-MAX bootstrap, leave-one-crisis-out, independently executable test suite, and bitwise replay. GPT-6 direct connector sandbox diagnostics were targeted, not a second full implementation.

## Verdict / what CC got right and wrong

- CC's criticism of unequal pre-ETF missing-asset rules is valid and must be preserved; its claim that all nine-state behavior could be reduced to simple inflation-only cash switching is **not substantiated by either test set**.
- Both auditors find evidence that exact *historical calendar alignment* is valuable, and fixed average asset exposure is not a sufficient explanation.
- OC official prereg formal verdict: `deep_history_macro_information_supported`, **in-sample**. GPT-6 provisional economic/deployment verdict: `deep_history_evidence_mixed_or_inconclusive` for **live alpha**. THESE ARE NOT NECESSARILY CONFLICTING: one tests retrospective signal specificity, the other requires uncontaminated out-of-sample/vintage observability to infer investability.
- The 2008 return contributions are not exclusive proof of stock-market timing causal ability: OC reported DH–C pre-cost arithmetic family contributions Equity +0.2174pp/year, Cash +0.1252, Rates +0.0422, Real −0.1038 (sum +0.2810). This differs from 0.53pp geometric CAGR improvement due to compounding and portfolio-path effects and should not be conflated as one-to-one contribution share.
- Real issues: macro release/vintage revisions, sample-selected structural weight matrix, large cross-era concentration, ETF-period bootstrap crossing zero. These are NOT solved by strong descriptive placebo percentiles.

## Agreed next action

Do not modify nine-state policy, thresholds, caps or portfolio in response to #188. Next study should focus on **true macro vintage/time-of-publication feasibility**, frozen weights, ETF-era realistic trade execution, and only then walk-forward/OOS evidence. Preserve independent finding and OC finding as two separate references; don't merge research branches into main.

`production_authorized=false`.
