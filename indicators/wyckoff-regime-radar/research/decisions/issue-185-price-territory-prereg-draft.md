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
predeclared rejection rules (7, 9).

**Revision note (v0.2.3, prereg-freeze correction round).** This revision
addresses the four P0 freeze blockers raised in review of v0.2.2:

* **P0.1 — swing-leg formula.** §2 now states
  `CYCLE_SWING_FRACTION × (Q90 − Q10) = 10 × w`. The earlier prose said
  `0.5 × w`, which is 20× smaller and is the *fail-open* direction. The
  **implementation was verified correct; the prose was wrong**. No threshold
  changed. Pinned by test.
* **P0.2 — information-level fail-closed is not an exposure policy.** §4.1
  replaces the band-only rule with the full frozen claim gate, and §4.2 fixes an
  explicit causal pre-outcome state table covering `OK + HEAVILY_REVISITED`,
  `OK + REVISITED (R = 2..4)`, `OK + SPARSE/UNVISITED (R <= 1)`,
  `DEGRADED/UNKNOWN` and the 120-bar episode expiry. The **abstain option was
  shown to be unreachable in this state**, and the round concluded that
  conservative hold was therefore forced. ⚠️ **SUPERSEDED by v0.2.4.** The
  unreachability holds, but the inference did not: conservative hold is C1's
  explicit **policy choice**, and the distinct alternative of routing the
  degraded branch to the unmodified baseline remains available (§4.2.1).
* **P0.3 — deterioration must never mechanically promote.** §4.4 removes "or on
  benchmark deterioration, whichever comes first" as a *release* trigger;
  deterioration now yields `DE_RISK` and never promotes. §4.3 and §6.6 make
  permanent suppression report as **censored / unbounded extra delay** plus
  **missed big-trend harvest**, never as `0` bars.
* **P0.4 — real R0/B3 event integration and missing constants.** §4.8 pins the
  frozen parent event source (the Issue #76 forward-logger export consumed by
  the #78 modules), its parity check and the exact eligibility rule; §4.6 pinned
  `o_min` (⚠️ **retired in v0.2.4** with C2); §5 freezes the exposure-policy
  decision; §6.5 fixed the wide-box stratum (⚠️ **replaced in v0.2.4** — the
  criteria there were not classifiers). All frozen **without reading any forward
  return outcome**.

**Revision note (v0.2.4, C1-only convergence round).** This revision converges the
empirical programme to **C1 alone** and repairs three defects raised in review of
v0.2.3. It reads no forward outcome and changes no PTM mathematics.

* **S1 — C2 silently changed its hypothesis.** The approved C2 was "PTM Guard plus
  a historical **touch-occupancy** `O >= o_min` **hold** condition"; what was
  implemented required three consecutive claiming bars before **release**. The
  unit (occupancy proportion → bar count), the direction (hold → release
  precondition) and the quantity (occupancy → claim persistence) all changed.
  `o_min = 3` was **not** approved. **Resolution: C2 is `RETIRED` from the active
  plan** (§4.6); its code and evidence remain reproducible, marked
  `RETIRED_NOT_AN_ACTIVE_CHALLENGER`, and its parameters are not tuned. The
  prereg now specifies **C1 only**, which introduces no new parameter.
* **S2 — the wide-box stratum was not a classifier.** `spread / w = 20` is an
  **algebraic identity** (true for every valid reference); `R <= 1` plus an
  unfixed claim selects *sparse claimed territory* — the treatment itself; and
  `sustained_escape()` reads the post-probe path, making it a valid retrospective
  **outcome** label rather than an ex-ante feature. §6.5 replaces all three with
  the frozen pre-probe **`width_atr`** descriptor (reference inter-decile span ÷
  pre-probe ATR), causal by construction and binned by pre-frozen feature-only
  tertiles. `sustained_escape` is retained for outcome-side reporting only.
* **S3 — the permanent-no-add-on statistic conflated censoring with suppression.**
  `evaluate_addon` returned `WITHHOLD_CENSORED` / `missed_addon` even when the
  fixture ended **before** the parent's eligibility bar (e.g. `gappy_reference`
  eligible 126 vs last bar 123). The `14/23 = 60.9% permanently censored` figure
  is **withdrawn**. §4.3 defines a five-category disposition taxonomy separating
  *what the policy decided* from *whether the horizon was observed*, and
  §4.3.3 reclassifies the zero "signal contradiction" count as an **invariant,
  not evidence**.

**It remains a draft: no outcome has been read, nothing is frozen, and no run is
authorised. `PREREG DRAFT — NOT AUTHORISED.`**

**Pending Sophira rulings (not decidable from design alone).** Each is stated
with a primary recommendation and rationale in the referenced section:

| # | item | primary recommendation | section |
|---|---|---|---|
| 1 | exposure-policy semantics for `DEGRADED/UNKNOWN` | conservative hold — **an explicit, approved policy choice**, whose full opportunity cost is charged to C1. The earlier claim that abstain and conservative hold are "not distinct behaviours" is **withdrawn**: routing the degraded branch to the unmodified baseline is a distinct, documented, unimplemented alternative (`BASELINE_ON_DEGRADED_ALTERNATIVE`). | §4.2.1 |
| 2 | `o_min` for C2 | **`o_min = 3` is NOT approved and is not needed: C2 is retired.** Not an active challenger. | §4.6 |
| 3 | acceptable **genuine** full-horizon suppression share | no number fixed; preferred form is a **joint** constraint (max false-trend loss *given* min retained `MFE >= 8 ATR` harvest). Must be separated from administrative right-censoring first, and **must not** be derived from the synthetic `0/9` (vacuous) or the withdrawn `60.9%`. | §7 rule 11 |
| 4 | whether C2's thin separation (1 of 33) disqualifies it | **resolved by ruling: YES — retire C2, preregister C1 alone.** Implemented. | §4.6 |

Status of each: **`PENDING_SOPHIRA_APPROVAL`** (items 1 and 3) or
**`RESOLVED_BY_RULING`** (items 2 and 4). Nothing above is frozen by this
document.

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
     reversal of the running extreme by at least `CYCLE_SWING_FRACTION` (`0.5`)
     × `(Q90 − Q10)`. Because `w = (Q90 − Q10) / RADIUS_DIVISOR` and
     `RADIUS_DIVISOR = 20`, that threshold is exactly **`10 × w`**. A leg ends
     at a *confirmed reversal*, so a monotone window returns 0 legs, not 1, and
     a trailing unpaired leg contributes `0.5` cycles.
     **Formula correction (P0.1 of the prereg review):** an earlier draft
     stated `0.5 × w`. That is **20× smaller** than the implemented threshold
     and is the *fail-open* direction — on `volatility_regime_shift` it would
     credit 5.5 cycles where the implementation credits 0.5, letting the cycle
     sub-guard pass. The code was checked against the tests and the synthetic
     geometry *before* this text was changed; the **prose was wrong, not the
     algorithm**, so no threshold was re-chosen and `CYCLE_SWING_FRACTION`
     remains `0.5`. Pinned by
     `test_d1_cycle_threshold_is_half_the_inter_decile_span_not_half_w`.
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
8. **Active candidate count: 1 challenger policy (C1).** No additional variants
   may be added after any outcome is seen, and no retired variant may be revived
   as a candidate. Any further variant is a new prereg.

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

## 4. Challenger policy (exactly one active: C1)

The challenge stays at the benchmark's 25% probe instead of promoting the earned
75%. **The policy layer can only withhold or release an add-on the parent has
already earned. It never accelerates a promotion, never reduces exposure, never
sizes, and never alters B1's Warning-First or any other risk constraint.**

* **C1 — PTM Guard (the only active challenger).** Withhold the earned 75% while
  the completed close at the decision bar does not carry a valid new-territory
  claim; release on the first completed close that does. Never a fixed delay.
* **C2 — PTM Guard with dwell condition. `RETIRED`.** Retained as historical
  evidence only; excluded from the comparison and from the decision surface.
  See §4.6.

C1 consumes the *same* frozen instrument as the baselines.

**No new number enters the freeze for the active challenger.** C1 introduces no
parameter: its rule is the frozen claim gate and nothing else. The only number
C2 ever added (`o_min`) is retired with C2 and **must not be tuned**. §4.6 records
why.

### 4.0 Scope of the convergence (what this revision did and did not do)

This revision converges the empirical programme to **C1 only**, in line with the
review ruling that C2 be dropped from the active plan. It makes three corrections
and keeps everything else frozen:

1. **C2 is retired from the active plan, not deleted.** Its code and its
   measurements remain reproducible as historical record (`CHALLENGER_POLICIES`
   contains both; `ACTIVE_CHALLENGERS` contains only C1). Nothing about C2's
   parameters is optimised, and its recorded weakness is not repaired.
2. **The wide-box stratum is redefined as an ex-ante observable** (§6.5). The
   previous criteria were not classifiers.
3. **The add-on cost accounting is repaired** so that *administrative
   right-censoring* is separated from *definite withholding* (§4.3). The earlier
   `14/23 = 60.9% permanently censored` figure is **withdrawn**.

**Unchanged by this revision:** A1–A7, the PTM mathematics (`w`, `R`, `O`, `N`,
all thresholds), the parent B3 clock and eligibility rule, the parent event source
and parity contract, all baseline policies, and the 190 phase-2 tests.

### 4.1 The gate is the full claim gate, not the revisit band

**This replaces the earlier `HEAVILY_REVISITED`-only rule, which was an
information-level fail-closed masquerading as an exposure policy.** Gating on
the revisit band alone leaves the hole the prereg review identified:
`long_period_box` sits at `R = 1` (`SPARSE`), so a band-only rule would have
promoted its 75% even though its reference is
`DEGRADED_REFERENCE_ADEQUACY`. A revisit band is an *information* statement
about how often a level has been touched; it is not by itself an exposure
decision.

C1 therefore gates on the **frozen claim rule**:

```
release_eligible(t)  =  is_new_territory_claim(t)
                     =  novelty_fresh(t)                  # R <= 1
                    and allows_new_territory_claim(t)      # A1 + A3 + coverage
                    and not suspect_scale_break(t)
```

`allows_new_territory_claim` is itself `validity == OK and
reference_coverage >= 1.0 and reference_adequacy_ok and scale_stable`
(`ptm_territory.py`, `FrozenReference.allows_new_territory_claim`). The policy
module mirrors it conjunct-by-conjunct in `claim_gate_failures`, so every
withheld add-on names the exact closed conjunct instead of reporting a bare
boolean.

The revisit bands then select **how much evidence is demanded**; they never
decide whether a degraded reference is trusted.

### 4.2 Causal pre-outcome state table (frozen)

`eligible = B3_break_t + 3`. Every state is read from the **completed** bar at
or after `eligible`; a decision taken on bar `t` is executable at `t + 1`.

| # | state of the completed bar `t` | C1 at `t` | releaseable later in this episode? | reported as |
|---|---|---|---|---|
| S1 | `OK`, `R <= 0` (`UNVISITED`) | release | yes | `PROMOTED` |
| S2 | `OK`, `R = 1` (`SPARSE`) | release | yes | `PROMOTED` |
| S3 | `OK`, `R = 2..4` (`REVISITED`) | withhold | only if `R` returns to `<= 1`, which the frozen rule cannot guarantee | `POLICY_WITHHELD_THROUGH_EXPIRY` if the horizon completes; else `OBSERVATION_RIGHT_CENSORED` |
| S4 | `OK`, `R >= 5` (`HEAVILY_REVISITED`) | withhold | as S3 | as S3 |
| S5 | any `DEGRADED_*` or `UNKNOWN`, any band | withhold (**conservative hold — an explicit policy choice**, §4.2.1) | only via S1/S2 | as S3 |
| S6 | observation absent at `t` | withhold | absent is not evidence | as S3 |
| S7 | benchmark deterioration at any `t` | `BASELINE_DE_RISK_BEFORE_RELEASE`, never promotes | no | `BASELINE_DE_RISK_BEFORE_RELEASE` |
| S8 | `t >= eligible + 120` while still withheld | **definite withholding**; never auto-promotes | no | `POLICY_WITHHELD_THROUGH_EXPIRY` |
| S9 | parent path `P3`, or no usable B3 | `PARENT_NOT_ELIGIBLE` | n/a | `PARENT_NOT_ELIGIBLE` |
| S10 | already at 100% before `eligible` | neutral | n/a | `ALREADY_FULL` |
| S11 | `OK`, `R <= 1`, but no claim | (unreachable — see below) | n/a | `BASELINE_HANDLES` |

A hold, once taken, is **retained** while the state is S3/S4/S5/S6 and is
released only by reaching S1/S2. A degraded or unknown state never counts as
novel and never counts as benign.

**An existing hold is never released by a later degraded state**, and a degraded
state never releases a hold that was already taken.

**An episode that simply runs out of data is none of these.** If the last
available bar is before `eligible + 120` and no release occurred, the disposition
is `OBSERVATION_RIGHT_CENSORED`: the future is **unknown**, not lost. The full
rule is in §4.3.

#### 4.2.1 S11 is unreachable — but conservative hold is still a choice

Its precondition needs a *trusted* reference at `R <= 1` that makes no claim.
`reference_is_valid` conjoins exactly the claim gate's non-novelty conjuncts, so
at `R <= 1` the claim must be true; the analyzer scans every trusted-reference
observation for a counterexample (**0 found**) and
`test_c8_trusted_abstain_branch_is_unreachable_and_the_old_claim_is_withdrawn`
pins the implication.

**This finding is narrower than an earlier version of this document claimed, and
that earlier claim is withdrawn.** The scan shows only that the *trusted `R <= 1`
no-claim state* never occurs. It does **not** show that "abstain" and
"conservative hold" are the same behaviour, and it does **not** make conservative
hold a mathematical necessity. A policy could still route `DEGRADED`/`UNKNOWN`
states to the **unmodified baseline** — i.e. release the add-on exactly as `R0`
would — which is a *different design* that changes no A1–A7 threshold, no PTM
mathematics and no B3 clock. That alternative is named in the code as
`BASELINE_ON_DEGRADED_ALTERNATIVE`, is **documented but not implemented**, and is
**not** counted among the challengers.

**Consequence.** C1 implements a **conservative hold on insufficient evidence**.
That is Sophira's approved research choice for this challenger, and it is recorded
here as a **deliberate policy preference whose full opportunity cost is charged
against C1** — not as a forced outcome. Genuine abstain semantics on the degraded
branch would be a *second* design, and this revision does not evaluate it.
**`PENDING_SOPHIRA_APPROVAL`.**

### 4.3 Why a withhold can become permanent, and how it must be reported

`is_new_territory_claim` can be true **only while `R <= 1`**. This is not an
assumption: across all 33 fixtures there are **zero** counterexamples of a claim
at `R >= 2`, and `novelty_fresh` is literally `nclass in (UNVISITED, SPARSE)`.
`R` is not constant within an episode — it grows along the path — so a withhold
taken at `R = 2..4` can be permanent even while the trend continues.

The reporting consequence is explicit and non-negotiable:

* A withheld add-on is **censored**: its extra delay is **unbounded**, not zero.
* A censored add-on is **excluded** from every mean and max delay figure. It is
  **never** rendered as `0` additional bars.
* A **definite** withholding (state S8) is charged as **unbounded extra delay**
  plus **forgone large-trend harvest** — never as 0 bars.
* A fixture whose add-on disappears entirely is **not** a zero-cost outcome.
* `max_added_delay_vs_v02_bars = 0` must **never** be quoted as the empirical
  confirmation cost of this policy. It applies only to synthetic observations
  whose claim survives; `one_way_reference_genuine_trend` loses its add-on
  entirely and the constructed `true_trend` B3 clock yields **4 bars** of extra
  delay. Neither is zero.

#### 4.3.1 Disposition taxonomy — policy outcome vs follow-up completeness

**資料不足不是永久不加碼，也不能把未來未知的機會成本當作已實現損失。**
("Insufficient data is not a permanent no-add-on, and the opportunity cost of an
unknown future must not be booked as a realized loss.")

Every episode terminates in exactly one declared disposition. The distinction
that matters is between *what the policy decided* and *whether we were able to
watch long enough to see the decision resolve*:

| disposition | count (33 synthetic fixtures) | meaning | charged to C1? |
|---|---:|---|---|
| `PARENT_NOT_ELIGIBLE` | 10 | the parent never earned an add-on (path `P3`, or no usable B3). Not a PTM cost at all. | no |
| `OBSERVATION_RIGHT_CENSORED` | 14 | follow-up **incomplete**: the data ended before the predeclared decision horizon. A later release is **UNKNOWN**. | **no** — not evidence of loss |
| `POLICY_WITHHELD_THROUGH_EXPIRY` | 0 | withheld through the **complete** `eligible + 120` horizon. The only *definite* add-on loss. | yes |
| `BASELINE_DE_RISK_BEFORE_RELEASE` | 0 | the baseline itself de-risked/exited before any release; PTM withheld nothing. | no |
| `PROMOTED` | 9 | released and executed at an observed finite delay (here all `0` bars). | n/a |
| `BASELINE_HANDLES` | 0 | declared, **provably unreachable** (§4.2.1) | n/a |
| `ALREADY_FULL` | 0 | already at 100% before eligibility | n/a |

`OBSERVATION_RIGHT_CENSORED` is itself split, because the two halves mean
different things:

* **14 right-censored, of which 5 end *before* the eligible decision bar** —
  `one_tick_breakout` (eligible 132, last bar 130), `gappy_reference` (126 / 123),
  `crossed_but_not_closed` (127 / 124), `degenerate_history` (124 / 123),
  `degenerate_history_tick_fallback` (124 / 123). No decision bar was ever
  observed, so these fixtures carry **no information about C1's behaviour at
  all**. An earlier version of this document counted them as permanent
  suppressions; that was wrong.
* **9 right-censored with an open hold at the last bar** — a hold was genuinely
  in force when the data stopped, but the future is unknown.

**Interior missing-data boundary (2026-10-15):** reaching an expiry *index*
alone does not establish a fully observed policy horizon. For
`POLICY_WITHHELD_THROUGH_EXPIRY`, every decision bar from
`eligible = B3_break_t + 3` through `eligible + 120` (inclusive) must
have an actual timestamp/indexed `TerritoryObservation`. Missing observation
indexes trigger `OBSERVATION_RIGHT_CENSORED` even if the expiry index itself
exists. A **present** `DEGRADED/UNKNOWN` reading still counts as observed
and follows C1's declared conservative-hold rule. The
`observed_post_eligible_bars` counter counts existing observations, not an
inferred integer range. This rule is locked by the sparse-endpoint and
interior-gap deterministic regression. It does not authorize new outcomes
or change the baseline.

#### 4.3.2 The `14/23 = 60.9%` figure is WITHDRAWN

The earlier figure summed *right-censored* episodes (including the five fixtures
that never reached a decision bar) into a *permanent-withholding* count. It is
**withdrawn** and must not be quoted as a withholding probability, as a market
estimate, or as the basis for any cutoff.

**The only valid withholding denominator** is parent-eligible episodes whose
predeclared decision horizon was **fully observed**:

```
withheld_share = |POLICY_WITHHELD_THROUGH_EXPIRY|
               / |{parent-eligible AND follow-up complete}|
```

On the synthetic set that denominator is **9**, and the numerator is **0** — so
the synthetic withheld share is **0.0%**, and it is a *vacuous* 0% rather than
evidence of safety. Only **1 of 23** entitled fixtures reaches the 120-bar
post-eligible horizon at all (and it is promoted). **The synthetic fixtures are
far too short, relative to the predeclared horizon, to estimate the
permanent-withholding rate or C1's opportunity cost.** That measurement requires
the real B3 cohort. Reporting a synthetic percentage as if it were a withholding
probability would be unsupported.

#### 4.3.3 The zero "signal contradiction" count is an invariant, not evidence

The previous revision reported `newly-introduced suppressions = 0` as a success.
It is not. A withheld add-on can only be counted as a contradiction if a claim
exists at or after eligibility, but a claim *implies* `reference_is_valid`, so
this quantity is a **tautology of the gate itself**. It is now reported as
`c1_signal_gate_invariant_holds` and explicitly labelled
**INVARIANT, NOT EVIDENCE**. It establishes nothing about how often C1 removes
false-trend loss, and nothing about how much real trend it forgoes.

#### 4.3.4 What remains a genuine policy question

Whether C1's conservative hold is *acceptable* is a risk-appetite decision that
the synthetic set cannot answer, because the synthetic set cannot measure the
cost. Sophira has approved the conservative hold as C1's deliberate challenger
semantics; the **acceptable genuine full-horizon suppression share** is still
**`PENDING_SOPHIRA_APPROVAL`** (§7 rule 11).

### 4.4 Deterioration never mechanically promotes (P0.3)

An earlier draft released the hold "on the first completed close with `R <= 1`,
**or on benchmark deterioration, whichever comes first**". That is wrong and
contrary to the inherited risk management: it lets a *deteriorating* benchmark
**promote** exposure, i.e. it uses deterioration as a promotion trigger.

The frozen transition is:

```
deterioration at any bar  ->  BASELINE_DE_RISK_BEFORE_RELEASE
                              released          = False
                              first_executable  = None
                              extra_delay_bars  = None   (no observable delay)
                              followup_complete = True
                              withheld_definite = False  (PTM withheld nothing)
                              promotes          = never
```

**`BASELINE_DE_RISK_BEFORE_RELEASE` is deliberately *not* counted as a PTM
loss.** The position was closed by the baseline's own risk path; C1 did not
withhold it, and it is therefore neither observed nor censored — it is excluded
from the withholding numerator *and* from the evaluable denominator. Counting it
as a PTM cost would double-charge a decision the baseline made independently.

Deterioration is handled by the baseline's own de-risk / exit path. PTM never
adds on it. Pinned by `test_b2_deterioration_while_withheld_never_promotes` and
`test_b2b_de_risk_is_not_a_ptm_withholding`.

**Intermediate `R = 2..4`.** A bar in S3 neither promotes nor resets: the hold
continues and can only be released by returning to S1/S2. Because the frozen
rule cannot claim at `R >= 2`, a path that leaves `R <= 1` and never returns
becomes a definite withholding **only if the full post-eligible horizon is
observed**; otherwise it is `OBSERVATION_RIGHT_CENSORED`. Either way
`extra_delay_bars = None` and it is never reported as a fixed 0-bar or n-bar
delay. Pinned by
`test_b4_middle_band_r2_to_r4_is_withheld_and_named_in_the_reason`,
`test_b5_withholding_through_complete_expiry_is_definite_not_zero` and
`test_c7_long_period_box_addon_is_never_released`.

### 4.5 Next-bar execution contract

For every bar `t` the policy is evaluated on the **completed** close at `t`, and
the resulting order can execute **no earlier than `t + 1`**. A release therefore
carries

```
first_release_signal_bar = t*        # first bar whose completed close releases
first_executable_bar     = t* + 1
extra_delay_bars         = (t* + 1) - (eligible + 1)
```

so `extra_delay_bars >= 0` always, and `= 0` means "actionable on exactly the
bar the parent itself would have filled". No release may be placed at or before
`eligible`. Pinned by
`test_a2_a_release_fills_no_earlier_than_the_bar_after_its_signal`,
`test_a3_no_release_before_eligibility_even_with_claims_from_the_breakout`, and
`test_b9_no_future_leak_release_bar_is_prefix_stable` (a release already earned
by a prefix is unchanged by any later bar).

### 4.6 C2 is retired (`RETIRED`, historical record only)

**C2 is not an empirical candidate in this preregistration, and `o_min = 3` is
not approved.** The reason is a silent change of hypothesis, recorded here so it
cannot be re-adopted by accident.

The originally approved C2 was *"PTM Guard plus a historical **touch-occupancy**
`O`, with `O >= o_min` as an additional **hold** condition"* — a condition on a
*dwelling proportion*. What was implemented required **three consecutive
claiming bars** inside the parent's acceptance window before **release**. Three
things changed at once, none of them announced:

1. **The unit changed**: occupancy *proportion* → *bar count*.
2. **The direction changed**: an additional **hold** condition (which would make
   C2 stricter than C1) became an additional **release** precondition (making C2
   a *different* rule, not a strictly harsher one).
3. **The quantity changed**: `O` is occupancy of the territory; the dwell run is
   *claim persistence*, which is a different measurement on the same bars.

`o_min = 3` was never approved, and it must not be tuned now. The five-value
sensitivity sweep that appeared in the previous revision is retained in the
artifacts as historical evidence, explicitly marked
`RETIRED_NOT_AN_ACTIVE_CHALLENGER`, and is not a basis for any decision.

**What is retained.** C2 remains callable (`CHALLENGER_POLICIES` includes it,
`evaluate_addon` still runs it) so that the previously recorded evidence stays
reproducible and auditable. Tests
`test_c1_only_one_active_challenger_and_c2_is_retired` and
`test_c5_dwell_counts_the_parents_own_acceptance_window` pin both facts: C2 runs,
C1 is the only *active* challenger. **Acceptance is not endorsement.**

**Why C1 alone is sufficient.** C2 separated from C1 on only **1 of 33**
synthetic fixtures (`long_trend_unbounded_novelty`, release at 203 vs 205). A
challenger that cannot be distinguished from C1 on the available design evidence
adds a decision surface without adding information, and it adds a parameter
(`o_min`) with no sound basis for a value. Dropping it is the conservative choice
for the *programme*, not merely for the policy. Sophira's ruling on this point is
already **NO — retire C2, preregister C1 alone**; this section implements it.

### 4.7 The delay C1 must be charged against (corrected contract)

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

### 4.8 Real R0/B3 event integration and the frozen parent source (P0.4)

The synthetic fixtures contain **no** markup/markdown/B3 event. Their B3 timings
are *constructed stand-ins* (the structural escape bar plus the frozen
three-bar confirmation) and are used only to illustrate timing. They are **not**
market-derived and must never be presented as R0/B3 event statistics.

**The frozen parent event source is the Issue #76 Pine forward-logger export**
(`ISSUE76|schema=1`, `LOOKBACK = 5`, probe `0.25`), consumed by the parent's own
committed research modules:

| item | value |
|---|---|
| event source module | `analyze_issue78_retest_path_stage1.py` |
| policy module | `analyze_issue78_second_entry_economic_policy.py` |
| export glob | `/mnt/data/pine-logs-#76 Forward Logger*.csv` |
| marker | `ISSUE76\|schema=1` |
| event chain | Breakout → Acceptance → Retest → Resume |
| baseline | `R0_Immediate` — add immediately at `B3_break_t + 3` |
| paths that add at t+3 | `P0_NoTouch`, `P1_WickHold`, `P2_Reclaim` |
| path that never adds | `P3_FailedAcceptance` |
| no usable B3 | episode remains at Probe |

**Exact eligibility rule:** the add-on `FULL − PROBE = 0.75` becomes eligible at
`B3_break_t + CONFIRMATION_BARS` for `P0/P1/P2`; `P3` never adds; an episode
without a usable B3 stays at Probe and is **not** a PTM cost. `B1` in §3 maps to
the parent's frozen reference policies (`ProbeOnly` / `FormalHold`); there is
**no literal `B1` symbol in the parent repository**, and this prereg says so
rather than inventing one.

**Every real raw file is identified explicitly.** The operator-side rehearsal
consumed a **9-file, 50,459,542-byte** export. Because the data is private and
must not be committed (AGENTS.md rule 8), the committed record is
`artifacts/issue185_price_territory/issue185_real_cohort_manifest.json`
(schema `issue185-real-cohort-v1`), which carries per file: **name, byte size,
row count and SHA-256**, plus the parity observed values, the parent contract,
the count of feature-unavailable windows and the frozen width tertile edges. Its
flags are `feature_only: true`, `outcomes_computed: false`,
`raw_data_committed: false`. The manifest is **frozen provenance, not a
reproduction recipe**: CI cannot re-derive these numbers and must never present
them as if it could.

**Date and hashes.** Rehearsal date is recorded in the manifest; SHA-256 digests
are full 64-hex-character values per file. No aggregate or truncated digest is
used as an identifier.

**Parity check, frozen and pre-outcome.** The parent already asserts four
constants (`analyze_issue78_second_entry_economic_policy.py` L36–42 and its
assertion block): `EXPECTED_EVENTS = 68118`, `EXPECTED_EPISODES = 1624`,
`EXPECTED_B3_EVENTS = 997`, `EXPECTED_P12 = 236`. A **counts-only rehearsal**
against the real export reproduced all four (reconstruction error `5.6e-14`)
and established the causal path composition of the 997 B3 events:
`P0_NoTouch` 411, `P1_WickHold` 110, `P2_Reclaim` 126 → **647 add at t+3**;
`P3_FailedAcceptance` 350 never add. The rehearsal stops **before** any return,
PnL or performance quantity is computed, and `scipy.stats.rankdata` — used only
by the parent's outcome helpers — is stubbed to *raise* so that a stray outcome
call cannot pass silently.

**The export is not committed to this repository** (`/mnt/data`, operator-side).
Therefore CI asserts the parity **contract** (constants and path composition via
`ast`, without importing the scipy-dependent parent modules), and the
**rehearsal counts are recorded as a local contract with provenance**, not as a
CI-checkable step. Tokens: `test_e1_parity_constants_in_the_parent_source_match_the_contract`,
`test_e2_provenance_names_the_real_parent_contract`,
`test_e3_real_cohort_manifest_is_optional_and_never_fabricated` (which passes
whether or not the manifest is present, and cross-checks the frozen tertile
edges against the code).

**The private export must never become a required CI step.** The real-cohort
script `analyze_issue185_real_cohort.py` exits non-zero when it *is* pointed at
data and the parity constants disagree, but exits `2` with an explanatory message
when no export is present — so CI stays green without the private data.

**Feature availability on the real cohort (disclosed reduced power).** The
ex-ante range descriptor (§6.5) is unavailable for **336 of the 997** B3 events,
overwhelmingly because the 120-bar pre-probe window spans a coordinate reset
(243 windows with one reset, 81 with two, 6 with three = 330) and 6 more have
insufficient pre-probe history. The usable stratum is therefore **661 of 997
(66%)**. That is a real reduction in power and it is disclosed here rather than
smoothed over.

**Freeze rule for this section:** every constant above is pinned **without
reading any forward return outcome**. No outcome column, no `OUTCOMES` function
and no conditional/outcome helper of the parent module may be executed during
freeze.

### 4.9 Predeclared decision the run must answer

This patch proves only that the guard is **consistent, causal, discriminating and
non-delaying on synthetic paths**. It does **not** establish that it is
beneficial on a market population, and — because the synthetic fixtures cannot
reach the decision horizon — it does **not** measure the guard's cost either.
Three questions remain open and are the actual content of this prereg:

1. Does the A1 false-suppression cost (§2.2) stay near zero on real cohorts, or
   does it block a material share of genuine emerging trends?
2. **Does C1 remove false-trend add-ons without forgoing real large-trend
   harvest?** This must be answered on the real cohort as a *joint* comparison:
   the reduction in wide-box false-trend loss against the retention of real
   `MFE >= 8 ATR` harvest, plus the opportunity cost of waiting and the definite
   full-horizon suppression share (§6.5, §6.6).
3. Does PTM add separation **beyond** the non-duplication comparators in §7?

If question 1 or 3 fails, the correct verdict is rejection, not redesign.

## 5. Freeze list (must be committed before the run)

* instrument version string (`v0.2.2`) and the full config fingerprint, including
  `min_reference_cycles`, `min_envelope_covered_fraction`,
  `max_unobserved_gap_fraction`, `max_w_over_scale`, `anchor_policy` and
  `apply_phase2_guards = True`;
* **the swing-leg threshold formula, `CYCLE_SWING_FRACTION × (Q90 − Q10) = 10 ×
  w`** — the prose correction of §2 (P0.1). The formula is frozen *as
  implemented*; no threshold was re-chosen;
* **the C1 gate** as the full frozen claim rule and the **state table of §4.2**,
  including S7 (`BASELINE_DE_RISK_BEFORE_RELEASE`, deterioration never promotes)
  and S8 (episode expiry never auto-promotes);
* **the disposition taxonomy of §4.3.1** — the five canonical dispositions plus
  the two declared supplementary states, and the rule that
  `OBSERVATION_RIGHT_CENSORED` is never counted as a permanent no-add-on;
* **the abstain-branch scope correction of §4.2.1** — `BASELINE_HANDLES` is
  unreachable *in the trusted `R <= 1` no-claim state only*; conservative hold is
  recorded as C1's **explicit policy choice**, and the distinct
  `BASELINE_ON_DEGRADED_ALTERNATIVE` design is documented but **not** implemented
  and **not** counted as a challenger;
* **C2 is retired** (§4.6). Its historical parameter `o_min = 3` is
  **RETIRED and must not be tuned**, and it is **not** frozen as a run parameter.
  `ACTIVE_CHALLENGERS = (C1_PTM_GUARD,)`;
* **the next-bar execution contract of §4.5**, including that
  `extra_delay_bars = (t* + 1) − (eligible + 1)`;
* **the censoring rules of §4.3 and §6.6**: a withheld add-on is unbounded,
  excluded from delay statistics, and never reported as 0 bars; an
  insufficient-observation episode is never reported as a loss;
* **the parent event provenance and parity contract of §4.8**, including the
  four frozen constants, the export glob, the `P0/P1/P2`-adds / `P3`-never-adds
  rule, the statement that no literal `B1` symbol exists in the parent repo, and
  the committed real-cohort manifest (files, sizes, row counts, SHA-256);
* **the ex-ante wide-box stratum definition of §6.5** — `width_atr` over the 120
  completed pre-probe bars with the feature-only tertile edges
  `WIDTH_ATR_EDGES = (7.368, 11.9931)`, the `sustained_escape` exclusion, and
  the `distinct_values > 1` falsification test;
* the exact code commit SHA of the analyzer;
* the exact cohort manifest, FIGI-set hash and bar-date range — inherited
  unchanged from the Issue #76 export and the #78 studies;
* the metric definitions below, including every threshold used to *stratify*
  (which must be backward-looking only), and the policy cost metrics of §6.6;
* the **active candidate count (1: C1)** and the rejection rules in §7;
* the artifact paths and the hashing method.

**Freeze discipline.** Every item above is frozen **without reading any forward
return outcome**: no return, PnL, MFE/MAE, hit-rate or performance column may be
inspected, and no parent outcome function may be executed while freezing.

## 6. Measurement

### 6.1 Clock

* All decisions use completed closes; earliest executable action is `t+1`.
* Entry, promotion and reduction timestamps are the benchmark's own; PTM may
  only move the *promotion* timestamp within C1.
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

### 6.5 Stratification: the ex-ante range descriptor (definitions frozen before outcomes)

Every stratum below is defined on **backward-looking** quantities only, computed
from data available at or before the decision bar. No stratum may reference a
forward return, and the classification is frozen **before** any outcome is read.

#### 6.5.1 Why the earlier wide-box criteria were withdrawn

The previous revision defined the wide-box stratum with three conditions, none of
which is a classifier. All three are **withdrawn**:

| superseded criterion | why it fails |
|---|---|
| `spread / w = RADIUS_DIVISOR` | This is an **algebraic identity**, not a test. `w = (Q90 − Q10) / RADIUS_DIVISOR`, so `spread / w ≡ RADIUS_DIVISOR = 20` for *every* valid reference. The condition is identically true and **discriminates nothing**. |
| `R <= 1` **plus** an unfixed claim | This selects *sparse claimed territory*, not a wide box. It is a **signal state**, and it is the very thing C1 gates on — using it as a stratum would stratify on the treatment. |
| `sustained_escape()` | A **valid retrospective outcome label, but not ex-ante**. It scans every bar after the probe and asks whether the path left the envelope *and never returned*; the answer is only known after the fact. Using it to *decide* classification is a look-ahead and would let the stratum be chosen with knowledge of the outcome. |

`sustained_escape` is retained for **outcome-side reporting only** (as a forward
label of which trends were real). It is **excluded from the classifier**.

#### 6.5.2 The frozen ex-ante descriptor: reference width in ATR units

The stratum is the **`width_atr`** of the frozen pre-probe reference:

```
width_atr = (Q90(close_ref) − Q10(close_ref)) / mean_true_range(last 14 pre-probe bars)
```

computed by `ptm_range_regime.range_regime_at(bars, anchor)`, which slices
`bars[anchor − 120 : anchor]` and **never reads the anchor bar or any later bar**.
It is therefore causal by construction: appending arbitrary future bars cannot
change it (pinned by `test_f1_range_regime_is_causal_no_future_influence` and
`test_f2_range_regime_ignores_the_anchor_bar_and_reads_only_the_past`).

This is the "frozen reference's width scaled by a pre-probe ATR" formulation the
review asked for. It is:
* **ex-ante** — a function of the 120 completed pre-probe bars only;
* **parameter-light** — one window length (14 bars), not a fitted threshold;
* **discriminating** — unlike `spread / w`, it takes many distinct values.

A secondary descriptor, `reversals` (the frozen reference's confirmed cycle
count, binned `REV_0` / `REV_1` / `REV_2PLUS`) records **reference traversals**.
Its bins are integer counts, so it introduces no tuned boundary.

#### 6.5.3 Bins are frozen feature-only, before any outcome

```
WIDTH_ATR_EDGES = (7.368, 11.9931)      # tertiles of width_atr
NARROW : width_atr <  edge0
MID    : edge0 <= width_atr < edge1
WIDE   : width_atr >= edge1
```

These edges are the **tertiles of the feature itself** over the real B3 cohort
(`n = 661` usable events; min 1.5081, q33 7.368, q50 9.4442, q67 11.9931,
max 61.5838). They are computed from the **feature only** — no return, no PnL, no
MFE enters their derivation. They are frozen in `ptm_range_regime.WIDTH_ATR_EDGES`
and cross-checked against the committed manifest by
`test_e3_real_cohort_manifest_is_optional_and_never_fabricated`.

Because a tertile split is a property of the cohort, **any cohort change
recomputes the edges before measurement and re-freezes them**. The edges must
never be adjusted after seeing outcomes.

#### 6.5.4 Falsification test for the tautology failure mode

The failure that invalidated the earlier stratum was a criterion that was
identically true. The operational guard against repeating it:

> **`synthetic_distinct_width_atr_values` and the real distinct-value count must
> both be `> 1`.** A tautological criterion produces exactly `1`.

The analyzer computes this and reports it as `discriminates: true/false`. On the
33 synthetic fixtures the descriptor takes **7** distinct values (the fixtures
mostly share one boxed reference construction, so spread there is weak **by
design** and the count is a *sanity check*, not a claim about power). On the real
cohort it takes **661**.

#### 6.5.5 Disclosed reduced power

The descriptor is **unavailable for 336 of 997 real B3 events (34%)**: 330
windows span a coordinate reset (one to three resets) and 6 have fewer than 15
pre-probe bars. Such episodes are reported as `UNAVAILABLE` with an explicit
reason and are **excluded from the width stratum**; they are never silently
binned. The usable stratum is **661 of 997 (66%)**. This materially reduces the
power of the wide-vs-narrow comparison and is disclosed here rather than smoothed
over.

Other inherited strata (unchanged):

* temporal blocks (eras) and the sleeves already used by issue-78 studies. The
  **Issue #76 forward-logger export is the existing cohort manifest** and its time
  blocks are inherited unchanged from the #78 studies — the prereg does **not**
  introduce a new manifest, a new sleeve or a new date range;
* market and asset class, with equal-asset and adequate-breadth weighting.

**Cohort manifest (frozen).** The research cohort is the Issue #76 forward-logger
export (`ISSUE76|schema=1`), the same population behind `EXPECTED_EVENTS =
68118` / `EXPECTED_EPISODES = 1624`. Its per-instrument coverage, era blocks and
sleeve assignment are the ones the #78 modules already use. Any cohort whose
counts fail the §4.8 parity check is **rejected before measurement**, not
adjusted afterwards. The committed real-cohort manifest (§4.8) records the exact
files, sizes, row counts and SHA-256 digests.

### 6.6 Policy cost metrics for C1 (mandatory, censoring-aware)

**The comparison the study exists to make.** Two things must be measured *jointly*
and reported together, never separately:

1. **False-trend loss reduction** — how much wide-box / failed-trend damage
   (§6.2) C1 removes relative to `R0_Immediate` and to Warning-First, **within
   the wide (`width_atr`) stratum**.
2. **Real large-trend harvest retained** — how much of the real large-trend
   harvest (`MFE >= 8 ATR`) survives the withholding, again within the stratum.

Reporting (1) without (2) is exactly the error the review warned about: it would
let a guard that suppresses almost all genuine trends look like a success. The
primary result is the **Pareto pair**, not either number alone (§6.4).

Mandatory C1 outputs:

* **The five-category disposition accounting, with every category's count**, using
  the taxonomy of §4.3.1:
  `PARENT_NOT_ELIGIBLE`, `OBSERVATION_RIGHT_CENSORED`,
  `POLICY_WITHHELD_THROUGH_EXPIRY`, `BASELINE_DE_RISK_BEFORE_RELEASE`,
  `PROMOTED` — plus the two supplementary, declared states `BASELINE_HANDLES`
  and `ALREADY_FULL`. The counts must **sum to the episode total**; the analyzer
  zero-fills and asserts this.
* **Permanent-no-add-on share** = `POLICY_WITHHELD_THROUGH_EXPIRY` divided by
  **parent-eligible episodes with a complete observed horizon** (§4.3.2). The
  denominator must be stated with the numerator. `OBSERVATION_RIGHT_CENSORED`
  episodes are **excluded** from this denominator and reported separately, because
  their future is unknown.
* **Insufficient-observation share** = `OBSERVATION_RIGHT_CENSORED` divided by
  parent-eligible episodes, **split into** (a) episodes that never reached the
  eligible decision bar and (b) episodes with an open hold at the last bar. Only
  (b) carries any information favourable or unfavourable to C1, and even (b) is
  not evidence of loss.
* **Extra delay distribution over `PROMOTED` add-ons only** — reported as a
  distribution (median, quantiles, max), never as a single mean. Held add-ons are
  excluded and reported separately as unbounded (§4.3).
* **Exposure days at 25% instead of 100%** while a hold is in force, i.e. the
  capital actually forgone, and the same measure inside the wide stratum.
* **Trading cost and turnover** saved/incurred by the withheld add-ons.
* **Tail risk** — downside tail behaviour at 25% versus 100% exposure while held,
  since the guard's whole purpose is to avoid adding into failed trends.
* **Opportunity cost of add-on waiting** — for `PROMOTED` add-ons, the
  forgone `MFE` between `eligible` and `first_executable`, in ATR.
* **Forgone real-trend harvest** — for `POLICY_WITHHELD_THROUGH_EXPIRY` add-ons,
  the subsequent `MFE >= 8 ATR` region the 75% did not participate in.
* **Incrementality** — whether PTM adds separation **beyond** Core-2
  `Structure x Extension`, A9 and a plain 120-day Donchian gate, computed on the
  same cohort with the same clock and the same eligibility rule.
* **Cohort provenance** — the exact raw files, byte sizes, row counts and
  SHA-256 digests from the committed manifest (§4.8), plus the parity observed
  values and the count of feature-unavailable episodes.

**Invariant, not evidence.** The signal-gate consistency check (no
`POLICY_WITHHELD_THROUGH_EXPIRY` episode has a claim at or after `eligible`) must
be reported as `c1_signal_gate_invariant_holds` and labelled **INVARIANT, NOT
EVIDENCE**. It is a tautology of the gate (§4.3.3) and must never be presented as
a measure of protection or as a result.

**Explicit non-reports.** A withheld add-on is never entered into a mean delay,
never rendered as `0` additional bars, and `max_added_delay_vs_v02_bars = 0` is
never quoted as the confirmation cost (§4.3). A right-censored episode is never
counted as a permanent no-add-on.

## 7. Rejection / stop rules (predeclared)

Reject PTM, or stop the programme, if any of the following holds:

1. **Non-duplication.** PTM shows no incremental separation from Core-2
   `Structure × Extension`, from the A9 volatility percentile, or from a plain
   120-day Donchian gate on the same cohort.
2. **Latency purchase.** Any false-trend benefit is obtained by systematically
   arriving late: the first-claim lag distribution shifts right by more than a
   pre-declared margin, or the benefit disappears under a
   matched-latency control. **All latency is measured against the corrected
   `eligible_promotion_t = B3_break_t + 3` baseline** (§4.7); a delay computed
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
10. **Censoring dishonesty.** A withheld add-on is reported as a finite delay —
    in particular any headline that quotes
    `max_added_delay_vs_v02_bars = 0` as the policy's confirmation cost, or
    averages censored add-ons in as if they were `0` bars. A withheld add-on is
    unbounded and must be reported as withheld plus forgone harvest (§4.3, §6.6).
    Symmetrically, an **unobserved** add-on must not be reported as a **loss**:
    summing `OBSERVATION_RIGHT_CENSORED` episodes into a permanent-suppression
    count is the same error in the opposite direction, and it is what produced
    the withdrawn `14/23 = 60.9%` figure (§4.3.2).
11. **Permanent-suppression cost too high.** If, on the cohort, the
    **`POLICY_WITHHELD_THROUGH_EXPIRY` share of fully-observed parent-eligible
    episodes** is material **and** the forgone `MFE >= 8 ATR` harvest is large,
    the conservative hold is rejected as an exposure policy. The exact cut is not
    fixed here because it is a risk-appetite decision, not an engineering fact —
    **`PENDING_SOPHIRA_APPROVAL`**. The preferred form of the criterion is a
    **joint constraint** — maximum acceptable false-trend loss *given* a minimum
    retained `MFE >= 8 ATR` harvest — rather than a single number on either side.
    **No cut may be derived from the synthetic set**, whose withheld share is a
    vacuous `0/9` because the fixtures cannot reach the horizon (§4.3.2). The
    `14/23 = 60.9%` figure is **withdrawn** and must not appear in any cutoff.
12. **Deterioration used as a promotion trigger.** Any release triggered by
    benchmark deterioration rather than by an affirmative claim, anywhere in the
    implementation or the analysis, invalidates the run (§4.4).
13. **Invariant reported as evidence.** The signal-gate consistency check is a
    tautology of the claim gate (§4.3.3). Presenting it as evidence of protection
    — for example quoting "newly-introduced suppressions = 0" as a result — is a
    reporting failure. It must be labelled **INVARIANT, NOT EVIDENCE**, and it may
    not substitute for the joint false-trend-loss / harvest-retention comparison
    of §6.6. The check is asserted in CI as an invariant, not as a headline.
14. **Stratum tautology.** A wide-box stratum criterion that is identically true
    (or constant) across the cohort. `spread / w ≡ 20` was exactly this failure
    and is withdrawn (§6.5.1). The stratum must report its distinct-value count
    and satisfy `distinct_values > 1` on both the synthetic and the real set.

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

The v0.2.4 convergence round performed **no** forward outcome, PnL or MFE
computation. It repaired the disposition accounting, replaced the invalid
wide-box classifier and retired C2 from the active plan. It touched no A1–A7
threshold and no PTM mathematics. `PREREG DRAFT — NOT AUTHORISED` remains in
force, and the next step is a design ruling on the two `PENDING_SOPHIRA_APPROVAL`
items (§4.2.1 conservative-hold semantics and §7 rule 11's joint cutoff), not a
research run.
