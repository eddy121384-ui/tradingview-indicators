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
  `DEGRADED/UNKNOWN` and the 120-bar episode expiry. The **abstain option is
  shown to be provably unreachable**, so conservative hold is forced rather than
  chosen — see the pending item below.
* **P0.3 — deterioration must never mechanically promote.** §4.4 removes "or on
  benchmark deterioration, whichever comes first" as a *release* trigger;
  deterioration now yields `DE_RISK` and never promotes. §4.3 and §6.6 make
  permanent suppression report as **censored / unbounded extra delay** plus
  **missed big-trend harvest**, never as `0` bars.
* **P0.4 — real R0/B3 event integration and missing constants.** §4.8 pins the
  frozen parent event source (the Issue #76 forward-logger export consumed by
  the #78 modules), its parity check and the exact eligibility rule; §4.6 pins
  `o_min`; §5 freezes the exposure-policy decision; §6.5 fixes the objective
  pre-outcome wide-box stratum and the cohort manifest. All frozen **without
  reading any forward return outcome**.

It remains a **draft**: no outcome has been read, nothing is frozen, and no run
is authorised. **`PREREG DRAFT — NOT AUTHORISED.`**

**Pending Sophira rulings (not decidable from design alone).** Each is stated
with a primary recommendation and rationale in the referenced section:

| # | item | primary recommendation | section |
|---|---|---|---|
| 1 | exposure-policy semantics for `DEGRADED/UNKNOWN` | conservative hold (forced: abstain is provably unreachable) | §4.2 |
| 2 | `o_min` value for C2 | `o_min = 3` (largest before the synthetic cliff; equals the parent's `CONFIRMATION_BARS`) | §4.6 |
| 3 | acceptable censored share of add-on entitlements | no number fixed — a risk-appetite decision, not an engineering fact | §7 rule 11 |
| 4 | whether C2's thin synthetic separation (1 of 33) disqualifies it | keep exactly two challengers; make C2 harsher rather than adding a third | §4.6 |

Status of each: **`PENDING_SOPHIRA_APPROVAL`**. Nothing above is frozen by this
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

## 4. Challenger policies (exactly 2, minimal and interpretable)

Both challengers stay at the benchmark's 25% probe instead of promoting the
earned 75%. **The policy layer can only withhold or release an add-on the parent
has already earned. It never accelerates a promotion, never reduces exposure,
never sizes, and never alters B1's Warning-First or any other risk constraint.**

* **C1 — PTM Guard.** Withhold the earned 75% while the completed close at the
  decision bar does not carry a valid new-territory claim; release on the first
  completed close that does. Never a fixed delay.
* **C2 — PTM Guard with dwell condition.** As C1, but the release additionally
  requires a run of `o_min` consecutive claiming bars inside the parent's own
  three-bar acceptance window.

Both challengers consume the *same* frozen instrument.

**No third challenger is added, and no new parameter is searched.** Exactly one
new number enters the freeze — C2's `o_min` (§4.6) — and it is disclosed with
its full synthetic sensitivity.

### 4.1 The gate is the full claim gate, not the revisit band

**This replaces the earlier `HEAVILY_REVISITED`-only rule, which was an
information-level fail-closed masquerading as an exposure policy.** Gating on
the revisit band alone leaves the hole the prereg review identified:
`long_period_box` sits at `R = 1` (`SPARSE`), so a band-only rule would have
promoted its 75% even though its reference is
`DEGRADED_REFERENCE_ADEQUACY`. A revisit band is an *information* statement
about how often a level has been touched; it is not by itself an exposure
decision.

Both challengers therefore gate on the **frozen claim rule**:

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

| # | state of the completed bar `t` | C1 at `t` | C2 at `t` | releaseable later in this episode? | reported as |
|---|---|---|---|---|---|
| S1 | `OK`, `R <= 0` (`UNVISITED`) | release | release iff `dwell_run >= o_min` | yes | `PROMOTE` |
| S2 | `OK`, `R = 1` (`SPARSE`) | release | release iff `dwell_run >= o_min` | yes | `PROMOTE` |
| S3 | `OK`, `R = 2..4` (`REVISITED`) | withhold | withhold | only if `R` returns to `<= 1`, which the frozen rule cannot guarantee | `WITHHOLD_PENDING` → `WITHHOLD_CENSORED` |
| S4 | `OK`, `R >= 5` (`HEAVILY_REVISITED`) | withhold | withhold | as S3 | as S3 |
| S5 | any `DEGRADED_*` or `UNKNOWN`, any band | withhold (**conservative hold**) | withhold | only via S1/S2 | `WITHHOLD_PENDING` → `WITHHOLD_CENSORED` |
| S6 | observation absent at `t` | withhold | withhold | absent is not evidence | `WITHHOLD_PENDING` |
| S7 | benchmark deterioration at any `t` | `DE_RISK`, never promotes | same | no | `DE_RISK_BASELINE` |
| S8 | `t >= eligible + 120` | censored, never auto-promotes | same | no | `WITHHOLD_CENSORED` |
| S9 | parent path `P3`, or no usable B3 | `NOT_ELIGIBLE` | same | n/a | `NOT_ELIGIBLE` |
| S10 | already at 100% before `eligible` | neutral | same | n/a | `ALREADY_FULL` |
| S11 | `OK`, `R <= 1`, but no claim | abstain / baseline handles | same | n/a | `BASELINE_HANDLES` |

A hold, once taken, is **retained** while the state is S3/S4/S5/S6 and is
released only by reaching S1/S2. A degraded or unknown state never counts as
novel and never counts as benign.

**An existing hold is never released by a later degraded state**, and a degraded
state never releases a hold that was already taken.

**S11 is provably unreachable, and that is reported rather than hidden.** Its
precondition needs a *trusted* reference at `R <= 1` that makes no claim, but
`reference_is_valid` conjoins exactly the claim gate's non-novelty conjuncts, so
at `R <= 1` the claim must be true. The analyzer scans every trusted-reference
observation for a counterexample (0 found) and
`test_c8_abstain_branch_is_provably_unreachable` pins the implication.

**Consequence — the honest answer to the review's request to choose between
"abstain / baseline handles" and "conservative hold":** on the frozen instrument
the two are **not distinct behaviours**, so the choice cannot be exercised as a
policy parameter. C1 and C2 necessarily implement **conservative hold**. Genuine
abstain semantics would require weakening the policy gate *below* the claim
gate, which is an **instrument change** and therefore out of scope for this
freeze round. **`PENDING_SOPHIRA_APPROVAL`.**

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
* Permanent suppression is charged as **censored / unbounded extra delay** plus
  **missed big-trend harvest** — never as 0 bars.
* A fixture whose add-on disappears entirely is **not** a zero-cost outcome.
* `max_added_delay_vs_v02_bars = 0` must **never** be quoted as the empirical
  confirmation cost of this policy. It applies only to synthetic observations
  whose claim survives; `one_way_reference_genuine_trend` loses its add-on
  entirely and the constructed `true_trend` B3 clock yields **4 bars** of extra
  delay. Neither is zero.

Measured on the 33 synthetic fixtures, C1 releases **9** and censors **14** of
the **23** fixtures that have a parent add-on entitlement (60.9% censored). Of
those 14, **0** had a claim at or after the eligibility bar — C1 never
contradicts the signal it is built on. Most censored fixtures are deliberately
broken or guard-instrumentation cases; the **declared** genuine sustained
escapes are `one_tick_breakout` and `one_way_reference_genuine_trend`, and only
the latter is a clear opportunity cost. This share is the dominant honest cost
of the policy and is a **policy decision, not a bug** —
**`PENDING_SOPHIRA_APPROVAL`**.

### 4.4 Deterioration never mechanically promotes (P0.3)

An earlier draft released the hold "on the first completed close with `R <= 1`,
**or on benchmark deterioration, whichever comes first**". That is wrong and
contrary to the inherited risk management: it lets a *deteriorating* benchmark
**promote** exposure, i.e. it uses deterioration as a promotion trigger.

The frozen transition is:

```
deterioration at any bar  ->  ADDON_DE_RISK
                              released          = False
                              first_executable  = None
                              extra_delay_bars  = None    (censored)
                              missed_addon      = True
                              promotes          = never
```

Deterioration is handled by the baseline's own de-risk / exit path. PTM never
adds on it. Pinned by `test_b2_deterioration_while_withheld_never_promotes`.

**Intermediate `R = 2..4`.** A bar in S3 neither promotes nor resets: the hold
continues and can only be released by returning to S1/S2. Because the frozen
rule cannot claim at `R >= 2`, a path that leaves `R <= 1` and never returns is
reported permanently censored (`extra_delay_bars = None`, `censored = True`,
`missed_addon = True`). It is never reported as a fixed 0-bar or n-bar delay.
Pinned by `test_b4_middle_band_r2_to_r4_is_withheld_and_named_in_the_reason` and
`test_b5_permanent_absence_of_release_evidence_is_censored_not_zero`.

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

### 4.6 `o_min` for C2 — candidate values, declared before outcomes

`o_min` is the number of consecutive claiming bars required inside the parent's
own acceptance window `B3_break + 1 .. B3_break + 3`.

Counting the dwell over the parent's acceptance window is deliberate: counting
only from the eligibility bar makes C2 censor an ordinary genuine trend whose
claim run *is* the acceptance window. That variant was implemented, observed to
censor `true_trend`, and rejected — it is recorded in the module as a REJECTED
alternative.

**This is a design disclosure, not a parameter search: no market outcome is
consulted and the challenger count stays at two.** Sweeping `o_min` over the 33
synthetic fixtures:

| `o_min` | = parent `CONFIRMATION_BARS` | released | censored | mean delay (released) | max delay (released) | differs from C1 |
|---:|---|---:|---:|---:|---:|---:|
| 1 | no | 9 | 14 | 0.00 | 0 | **0 — degenerate, equals C1** |
| 2 | no | 9 | 14 | 0.11 | 1 | 1 |
| **3** | **yes** | **9** | **14** | **0.22** | **2** | **1** |
| 4 | no | 4 | 19 | 1.50 | 3 | 9 |
| 5 | no | 4 | 19 | 2.50 | 4 | 9 |
| 6 | no | 4 | 19 | 3.50 | 5 | 9 |

* `o_min = 1` is **degenerate**: C2 becomes exactly C1 and adds nothing.
* `o_min = 4` and above crosses a cliff: the released count collapses `9 → 4`
  and nine fixtures diverge from C1.
* **Primary recommendation: `o_min = 3`** — the largest value before the cliff,
  equal to the parent's own frozen `CONFIRMATION_BARS`, and the only candidate
  that reuses an already-frozen horizon instead of introducing a new number.
  **`PENDING_SOPHIRA_APPROVAL`.**
* Disclosed weakness: C2 differs from C1 on only **1 of 33** synthetic fixtures
  (`long_trend_unbounded_novelty`, release at 203 vs 205), so C2's
  distinguishing power on synthetics is thin. Its value must be judged on the
  real cohort, not here. If Sophira judges that thinness disqualifying, the
  correct response is to keep exactly two challengers and make C2 harsher, not
  to add a third.

### 4.7 The delay C1/C2 must be charged against (corrected contract)

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

**Parity check, frozen and pre-outcome.** The parent already asserts four
constants (`analyze_issue78_second_entry_economic_policy.py` L741–757):
`EXPECTED_EVENTS = 68118`, `EXPECTED_EPISODES = 1624`,
`EXPECTED_B3_EVENTS = 997`, `EXPECTED_P12 = 236`. A **counts-only rehearsal**
against a real export reproduced all four (reconstruction error
`5.6e-14`) and established the causal path composition of the 997 B3 events:
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
`test_e2_provenance_names_the_real_parent_contract`.

**Freeze rule for this section:** every constant above is pinned **without
reading any forward return outcome**. No outcome column, no `OUTCOMES` function
and no conditional/outcome helper of the parent module may be executed during
freeze.

### 4.9 Predeclared decision the run must answer

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
  `apply_phase2_guards = True`;
* **the swing-leg threshold formula, `CYCLE_SWING_FRACTION × (Q90 − Q10) = 10 ×
  w`** — the prose correction of §2 (P0.1). The formula is frozen *as
  implemented*; no threshold was re-chosen;
* **the C1/C2 gate** as the full frozen claim rule and the **state table of
  §4.2**, including S7 (`DE_RISK`, deterioration never promotes) and S8 (episode
  expiry never auto-promotes);
* **the abstain-branch finding of §4.2** — `BASELINE_HANDLES` is provably
  unreachable, so "conservative hold" is forced and is *not* a free parameter;
* **the challenger parameter `o_min` (declared here, before outcomes, and added
  to the fingerprint when C2 is instantiated)** with its recommended value 3 and
  the sensitivity table of §4.6;
* **the next-bar execution contract of §4.5**, including that
  `extra_delay_bars = (t* + 1) − (eligible + 1)`;
* **the censoring rules of §4.3 and §6.6**: a censored add-on is unbounded,
  excluded from delay statistics, and never reported as 0 bars;
* **the parent event provenance and parity contract of §4.8**, including the
  four frozen constants, the export glob, the `P0/P1/P2`-adds / `P3`-never-adds
  rule and the statement that no literal `B1` symbol exists in the parent repo;
* **the objective pre-outcome wide-box stratum definition of §6.5**,
  parameter-free and computed without any forward return;
* the exact code commit SHA of the analyzer;
* the exact cohort manifest, FIGI-set hash and bar-date range — inherited
  unchanged from the Issue #76 export and the #78 studies;
* the metric definitions below, including every threshold used to *stratify*
  (which must be backward-looking only), and the policy cost metrics of §6.6;
* the candidate count (2) and the rejection rules in §7;
* the artifact paths and the hashing method.

**Freeze discipline.** Every item above is frozen **without reading any forward
return outcome**: no return, PnL, MFE/MAE, hit-rate or performance column may be
inspected, and no parent outcome function may be executed while freezing.

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

Every stratum below is defined on **backward-looking** quantities only, computed
from data available at or before the decision bar. No stratum may reference a
forward return, and the classification is frozen **before** any outcome is read.

**Objective pre-outcome wide-box stratum (the D1 cohort).** The wide-box
stratum is the population on which the D1 defect must be eliminated, so its
definition cannot be hand-picked per fixture. It is defined by the
**parameter-free** classifier already in the analyzer:

```
sustained_escape(episode) = the completed path leaves the frozen reference
                            envelope (bar high > ref.max_high for a long /
                            bar low  < ref.min_low for a short) from the probe
                            onward AND never returns inside it
```

`sustained_escape` takes **no threshold parameter**, so it cannot be tuned to
the result. The stratum is then the set of opportunities whose pre-outcome
reference state is the wide-box regime, frozen as:

* `spread / w = RADIUS_DIVISOR` (the reference's inter-decile span is 20 × w),
  i.e. the reference box is wide relative to its own quantile width; **and**
* the armed-gated revisit count at the decision bar is `R <= 1`; **and**
* the episode produced a claim under **v0.2** (the unfixed signal).

Membership is computed from the frozen reference and the v0.2 readout **only**;
whether the trade then worked is an outcome and is never an input.

* wide range versus narrow range, using the backward-looking objective
  definition frozen above;
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
adjusted afterwards.

### 6.6 Policy cost metrics (mandatory, and censoring-aware)

The C1/C2 evaluation must report:

* **censored share** of the add-on entitlements, alongside its complement;
* **extra delay distribution over released add-ons only**, never a single mean;
  censored add-ons are **excluded** and reported separately as unbounded;
* **exposure-days at 25% instead of 100%** while a hold is in force, i.e. the
  capital actually forgone;
* **missed big-trend harvest**: for every censored add-on, the subsequent
  `MFE ≥ 8 ATR` region the 75% did not participate in;
* **newly-introduced suppression count**: opportunities where the phase-2 signal
  emitted a claim at or after `eligible` and the policy still withheld. This must
  be **0**; a non-zero value means the policy contradicts the signal it is built
  on;
* an explicit **non-report**: a censored add-on is never entered into a mean,
  never rendered as `0` additional bars, and
  `max_added_delay_vs_v02_bars = 0` is never quoted as the confirmation cost
  (§4.3).

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
    averages censored add-ons in as if they were `0` bars. A censored add-on is
    unbounded and must be reported as censored plus missed harvest (§4.3, §6.6).
11. **Permanent-suppression cost too high.** If, on the cohort, the censored
    share of add-on entitlements is material **and** the missed big-trend
    harvest is large, the conservative hold is rejected as an exposure policy.
    The exact cut is not fixed here because it is a risk-appetite decision, not
    an engineering fact — **`PENDING_SOPHIRA_APPROVAL`**. On the synthetic set
    the censored share is **14 of 23 (60.9%)** with **0** newly-introduced
    suppressions and **2** declared genuine sustained escapes (§4.3); that is a
    disclosure, not a result.
12. **Deterioration used as a promotion trigger.** Any release triggered by
    benchmark deterioration rather than by an affirmative claim, anywhere in the
    implementation or the analysis, invalidates the run (§4.4).
13. **Signal contradiction.** A non-zero newly-introduced suppression count —
    i.e. the policy withholds an add-on for which the phase-2 signal emitted a
    claim at or after `eligible`. This must be `0` and is asserted in CI.

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
