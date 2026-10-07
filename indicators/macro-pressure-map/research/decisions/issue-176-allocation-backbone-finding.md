# Issue #176 — Allocation backbone hardening — Finding

- Issue: [#176](https://github.com/eddy121384-ui/tradingview-indicators/issues/176)
- Branch: `research/issue-176-allocation-backbone-hardening`
- Base (pre-issue) HEAD: `f1fdda31fc355ac857796fe10ca3b7bcd38964b8` (Issue #174 final)
- Prereg commit (FIRST on branch, BEFORE any conditioned hardened result):
  `7a48b62ade201127b5ce1ae27633730dfcb30fba`
- Overall verdict: `allocation_backbone_hardened_with_limitations`
- `outcome_data_loaded=true` (post-prereg rerun only)
- `production_authorized=false`
- `revised_macro_history=true`, `real_time_vintage_claim=false`
- Research only. No weights optimized. No Pine changed. Do not merge.

## 1. Bottom line

Two sleeves hardened, two honestly declared unresolvable with free data:

| sleeve | verdict | series |
|---|---|---|
| sp500 | `hardened_with_limitation` | `sp500_tr_hardened` = Yahoo ^GSPC daily month-end price + Shiller dividend accrual, 1966-03–2023-06 (688 mo); gate 0.9999/0.048pp PASS |
| nasdaq | `unresolved_keep_issue174_semantics` | #174 FRED price retained; official TR only 2003+ (fails ≤1990 rule); wedge +0.96%/yr documented |
| russell | `unresolved_keep_issue174_semantics` | #174 ^RUT price retained; official TR only 1995+ (fails ≤1990 rule); wedge +1.34%/yr documented |
| oil | `hardened_with_limitation` | NEW `oil_investable_return` = CL=F excess + TB3MS collateral, 2000-09–2026-08 (312 mo); spot proxy KEPT separately; USO gate 0.923 PASS |

Conditional rerun (frozen #174 rules, self-check 0 mismatches): **all 9 S&P
state conclusions unchanged** (labels + zero flags identical); oil
investable cells are new evidence (1 unfavorable, 5 mixed, 3 insufficient;
0 zero candidates). No #174 conclusion reversed.

## 2. Frozen macro/rules (unchanged — self-check proves it)

DH v0.1 blob `42516418…07dcfc`; ±10 bands; 362 episodes; frozen eras;
Cash TB3MS/1200; p10 tail; -2pp/-5pp materiality; #174 §9/§10 code verbatim.
Self-check recomputed 36 old cells (sp500/oil/nasdaq/russell × 9 states):
0 mean mismatches >1e-12, 0 label mismatches.

## 3. Source audit (per-sleeve semantics; full table `source-candidate-audit.csv`)

- S&P SELECTED: ^GSPC daily month-ends (61 yearly windows, 15,291 daily pts)
  + Shiller D/12 accrual. REJECTED: Shiller avg-price base (0.63 corr vs
  month-end — timing smoothing), FRED SP500 (2016+ only), ^SP500TR as backbone
  (1988+, QA benchmark instead). French market TR SUPERSEDED for the S&P
  sleeve (retained in repo, renamed `broad_market_tr_french` in #176 outputs).
- Nasdaq RETAINED price; REJECTED: QQQ/Nasdaq-100 (wrong index), ^XCMP
  stitching (starts 2003-09-25, would erase E1+E2).
- Russell RETAINED price; REJECTED: IWM (ETF deep-history), constituent
  backfill, French ME proxy (different universe), ^RUTTR stitching (1995+).
- Oil DUAL: spot retained + investable added; REJECTED: silent stitching,
  USO-as-history (2006+ ETF, QA only), EIA futures (no clean WTI series).

## 4. Provenance / hashes (`provenance.json`)

Every fetch recorded with URL/bytes/SHA256: ^GSPC daily chained hash,
Shiller mirror SHA, Yahoo monthly SHAs (^SP500TR/^RUT/^RUTTR/CL=F/USO),
FRED SHAs (NASDAQCOM/NASDAQXCMP/TB3MS), Damodaran SHA, French ME zip SHA +
member list. Frozen #174 backbone SHA + macro blob SHA recorded.

## 5. Modern QA (`qa-comparison.json`)

- S&P recon vs ^SP500TR (n=425): pear 0.9999, MAE 0.048pp, cum ratio 0.977,
  vol diff -0.004pp → gate PASS → hardened_with_limitation.
- Oil investable vs USO (n=244): pear 0.923 → gate PASS.
- Nasdaq wedge 2003+: +0.080pp/mo (~0.96%/yr, n=277). Russell wedge 1995+:
  +0.112pp/mo (~1.34%/yr, n=376). Small vs monthly vol; documented drag of
  price-only series.

## 6. Old-vs-new unconditional (`old-vs-new-unconditional.csv`)

- sp500 (n=688 overlap): pear 0.989, mean diff -0.018pp/mo (new slightly
  lower), vol diff -0.54pp ann, cum ratio 0.93, MAE 0.50pp. Largest
  disagreements: 2000-02 (-4.8pp), 2000-03 (+4.1pp) — dot-com months where
  CRSP breadth and S&P500 diverged; disclosed, not tuned.
- oil spot vs investable (n=312): pear 0.759, MAE 5.61pp — different
  economics (monthly-avg spot vs month-end futures+collateral) + curve effects;
  textbook case 2020-04: spot -43.3% (avg incl. negative print) vs
  investable -8.0% (rolled before expiry). Never stitched.

## 7. Sensitivity rerun (`affected-state-sensitivity.csv`)

S&P new coverage 1966-03–2023-06 (688 mo; 38 recent months truncated by the
datahub dividend defect — disclosed §9). All 9 states: evidence labels
identical (Low-High unfavorable, Neutral-Low + High-Neutral favored, rest
mixed), zero flags identical (all false), means within 0.2pp, vols within
0.6pp, hit-rates within 0.05. Conclusions: 9/9 `unchanged`.
`changed-classification.csv` is empty (header only) — no label or flag moved.

Oil investable (`oil-investable-state-cells.csv`): Low-Low unfavorable
(n=34, epHit 0.20, zero=false on n<60); Neutral-Low/Neutral-Neutral/
Neutral-High/High-Neutral/High-High mixed; Low-Neutral/Low-High/High-Low
insufficient_sample (n=19/21/10). Zero candidates: 0/9 (all false).

## 8. Limitations / unresolved

- S&P recon ends 2023-06 (datahub Shiller dividends zeroed from 2023-07;
  upstream Yale ie_data.xls verified fetchable but BIFF parsing is deferred
  to a follow-up issue — NOT done here per firewall).
- S&P dividend levels are Shiller-interpolated; 2.3% long-run level drift
  (cum 0.977) disclosed.
- Nasdaq/Russell remain price-only (wedges ~1%/yr understatement).
- Oil investable starts 2000-09 (loses E1/E2; 3 insufficient_sample states),
  Yahoo roll day opaque, no fees, month-end vs monthly-avg timing vs spot.
- CL=F monthly-bar holes (e.g. 2020-03) filled via daily month-ends (same
  frozen series definition; disclosed refinement).
- No weight optimization, no allocation rule, no Pine change.

## 9. Artifacts

- `research/issue-176-allocation-backbone-prereg.md` (prereg `7a48b62`)
- `research/issue_176_backbone.py` + `research/test_issue_176_backbone.py`
- `research/test_issue_176_mirror.mjs` (executed: ALL PASS)
- `research/issue_176_build.mjs` (fetch/build/QA; NO macro join)
- `research/issue_176_rerun.mjs` (frozen-rule rerun)
- `research/generated/issue-176/source-candidate-audit.csv`
- `research/generated/issue-176/provenance.json`
- `research/generated/issue-176/hardened-monthly-returns.csv`
- `research/generated/issue-176/qa-comparison.json`
- `research/generated/issue-176/old-vs-new-unconditional.csv`
- `research/generated/issue-176/affected-state-sensitivity.csv`
- `research/generated/issue-176/changed-classification.csv`
- `research/generated/issue-176/oil-investable-state-cells.csv`
- `research/generated/issue-176/summary.json`
- This finding.

## 10. Tests / bugs fixed

- Python stdlib suite (builders + metrics); Node mirror executed ALL PASS.
- Build/ rerun determinism: gates PASS identically across reruns.
- Bugs fixed pre-final: (1) CRLF `oil\r` header key zeroing oil overlap
  (header-trim fix); (2) 1966-03 edge missing prev month (1966-02 build
  window, as in #174); (3) CL=F monthly-bar holes incl. 2020-03 (daily
  month-end merge, same frozen series); (4) Yahoo monthly cap ~502 pts
  (yearly daily pagination for ^GSPC); (5) rerun oil zero flags added
  (full VERBATIM incl. ex-worst).

## 11. Explicit confirmations

- S&P 500 no longer mislabeled broad-market TR (renamed + replaced).
- Nasdaq ≠ Nasdaq-100/QQQ; Russell ≠ IWM/constituents; spot ≠ investable.
- No ETF as deep-history primary. No silent stitching. No dropped periods.
- Macro/state/episode/era/tail/materiality/evidence/zero rules unchanged.
- #174 findings NOT retrospectively modified.
- `future_allocation_policy_candidate`: (a) Yale-xls dividend extension for
  S&P recon 2024+; (b) allocation-weight research may now use hardened S&P +
  dual oil series (untested here).
- `production_authorized=false`. Do not merge.
