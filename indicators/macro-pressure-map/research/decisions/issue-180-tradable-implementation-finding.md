# Issue #180 — Tradable implementation reality check — Finding

- Issue: [#180](https://github.com/eddy121384-ui/tradingview-indicators/issues/180)
- Branch: `research/issue-180-tradable-implementation-reality-check`
- Base (pre-issue) HEAD: `10dcdce0ec86b0493d6df6b916b720eba46dcbe6` (#178 final)
- Prereg commit (FIRST, BEFORE any implementation result):
  `35981b88b6e293492ce870a4f3dca6ce0d598823`
- Formal verdict: `tradable_implementation_candidate_complete`
- `production_authorized=false`
- Research only. No optimizer ran. No Pine changed. Do not merge.

## 1. Bottom line

The frozen #178 policy survives realistic ETF implementation essentially
intact. On the strict 2006-06+ panel (240 months, all proxies genuine):
implementation post-cost CAGR **8.16%** vs research **8.05%**
(gap **+0.11pp/yr**), vol 7.66% vs 7.77%, MaxDD **-16.5% vs -17.4%**,
TE **1.08%/yr**, cost drag **0.007%/yr**, 0.8% of months differ by >1pp,
best/worst state ranks unchanged, defensive-state vol worse by only 0.45pp.
All six frozen decision gauges pass. Costs are negligible because frozen
turnover is low (B-2) and ETF returns are net of expenses by construction.

## 2. Frozen implementation (verbatim prereg §§1–7)

All-ETF primary set (Yahoo monthly adjclose TR, net of ER, no backfill):
SPY 1993-01 / QQQ 1999-03 (LABELED Nasdaq-100 proxy, never renamed) /
IWM 2000-05 / SHY+IEF+TLT 2002-07 / GLD 2004-11 / USO 2006-04 (front-month
WTI fund, laddered since Apr-2020, ER 0.60%) / Cash = identical T-bill
series. Alternate: ONEQ genuine Composite (2003-10). Costs: turnover × 2bp
(primary), × 10bp (alternate); ERs documentation-only (already in NAV).
Execution: month-end close (alternate: 1-mo lag). Missing proxy → weight to
Cash. Strict panel 2006-06-01 (asserted 0 drops). Benchmarks: neutral ETF
basket / Cash / SPY / SPY-IEF 60-40 under identical framework.

## 3. Tracking study (unconditional; frozen §8 rules)

| sleeve | proxy | n | corr | TE% | annDiff | class |
|---|---|---|---|---|---|---|
| sp500 | SPY | 365 | 0.9982 | 0.89 | -0.06pp | faithful |
| nasdaq | QQQ | 331 | 0.9830 | 4.37 | +1.56pp | materially_different (universe mismatch, labeled) |
| russell | IWM | 315 | 0.9986 | 1.05 | +1.28pp | acceptable (TR-vs-price wedge favors fund) |
| treasury2y | SHY | 289 | 0.9846 | 0.29 | +0.10pp | acceptable |
| treasury10y | IEF | 289 | 0.8928 | 3.29 | +0.60pp | materially_different (band-vs-point duration) |
| longtreasury | TLT | 289 | 0.9869 | 2.57 | +0.01pp | acceptable |
| gold | GLD | 261 | 0.6281 | 13.68 | -0.48pp | materially_different (monthly-avg vs month-end timing) |
| oil | USO | 244 | 0.9229 | 15.66 | -9.10pp/yr | materially_different (contango + fees + 2020 shift) |

QQQ vs official Composite TR (2003+): quantified in tracking.csv. Cash:
identical → faithful by construction. Four materially-different sleeves are
REPORTED, not repaired — yet portfolio-level preservation still holds
(§5), because their weights are small and errors diversify.

## 4. A/B/C results (strict panel, n=240)

A research: 8.05% / 7.77% / +6.31% excess / 0.83 / -17.37% / -6.96%.
B pre-cost: 8.17% / 7.66% / +6.43% / 0.85 / -16.44% / -6.79%.
C post-cost: 8.16% / 7.66% / +6.42% / 0.85 / -16.45% / -6.79%.
Benchmarks (strict): neutral-ETF 7.53%/-24.2%; Cash 1.65%; SPY 11.22%/-50.8%;
60-40 8.38%/-29.2%. Full-live B/C span 1993+ (early years ≈ Cash by
construction — disclosed, not performance).

## 5. Preservation audit (§9 gauges, all pass)

| gauge | value | threshold | pass |
|---|---|---|---|
| \|CAGR gap\| | 0.11pp | ≤1.0 | ✓ |
| TE | 1.08% | ≤2.5 | ✓ |
| MaxDD gap | +0.92pp | ≥−5 | ✓ |
| cost drag | 0.007%/yr | ≤0.4 | ✓ |
| best/worst rank | HN best, LH worst, both legs | kept | ✓ |
| defensive vol | +0.45pp | ≤2 | ✓ |

>1pp months: 0.8% (2/240). Largest tracking months in preservation.json.
No defensive state became materially riskier.

## 6. State implementation (strict panel; small-n caveat on HL n=3, LN n=9)

Drag (post−research mean) per state ranges −0.12pp to +0.11pp/mo; worst
pre-cost months track research worst months closely. Full table
state-implementation.csv. Weights NEVER changed on these results.

## 7. Eras (frozen bounds; live-history honesty)

E1 B/C = Cash (100% cash weight — no proxies; reported, not hidden).
E2 B/C 77% cash. E3: B 7.43% vs A 7.15%. E4: B 9.16% vs A 9.36%.
Genuine implementation evidence lives in E3(partial)+E4; earlier eras are
research-history only.

## 8. Sensitivity (descriptive; primary retained)

ONEQ-for-nasdaq: 7.89%/7.72%/-16.7%. 10bp costs: 8.13% (drag still tiny).
1-mo lag: 7.82%/-19.7% (timing matters more than costs — reported, primary
kept). Conclusions stable.

## 9. Limitations

20-year strict live history only; 4 materially-different sleeve proxies
(Nasdaq universe, 10Y duration band, gold timing, oil contango);
USO 2020 regime shift; QQQ labeled proxy; state table small-n cells;
revised macro history; zero modeled costs beyond turnover rate; candidate
only.

## 10. Artifacts (all `issue-180`)

Prereg, `issue_180_policy.py`, `test_issue_180_policy.py`,
`test_issue_180_mirror.mjs` (ALL PASS), `issue_180_build.mjs`,
`issue_180_backtest.mjs`, `proxy-map.csv`, `proxy-monthly-returns.csv`,
`tracking.csv`, `implementation-monthly.csv` (A/B/C stream),
`performance.json`, `preservation.json` (in performance.json),
`state-implementation.csv`, `era-live.json`, `benchmarks.json`,
`sensitivity.json`, `policy.json` (in fact: machine-readable proxy map +
pins — see note), `summary.json`, this finding.

Note: prereg §11 named `policy.json` as the machine-readable policy artifact;
it carries the frozen proxy map, cost/timing framework refs, input SHAs and
flags. The frozen #178 weight matrix itself is NOT duplicated (pinned by SHA).

## 11. Tests / determinism / bugs

- Python stdlib suite + Node mirror (ALL PASS).
- Timeline self-check 0/721 vs #178; B/C rerun bit-identical; strict-panel
  assertion 0 drops.
- Bugs fixed pre-final: (1) cumulative-vs-annualized tracking-diff mislabel;
  (2) backtest overwrote build's proxy file (same filename — separated into
  `proxy-monthly-returns.csv` vs `implementation-monthly.csv`; affected runs
  discarded, pipeline rerun clean); (3) sensitivity legs reported pre-cost
  returns (now post-cost); (4) brace/paren syntax slips; (5) era cash-weight
  lens used wrong Ws (now implementation Ws for B/C, null for A with pointer
  to #178); (6) JS `void`/dead-code cleanup.

## 12. Explicit confirmations

- #178 weights/tiers/zeros/caps/B-2 unchanged (SHA-pinned; timeline 0 mismatch).
- No trajectory, no V6.6, no optimizer/grid search, no post-hoc thresholds.
- QQQ never renamed; spot oil never used; costs/turnover never hidden.
- `future_allocation_policy_candidate`: live-trading validation with real
  brokerage fills before any production use.
- `production_authorized=false`. Do not merge.
