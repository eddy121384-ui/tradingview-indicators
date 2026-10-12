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

## 4. BEFORE / AFTER — Case A, large box

Fixture `wide_box_traversal`. Benchmark probe at `t0 = 120`; the frozen
benchmark promotes earned exposure at `t+3`.

| bar | t | close | benchmark | PTM R | PTM N | class | earliest PTM action |
|---:|---:|---:|---|---:|---:|---|---|
| 120 | t0 | 102.00 | 25% probe issued | 7 | 0.1250 | HEAVILY_REVISITED | close 120 → action 121 |
| 121 | t+1 | 104.00 | probe | 12 | 0.0769 | HEAVILY_REVISITED | 122 |
| 122 | t+2 | 106.00 | probe | 12 | 0.0769 | HEAVILY_REVISITED | 123 |
| **123** | **t+3** | **108.00** | **baseline promotes to full** | **12** | **0.0769** | HEAVILY_REVISITED | **123** |
| 128 | t+8 | 118.00 | full | 6 | 0.1429 | HEAVILY_REVISITED | 129 |
| 168 | t+48 | 120.01 | full | 6 | 0.1429 | HEAVILY_REVISITED | 169 |

* **New indicator's earliest information:** the probe close itself
  (bar 120, lenient state already visible; `actionable_at_bar = 121`).
* **Original model's add time:** bar 123.
* **PTM can inform the promotion decision 3 bars before it happens, and it
  never changes its mind** — 53 post-probe bars, including the apparent rallies
  to 118, 119 and one tick above 120, produce **zero** new-territory claims.
* The apparent rally to 118 at bar 128 yields N = 0.143, i.e. the indicator
  refuses to read magnitude, slope or volatility as novelty.

**Deferred, not decided here:** whether a sustained HEAVILY_REVISITED state
should hold the earned 75%. That is a preregistered policy challenger
(`PTM Guard`), and it needs an explicit release rule.

## 5. BEFORE / AFTER — Case B, genuine emerging trend

Fixture `true_trend` (identical post-anchor path to `fake_breakout` through the
first close beyond the envelope). Probe at `t0 = 120`; benchmark promotes at
`t+3`.

| bar | t | close | benchmark | PTM R | PTM N | acceptance | class | earliest PTM action |
|---:|---:|---:|---|---:|---:|---:|---|---|
| 120 | t0 | 103.00 | 25% probe issued | 7 | 0.1250 | 0.125 | HEAVILY_REVISITED | 121 |
| **123** | **t+3** | **112.00** | **baseline promotes to full** | **12** | **0.0769** | 0.077 | HEAVILY_REVISITED | 123 |
| 125 | t+5 | 118.00 | full | 6 | 0.1429 | 0.099 | HEAVILY_REVISITED | 126 |
| 126 | t+6 | 120.00 | full | 6 | 0.1429 | 0.121 | HEAVILY_REVISITED | 127 |
| **127** | **t+7** | **121.60** | full | **0** | **1.0000** | 0.429 | UNVISITED | **128** |
| 129 | t+9 | 126.00 | full | 0 | 1.0000 | **1.000** | UNVISITED | 130 |
| 130 | t+10 | 129.00 | full | 0 | 1.0000 | 1.000 | UNVISITED | 131 |

* **New indicator's earliest new-territory evidence:** bar 127 (the first close
  beyond the frozen envelope), `actionable_at_bar = 128`.
* **Original model's add time:** bar 123 — i.e. **PTM cannot confirm anything
  before the baseline promotion in this fixture**, and a PTM Guard would delay
  the promotion to full by **4 bars**.
* That 4-bar delay is **data-dependent**, not a fixed waiting period: the guard
  releases as soon as `R` reaches 0, which here takes 4 closes because the fuzzy
  band still overlaps old territory at 120.00 (N = 0.143, `F` = 0.000).
* Acceptance maturity reaches 1.000 at bar 129 without any extra waiting beyond
  the three-close window.

### The honest limitation this pair exposes

`true_trend` and `fake_breakout` are **identical** through bar 127 inclusive.
The indicator changes state on the same close that a fake breakout would, with
the same value. Therefore:

* PTM cannot support any "fast-evidence" earlier add at the first escape close;
* the only thing that separates the two cases is what happens **after** the
  claim, which is by construction not available in advance;
* the real trade-off — a quicker add that is exposed to fake breakouts versus a
  slower add that pays a confirmation tax — is **not removed** by this design.

## 6. What this interface deliberately does not do

* No new percentage steps (no `25→50→75→100` ladder).
* No default 5-day (or any fixed) delay on profitable breakouts.
* No threshold at which PTM forces a hold, a release, an add or a reduction.
* No modification of the 25% probe, the t+3 promotion, or any stop/risk rule.
* No reading of PTM as a standalone entry signal.
* No claim that a PTM state is right; only that it is observable, causal and
  reportable at a stated bar.

## 7. Interface risks carried into the preregistration

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
