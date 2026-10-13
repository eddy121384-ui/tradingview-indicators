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
| Artifacts | `indicators/wyckoff-regime-radar/research/artifacts/issue185_price_territory/` (50 files) |
| Tests | `python -m pytest -q test_issue185_price_territory.py` → **190 passed** |
| Runner | `python analyze_issue185_price_territory.py` |
| Independent audit | separate adversarial verification passes by a second agent (different context, own from-scratch reimplementation); the phase-1 pass drove §6.C and §9, the phase-2 pass is reported in §12.1 |

**Design conclusion (phase 1): `PROCEED_TO_PREREG`** — conditional on the
mandatory pre-outcome amendments `A1`–`A6` in §7.

**Phase-2 conclusion: `READY_FOR_PREREG_REVIEW`** — A1, A2 and A3 are
implemented with frozen pre-outcome thresholds, the promotion clock is
corrected, and the accepted false-suppression cost is declared. This is a
*readiness* conclusion: the patch is safe and reviewable. It is not a claim of
edge, and it is not a statement about any market. See §6.E and §12.

This is a *design feasibility* conclusion. It is not a claim of edge, and it is
not a statement about any market.

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
| occupancy `O` | share of **valid** reference bars touching the inner band, `0..1` (denominator is `n_valid`, not 120 — see AM6) |
| novel territory claim | `is_new_territory_claim` is true iff validity is `OK`, the reference is complete (coverage 1.0), `R ≤ 1` (class `UNVISITED` or `SPARSE`), and no scale break is latched |
| novelty `N` | `1 / (1 + R)` |
| acceptance trace `A` | mean of `N` over at most the last **3** post-anchor closes **including the current one** |
| evidence maturity | `min(3, t − t0 + 1)`, reported on every bar |
| frontier `F` | long `(P − max(high_ref))/w`; short `(min(low_ref) − P)/w`; **context only, never a gate** |
| frontier (close variant) | also emitted using `max/min(close_ref)` for transparency |
| stagnation | `days_since_best_frontier`, `frontier_change_3`, `progress_3_w`, `range_3_w`, `bars_since_significant_progress`, `stall_flag` — descriptive only |
| anchor policy | `first_probe_wins`: overlapping probes attach to the open episode and do **not** reset maturity |
| observability | every value is a completed-close value; `actionable_at_bar = bar_index + 1` |
| fail-closed | `UNKNOWN_*` → all territory numbers `None` (only the positional `evidence_bars` counter remains); `DEGRADED_*` → numbers reported but **no new-territory claim** |
| scale break | a latched one-bar price-unit break (`suspect_scale_break`) suppresses the claim while leaving the numbers published for diagnosis; the level-vs-median drift ratio is reported separately as `drift_scale_warning` and never gates |
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
`wide_box_traversal` gives high R with O = 0.20 at 118 and N = 0.1429. At 116
the same fixture reads N = 0.0769, the readout the design published for the
fake-breakout case. However `R` is *not* a pure function of the territory: it
is a function of how many legs fit into 120 bars (see (a)). **Verdict:
distinguishable as signatures, not yet comparable as a scale across
instruments (defect D2).**

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
Yes. `true_trend` and `fake_breakout` share the same post-anchor path through the
first close beyond the envelope (121.60). The test asserts every observation up
to and including that bar is **identical**, and that they diverge only
afterwards.

**What that identity does establish:** for **those two specific paths, at that
specific timestamp**, no causal rule can separate them — the distinguishing
information is simply not in the data at that bar. It follows that a policy
acting on the first claim alone has no mechanism *derivable from that evidence*,
and it is reasonable **not** to authorise a fast-evidence earlier add on this
basis.

**What it does not establish (corrected in phase 2):** an earlier draft of this
section claimed the ambiguity was "fatal to Fast-Evidence as an idea" and that
"novelty carries *no* information about continuation". **Those are population
claims and they are not supported.** Two hand-built synthetic paths agreeing at
one timestamp is a statement about those paths, not a measurement that first-day
novelty has zero conditional probability information across a market population.
The strong claim has been withdrawn; establishing or refuting it would require a
forward study, which this phase is explicitly not authorised to run. The
verdict is therefore narrower: *this pair of paths is inseparable at that bar,
and no fast-add policy may be justified by this indicator's first-claim
evidence alone.*

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
| **D8** | S3 | the scale-break screen is a weak heuristic: it detects a **multiplicative** re-basing, which is the real phenomenon, so it is invariant under price inversion but **not** under arithmetic reflection | a genuine overnight −48.5% move is flagged (false positive) while the reflected +48.5% jump (ratio 1.485, just inside the 1.5 band) is not; any split milder than the factor is missed (false negative) | screen stays a data-quality prompt that suppresses claims (C2); `drift_scale_warning` surfaces the level-vs-median ratio without gating (AM8). Prefer an explicit adjustment/roll field from the data layer. **Residual asymmetry is pinned by a test, not hidden** |
| **D9** | S2 | v0.2 does not specify anchor management for overlapping probes, and the choice materially changes the output | `first_probe_wins` keeps `evidence_bars`=3 at bar 135; `reanchor_each_probe` resets it to 1 at the same bar | amendment **A5**: freeze `first_probe_wins` + 120-bar staleness cap, or state the alternative explicitly, before outcomes |
| **D10** | S2 | **found in phase 2.** The frozen one-bar scale-break screen is **level-dependent**: a fixed absolute move is a large *relative* move at a low price level, so it latches and suppresses claims that the identical higher-level path is allowed to make | `true_trend` shifted by −130: R/O/N identical to the unshifted path, but `suspect_scale_break` latches at bar 129; v0.2 keeps claims at 129, 130, the shifted path loses them | **not fixed** — fixing it changes a frozen v0.2 screen. Declared as a limitation (§6.F L8) and covered by prereg rejection rule 6 plus a mandatory level-stratified rate |

Status after phase 2: **D1 closed** (A1, `long_period_box`: 12 claim bars → 0);
**D3 mitigated, not a claim change** (A3 now names the condition:
`volatility_regime_shift` reports `SCALE_UNSTABLE` instead of leaving the
instrument silently inert — but it did not claim under v0.2 either, so A3 did not
remove a false release there, and saying so would overstate it);
**D7 closed by the envelope-based half of A1** (`gappy_reference`
`envelope_covered_fraction = 0.002` → blocked: 3 claim bars → 0); **D2 mitigated
descriptively** (A2 emits `episodes_per_cycle`, which is speed-comparable: fast
and slow boxes both give 1.0 against raw R of 6 vs 3 — but A2 is descriptive and
does not enter the claim predicate); **D4 open** (the overlap-fraction variant
cannot exclude an enclosing wick — pinned by a test); **D5 open**; **D6 narrowed
and corrected** (see §5.h); **D8 open**; **D9 closed** (A5 frozen, and the anchor
policy is now in the config fingerprint); **D10 new and open**.

### B. Design ambiguities resolved by this implementation

| id | ambiguity in the v0.2 text | choice made | why it matters |
|---|---|---|---|
| AM1 | "distance from frozen historical **high**" — bar high or max close? | **bar high** (`max(high_ref)`) as primary, max close emitted alongside | changes `F` by the wick allowance; both are reported so neither is hidden |
| AM2 | quantile definition unspecified | `numpy` linear interpolation, pinned | a different quantile convention changes `w` and therefore `R` |
| AM3 | acceptance trace "at most the most recent three closes" — is the current close included? | **yes, included** | this is what makes the first close actionable; excluding it delays the trace by one bar |
| AM4 | does the outer re-arm test use the bar range or the close? | **bar range** ("the entire reference bar is outside") | using closes would re-arm far more often and inflate `R` |
| AM5 | `P` = current price: close, or high/low? | **completed close** | the design is defined "at today's completed close"; using the high would leak the day's extreme into a close-time decision |
| AM6 | occupancy denominator: 120, or the number of valid reference bars? | **`n_valid`**, matching the §2 wording "share of valid reference bars" | with 8 missing bars `missing_reference_bars` reports O 7.1% higher than a `/120` reading; it also means O is not comparable across different coverage |
| AM7 | inner touch boundary: inclusive (`≥`/`≤`) or strict overlap? | **inclusive**, exactly as written in the spec (`high_i ≥ P−w and low_i ≤ P+w`) | at tick-aligned prices `w` is often an exact multiple of the price quantum, so the choice is not measure-zero in practice — see §6.C `C1` |
| AM8 | what may latch the scale-break screen? | only a **one-bar** price-unit break; the level-vs-median ratio is reported as `drift_scale_warning` but never latches | the drift version flagged any sustained large move and, because a ratio is not invariant under arithmetic reflection, silently suppressed claims on long downtrends but not equally sized uptrends — see §6.C `C5` |

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

### D. Conformance defects found by the independent audit and fixed

These were found by a second, adversarial verification pass that wrote its own
reimplementation of `R/O/N` straight from the spec text and diffed the whole
fixture family against it. Each fix carries a regression test.

| id | conformance issue | wrong behaviour before | behaviour now |
|---|---|---|---|
| **C1** | inner touch used a **strict** overlap (`> 0`) while the v0.2 spec is **inclusive** (`high ≥ P−w`, `low ≤ P+w`) | at close 115.20 with `w = 0.8` the inner high is exactly 116.00 and 12 reference bars have `low == 116.00`; they were dropped, so O read 0.10 instead of 0.20. Worst case: 120 reference bars all exactly at 100.0 and a query at 100.0 were reported `UNVISITED` with N = 1.0 (a price equal to every bar called "never visited"), and a constructed band-edge case emitted a **false new-territory claim** | inclusive predicate; O = 0.20, the equal-price case reads R = 1, N = 0.5, and the band-edge case reads R = 2, N = 0.333, claim = False. The published v0.2 readouts are unchanged and still reproduce exactly |
| **C2** | a **latched scale break did not block** `is_new_territory_claim`, contradicting the spec's requirement to return UNKNOWN when the price quantum is unavailable and the fixture's own note that an unadjusted split "must be screened, **not** reported as a brand-new territory" | `unadjusted_split` and `futures_roll` each emitted 11 new-territory claims with N = 1.0 after the price unit broke | claims are suppressed while the numbers stay published for diagnosis: both fixtures now report 0 claims with 11 latched suspect bars |
| **C3** | an anchor **past the end of the data** silently froze a truncated window and reported `DEGRADED_REFERENCE_COVERAGE` | `build_reference(bars, 123)` on 120 bars returned a 117-bar reference with `w` and a misleading "mostly complete" state | `UNKNOWN_INSUFFICIENT_HISTORY` with no numbers, whenever the frozen window cannot hold exactly 120 bars |
| **C4** | lowering `min_reference_coverage` could reopen claims on a **partial** reference | with `min_reference_coverage = 0.0`, `missing_reference_bars` (coverage 0.933) reported validity `OK` and emitted 4 claims | the claim gate independently requires coverage 1.0, so the knob can no longer reopen a claim; validity and numbers are unchanged |
| **C5** | the scale-break latch keyed partly on the **level vs the reference median**, so any sustained large move latched it | a 250-bar one-way advance kept its claims (its ratio stayed under 1.5) while the *arithmetically reflected* downtrend latched and lost all of them — a long/short asymmetry created by a data-quality heuristic | only a one-bar jump latches, which is what a split or roll actually is; the drift ratio is still reported (`drift_scale_warning`), and the asymmetry disappeared from the reflected-path test |
| **C6** | the chart renderer looked up `DejaVuSans.ttf` **by bare name** | resolves on Linux, raises on Windows, so chart bytes would differ by platform and could fail the CI reproducibility gate for a reason unrelated to the indicator | the renderer always uses Pillow's bundled default font; CI pins `pillow==12.3.0` |

`C1` and `C2` changed behaviour, not just robustness, and the published readouts
were re-derived after them: all eight still match exactly, and the artifact tree
still reproduces byte-for-byte.

### E. Phase-2 remediation — A1/A2/A3 implemented (old signal vs fixed signal)

Committed as `v0.2.2`. All thresholds are module-level constants, appear in
`PTMConfig.fingerprint()`, and are pinned by tests. They were fixed from
synthetic geometry **before** the patch was written, with no outcome inspected.

| guard | frozen threshold | constant |
|---|---|---|
| A1 cycles | `reference_cycle_count ≥ 1.0` | `MIN_REFERENCE_CYCLES` |
| A1 coverage | `envelope_covered_fraction ≥ 0.5` | `MIN_ENVELOPE_COVERED_FRACTION` |
| A1 gap | `max_unobserved_gap_fraction ≤ 0.25` | `MAX_UNOBSERVED_GAP_FRACTION` |
| swing leg | `0.5 × w` reversal of the running extreme | `CYCLE_SWING_FRACTION` |
| A3 | `w / abs(median close_ref) ≤ 0.05` | `MAX_W_OVER_SCALE` |

**Correction to §7's A1 wording:** the gap guard keys on the largest unobserved
hole **between merged reference bar ranges**, not on close-to-close jumps. A
close-gap gate was explicitly rejected: `crossed_but_not_closed` has
`max_close_gap_w = 10.0` while its bar ranges cover **100%** of the envelope, so
a close-gap gate would have falsely rejected a fully observed reference. The
close-gap statistic is still emitted as a diagnostic.

#### Per-scenario result (33 fixtures; `issue185_ptm_phase2_comparison.csv`)

Two of the 33 are guard-INSTRUMENTATION constructs, not scenarios: they
exist so each A1 envelope sub-guard is individually pinned. They are
deliberately blocked and are excluded from every suppression headline
(`instrumentation_fixtures_excluded_from_headline`). The 3 suppressed
scenarios below are the scenario population.

| scenario | v0.2 claim bars | fixed claim bars | first recognition | added delay | model promotion (constructed) | falsely blocked |
|---|---:|---:|---|---:|---|---|
| large box `wide_box_traversal` | 0 | 0 | — | 0 | `B3_break + 3` | no |
| large box `long_period_box` (D1) | **12** | **0** | — | — | `B3_break + 3` | correct block |
| sparse box `sparse_slow_box` | 0 | 0 | — | 0 | `B3_break + 3` | no |
| genuine trend `true_trend` | 4 @127 | 4 @127 | 127 | 0 | 123 (coincident) / 133 (B3+10) | no |
| genuine trend `slow_trend` | 19 @161 | 19 @161 | 161 | 0 | `B3_break + 3` | no |
| long trend `long_trend_unbounded_novelty` | 167 @203 | 167 @203 | 203 | 0 | `B3_break + 3` | no |
| healthy retest | 7 @126 | 7 @126 | 126 | 0 | `B3_break + 3` | no |
| fake breakout | 1 @127 | 1 @127 | 127 | 0 | `B3_break + 3` | no |
| volatility regime shift (D3) | 0 | 0 | — | 0 | `B3_break + 3` | no claim either way; now **flagged `SCALE_UNSTABLE`** instead of silently inert |
| gappy reference (D7) | 3 @120 | **0** | — | — | `B3_break + 3` | correct block |
| one-way reference | 8 @120 | **0** | — | — | `B3_break + 3` | **COST — real trend** |
| unadjusted split / futures roll | 0 | 0 | — | 0 | `B3_break + 3` | no |
| zero-level series | 0 | 0 | — | 0 | `B3_break + 3` | fail closed: `SCALE_UNKNOWN` |
| negative-level series | 4 @127 | 4 @127 | 127 | 0 | `B3_break + 3` | no |
| low-level false alarm (D10) | 2 @127 | 2 @127 | 127 | 0 | `B3_break + 3` | no phase-2 change; pre-existing screen |
| long wick (D4) | 5 @120 | 5 @120 | 120 | 0 | `B3_break + 3` | no |
| crossed-but-not-closed | 1 @120 | 1 @120 | 120 | 0 | `B3_break + 3` | no — close gaps are not gated |

Note on D3: `volatility_regime_shift` did **not** claim under v0.2 either — its
`w` inflated so far that novelty was never fresh. A3's contribution is therefore
not "it removed a claim" but "it names the condition instead of leaving the
instrument silently inert". That is a weaker but honest claim.

Aggregate: **3 fixtures suppressed** (2 correct, 1 declared cost),
**`max_added_delay_vs_v02_bars = 0`**, **`max_ptm_extra_delay_vs_corrected_model_baseline_bars = 0`**,
and all 8 published v0.2 reconstruction readouts still match exactly.

#### Corrected promotion clock

`eligible_promotion_t = B3_break_t + 3`, **not** `probe_t0 + 3`. Modelled in the
new `ptm_promotion_clock.py`, which tracks six independent timestamps
(`probe_t0`, `B3_break_t`, `B3_confirmation_t`, `eligible_promotion_t`,
`PTM_observation_t`, `next_executable_t`) and never implements breakout
detection. Measured error of the old probe-based baseline:
**10 bars** for a breakout 10 bars after the probe, up to **80 bars** on the
long-trend fixture. Measuring PTM's delay against the naive baseline would have
manufactured a latency cost that does not exist.

#### New defect found by this phase (D10) — not fixed

`| **D10** | S2 | the frozen one-bar scale-break screen is **level-dependent**: a fixed absolute move is a large relative move at a low price level | `true_trend` shifted by −130: identical R/O/N to the unshifted path, but `suspect_scale_break` latches at bar 129 and suppresses the claims v0.2 keeps | declared limitation; fixing it would change a frozen v0.2 screen. Prereg rejection rule 6 + a mandatory level-stratified rate. |`

A3 itself is fine in that fixture (`SCALE_STABLE`); the suppression comes from
the pre-existing screen. A3's own known asymmetry stands: the ratio is
**multiplicatively invariant** (an adjusted 2:1 split halves every value and
leaves the ratio unchanged) but **not translation invariant**, and it becomes
`SCALE_UNKNOWN` at a zero price level. Both are documented and pinned by tests.

#### Overclaim withdrawn

§5.h's population-level claim is withdrawn (see the correction there). The
phase-2 guard set is not justified by it.

### F. Standing limitations (not defects — declared)

* **L1** intraday path order is unidentifiable from daily OHLC; multiple
  intraday crossings count once.
* **L2** no volume-at-price is claimed; the method never fabricates
  transacted-volume evidence.
* **L3** the indicator has **no** opinion about the benchmark's probe. It never
  creates, removes or resizes an opportunity.
* **L4** all values are completed-close values; earliest action is `t+1`.
* **L5** the stagnation problem is **not solved** by this work. The prototype
  exposes it; it does not fix it.
* **L6** the A1 adequacy guard refuses certification when a 120-bar window
  contains no complete round trip. A genuine emerging trend behind a one-way
  reference is therefore suppressed. Declared, measured, and accepted in
  `prereg-draft` §2.2 — not an oversight.
* **L7** the A3 ratio is level-relative: multiplicatively invariant but not
  translation invariant, and `SCALE_UNKNOWN` at a zero price level.
* **L8** the frozen one-bar scale-break screen is level-dependent (D10) and is
  **not** fixed by this phase.

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
   long/short-symmetric, fail-closed information layer, and 76 synthetic
   assertions pass — including future-append invariance at every truncation
   and a forward-mutation test that replaces every later bar with garbage.
2. The published v0.2 readouts are independently re-derived exactly, and the
   rejected v0.1 close-only aliasing is independently demonstrated
   (0 vs 30 episodes on the same reference). A second, independent
   reimplementation of `R/O/N` written from the spec text agrees with the
   module on 698 of 698 observations.
3. The primary use case is served **for boxes whose sweep period fits inside
   the 120-bar window**: across 53 post-probe bars of large-box traversal
   reaching 118, 119 and one tick above 120, PTM **never** claims new
   territory, while a genuine escape is recognised on the same completed close
   as the escape (latency 0). This does **not** carry over to a box whose
   sweep is longer than the window, which is defect `D1`.
4. The observable is not a strict function of ER20, rolling range/ATR width or
   a Donchian gate on controlled paths.
5. Every failure found is reproduced by a named fixture. The guards that
   address them are **specified** as `A1`–`A6` in §7; `A4` exists in the
   prototype as a challenger mode, while `A1`, `A2` and `A3` are **not yet
   implemented** and their thresholds are undeclared, so they are
   implementation prerequisites inside the preregistration commit rather than
   satisfied conditions.

Conditions (mandatory): amendments `A1`–`A6`, with `A1`, `A2` and `A3`
implemented and re-tested **inside** the prereg commit before any outcome is
read; the falsification criteria below; and an explicit statement that PTM is a
**challenger evidence layer** only.

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

### Independent verification pass

A second agent, with a fresh context and no access to this document's
reasoning, audited the prototype against the spec text and wrote its own
`R/O/N` implementation. Results:

| check | outcome |
|---|---|
| spec conformance of the core geometry | confirmed, **except** the strict/inclusive touch predicate (`C1`, fixed) and the scale-break claim gate (`C2`, fixed) |
| 19 cited numbers re-derived independently | 19/19 exact |
| `R/O/N` recomputed from the spec text over the whole fixture family | after `C1`: 698/698 observations agree |
| truncation causality, every fixture × every cut | 0 violations |
| forward **mutation** (all later bars replaced by garbage) | 0 violations |
| long/short reflection symmetry | 0 violations after `C5`; the residual scale-break asymmetry is multiplicative-vs-affine and is now pinned by a test |
| fail-closed sweep over all observations | 0 cases of numeric novelty under `UNKNOWN_*`; 0 claims under `DEGRADED_*` |
| artifact reproducibility | 42/42 files byte-identical |
| document/table consistency | reproduction table 8/8, latency table 8/8, `summary.json` fields as stated |

Its two harshest objections, both accepted and now reflected above: the verdict
was conditional on guards (`A1`–`A3`) that were not implemented, and the
"primary use case is served" claim depended on every fixture window containing
at least three complete sweeps. Both are now stated as conditions rather than
as achieved results.

#### Phase-2 verification pass

A second adversarial pass audited the phase-2 patch and its evidence. Findings
and their disposition are recorded in §12; the phase-2 verification table is in
§12.

## 10. Artifacts

```
indicators/wyckoff-regime-radar/research/
  ptm_territory.py                              PTM v0.2.2 prototype (+ A1/A2/A3)
  ptm_promotion_clock.py                        corrected B3 promotion clock
  ptm_territory_fixtures.py                     33 deterministic fixtures
  ptm_territory_charts.py                       Pillow audit charts
  analyze_issue185_price_territory.py           runner
  test_issue185_price_territory.py              190 tests
  decisions/issue-185-price-territory-engineering-review-finding.md   (this file)
  decisions/issue-185-price-territory-integration-interface.md
  decisions/issue-185-price-territory-prereg-draft.md
  artifacts/issue185_price_territory/
    issue185_ptm_report.md                      run report
    issue185_ptm_summary.json                   machine-readable summary
    issue185_ptm_latency.csv                    first-recognition statistics
    issue185_ptm_reproduction.csv               published-readout comparison
    issue185_ptm_phase2_comparison.csv          v0.2 vs fixed, per fixture
    issue185_ptm_promotion_clock.csv            the six-timestamp clock
    issue185_ptm_traces_all.csv                 all per-bar trajectories
    traces/<fixture>.csv                        one trajectory per fixture
    charts/*.png                                audit and comparison charts
```

The whole artifact tree (**50 files**) reproduces byte-for-byte on one machine:
re-running `python analyze_issue185_price_territory.py --outdir <tmp>` and
hashing every file against the committed tree yields zero differences. CI
enforces the **text** artifacts (CSV, JSON, Markdown) with
`diff -r --exclude=charts` against the committed tree, and enforces chart
determinism by diffing the PNGs of two runs on the same runner plus a
count/dimension sanity check. PNG bytes are deliberately **not** asserted
across platforms: rasterisation depends on the Pillow/FreeType build, which is
why Pillow is pinned and the renderer no longer performs an OS-dependent font
lookup (`C6`). Line endings are handled by git normalisation (blobs are LF), so
the comparison is always between two trees produced on the *same* platform.

## 11. Boundary statement

No market data was downloaded or used. No historical return, trade, position,
exposure, P&L or risk statistic was computed. No parameter was tuned; the only
constants are the design candidates from the v0.2 note plus the explicitly
labelled descriptive diagnostics in §2. OOS5 was not contacted. No Pine,
production, strategy or sizing rule was modified. Nothing was merged; no pull
request was opened. `#78` remains open.

**This is a design-feasibility conclusion, not a trading-performance
conclusion.**

## 12. Phase-2 verdict

### `READY_FOR_PREREG_REVIEW`

Exactly one verdict was permitted. The alternatives and why they do not apply:

* **not `NEEDS_REDESIGN`** — the phase-1 blockers D1/D7 are closed by
  implemented, tested guards; the promotion-clock contract error is corrected in
  code and in both companion documents; no claim of the instrument is now
  unsupported, and the one overclaim found in its own earlier draft has been
  withdrawn (§5.h);
* **not `BLOCKED`** — nothing external is missing. The patch, its tests, its
  artifacts and its reproducibility gate are all complete and self-contained.

`READY_FOR_PREREG_REVIEW` means the **engineering patch is ready for Sophira's
review**. It does **not** mean the prereg is frozen, and it does **not** authorise
a run. Per the review comment, the next gate is Sophira signing off before a
separate frozen research run.

### What was required, and what was delivered

| required by the review | disposition |
|---|---|
| §1 fix the timing contract; model six timestamps; `eligible_promotion_t = B3+3`, never `probe+3`; measure against the real B3-eligible promotion | done — `ptm_promotion_clock.py`, integration interface §4, prereg §4.1; the naive baseline's error is measured (**10** bars for `B3+10`, up to **80** on the long trend) |
| §2 A1/A2/A3 must actually be implemented; `long_period_box` `R=1, N=0.5, claim=True` inside the box must stop | done — A1/A2/A3 implemented with frozen thresholds; `long_period_box` goes 12 claim bars → **0**; a test proves lowering only `min_reference_cycles` reopens the claim |
| §2 report false-suppression and genuine-trend lag **together**, not one without the other | done — `issue185_ptm_phase2_comparison.csv` reports both per fixture; the cost is named (`one_way_reference_genuine_trend`), classified and declared in prereg §2.2; a rejection rule (prereg §7 rule 7) is predeclared |
| §3 do not claim first-day novelty has zero information across a population | done — the claim is withdrawn in §5.h and in integration-interface §6; the narrow, correct statement replaces it |
| §3 not authorising fast adds | respected — no fast-add policy exists anywhere; the interface and prereg both forbid it |
| §4 no forward outcomes; do not close #185 | respected — no market data, no returns, no OOS; #185 stays open |

### Verification performed

| check | outcome |
|---|---|
| test suite | **190 passed** (`python -m pytest -q test_issue185_price_territory.py`) |
| published v0.2 readouts after the patch | 8/8 still match exactly (`episodes_match` and `novelty_match` both true) |
| artifact reproducibility | **50/50** files byte-identical between two runs; committed tree == fresh run |
| config fingerprint completeness | every `PTMConfig` field is in `fingerprint()` and no extra keys (checked with `dataclasses.fields`) |
| guards cannot be bypassed by the default path | `apply_phase2_guards` defaults to `True`, is asserted in the CI evidence gate, and every claim is re-derived from the predicate in a test |
| no fixed waiting period added | `observable_at_bar = t`, `actionable_at_bar = t+1` on every observation of every fixture |
| long/short reflection symmetry | A1/A2/A3 outcomes and R/O/N identical under mirroring on every checked fixture |
| causality under truncation | the five guard-relevant fixtures × every cut reproduce the corresponding prefix of the full run (no future dependence) |
| pinned documentation numbers | the 18 v0.2-vs-fixed claim counts quoted in §6.E are enforced by `test_phase2_comparison_numbers_are_pinned` |
| A5 freeze gap found and closed | `anchor_policy` was only a bare argument to `evaluate_stream`, so the defective re-anchor policy could be selected **without changing the frozen fingerprint**. It is now a `PTMConfig` field, in the fingerprint, validated (unknown values raise), and pinned by tests |
| independent adversarial audit | **see §12.1** — it found one P1 defect in this author's own phase-2 code; that defect is fixed and re-mutated |

### 12.1 Independent phase-2 adversarial audit

A verifier with no access to the author's reasoning was instructed to **falsify**
the patch and to report nothing it had not executed. It pinned the source tree
by SHA-256, re-ran everything against that snapshot, and reported per item.

| audit item | verdict |
|---|---|
| guard bypass on all fixtures + 4 000 fuzzed episodes | not falsified for defaults — **but one P1 fail-open found** |
| promotion-clock arithmetic (432-case grid) | not falsified |
| documented claim counts recomputed independently | not falsified (14/14 exact) |
| division by zero / NaN / inf | partially falsified — two real defects |
| vacuous tests + mutation testing (16 mutants) | **4 mutants survived** |
| config fingerprint completeness | not falsified (20 fields ⇔ 20 keys) |
| artifact honesty recomputed independently | not falsified (33/33 fixtures exact) |
| byte reproducibility | not falsified (48/48 across runs and vs committed) |
| overclaims in the generated report | **falsified — three statements** |

| id | sev | finding | disposition |
|---|---|---|---|
| A-P1 | **P1** | A reference bar with `low = -1e308, high = +1e308` is *finite*, so the reference-level finiteness check passes, but the derived span overflows to `inf`. Then `inf/inf = nan` and `nan < 0.5` is `False`, so **both** A1 envelope sub-guards silently failed **open** and a claim was emitted carrying `envelope_covered_fraction = nan`. 233 of 3 000 fuzzed pathological series reproduced it. | **FIXED.** `_envelope_geometry` now rejects non-finite or inverted bar ranges and any non-finite derived quantity, returns `unusable=True`, and the caller fails closed: an explicit reason is added, coverage is reported as `0.0` and the gap as `1.0` — never NaN. `reference_gap_diagnostics` mirrors it. Pinned by `test_audit_non_finite_bar_range_fails_closed_not_open`; restoring the old code is killed by that test. |
| A-P2a | P2 | Mutants M1 (drop `reference_adequacy_ok` from the claim gate) and M9 (drop `scale_stable`) survived the suite as it then stood (151 tests). | **FIXED.** Pinned directly on the predicate by `test_audit_claim_gate_requires_adequacy_and_scale_even_at_validity_ok`. Re-run mutation: both killed. |
| A-P2b | P2 | Mutants M10 (disable the gap reason) and M11 (disable the coverage reason) survived: only the **cycle** sub-guard was individually pinned. | **FIXED.** Two new fixtures trip **exactly one** envelope sub-guard each (`envelope_gap_only`: coverage 0.68 passes, gap 0.32 fails; `envelope_coverage_only`: gap 0.20 passes, coverage 0.40 fails), backed by a CI assertion on `validity_reason_count == 1`. Re-run mutation: both killed. |
| A-P2c | P2 | `radius_divisor=0` raised a bare `ZeroDivisionError`; `acceptance_window=1` sliced `[-0:]`, the **whole history**, silently redefining the acceptance trace. | **FIXED.** `PTMConfig.__post_init__` rejects the whole class of crash/redefinition inputs (30 parametrized cases), and the slice is guarded. Each pinned by a test. |
| A-P2d | P2 | The report claimed `apply_phase2_guards=False` leaves "every diagnostic identical". False: `validity` differs on 6 fixtures and `guards_enforced` on 30. | **FIXED** in the generator: the report now states exactly what is identical (all measured quantities: R, O, N, acceptance, A1/A2/A3 numerics) and what is not (the gate and the derived labels). |
| A-P2e | P2 | The report claimed all delay comparisons use the corrected baseline, contradicted by 11 rows of its own CSV carrying a naive-baseline column. | **FIXED** in the generator: the two baselines are now named and distinguished. |
| A-P3 | P3 | `max_added_delay_vs_v02_bars = 0` was unqualified (for suppressed fixtures the delay is unbounded, not zero). | **FIXED**: a scope qualifier ships in the summary and the report, asserted in CI. |
| A-P3 | P3 | `_swing_legs` docstring called the return value "turning points"; it is the number of confirmed reversals (a monotone window returns 0). | **FIXED**: docstring corrected. |
| A-P3 | P3 | `probe_plus_three_naive_t` is derived from `confirmation_bars`, not literally `probe+3`. | **FIXED**: an explicit `naive_probe_clock_basis` string ships in the dataclass so a non-default window cannot be misread. |

Defects the audit found that are **accepted and left open**, with reasons:

1. A denormal `tick = 5e-324` is accepted and produces `inf` in the published
   relative diagnostics. The band width itself is still finite and the claim
   gate is unaffected; the value is absurd input rather than a reachable market
   condition. Recorded, not fixed.
2. Reference closes containing `NaN` are labelled
   `UNKNOWN_ZERO_BAND_WIDTH` rather than a dedicated non-finite label. The
   claim is still blocked and `w` is still `None`; only the label is imprecise.
3. The clock accepts negative timestamps and truncates float timestamps via
   `int()`. It is a modelling helper, never fed by the indicator.
4. `b3_confirmation_t` is populated even when confirmation failed and
   eligibility is `None`. It records *when* confirmation would have completed,
   which is useful for the failure case.
5. `apply_phase2_guards` is documented as a runner-only comparison switch but is
   not enforced as one. It defaults to `True`, no default construction sets it
   to `False`, and no real observation path can reach `False`; a caller holding
   the dataclass can still ask for the legacy gate deliberately.

The audit could not test the hosted CI path, the surrounding prose, or Pine
behaviour; those are disclosed here rather than implied to be verified.

### Open items carried into the prereg (not blockers)

1. **D4** — the overlap-fraction variant cannot exclude an enclosing wick.
2. **D5** — stagnation is reported but not solved.
3. **D8** — the scale-break screen remains a weak heuristic.
4. **D10** — the frozen one-bar screen is level-dependent and unfixed.
5. The A1 false-suppression **rate** on real cohorts is unknown and is the
   central measurement question (prereg §4.2).
6. No hosted CI status was visible for the phase-1 commit `89285e4` when this
   was written; the workflow was extended for phase 2 and its evidence gate was
   verified locally, but hosted execution is reported separately and honestly.

### Explicit non-authorisation

This verdict does not authorise historical outcome research, any parameter
change, any production or Pine change, any strategy or sizing change, any merge,
or any contact with OOS5. It authorises **review of the engineering patch**. The
preregistration remains a DRAFT.
