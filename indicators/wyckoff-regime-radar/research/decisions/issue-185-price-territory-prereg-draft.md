# Issue #185 — Price Territory Memory: preregistration DRAFT (not authorised)

**Status: DRAFT FOR REVIEW. NOT FROZEN. NOT AUTHORISED TO RUN.** No forward
outcome has been inspected by this draft. Writing this document does not
authorise historical outcome research. A separate explicit instruction is
required before any number below is executed.

**Revision note (v0.2.2, phase 2).** This revision lands the A1/A2/A3 guards as
implemented code with frozen thresholds, corrects the promotion clock from
`probe + 3` to `B3_break + 3`, corrects the A1 gap guard from close-to-close
jumps to envelope coverage, declares the accepted A1 false-suppression cost
(§2.2), carries the unfixed D10 scale-break level dependence (§2.4), and adds two
predeclared rejection rules (7, 9). It remains a draft: **no outcome has been
read and no run is authorised.**

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

## 2. Frozen instrument (v0.2.2 = v0.2 + amendments A1–A7, A1/A2/A3 implemented)

Prototype state at the time of writing: **v0.2.2**. A1, A2, A3, A4, A5, A6 and
A7 are all **implemented** and covered by 190 synthetic tests
(`test_issue185_price_territory.py`). This supersedes the earlier v0.2.1 text,
which described A1/A2/A3 as specified-but-unimplemented. Nothing in this phase
read a market outcome; every threshold below was fixed from synthetic geometry
before the patch was written.

The engineering-review verdict for the previous phase was `PROCEED_TO_PREREG`
conditional on A1–A3 landing. They have landed. **This draft is still DRAFT:
not frozen, not authorised to run.**

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
   the current close), `evidence_bars`, `F` (context only, never a gate), plus
   the A1/A2/A3 reference-quality fields in item 7. A new-territory claim is
   raised only when validity is `OK`, reference coverage is 1.0, the A1 and A3
   guards pass, and no scale break is latched.
6. **Anchor policy.** `first_probe_wins` with a 120-bar staleness cap (A5).
7. **Amendments — instrument-validity guards, none of them tuned.** All are
   implemented; every threshold below is a module-level constant in
   `ptm_territory.py`, appears in `PTMConfig.fingerprint()`, and is pinned by a
   test so it cannot change silently.
   * **A1** reference adequacy — a claim requires **all** of:
     `reference_cycle_count ≥ MIN_REFERENCE_CYCLES` (`1.0`),
     `envelope_covered_fraction ≥ MIN_ENVELOPE_COVERED_FRACTION` (`0.5`), and
     `max_unobserved_gap_fraction ≤ MAX_UNOBSERVED_GAP_FRACTION` (`0.25`).
     `reference_cycle_count = swing_legs / 2.0` (float), where a swing leg is a
     `CYCLE_SWING_FRACTION` (`0.5`) × `w` reversal of the running extreme and a
     trailing unpaired leg contributes `0.5`.
     **Correction to the earlier v0.2.1 draft:** the gap guard keys on the
     **largest unobserved hole between the merged reference bar ranges**, *not*
     on close-to-close jumps. A close-gap gate was rejected because a fully
     observed reference can legitimately teleport between closes while its bar
     ranges cover every price in between (`crossed_but_not_closed` has a
     `max_close_gap_w` of 10.0 with `envelope_covered_fraction = 1.000`). The
     close-gap statistic is still **reported**, as a diagnostic only.
   * **A2** scale comparability — `episodes_per_cycle = R / reference_cycle_count`
     (market-speed-comparable) and `revisit_density = R / n_valid` are emitted
     alongside `R`, never replacing it. `episodes_per_cycle` is `None` when no
     complete cycle exists (`COMPARABILITY_NO_COMPLETE_CYCLE`) and `0.0` when
     `R = 0` inside a complete cycle — a measured zero, distinct from
     unmeasurable. The challenger keys on a declared quantity.
   * **A3** `scale_reference = abs(median close_ref)` and
     `w_over_scale = w / scale_reference` are emitted;
     `SCALE_UNSTABLE` blocks claims when `w_over_scale > MAX_W_OVER_SCALE`
     (`0.05`). This is exactly equivalent to "the inter-decile close range must
     not exceed 100% of the reference price level", since `w = span / 20` and
     `20 × 0.05 = 1.0`. A zero or non-finite `scale_reference` yields
     `SCALE_UNKNOWN` and **fails closed**; it is never divided by.
     Known limitation: the ratio is **multiplicatively invariant but not
     translation invariant** (see §2.2).
   * **A4** range-overlap primary, minimum-overlap-fraction variant emitted as
     a mandatory secondary statistic. **Still open:** the variant cannot exclude
     a bar whose range fully encloses the band, so long-wick sensitivity is not
     fixed by it (pinned by a test).
   * **A5** `first_probe_wins` anchor with a 120-bar staleness cap.
   * **A6** stagnation/progress diagnostics are reported separately and are
     **not** combined with `N` and **not** used as a filter in the primary
     challenger.
   * **A7** the touch predicate is inclusive, exactly as written in the v0.2
     spec, and the scale-break screen may suppress a claim but may never create
     one. Both are implemented and pinned by tests (see the finding doc §6.C
     `C1`, `C2`).
8. **Candidate count: 2 challenger policies.** No additional variants may be
   added after any outcome is seen. Any further variant is a new prereg.

### 2.2 Accepted cost of A1, declared before outcomes

The A1 guard blocks any window in which no complete round trip formed. On the
synthetic set this suppresses exactly three fixtures:

| fixture | v0.2 claim bars | v0.2.2 claim bars | classification |
|---|---:|---:|---|
| `long_period_box` | 12 | 0 | correct — the D1 false release |
| `gappy_reference` | 1 | 0 | correct — data-quality guard |
| `one_way_reference_genuine_trend` | 10 | 0 | **COST — a real sustained escape refused certification** |

The cost is **declared and accepted here, before any outcome**: a window that
never formed a region cannot supply evidence about novelty relative to that
region, and a price-only test cannot separate a long box from a real trend. The
indicator returns "insufficient evidence" rather than guessing. Whether this cost
is acceptable at cohort scale is a **measured question for the run**, not a
decided one; §7 rule 7 makes it a predeclared rejection condition.

`one_way_reference_genuine_trend` is a synthetic worst case, not an estimate of
the real-world false-suppression rate. No rate is claimed here.

### 2.3 What A1/A2/A3 do not do

Measured on the synthetic set (33 fixtures, 2 of them guard-instrumentation and excluded from the counts below; `issue185_ptm_phase2_comparison.csv`):

* **zero added delay** on every fixture whose v0.2 signal survives
  (`max_added_delay_vs_v02_bars = 0`);
* **zero** change to the 8 published v0.2 reconstruction readouts
  (`all_episodes_match` and `all_novelty_match` both true);
* no fixed waiting period anywhere: `observable_at_bar = t` and
  `actionable_at_bar = t + 1` on every observation of every fixture;
* all three guards are reflection-symmetric, and A2 does not enter the claim
  predicate at all (pinned by recomputation).

### 2.4 Known defect carried into the run (D10, not fixed)

The frozen one-bar scale-break screen is **level-dependent**: a fixed absolute
move is a large *relative* move at a low price level. Shifting `true_trend` by
−130 makes the same 3.0 move a 43% change near level −7, which latches the screen
and suppresses claims whose `R`/`O`/`N` are identical to the positive-level path
(`low_level_scale_break_false_alarm`). **This is not fixed** — fixing it would
change a frozen v0.2 screen — and it is declared here so that a low-level or
negative-yield instrument cannot silently lose signals. §7 rule 6 covers it.

### 2.5 Comparison-only switch (excluded from the run)

`PTMConfig.apply_phase2_guards` defaults to `True` and exists **only** so the
runner can print an old-vs-fixed table. Setting it to `False` lifts the A1/A3
gate while leaving every diagnostic identical. **The run must use the default.**
The committed config fingerprint asserts `apply_phase2_guards = True` in CI.

### 2.1 Explicitly excluded

* PTM as an entry trigger or opportunity classifier.
* Any change to the 25% probe, the `B3_break + 3` promotion, Warning-First,
  stops or the risk budget.
* Any "fast-evidence" **earlier** add. The engineering review shows the first
  escape close is byte-identical between a true and a fake breakout, so an
  earlier add has no stated mechanism. It may be added only in a later prereg
  with a new mechanism.
* Any hand-chosen universal novelty cutoff. If a cutoff is needed by a
  challenger it is declared here, once, before outcomes.

## 3. Baseline execution policies (comparators, unchanged)

* **B0 — R0 Immediate.** 25% probe at a fresh formal Markup/Markdown; then the
  first usable post-entry B3 breakout, then three completed observation bars
  `P0/P1/P2`; promotion to 100% becomes eligible at
  **`B3_break_t + 3`** — the frozen parent contract. `P3` / no usable B3 remain
  probe. **An earlier draft wrote this as `t+3` where `t` was the probe; that
  was wrong and is corrected here.** The probe and the breakout are separate
  events and are tracked as separate timestamps.
* **B1 — R0 + Warning-First.** B0 plus the existing defensive reduction rule,
  with its documented lost large-trend harvest.

Core-2 `Structure × Extension` supplies context only. The optional A9
volatility percentile is a risk overlay / control variable, not a second alpha
claim; A9 itself was rejected as an independent dimension.

## 4. Challenger policies (2, minimal and interpretable)

* **C1 — PTM Guard.** Keep the benchmark's 25% probe instead of promoting the
  earned 75% at `eligible_promotion_t` **while** the completed close at that bar
  is in a `HEAVILY_REVISITED` state. Release the hold — and promote, no earlier
  than the next bar — on the first completed close with `R ≤ 1`, or on benchmark
  deterioration, whichever comes first. Never a fixed delay.
* **C2 — PTM Guard with dwell condition.** As C1, but the hold additionally
  requires `O ≥ o_min` (old region both revisited *and* dwelt in), with `o_min`
  declared before outcomes.

Both challengers consume the *same* frozen instrument. Both inherit B1's
Warning-First and all risk constraints unchanged.

### 4.1 The delay C1/C2 must be charged against (corrected contract)

The PTM extra delay is measured **relative to the real
`eligible_promotion_t = B3_break_t + 3`**, never against `probe_t0 + 3`. Measured
on the synthetic clock (`issue185_ptm_promotion_clock.csv`), the naive probe
baseline is too early by **10 bars** for a breakout 10 bars after the probe, and
by more for later breakouts (`long_trend_unbounded_novelty`: 80 bars).

Consequently the same PTM evidence can be *earlier* than the promotion or
*later* than it, depending purely on when the breakout arrives:

| fixture | construction `B3_break_t` | `eligible_promotion_t` | PTM first evidence | extra delay |
|---|---:|---:|---:|---:|
| `true_trend` | 120 (coincident) | 123 | 127 | 4 bars |
| `true_trend` | 130 (10 bars later) | 133 | 127 | **0 bars** |
| `wide_box_traversal` | 130 | 133 | none (no claim) | n/a |

The old contract would have reported the second row as a 4-bar delay too, by
comparing PTM at 127 against the fictional baseline of 123. **Any prereg run must
record all six timestamps**, and the delay distribution must be reported against
the corrected baseline. Reporting a delay against `probe + 3` would manufacture
a latency cost that does not exist and would bias the programme toward
rejecting a safe guard.

### 4.2 Predeclared decision the run must answer

The phase-2 patch proves only that the guards are **consistent, causal and
non-delaying on synthetic paths**. It does **not** establish that they are
beneficial on a market population. Three questions remain open and are the
actual content of this prereg:

1. Does the A1 false-suppression cost (§2.2) stay near zero on real cohorts, or
   does it block a material share of genuine emerging trends?
2. Does C1/C2's measured extra delay, on the corrected baseline, remain an
   acceptable distribution?
3. Does PTM add separation **beyond** the non-duplication comparators in §7?

If question 1 or 3 fails, the correct verdict is rejection, not redesign.

## 5. Freeze list (must be committed before the run)

* instrument version string (`v0.2.2`) and the full config fingerprint, including
  `min_reference_cycles`, `min_envelope_covered_fraction`,
  `max_unobserved_gap_fraction`, `max_w_over_scale`, `anchor_policy` and
  `apply_phase2_guards = True`, plus the challenger parameter `o_min` (declared
  here, before outcomes, and added to the fingerprint when C2 is instantiated);
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
* **All six timestamps must be recorded per opportunity**: `probe_t0`,
  `B3_break_t`, `B3_confirmation_t`, `eligible_promotion_t`, `PTM_observation_t`
  and `next_executable_t`. `eligible_promotion_t = B3_break_t + 3`, never
  `probe_t0 + 3`.
* The naive `probe + 3` baseline must be **recorded alongside** so its error
  stays measurable, but no decision, delay statistic or rejection test may use
  it as the baseline.
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

* `longest_inner_run`, acceptance trace and the stagnation diagnostics
  (`days_since_best_frontier`, `stall_flag`, …), reported separately;
* the A1/A2/A3 reference-quality fields (`reference_cycle_count`,
  `reference_adequacy_ok`, `envelope_covered_fraction`,
  `max_unobserved_gap_fraction`, `episodes_per_cycle`, `revisit_density`,
  `comparability_status`, `w_over_scale`, `scale_state`), plus
  `validity_reasons`, so that every blocked claim is attributable to a named
  guard rather than an opaque label;
* **false-suppression accounting**, reported together with detection lag, never
  separately: for every opportunity where the A1/A3 guards change the signal
  versus v0.2, record which guard fired and what the price subsequently did. The
  engineering review is explicit that "a guard which prevents false releases by
  suppressing almost all legitimate emerging trends is not a successful fix";
* the **level-dependence rate** of the frozen one-bar scale-break screen (§2.4),
  stratified by price level, so that D10 cannot hide.

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
   matched-latency control. **All latency is measured against the corrected
   `eligible_promotion_t = B3_break_t + 3` baseline** (§4.1); a delay computed
   against `probe + 3` is not admissible evidence for this rule.
3. **D1 survival.** The long-period-box false release demonstrated in the
   engineering review is not eliminated by A1 on the cohort.
4. **D5 survival.** The stagnation failure materially degrades large-trend
   harvest (`MFE ≥ 8 ATR`) relative to B0/B1.
5. **Narrowness.** Any gain is confined to one era, one sleeve or one asset
   class.
6. **Adjustment artefacts.** Results depend on unadjusted splits, rolls or
   gappy reference windows in a way the A1/scale-break guards do not catch, or
   the D10 level-dependence of the frozen scale-break screen (§2.4) removes a
   material share of signals at low price levels.
7. **False-suppression cost too high.** The A1 adequacy guard blocks a material
   share of *genuine* emerging trends. The cost is declared in §2.2 and the
   threshold is fixed here, before outcomes:
   * **reject** if, among opportunities where v0.2 raised a claim and the guards
     suppress it, more than **one third** are followed by a sustained escape
     (defined backward-looking as the close remaining beyond the frozen envelope
     for at least 3 consecutive bars within the next 10 bars);
   * **report, do not reject**, if the share is at or below one third, but the
     suppressed population's median subsequent `MFE` is at least
     `8 ATR` — this is a "promising but blocked" finding and requires a new
     prereg with a different mechanism, not a threshold change here;
   * the share and the `MFE` distribution are both mandatory outputs even if
     no rejection fires.
8. **Late-but-lucky.** The guard's apparent benefit is explained by a
   mechanical side effect — notably a shift in the *size* of the promoted
   position or the number of promoted opportunities — rather than by its stated
   mechanism.
9. **Reporting failure.** Any blocked claim cannot be attributed to a named
   guard through `validity` / `validity_reasons`, or the false-suppression
   accounting is reported separately from detection lag.

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
