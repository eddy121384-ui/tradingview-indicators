# Issue #178 — 9-sleeve state weight policy — Finding

- Issue: [#178](https://github.com/eddy121384-ui/tradingview-indicators/issues/178)
- Branch: `research/issue-178-state-weight-policy`
- Base (pre-issue) HEAD: `bc652bd615f2c5e9137050d01c666dbcd9528cd3` (#177 final)
- Prereg commit (FIRST, BEFORE any weight or backtest):
  `844dd71fa3ea5b9a975b5a0972d10396bc19e5ea`
- Formal verdict: `state_weight_policy_candidate_complete_with_limitations`
- `production_authorized=false`
- Research only. No optimizer ran. No Pine changed. Do not merge.

## 1. Bottom line

The frozen #177 qualitative tiers translate into a sensible deterministic
long-only portfolio: max-history CAGR **8.85%** at **7.21%** vol
(Cash excess **+4.08%/yr**, Sharpe-like **0.59**, MaxDD **-17.4%**) vs static
neutral **8.33% / 8.13% / +3.58% / 0.47 / -24.0%**. The policy earns its keep
through risk reduction (lower vol, shallower drawdown, smaller worst month
-7.9% vs -11.4%), not return maximization. It trails 100% equity
(10.72% CAGR, 15.7% vol, -50.3% MaxDD) with less than half the volatility.
No parameter was tuned: the first frozen design is the reported design.

## 2. Frozen policy (verbatim prereg §§1–8)

- Neutral baseline: S&P 25 / Nasdaq 12 / Russell 8 / 2Y 8 / 10Y 14 / Long 8 /
  Gold 6 / Oil 4 / Cash 15 (families 45/30/10/15).
- Multipliers: 0× / 0.5× / 1.0× / 1.75×.
- Sleeve caps: 35/20/15/15/25/15/12/8; family caps 60/50/15; Cash min 2,
  max 60; bias minimums low 5 / neutral 10 / high 20.
- Normalization: raw → sleeve caps → family caps → residual Cash with
  bias-min/max clamp (pro-rata) → re-cap shave → 2dp largest-remainder
  (tier-0 excluded) = exactly 100.00%.
- Rebalance primary B-2 confirmation (alternate S3 immediate); no lookahead
  (month-m uses states through m−1); start 1966-05; zero costs.
- Missing data: sleeve excluded when return missing (S&P French fallback
  2023-07–2026-08, 35 flagged months; oil pre-2000-09 excluded; nasdaq/russell/
  2Y/long-gap per genuine coverage). Panels: max-history (1966-05+, n=721) +
  full-universe (2000-09–2023-06, 0 drops, n=274).
- Benchmarks: static neutral (monthly rebalance), Cash 100%, French equity
  100%, 60/40 French/10Y. Sensitivity: S1 alt baseline, S2 alt multipliers
  (0.25×/2×), S3 immediate — no promotion of best case.

## 3. 9-state percentage matrix (rounded 2dp, rows = 100.00%)

| state | S&P | Nas | Rus | 2Y | 10Y | Long | Gold | Oil | Cash | binds | bias |
|---|---|---|---|---|---|---|---|---|---|---|---|
| Low-Low | 23.52 | 11.29 | 7.52 | 12.54 | 21.95 | 12.54 | 5.64 | 0 | 5.00 | family:rates | low |
| Low-Neutral | 25.00 | 12.00 | 8.00 | 8.00 | 14.00 | 8.00 | 3.00 | 4.00 | 18.00 | — | neutral |
| Low-High | 12.50 | 6.00 | 4.00 | 8.00 | 7.00 | 4.00 | 6.00 | 4.00 | 48.50 | — | high |
| Neutral-Low | 31.08 | 10.65 | 7.10 | 12.43 | 12.43 | 12.43 | 5.33 | 3.55 | 5.00 | sleeve:sp500 | low |
| Neutral-Neutral | 25.00 | 12.00 | 8.00 | 8.00 | 14.00 | 8.00 | 3.00 | 4.00 | 18.00 | — | neutral |
| Neutral-High | 25.00 | 12.00 | 0 | 4.00 | 7.00 | 4.00 | 6.00 | 4.00 | 38.00 | — | high |
| High-Low | 25.00 | 12.00 | 4.00 | 8.00 | 14.00 | 14.00 | 0 | 4.00 | 19.00 | — | neutral |
| High-Neutral | 30.44 | 17.39 | 12.17 | 4.00 | 7.00 | 4.00 | 6.00 | 4.00 | 15.00 | sleeve:sp500;sleeve:nasdaq;family:equity | neutral |
| High-High | 25.00 | 12.00 | 8.00 | 4.00 | 7.00 | 4.00 | 6.00 | 4.00 | 30.00 | — | neutral |

Zero cells intact (Low-Low Oil, Neutral-High Russell, High-Low Gold = 0%).
Caps bind in 3 states (reported, deterministic). Ordering respected
everywhere caps don't bind.

## 4. Performance (primary, B-2)

Max-history (n=721): CAGR 8.85%, vol 7.21%, Cash excess +4.08%/yr,
Sharpe-like 0.59, MaxDD -17.4%, worst -7.86%, pos 66.2%, avg Cash 27.3%
(avg families: equity 41.6 / rates 25.3 / real assets 6.6).
Full-universe (n=274): CAGR 5.99%, vol 7.31%, excess +4.44%/yr,
Sharpe-like 0.63, MaxDD -17.4%.
Benchmarks (max): neutral 8.33%/8.13%/-24.0%; cash 4.58%; equity100
10.72%/15.70%/-50.3%; 60/40 9.15%/10.13%/-30.4%.
Strongest states (max panel CAGR): Low-Low 14.8%, Neutral-Low 11.6%,
High-Low 11.1%. Weakest: Neutral-High 3.6%, Low-High 5.2% (high-Cash
stagflation postures did their defensive job, not a failure).
Eras (policy vs neutral CAGR): E1 7.45 vs 6.27; E2 10.16 vs 10.18;
E3 7.15 vs 6.15; E4 9.36 vs 8.89 — ahead or tied in all four eras.

## 5. Turnover

B-2: 35.0%/yr, 106 allocation switches from 358 raw state changes
(~70% of 1-month flickers filtered), avg 6.8 months between changes,
avg 19.9pp one-way per rebalance. Immediate (S3): 108.1%/yr, 340 switches —
the guard earns its place; reported, primary unchanged.

## 6. Sensitivity (stability, not selection)

Max-history CAGR: primary 8.85 / S1 9.07 / S2 8.90 / S3 9.15; vols 7.2–8.2.
Full-universe: 5.99 / 6.16 / 5.98 / 6.49. Conclusions stable across baseline,
multiplier, and rebalance perturbations; primary retained regardless.

## 7. Limitations

Nasdaq/Russell price-only; S&P recon ends 2023-06 (+French fallback flagged);
oil investable from 2000-09; long gap handled by exclusion; revised (not
vintage) macro; zero costs; no transaction friction modeled; policy candidate
only — NOT production.

## 8. Artifacts (all `issue-178`)

Prereg, `issue_178_policy.py`, `test_issue_178_policy.py`,
`test_issue_178_mirror.mjs` (ALL PASS), `issue_178_build.mjs`,
`issue_178_backtest.mjs`, `weight-matrix.csv`, `state-cards.md`,
`backtest-monthly.csv`, `performance.json`, `benchmarks.json`,
`turnover.json`, `era-report.json`, `sensitivity.json`, `policy.json`,
`summary.json`, this finding.

## 9. Tests / determinism / bugs

- Python stdlib suite + Node mirror (9 assertions) ALL PASS.
- Matrix rebuild bit-identical; backtest rerun bit-identical.
- Audit: 9 states × 9 sleeves, all rows 100.00%, zeros intact, caps/cash
  bounds pass, no negatives, no leverage.
- Bugs fixed pre-final: (1) JS `in`-on-Set membership (weights collapsed —
  caught by audit); (2) cumulative-vs-annualized Cash-excess mislabel;
  (3) return loop required returns for zero-weight sleeves (collapsed panel
  to n=309 — caught by n-count check); (4) mirror-test remainder expectation.

## 10. Explicit confirmations

- #177 tiers/zeros/cash-bias unmodified (SHA-pinned, tier-drift audit clean).
- No trajectory, no V6.6, no optimizer/grid search, no percentages-to-tiers
  reverse-fitting, no hidden overrides.
- `future_allocation_policy_candidate`: cost-aware + vintage-data validation
  before any production use.
- `production_authorized=false`. Do not merge.
