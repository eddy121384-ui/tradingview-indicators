# Issue #185 — C1 A1 necessary-condition replication (2026-10-16)

**Decision: `FROZEN_GATE_2_FAIL_BY_UPPER_BOUND / C1 REJECTED FOR CURRENT SOURCE-COHORT`.**
This is a decisive *necessary-condition bound*, not a falsely claimed
byte-identical execution of `ptm_territory.py` and `ptm_addon_policy.py`.
Original-module full event-by-event parity, net transaction costs and
120-bar outcome-disposition counts remain unverified; none is needed to
**rescue** the already-failed, independently bounded 90% joint pass gate.
No parameter change, alternative challenger, OOS5 evaluation, or deployment.

## Provenance and frozen population

- Original **9 Issue #76 logger CSVs**: all nine independently verified against
  the original SHA-256 and bytes; **68,118 unique parent events**.
- **13 Issue #185 absolute-OHLC CSVs**, 9 exact feeds. Three earlier-seam
  candles remain separately identified as source-derived, not observed.
- Reconstructed frozen parent-eligible **647** add-ons. Exactly **447** have
  the original *feature-only*, strictly pre-probe 120-bar descriptor; frozen
  edges `(7.368, 11.9931)` give NARROW=144, MID=144, WIDE=159.
  The `WIDE & retrospective MFE>=8 ATR` comparison group contains **72**
  outcome-observed parent-eligible opportunities (above the 30 floor).
- Reference-anchor and cohort construction were verified separately. The
  frozen `width_atr` group is derived from the #76 coordinate representation;
  the PTM A1/A3 eligibility checks are derived from **native absolute OHLC**
  levels, never from arbitrary zero-referenced #76 coordinates. This is
  deliberate: retroactively changing the original stratification to fit
  absolute level scales would change the signed-off cohort.
- All 72 strong-WIDE reference windows have 120 directly recorded absolute
  OHLC bars. None needs one of the three inferred seam bars. Source-seam
  exclusion/recovery therefore cannot change this 72-event falsification.

## Exact frozen *guard formulas*, independently recomputed

The pre-outcome constants are unchanged: reference 120 bars; Q10/Q90;
`w=(Q90-Q10)/20`; A1 requires **at least two confirmed 0.5-span
reversal legs**, merged OHLC envelope coverage >=0.50, largest uncovered
gap <=0.25 of envelope. A3 requires `w/abs(median_close)<=0.05` using the
native price/yield level. A fresh territory claim cannot be made without
A1 AND A3; the approved C1 policy **conservatively holds** (does not simply
fall back to B0) when that reference is degraded. The reference is frozen at
the parent probe.

Results on the **72** WIDE strong-trend episodes:

| Preregistered guard check | Count |
| --- | ---: |
| A3 stable on absolute prices | 72 / 72 |
| A1 reference adequate | **2 / 72** |
| A1 rejected | **70 / 72** |
| A1 round-trip criterion failed (overlaps other failures) | 13 / 72 |
| A1 merged-envelope coverage <50% (overlaps other failures) | **66 / 72** |
| A1 largest-uncovered-gap >25% | 0 / 72 |
| Both A1 and A3 true (potentially releasable) | **2 / 72** |

Of those 2 A1+A3-eligible episodes, one was **TVC:GB10Y** and one
**TVC:JP10Y**. The previously observed C1 shadow release in only 1/72
is therefore plausible but not used as an assumption for the bound.

**Mechanism/data suitability:** the supplied TVC daily yield candles often
have identical recorded high and low (no observed intraday bar span). Exact
source zero-range rates: AU10Y=67.8%; DE10Y=69.8%; FR10Y=62.8%;
GB10Y=67.9%; US10Y=67.7%. In contrast JP10Y has 3.2%.
Thus the unchanged A1 *OHLC-range envelope* geometry rejects many
genuine bond-yield trends. This is an identifiable **instrument/source
representation interaction**, not evidence that all PTM concepts fail.

## Model-independent generous gross-harvest upper bound

The 90% gate is *gross favorable 75%-add-on harvest*, so fees and DV01
need not be determined to **falsify** this necessary condition.

For the two A1+A3-valid WIDE-strong episodes, grant C1 something it cannot
actually receive: the entire **75% add-on from the first formal trend bar**
instead of waiting until B3+3, with every positive normalized signed
`move1 / entry_scale` credited, through episode end. The two
**over-generous** total positive opportunities are:

- GB10Y: **29.700564** ATR-like normalized contribution units;
- JP10Y: **90.085246** such units;
- combined C1 **absolute theoretical maximum: 119.785810**.

The matched 72-episode B0 positive add-on harvest, counted from the
actual parent B3+3 clock, is **1,991.573703** on the previous parent's
all-row signed-`move1` convention; the earlier more conservative shadow
next-bar/exit readout is **1,960.601218**. Using the **smaller** denominator
(favors C1), the upper bound is:

`119.785810 / 1960.601218 = 6.11% < 90.00%.`

Even the impossible **from-day-one** C1 bound is >83 percentage points
below the owner-approved 90% threshold. The normal B3+3-limited bound,
with both valid episodes promoted immediately when eligible, is only
`110.905896 / 1991.573703 = 5.57%`. Real C1 requires a later
trusted positive novelty claim and can only perform worse on this metric.
This upper bound does **not** use C1's MFE as trade PnL or fit costs/thresholds.

It is a one-sided logical rejection; a bootstrap, transaction-cost
assumption, censoring denominator, or exact R/O/N signal replay cannot
turn 6.11% into 90% while respecting the frozen A1 and conservative-hold
policy. Both B0 and B1 comparisons were required; failure against
**B0 alone** is sufficient for the joint gate to fail.

## Correct interpretation / next action

**Reject C1 as the approved add-on exposure policy for the frozen Issue #76
FX/10Y sample.** Preserve B0/B1 and the #185 code for research, mark the
discovery candidate negative and do not spend OOS5 on this rejected
candidate. The 20% net-loss and 20% definite-withholding gates remain
unadjudicated; this is not evidence of their success or failure.

The requested byte-identical PTM-module execution was **not performed in
the present runtime** because the linked GitHub source was inspectable
through the connector but not executable alongside private CSVs. This
memo instead tests a mathematically *necessary* prerequisite using
the actual original constants and 120-bar references, with a far stronger
upper-bound rejection. Do not label it a completed exact-module parity run.
A later implementation audit may compare the 72 reference evaluations
directly, but should not be used to retune, resurrect C1, or open OOS5.

**Research decision:** `C1_REJECTED_ON_PREDECLARED_GROSS_HARVEST_GATE`.
The general value of a territory descriptor for **other, newly
preregistered purposes or properly measured sources** remains untested.
