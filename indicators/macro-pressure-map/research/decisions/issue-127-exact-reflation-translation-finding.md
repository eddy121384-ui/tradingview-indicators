# Issue #127 finding — exact V6.6 Reflation production translation gate

Status: **COMPLETE — MODERN EXACT-V6.6 TRANSLATION CANDIDATE**

Formal preregistered verdict:

`exact_v66_reflation_translation_candidate`

Production authorization: **NO — explicit product decision still required**

## Frozen rule tested

Neutral:
- SPY 40%
- TLT 40%
- GLD 10%
- SHV 10%

When exact V6.6 is Regime 3 — Reflation / Inflation Rising:
- SPY 45%
- TLT 35%
- GLD 10%
- SHV 10%

All other regimes remain neutral.

Primary tactical cost:
- 5bp one-way per dollar of target turnover.

## Modern sample

- 234 completed monthly periods
- origins 2007-02-01 through 2026-07-01
- 47 active Regime-3 months
- 20 active episodes

All three frozen modern temporal segments are policy-evaluable.

## Full-sample result

### Action

- CAGR: **7.4571%**
- Sharpe vs SHV: **0.6983**
- max drawdown: **-21.1222%**
- terminal wealth: 4.0653x
- annualized tactical turnover: 10.26%
- cumulative tactical cost: 0.10%
- annualized cost drag: ~0.55bp/year

### Neutral C0

- CAGR: **7.3233%**
- Sharpe vs SHV: **0.6850**
- max drawdown: **-21.1222%**
- terminal wealth: 3.9677x

### Action minus C0

- CAGR advantage: **+0.1338 percentage point/year**
- Sharpe advantage: **+0.0133**
- max-drawdown difference: effectively **0.00pp**
- terminal wealth difference: +0.0976x

The modern exact implementation is directionally consistent with the long-history #123 result, whose 5pp policy advantage was approximately +0.138pp/year.

## Exposure-matched C1

Average realized Action weights:

- SPY 41.0043%
- TLT 38.9957%
- GLD 10%
- SHV 10%

C1:
- CAGR: 7.4064%
- Sharpe: 0.6911
- max drawdown: -20.9824%

Action beats C1:

- CAGR: **+0.0508pp/year**
- Sharpe: **+0.00725**

Therefore the result is not explained solely by carrying slightly more Equity exposure on average.

## Temporal validation

### Pre-2020

- active months: 34
- CAGR advantage: **+0.1153pp/year**
- Sharpe advantage: +0.00961

### 2020–2022

- active months: 8
- CAGR advantage: **+0.3766pp/year**
- Sharpe advantage: +0.0320

### 2023+

- active months: 5
- CAGR advantage: **-0.0208pp/year**
- Sharpe advantage: -0.00209

All three segments are evaluable.

Two of three are positive, satisfying the frozen temporal gate.

The post-2023 disadvantage is tiny and far inside the frozen -0.25pp/year tolerance.

## Episode robustness

Strongest positive active episode:

- 2020-12-01 through 2021-07-01
- 8 months
- gross contribution: +1.1094%

Total positive active-episode contribution:
- +4.7305%

Strongest episode share:
- **23.45%**

This is well below the frozen 50% concentration ceiling.

After reverting the entire strongest episode to neutral and recomputing turnover:

- Action CAGR: 7.3957%
- C0 CAGR: 7.3233%
- remaining CAGR advantage: **+0.0723pp/year**
- Sharpe remains above C0

The full-sample result does not depend on one winning episode.

## Eleven-part final gate

PASS:

1. Action CAGR > C0
2. Action Sharpe > C0
3. max-drawdown degradation <=1.0pp
4. active Regime-3 months >=12
5. active episodes >=5
6. evaluable temporal segments >=2
7. >=2 evaluable temporal segments positive
8. no evaluable temporal segment below -0.25pp/year
9. strongest-episode leaveout remains positive
10. strongest positive episode share <=50%
11. Action beats C1 on CAGR and Sharpe

Result:

**11 / 11 gates PASS**

Formal verdict:

`exact_v66_reflation_translation_candidate`

## Evidence stack

The same economic direction now survives four distinct layers:

1. modern exact V6.6 pairwise evidence (#109):
   - Reflation SPY > TLT direction positive but underpowered

2. ultra-long-history pairwise rematch (#121):
   - Reflation Equity > Treasury revived
   - strict causal t+2 mean +13.81pp/year
   - CI fully positive
   - cross-era robustness passed

3. ultra-long-history portfolio translation (#123):
   - fixed 5pp Equity-over-Treasury tilt
   - 1930–2025
   - 10/10 policy gates passed
   - +0.138pp/year CAGR

4. HMRA-to-exact state bridge (#125):
   - exact Regime 3 occupancy lift +25.21pp in HMRA Reflation years
   - Regime 3 was the largest positive exact-regime lift
   - 9/10 bridge gates passed
   - sole miss was Growth-high bootstrap lower bound narrowly below zero

Issue #127 adds the fifth layer:

5. exact modern V6.6 portfolio translation:
   - fixed +5pp SPY / -5pp TLT
   - 11/11 implementation gates passed
   - +0.134pp/year CAGR
   - no max-drawdown worsening
   - beats exposure-matched C1
   - survives strongest-episode removal

## Interpretation

The evidence now supports preserving:

> exact V6.6 Regime 3 / Reflation → +5pp Equity / -5pp Duration

as the leading fixed-size Action Layer production candidate.

The modern observed CAGR increment is almost identical in magnitude to the independently structured long-history policy translation:

- long history #123: ~+0.138pp/year
- exact modern #127: ~+0.134pp/year

This similarity was not an optimization target and no modern weight was tuned to achieve it.

## Boundary

Issue #127 still does not automatically enable live trading.

A final product decision must explicitly choose whether to:

- display the tilt as an informational Action Layer;
- enable it as a model portfolio recommendation;
- or continue shadow monitoring before activation.

Do not:
- increase the tilt;
- add other near-miss states;
- mix in Gold > Cash without a separate decision;
- reinterpret this as guaranteed future outperformance.
