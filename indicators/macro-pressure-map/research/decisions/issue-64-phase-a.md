# Issue #64 Phase A — regime-conditioned asset behaviour

## Interim verdict

**`cross_asset_structure_present_but_regime_specific_and_era_sensitive`**

Phase A finds economically meaningful cross-asset differences across the frozen Macro Pressure Map V6.6 Growth × Inflation regimes, but it does **not** support assigning a separately optimized historical winner to each of the nine cells.

The most coherent **exploratory Phase B hypothesis** is **Reflation / Inflation Rising → SPY outperforming TLT**. The point direction survives a pre-2020 development slice and a post-2019 reused exploratory slice at both the 1M and 3M horizons, with nominal paired-return bootstrap intervals above zero in both eras.

This relationship was selected after inspecting 81 regime / horizon / pair comparisons. Those intervals are **not adjusted for post-selection or multiplicity**, so they do not establish a confirmed or robust allocation effect. They justify a deliberately constrained prospective-style portfolio hypothesis test on reused history, not an alpha claim.

By contrast, many other apparent full-history regime winners change when the history is split. The correct Phase-A conclusion is therefore not “the nine cells map cleanly to nine portfolio recipes.” It is “some regime-conditioned relative-asset relationships are coherent enough to justify constrained portfolio hypotheses, while many cells are era-sensitive and should default to a neutral diversified allocation.”

## Evidence and provenance

Signal state is not rebuilt from a fresh FRED download. It is derived from the exact TradingView V6.6 parity log already used in Issue #59:

- source Pine-log SHA-256: `c0220d4974b2fd0154c4cf8f33b4b3effb27a58e21ee96a1b0109011ce638e3d`;
- plotted V6.6 axes use EMA(5), so raw state is recovered causally from adjacent plotted observations using `raw_t = 3 * plot_t - 2 * plot_(t-1)`;
- independently rebuilding raw GPI / IPI / FCPI from the logged V6.6 source inputs after Python warm-up gives maximum absolute discrepancies of only about `2.5e-08`, consistent with TradingView log decimal rounding;
- `verify_issue_64_axis_reconstruction.py` reproduces that independent raw-axis cross-check when supplied the exact hash-frozen operator-local Pine log and fails if any axis exceeds `5e-08` maximum absolute error;
- the committed `issue-64-frozen-axis-audit.csv` preserves 51 deterministic raw GPI / IPI / FCPI checkpoints (every 100th derived row plus the final row), SHA-256 `9021844c7ed0b927ce95ca3de117ac3749eb3c5541e5d6c46557aa5624fa08c1`;
- the committed derived transition file has SHA-256 `80446bbcb91be8b18eb0b95e62466edf892e4c04087696a04532f0fe214698af`;
- frozen regime history: 2007-01-04 through 2026-08-14, 4,934 daily rows represented by 739 transitions;
- outcomes: adjusted-price SPY / TLT / GLD proxies from Yahoo Finance using `auto_adjust=True`;
- signal is never forward-filled past 2026-08-14. Later outcome prices may only complete forward windows that started while a frozen signal existed.

The operator-local Pine log remains intentionally uncommitted. The committed axis audit is inspectable evidence, while the verification script provides the reproducible full-axis cross-check path for a checkout that has the hash-matching source log.

Latest verified workflow:

- run `32439125598`;
- artifact `9431783095`;
- artifact SHA-256 `4f5fe53b8dd8bec8d7ef862673d1296c6261b143150cc010e4fec5c1addd9df9`;
- 10 focused tests passed;
- strict JSON validation passed;
- evidence artifact upload passed.

## Regime occupancy

All nine frozen regimes have material representation. The two largest are:

- Slowdown / Disinflation: 1,094 rows, 22.17%;
- Reflation / Inflation Rising: 1,057 rows, 21.42%.

The smallest still has 319 rows (Growth Slowdown / Stable Inflation, 6.47%). The main limitation is therefore not a missing nine-cell state; it is temporal stability of the asset preference inside each state.

## Why a nine-cell winner map is rejected

Phase A splits the history into:

- **development:** 2007-01-04 through 2019-12-31;
- **post-2019 reused exploratory:** 2020-01-01 through the frozen signal cutoff.

The development price panel itself ends at 2019-12-31, so a 1M / 3M / 6M forward window starting near the end of development cannot borrow 2020 outcomes.

Across 9 regimes × 3 horizons = 27 leader comparisons:

- only **9 / 27** have the same best-return asset in both eras;
- development leaders: SPY 12, TLT 8, GLD 7;
- post-2019 leaders: SPY 5, TLT 0, GLD 22.

That post-2019 gold dominance is too different from the development distribution to justify a full-history “best asset per cell” rule.

Across 81 direct pairwise regime / horizon comparisons (SPY−TLT, SPY−GLD, TLT−GLD), only **39 / 81** retain the same point-estimate sign across the two eras. Only **2 / 81** have nominal 95% paired-spread intervals excluding zero in the same direction in both eras. Because this is a multiple-comparison search, those 2 cells are hypothesis-generating rather than multiplicity-adjusted discoveries.

## Selected exploratory hypothesis — Reflation: SPY over TLT

Direct paired-return spread = SPY total return minus TLT total return.

### 1M

- development: **+1.41%**, nominal 95% CI **[+0.01%, +2.74%]**, n=51 embargoed starts;
- post-2019 reused exploratory: **+2.31%**, nominal 95% CI **[+0.70%, +4.01%]**, n=22.

### 3M

- development: **+4.17%**, nominal 95% CI **[+1.41%, +7.02%]**, n=23;
- post-2019 reused exploratory: **+6.42%**, nominal 95% CI **[+2.71%, +10.39%]**, n=11.

### 6M

- development: +4.58%, nominal 95% CI [-4.17%, +12.32%], n=15;
- post-2019 reused exploratory: +12.00%, nominal 95% CI [+6.75%, +17.61%], n=7.

The sign remains positive at 6M, but development uncertainty is wide. Because Reflation/SPY-over-TLT was selected after inspecting the broader table, the appropriate claim is only that it is the **most coherent candidate for an isolated Phase B override**, not that the relationship has been statistically confirmed.

## Promising but weaker hypothesis — Stagflation: gold over equity

For SPY minus GLD, the point estimate is negative in both eras at all three horizons:

- 1M: development -1.48%, post-2019 -1.05%;
- 3M: development -4.04%, post-2019 -4.13%;
- 6M: development -6.08%, post-2019 -9.21%.

However, development confidence intervals cross zero at every horizon. Only the post-2019 6M interval excludes zero. This is economically coherent and may be tested as a separate secondary override, but it is not confirmatory evidence.

## Important counterexample — Slowdown / Disinflation is era-sensitive

The full-history table makes gold look strong in Slowdown / Disinflation, but TLT versus GLD changes materially by era:

- 1M TLT−GLD: development +0.78% vs post-2019 -2.19%;
- 3M: development +0.60% vs post-2019 -8.50%;
- 6M: development -2.35% vs post-2019 -17.05%.

Therefore Phase A does not justify a hard rule such as “Slowdown = long duration” or “Slowdown = gold.” A diversified defensive/default allocation is methodologically safer until a separate, stable relationship is demonstrated.

## Phase A decision

Proceed to **constrained Phase B**, but reject per-regime historical optimization.

Phase B should use a small number of transparent portfolio templates with a neutral/default allocation for ambiguous regimes. The first test should isolate one hypothesis selected from Phase A rather than exploit every observed cell.

A conservative sequence is:

1. neutral diversified portfolio as the default;
2. one pre-frozen Reflation override that overweights equity and underweights long duration;
3. measure that portfolio effect as an exploratory reused-history test, explicitly accounting for the fact that the hypothesis was selected from Phase A;
4. only afterward, optionally test a separate Stagflation gold-over-equity defensive override;
5. do not invent separate fitted weights for the remaining seven states.

Exact weights, rebalance timing, cost assumptions and comparison benchmarks must be frozen **before** Phase B portfolio results are viewed.

## Evidence boundary

Everything in Phase A is development / reused exploratory historical evidence. The 2020–2026 slice is **not** newly untouched OOS. Nominal bootstrap intervals are not multiplicity-adjusted and should not be read as confirmatory discovery statistics. No production V6.6 parameter changed.
