# Issue #78 — Big Trend vs Failed Trend Feature Study audit

Date: 2026-09-15

## Purpose

This note independently audits the already-generated Big-vs-Failed finding against its preregistration. It does not change labels, windows, classifier semantics, or thresholds, and it does not create a Trend Quality composite.

The audit question is deliberately narrow:

> Which preregistered feature families have earned the right to survive into a later causal sizing study?

## Method checks

The analyzer is consistent with the preregistered information sets:

- E0 trailing features use rows strictly before the fresh trend-entry bar; the forward `move1[t]` on the entry row is not used in E0.
- E5 / E10 use only the first 5 / 10 completed post-entry daily moves and are therefore eligible only for post-entry sizing decisions.
- Large / Failed labels remain frozen at `MFE >= 8 entry ATR` and `MFE < 4 entry ATR`; the middle bucket is not relabeled.
- AUC is computed per market and then equal-market aggregated.
- Quintiles are formed within market before equal-market aggregation.
- Direction slices are diagnostic only; no Markup / Markdown-specific rule is created.

No material preregistration violation was found in the first-pass analyzer.

## Survivor classification

### Strong survivor — early directional price proof

**Verdict: STRONG SURVIVOR for a later sizing experiment, not an entry filter.**

The strongest evidence is the trend's own early causal price behavior after a probe is live.

All-years equal-market separation:

- E5 cumulative aligned move: mean AUC `0.776`, above 0.50 in `9/9` markets.
- E10 cumulative aligned move: mean AUC `0.842`, `9/9`.
- E5 directional path efficiency: `0.755`, `9/9`.
- E10 directional path efficiency: `0.815`, `9/9`.
- Low early giveback is useful but weaker: E5 `0.675`, E10 `0.681`, both `9/9`.

The E10 cumulative-proof quintiles are strongly ordered without selecting a cutoff:

- Large share: `6.8% -> 9.0% -> 17.2% -> 27.4% -> 49.9%`.
- Failed share: `87.8% -> 76.7% -> 64.6% -> 45.0% -> 16.5%`.
- Persistence + Gentle mean return: `-0.864 -> -0.182 -> +0.415 -> +1.405 -> +2.244 ATR`.

The result is also directionally broad. Cumulative aligned move has AUC `0.779 / 0.778` at E5 and `0.874 / 0.834` at E10 for Markup / Markdown respectively.

Most importantly, the feature does not merely identify the bad calendar era. Within the preregistered 2015–2019 stress slice, among eligible markets:

- E5 cumulative move: AUC `0.767`, `4/4` markets above 0.50.
- E10 cumulative move: AUC `0.905`, `4/4`.
- E5 directional efficiency: `0.747`, `4/4`.
- E10 directional efficiency: `0.858`, `4/4`.

This is the clearest feature family that passes the intended falsification.

#### Important limitation

This is not an entry-time forecasting result. The final Large label is based on eventual MFE, so early cumulative move / early MFE are mechanically related to the outcome. Their legitimate research use is operational:

> after a probe has already been opened, has the trend earned the right to receive more risk?

AUC alone cannot prove economic superiority of an E5 or E10 upgrade policy. That requires a separately preregistered causal sizing test.

### Weak survivor — E0 structural context

**Verdict: WEAK SURVIVOR as descriptive / initial-confidence context only. Not a hard gate.**

The best E0 features show modest but broad all-years separation:

- 126-bar direction-aligned range location: AUC `0.606`, `9/9` markets above 0.50.
- 252-bar range location: AUC `0.610`, `8/9`, but materially lower coverage.
- 63-bar directional displacement / entry ATR: AUC `0.592`, `9/9`.
- 63-bar range location: AUC `0.589`, `8/9`.
- 63-bar range escape: AUC `0.589`, `7/9`.
- 63-bar direction-aligned efficiency: AUC `0.577`, `8/9`.

The 126-bar range-location quintiles show useful end-to-end separation but are not perfectly monotonic: the lowest quintile has Large share about `7.9%` and Failed share `82.1%`, versus about `21.8%` / `64.9%` in the highest quintile.

The stress-slice evidence is not strong enough to promote E0 context further. In 2015–2019, long contiguous-history requirements leave only `1–2` eligible markets for many of the leading E0 features. That is too little cross-market evidence to claim the feature family passed the within-era falsification.

Therefore E0 structure can survive only as a low-complexity candidate for initial confidence, subject to later out-of-sample validation. It has not earned the right to block entries.

### Reject — absolute path efficiency as a standalone entry feature

**Verdict: REJECT.**

The preregistered unsigned `走很多、沒走遠` Efficiency Ratio does not separate future Large and Failed episodes reliably:

- ER20 AUC `0.524`.
- ER63 `0.494`.
- ER126 `0.438`.

The quintiles are non-monotonic and longer-window results can invert the expected relationship. Do not rescue this family by changing windows after inspection.

### Reject — simple regime churn / recent entry counts / raw trend occupancy

**Verdict: REJECT as standalone universal entry discriminators.**

Stage-change counts, fresh trend-entry counts, and raw directional-state occupancy sit around chance or below it in the all-years equal-market test, with poor quintile ordering and unstable era behavior.

The fact that some churn measures happen to look better in the small 2015–2019 eligible subset is not sufficient evidence, because they fail the broader cross-market test and would amount to rescuing a feature on the known failure era.

## What this study does and does not say

The evidence supports a specific architecture shift:

> Trend Quality should be treated primarily as something the trend **earns after entry**, rather than something a static E0 filter can confidently know in advance.

That does **not** mean E10 is automatically superior to E5. E10 has stronger separation but also delays risk deployment by another five daily moves. The opportunity cost of waiting is not measured by AUC and must be evaluated economically.

It also does not mean early MFE should simply become the score. Early MFE is partly tautological relative to the eventual-MFE label. Cumulative aligned progress and directional path efficiency are preferable mechanistic candidates for a next sizing test because they describe both progress and quality of path.

## Audit decision

The preregistered Big-vs-Failed study passes as a useful discovery study.

Feature-family status:

| Family | Decision | Allowed role next |
| --- | --- | --- |
| E5/E10 cumulative aligned progress | **Strong survivor** | post-entry sizing / upgrade research |
| E5/E10 directional path efficiency | **Strong survivor** | post-entry sizing / upgrade research |
| E5/E10 low giveback | **Weak-to-secondary survivor** | secondary confirmation only |
| E0 range location / medium-horizon directional displacement | **Weak survivor** | descriptive / frozen initial-confidence modifier candidate |
| E0 absolute Efficiency Ratio | **Reject** | none |
| E0 stage-change churn | **Reject** | none |
| E0 fresh trend-entry count | **Reject** | none |
| E0 raw directional occupancy | **Reject** | none |

## Next justified experiment

Do not build a multi-feature Trend Quality composite yet.

The next step should be a separately preregistered **proof-based sizing frontier** that keeps the existing probe architecture and compares a very small number of causal upgrade rules against the current age-only Persistence ramp.

At minimum it should answer:

1. Does adding risk after early cumulative aligned proof improve failed-trend damage versus large-trend harvest?
2. Does directional path efficiency add useful incremental information beyond cumulative progress, or is it redundant?
3. Is acting at E5 economically better than waiting to E10 once missed early participation is charged explicitly?
4. Does the same frozen rule remain useful in the 2015–2019 stress slice and later on new heterogeneous / weekly / prospective evidence?

No threshold, score weight, or production rule is selected by this audit. PR #80 remains Draft.
