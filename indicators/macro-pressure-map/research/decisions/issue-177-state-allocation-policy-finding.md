# Issue #177 — 9-sleeve state allocation policy (0 / Low / Neutral / High) — Finding

- Issue: [#177](https://github.com/eddy121384-ui/tradingview-indicators/issues/177)
- Branch: `research/issue-177-state-allocation-policy`
- Base (pre-issue) HEAD: `5d596047e1da5531f43190bad761a79a8b3ac342` (Issue #176 final)
- Prereg commit (FIRST on branch, BEFORE any 9×9 matrix was generated):
  `8fb864ef1a7925235153679f2a2e83220f4f6d18`
- Builder/tests commit: `5a348aa6c2b3c7f032cacaf487d6103347ddb27f`
- Overall verdict: **`state_allocation_policy_candidate_complete_with_limitations`**
- `outcome_data_loaded=true` (post-prereg only)
- `production_authorized=false`
- `revised_macro_history=true`, `real_time_vintage_claim=false`
- Research policy candidate only. No weights. No percentages. No optimizer. No Pine
  change. Not independently validated. Do not merge.

## 1. Bottom line

The frozen #174/#176 evidence translates cleanly into a deterministic exposure map:
**10 High, 42 Neutral, 17 Low, 3 Zero across 72 non-cash cells.** Every tier re-derives
from the frozen rules with no manual exception, and the verdict carries `with_limitations`
because **36 of 72 cells rest on a documented source limitation** (S&P reconstruction end,
Nasdaq/Russell price-only, investable-oil history) and **3 oil cells are
`insufficient_sample`**.

The dominant qualitative signal is *rates work when inflation is low; nothing is preferred
when inflation is high*: 6 of the 10 High cells are Treasuries, and **no High-inflation
state contains a single High sleeve**. The largest single surprise is that **Cash bias is
`low` in the Low-Growth/Low-Inflation bust (score 9)** because all three Treasury sleeves
are High there, while the only real-asset `0` in that state is Oil.

This is a policy *translation* of already-observed evidence. It is **not** an
independently validated allocation policy.

## 2. Frozen lineage and what was reused

| input | role |
|---|---|
| #174 final `f1fdda3` | 9-sleeve outcome map: evidence classification, month/episode/era/danger tables, strict zero-candidate flag |
| #176 final `5d59604` | hardened S&P 500 TR reconstruction; investable-oil series; per-sleeve verdicts |
| DH v0.1 macro blob `42516418…07dcfc` | growth/inflation states, ±10 bands, 9 states — unchanged |
| #174 `panel-comparison.json` | full-common-sample window rule (start 1987-10-01) |

Sleeve → policy evidence source (frozen in the prereg §2):

- `sp500` → #176 `affected-state-sensitivity` hardened columns (supersedes #174 broad-market proxy).
- `oil` → #176 `oil-investable-state-cells` (investable supersedes WTI spot for allocation).
- `nasdaq`, `russell`, `treasury2y`, `treasury10y`, `longtreasury`, `gold` → #174 unchanged.
- `cash` → residual only, never classified against itself.

## 3. Frozen rules actually applied (no post-hoc edits)

- `historically_favored` → **High**; `historically_unfavorable` → **Low** (upgradeable to
  `0` only via the zero rule); `mixed` → **Neutral** iff mean Cash excess ≥ 0 else **Low**;
  `insufficient_sample` → **Neutral** + `low_confidence=true`, never High or 0.
- Zero rule: `0` iff **A** (frozen `future_zero_weight_candidate` / #176 `zero_new` /
  #176 investable `zero_candidate` = true) **or B** (unfavorable AND mean excess < 0 AND
  episode excess hit ≤ 0.40 AND ≥1 severe tail [p10 monthly excess ≤ −4pp | worst episode
  ≤ −15% | P(monthly excess < −2pp) ≥ 10%] AND ex-worst-episode mean excess < 0).
- Confidence is separate from direction: `limited` iff `eligible_with_limitation`
  (nasdaq, russell, oil) or #176 verdict `hardened_with_limitation` /
  `unresolved_keep_issue174_semantics` (sp500, nasdaq, russell, oil). **No tier was
  downgraded for a source limitation.**
- Cash: `cash_role=residual`; opportunity points High +2 / Neutral +1 / Low 0 / 0 −1;
  bias `high` ≤ 3, `neutral` 4–8, `low` ≥ 9. Qualitative only — never a weight.

## 4. The complete 9-state map

Legend: `†` = `confidence=limited`, `‡` = `policy_sensitive=true` (tier changes under the
full-common-sample panel). Tiers are qualitative only.

### G_Low/I_Low — Deflationary bust (contracting activity, falling prices)

| High | Neutral | Low | Zero | Cash bias |
|---|---|---|---|---|
| `treasury2y`, `treasury10y`, `longtreasury` | `sp500`†, `nasdaq`†, `russell`†, `gold` | — | `oil`† | **low** (score 9) |

### G_Low/I_Neutral — Disinflationary slowdown (weak growth, stable prices)

| High | Neutral | Low | Zero | Cash bias |
|---|---|---|---|---|
| — | `sp500`†, `nasdaq`†‡, `russell`†, `treasury2y`‡, `treasury10y`‡, `longtreasury`, `oil`† | `gold`‡ | — | neutral (score 7) |

### G_Low/I_High — Stagflationary slump (weak growth, high inflation)

| High | Neutral | Low | Zero | Cash bias |
|---|---|---|---|---|
| — | `treasury2y`‡, `gold`, `oil`† | `sp500`†, `nasdaq`†, `russell`†, `treasury10y`‡, `longtreasury` | — | **high** (score 3) |

### G_Neutral/I_Low — Healthy disinflation (steady growth, low inflation)

| High | Neutral | Low | Zero | Cash bias |
|---|---|---|---|---|
| `sp500`†, `treasury2y`‡, `longtreasury`‡ | `nasdaq`†, `russell`†, `treasury10y`, `gold`, `oil`† | — | — | **low** (score 11) |

### G_Neutral/I_Neutral — Balanced expansion

| High | Neutral | Low | Zero | Cash bias |
|---|---|---|---|---|
| — | `sp500`†, `nasdaq`†, `russell`†, `treasury2y`, `treasury10y`, `longtreasury`, `oil`† | `gold` | — | neutral (score 7) |

### G_Neutral/I_High — Late-cycle heat (steady growth, elevated inflation)

| High | Neutral | Low | Zero | Cash bias |
|---|---|---|---|---|
| — | `sp500`†, `nasdaq`†, `gold`, `oil`† | `treasury2y`, `treasury10y`‡, `longtreasury`‡ | `russell`† | **high** (score 3) |

### G_High/I_Low — Productivity boom (strong growth, low inflation)

| High | Neutral | Low | Zero | Cash bias |
|---|---|---|---|---|
| `longtreasury` | `sp500`†, `nasdaq`†‡, `treasury2y`, `treasury10y`‡, `oil`† | `russell`† | `gold` | neutral (score 6) |

### G_High/I_Neutral — Broad boom

| High | Neutral | Low | Zero | Cash bias |
|---|---|---|---|---|
| `sp500`†, `nasdaq`†, `russell`† | `gold`, `oil`† | `treasury2y`, `treasury10y`‡, `longtreasury` | — | neutral (score 8) |

### G_High/I_High — Overheating

| High | Neutral | Low | Zero | Cash bias |
|---|---|---|---|---|
| — | `sp500`†, `nasdaq`†, `russell`†, `gold`‡, `oil`† | `treasury2y`, `treasury10y`, `longtreasury` | — | neutral (score 5) |

## 5. Tier counts and structure

| tier | cells | share of 72 |
|---|---|---|
| High | 10 | 13.9% |
| Neutral | 42 | 58.3% |
| Low | 17 | 23.6% |
| Zero | 3 | 4.2% |

By inflation band (of 24 cells each):

| inflation | High | Neutral | Low | Zero |
|---|---|---|---|---|
| Low | 7 | 14 | 1 | 2 |
| Neutral | 3 | 16 | 5 | 0 |
| High | 0 | 12 | 11 | 1 |

By growth band (of 24 cells each): Low 3/14/6/1, Neutral 3/16/4/1, High 4/12/7/1.

## 6. Zero-exposure audit (all three `0` cells)

Every audit is `zero-audit.csv`. Two zero cells satisfy **both** A and B; one satisfies B only.

| state | sleeve | path | evidence | mean excess | episode hit | p10 excess | worst episode | P(ex < −2pp) | ex-worst mean | why |
|---|---|---|---|---|---|---|---|---|---|---|
| G_Low/I_Low | oil (investable) | **B** | unfavorable | −2.93pp | 0.200 | −19.24pp | −30.81pp | 0.529 | −3.27pp | B: hit ≤ 0.40 and three tail conditions; #174/#176 strict flags were false only because the stricter #174 flag also requires n ≥ 60 (investable cell has 34 months / 15 episodes) |
| G_Neutral/I_High | russell | **A** (+B) | unfavorable | −0.56pp | 0.400 | −8.67pp | −19.18pp | 0.413 | −0.30pp | frozen #174 `future_zero_weight_candidate=true`; path B also passes |
| G_High/I_Low | gold | **A** (+B) | unfavorable | −0.65pp | 0.400 | −5.13pp | −16.63pp | 0.323 | −0.30pp | frozen #174 `future_zero_weight_candidate=true`; path B also passes |

**Oil at Low/Low is the only zero created by the policy rule itself** rather than by an
inherited frozen flag. It is robust to the #176 series switch: the #174 WTI-spot cell also
passes the #177 rule B (mean excess −4.24pp, hit 0.222, p10 −25.25pp, ex-worst −4.23pp).
It rests on 34 investable months / 15 episodes — the thinnest evidence behind any zero.

**Unfavorable cells that stayed Low** (the frozen rule deliberately did not zero them):

| state | sleeve | sole failing condition |
|---|---|---|
| G_Low/I_High | sp500 (hardened) | episode hit 0.452 > 0.40 |
| G_Low/I_High | longtreasury | episode hit 0.429 > 0.40 |
| G_Neutral/I_High | longtreasury | ex-worst-episode mean excess **+0.0154pp** (≥ 0) |
| G_High/I_High | treasury2y | no severe tail (p10 −0.43pp, worst ep −1.42pp, P(ex<−2pp) 0.000) |

## 7. Confidence / source-limitation table

`confidence.csv` (9 states × 8 non-cash sleeves); **36 limited / 36 full**.

| sleeve | confidence | limitation recorded in every cell | #176 verdict |
|---|---|---|---|
| sp500 | limited | S&P TR reconstruction (^GSPC month-ends + Shiller dividends); ends 2023-06 | `hardened_with_limitation` |
| nasdaq | limited | price-only; dividends excluded (~0.96%/yr wedge); official TR only 2003+ | `unresolved_keep_issue174_semantics` |
| russell | limited | price-only; dividends excluded (~1.34%/yr wedge); official TR only 1995+ | `unresolved_keep_issue174_semantics` |
| oil | limited | investable = CL=F excess + TB3MS collateral from 2000-09; spot kept separately | `hardened_with_limitation` |
| treasury2y | full | synthetic 2Y CMT TR | — |
| treasury10y | full | frozen #166 synthetic 10Y TR | — |
| longtreasury | full | synthetic 20Y CMT TR; 73-month 1987-10..1993-10 gap | — |
| gold | full | Pink Sheet monthly-avg price; pre-1971 fixed parity | — |
| cash | full | residual; direct T-bill accrual | — |

`low_confidence=true` (insufficient sample) — 3 cells, all investable oil:
`G_Low/I_Neutral` (19 months), `G_Low/I_High` (21 months), `G_High/I_Low` (10 months).
All three are held at Neutral per the frozen rule and can never be High or 0.

## 8. Common-sample policy sensitivity (descriptive only)

Full-common-sample panel = 1987-10-01..2026-08-01 (464 months; the only gap is
long-treasury 1987-10..1993-10, 73 months, asserted). **14 of 72 cells (19.4%) change**;
the primary matrix is untouched and every changed cell is flagged `policy_sensitive=true`.

| state | sleeve | primary | common-sample | full-panel evidence |
|---|---|---|---|---|
| G_Low/I_Neutral | nasdaq | Neutral | Low | mixed |
| G_Low/I_Neutral | treasury2y | Neutral | High | favored |
| G_Low/I_Neutral | treasury10y | Neutral | High | favored |
| G_Low/I_Neutral | gold | Low | High | favored |
| G_Low/I_High | treasury2y | Neutral | High | favored |
| G_Low/I_High | treasury10y | Low | Neutral | mixed |
| G_Neutral/I_Low | treasury2y | High | Neutral | mixed |
| G_Neutral/I_Low | longtreasury | High | Low | mixed |
| G_Neutral/I_High | treasury10y | Low | Neutral | mixed |
| G_Neutral/I_High | longtreasury | Low | Neutral | mixed |
| G_High/I_Low | nasdaq | Neutral | Low | mixed |
| G_High/I_Low | treasury10y | Neutral | High | favored |
| G_High/I_Neutral | treasury10y | Low | Neutral | mixed |
| G_High/I_High | gold | Neutral | Low | unfavorable |

Concentration: **10 of the 14 changes are Treasury sleeves** (all three tenors), 2 Nasdaq,
2 gold, 0 S&P, 0 Russell, 0 oil. The duration sleeve is the least stable component of the
policy; the equity/oil directions are the most stable.

## 9. Biggest economically surprising findings (kept, not repaired)

1. **Cash bias is `low` in the deflationary bust (`G_Low/I_Low`, score 9).** A bust state
   produces the *weakest* demand for Cash because the three Treasury sleeves are all High
   and 4 further sleeves are Neutral. The mechanism is coherent (duration is the favored
   asset in deflation) but the label reads backwards at first glance.
2. **Oil is `0` in the deflationary bust** — the only non-inherited zero. Crude's
   deflationary-bust cell has the worst episode (−30.8%) and a 20% episode hit rate.
3. **No High sleeve exists in any High-inflation state.** `G_Low/I_High`,
   `G_Neutral/I_High` and `G_High/I_High` contain zero Highs; two of the three instead get
   `cash_bias=high`. The policy expresses "no preferred asset when inflation is high".
4. **Gold is `0` in the productivity boom (`G_High/I_Low`) but only Neutral in the
   stagflationary slump (`G_Low/I_High`)** — the frozen direction comes from gold's
   boom cell (mean excess −0.65pp, flagged) versus its stagflation cell (mean excess
   +1.31pp but `mixed`, so Neutral).
5. **Russell 2000 is `0` in late-cycle heat (`G_Neutral/I_High`) while S&P 500 and Nasdaq
   are Neutral** — small caps are removed from an equity-friendly growth state on a
   75-month price-only sample.
6. **The rate sleeve dominates the High count**: 6 of 10 Highs are Treasuries. Long
   Treasury is High in both Low-inflation states but Low in all three High-growth states.
7. **58% of cells are Neutral** — the policy discriminates weakly; it is closer to a
   defensible default map than a strongly opinionated one.
8. **The #176 investable-oil switch changes the answer at `G_Neutral/I_Low`**: #174 WTI
   spot is `historically_unfavorable` (mean excess −0.43pp, hit 0.467) and would imply
   **Low**, while the investable series is `mixed` (mean excess **+1.83pp**) and yields
   **Neutral**. Both series agree on the Low/Low zero.
9. **Long Treasury at `G_Neutral/I_High` misses zero by +0.0154pp** on the
   ex-worst-episode mean. A single small-sign flip would have added a fourth zero cell.
10. **The investable-oil switch also matters at `G_High/I_Low`** (raised by the
   independent audit): under the superseded #174 WTI-spot series that cell would *also*
   satisfy path B (mean excess −1.745%, episode hit 0.368, p10 −9.62%, ex-worst −0.817%)
   and would therefore be `0`; the investable series is `insufficient_sample` (10 months)
   and holds the cell at Neutral. Both oil divergences (§9.8 and here) follow the frozen
   §2 hierarchy — no rule was bent.

## 10. Source / data limitations (explicit)

- **Nasdaq** long history is **price return only**; dividends excluded (~0.96%/yr wedge);
  official total return only from 2003+. Limitation retained on all 9 cells; tier not
  downgraded.
- **Russell 2000** long history is **price return only**; dividends excluded (~1.34%/yr
  wedge); official TR only from 1995+. Limitation retained on all 9 cells; tier not
  downgraded.
- **S&P 500** uses the #176 hardened reconstruction, which **ends 2023-06**; the 2023-08+
  window is absent from the hardened series.
- **Oil** investable history starts **2000-09** (CL=F excess + TB3MS collateral). Three
  states are `insufficient_sample`; the Low/Low zero uses 34 months / 15 episodes.
  WTI spot is retained separately and is **not** used for allocation.
- **Long Treasury** is a synthetic 20Y CMT TR series with a **73-month
  1987-10..1993-10 gap**. Earlier notes labelled this an "82-mo" gap; the measured gap is
  73 months (464 − 391) and is corrected here.
- **Revised macro history**: DH v0.1 uses revised data; `real_time_vintage_claim=false`.
- **Not independently validated**: the policy translates already-observed #174/#176
  outcomes. It must not be read as out-of-sample evidence.
- **Weak discrimination**: 58% Neutral; the map is dominated by one tier.
- **Cash bias is qualitative only** and is not a weight; the threshold bands were frozen
  before the matrix and were not tuned.
- One structural 3×3 state only: **no trajectory, no V6.6 tactical overlay**.

## 11. Verification evidence

- **Frozen-input pinning**: 12 inputs pinned to canonical HEAD blob SHA-256, with the
  worktree copy asserted byte-equivalent after CRLF normalisation (STOP on drift).
- **Self-check gate (before any tier)**: the builder recomputes the full #174
  month/episode/era/danger/classification tables and the #176 hardened S&P / investable-oil
  tables with the frozen formulas — **2,745 field comparisons, 0 mismatches**:

  | frozen table | fields compared | mismatches |
  |---|---|---|
  | issue-174/month-weighted | 648 | 0 |
  | issue-174/episode-weighted | 243 | 0 |
  | issue-174/era-stability | 162 | 0 |
  | issue-174/downside-danger | 405 | 0 |
  | issue-174/evidence-classification | 1,134 | 0 |
  | issue-176/affected-state-sensitivity | 72 | 0 |
  | issue-176/oil-investable | 81 | 0 |

- **Panel-coverage assertion**: 464 window months reproduced exactly against
  `panel-comparison.json` (per-sleeve n and mean, 0 mismatch); long-treasury is the only
  sleeve with missing months and its gap is the disclosed contiguous 1987-10..1993-10
  block (73 months).
- **Builder consistency checks**: 15/15 pass, recorded machine-readably in
  `summary.json.checks` (no unfavorable→High; every zero passes A/B; insufficient never
  High/0; 9 states × 9 sleeves; #176 supersession; Nasdaq/Russell limitations; no
  trajectory; no V6.6; no manual overrides; no percentages/weights).
- **Independent acceptance suite** `test_issue_177_matrix.mjs`: **20/20 pass**. It does not
  import the builder — it has its own CSV reader, its own state-episode construction and
  its own quantile/compound helpers, re-derives every tier from the frozen #174/#176 files,
  re-derives the S&P/investable-oil tail statistics from raw monthly returns, audits the
  zero rule, recomputes the cash score, and verifies the sensitivity flags. It includes a
  rebuild-and-compare step (canonical LF content) that proves the builder is a pure
  function of its inputs.
- **Primitive tests**: `test_issue_177_policy.py` 16/16 pass under the bundled Python;
  `test_issue_177_mirror.mjs` 10/10 assertions pass.
- **Third, toolchain-independent mirror** `test_issue_177_pandas_mirror.py` (Python +
  pandas + numpy): 5/5 pass. It shares no code with the builder or the Node suite — it
  rebuilds the 3×3 states and the state episodes itself, recomputes the policy statistics
  from raw monthly returns for the hardened S&P 500 and investable-oil series, and
  reproduces **all 72 tiers with 0 mismatches** and all 9 Cash scores/biases. It also
  independently reproduces the Low/Low oil zero inputs (n = 34, 15 episodes, mean excess
  −2.932%, episode hit 0.200, p10 −19.24%, worst episode −30.81%, P(ex < −2pp) 0.529,
  ex-worst −3.269%).
- **Independent read-only audit** (separate agent, own re-implementation of the frozen
  #174 §9 classifier, §10 strict-zero flag, month/episode/era/danger statistics and the
  #177 tier/zero/cash/common-sample rules; **620 assertions, 0 FAIL**, artifacts compared
  but never used as an arithmetic input). It independently reproduced all 72 tiers, the
  full common-sample panel (all 72 `implied` tiers and 72 `evidence_full` labels), the
  #176 supersession on all 18 sp500/oil cells, the 3 zero cells and the correct
  non-zeroing of the 4 near-misses, the 9 Cash scores/biases, and all 6 artifact
  SHA-256 hashes. It found **no rule violation, no hidden limitation and no
  summary-vs-CSV inconsistency**. Its one structural finding — that `policy-matrix.csv`
  serialised only the 72 non-cash cells — is fixed in the follow-up fix commit
  `31965ed89cc48847adb8447bf8680f310d22f83c` (see §12.10); after the fix the matrix is a true 9×9 (81 rows) and the cash
  rows now carry `cash_role`, `opportunity_score`, `cash_bias`, `confidence=full` and the
  cash limitation note.
- **Parent regression**: `test_issue_174_nine_sleeve_backbone.py` 24/24,
  `test_issue_174_mirror.mjs` 12/12, `test_issue_176_backbone.py` 7/7,
  `test_issue_176_mirror.mjs` 5/5 — all pass, no #174/#176 artifact touched.
- **Determinism**: three consecutive builds produced byte-identical artifacts; the
  acceptance suite re-runs the build and re-compares all 7 artifacts plus the hash
  manifest.
- **No policy drift while hardening QA**: the pre-hardening matrix was snapshotted first;
  after hardening, `exposure`, `confidence`, the 3 zero cells, the cash-bias table and the
  14 sensitivity changes were all confirmed identical (0 drift).

## 12. Bugs found and fixed during this issue

1. **CRLF parsing fragility (real latent hazard).** Every frozen CSV is CRLF, but the first
   builder split lines on `"\n"` and never trimmed fields, so the **last column of every
   frozen file kept a trailing `\r`**. Flags read from a last column
   (`oil-investable-state-cells.csv.zero_candidate`, `future-zero-candidates.csv.
   future_zero_weight_candidate`) would compare `"true\r" !== "true"` and silently read as
   false. Current output was unaffected (the flags actually used were non-last columns, and
   the affected values were all false), but path A for investable oil would have been
   silently missed had it ever been true. Fixed by normalising CRLF and trimming every
   field in one `parseCsv`.
2. **Incomplete self-check gate.** The gate compared only 5 fields per #174 cell
   (evidence, mean, p10 excess, worst episode, P(ex<−2pp)) and 2 for #176. It now compares
   **2,745 fields across all 7 frozen tables**, including volatility, raw p10, median,
   cash-excess mean and positive fraction, episode excess hit rate, worst episode, era
   label, evaluated-era count, P(underperform), persistent flags, ex-worst mean and the
   **recomputed strict zero flag** — turning "verbatim engine" from a claim into a
   demonstrated property (0 mismatches).
3. **Vacuous panel-coverage check.** The prereg required a real full-common-sample
   assertion, but the implementation was `NONCASH.every((sl) => true)` — always true. Now
   a real assertion: 464 months, per-sleeve n/mean equal to `panel-comparison.json`, and
   the long-treasury gap checked for length/contiguity.
4. **Verdict derived from the wrong signal.** The verdict was inferred from the existence
   of zero cells (`counts["0"] !== undefined`), which is coincidental. Now derived from
   actual limitation state (`any_limited_confidence || any_low_confidence`). The value is
   unchanged (`..._with_limitations`) but is now correct for the stated reason.
5. **Required primary-output fields missing.** `future_zero_candidate`, `zero_rule_reason`
   and `policy_sensitive` were not columns of `policy-matrix.csv` (the flag lived only in
   the sensitivity table). Added, with the zero audit extended to record the ex-worst mean
   and severe-tail evaluation.
6. **Nominal frozen-input verification.** Only the macro blob SHA was checked; the #174/#176
   files were read from the worktree and merely hashed into the summary. All 12 inputs are
   now pinned to canonical HEAD blob SHAs with worktree equivalence enforced.
7. **Incorrect limitation text.** Long-treasury's note said "82-mo 1987-93 gap"; the
   measured gap is **73 months**. Corrected.
8. **Stale documentation and cwd coupling.** `issue_177_policy.py` claimed "no Python
   runtime on this machine" (false — the primitive tests now execute), and the builder
   resolved `ROOT` from `process.cwd()`, requiring invocation from the repo root. Both
   fixed.
9. **No matrix-level acceptance test existed.** Added `test_issue_177_matrix.mjs`
   (20 checks) and `test_issue_177_pandas_mirror.py` (5 checks, a separate
   Python/pandas/numpy implementation). Three authoring pitfalls were found and fixed
   while writing them: self-referential scans (a regex tested against source text
   containing the regex literal), comparing a hash manifest without CRLF normalisation
   (which would have failed on a clone with `core.autocrlf=true`), and exact float
   equality across toolchains (pandas and JS sum in different orders, so the frozen
   `1e-12` tolerance is used).
10. **The machine-readable "9×9" matrix serialised only 8 sleeves per state.** The builder
    built the Cash row in memory (so its internal "every state contains all 9 sleeves"
    check passed) but wrote only the 72 non-cash rows to `policy-matrix.csv`; Cash
    `confidence=full` and the Cash limitation note existed in no generated artifact. This
    was found by the independent read-only audit, not by the internal checks — a reminder
    that an internal check is only as strong as the object it is applied to. Fixed by
    serialising the full 81-row matrix (72 non-cash cells + 9 Cash rows) with three added
    columns (`cash_role`, `opportunity_score`, `cash_bias`), and by extending the
    acceptance suite to assert the matrix Cash rows directly. **The fix changed no tier**:
    all 72 non-cash rows are unchanged in state/sleeve/exposure/confidence/evidence/zero
    path/limitation/policy_sensitive (drift 0 verified by diff), and `tier_counts`,
    the 3 zero cells, the Cash biases and the 14 sensitivity changes are identical.

## 13. Deliverables (all paths contain `issue-177`)

| path | content |
|---|---|
| `research/issue-177-state-allocation-policy-prereg.md` | frozen preregistration (committed first) |
| `research/issue_177_policy.py` | frozen policy primitives (stdlib only) |
| `research/issue_177_build.mjs` | deterministic builder |
| `research/test_issue_177_policy.py` | primitive unit tests (16) |
| `research/test_issue_177_mirror.mjs` | executed Node mirror (10 assertions) |
| `research/test_issue_177_matrix.mjs` | independent acceptance suite (20 checks) |
| `research/test_issue_177_pandas_mirror.py` | third independent mirror, Python + pandas + numpy (5 checks) |
| `research/generated/issue-177/policy-matrix.csv` | 9×9 machine-readable matrix (81 rows: 72 non-cash cells + 9 Cash residual rows) |
| `research/generated/issue-177/state-cards.md` | human-readable state cards |
| `research/generated/issue-177/cash-bias.csv` | Cash residual / score / bias table |
| `research/generated/issue-177/zero-audit.csv` | zero-exposure audit with rule path + reason |
| `research/generated/issue-177/confidence.csv` | policy-confidence table (36 limited / 36 full) |
| `research/generated/issue-177/sensitivity-common-sample.csv` | sensitivity table (72 rows) |
| `research/generated/issue-177/summary.json` | machine-readable summary + 15 checks + input SHAs + artifact hashes |
| `research/decisions/issue-177-state-allocation-policy-finding.md` | this finding |

## 14. Boundaries observed

No percentages, no portfolio weights, no mean-variance/Sharpe/CAGR/drawdown optimization,
no risk parity, no minimum variance, no grid search, no leverage, no shorts, no new or
dropped assets, no change to Growth_DH/Inflation_DH, no change to the ±10 thresholds or the
9 state definitions, no trajectory, no V6.6, no edit to any individual matrix cell, no
change to the zero rule or the cash thresholds after seeing results, no alteration of
#174/#176 evidence classifications, no Pine or production-code change, no merge.

## 15. Verdict

**`state_allocation_policy_candidate_complete_with_limitations`**

Reasons the verdict is *with limitations* rather than plain complete:

- 36 of 72 cells (sp500, nasdaq, russell, oil) carry a documented source limitation;
- Nasdaq and Russell long histories remain price-only proxies for total return;
- 3 investable-oil cells are `insufficient_sample`;
- the Low/Low oil zero rests on 34 months;
- 14 of 72 cells are policy-sensitive to the common-sample panel;
- 58% of cells are Neutral, so the policy discriminates weakly;
- the policy translates already-observed evidence and is not independently validated.

`production_authorized=false`. No merge.
