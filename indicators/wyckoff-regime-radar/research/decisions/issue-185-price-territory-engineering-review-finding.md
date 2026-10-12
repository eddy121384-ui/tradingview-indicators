# Issue #185 — Price Territory Memory v0.2: independent engineering review

**Status:** DESIGN-FEASIBILITY FINDING. Synthetic deterministic fixtures only.
No market data, no historical returns, no strategy backtest, no parameter
search, no OOS5 contact, no Pine and no production change, no merge.

| field | value |
|---|---|
| Issue | [#185](https://github.com/eddy121384-ui/tradingview-indicators/issues/185) |
| Parent | [#78](https://github.com/eddy121384-ui/tradingview-indicators/issues/78) (stays open) |
| Design authority | Sophira v0.1 [#6117440344](https://github.com/eddy121384-ui/tradingview-indicators/issues/185#issuecomment-6117440344), v0.2 [#6117510142](https://github.com/eddy121384-ui/tradingview-indicators/issues/185#issuecomment-6117510142) |
| Branch | `research/issue-185-price-territory-engineering-review` |
| Base branch | `research/issue-78-market-structure-dimension-audit` @ `e316d19` |
| Base lineage | `e316d19` (A9 finding) → `04a982c` (A5 untouched OOS4 validation of causal Core-2) → `61724c2` (A4 Core-2) |
| Not based on | `research/issue-78-trigger-layer-discovery`, `research/issue-78-failed-break-*` (frozen event side-branch) |
| Artifacts | `indicators/wyckoff-regime-radar/research/artifacts/issue185_price_territory/` |
| Tests | `python -m pytest -q test_issue185_price_territory.py` → **67 passed** |
| Runner | `python analyze_issue185_price_territory.py` |

**Design conclusion: `PROCEED_TO_PREREG`** — conditional on the mandatory
pre-outcome amendments `A1`–`A6` in §7. This is a *design feasibility*
conclusion. It is not a claim of edge, and it is not a statement about any
market.

---

## 1. What was asked, and what this document is not

Issue #185 asked for the *first* step of a two-step programme: an independent
engineering implementation of the v0.2 design, deterministic artificial-market
tests, an adversarial design review, and a prereg-ready specification. It
explicitly forbids running historical outcome research in this round.

This document therefore reports:

* whether v0.2 is implementable, causal, deterministic, symmetric and
  fail-closed;
* whether the published synthetic readouts can be independently re-derived;
* where the design fails on constructed counterexamples;
* whether the observable is a repackaging of an existing coordinate;
* what a preregistration would have to freeze.

It does **not** report win rates, returns, AUC, expectancy, or any economic
quantity. Passing 67 synthetic assertions is not evidence of trading value.

## 2. Implementation contract actually executed

Written from the v0.2 comment text. Where the text was ambiguous, the choice is
recorded here and flagged in §6.B as a design ambiguity rather than silently
decided.

| element | implemented semantics |
|---|---|
| reference | `bars[t0-120 : t0]`, completed pre-probe bars, frozen at the first probe, never slides |
| zone radius | `w = (Q90(close_ref) − Q10(close_ref)) / 20`, quantile **method = linear** (pinned) |
| inner band | `[P − w, P + w]`, P = current **completed close** |
| outer band | `[P − 2w, P + 2w]` |
| inner touch | bar **range** overlaps the inner band: `high_i ≥ P−w and low_i ≤ P+w` |
| re-arm | the **entire** historical bar is outside the outer band: `low_i > P+2w or high_i < P−2w` |
| revisit episodes `R` | armed-gated touch count; a touch while armed counts and disarms |
| occupancy `O` | share of valid reference bars touching the inner band, `0..1` |
| novelty `N` | `1 / (1 + R)` |
| acceptance trace `A` | mean of `N` over at most the last **3** post-anchor closes **including the current one** |
| evidence maturity | `min(3, t − t0 + 1)`, reported on every bar |
| frontier `F` | long `(P − max(high_ref))/w`; short `(min(low_ref) − P)/w`; **context only, never a gate** |
| frontier (close variant) | also emitted using `max/min(close_ref)` for transparency |
| stagnation | `days_since_best_frontier`, `frontier_change_3`, `progress_3_w`, `range_3_w`, `bars_since_significant_progress`, `stall_flag` — descriptive only |
| anchor policy | `first_probe_wins`: overlapping probes attach to the open episode and do **not** reset maturity |
| observability | every value is a completed-close value; `actionable_at_bar = bar_index + 1` |
| fail-closed | `UNKNOWN_*` → all numbers `None`; `DEGRADED_*` → numbers reported but **no new-territory claim** |
| `direction` contract | must be `+1` or `−1`; any other value **raises** `ValueError` rather than being silently coerced to long |
| non-finite reference | any non-finite OHLC in the reference → `UNKNOWN_NONFINITE_REFERENCE` (no numbers, no claim) |
| non-finite query | any non-finite OHLC in the query bar → `UNKNOWN_NONFINITE_QUERY` (no numbers, no claim) |

Causality was verified operationally, not by inspection: for every fixture and
every truncation point, an episode recomputed from the truncated series is
bit-for-bit equal to the corresponding prefix of the full-series episode
(`test_no_observation_reads_a_future_bar`,
`test_future_append_invariance`).

## 3. Independent re-derivation of the published v0.2 readouts

Sophira's original fixture was **not handed over** with the issue. A 6-sweep,
120-bar, 100–120 box with 10-bar legs was constructed independently from the
written definition. It re-derives every published number exactly:

| checkpoint | published R | published N | observed R | observed N | match |
|---|---:|---:|---:|---:|---|
| box rise to 118 | 6 | 0.143 | 6 | 0.142857 | yes |
| box rise to 119 | 6 | 0.143 | 6 | 0.142857 | yes |
| one tick above high, 120.01 | 6 | 0.143 | 6 | 0.142857 | yes |
| initial crossing to 121.60 | 0 | 1.000 | 0 | 1.000 | yes |
| fake breakout back at 116 | 12 | 0.077 | 12 | 0.076923 | yes |
| true breakout 123→126→129 | 0 | 1.000 | 0 | 1.000 | yes |
| healthy retest to 118 | 6 | 0.143 | 6 | 0.142857 | yes |
| new zone 124.6 stalls 18 days | 0 | 1.000 | 0 | 1.000 | yes |

**This is an independent reconstruction, not a reproduction of Sophira's
file.** It shows the v0.2 *text* determines the published pattern; it says
nothing about any instrument. The mechanism is transparent: the reference
high is exactly 120.0, `w = 0.8`, and the arming geometry of the 6-sweep box
yields 1 episode per sweep at 118/119/120.01 and 2 per sweep at 116.

The rejected v0.1 aliasing is independently demonstrated rather than asserted:
in `crossed_but_not_closed` the reference **closes** only ever take the values
100/110/120 while the bar ranges span every leg. v0.1 close-only counting at
118 returns **0 episodes → novelty 1.00**; the implemented OHLC semantics return
**30 episodes → novelty 0.0321**. The bug and the fix are both on the record.

## 4. The ten required synthetic scenarios

All fixtures are deterministic constants. Per-bar trajectories are in
`artifacts/issue185_price_territory/traces/`; latency statistics in
`issue185_ptm_latency.csv`; charts in `.../charts/`.

| # | scenario | fixture | result |
|---|---|---|---|
| 1 | large 100–120 box, repeated traversals reaching 118/119/120.01 | `wide_box_traversal` | **never** claims new territory across 53 post-probe bars; R at 118/119/120.01 = 6, N = 0.143, O = 0.10–0.20 |
| 2 | true trend leaving the historical region | `true_trend` | first claim at the escape close, **latency 0 bars**; R 6→0, N 0.143→1.000 at 121.60 |
| 3 | fake breakout, immediate return to the box | `fake_breakout` | N 1.000 → 0.143 → 0.077 within three closes; deterioration visible immediately |
| 4 | healthy retest into the old zone then continuation | `healthy_retest` | at the retest R = 6, N = 0.143, A = 0.429; A recovers 0.429→1.000 over the next three closes, no hard reset |
| 5 | one minimum-tick breakout (120.01) | `one_tick_breakout` | R constant at 6 across 119.99/120.00/120.01/120.02; F crosses zero smoothly (−0.0125→+0.0250); **no claim** |
| 6 | post-breakout long stagnation | `post_breakout_stall` | N pinned at 1.000 for 18 flat bars (known defect); `stall_flag` true, `bars_since_significant_progress` = 18 |
| 6b | creeping stagnation (+0.01/bar) | `creeping_stall` | `days_since_best_frontier` resets to **0** every bar while `range_3_w` = 0.0375; the amplitude gauge still exposes it |
| 7 | slow trend (+0.5/bar) | `slow_trend` | recognised at 121.0 with R = 0, N = 1.000 despite a 0.5 daily step (0.625·w); no speed preference |
| 8 | short mirror | `*__short_mirror` | exact reflection invariance on R, O, longest inner run, N, class, F and claim flags for both the box and the trend fixtures |
| 9 | missing bars / splits / rolls / gaps | `missing_reference_bars`, `adjusted_split`, `unadjusted_split`, `futures_roll`, `gappy_reference` | consistent 2:1 adjustment is affine-invariant; 8 missing reference bars → `DEGRADED_REFERENCE_COVERAGE` (112/120) and **zero claims**; unadjusted 2:1 split and a 4× roll are screened and latched; no cross-bar path is ever inferred |
| 10 | future-append invariance | all of the above | appending future bars changes no earlier observation, at every truncation point |

### First-recognition statistics (bars)

| fixture | structural escape | first claim | latency | claims | validity |
|---|---:|---:|---:|---:|---|
| `wide_box_traversal` | 168 | — | — | 0 | OK |
| `true_trend` | 127 | 127 | **0** | 4 | OK |
| `fake_breakout` | 127 | 127 | **0** | 1 | OK |
| `healthy_retest` | 126 | 126 | **0** | 7 | OK |
| `one_tick_breakout` | 129 | — | — | 0 | OK |
| `slow_trend` | 160 | 161 | **1** | 19 | OK |
| `long_trend_unbounded_novelty` | 200 | 203 | **3** | 167 | OK |
| `missing_reference_bars` | 127 | — | — | 0 | DEGRADED |

The structural escape is the first post-probe bar whose **range** traded beyond
the frozen envelope. Latency is `first_claim − structural_escape`. A negative
latency is possible and intentional: the frontier is not a gate, so a region
inside the 120-day envelope can still be genuinely unvisited
(`long_period_box`, `gappy_reference`).

## 5. Adversarial review of the specific questions in the task

**a. Are 120 reference bars enough to record a large box?**
For a 20-bar sweep, yes: 6 sweeps, R = 6. For a 40-bar sweep, 120 bars holds
only 3 sweeps and the identical box yields R = 3, N = 0.250
(`sparse_slow_box`). For a box whose sweep is longer than 120 bars the window
contains at most one crossing: `long_period_box` reports **R = 1, N = 0.500,
O = 0.092, `is_new_territory_claim = True`** at 112 — i.e. *inside* a
long-established box. **Verdict: not sufficient in general; the reference
length is a real identifiability limit, not a tuning knob (defect D1).**

**b. Is the zone width sensitive to extreme prices?**
Yes. `volatility_regime_shift` replaces the last 15 of 120 reference closes
with 400. `Q90` moves 118 → 400, so `w` moves 0.8 → **14.9**, the inner band
swallows the whole box, R collapses 6 → 1 and O inflates to 0.783. The
instrument does not fail loudly, it becomes inert and drifts toward N = 0.5
everywhere. **Verdict: sensitive; needs a scale-stability guard (defect D3).**

**c. Can one long wick cause excessive historical visitation?**
Yes, in the direction that costs real trends. `long_wick` adds a single bar to
the box reference with `high = 150`. At 135 — genuinely beyond all observed
price — the wick bar touches, so R = 1 and N = **0.500 instead of 1.000**.
**Verdict: confirmed; the defect is conservative (under-claims) but it directly
taxes large-trend harvest (defect D4).** A `min_overlap_fraction` and a
`body_overlap` touch mode are implemented as challengers and are *not* the
default.

**d. Can dwelling and repeated return be reliably distinguished?**
The two primitives are genuinely separable, which is why they are reported
separately: `long_period_box` gives low R with non-zero O (0.092), while
`wide_box_traversal` gives high R with O = 0.20 at 118 and 0.077 N. However
`R` is *not* a pure function of the territory: it is a function of how many
legs fit into 120 bars (see (a)). **Verdict: distinguishable as signatures,
not yet comparable as a scale across instruments (defect D2).**

**e. What does daily OHLC leave unidentifiable?**
The intraday path order. One bar can cross the inner band many times and is
counted at most once; whether a bar traded low→high or high→low is unknown;
a bar's touch cannot be attributed to the beginning or end of the session. The
outer re-arm rule is therefore evaluated on the whole bar, which is the only
causal choice available. **Verdict: irreducible with daily OHLC; must be
declared, not papered over (limitation L1).**

**f. Can a long trend stay "new territory" forever?**
Yes. `long_trend_unbounded_novelty` advances 250 bars one-way with a frozen
reference: at bar 369 R = 0 and N = **1.000**, and `days_since_best_frontier`
= 0 every single bar. **Verdict: confirmed (defect D5).** This is the intended
tension with "the reference must not slide", and it is not resolved here.

**g. How should overlapping probes be anchored?**
v0.2 does not say. It matters a great deal: under `reanchor_each_probe` the
reference re-freezes and `evidence_bars` restarts at 1 at each probe, so a
single opportunity is repeatedly reset to "nascent"; under the implemented
`first_probe_wins` the anchor and maturity persist. **Verdict: must be frozen
in the prereg; implemented default is `first_probe_wins` with a
120-bar staleness cap (defect D9 / amendment A5).**

**h. Is the first-day true/fake ambiguity honestly represented?**
Yes, and it is the sharpest result in this review. `true_trend` and
`fake_breakout` share the same post-anchor path through the first close beyond
the envelope (121.60). The test asserts every observation up to and including
that bar is **identical**, and that they diverge only afterwards. **Verdict:
the ambiguity is irreducible… and it is fatal to "Fast-Evidence" as an idea.**
At the earliest bar where novelty can fire, novelty carries *no* information
about continuation. Any earlier add must be justified by something else.

**i. Is this a repackaged channel breakout, moving average or efficiency
ratio?** See §8. On controlled synthetic paths the observable is provably not
a function of `ER20`, nor of the rolling range, and it is explicitly *not* a
Donchian gate (one tick above the 120-day high gives the same N = 0.143 as
118.00). Incremental *empirical* information against Core-2/A9 remains
unproven and is a preregistration question, not a design claim.

## 6. Findings register

Severity: **S1** blocks a prereg as-is · **S2** must be handled before
preregistration, fix is bounded · **S3** documented limitation, acceptable.

### A. Confirmed defects (with counterexample)

| id | sev | defect | counterexample (exact) | proposed fix |
|---|---|---|---|---|
| **D1** | **S1** | 120-bar window cannot see a box whose period exceeds the window; a long-established box is reported as sparse/unvisited and **claims** new territory | `long_period_box` @112 → R=1, N=0.500, O=0.092, claim=True | amendment **A1**: reference-adequacy gate — count complete traversals of the frozen envelope (`reference_cycle_count`); if < 1, mark `DEGRADED_REFERENCE_ADEQUACY` and block claims instead of falsely releasing |
| **D2** | **S1** | `R` is observation-density dependent, so `N` is not comparable across instruments, timeframes or volatility regimes | identical box: 20-bar sweeps → R=6, N=0.143; 40-bar sweeps → R=3, N=0.250 | amendment **A2**: keep raw `R`, additionally emit `episodes_per_cycle` and `revisit_density`; the prereg must declare which is primary and evaluate within-instrument |
| **D3** | S2 | `w` is fragile to ≥11% extreme closes in the window; the instrument silently becomes inert | `volatility_regime_shift` → w 0.8→14.9, O→0.783, N→0.5 everywhere | amendment **A3**: emit `w/median_ref`, add `SCALE_UNSTABLE` degraded state that blocks claims above a pre-declared ratio; do not silently replace the quantile formula |
| **D4** | S2 | a single bar's wick is treated as full occupancy of everything it spans | `long_wick` @135 → R=1, N=0.500 instead of 1.000 | amendment **A4**: keep range-overlap primary, but emit the `min_overlap_fraction` variant as a mandatory secondary so wick sensitivity is measured, not assumed |
| **D5** | S2 | with a frozen reference, novelty never decays; a dead stall is indistinguishable from a live trend | 250-bar trend → N=1.000 at bar 369, `days_since_best_frontier`=0 every bar; 18 flat bars → N=1.000, `stall_flag`=True | amendment **A6**: progress/stagnation stays a **separate** reporting channel and a separate preregistered challenger; explicitly **not** folded into novelty. **Not solved by this review.** |
| **D6** | S3 | at the first close beyond the envelope, true and fake breakouts are identical | `true_trend` vs `fake_breakout` identical through 121.60 | irreducible. The prereg must not test any policy that acts on the first claim alone |
| **D7** | S2 | a gappy or sparse reference overstates novelty and v0.2 math cannot detect it | `gappy_reference` → `max_close_gap_w` = 20.0, `envelope_covered_fraction` = 0.002, R=0 at the un-observed middle | amendment **A1** extended: `max_close_gap_w` and `envelope_covered_fraction` are mandatory reported diagnostics with pre-declared thresholds blocking claims |
| **D8** | S3 | the scale-break screen is a weak heuristic | a genuine −55% move is flagged (false positive); any split milder than the factor is missed (false negative) | data-quality prompt only, never a gate; prefer an explicit adjustment/roll field from the data layer |
| **D9** | S2 | v0.2 does not specify anchor management for overlapping probes, and the choice materially changes the output | `first_probe_wins` keeps `evidence_bars`=3 at bar 135; `reanchor_each_probe` resets it to 1 at the same bar | amendment **A5**: freeze `first_probe_wins` + 120-bar staleness cap, or state the alternative explicitly, before outcomes |

### B. Design ambiguities resolved by this implementation

| id | ambiguity in the v0.2 text | choice made | why it matters |
|---|---|---|---|
| AM1 | "distance from frozen historical **high**" — bar high or max close? | **bar high** (`max(high_ref)`) as primary, max close emitted alongside | changes `F` by the wick allowance; both are reported so neither is hidden |
| AM2 | quantile definition unspecified | `numpy` linear interpolation, pinned | a different quantile convention changes `w` and therefore `R` |
| AM3 | acceptance trace "at most the most recent three closes" — is the current close included? | **yes, included** | this is what makes the first close actionable; excluding it delays the trace by one bar |
| AM4 | does the outer re-arm test use the bar range or the close? | **bar range** ("the entire reference bar is outside") | using closes would re-arm far more often and inflate `R` |
| AM5 | `P` = current price: close, or high/low? | **completed close** | the design is defined "at today's completed close"; using the high would leak the day's extreme into a close-time decision |

### C. Hardening applied during this review (robustness, not design defects)

Found by independently probing the prototype with malformed input, and fixed
with regression tests.

| id | issue found | behaviour before | behaviour now |
|---|---|---|---|
| **H1** | a **NaN query close** made every band comparison compare against NaN and silently registered spurious touches | reference bars "touched" → published `novelty = 0.5` for an unusable price | `UNKNOWN_NONFINITE_QUERY`, all numbers `None`, no claim |
| **H2** | a reference bar with a **non-finite high/low** did not invalidate the reference (the radius is computed from closes and stays finite) | reference `OK`, `max_high`/`min_low` unusable | `UNKNOWN_NONFINITE_REFERENCE`, `is_usable False`, no numbers, no claim |
| **H3** | an invalid `direction` (`0`, `2`, `-2`) was silently coerced to `+1` by `int(np.sign(d)) or 1` | a caller bug returned a plausible **long-side** answer | `ValueError` — the side is a caller contract, not market data |
| **H4** | an all-invalid reference window | already failed closed (`UNKNOWN_INSUFFICIENT_HISTORY`) — confirmed, not changed | unchanged |

`H1` and `H2` are exactly the failure mode the fail-closed rule is supposed to
prevent, which is why they are called out rather than buried. They do not
change any fixture result: all 42 artifacts still reproduce byte-for-byte.

### D. Standing limitations (not defects — declared)

* **L1** intraday path order is unidentifiable from daily OHLC; multiple
  intraday crossings count once.
* **L2** no volume-at-price is claimed; the method never fabricates
  transacted-volume evidence.
* **L3** the indicator has **no** opinion about the benchmark's probe. It never
  creates, removes or resizes an opportunity.
* **L4** all values are completed-close values; earliest action is `t+1`.
* **L5** the stagnation problem is **not solved** by this work. The prototype
  exposes it; it does not fix it.

## 7. Mandatory pre-outcome amendments for the preregistration

If any of `A1`–`A6` is rejected, the correct verdict becomes `REDESIGN`, not
`PROCEED_TO_PREREG`. None of them is a tuned parameter; all are
instrument-validity guards decided **before** any forward outcome exists.

* **A1 — reference adequacy.** Require at least one complete traversal of the
  frozen envelope before any claim; require `envelope_covered_fraction` and
  `max_close_gap_w` inside pre-declared bounds. Otherwise report a degraded
  state and block the claim. Rationale: D1, D7.
* **A2 — scale comparability.** Keep `R` and `N` as specified, and emit
  `episodes_per_cycle` and `revisit_density`. Declare in the prereg which
  quantity the challenger policy keys on, and evaluate within-instrument
  rather than against one cross-sectional threshold. Rationale: D2.
* **A3 — scale stability.** Emit `w / median_ref` and a `SCALE_UNSTABLE`
  state with a pre-declared bound. Do not silently replace `(Q90−Q10)/20`.
  Rationale: D3.
* **A4 — touch sensitivity.** Keep range-overlap as primary; report the
  minimum-overlap-fraction variant as a mandatory secondary statistic.
  Rationale: D4.
* **A5 — anchor policy.** Freeze `first_probe_wins` and the staleness cap, or
  justify the alternative in writing. Rationale: D9.
* **A6 — stagnation is separate.** Progress/stagnation diagnostics must not be
  combined with novelty into one score and must not be used as a filter in the
  primary challenger. Rationale: D5.

## 8. Is PTM a repackaging of an existing coordinate?

Construct-level evidence only; no historical data was used.

| coordinate | relation to PTM novelty | evidence |
|---|---|---|
| **Donchian / 120-day breakout** | **not** equivalent. `F` is context and never gates `N`. One tick above the frozen high (120.01) gives the same R=6, N=0.143 as 118.00, and `one_tick_breakout` never claims. Conversely a region *inside* the envelope can be genuinely unvisited and claim (`long_period_box`). | `test_published_wide_box_readout`, `test_one_tick_breakout_has_no_signal_discontinuity` |
| **ER20 / path efficiency** | **not** a function of it. Identical 20-bar path, different frozen reference → identical ER20 = 1.000 but N = 0.143 vs 1.000. Identical reference and identical final close, different path → identical N = 0.143 but ER20 = 1.000 vs < 0.5. | `test_same_recent_path_different_reference_gives_different_novelty`, `test_same_reference_different_path_gives_same_novelty_different_er` |
| **ATR / Bollinger width (A9 D3)** | **not** a width proxy. `w` is a *frozen* reference scale; it does not respond to current volatility. That is precisely why D3 (a regime shift inside the frozen window) is a defect rather than a feature. | §5b |
| **Core-2 `Structure × Extension`** | different input class: Core-2 is a state map over current structure/extension; PTM counts *historical bar-range overlap* against a frozen envelope. No shared denominator. Whether it is *incrementally* informative beyond Core-2 is **untested** and is exactly what the prereg must falsify. | §9 |

Construct distinctness on synthetic paths is established. **Incremental
empirical information is not established and is not claimed.**

## 9. Verdict

### `PROCEED_TO_PREREG`

Justification, restricted to design feasibility and non-duplication:

1. v0.2 is implementable as a deterministic, causal, non-repainting,
   long/short-symmetric, fail-closed information layer, and 67 synthetic
   assertions pass — including future-append invariance at every truncation.
2. The published v0.2 readouts are independently re-derived exactly, and the
   rejected v0.1 close-only aliasing is independently demonstrated
   (0 vs 30 episodes on the same reference).
3. The primary use case is served: across 53 post-probe bars of large-box
   traversal reaching 118, 119 and one tick above 120, PTM **never** claims new
   territory, while a genuine escape is recognised on the same completed close
   as the escape (latency 0).
4. The observable is not a strict function of ER20, rolling range/ATR width or
   a Donchian gate on controlled paths.
5. Every failure found is bounded, reproduced by a named fixture, and has a
   pre-outcome instrument-validity guard.

Conditions (mandatory): amendments `A1`–`A6`, the falsification criteria in the
prereg draft, and an explicit statement that PTM is a **challenger evidence
layer** only.

### What `PROCEED_TO_PREREG` does not mean

* It does not mean PTM improves anything. No return, win rate or risk metric
  was computed.
* It does not mean the challenges in §5 are solved. `D1`, `D2` and `D5` are
  live and are handed to the prereg as falsification targets.
* It does not authorise any change to the frozen `25% probe → t+3 100% full`
  benchmark, Warning-First, or any stop/risk rule.
* It does not authorise a PTM "Fast-Evidence" earlier add. §5h shows the first
  claim carries no continuation information.
* It does not contact OOS5, merge anything, or touch Pine/production.

### Falsification criteria the prereg must carry

Reject PTM at outcome stage if any holds:

* no separation from Core-2 `Structure × Extension`, A9 D3 volatility
  percentile, or a plain 120-day Donchian gate on the frozen cohort;
* any improvement in false-trend damage is bought by systematic lateness
  (measured as first-claim lag distribution, not a mean);
* the long-period-box false release (D1) is not eliminated by A1;
* the wide-box benefit appears only in one era, one sleeve or one asset class;
* the stall failure (D5) produces materially worse large-trend harvest
  (MFE ≥ 8 ATR) than the frozen R0 benchmark.

## 10. Artifacts

```
indicators/wyckoff-regime-radar/research/
  ptm_territory.py                              frozen v0.2 prototype
  ptm_territory_fixtures.py                     27 deterministic fixtures
  ptm_territory_charts.py                       Pillow audit charts
  analyze_issue185_price_territory.py           runner
  test_issue185_price_territory.py              67 tests
  decisions/issue-185-price-territory-engineering-review-finding.md   (this file)
  decisions/issue-185-price-territory-integration-interface.md
  decisions/issue-185-price-territory-prereg-draft.md
  artifacts/issue185_price_territory/
    issue185_ptm_report.md                      run report
    issue185_ptm_summary.json                   machine-readable summary
    issue185_ptm_latency.csv                    first-recognition statistics
    issue185_ptm_reproduction.csv               published-readout comparison
    issue185_ptm_traces_all.csv                 all per-bar trajectories
    traces/<fixture>.csv                        one trajectory per fixture
    charts/*.png                                audit and comparison charts
```

The whole artifact tree (42 files) is byte-for-byte reproducible: re-running
`analyze_issue185_price_territory.py --outdir <tmp>` and hashing every file
against the committed tree yields zero differences, and CI enforces this with
`diff -r artifacts/issue185_price_territory <tmp>`.

## 11. Boundary statement

No market data was downloaded or used. No historical return, trade, position,
exposure, P&L or risk statistic was computed. No parameter was tuned; the only
constants are the design candidates from the v0.2 note plus the explicitly
labelled descriptive diagnostics in §2. OOS5 was not contacted. No Pine,
production, strategy or sizing rule was modified. Nothing was merged; no pull
request was opened. `#78` remains open.

**This is a design-feasibility conclusion, not a trading-performance
conclusion.**
