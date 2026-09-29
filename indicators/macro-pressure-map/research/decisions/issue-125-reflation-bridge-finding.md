# Issue #125 finding — HMRA Reflation to exact V6.6 Reflation bridge

Status: **COMPLETE — STRONG SAME-YEAR R3 ALIGNMENT, BUT ONE AXIS CONFIDENCE GATE MISSED**

Formal preregistered verdict:

`bridge_semantically_related_but_not_reflation_specific`

Production authorization: **NO**

## Important naming nuance

The deterministic fallback label above is coarse.

The result did **not** fail because exact Regime 3 lacked specificity.

In fact:

- exact Regime 3 had the largest positive occupancy lift of all nine exact V6.6 regimes;
- the Regime 3 occupancy CI excluded zero positively;
- every leave-one-HMRA-Reflation-year-out Regime 3 lift remained positive.

The single failed full-support gate was:

> exact Growth-high occupancy bootstrap CI lower bound > 0

Observed lower bound was approximately **-0.21 percentage point**, narrowly crossing zero.

Therefore the most accurate interpretation is:

> strong same-year Reflation-to-R3 state alignment, but not a full preregistered bridge pass.

## Sample

Primary overlap:

- complete years: **2007–2025**
- common years: **19**
- HMRA Reflation years: **6**
  - 2009
  - 2011
  - 2016
  - 2017
  - 2018
  - 2021

Exact V6.6:
- frozen Issue #64 transition history
- SHA-256:
  `80446bbcb91be8b18eb0b95e62466edf892e4c04087696a04532f0fe214698af`

Exact state sampling:
- one month-end state per calendar month
- annual inference unit

No asset returns were loaded.

## Exact Regime 3 alignment

HMRA Reflation years:

- mean exact R3 monthly occupancy: **36.11%**

Other HMRA years:

- mean exact R3 monthly occupancy: **10.90%**

Lift:

- **+25.21 percentage points**

Year-level bootstrap 95% CI:

- **+14.42pp to +35.04pp**

Median occupancy lift:

- **+25.00pp**

This is a strong same-year association.

## Exact Growth-high axis

Exact Growth-high means Regimes 1/2/3.

HMRA Reflation years:

- mean Growth-high occupancy: **45.83%**

Other years:

- **28.21%**

Lift:

- **+17.63pp**

Bootstrap 95% CI:

- **-0.21pp to +34.19pp**

The mean is clearly positive, but the lower bound narrowly crosses zero.

This is the sole failed full-support gate.

## Exact Inflation-high axis

Exact Inflation-high means Regimes 3/6/9.

HMRA Reflation years:

- mean Inflation-high occupancy: **56.94%**

Other years:

- **33.97%**

Lift:

- **+22.97pp**

Bootstrap 95% CI:

- **+8.97pp to +37.61pp**

This axis passes cleanly.

## Regime specificity

Mean occupancy lift by exact V6.6 regime:

1. Regime 3: **+25.21pp**
2. Regime 6: +3.10pp
3. Regime 8: +2.56pp
4. Regime 2: +0.64pp
5. Regime 5: -0.75pp
6. Regime 9: -5.34pp
7. Regime 1: -8.23pp
8. Regime 7: -8.33pp
9. Regime 4: -8.87pp

Regime 3 is unambiguously the largest positive lift.

Therefore the bridge is not merely linking HMRA Reflation to generic “risk-on” or “inflationary” exact states; the strongest exact-state association is specifically R3.

## Leave-one-HMRA-Reflation-year-out robustness

Removing each HMRA Reflation year one at a time leaves the R3 occupancy lift positive:

- omit 2009: +25.77pp
- omit 2011: +25.77pp
- omit 2016: +27.44pp
- omit 2017: +24.10pp
- omit 2018: +25.77pp
- omit 2021: +22.44pp

No single overlap year drives the R3 bridge.

## Monthly binary diagnostic

Diagnostic only:

- TP: 26 months
- FP: 46
- FN: 17
- TN: 139
- accuracy: **72.37%**
- precision: **36.11%**
- recall: **60.47%**
- Jaccard: **29.21%**

The modest precision/Jaccard are expected because:

- HMRA is an annual slow-moving macro classifier;
- exact V6.6 is a daily market-implied state that can switch repeatedly within a year.

These monthly binary metrics were not acceptance gates.

## Timing diagnostics

### HMRA state_t versus exact V6.6 in t+1

R3 occupancy lift:

- **+8.33pp**
- CI crosses zero

Growth-high lift:

- **-0.69pp**

Inflation-high lift:

- **+9.03pp**

The same-year state identity weakens materially one year later.

### HMRA state_t versus exact V6.6 in t+2

R3 occupancy lift:

- **-3.91pp**

Growth-high lift:

- +3.28pp

Inflation-high lift:

- **-9.09pp**

This confirms that HMRA Reflation is not a persistent two-year label for exact V6.6 state occupancy.

That does not contradict #121/#123 because their t+2 timing was a conservative causal asset-return protocol, not a claim that the macro state itself remains unchanged for two years.

## Ten-part bridge gate

PASS:

1. >=15 common complete years
2. >=3 HMRA Reflation years
3. R3 occupancy lift >0
4. R3 bootstrap CI lower bound >0
5. Growth-high occupancy lift >0
7. Inflation-high occupancy lift >0
8. Inflation-high CI lower bound >0
9. R3 is largest positive regime lift
10. every leave-one-Reflation-year-out R3 lift >0

FAIL:

6. Growth-high bootstrap CI lower bound >0

Observed:

- Growth-high CI lower bound = **-0.21pp**

Result:

**9 / 10 gates PASS**

Formal deterministic verdict:

`bridge_semantically_related_but_not_reflation_specific`

Again, the bucket name should not be read literally as “R3 was not specific”; R3 specificity passed. The failure is the Growth-high confidence sub-gate.

## Research interpretation

The evidence strongly supports a **same-year semantic relationship** between the two Reflation concepts:

> When HMRA classifies a year as Reflation, exact V6.6 spends materially more of that year in Regime 3, and Regime 3 is the exact state with by far the largest occupancy lift.

This substantially strengthens the relevance of #121/#123 to modern V6.6 Reflation.

However, the preregistered full bridge threshold was deliberately stricter and required both exact axes to have positive-side confidence intervals. Growth-high narrowly failed that requirement.

Therefore:

> HMRA long-history Reflation evidence can be treated as meaningful supporting evidence for exact V6.6 Regime 3, but Issue #125 does not by itself authorize a production Reflation tilt.

## Next boundary

A subsequent exact-V6.6 production translation study may use the following facts as **prior evidence**:

- modern exact R3 SPY−TLT direction was positive in #109;
- ultra-long HMRA Reflation Equity>Treasury revived in #121;
- 96-year 5pp policy translation passed 10/10 gates in #123;
- same-year HMRA Reflation strongly concentrates exact V6.6 Regime 3 in #125.

It must not:
- claim #125 was a full bridge pass;
- lower or retroactively change the Growth-high CI gate;
- optimize a modern tilt size after seeing results.
