# Issue #177 — 9-sleeve state allocation policy — Preregistration (frozen)

- Issue: [#177](https://github.com/eddy121384-ui/tradingview-indicators/issues/177)
- Branch: `research/issue-177-state-allocation-policy`
- Base (pre-prereg) HEAD: `5d596047e1da5531f43190bad761a79a8b3ac342` (Issue #176 final)
- This prereg is the FIRST Issue #177 commit on that branch.
- Status: PREREGISTRATION — frozen before the full 9-state policy matrix is generated.
- `outcome_data_loaded=false` (at prereg commit; no policy matrix exists)
- `production_authorized=false`
- `revised_macro_history=true`
- `real_time_vintage_claim=false`

## 0. Non-contamination attestation (ordering mandate)

The CURRENT GitHub Issue #177 body was read in full via webfetch (authoritative;
no cached copy). Before this commit, only the frozen #174/#176 input SCHEMAS
and evidence DEFINITIONS were inspected (file layouts, column names,
eligibility/evidence value sets, rule texts in prior preregs/findings).
No 0/Low/Neutral/High tier was assigned to any state × sleeve before this commit.

Sequence (mandatory):

1. read Issue #177;
2. inspect frozen input schemas/definitions only;
3. write this prereg;
4. commit it;
5. record the prereg commit SHA in the finding;
6. only then generate the full policy matrix.

Any later change to any frozen rule below requires a NEW issue.

## 1. Research lineage (frozen inputs — do not alter)

- #174 final `f1fdda3`: 9-sleeve outcome map. Key inputs reused verbatim:
  - `generated/issue-174/evidence-classification.csv`
    (state,sleeve,eligibility,n_months,n_episodes,mean_ex,pos_m_frac,ep_hit,
    p10_ex,worst_m,p_under,persistent_positive,persistent_negative,
    era_label,evidence,future_zero_weight_candidate,ex_worst_mean_ex)
  - `generated/issue-174/month-weighted-outcomes.csv` (adds mean, vol_ann,
    cash_ex sign/value fields)
  - `generated/issue-174/episode-weighted-outcomes.csv` (episode hit rates,
    worst/best episodes, concentration)
  - `generated/issue-174/era-stability.csv` (era_label per cell)
  - `generated/issue-174/downside-danger.csv` (worst_monthly, worst_episode,
    max_state_dd, p10, p10_ex, p_underperform, p_material_monthly,
    p_material_episode)
  - `generated/issue-174/future-zero-candidates.csv`
  - `generated/issue-174/panel-comparison.json` (full-panel window rule)
- #176 final `5d59604` (`allocation_backbone_hardened_with_limitations`):
  - `generated/issue-176/affected-state-sensitivity.csv`
    (sp500 hardened cells: n_old/n_new, mean/ex/vol/p10/hit old/new,
    ev_old/ev_new, zero_old/zero_new, conclusion — all 9 `unchanged`)
  - `generated/issue-176/oil-investable-state-cells.csv`
    (oil_investable_return cells: n,episodes,mean,meanEx,vol,p10,epHit,
    evidence,zero_candidate)
  - Sleeve verdicts: sp500 `hardened_with_limitation`, nasdaq
    `unresolved_keep_issue174_semantics`, russell
    `unresolved_keep_issue174_semantics`, oil `hardened_with_limitation`
    (dual series).
- Frozen macro: DH v0.1, ±10 bands, 9 states, frozen episodes/eras (all per
  #174; no trajectory, no V6.6 in this issue).

## 2. Frozen evidence-source hierarchy (per sleeve)

| sleeve | policy evidence source | parent |
|---|---|---|
| sp500 | #176 `affected-state-sensitivity` hardened columns (ev_new, ex_new, hit_new, p10_new, vol_new, zero_new); danger/tail inputs recomputed per §6 | #176 supersedes #174 |
| oil | #176 `oil-investable-state-cells` (investable supersedes spot for allocation); danger/tail inputs recomputed per §6 | #176 supersedes #174 |
| nasdaq | #174 evidence-classification + month/episode/era/danger rows | #174 (limitation explicit) |
| russell | #174 rows (see above) | #174 (limitation explicit) |
| cash | residual only (never classified) | #174 |
| treasury2y | #174 rows | #174 |
| treasury10y | #174 rows | #174 |
| longtreasury | #174 rows | #174 |
| gold | #174 rows | #174 |

#174 spot-oil cells are NOT policy inputs (investable supersedes for
allocation exposure). #174 broad-market sp500 cells are NOT policy inputs
(hardened reconstruction supersedes).

## 3. Frozen non-cash translation rules (verbatim from Issue #177)

For each state × non-cash sleeve, using the §2 source:

- `historically_favored` → `High`
- `historically_unfavorable` → `Low`, upgradeable to `0` ONLY via §4
- `mixed` → `Neutral` if mean Cash excess ≥ 0, else `Low`
- `insufficient_sample` → `Neutral` + `low_confidence=true`; NEVER High or 0

No manual exceptions. No discretionary promotion.

## 4. Frozen zero rule (verbatim; field mapping fixed here)

Exposure `0` ONLY IF (A) OR (B):

- (A) frozen flag true: #174 `future_zero_weight_candidate` for #174-sourced
  sleeves; #176 `zero_new` for sp500; #176 investable `zero_candidate` for oil.
- (B) ALL hold on current hardened evidence: evidence =
  `historically_unfavorable`; mean Cash excess < 0; episode excess hit rate
  ≤ 0.40; AND ≥1 severe tail condition (p10 monthly Cash excess ≤ -4pp;
  worst episode ≤ -15%; P(monthly excess < -2pp) ≥ 10%); AND ex-worst-episode
  mean Cash excess < 0.

Zero-reason recorded per 0-cell (`zero_rule_path=A/B`, triggering fields).

## 5. Frozen confidence mapping (direction vs confidence separated)

`limited` iff sleeve eligibility is `eligible_with_limitation` (nasdaq,
russell, oil per #174 machine column) OR #176 verdict is
`hardened_with_limitation`/`unresolved_keep_issue174_semantics`
(sp500, nasdaq, russell, oil). Otherwise `full`
(cash, treasury2y, treasury10y, longtreasury, gold).
Tiers are NEVER altered by confidence; limitations stay visible in every
cell + state card + confidence table. Insufficient-sample cells additionally
carry `low_confidence=true`.

## 6. Frozen danger/tail inputs (recomputation procedure, NOT new evidence)

The builder recomputes danger inputs for hardened sleeves (sp500 hardened,
oil investable) from frozen hardened returns + frozen macro with frozen #174
formulas (p10 excess, worst episode, p_material monthly/episode, ex-worst
mean). SELF-CHECK GATE (must pass before any tier is emitted): recomputing
the #174 danger/month/episode tables from frozen #174 returns must reproduce
them with 0 mismatches (same 0-mismatch bar as #176). #174 danger values are
used as-recorded for #174-sourced sleeves.

## 7. Frozen Cash rule + pre-matrix contradiction check

Points: High=+2, Neutral=+1, Low=0, 0=-1; sum over the 8 non-cash sleeves.
Bias: score ≤ 3 → high; 4–8 → neutral; ≥ 9 → low.
PRE-MATRIX CHECK (pure arithmetic, no data): attainable range is
[8×(-1), 8×(+2)] = [-8, 16]; thresholds (≤3 / 4–8 / ≥9) partition ALL integers
with no gaps/overlaps; all three bands are reachable (e.g. all-Low → 0 →
high; mixed → mid; all-High → 16 → low). NO contradiction → proceed.
Thresholds frozen; qualitative residual rule only (NOT percentages/optimizer).
Cash cells: `cash_role=residual`, no self-comparison, confidence `full`.

## 8. Frozen economic state descriptions (human labels, not data-derived)

- G_Low/I_Low: Deflationary bust — contracting activity with falling prices.
- G_Low/I_Neutral: Disinflationary slowdown — weak growth, stable prices.
- G_Low/I_High: Stagflationary slump — weak growth with high inflation.
- G_Neutral/I_Low: Healthy disinflation — steady growth, low inflation.
- G_Neutral/I_Neutral: Balanced expansion — steady growth, neutral inflation.
- G_Neutral/I_High: Late-cycle heat — steady growth with elevated inflation.
- G_High/I_Low: Productivity boom — strong growth, low inflation.
- G_High/I_Neutral: Broad boom — strong growth, neutral inflation.
- G_High/I_High: Overheating — strong growth with high inflation.

## 9. Frozen consistency checks (automatic; all must pass)

1. no unfavorable cell is High; 2. every 0 passes §4 audit; 3. insufficient
   cells never High/0; 4. Cash residual-only; 5. all 9 states × 9 sleeves
   present; 6. #176 S&P/oil evidence supersedes #174; 7. unchanged #174 inputs
   byte-identical to frozen files; 8. nasdaq/russell limitations explicit in
   every artifact; 9. no trajectory field read; 10. no V6.6 field read;
   11. matrix regeneration is bit-identical (determinism test).

## 10. Frozen common-sample sensitivity (descriptive only)

Recompute state×asset evidence over the full-common-sample window
(start 1987-10-01 per #174 panel rule; assert all 9 sleeves have month-ends
in-window modulo the disclosed long-treasury gap, else STOP) with frozen
formulas; self-check max-history reproduction (0 mismatches); derive implied
tiers with §§3–5; compare per cell vs primary; flag differences
`policy_sensitive=true`. NEVER alter the primary matrix for sensitivity
results. NEVER search thresholds to reduce changes.

## 11. Frozen deliverables (all paths contain `issue-177`)

- `research/issue-177-state-allocation-policy-prereg.md` (this file)
- `research/issue_177_policy.py` (frozen stdlib: tier/zero/cash/sensitivity primitives)
- `research/test_issue_177_policy.py` (+ executed Node mirror test)
- `research/issue_177_build.mjs` (deterministic matrix + cards + tables + summary)
- `research/generated/issue-177/policy-matrix.csv` (9×9 machine-readable)
- `research/generated/issue-177/state-cards.md`
- `research/generated/issue-177/cash-bias.csv`
- `research/generated/issue-177/zero-audit.csv`
- `research/generated/issue-177/confidence.csv`
- `research/generated/issue-177/sensitivity-common-sample.csv`
- `research/generated/issue-177/summary.json`
- `research/decisions/issue-177-state-allocation-policy-finding.md`

Builder MUST verify frozen file SHAs before reading, record them, never
overwrite other issues' artifacts, never touch Pine, never assign
percentages, never optimize.

## 12. Anti-tuning firewall

After this prereg commit and the first matrix inspection, do NOT change:
translation rules; zero rule; cash thresholds; confidence mapping; state
descriptions; evidence hierarchy; danger procedure; sensitivity procedure;
or any #174/#176 input. Surprises are REPORTED, never hand-fixed. Any change
requires a new issue. Forbidden: percentages, optimizers (any), leverage,
shorts, threshold/macro changes, trajectory, V6.6, asset add/drop, manual
cell edits, post-hoc rule changes, Pine changes, merging.

## 13. Product boundary

Research policy candidate only. Final verdict ∈
(`state_allocation_policy_candidate_complete`,
`state_allocation_policy_candidate_complete_with_limitations`,
`state_allocation_policy_not_ready`). Finding MUST contain
`production_authorized=false`. Do not merge.
