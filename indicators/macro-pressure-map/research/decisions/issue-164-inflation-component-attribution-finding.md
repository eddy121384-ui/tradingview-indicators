# Issue #164 — Deep-History inflation v0.1 — component attribution

- Issue: [#164](https://github.com/eddy121384-ui/tradingview-indicators/issues/164)
- Branch: `research/issue-164-inflation-component-attribution` (isolated worktree; shared checkout untouched)
- Frozen model: `cc331bf11591ab49c6f5a5023cfee39b2cf09fde`
  (DH monthly CSV SHA256 verified `42516418ec8d1ce981d1b4bc05e2ae86809d6acbf5de63dccbad515db507dcfc`)
- Frozen parents: #160 (5 equal-weight roles), #161 (inflation valid with
  limitations), #163 (leading NOT supported; 182 composite vs 105 CPI turns,
  median lead 0, 82 unmatched composite turns — all reproduced exactly here)
- Formal verdict: `inflation_component_attribution_mixed`
- `outcome_data_loaded=false`
- `production_authorized=false`
- Attribution is arithmetic only; no causality claimed. No model change, no
  v0.2, no asset-outcome testing. Do not merge.

## 1. Turn frequency (A): excess turning is systemic, not component-specific

Frozen sign-reversal + 1M-confirmation rule, identical for all series:

| component | turns | median dwell | mean dwell | composite ±1mo share | unique (share) | unmatched-82 hit (share) |
|---|---|---|---|---|---|---|
| I1 Headline CPI | 179 | 3.5 mo | 3.97 | 0.769 | 19 (10.6%) | 56 (68.3%) |
| I2 Core PCE | 171 | 3.0 mo | 4.30 | 0.687 | 21 (12.3%) | 58 (70.7%) |
| I3 Producer Prices | 174 | 4.0 mo | 4.21 | 0.736 | 21 (12.1%) | 55 (67.1%) |
| I4 Wage Growth | 176 | 4.0 mo | 4.17 | 0.698 | 30 (17.1%) | 61 (74.4%) |
| I5 Energy Inflation | 181 | 4.0 mo | 4.04 | 0.753 | 22 (12.2%) | 57 (69.5%) |

No small subset explains the excess: all five turn 171–181 times with 3–4
month median dwells, accompany ~70–77% of composite turns, and implicate
~67–74% of the 82 unmatched composite turns each. I4 (wages) is marginally the
most idiosyncratic (highest unique and unmatched shares) but the gaps are
small. Conclusion: high-frequency turning is a property of applying 60-month
z/momentum scoring to noisy monthly inputs — systemic across roles, not
attributable to one or two bad components.

## 2. Short-horizon swings: mild shock > broad > persistent gradient

Mean absolute monthly / 3-month score changes: I5 15.6/25.1, I3 15.0/22.6,
I1 14.8/22.9, I4 14.8/21.2, I2 14.2/19.6. Energy moves most per month, core PCE
least — the predicted direction, but the spread is narrow (~10% on 1M,
~28% on 3M), so this is a gradient, not a cleavage.

## 3. Early-extremum drivers (B, C): rotating, not consistent

Level shares at the composite extremum (points = score/5) and 3M-change shares:

- **1973–75 peak (1974-01, +66.6):** level I5 28.9% (96.2) + I3 25.2% + I1
  24.1% + I2 21.8%, I4 ≈ 0% (0.26, flat); 3M-change I2 52%, I5 36%, I4 −14%.
  Driver: energy level + core-PCE run-up; wages absent.
- **2008 spike (2007-11, +45.2):** level I3 32.3% + I1 30.7% + I5 23.8% +
  I2 19.2%, I4 −5.8% (opposed, −13.1); 3M-change split I1/I3/I5 ≈ 26–29% each.
  Driver: joint broad + upstream + energy; wages opposed. All components had
  turned up 12–15 mo earlier — a collective early turn.
- **2008 crash trough (2008-12, −84.2):** all five deeply negative (−74 to
  −92); 3M-descent I1 28% + I3 28% + I5 25%, I2 12.5%, I4 6.4%. Broad-based
  collapse led by CPI/PPI/energy; wages marginal.
- **2021–22 surge (2021-04, +92.6):** all five simultaneously extreme
  (85–97; level shares 18–21% each); 3M-change I4 28.2% (wage surge +118),
  I1 24.5%. Driver: whole-composite spike with wages the largest marginal
  contributor; earliest turns 2020-01–2020-03 (COVID rebound).
- **2023–26 trough (2023-06, −29.3):** level I5 37.5% + I3 32.0% + I1 30.5%,
  I2 6.7%, I4 −6.7% (opposed at +9.8); 3M-descent I2 80.7% + I1 50.9% against
  flat/opposed energy, PPI, wages. Driver: headline + core disinflation while
  wages never normalized.
- Other episodes in table: 1978–80 peak jointly led (I2 change share 82%),
  1981–86 trough broad-based, 1990 peak energy-led on the month (d1 share
  182% against offsetting core), late-60s edge peak (sample-start artifact;
  interior dynamics core/producer-led).

Wages twice opposed fast composite swings (2007-11, 2023-06) and were flat at
the 1974-01 peak — the slow persistent leg does not join rapid turns. But
"shock/upstream dominance" fails as a general rule: core PCE drove the 1974
run-up (52%), all five drove 2021-22 jointly, headline + core drove the 2023
descent. Drivers rotate by episode.

## 4. Semantic grouping test (D): frequency prediction fails

Persistent (I2+I4) vs broad (I1+I3) vs shock (I5): turn counts 347/353/181
(scale with group size; per-component rates identical), union median dwell 2 mo
for persistent and broad vs 4 mo for shock (density artifact: two series turn
nearly every other month somewhere). Persistent components do NOT turn less
often or dwell longer. Supported directionally only in swing size (§2) and in
wage idiosyncrasy (highest unique-turn share; opposed stance at fast extrema).

## 5. Independent benchmarks per component (E)

| component | deflator P/S/dir (n≈245) | 6M d3 S | 9M d3 S | CPI hit rate | CPI median lead |
|---|---|---|---|---|---|
| I1 CPI | 0.30/0.29/0.61 | 0.11 | 0.22 | 0.97 | 0 mo |
| I2 Core PCE | **0.37/0.36**/0.60 | 0.18 | 0.18 | 0.91 | 1 mo |
| I3 PPI | 0.19/0.19/0.57 | 0.14 | 0.20 | 0.96 | 1 mo |
| I4 Wages | −0.05/−0.01/0.53 | 0.06 | 0.06 | 0.93 | 2 mo |
| I5 Energy | 0.19/0.16/0.56 | 0.06 | 0.17 | 0.99 | 0 mo |

Core PCE has the best deflator link (still modest); wage *changes* carry no
future-CPI or deflator signal (wage *level* associates 0.24–0.25 with 6/9M CPI
change — Phillips-style level effect, reported descriptively). No component
leads CPI turns systematically (medians 0–2 mo with dense-turn coincidence).
Circularity disclosed: I1 is CPI itself (turn/direction overlap mechanical);
I2 shares PCE concepts with the deflator family.

## 6. Verdict

`inflation_component_attribution_mixed`

A small consistent culprit does not exist: excess turning is spread evenly over
all five components (systemic scoring property), and early-extremum drivers
rotate by episode (energy+core; joint broad; all-five; headline+core). Real but
partial patterns — shock swings largest, wages idiosyncratic and opposed at
fast turns, core PCE the best deflator link — do not reach the "clear" bar
(small subset consistently explaining most excess turns and/or early extrema),
while the sample is ample enough to rule out "inconclusive". No redesign is
authorized by this verdict.

## 7. Artifacts

- `research/decisions/issue-164-inflation-component-attribution-finding.md` (this file)
- `research/generated/issue-164/inflation-component-diagnostics.csv` (per-component table)
- `research/generated/issue-164/inflation-episode-attribution.csv` (9 extrema × 5 components)
- `research/generated/issue-164/inflation-component-attribution-summary.json` (all tables + verdict)

## 8. Workflow evidence and verification

- Isolated worktree at the frozen base; shared checkout untouched.
- DH CSV hash verified; benchmark FNV hashes verified (GDPD, Michigan, CPI/CorePCE reuse).
- Composite/CPI turn counts reproduced exactly from #163 (182/105) before attribution.
- A CRLF header-parsing bug initially zeroed the I5 column (phantom "energy exonerated");
  caught by the all-5-finite composite-consistency check and fixed — all numbers above
  are post-fix. A group-mean double-count bug was likewise caught and fixed.
- Episode windows, CPI/deflator extrema, and turn rule are #161/#163-frozen; the
  only new constructs are the documented ±1mo sharing and earliest-turn-in-window rules.

## 9. Explicit confirmations

- No asset-return outcome was loaded: no SPY/TLT prices or returns, no
  equity-minus-duration spread, no Issue #136 payoff data — frozen DH
  components plus CPI, GDP-deflator, and Michigan macro benchmarks only.
  `outcome_data_loaded=false`.
- No production code was changed; DH v0.1 was not altered, refit, reweighted,
  or reduced. `production_authorized=false`.
- Do not merge.
