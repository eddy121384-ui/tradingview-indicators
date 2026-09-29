# Issue #115 finding — Gold > Cash defensive sleeve robustness

Status: **COMPLETE — ECONOMICALLY POSITIVE, BUT POST-HOC ROBUSTNESS GATE NOT FULLY PASSED**

Workflow:
- run: `36517227786`
- head: `1d86c71fcc62f08d5e514298dd3b6cab63d613d8`
- artifact: `issue-115-gold-defensive-sleeve`
- artifact id: `11010964377`
- artifact digest: `sha256:179bf5f9a0673a3383257a5c70db0510c655b4bc87b6b04ff1371d9876d153eb`

Final preregistered verdict:

`gold_defensive_sleeve_economically_positive_but_posthoc_not_robust`

Production authorization: **NO**

## Research-integrity status

This study is explicitly post-hoc.

The Gold-only hypothesis was selected after Issue #113 attribution showed that most gross Action Layer contribution came from Gold > Cash.

Therefore this result is reused/development evidence, not independent confirmation.

## Frozen rule tested

Neutral:

- SPY 40%
- TLT 40%
- GLD 10%
- SHV 10%

Gold-only defensive tilt:

- Regime 7 — Slowdown / Disinflation:
  - GLD +5pp / SHV -5pp
- Regime 8 — Growth Slowdown / Stable Inflation:
  - GLD +5pp / SHV -5pp
- Regime 9 — Stagflation Pressure:
  - GLD +5pp / SHV -5pp
- Regimes 1–6:
  - no view

Primary tactical transaction cost: 5bp one-way per dollar of target turnover.

Sample:

- 234 completed monthly periods
- 2007-02-01 through 2026-07-01 origins
- 87 active months
- 29 active episodes

## Full-sample result

### Gold-only

- CAGR: **7.6954%**
- annualized vol: 8.8409%
- Sharpe vs SHV: **0.7173**
- max drawdown: **-21.3639%**
- Calmar: 0.3602
- terminal wealth: 4.2447
- annualized tactical turnover: **14.87%**
- total tactical cost: 0.1450%
- annualized cost drag: ~0.79bp/year

### C0 neutral

- CAGR: **7.3233%**
- Sharpe vs SHV: **0.6850**
- max drawdown: **-21.1222%**
- terminal wealth: 3.9677

### Incremental vs C0

- CAGR advantage: **+0.3721 percentage point / year**
- Sharpe advantage: **+0.0323**
- max-drawdown difference: **-0.2417 percentage point**
- terminal wealth difference: +0.2770

The Gold-only sleeve is economically positive, but the preregistered +0.05 Sharpe hurdle is not met.

## Exposure-matched C1

Realized average Gold-only weights:

- SPY: 40.0000%
- TLT: 40.0000%
- GLD: 11.8590%
- SHV: 8.1410%

C1:

- CAGR: 7.4883%
- Sharpe: 0.6932
- max drawdown: -21.2599%

Gold-only beats C1 on both CAGR and Sharpe.

Therefore the result is not explained solely by holding more Gold and less Cash on average.

## Comparison with Issue #113 full sparse overlay

Issue #113 C2:

- CAGR: 7.7538%
- Sharpe: 0.7215
- max drawdown: -21.3660%
- annualized tactical turnover: 21.54%

Gold-only minus C2:

- CAGR: **-0.0584pp/year**
- Sharpe: **-0.0042**
- max drawdown: effectively unchanged
- annualized tactical turnover is materially lower: **14.87% vs 21.54%**

Interpretation:

Removing the Equity-vs-Duration sleeve sacrifices only a small amount of historical CAGR/Sharpe, while simplifying the rule and reducing turnover.

This is descriptive only; C2 is not a gate.

## Temporal validation

All three eras retain positive Gold-only CAGR advantage vs C0.

### Pre-2020

- Gold-only CAGR: 8.2346%
- C0 CAGR: 7.8430%
- CAGR advantage: **+0.3916pp**
- Sharpe advantage: +0.0339
- max DD difference: **+1.4292pp better**

### 2020–2022

- Gold-only CAGR: 1.1461%
- C0 CAGR: 1.0495%
- CAGR advantage: **+0.0966pp**
- Sharpe advantage: +0.0082
- max DD difference: -0.2417pp

### 2023+

- Gold-only CAGR: 11.4785%
- C0 CAGR: 10.9260%
- CAGR advantage: **+0.5525pp**
- Sharpe advantage: **+0.0500**
- max DD difference: effectively flat

The CAGR effect does not reverse sign across the three preregistered eras.

## Episode robustness

Strongest positive episode:

- 2007-08-01 through 2008-02-01
- 7 months
- contribution sum: +1.8592%
- top-positive episode share: **20.99%**

After reverting that entire episode to C0 and recomputing turnover:

- leaveout Gold-only CAGR: 7.5937%
- leaveout CAGR advantage vs C0: **+0.2703pp/year**

The full-sample result is not dependent on one winning episode.

## Leave-one-state-out robustness

All three fixed counterfactuals retain positive full-sample CAGR advantage vs C0.

### Remove Regime 7

Keep Regimes 8/9:

- CAGR advantage: **+0.1850pp**
- Sharpe advantage: +0.0194
- max DD difference: +0.0091pp

### Remove Regime 8

Keep Regimes 7/9:

- CAGR advantage: **+0.3439pp**
- Sharpe advantage: +0.0288
- max DD difference: -0.2438pp

### Remove Regime 9

Keep Regimes 7/8:

- CAGR advantage: **+0.2102pp**
- Sharpe advantage: +0.0161
- max DD difference: -0.2566pp

No single one of Regimes 7, 8, or 9 is solely responsible for the positive full-sample CAGR effect.

This does **not** authorize selecting a preferred subset.

## State contribution diagnostic

Gross Gold-minus-Cash arithmetic contribution:

### Regime 7 — Slowdown / Disinflation

- active months: 51
- contribution sum: **+3.6166%**
- annualized mean over full sample: +0.1855pp/year

### Regime 8 — Growth Slowdown / Stable Inflation

- active months: 15
- contribution sum: **+0.5151%**
- annualized mean over full sample: +0.0264pp/year

### Regime 9 — Stagflation Pressure

- active months: 21
- contribution sum: **+2.9798%**
- annualized mean over full sample: +0.1528pp/year

Regime 8 is the smallest Gold contributor, but it was preregistered and must remain in the rule.

## Cost sensitivity

0bp:
- CAGR 7.7033%
- Sharpe 0.7181

5bp primary:
- CAGR 7.6954%
- Sharpe 0.7173

10bp:
- CAGR 7.6875%
- Sharpe 0.7164

Cost is not the reason the gate fails.

## Stricter post-hoc production gate

PASS:

1. full CAGR advantage >= +0.25pp
3. max DD not worse by >1.5pp
4. all 3 eras positive CAGR advantage
5. minimum era CAGR advantage >= 0
6. strongest-episode leaveout remains positive
7. beats C1 on CAGR and Sharpe
8. all three leave-one-state-out variants remain positive

FAIL:

2. Sharpe advantage >= +0.05

Observed full-sample Sharpe advantage is only **+0.0323**.

Result: **7 / 8 gates PASS**

Deterministic verdict:

`gold_defensive_sleeve_economically_positive_but_posthoc_not_robust`

## Product implication

The Gold > Cash sleeve is the cleanest surviving Macro Pressure Map Action Layer candidate so far.

Compared with the broader #113 overlay it:

- preserves most of the historical CAGR improvement;
- preserves most of the Sharpe improvement;
- has lower turnover;
- stays positive across all three eras;
- survives strongest-episode removal;
- survives removing any one of Regimes 7/8/9;
- beats the exposure-matched static control.

But it still does **not** satisfy the preregistered risk-adjusted hurdle, and the hypothesis was selected post-hoc from the same sample.

Therefore:

> **Preserve Gold > Cash in Regimes 7/8/9 as the leading research candidate, but do not authorize production sizing yet.**

Do not rescue this by:

- lowering the +0.05 Sharpe hurdle;
- increasing the Gold tilt above 5pp;
- dropping Regime 8 after seeing its smaller contribution;
- selecting the best leave-one-state-out subset;
- adding trajectory / FCPI / Reflation / commodities.

The appropriate next evidence is genuinely new data, not another in-sample retune.
