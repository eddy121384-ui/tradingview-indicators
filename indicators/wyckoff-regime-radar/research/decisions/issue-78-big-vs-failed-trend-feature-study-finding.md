# Issue #78 — Big Trend vs Failed Trend Feature Study finding

Date: 2026-09-15

## Executive finding

The strongest first-pass discriminator is **not a static entry-time context variable**. It is the trend's own **early causal price proof after entry**.

Across the accepted nine daily markets:

- E5 cumulative direction-aligned move: equal-market mean AUC `0.776`, above 0.50 in `9/9` markets.
- E10 cumulative direction-aligned move: equal-market mean AUC `0.842`, above 0.50 in `9/9` markets.
- E5 directional path efficiency: AUC `0.755`, `9/9` markets.
- E10 directional path efficiency: AUC `0.815`, `9/9` markets.
- Early giveback is also useful but weaker: E5 AUC `0.675`, E10 AUC `0.681`, both `9/9` markets.

The best entry-close (`E0`) features are materially weaker. Structural range location / directional lead-in show some real separation, but nothing near E5 / E10.

The practical interpretation is:

> **Large trends are only modestly distinguishable before they start, but they tend to prove themselves quickly after the probe is live.**

This supports a research architecture of **probe first, then size up on causal price proof**, rather than trying to find a perfect pre-entry filter.

## Sample

Accepted Issue #76 event rows: `68,118`.

Completed known-start formal trend episodes: `1,624`.

Frozen labels:

- Failed / small (`MFE < 4 entry ATR`): `1,058` episodes.
- Large (`MFE >= 8 entry ATR`): `308` episodes.
- Middle (`4 <= MFE < 8`): `258` episodes.

No label threshold was optimized after outcomes were inspected.

## Entry-close evidence (E0)

The best all-years E0 features were:

| Feature | Equal-market mean AUC | Markets > 0.50 | Interpretation |
| --- | ---: | ---: | --- |
| 252-bar direction-aligned range location | 0.610 | 8/9 | Large trends tend to begin nearer the favorable side of the long range. Coverage is lower and temporal evidence is sparse. |
| 126-bar direction-aligned range location | 0.606 | 9/9 | Best broadly consistent static context feature in this pass. |
| 63-bar directional displacement / entry ATR | 0.592 | 9/9 | Large trends tend to have a stronger medium-horizon directional lead-in. |
| 63-bar range location | 0.589 | 8/9 | Similar structural-location signal at a shorter horizon. |
| 63-bar range escape / entry ATR | 0.589 | 7/9 | Genuine escape helps, but many valuable trends still start inside a wider range. |
| 63-bar direction-aligned efficiency | 0.577 | 8/9 | Some signal, but modest. |

The 126-bar range-location quintiles are illustrative:

- bottom quality quintile: Large-share `7.9%`, Failed-share `82.1%`, equal-market mean Persistence+Gentle return `-0.304 ATR`;
- top quality quintile: Large-share `21.8%`, Failed-share `64.9%`, return `+0.487 ATR`.

This is useful separation, but it is not a production gate and the middle quintiles are not perfectly monotonic.

### What did **not** work well at entry

The first-pass `走很多、沒走遠` absolute Efficiency Ratio is not a good standalone pre-entry discriminator here:

- abs ER 20: AUC `0.524`;
- abs ER 63: AUC `0.494`;
- abs ER 126: AUC `0.438`.

This supports the earlier visual concern that absolute path efficiency measures local smoothness better than whether a leg will become a major structural trend.

Simple recent classifier churn also failed as a universal pre-entry discriminator:

- stage-change counts: approximately `0.50` AUC;
- fresh trend-entry counts: approximately `0.48–0.51` AUC;
- directional-state occupancy under the preregistered `higher is better` hypothesis was below `0.50`.

Do not rescue these by changing windows after seeing the result.

## Early causal proof (E5 / E10)

The early-proof results are much stronger.

### Five completed daily moves after entry

| Feature | Equal-market mean AUC | Markets > 0.50 |
| --- | ---: | ---: |
| cumulative aligned move | **0.776** | **9/9** |
| early MFE | 0.763 | 9/9 |
| directional path efficiency | 0.755 | 9/9 |
| low giveback | 0.675 | 9/9 |

Equal-market median cumulative move by final label:

- Large: `+1.465 ATR`;
- Failed: `-0.408 ATR`.

Five-day cumulative-proof quintiles:

- Q1: Large-share `5.9%`, Failed-share `87.4%`, Persistence+Gentle return `-0.531 ATR`;
- Q5: Large-share `41.2%`, Failed-share `31.9%`, return `+1.582 ATR`.

### Ten completed daily moves after entry

| Feature | Equal-market mean AUC | Markets > 0.50 |
| --- | ---: | ---: |
| cumulative aligned move | **0.842** | **9/9** |
| early MFE | 0.820 | 9/9 |
| directional path efficiency | 0.815 | 9/9 |
| low giveback | 0.681 | 9/9 |

Equal-market median cumulative move by final label:

- Large: `+2.548 ATR`;
- Failed: `-0.292 ATR`.

Ten-day cumulative-proof quintiles are strongly ordered:

- Q1: Large-share `6.8%`, Failed-share `87.8%`, Persistence+Gentle return `-0.864 ATR`;
- Q2: Large-share `9.0%`, Failed-share `76.7%`, return `-0.182 ATR`;
- Q3: Large-share `17.2%`, Failed-share `64.6%`, return `+0.415 ATR`;
- Q4: Large-share `27.4%`, Failed-share `45.0%`, return `+1.405 ATR`;
- Q5: Large-share `49.9%`, Failed-share `16.5%`, return `+2.244 ATR`.

This is the clearest first-pass evidence in the study.

## Direction diagnostic

The early-proof result is not being created by only one direction.

For cumulative aligned move:

- E5: Markup AUC `0.779`; Markdown `0.778`.
- E10: Markup AUC `0.874`; Markdown `0.834`.

Directional path efficiency shows the same pattern:

- E5: Markup `0.770`; Markdown `0.758`.
- E10: Markup `0.844`; Markdown `0.807`.

No separate long / short policy is justified or allowed.

## 2015–2019 stress slice

The key question was whether a useful feature merely labels the bad calendar era or actually separates good and bad trends **inside** it.

Entry-time E0 evidence is underpowered in this slice because there are only `25` Large episodes in the full 2015–2019 sample, and long contiguous trailing-window requirements reduce usable E0 observations further. Therefore no strong E0 claim is made for this era.

The early-proof features do retain strong within-era separation among eligible markets:

- E5 cumulative move: AUC `0.767`, `4/4` eligible markets above 0.50;
- E10 cumulative move: AUC `0.905`, `4/4`;
- E5 directional efficiency: AUC `0.747`, `4/4`;
- E10 directional efficiency: AUC `0.858`, `4/4`;
- E10 low giveback: AUC `0.763`, `4/4`.

For those eligible 2015–2019 samples:

- E5 median cumulative proof: Large `+1.600 ATR`, Failed `-0.075 ATR`;
- E10: Large `+2.475 ATR`, Failed approximately `0.000 ATR`.

This does **not** mean 2015–2019 is solved. It means that even in the bad era, the few trends that eventually become large tend to prove themselves early, while many surviving failed trends do not.

## Important causality / interpretation caveat

E5 / E10 results are **not entry prediction**.

They use information observed after the position has already been probed. They are only eligible for post-entry sizing decisions.

Also, the final Large label is defined by eventual MFE, so early MFE / cumulative progress is mechanically related to the outcome. That is not a forecasting miracle. The useful question is operational:

> after 5 or 10 completed daily moves, can the system distinguish trends that deserve more exposure from trends that still have not earned it?

The answer in this in-sample study is clearly more promising than trying to solve the problem entirely at entry.

E5 / E10 failed samples are conditional on the formal trend still being alive at those decision times. Shorter failed episodes have already exited and therefore correctly do not enter a decision that could not have existed in real time.

## Current survivor ranking

### Strong survivor for the next sizing study

**Early directional price proof**, especially cumulative direction-aligned displacement plus path efficiency.

### Secondary context survivor

**Medium / long range location and medium-horizon directional displacement**. These may help set initial confidence but are too weak to act as hard entry gates on current evidence.

### Downgraded / rejected as standalone entry discriminators

- absolute Efficiency Ratio;
- simple formal-stage churn counts;
- fresh trend-entry counts;
- raw directional-state occupancy.

## What should happen next

Do **not** build a large multi-feature model yet.

The next justified experiment is a separately preregistered, very small causal sizing frontier using the existing probe architecture, for example:

1. start from the current Persistence + Gentle probe;
2. keep E0 context descriptive or at most a frozen low-complexity initial-confidence modifier;
3. test whether position upgrades conditioned on **early cumulative proof / early directional efficiency** improve the trade-off between failed-trend damage and large-trend harvest;
4. compare against the current age-only Persistence ramp and the already studied opposition-entry brake;
5. freeze any survivor before new heterogeneous / weekly / prospective OOS validation.

No production Trend Quality score or parameter is selected by this finding.

## Reproducibility / artifacts

Analyzer:

`indicators/wyckoff-regime-radar/research/analyze_issue78_big_vs_failed_features.py`

Committed compact evidence:

- `research/data/derived/issue78-big-vs-failed-separation.csv`
- `research/data/derived/issue78-big-vs-failed-quintiles.csv`
- `research/data/derived/issue78-big-vs-failed-direction.csv`

The analyzer also emits the episode-level feature table and per-market detail when run against the accepted nine Issue #76 Pine-log files. Those larger local artifacts are reproducible from the frozen accepted inputs and are not required to change classifier semantics.

## Allowed conclusion

> **The frozen classifier's largest remaining weakness is not best addressed by a static calendar/regime filter. Entry-time structure offers modest information, but the trend's own first 5–10 daily moves provide much stronger, cross-market causal evidence about whether it is developing into a large trend. The next research step should therefore test proof-based position upgrades, not another hard pre-entry filter.**
