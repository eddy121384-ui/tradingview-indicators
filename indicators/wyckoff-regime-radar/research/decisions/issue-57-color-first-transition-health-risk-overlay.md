# Issue #57 — Color-first regime trading + Transition Health risk overlay

Status: **REUSED-DATA STRATEGY-PROXY DIAGNOSTIC ONLY**.

This decision is frozen before inspecting any strategy-proxy outcome. It does not modify production Pine and does not claim a deployable trading strategy.

## Question

The default visual background is `單色｜正式主導`. Does using that Formal color immediately as the primary directional regime, with Transition Health only as an early risk-management overlay, improve the realized price path versus waiting for the +3 Healthy marker?

The purpose is specifically to test the user's observation that the background color is earlier and more persistent than the +3 Transition Health marker.

## Frozen color-direction mapping

Use the current v0.6 `formal_id` only:

- stages **1 / 2 / 3** (`吸籌 / 拉升 / 再吸籌`) => **bull color = +1**;
- stages **4 / 5 / 6** (`派發 / 崩跌 / 再出貨`) => **bear color = -1**;
- `formal_id == 0` => **flat = 0**.

No Candidate, Pace, price, volatility, or support/resistance filter is added.

## Frozen execution convention

A color / Transition Health observation is known only at a bar close. Therefore the resulting position is applied from the **next bar's close-to-close return**. No same-bar execution is allowed.

Primary comparison is a structural strategy proxy, not a broker-level backtest.

## Variant A — `color_only`

- desired position = current Formal color direction;
- when color changes, follow the new color on the next bar;
- when Formal becomes neutral, go flat on the next bar.

## Variant B — `color_plus_th_gate`

Start from the same color position.

Transition Health is not an entry delay.

- **Early Damaged:** while a tracked handoff is in age +1 through +3, the first bar where the carried stage no longer strictly leads the old-context stage is an observable early-damage event.
- If Early Damaged direction matches the current Formal color direction, set a **risk block** at that close and go flat from the next bar.
- While blocked, remain flat as long as the same Formal color family remains active.
- A later **Healthy +3** event in the same direction clears the block and restores the Formal-color position from the next bar.
- Any Formal color-family change (including neutral or opposite direction) resets the old block; the new Formal color is followed normally.
- Healthy without a prior block has no entry effect: it is only a hold confirmation.

No half-size rule is used in the primary test because choosing 50% would introduce an arbitrary sizing parameter.

## Samples

Report separately:

1. the seven already-burned FX development fixtures used throughout Issue #57;
2. the five 2022–2026 FX fixtures that were previously independent for the frozen +3 Transition Health rule but are now **reused evidence for this new overlay hypothesis**;
3. combined 12-pair descriptive summary.

No sample in this study is independent validation of the new trading overlay.

## Metrics

For each pair and each variant report:

- annualized gross return proxy;
- annualized volatility;
- gross Sharpe proxy (zero cash rate; descriptive only);
- maximum drawdown;
- annualized turnover;
- exposure share;
- number of color-family entries;
- number of Early Damaged blocks;
- number of Healthy re-risk events.

Also report pairwise wins of `color_plus_th_gate` versus `color_only` for return, Sharpe, and drawdown.

A fixed **2 bp per unit absolute position change** cost sensitivity is reported for both variants, but the decision must not be based on choosing whichever cost makes one variant look best.

## Interpretation boundary

The overlay is useful only if the early-damage gate improves risk-adjusted behavior across multiple pairs without destroying the directional advantage of the color baseline. If it mainly exits profitable color regimes and lowers return without a meaningful drawdown/Sharpe benefit, Transition Health should remain a descriptive visual layer rather than a trading-management rule.

Do not tune the +3 checkpoint, Formal mapping, block duration, re-entry rule, cost, or position size after seeing these results.