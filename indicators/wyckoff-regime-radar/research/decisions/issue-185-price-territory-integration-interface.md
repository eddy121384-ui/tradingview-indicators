# Issue #185 — PTM v0.2 integration interface (draft, information-only)

**Status:** interface draft. No production patch, no Pine, no sizing rule, no
threshold. This document describes how the inherited model *would* consume PTM
evidence if a later, independently preregistered challenger is authorised.

Related: `issue-185-price-territory-engineering-review-finding.md`,
`issue-185-price-territory-prereg-draft.md`.

## 1. Boundary

Four layers are kept explicitly separate. PTM lives only in layer 4 as an
*evidence* channel.

| layer | owner | PTM may | PTM must not |
|---|---|---|---|
| 1. CONTEXT | Core-2 `Structure × Extension` (+ optional A9 volatility overlay as risk context) | read, label the boundary | substitute for it, or be promoted to an entry trigger |
| 2. PROBE | frozen benchmark `formal Markup/Markdown → 25% probe` | annotate each probe | create, suppress, resize or retime a probe |
| 3. EARNED EXPOSURE | frozen benchmark `B3 / P0–P3 3-bar acceptance → 100% at t+3 for P0/P1/P2` | emit evidence aligned to the existing promotion date | define new promotion dates, new percentages, or new gates |
| 4. DEFENSE + PTM EVIDENCE | Warning-First and hard stop/risk budget are independent; PTM is a challenger evidence layer | report state, earliest observability, deterioration | override, multiply, delay or bypass any defense rule |

Two inherited research lines stay distinct: legacy **R0 benchmark** (execution
policy comparator) and the newer **Core-2 context** track. PTM does not merge
them and does not treat Core-2 as an entry engine.

## 2. Causal state diagram

```
                          (completed close t, actionable t+1)
   CONTEXT (Core-2)                 PROBE (frozen benchmark)
        |                                   |
        |                                   | first probe at t0
        |                                   v
        |                      +--------------------------+
        |                      |  FREEZE reference        |
        |                      |  bars[t0-120 : t0]       |
        |                      |  w, unit, direction      |
        |                      +------------+-------------+
        |                                   |
        v                                   v
   +---------------------------------------------------------------+
   |  PTM EVIDENCE  (information only, recomputed every close)      |
   |                                                                |
   |   OLD-TERRITORY CAUTION  <-- R high / O high / N low           |
   |   NO-EVIDENCE-YET        <-- R == 1 (SPARSE)                   |
   |   NEW-TERRITORY EVIDENCE <-- R == 0 (UNVISITED) + validity OK  |
   |   DETERIORATION          <-- N falls back after a claim        |
   |   PROGRESS / STAGNATION  <-- separate channel, NOT mixed in    |
   |   UNKNOWN / DEGRADED     <-- fail closed, no claim             |
   |   SCALE-BREAK SUSPECT    <-- price unit broken, no claim       |
   +-------------------------------+-------------------------------+
                                   |
                (no automatic action; evidence only)
                                   v
   EARNED EXPOSURE (frozen: 25% probe, t+3 promotion for P0/P1/P2)
                                   |
                                   v
   DEFENSE (Warning-First, hard stop) -- independent, never bypassed
```

The exact claim rule, stated once so downstream code cannot misread it:

```
is_new_territory_claim  ==  validity == OK
                        and  reference_coverage == 1.0
                        and  revisit_episodes <= 1     # UNVISITED or SPARSE
                        and  not suspect_scale_break
```

`R == 1` (class `SPARSE`) **does** raise the claim flag even though the diagram
lists it under "no-evidence-yet": the class label describes evidence strength,
the boolean describes whether that closed bar is permitted to claim. A consumer
that wants only the strongest state must test `novelty_class == "UNVISITED"`
explicitly instead of the boolean.

Overlapping probes: under the frozen default `first_probe_wins` the first probe
of an episode freezes the reference; later probes inside the same opportunity
are attached as re-probes and **do not** reset evidence maturity. A new episode
opens only after the reference window is fully stale (120 bars) or when the
benchmark emits a probe while no episode is open.

## 3. Contract

### Inputs

| name | type | notes |
|---|---|---|
| `bars` | ordered `open, high, low, close, valid, label` | completed bars only; `valid=False` marks a known-missing session |
| `probes` | ordered `(index, direction ∈ {+1, −1})` | produced by the inherited model; PTM never generates one |
| `price_unit` | positive tick / price quantum, optional | only used when the reference inter-quantile spread is 0, and only under an explicit opt-in |
| `config` | frozen constants | `reference_bars=120`, quantiles 0.10/0.90, divisor 20, outer ×2, acceptance window 3, anchor policy, touch mode |

### Outputs (per probe episode, per completed close)

| output | meaning |
|---|---|
| `revisit_episodes` | old-region independent visit count `R` |
| `occupancy` | old-region dwell share `O` (separate from `R`, never fused) |
| `longest_inner_run` | longest uninterrupted reference touching run |
| `novelty` | `1/(1+R)` — descriptive, **not** a probability |
| `novelty_class` | `UNVISITED / SPARSE / REVISITED / HEAVILY_REVISITED` |
| `acceptance_trace` | mean novelty over the last ≤3 post-anchor closes, live from close 1 |
| `evidence_bars` | accumulated evidence maturity `min(3, t−t0+1)` |
| `frontier_progress` | signed distance beyond the frozen extreme, in `w` units (context only) |
| stagnation diagnostics | `days_since_best_frontier`, `frontier_change_3`, `progress_3_w`, `range_3_w`, `bars_since_significant_progress`, `stall_flag` — **unsolved problem, reporting only** |
| `is_new_territory_claim` | descriptive claim; false unless validity is `OK` |
| `observable_at_bar` / `actionable_at_bar` | `t` and `t+1` (next-bar action) |
| `validity`, `validity_detail` | `OK`, `DEGRADED_*`, `UNKNOWN_*` — fail closed |
| `suspect_scale_break` | latched data-quality prompt (split/roll/unit), never a gate |

### A1 / A2 / A3 reference-quality outputs (phase 2, implemented)

These are reference-level facts, reported on every observation. They gate the
claim through `allows_new_territory_claim`, never by suppressing output.

| output | meaning |
|---|---|
| `swing_legs`, `reference_cycle_count` | confirmed swing legs and round trips in the frozen window; `legs / 2.0`, a trailing unpaired leg counts 0.5. A leg needs a reversal of the running extreme by `CYCLE_SWING_FRACTION` (`0.5`) × `(Q90 − Q10)` = `10 × w`, so a monotone window yields 0 legs |
| `reference_adequacy_ok` | `False` when the window has no complete round trip or leaves an unobserved envelope gap |
| `envelope_covered_fraction`, `max_unobserved_gap_fraction`, `max_unobserved_gap_w` | how much of the reference price envelope is actually observed, and the largest hole in it |
| `episodes_per_cycle` | `R / reference_cycle_count` — the **market-speed-comparable** revisit rate; `None` when no complete cycle exists |
| `revisit_density` | `R / n_valid` — per-bar density; `0.0` is a legitimate measured zero |
| `comparability_status` | `COMPARABILITY_OK` / `COMPARABILITY_NO_COMPLETE_CYCLE` / `COMPARABILITY_REFERENCE_UNUSABLE` |
| `scale_reference`, `w_over_scale`, `scale_state` | `abs(median close)` denominator, `w / scale_reference`, and `SCALE_STABLE` / `SCALE_UNSTABLE` / `SCALE_UNKNOWN` |

Precedence when several guards fire, and every triggered reason is listed in
`validity_reasons`:

1. `DEGRADED_DEGENERATE_REFERENCE` (tick fallback)
2. `DEGRADED_SCALE_UNSTABLE` (A3)
3. `DEGRADED_REFERENCE_ADEQUACY` (A1)
4. `DEGRADED_REFERENCE_COVERAGE`
5. `OK`

## 4. The timing contract (corrected)

An earlier version of this document said "the benchmark promotes earned exposure
at `t+3`", where `t` was the probe. **That is wrong and it has been removed.**
The frozen #78 mechanics are: a new formal Markup/Markdown emits a 25% probe,
then the **first usable post-entry B3 breakout** is followed by three completed
observation bars `P0..P2`, and those bars become eligible at `B3 + 3`. The probe
is not the breakout.

Six timestamps are therefore tracked separately and must never be conflated:

| timestamp | meaning | owner |
|---|---|---|
| `probe_t0` | the 25% probe bar | inherited model |
| `B3_break_t` | the first qualifying post-entry breakout bar | inherited model |
| `B3_confirmation_t` | `B3_break_t + 3` (end of `P0..P2`) | inherited model |
| `eligible_promotion_t` | bar at which promotion may be decided = `B3_confirmation_t` | inherited model |
| `PTM_observation_t` | the close at which PTM evidence exists | this indicator |
| `next_executable_t` | `max(eligible_promotion_t, PTM_observation_t) + 1` | joint |

`eligible_promotion_t` is **`B3_break_t + 3`, never `probe_t0 + 3`**. The naive
probe-based baseline is retained only so its error stays measurable; measured on
the synthetic clock it is 10 bars too early for a breakout 10 bars after the
probe (`build_promotion_clock`, `ptm_promotion_clock.py`).

The synthetic fixtures in this review contain **no markup/markdown/B3 event**.
Any promotion bar quoted below is a **constructed** stand-in and is labelled as
such; it is not an observation about the inherited model.

## 5. BEFORE / AFTER — Case A, large box

Fixture `wide_box_traversal`. Probe at `probe_t0 = 120`. Because the synthetic
path has no B3 event, two breakout timings are constructed explicitly.

### Construction A1 — breakout coincident with the probe (`B3_break_t = 120`)

This is the only construction under which the old `probe + 3` text happened to be
numerically right; it is a special case, not the general rule.

| bar | close | benchmark | PTM R | PTM N | class | earliest PTM action |
|---:|---:|---|---:|---:|---|---|
| 120 = `probe_t0` = `B3_break_t` | 102.00 | 25% probe issued | 7 | 0.1250 | HEAVILY_REVISITED | close 120 → action 121 |
| 121 | 104.00 | probe | 12 | 0.0769 | HEAVILY_REVISITED | 122 |
| 122 | 106.00 | probe | 12 | 0.0769 | HEAVILY_REVISITED | 123 |
| **123** = `eligible_promotion_t` | **108.00** | **confirmation complete; promotion decidable** | **12** | **0.0769** | HEAVILY_REVISITED | **124** |
| 128 | 118.00 | promoted | 6 | 0.1429 | HEAVILY_REVISITED | 129 |
| 168 | 120.01 | promoted | 6 | 0.1429 | HEAVILY_REVISITED | 169 |

### Construction A2 — breakout 10 bars after the probe (`B3_break_t = 130`)

The realistic case. `B3_confirmation_t = eligible_promotion_t = 133`;
`next_executable_t = 134`.

| quantity | value |
|---|---|
| `probe_t0` | 120 |
| `B3_break_t` | 130 |
| `B3_confirmation_t` = `eligible_promotion_t` | 133 |
| naive (`probe + 3`) baseline | 123 |
| **naive baseline error** | **10 bars too early** |
| `PTM_observation_t` (probe close) | 120, actionable 121 |
| PTM vs eligibility | `PTM_EARLIER` |
| **PTM extra delay** | **0 bars** |

* **New indicator's earliest information** is the probe close itself
  (`actionable_at_bar = 121`), independent of when the breakout arrives.
* **PTM informs the promotion decision before it is decidable** in both
  constructions, and it **never changes its mind** — 53 post-probe bars,
  including the apparent rallies to 118, 119 and one tick above 120, produce
  **zero** new-territory claims.
* The apparent rally to 118 at bar 128 yields N = 0.143: the indicator refuses to
  read magnitude, slope or volatility as novelty.
* Phase-2 guard status of this reference: `reference_cycle_count = 6.0`,
  `reference_adequacy_ok = True`, `scale_state = SCALE_STABLE`
  (`w/scale = 0.00727`), validity `OK`.

**Deferred, not decided here:** whether a sustained HEAVILY_REVISITED state
should hold the earned 75%. That is a preregistered policy challenger
(`PTM Guard`), and it needs an explicit release rule.

## 6. BEFORE / AFTER — Case B, genuine emerging trend

Fixture `true_trend` (identical post-anchor path to `fake_breakout` through the
first close beyond the envelope). Probe at `probe_t0 = 120`.

| bar | close | benchmark | PTM R | PTM N | acceptance | class | earliest PTM action |
|---:|---:|---|---:|---:|---:|---|---|
| 120 | 103.00 | 25% probe issued | 7 | 0.1250 | 0.125 | HEAVILY_REVISITED | 121 |
| 123 | 112.00 | probe | 12 | 0.0769 | 0.077 | HEAVILY_REVISITED | 124 |
| 125 | 118.00 | probe | 6 | 0.1429 | 0.099 | HEAVILY_REVISITED | 126 |
| 126 | 120.00 | probe | 6 | 0.1429 | 0.121 | HEAVILY_REVISITED | 127 |
| **127** | **121.60** | probe | **0** | **1.0000** | 0.429 | UNVISITED | **128** |
| 129 | 126.00 | probe | 0 | 1.0000 | **1.000** | UNVISITED | 130 |
| 130 | 129.00 | probe | 0 | 1.0000 | 1.000 | UNVISITED | 131 |

The promotion bar depends entirely on when the constructed breakout is placed,
which is exactly why the contract had to be fixed:

| construction | `B3_break_t` | `eligible_promotion_t` | `PTM_observation_t` | PTM vs eligibility | **PTM extra delay** |
|---|---:|---:|---:|---|---:|
| breakout coincident with probe | 120 | 123 | 127 | `PTM_LATER` | **4 bars** |
| breakout 10 bars after probe | 130 | 133 | 127 | `PTM_EARLIER` | **0 bars** |

The old `probe + 3` text would have reported the second row as a 4-bar delay too,
by comparing PTM at 127 against the fictional baseline of 123 instead of the real
133. **The measured extra delay is 0 or 4 bars depending on the breakout timing,
never a fixed number** — and in no case is it a fixed waiting period: the guard
releases as soon as `R` reaches 0, which here takes 4 closes because the fuzzy
band still overlaps old territory at 120.00 (N = 0.143, `F` = 0.000).

Phase-2 guard status of this reference: `reference_cycle_count = 6.0`,
`reference_adequacy_ok = True`, `scale_state = SCALE_STABLE`, validity `OK`. The
phase-2 guards change **nothing** here: the v0.2 and guarded signals both first
fire at bar 127 with zero added delay.

### The honest limitation this pair exposes

`true_trend` and `fake_breakout` are **identical** through bar 127 inclusive.
The indicator changes state on the same close that a fake breakout would, with
the same value. The correct conclusion is narrow:

* **those two specific paths, at that specific timestamp, cannot be separated by
  any causal rule** — the information is not present in the data at that bar;
* therefore PTM cannot support a "fast-evidence" earlier add at the first escape
  close, and it is reasonable **not** to authorise fast adds;
* what separates the two cases is what happens **after** the claim, which is by
  construction unavailable in advance;
* the real trade-off — a quicker add exposed to fake breakouts versus a slower
  add that pays a confirmation tax — is **not removed** by this design.

**What this does not establish (earlier draft overclaimed here):** it does *not*
establish that first-day novelty carries zero conditional probability
information across a market population. Two hand-built paths agreeing at one
timestamp is a statement about those paths, not a population-level measurement.
That stronger claim has been removed and would require a forward study that this
phase is explicitly not authorised to run.

## 7. Case C — the long-period box (the blocker, now closed)

Fixture `long_period_box`. The frozen 120-bar window is a single slow one-way
ramp (105.00 → 118.00), i.e. **no round trip at all**, and the post-anchor path
oscillates inside the resulting wide band (119 → 110 → 119).

Under v0.2 this produced a **claim at close 112, inside the box** — the false
release that made the promotion-guard proposal unsafe. Under phase 2 it produces
**zero claims**:

| quantity | v0.2 | phase 2 |
|---|---:|---:|
| first claim bar | 112 | — (none) |
| claim bars in the episode | 12 | **0** |
| `validity` | `OK` | `DEGRADED_REFERENCE_ADEQUACY` |
| `swing_legs` | — | 1 |
| `reference_cycle_count` | — | 0.5 |
| `reference_adequacy_ok` | — | `False` |
| `reference_coverage` | 1.000 | 1.000 |
| `envelope_covered_fraction` | 1.000 | 1.000 |
| `max_unobserved_gap_fraction` | 0.000 | 0.000 |
| `scale_state` | `SCALE_STABLE` | `SCALE_STABLE` |
| `comparability_status` | — | `COMPARABILITY_NO_COMPLETE_CYCLE` |
| `episodes_per_cycle` | — | `None` |

A1 is the **only** guard that catches this case: coverage, envelope and scale are
all healthy. Lowering only `min_reference_cycles` to 0.0 reopens the claim and
changes nothing else about the observation, so the guard is a genuine single
point of control rather than an accidental interaction.

This is exactly the "insufficient evidence" outcome the task's governing
principle asks for: the indicator refuses to certify novelty from a window that
never established a region to be novel relative to.

**The cost, stated plainly:** the same guard also refuses
`one_way_reference_genuine_trend`, a real sustained escape to 160.00 behind a
one-way reference. That suppression is reported in
`issue185_ptm_phase2_comparison.csv` and is a deliberate trade, not an oversight.

## 8. What this interface deliberately does not do

* No new percentage steps (no `25→50→75→100` ladder).
* No default 5-day (or any fixed) delay on profitable breakouts.
* No threshold at which PTM forces a hold, a release, an add or a reduction.
* No modification of the 25% probe, the t+3 promotion, or any stop/risk rule.
* No reading of PTM as a standalone entry signal.
* No claim that a PTM state is right; only that it is observable, causal and
  reportable at a stated bar.

## 9. Interface risks carried into the preregistration

1. **Anchor drift (D9).** If a live implementation re-anchors per probe
   instead of per opportunity, evidence maturity silently restarts and the
   comparator changes. The anchor policy must be frozen.
2. **Validity plumbing.** If a degraded reference silently falls back to
   "unknown = treat as new", the guard fails open. The contract is fail-closed:
   `DEGRADED_*` produces numbers but **no** claim.
3. **Adjustment/roll feed.** The price-ratio scale-break screen is a weak
   prompt with known false positives and false negatives. A later
   implementation must consume an explicit adjustment/roll field rather than
   infer it from price.
4. **Stagnation.** The interface exposes stagnation but does not act on it.
   Treating `stall_flag` as a validated reduction trigger would be an
   unauthorised rule change and is out of scope.
