# Issue #176 — Allocation backbone hardening — Preregistration (frozen)

- Issue: [#176](https://github.com/eddy121384-ui/tradingview-indicators/issues/176)
- Branch: `research/issue-176-allocation-backbone-hardening`
- Base (pre-prereg) HEAD: `f1fdda31fc355ac857796fe10ca3b7bcd38964b8` (Issue #174 final)
- This prereg is the FIRST Issue #176 commit on that branch.
- Status: PREREGISTRATION — frozen before any Growth × Inflation-conditioned
  hardened return is computed or viewed.
- `outcome_data_loaded=false` (at prereg commit; no hardened macro × asset join exists)
- `production_authorized=false`
- `revised_macro_history=true`
- `real_time_vintage_claim=false`

## 0. Non-contamination attestation (ordering mandate)

This prereg is written from the CURRENT GitHub Issue #176 body plus the frozen
#174 lineage alone. The CURRENT Issue #176 body was read in full via webfetch
(no cached copy).

At the moment this file is committed:

- no hardened (or otherwise new) state-conditioned asset return has been computed;
- no hardened state × asset table, episode-conditioned, era-conditioned,
  tail-conditioned, or Cash-relative hardened return has been viewed;
- only UNCONDITIONAL source-feasibility probes were run (first/last
  observation, frequency, month-end availability, unconditional correlation /
  wedge / MAE vs modern overlap). Those probes never joined any return to
  Growth_DH / Inflation_DH and never cut by state, episode, or era;
- the frozen #174 macro series and #174 outcome tables were referenced only
  for coverage/rule reuse, not re-sorted by any new series.

Sequence (mandatory):

1. write this prereg;
2. commit it;
3. record the prereg commit SHA in the finding;
4. only then build hardened series + unconditional old-vs-new + QA;
5. only then rerun affected #174 cells.

Any later change to any frozen quantity below requires a NEW issue.

## 1. Research lineage (frozen inputs — do not alter)

### 1.1 Issue #174 final (parent study)

- Commit `f1fdda3` (branch `research/issue-174-nine-sleeve-macro-asset-map`).
- #174 backbone: `generated/issue-174/nine-sleeve-monthly-returns.csv`
  (sp500, nasdaq, russell, cash, treasury2y, treasury10y, longtreasury,
  gold, oil_price_proxy).
- #174 macro: `generated/issue-160/deep-history-v01-monthly.csv`
  (git-blob SHA256 `42516418…07dcfc`), Growth_DH / Inflation_DH.
- #174 frozen rules reused EXACTLY (no modification of any kind):
  ±10 state bands; 9 states; contiguous-calendar-month episodes (frozen holes
  2025-10/2025-11/2026-01 break episodes); eras E1 1966-03–1979-12,
  E2 1980-01–2007-12, E3 2008-01–2019-12, E4 2020-01–2026-08;
  Cash benchmark (TB3MS_{t-1}/1200); 10th-percentile tail metric (NOT ES);
  materiality monthly excess <-2.0pp / episode geometric excess <-5.0pp;
  evidence-classification rule (§9 of #174 prereg) and
  future-zero-weight-candidate rule (§10 of #174 prereg) VERBATIM,
  reimplemented line-for-line with a self-check that old cells reproduce
  #174 exactly before any new cell is interpreted.

### 1.2 Untouched sleeves

cash, treasury2y, treasury10y, longtreasury, gold are NOT investigated here.
Their #174 series, cells, labels, and flags are reused as-is (reproduction
self-check only). No new data for them. No re-validation of their QA.

## 2. Frozen source-feasibility summary (unconditional only)

Feasibility probes (transport + coverage + unconditional overlap) established,
without any macro join:

- S&P 500 TR: Yahoo `^SP500TR` genuine month-end TR from 1988-01 (466 pts);
  Yahoo `^GSPC` monthly endpoint truncated to 1985+ (cap ~502 pts) but
  Yahoo `^GSPC` DAILY reaches 1964+ (month-ends recoverable by yearly
  pagination); Shiller/datahub monthly P+D (1871+, ODC-PDDL-1.0) provides
  dividend levels; FRED SP500 useless deep (2016+). Shiller monthly-AVERAGE
  prices correlate only ~0.63 with month-end prices → REJECTED as return
  base (timing smoothing breaks month-end tail semantics).
- Nasdaq TR: official `^XCMP` / FRED `NASDAQXCMP` (Nasdaq Inc. via FRED)
  daily from 2003-09-25 (6009 rows) — genuine but short (loses E1+E2);
  no `^IXICTR` exists; QQQ is Nasdaq-100 (FORBIDDEN substitute); no free
  pre-2003 Nasdaq dividend history found → reconstruction would fabricate yields.
- Russell TR: Yahoo `^RUTTR` genuine from 1995-06-01 (377 pts); official
  history extends to Dec-1978 per FTSE Russell, but no free machine-readable
  pre-1995 TR source found; FRED has no Russell TR; IWM is 2000+ ETF
  (FORBIDDEN deep); French ME portfolios exist (academic small-cap, different
  universe — documented as REJECTED substitute).
- Oil investable: Yahoo `CL=F` front-month continuous closes from 2000-08
  (269 pts) + FRED TB3MS collateral gives deterministic excess+collateral TR;
  EIA futures endpoint returns heating-oil/spot families, no clean WTI crude
  futures monthly (product EPC0F empty); USO (2006+) available for QA.

## 3. Frozen final methodologies (all four sleeves)

Month label = first-of-month `YYYY-MM-01` for the calendar month whose return
accrued. Decimal returns. Month-end = last available daily bar in the calendar
month (daily sources) or the published monthly bar close (Yahoo monthly).

### 3.1 S&P 500 — hardened reconstruction `sp500_tr_hardened` (REPLACES #174 sp500)

```
r_price,t  = P^GSPC_t / P^GSPC_{t-1} - 1        (Yahoo ^GSPC DAILY month-end closes,
                                                 yearly paginated fetch)
div_accr,t = (D^Shiller_t / 12) / P^GSPC_{t-1}  (Shiller monthly Dividend level,
                                                 ODC-PDDL-1.0 via datahub mirror)
r_sp500_tr,t = r_price,t + div_accr,t
```

- Universe: S&P 500 (S&P Composite post-1957; pre-1957 90-stock history is
  outside our window). Dividends: Shiller cash-dividend levels, linearly
  interpolated intra-year by Shiller (disclosed smoothing of the LEVEL only;
  timing stays month-end via ^GSPC).
- First return: 1966-03-01 (needs 1966-02 ^GSPC close + Shiller D).
- Unconditional adoption gates (frozen): vs Yahoo `^SP500TR` month-end TR over
  maximal overlap: Pearson ≥ 0.99 AND MAE ≤ 0.20pp AND cumulative-ratio in
  [0.90, 1.10]. Probes show ~0.9999 / ~0.05pp (margin recorded, not tuned).
- On pass: verdict `hardened_with_limitation` (reconstruction, not official;
  interpolated dividend levels; small long-run drift disclosed).
  On fail: `unresolved_keep_issue174_semantics`.
- The #174 French-market series is RETAINED in the repo but RENAMED in all
  #176 outputs as `broad_market_tr_french` (never again labeled S&P 500).

### 3.2 Nasdaq — `unresolved_keep_issue174_semantics` (KEEP #174 nasdaq price)

- #174 series (FRED NASDAQCOM month-end price return, 1971-03+) is RETAINED
  UNCHANGED as the Nasdaq sleeve.
- Official TR (`^XCMP` / FRED `NASDAQXCMP`, 2003-09-25+) starts after E1+E2
  (fails the frozen adoption rule §4: official TR must start ≤1990-01 to
  replace a full-history series). It is FETCHED and reported as QA/wedge
  evidence only (TR-minus-price wedge ≈ +0.96%/yr), never stitched.
- No dividend reconstruction (no defensible pre-2003 dividend history; a
  constant-yield backcast would fabricate). No QQQ / Nasdaq-100 substitution.
- Verdict: `unresolved_keep_issue174_semantics` with quantified wedge.

### 3.3 Russell — `unresolved_keep_issue174_semantics` (KEEP #174 russell price)

- #174 series (Yahoo ^RUT month-end price return, 1987-10+) is RETAINED
  UNCHANGED as the Russell sleeve.
- Official TR (`^RUTTR`, 1995-06+) fails the frozen adoption rule §4
  (starts >1990-01; adopting it would erase 1987-1995 including the 1987 crash
  and create all-insufficient_sample E1/E2 cells). It is FETCHED and reported
  as QA/wedge evidence only (TR-minus-price wedge ≈ +1.34%/yr), never stitched.
- No IWM substitution, no constituent backfill, no French small-cap proxy
  substitution (French ME documented as REJECTED candidate: different universe).
- Verdict: `unresolved_keep_issue174_semantics` with quantified wedge.

### 3.4 Oil — ADD `oil_investable_return`, KEEP `oil_price_proxy` (DUAL, never stitched)

```
excess_t     = F^CL_t / F^CL_{t-1} - 1   (Yahoo CL=F continuous front-month
                                           month-end closes; exchange roll
                                           calendar; exact roll day OPAQUE —
                                           disclosed limitation)
collateral_t = TB3MS_{t-1} / 1200          (same frozen Cash accrual)
r_oil_inv,t  = (1 + excess_t) * (1 + collateral_t) - 1
```

- Contract: WTI crude front-month (CME/NYMEX via Yahoo continuous).
  Roll timing/frequency: Yahoo continuous methodology (opaque); roll-yield is
  EMBEDDED in the continuous price change (excess return); fees: none assumed
  (disclosed; real funds subtract fees).
- First return: 2000-09-01 (CL=F monthly from 2000-08; needs prev).
- KEEP #174 `oil_price_proxy` (FRED MCOILWTICO spot, 1986-02+) UNCHANGED as a
  separate series. The two are NEVER stitched; state cells are computed for
  EACH independently; investable cells start 2000-09 (E3+E4 + late E2 only).
- QA gate (frozen): vs USO adjclose TR over maximal overlap: Pearson ≥ 0.80
  (spot-vs-fund + roll drag disclosed). Probes show ~0.93.
- Verdict: `hardened_with_limitation` (short history + opaque roll day +
  no-fee assumption).

## 4. Frozen adoption / verdict rules (unconditional only)

- Official TR replaces a full-history #174 series ONLY IF its first monthly
  return is ≤1990-01-01 (covers ≥~80% of the 1966-03 window and reaches E2).
- Reconstruction is adopted ONLY IF its modern-overlap QA passes the frozen
  gates in §3 (Pearson/MAE/cumulative bands stated there).
- Selection depends ONLY on semantics, source quality, coverage, validation.
  NEVER on state-conditioned performance (unseen at prereg).
- Per-sleeve verdicts ∈ {`hardened_primary`, `hardened_with_limitation`,
  `unresolved_keep_issue174_semantics`}. Expected (to be confirmed by frozen
  gates post-prereg): sp500 hardened_with_limitation, nasdaq unresolved,
  russell unresolved, oil hardened_with_limitation (dual).
- Overall ∈ {`allocation_backbone_hardened`,
  `allocation_backbone_hardened_with_limitations`,
  `allocation_backbone_not_ready`}.

## 5. Frozen unconditional comparison + QA (post-prereg, pre-rerun)

For each hardened/new series vs its #174 counterpart over maximal overlap
(and vs modern ETF/index overlap), report UNCONDITIONALLY:

- coverage diff (first/last/n, gap count);
- Pearson correlation of monthly returns;
- mean-return difference (pp/mo and annualized);
- volatility difference (annualized biased-sd);
- worst large-disagreement months (|new − old| sorted top-10 with dates);
- cumulative-ratio (prod(1+r_new)/prod(1+r_old));
- modern QA table (gates as in §3).

No state, episode, era, tail, or Cash-relative cut appears in these artifacts.

## 6. Frozen conditional rerun (post-prereg only; affected cells ONLY)

Rerun with the EXACT #174 frozen stack (§1.1): same macro file, same ±10
bands, same episodes, same eras, same Cash, same p10, same materiality,
same classification and zero-candidate code (self-check: old cells reproduce
#174 bit-for-bit before new cells are read).

- sp500: recompute all 9 state cells with `sp500_tr_hardened`; report
  old/new: state mean, Cash excess, vol, p10, episode hit-rate, evidence
  label, zero flag.
- oil_investable_return: compute all 9 state cells as NEW (no old counterpart;
  spot cells reproduced for reference, not altered).
- nasdaq, russell: NO recomputation (series unchanged); reproduction
  self-check only.
- Untouched sleeves: reproduction self-check only.
- Classify each affected conclusion as unchanged / weakened / strengthened /
  reversed (definitions: label or zero-flag change = reversed if favored↔
  unfavorable, else strengthened/weakened by excess-sign or hit-rate band
  crossing with same label; else unchanged). No rule is tuned after seeing
  differences.

## 7. Frozen deliverables (all paths contain `issue-176`)

- `research/issue-176-allocation-backbone-prereg.md` (this file)
- `research/issue_176_backbone.py` (frozen stdlib: recon/excess/collateral/
  wedge/comparison primitives)
- `research/test_issue_176_backbone.py` (+ executed Node mirror test)
- `research/issue_176_build.mjs` (fetch + hardened build + provenance +
  source audit + unconditional old-vs-new + QA; NO macro join)
- `research/issue_176_rerun.mjs` (frozen-rule conditional rerun + sensitivity +
  classification-change tables + summary)
- `research/generated/issue-176/source-candidate-audit.csv`
- `research/generated/issue-176/provenance.json`
- `research/generated/issue-176/hardened-monthly-returns.csv`
- `research/generated/issue-176/qa-comparison.json`
- `research/generated/issue-176/old-vs-new-unconditional.csv`
- `research/generated/issue-176/affected-state-sensitivity.csv`
- `research/generated/issue-176/changed-classification.csv`
- `research/generated/issue-176/summary.json`
- `research/decisions/issue-176-allocation-backbone-finding.md`

Evaluator MUST verify the #174 backbone + macro blob SHAs before any join,
record every source URL/bytes/SHA256, never overwrite other issues'
artifacts, never change Pine, never optimize weights.

## 8. Anti-tuning firewall

After this prereg commit and the first hardened conditional inspection, do NOT
change: Deep-History construction; ±10 thresholds; state labels; episode
definitions; era boundaries; tail metric; materiality; evidence or
zero-candidate rules; sleeve methodologies (§3); adoption gates (§4);
panel or coverage rules. Any such change requires a new issue. Forbidden:
weight optimization (any form); new allocation rules; QQQ/IWM/USO as deep
history; calling Nasdaq-100 "Composite"; calling CRSP market "S&P 500";
calling spot investable; silent stitching; deleting periods; retrospective
#174 edits; Pine changes; merging.

## 9. Product boundary

Research only. No allocation percentages. No new allocation rule (ideas only
as `future_allocation_policy_candidate`, untested). Final finding MUST contain
`production_authorized=false`. Do not merge.
