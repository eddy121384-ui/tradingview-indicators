# Issue #59 — Joint-axis walk-forward holdout

Status: **JOINT-AXIS HOLDOUT COMPLETE**

Purpose: test whether the frozen V6.6 **combination** adds information beyond the best individual axis, without retuning V6.6.

## Design

Training / threshold-definition period:
- 2008-06-02 through 2019-12-31

Holdout:
- 2020-01-01 through 2026-08-14

The 20-day axis-change extreme cuts are learned once from the training period and then frozen:
- GPI d20: low `-21.06`, high `+19.53`
- IPI d20: low `-21.20`, high `+22.51`

No threshold is re-estimated on the holdout.

Two aligned joint transition states are compared:

- **Reflation impulse** = GPI d20 high AND IPI d20 high
- **Slowdown / disinflation impulse** = GPI d20 low AND IPI d20 low

Only the first bar entering each joint state is counted.

Event counts:
- training: 42 reflation vs 57 slowdown/disinflation events
- holdout: 28 reflation vs 23 slowdown/disinflation events

Primary statistic: mean forward-20d outcome of Reflation minus Slowdown/Disinflation.

## Main result — the GPI+IPI combination adds separation in Treasuries

| 20d outcome | Training joint spread | Holdout joint spread | Holdout GPI-only | Holdout IPI-only |
|---|---:|---:|---:|---:|
| US10Y yield | **+7.57 bp** | **+15.90 bp** | +11.24 bp | +6.48 bp |
| US02Y yield | **+4.77 bp** | **+16.63 bp** | — | — |
| ZN1! | **-0.54%** | **-1.04%** | -0.70% | -0.31% |
| TLT | -1.21% | -1.44% | -1.28% | -0.81% |
| USDJPY | +0.14% | +1.19% | +0.40% | -0.12% |
| EURUSD | -0.06% | +0.23% | ~0.00% | +0.84% |

Bootstrap 95% intervals for the joint contrast:

Training:
- US10Y: **[+0.08, +15.14] bp**
- US02Y: **[+0.18, +9.63] bp**
- ZN1!: **[-1.05%, -0.06%]**

Holdout:
- US10Y: **[+3.79, +28.41] bp**
- US02Y: **[+4.82, +28.10] bp**
- ZN1!: **[-1.77%, -0.32%]**

The Treasury result is both economically coherent and stronger in the 2020–2026 holdout than in training:
- aligned growth+inflation acceleration is followed by higher nominal yields / weaker Treasury futures;
- aligned growth+inflation deceleration is followed by lower yields / stronger Treasury futures.

The joint GPI+IPI contrast is also larger than either individual axis on US10Y and ZN in the holdout.

## Important nuance

The joint improvement does **not** generalize cleanly to every asset:
- EURUSD does not show stable joint-axis improvement;
- USDJPY is stronger in holdout but not in training;
- TLT direction is coherent, but its bootstrap interval overlaps zero.

The strongest evidence is specifically in **nominal Treasury rates / ZN**, which is valuable because these are not default-path V6.6 inputs.

## FCPI as conditioning overlay

FCPI still does not earn a strong incremental-predictive claim.

Exploratory conditioning of the joint events by FCPI level/change produced some interesting crisis-era splits, but the extra separation is not stable enough between training and holdout to freeze as a rule. Therefore:

**Do not promote FCPI into a predictive filter based on Issue #59 results.**

Its current justified role remains:
- summarize credit / rates-dollar / volatility stress;
- provide a risk-condition overlay;
- help describe whether a GPI/IPI macro impulse is occurring under stressed or normal financial conditions.

## Joint-axis verdict

This is the first result in Issue #59 that clearly supports the **combined regime architecture**, rather than only the individual axes.

### Earned

- GPI + IPI joint transition alignment adds information beyond either axis alone for future Treasury-rate / ZN behavior.
- The result survives a true era holdout with frozen training-period thresholds.
- The useful object is again **transition / alignment**, not the static regime label by itself.

### Not earned

- no universal cross-asset trading rule;
- no stable FX edge from the joint state;
- no incremental predictive role for FCPI yet;
- no justification to tune V6.6 thresholds or weights.

## Implication for a future V6.7

Do not redesign yet, but the research direction is now clearer:

1. preserve GPI and IPI;
2. emphasize **joint transition / alignment** in the UI and research language;
3. keep FCPI as a conditioning / stress overlay unless future evidence proves more;
4. avoid presenting static `Goldilocks / Reflation / Stagflation` labels as deterministic forecasts.

Issue #59 should remain open until the final synthesis / KEEP-SIMPLIFY-RECALIBRATE verdict is written.
