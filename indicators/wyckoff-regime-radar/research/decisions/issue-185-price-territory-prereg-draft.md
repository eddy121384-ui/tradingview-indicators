# Issue #185 — Price Territory Memory: preregistration DRAFT (not authorised)

**Status: DRAFT FOR REVIEW. NOT FROZEN. NOT AUTHORISED TO RUN.** No forward
outcome has been inspected by this draft. Writing this document does not
authorise historical outcome research. A separate explicit instruction is
required before any number below is executed.

Companion documents:

* `issue-185-price-territory-engineering-review-finding.md` (design review)
* `issue-185-price-territory-integration-interface.md` (interface contract)

## 0. Lineage and cohort integrity

| item | value |
|---|---|
| Base branch | `research/issue-78-market-structure-dimension-audit` |
| Base commit | `e316d19` (A9 finding) |
| Contains | `04a982c` A5 untouched OOS4 validation of causal Core-2; `61724c2` A4; `8c3ded9` frozen OOS4 universe |
| Explicitly not a base | `research/issue-78-trigger-layer-discovery` (A6), `research/issue-78-failed-break-*` (A7/A8 event side-branch) |
| Discovery cohort | OOS3 (300 FIGIs) — **reused discovery, not fresh OOS** |
| OOS4 | already contacted by A5 for Core-2 context; **not pristine** |
| OOS5 | **must not be contacted** under this prereg |

OOS3 and OOS4 were both already used by earlier issue-78 studies. Neither may
be described as fresh out-of-sample evidence.

## 1. Research question, stated falsifiably

Does a frozen Reference-Territory Memory observable — the count of independent
historical bar-range visits to the price region around today's completed close,
measured against a reference frozen at the benchmark's probe — carry
**incremental, causal** information about whether an issued probe is inside a
wide range that will keep rejecting price, as opposed to early participation in
a persistent trend?

The prereg tests **both** sides of the trade-off and predeclares rejection.

## 2. Frozen instrument (v0.2.1 = v0.2 + amendments A1–A7)

Prototype state at the time of writing: v0.2, plus A4, A5 and A7, are
implemented and covered by 76 synthetic tests; A1, A2 and A3 are specified but
**not implemented**. The engineering-review verdict `PROCEED_TO_PREREG` is
conditional on A1–A3 landing inside the prereg commit. If any of them is
rejected, the correct verdict reverts to `REDESIGN`.

All of the following are frozen before outcomes:

1. **Reference.** Exactly the 120 completed bars preceding the first probe of
   an opportunity. Never slides within the episode.
2. **Zone radius.** `w = (Q90(close_ref) − Q10(close_ref)) / 20`, quantiles by
   linear interpolation, in instrument-native price units.
3. **Bands.** Inner `[P−w, P+w]`; outer `[P−2w, P+2w]`; `P` is the completed
   close.
4. **Touch.** Historical bar **range** satisfies the inclusive inner-band test
   `high ≥ P−w and low ≤ P+w` (see amendment note A7 below). The outer re-arm
   test uses the whole bar range and requires the bar to be entirely outside.
5. **Outputs.** `R` (revisit episodes), `O` (occupancy share over **valid**
   reference bars), `N = 1/(1+R)`, `A` (mean of ≤3 post-anchor `N` including
   the current close), `evidence_bars`, `F` (context only, never a gate).
   A new-territory claim is raised only when validity is `OK`, reference
   coverage is 1.0, `R ≤ 1`, and no scale break is latched.
6. **Anchor policy.** `first_probe_wins` with a 120-bar staleness cap (A5).
7. **Amendments — instrument-validity guards, none of them tuned.** `A1`, `A2`
   and `A3` are **not yet implemented**: they are implementation prerequisites
   that must land, with tests, inside the prereg commit and be re-verified
   before any outcome is read. Their thresholds are declared below and are
   frozen at that point, not afterwards.
   * **A1** reference adequacy — claims blocked unless
     `reference_cycle_count ≥ 1`, `envelope_covered_fraction ≥ f_min`, and
     `max_close_gap_w ≤ g_max`, with `f_min` and `g_max` declared in the frozen
     config *before* the run and not adjusted afterwards;
   * **A2** scale comparability — `episodes_per_cycle` and `revisit_density`
     emitted alongside `R`; the challenger keys on a declared quantity;
   * **A3** `w / median_ref` emitted; `SCALE_UNSTABLE` blocks claims above a
     pre-declared bound;
   * **A4** range-overlap primary, minimum-overlap-fraction variant emitted as
     a mandatory secondary statistic;
   * **A5** `first_probe_wins` anchor with a 120-bar staleness cap;
   * **A6** stagnation/progress diagnostics are reported separately and are
     **not** combined with `N` and **not** used as a filter in the primary
     challenger;
   * **A7** the touch predicate is inclusive, exactly as written in the v0.2
     spec, and the scale-break screen may suppress a claim but may never create
     one. Both are implemented and pinned by tests (see the finding doc §6.C
     `C1`, `C2`).
8. **Candidate count: 2 challenger policies.** No additional variants may be
   added after any outcome is seen. Any further variant is a new prereg.

### 2.1 Explicitly excluded

* PTM as an entry trigger or opportunity classifier.
* Any change to the 25% probe, the `t+3` promotion, Warning-First, stops or the
  risk budget.
* Any "fast-evidence" **earlier** add. The engineering review shows the first
  escape close is byte-identical between a true and a fake breakout, so an
  earlier add has no stated mechanism. It may be added only in a later prereg
  with a new mechanism.
* Any hand-chosen universal novelty cutoff. If a cutoff is needed by a
  challenger it is declared here, once, before outcomes.

## 3. Baseline execution policies (comparators, unchanged)

* **B0 — R0 Immediate.** 25% probe at a fresh formal Markup/Markdown; P0/P1/P2
  promote to 100% at `t+3`; P3 / no usable B3 remain probe.
* **B1 — R0 + Warning-First.** B0 plus the existing defensive reduction rule,
  with its documented lost large-trend harvest.

Core-2 `Structure × Extension` supplies context only. The optional A9
volatility percentile is a risk overlay / control variable, not a second alpha
claim; A9 itself was rejected as an independent dimension.

## 4. Challenger policies (2, minimal and interpretable)

* **C1 — PTM Guard.** Keep the benchmark's 25% probe instead of promoting the
  earned 75% at the existing promotion date **while** the current completed
  close is in a `HEAVILY_REVISITED` state. Release the hold — and promote, no
  earlier than the next bar — on the first completed close with `R ≤ 1`, or on
  benchmark deterioration, whichever comes first. Never a fixed delay.
* **C2 — PTM Guard with dwell condition.** As C1, but the hold additionally
  requires `O ≥ o_min` (old region both revisited *and* dwelt in), with `o_min`
  declared before outcomes.

Both challengers consume the *same* frozen instrument. Both inherit B1's
Warning-First and all risk constraints unchanged.

## 5. Freeze list (must be committed before the run)

* instrument version string and the full config fingerprint (including `f_min`,
  `g_max`, the A3 bound, `o_min`);
* the exact code commit SHA of the analyzer;
* the exact cohort manifest, FIGI-set hash and bar-date range;
* the metric definitions below, including every threshold used to *stratify*
  (which must be backward-looking only);
* the candidate count (2) and the rejection rules in §7;
* the artifact paths and the hashing method.

## 6. Measurement

### 6.1 Clock

* All decisions use completed closes; earliest executable action is `t+1`.
* Entry, promotion and reduction timestamps are the benchmark's own; PTM may
  only move the *promotion* timestamp within C1/C2.
* No retrospective peak/trough labels for live policy decisions.

### 6.2 False-trend / wide-box damage

Repeated whipsaws and failed trends, time-in-range, giveback after promotion,
exposure-days at 100%, turnover and trade cost, maximum drawdown, downside
tails. Reported per opportunity and aggregated.

### 6.3 Real-trend opportunity cost (equally weighted)

* earliest-observation lag in bars — reported as a **distribution**, not a mean;
* fraction of the initial trend captured and the cost of delayed adds in ATR;
* percentage of gross harvest retained in large trends, with large trend
  defined by the frozen threshold `MFE ≥ 8 ATR`;
* lost opportunity from classifying a strong trend as a box.

### 6.4 Reporting form

Plot or tabulate the **Pareto frontier**: false-trend risk reduction versus
large-trend harvest retained versus detection latency. A single scalar
accuracy/AUC headline is explicitly not an acceptable primary result.

### 6.5 Stratification (definitions frozen before outcomes, backward-looking)

* wide range versus narrow range, using a backward-looking objective
  definition frozen in the prereg;
* temporal blocks (eras) and the sleeves already used by issue-78 studies;
* market and asset class, with equal-asset and adequate-breadth weighting.

## 7. Rejection / stop rules (predeclared)

Reject PTM, or stop the programme, if any of the following holds:

1. **Non-duplication.** PTM shows no incremental separation from Core-2
   `Structure × Extension`, from the A9 volatility percentile, or from a plain
   120-day Donchian gate on the same cohort.
2. **Latency purchase.** Any false-trend benefit is obtained by systematically
   arriving late: the first-claim lag distribution shifts right by more than a
   pre-declared margin, or the benefit disappears under a
   matched-latency control.
3. **D1 survival.** The long-period-box false release demonstrated in the
   engineering review is not eliminated by A1 on the cohort.
4. **D5 survival.** The stagnation failure materially degrades large-trend
   harvest (`MFE ≥ 8 ATR`) relative to B0/B1.
5. **Narrowness.** Any gain is confined to one era, one sleeve or one asset
   class.
6. **Adjustment artefacts.** Results depend on unadjusted splits, rolls or
   gappy reference windows in a way the A1/scale-break guards do not catch.

Falsification is a valid and predeclared outcome. No outcome-driven rescue, no
post-hoc threshold shopping, no re-labelling of discovery data as fresh OOS.

## 8. Holdout

A survivor is validated on an untouched holdout in a **separate issue**, after
the survivor is frozen. OOS5 remains untouched until then. Reused OOS3 is
discovery only.

## 9. Deliverables if authorised

Frozen prereg commit; analyzer commit; per-opportunity trajectory export;
Pareto tables/plots; explicit failures and trade-offs; a verdict document
stating which §7 rule fired, if any.

## 10. Explicit non-authorisation

This draft does not authorise: historical outcome research, any parameter
change, any production or Pine change, any strategy or sizing change, any merge,
or any contact with OOS5. It is a specification for review, nothing more.
