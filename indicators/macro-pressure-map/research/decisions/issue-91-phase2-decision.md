# Issue #91 Phase 2 finding

## Verdict

`inflation_regime_dependent_mapping`

HMRA-v0.1 contains meaningful long-history cross-asset structure, but a fixed state→asset mapping is not uniformly stable across the 1928–2025 sample.

The cleanest higher-order interaction is **absolute inflation background**, especially for duration versus cash.

## Primary structural evidence

Across the full same-year structural sample:

- Reflation: Equity − Treasury **+11.72pp/year** (n=22; bootstrap mean CI +3.05 to +19.95pp).
- Goldilocks: Equity − Treasury **+15.31pp/year** (n=20; CI +9.83 to +20.93pp).
- Slowdown / Disinflation: Treasury − Cash **+6.04pp/year** (n=15; CI +2.02 to +10.26pp).
- Disinflationary Drift: Treasury − Cash **+6.33pp/year** (n=10; CI +1.70 to +11.11pp).

Stagflation is different: its unconditional Equity − Treasury and Treasury − Cash means are negative, but both have wide full-sample uncertainty.

## The higher-order inflation interaction

The preregistered split was CPI inflation below 4% versus >=4%, evaluated *within the same HMRA cell*.

### Reflation / Inflation Rising

Treasury − Cash:

- inflation <4%: **+2.03pp** (n=15)
- inflation >=4%: **−3.08pp** (n=7)
- difference: **−5.11pp**
- bootstrap difference CI: **−10.01 to −0.43pp**

### Stagflation Pressure

Treasury − Cash:

- inflation <4%: **+1.40pp** (n=8)
- inflation >=4%: **−4.71pp** (n=11)
- difference: **−6.11pp**
- bootstrap difference CI: **−12.30 to −0.10pp**

The sign reversal occurs independently in two economically different HMRA cells and both difference CIs exclude zero. This is the strongest evidence for `inflation_regime_dependent_mapping`.

Stagflation Equity − Treasury also reverses sign across the same inflation split, but its difference CI includes zero; it is supporting, not decisive, evidence.

## 1970s versus 2020s

The analogy is real, but more specific than “stocks and bonds behave exactly like the 1970s.”

For **duration versus cash**, the resemblance is striking in the descriptive same-year evidence:

- 1978 Reflation: Treasury − Cash −7.96pp
- 2021 Reflation: Treasury − Cash −4.46pp
- 1973 Stagflation: −3.38pp
- 1974 Stagflation: −5.86pp
- 1979 Stagflation: −9.38pp
- 1980 Stagflation: −14.38pp
- 2022 Stagflation: **−19.92pp**

Equity − Treasury is much less uniform: 1973–74 strongly favored Treasuries relative to equities, while 1979–80 favored equities, and 2022 was almost a tie because both were poor. Therefore the long-history result supports an inflation-sensitive **duration mapping**, not a simplistic “1970s template.”

## Era robustness

Some mappings are durable:

- Reflation Equity − Treasury stays positive under every leave-one-era-out rerun.
- Goldilocks Equity − Treasury also stays positive under every leave-one-era-out rerun.
- Stagflation Treasury − Cash stays negative under every eligible leave-one-era-out rerun.

But Stagflation Equity − Treasury is era-sensitive: three era omissions trigger a concentration flag/sign instability.

Overall, 17 of 118 leave-one-era-out cell/spread reruns were flagged as era-concentrated.

## Strict-causal t+2 evidence

The conservative forward mapping is not a copy of the contemporaneous structure.

- Reflation state_t → Equity − Treasury_{t+2}: **+13.81pp** (n=22; CI +6.04 to +20.86pp).
- Disinflationary Drift: **+9.20pp** (n=9; CI +1.83 to +17.00pp).
- Stagflation: +4.67pp, CI crosses zero.
- Slowdown / Disinflation: +9.12pp, CI crosses zero.

Notably, Stagflation and Slowdown Equity − Treasury have opposite signs in the contemporaneous and t+2 summaries. The HMRA state→asset relation therefore must not be treated as a simple fixed one-year trading law.

## Independent source check

Damodaran versus JST, 1928–2020:

- equity annual-return correlation: **0.9747**
- Treasury annual-return correlation: **0.9485**
- Equity − Treasury correlation: **0.9625**
- eligible HMRA cells with n>=5: 5
- mean Equity − Treasury sign agreement: **5/5**

The central equity/bond result is therefore not an artifact of choosing one return dataset.

## What this does *not* authorize

Phase 2 did not run the #89 portfolio matrix and did not optimize weights.

The finding does **not** justify immediately adding a third axis to production V6.6. It says something narrower and more useful:

> the economic meaning of Growth × Inflation for asset allocation is conditional on the background level of inflation, with the clearest evidence in the duration-versus-cash relationship.

Any portfolio rule that uses this interaction must be separately preregistered and tested.
