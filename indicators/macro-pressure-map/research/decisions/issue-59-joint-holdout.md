# Issue #59 — Joint-axis post-2019 exploratory evaluation

Status: **JOINT-AXIS EXPLORATORY EVALUATION COMPLETE — NON-OVERLAPPING EVENTS**

Historical note: this file keeps the old `issue-59-joint-holdout.md` filename so existing links do not break. Its current interpretation is exploratory reused-era analysis, not untouched holdout validation.

## Evidence boundary

The 2020–2026 period is **not an untouched holdout** for the synchronized-transition hypothesis. Earlier Issue #59 historical and out-of-component diagnostics had already inspected that era before the joint hypothesis was selected.

Therefore the post-2019 result below is an **exploratory frozen-threshold evaluation**, not decision-grade OOS validation.

## Corrected event design

Threshold-definition period:
- 2008-06-02 through 2019-12-31

Development outcome evaluation:
- ends 2019-12-02
- final 20 trading rows are purged so no forward-20d development outcome uses 2020 prices

Post-2019 exploratory era:
- 2020-01-02 through 2026-08-14

Frozen cuts:
- GPI d20: low `-21.06`, high `+19.53`
- IPI d20: low `-21.20`, high `+22.51`

Joint states:
- **Reflation impulse** = GPI d20 high AND IPI d20 high
- **Slowdown / disinflation impulse** = GPI d20 low AND IPI d20 low

True state entries are detected on the complete chronological frame before period slicing. A shared **20-trading-row embargo** is applied across positive and negative events so accepted forward-20d windows do not overlap.

Non-overlapping joint event counts:
- development: **23** reflation vs **33** slowdown/disinflation
- post-2019 exploratory: **15** vs **15**

## Raw joint contrast

Reflation minus Slowdown/Disinflation forward-20d spread:

| Outcome | Development joint | Development 95% CI | Post-2019 exploratory joint | Exploratory 95% CI |
|---|---:|---:|---:|---:|
| US10Y yield | +5.87 bp | [-3.88, +15.69] | **+18.81 bp** | **[+2.19, +35.60]** |
| US02Y yield | +3.30 bp | [-3.38, +10.11] | **+17.68 bp** | **[+2.80, +33.19]** |
| ZN1! | -0.44% | [-1.11%, +0.24%] | **-1.18%** | **[-2.15%, -0.21%]** |
| TLT | -1.35% | [-3.23%, +0.42%] | -2.03% | [-4.29%, +0.40%] |
| USDJPY | +0.57% | [-0.92%, +2.17%] | +0.62% | [-1.30%, +2.59%] |
| EURUSD | -0.25% | [-1.83%, +1.39%] | +0.31% | [-1.19%, +1.86%] |

The post-2019 Treasury association remains economically coherent, but it is reused-era historical evidence only.

## Why the old incremental claim is withdrawn

The first interpretation compared the raw joint spread with separately embargoed GPI-only and IPI-only spreads. Those event sets use different dates and sample sizes, so a larger raw joint point estimate does **not** prove that the second axis adds information.

A later matched conditional study fixes one anchor-event universe and tests the nested confirmation lift directly. The values below are rounded from the committed durable artifact `issue-59-matched-incremental.json`, which preserves exact anchor-only spreads, confirmed spreads, confirmation lifts, and confidence intervals for US10Y, US02Y, ZN1!, and TLT. Local files under `research/generated/` are disposable rerun products and are not repository evidence.

| Anchor | Outcome | Anchor-only spread | Confirmed spread | Confirmation lift | Durable 95% CI |
|---|---:|---:|---:|---:|---:|
| GPI | US10Y | +11.10 bp | +12.48 bp | +1.38 bp | [-17.98, +23.78] |
| GPI | ZN1! | -0.64% | -0.74% | -0.11% | [-1.40%, +1.08%] |
| IPI | US10Y | +10.79 bp | +8.51 bp | -2.28 bp | [-22.50, +15.20] |
| IPI | ZN1! | -0.59% | -0.61% | -0.02% | [-1.16%, +1.26%] |

All durable-recorded confirmation-lift intervals for **US10Y, US02Y, ZN1!, and TLT** cross zero in both the development and post-2019 exploratory samples.

Evidence:
- `issue-59-matched-incremental.md`
- `issue-59-matched-incremental.json`
- `matched_incremental_validation.py` plus the Pine Log hashes in `../REPRODUCIBILITY.md` provide the rerun path; generated local outputs are not committed evidence

## Correct interpretation

What Issue #59 supports:
- synchronized GPI+IPI states can identify an interesting Treasury / ZN historical subset;
- transition/alignment remains useful descriptive information for understanding what the market is pricing;
- the non-overlap and leakage fixes make the raw event description cleaner.

What Issue #59 does **not** support:
- calling 2020–2026 an untouched holdout for this hypothesis;
- claiming the joint state has proven incremental predictive information beyond GPI or IPI alone;
- a universal cross-asset rule;
- a stable FX edge;
- a complete trading strategy or causal macro forecast.

## Joint-axis verdict

**KEEP GPI+IPI interaction as a descriptive / research feature, but withdraw the claim that incremental predictive value is validated.**

The generator `joint_holdout_validation.py` now preserves the same exploratory reused-era boundary on rerun. Any future predictive hypothesis about synchronized GPI+IPI movement should be frozen in advance and tested on genuinely unseen future data.
