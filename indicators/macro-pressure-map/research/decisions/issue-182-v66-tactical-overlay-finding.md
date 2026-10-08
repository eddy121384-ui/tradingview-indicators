# Issue #182 — V6.6 tactical overlay — Finding

- Issue: [#182](https://github.com/eddy121384-ui/tradingview-indicators/issues/182)
- Branch: `research/issue-182-v66-tactical-overlay`
- Base (pre-issue) HEAD: `ac251ad5149d9f550d82dfb34b3551fe01032367` (#180 final)
- Prereg commit (FIRST, BEFORE any overlay result):
  `ff56fd5d4cd5c238bec2ff83befabda220a9e605`
- Formal verdict: `v66_tactical_overlay_candidate_supported`
- `production_authorized=false`
- Research only. No optimizer ran. No Pine changed. Do not merge.

## 1. Bottom line

The bounded ±5pp Equity↔Cash V6.6 overlay earns a narrow, risk-shaped place:
on the primary 2007-01+ tradable panel (n=232) post-cost C vs structural A
gives CAGR **−0.31pp/yr**, Sharpe-like **+0.011**, MaxDD **+1.33pp better**
(−15.11% vs −16.44%), incremental turnover **+21.2pp/yr**, cost drag
**0.011pp/yr**, A-vs-C corr **0.997**, top-1 episode share **21%**, best/worst
state ranks unchanged, defensive-state vol worse by only 0.45pp. All 7 frozen
gates pass. The overlay does not add return; it trims left-tail risk at
negligible cost. Risk-off dominates the sample (163/232 months).

## 2. Frozen design (verbatim prereg)

V6.6 bytes reused exactly (gzip/csv SHAs verified, 388 months, no gaps);
rule: Growth=High & Inflation≠High → risk-on; Growth=Low OR Inflation=High →
risk-off; else neutral (High/High is risk-off by construction). Budget ±5pp
Equity↔Cash only; pro-rata non-zero equity sleeves; tier-0 stays 0; sleeve
caps + 60 family cap + cash floor 2; single-pass blocked→Cash (blocked: none
in 27 combos). Timing: overlay(m) from V6.6 state(m−1) (alternate: m−2);
structural B-2 intact. Costs: turnover×2bp (alternate 10bp). Panels:
research-backbone + tradable ETF, both 2007-01 → 2026-08. Sensitivities:
±10pp / lag-2 / 10bp only.

## 3. Parent-input integrity disclosures (material)

(a) V6.6 month mapping: month-end dates → calendar months; primary window
2007-01+ per #160 lineage (pre-2007 partial-component history excluded).
(b) IMPORTANT — #178 backtest carries a cash-minimum bug AFFECTING ONLY the
A leg: its `loadTiers` reads `cash-bias.csv` col 1 (opportunity_score
"9"/"7"/…) instead of col 2 (bias label), so `CMIN_BIAS` lookup yields
`undefined` and the bias-minimum scaling never fires; cash falls back to
residual floored at CASH_MIN=2 with non-cash unscaled. Proof: byte-exact
replication of the buggy engine reproduces `backtest-monthly.csv` with
0 mismatches / 232 months. Affected: Low-Low (weights sum 103, cash 2) and
Neutral-Low (sum 107, cash 2) — inadvertent leverage up to 109% gross,
violating #178's own no-leverage criterion. All other states byte-identical
to matrix weights. The frozen matrix itself is correct (rows sum 100.00).
(c) Consequences for #182: leg A is taken VERBATIM from frozen parent files
(exact by construction); legs B/C build on frozen MATRIX weights (sums 100,
no leverage — acceptance criteria require it). Measured C−A therefore mixes
overlay effect + base correction in LL/NL months. Attribution (post-hoc
arithmetic, not a gate input): base effect (matrix-base minus file-A) averages
−6.2bp/mo over 29 LL months and −9.5bp/mo over 43 NL months (≈ −0.30pp/yr
panel-wide); the PURE overlay effect is ≈ −0.01pp/yr — i.e. essentially
return-neutral with the risk improvements above. Gates were evaluated on
as-measured C−A per prereg (frozen A reproduction); the verdict is unaffected
in direction, and this decomposition is disclosed so no one misreads the
−0.31pp gap as overlay harm.

## 4. A/B/C performance (primary tradable panel, n=232)

A: 8.13% / 7.78% / +6.51% excess / 0.853 / −16.44% / −6.79%.
B: 7.84% / 7.30% / +6.22% / 0.865 / −15.10% / −6.14%.
C: 7.82% / 7.30% / +6.21% / 0.864 / −15.12% / −6.14%.
Research panel: A 8.00% / B 7.44% / C 7.43% (same pattern; overlay ≈ neutral
on returns, vol −0.78pp, MaxDD +1.81pp).
Frequencies: risk-on 35 (15%), risk-off 163 (70%), neutral 34.
Avg Equity 42.6% / Cash 22.1% under overlay.

## 5. Preservation gates (frozen §8, primary panel — all pass)

g1 CAGR −0.31pp ≥ −0.50 ✓; g2 Sharpe +0.011 ≥ −0.05 ✓; g3 MaxDD +1.33pp ≥ −3 ✓;
g4 incremental turnover 21.2pp ≤ 40 ✓; g5 top-1 21% ≤ 60% ✓;
g6 worst segment −0.65pp (2023+) ≥ −1.0 ✓; g7 worst state (n≥12) −1.82pp ≥ −3.0 ✓.
>1pp months: 3.4% (8/232). Rank kept (best High-Neutral, worst Low-High both
legs). Defensive vol: +0.45pp max. → SUPPORTED.

## 6. Conditional diagnostics (diagnostic only, no remapping)

- By V6.6 class (tradable mean contrib/mo): risk-on +2.8bp (n=35),
  risk-off −4.4bp (n=163), neutral −0.1bp (n=34). Benefit is NOT from
  risk-on timing; it comes from smaller losses/drawdown in risk-off months.
- Alignment (Growth bands equal): aligned 83 mo −5.6bp/mo vs divergent 149 mo
  −1.1bp/mo — overlay drag concentrates where layers agree, not where V6.6
  adds orthogonal information. Reported, not a rule.
- Transitions (±3mo union, 36 events): inside −3.6bp/mo (n=172) vs outside
  −0.3bp/mo (n=60) — no transition-timing edge; motivation unconfirmed.
- Segments: pre-2020 −0.34pp/yr, 2020–22 +0.16pp/yr, 2023+ −0.65pp/yr
  (tradable); risk improvement (MaxDD) present in all three.
- States: contributions −15bp to +8bp/mo; worst-state gate passes; High-Low
  n=3 — too thin to read.

## 7. Sensitivity (descriptive; primary retained)

S1 ±10pp: C 7.46% (−0.36pp vs primary C) — doubling the budget does not help.
S2 lag state(m−2): 7.81% (−0.01pp) — timing robust.
S3 10bp costs: 7.77% (−0.05pp) — costs immaterial at this turnover.
No promotion. No grid.

## 8. Benchmarks (V6.6 panel, proxies)

Neutral ETF 7.42%/−24.2%; Cash 1.52%; SPY 10.85%/−50.8%; 60-40 8.12%/−29.5%.
Overlay C (7.82%) sits between neutral and 60-40 on return at lower vol than
both, with the shallowest MaxDD of any risk-taking comparator.

## 9. Limitations

19.4-year V6.6 window (2007+); 70% risk-off sample skew; High-Low n=3;
revised (not vintage) macro + market data; #178 A-leg bug disclosed above
(B/C unaffected — matrix-based); sleeve proxy imperfections inherited
(#180: QQQ/IEF/GLD/USO materially different at sleeve level, absorbed at
portfolio level); zero modeled costs beyond turnover rate; candidate only.

## 10. Artifacts (all `issue-182`)

Prereg, `issue_182_overlay.py`, `test_issue_182_overlay.py`,
`test_issue_182_mirror.mjs` (ALL PASS, 12 assertions), `issue_182_build.mjs`,
`issue_182_backtest.mjs`, `v66-input-manifest.json`,
`v66-exact-monthly.csv.gz.b64` (byte-exact copy), `tactical-timeline.csv`
(236 months: 36 on / 166 off / 34 neutral), `overlay-weights.csv` (27 combos),
`structural-vs-overlay.csv`, `performance.json`, `incremental.json`,
`state-diagnostics.csv`, `v66-diagnostics.json`, `alignment.json`,
`transition.json`, `era-stability.json`, `sensitivity.json`,
`benchmarks.json`, `overlay-policy.json`, `summary.json`, this finding.

## 11. Tests / determinism / bugs

- Python stdlib suite (classify incl. High/High→risk-off; overlay incl.
  cash-floor/family-cap/zero-sleeve cases; gate mapping) + Node mirror
  ALL PASS.
- V6.6 continuity asserted (388/388 months); CSV+gzip SHA gates pass.
- A-leg file-verbatim attachment (R n=232, T n=232; timeline drift asserted).
- Tradable-A matrix recompute cross-check 0/232 (proves #180 has no analogous
  bug). B/C rerun bit-identical.
- Bugs fixed pre-final: (1) git-show revision syntax for cross-branch bytes;
  (2) duplicate prevYm; (3) paren/brace slips; (4) era-block variable
  shadowing + Ws propagation; (5) sensitivity legs reporting pre-cost
  (now post-cost) + ONEQ cost application; (6) dead-code removal;
  (7) THE #178 cash-min bug — documented in §3, NOT repaired (frozen parent),
  worked around by file-verbatim A + matrix-based B/C + base-effect attribution.

## 12. Explicit confirmations

- #178 weights/tiers/zeros/caps/B-2, #180 proxies/costs/timing, V6.6 bytes —
  all unchanged (SHA-pinned; timeline 0 mismatches; A legs verbatim).
- No trajectory, no V6.6 rebuild/remap, no budget search, no sleeve/duration/
  gold/oil rotation, no leverage/shorts, no optimizer/grid, no #169-trigger
  use, no pristine-OOS claim.
- `future_allocation_policy_candidate`: none from this issue (overlay verdict
  stands on frozen rules; any timing/budget variant needs a new issue).
- `production_authorized=false`. Do not merge.
