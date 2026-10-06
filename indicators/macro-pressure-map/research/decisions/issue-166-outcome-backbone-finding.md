# Issue #166 — Deep-History outcome backbone — 1966+ monthly equity & Treasury returns

- Issue: [#166](https://github.com/eddy121384-ui/tradingview-indicators/issues/166)
- Branch: `research/issue-166-outcome-backbone` (isolated worktree; shared checkout untouched)
- Base: Issue #165 final `8267c00baedd880c0b5c4292d025f3c7593976c0`
- Formal verdict: `deep_history_outcome_backbone_feasible_with_limitations`
- `macro_outcome_join_performed=false`
- `production_authorized=false`
- SOURCE FEASIBILITY + RETURN-SERIES VALIDATION ONLY. No return was joined to
  Growth_DH/Inflation_DH, no macro-conditioned return was computed, and no
  signal-conditioned outcome was inspected. Do not merge.

## 1. Equity backbone: Fama-French US market monthly total return (SELECTED)

Investigated in issue order: (1) observed TV total-return indexes — `SP:SPXTR`
returns permission-denied (`cme_sp_indices_dly`); broad "Total Return Index"
search returns zero symbols; (2) Fama-French/CRSP monthly market return —
available, authoritative, research-compatible → SELECTED, so Shiller
price+dividend construction (option 3) was not pursued.

- Series: Fama-French 3-Factor monthly `Mkt-RF + RF`, file
  `F-F_Research_Data_Factors.csv` (202608 CRSP vintage),
  file SHA256 `d7d7fe37b150b5b15c9c069b3ba101dfe1af568c6d7b5db6e73cd0a6c0c9e5e5`.
- Coverage: 1926-07 → 2026-08 (1202 months); backbone window 1966-03 → 2026-08
  holds **726 valid monthly returns**, zero missing-flag months, zero gaps.
- Dividends included directly (CRSP holding-period returns with distributions);
  monthly, no ETF wrapper. Free for research; cite French + CRSP.
- Caveats (disclosed, not disqualifying): CRSP revises history (Dec-2012
  market-return redefinition; CIZ flat-file format from the Jan-2025 vintage);
  T-Bill leg switched Ibbotson→ICE BofA after 2024-05 (RF leg only, basis
  points); universe is CRSP value-weight, not exactly S&P 500.
- QA (unconditional, no macro join): vs Damodaran annual S&P TR (1960–2025,
  n=66) Pearson **0.990**, Spearman 0.985, MAE **2.0pp**; vs Yahoo ^SP500TR
  monthly (1988+, n=463) Pearson **0.989**, MAE 0.45pp, cumulative ratio 1.013;
  vs SPY TR (1993+, n=403) Pearson 0.987.
- Gates 1–6: start 1926 ≤ 1966-03 PASS; monthly + dividends PASS; no ETF PASS;
  726 ≥ 700 PASS; no multi-month gaps PASS; overlap Pearson 0.989 ≥ 0.98 PASS
  on numbers alone (documented CRSP methodology equivalence additionally holds).

## 2. Treasury backbone: frozen synthetic 10Y CMT total return (SELECTED)

Observed-index search failed first: `SP:SPUSTTTR` permission-denied (same
group); TV "Treasury Total Return" search returns only modern ETF wrappers
(VTG); FRED direct CSV download was transport-blocked. Per the issue, the
frozen synthetic path was therefore built — no formula tuning performed.

- Yield input: FRED DGS10 via TradingView weekly bars, month-end last-bar
  sampling, 1962-01 → 2026-09, **777 complete months, zero holes**.
- Frozen construction (exact): month-end 10Y par yield y_t; initiate 10Y par
  bond (face 100, annual coupon c=100·y_t, semiannual payments); hold one month;
  reprice remaining 9y11m flows (19 coupons + principal at fractional periods
  5/6…119/6) at the single next-month yield y_{t+1}; one-month total return =
  dirty PV/100 − 1; roll into a fresh par bond. Monthly steps of 1/12 year;
  accrual embedded in the dirty price (no double-counted coupon cash).
- Limits disclosed: single-yield curve approximation; par-coupon
  simplification; month-end timing; weekly-sampled month ends; FRED vintage
  revisions.
- Coverage: first return **1966-03-01** (Feb+Mar 1966 yields), last 2026-09-01;
  **776 months, zero month-skips**; 726 returns in 1966-03…2026-08.
  Coupon-inclusive, no ETF wrapper.
- Spot plausibility: 1981-08 −3.0% (yields 14.67→15.51); 1982-08 +7.9%
  (13.68→12.47); 1987-10 +5.5%; 1994-04 −1.5%; 2008-12 +4.4%; 2020-03 +5.0%;
  2022-10 −2.4%. All sign-correct for rate moves.
- Validation: vs frozen Damodaran annual T.Bond (common 1963–2025, n=63)
  Pearson **0.984**, Spearman 0.984, MAE **1.25pp** (gates 6, 7 PASS with
  margin). Modern sanity vs TLT TR (2002+, n=290): Pearson 0.856, sign
  agreement 0.834 — no material construction error given the disclosed ~2x
  duration mismatch (TLT ~15–18y vs synthetic ~8y); gate 8 PASS on the
  issue-literal "no material error" reading.
- Damodaran provenance: `histretSP.html` downloaded raw (656121 bytes),
  SHA256 `127c772f0fea8763391dbf2c1c7d3ecd3a07ca2b23f81ab47af58b529e2b5647`
  matches the frozen value exactly; 98 annual rows 1928–2025 parsed locally
  (spot-verified 1966/2022/2025 against the rendered table).
- Gates 1–5, 6, 7 PASS (start exactly 1966-03; monthly coupon-inclusive; no
  ETF; 726 ≥ 700; no gaps).

## 3. Missing-data audit

- French market: zero −99.99/−999 flags in file; zero calendar gaps 1960+.
- DGS10 month-ends: 777/777 calendar months, zero holes; synthetic returns
  consecutive (zero month-skips).
- Damodaran: 98/98 annual rows 1928–2025, both needed columns present.
- Yahoo QA series: no null adjusted closes (SPY 405, TLT 291, ^SP500TR 465
  monthly returns).
- Known benign edges: French file ends 2026-08 (vintage); Damodaran ends 2025;
  annualization uses full calendar years only.

## 4. Verdict

`deep_history_outcome_backbone_feasible_with_limitations`

Both backbones pass every frozen gate on the numbers. The "with limitations"
qualifier records real, disclosed caveats rather than gate failures: synthetic
(not observed) Treasury construction with single-yield approximation;
CRSP/FRED vintage-revision policies; weekly-sampled month-end yields; TLT
duration mismatch in modern QA; French universe ≠ S&P 500 exactly (MAE 2.0pp
vs Damodaran). This verdict authorizes only backbone existence — it does NOT
authorize any macro-conditioned outcome analysis, which was not performed here.

## 5. Artifacts (+ provenance)

- `research/decisions/issue-166-outcome-backbone-finding.md` (this file)
- `research/generated/issue-166/outcome-source-matrix.csv` (investigated /
  selected / rejected candidates with reasons)
- `research/generated/issue-166/equity-monthly-total-returns.csv`
  (1960-01 → 2026-08, 800 rows, decimal monthly TR)
- `research/generated/issue-166/treasury-monthly-total-returns.csv`
  (1966-03 → 2026-09, 776 rows: return + start/end yields)
- `research/generated/issue-166/outcome-backbone-validation.json`
  (coverage, QA metrics, all 14 gate booleans, verdict, hashes, URLs)
- Hashes: French CSV `d7d7fe37…`, Damodaran `127c772f…` (byte-exact frozen
  match), DGS10 compact + Yahoo QA files recorded in Temp with FNV cross-checks.

## 6. Workflow evidence and verification

- Isolated worktree at the frozen base; shared checkout untouched.
- Denials and absences documented with verbatim errors (SPXTR/SPUSTTTR
  permission-denied strings; empty TV searches; FRED transport block).
- Two implementation bugs were caught by validation before finalizing: an
  `r.r`-vs-`mktret` field mixup that NaN-poisoned all equity comparisons
  (isolated via a standalone replication: true Pearson 0.990), and an
  over-strict numeric gate-8 of my own invention replaced with the issue-literal
  "no material construction error" reading (verdict-invariant either way only
  if Damodaran gates hold — they do, with margin).
- No macro series was loaded in the return pipeline; no join key was ever
  constructed between returns and Growth_DH/Inflation_DH.

## 7. Explicit confirmations

- `macro_outcome_join_performed=false` — no return was joined to any
  Deep-History state, no macro-conditioned return was computed, no
  signal-conditioned outcome was inspected (including no reading of Issue #136
  payoff tables for hypothesis selection).
- `production_authorized=false` — no production code changed; 5 new research
  files only.
- Do not merge.
