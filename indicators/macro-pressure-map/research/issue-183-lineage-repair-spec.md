# Issue #183 — Lineage repair specification (frozen)

- Issue: [#183](https://github.com/eddy121384-ui/tradingview-indicators/issues/183)
- Branch: `research/issue-183-allocation-lineage-repair`
- Base (pre-spec) HEAD: `57852112ce95913d48297b35f803a1583cbab314` (#182 final)
- This spec is the FIRST Issue #183 research commit on this branch.
- Status: REPAIR SPECIFICATION — frozen before any corrected replay result
  is generated or viewed.
- `outcome_data_loaded=false` (at spec commit; no replay output exists)
- `production_authorized=false`
- `revised_macro_history=true`
- `real_time_vintage_claim=false`

## 0. Ordering attestation

The CURRENT GitHub Issue #183 body was read in full via webfetch
(authoritative; no cached copy). Parent artifacts (#178 weights/policy/backtest
mechanics, #180 proxies/costs/timing, #182 V6.6 bytes/rule/gates, frozen
preregs §§-quoted below) were read as frozen INPUTS only. Pre-spec work was
limited to BUG-MECHANISM verification (code reading + cash-bias.csv column
check; no replay metric computed). No corrected CAGR/Sharpe/MaxDD or gate
outcome was computed or viewed.

Sequence (mandatory):

1. read Issue #183;
2. verify bug mechanism + parent artifact presence (no replay metrics);
3. freeze this spec;
4. commit it;
5. record spec SHA;
6. ONLY THEN run corrected replays.

Any later repair-scope change requires a NEW issue.

## 1. Bug proof (frozen fact, verified pre-spec)

- File: `indicators/macro-pressure-map/research/issue_178_backtest.mjs`,
  loader line 40: `cb[c[0]] = c[1]`.
- `cash-bias.csv` header: `state,opportunity_score,cash_bias,cash_role`.
  Column 1 is `opportunity_score` ("9","7",…); the bias label ("low"/
  "neutral"/"high") is column 2.
- Line 25: `CMIN_BIAS = {low:5, neutral:10, high:20}` → lookup of "9" yields
  `undefined` → line 62 `100 − S < undefined` is false → bias-minimum scaling
  NEVER fires → cash falls through to residual floored at `CASH_MIN = 2`
  with non-cash weights unscaled.
- Affected states (only states whose raw non-cash sum exceeds its bias floor):
  Low-Low (raw 101 → used 101 + cash 2 = 103% gross) and Neutral-Low
  (raw 107 → used 107 + cash 2 = 109% gross). All other states byte-identical
  to the frozen matrix path (verified: 6 states match to rounding).
- The frozen `weight-matrix.csv` itself is CORRECT (9 rows sum to 100.00).
  The defect lives ONLY in the backtest weight computation. No parent
  artifact is modified by this issue.

## 2. Corrected engine (frozen definition)

The corrected replay consumes the frozen 9×9 matrix DIRECTLY as the
portfolio source of truth (per-issue preference), with these frozen asserts
evaluated BEFORE any return is touched (fail-stop):

- every state row sums to exactly 100% (tolerance 1e-9 pre-rounding);
- gross exposure ≤ 100% + 1e-9 in every applied month;
- no sleeve weight < −1e-9;
- the three frozen zero cells remain exactly 0;
- sleeve caps respected (matrix is pre-capped; assert ≤ cap + 1e-9);
- family caps respected (Equity ≤ 60, Rates ≤ 50, Real ≤ 15, + 1e-9);
- Cash within [2, 60] in every applied month;
- B-2 confirmation rule byte-identical to #178 (allocation for month m from
  DH states through m−1; hold on unconfirmed months; backtest starts
  1966-05-01; turnover = 0.5×Σ|Δtarget| fraction units).

## 3. Replay scopes (mirror parent deliverables exactly, no additions)

- Phase A (#178): max-history (1966-05+, dynamic availability per #178 §7
  with hardened-S&P French fallback + investable oil + #174 others) AND
  full-universe (2000-09–2023-06) panels; benchmarks (static Neutral, Cash
  100%, French equity 100%, 60/40 French/10Y, monthly rebalanced);
  S1 (alt baseline 30/15/10/6/12/7/5/3), S2 (0/0.25/1/2), S3 (immediate)
  sensitivities; metrics per #178 §9; eras E1–E4 frozen bounds; state-level
  means; turnover block (ann/one-way/switches/raw changes/avg-between/
  avg-change). Old buggy series is READ from frozen
  `backtest-monthly.csv` (never recomputed) for the old-vs-corrected diff.
- Phase B (#180): proxy map / costs (turnover×0.0002, alt 0.0010) / timing
  (month-end close; alt 1-mo lag) / missing-proxy-to-Cash / strict panel
  2006-06-01+ (assert 0 drops) / benchmarks / ONEQ-10bp-lag sensitivities —
  all verbatim; A/B/C with corrected structural base; ORIGINAL six gauges
  (|CAGR|≤1.0, TE≤2.5, MaxDD≥−5, drag≤0.4, rank kept, defensive vol≤2) and
  ORIGINAL verdict mapping reused unchanged.
- Phase C (#182): V6.6 bytes (§5), ±10 bands, risk mapping, ±5pp budget,
  pro-rata scaling, zeros, timing state(m−1), costs, panels (research
  2007-01+ backbone; tradable 2007-01+ ETF), ORIGINAL seven gates
  (C−A≥−0.50pp; ΔSharpe≥−0.05; ΔMaxDD≥−3pp; incr turnover≤40pp/yr;
  concentration moot-if-no-benefit else top-1≤60%; worst segment≥−1.0pp/yr;
  worst state(n≥12)≥−3.0pp/yr) and ORIGINAL verdict mapping, transition
  ±3mo union windows, alignment (Growth bands equal), segments
  pre-2020/2020–22/2023+, S1/S2/S3 — all verbatim.
- Determinism: every replay runs twice; any bit-difference fails the run.

## 4. Verdict mappings (frozen; evaluated post-replay, thresholds fixed)

- Corrected #178: `..._revalidated` | `..._revalidated_with_limitations` |
  `..._invalidated_by_repair`. Basis (frozen here): revalidated iff corrected
  policy keeps CAGR within ±1.0pp/yr of neutral-benchmark-relative standing
  (same sign of policy-minus-neutral CAGR gap as buggy run), MaxDD no worse
  than buggy by >3pp, turnover within ±5pp/yr of buggy, no new cap/cash
  violation, sensitivities stable; invalidated iff corrected MaxDD worsens
  >10pp vs buggy or any integrity assert fails; else with_limitations.
  (Comparative-revalidation framing is frozen here because #178 itself had no
  pass/fail gates — this mapping is the only new judgment in the issue, and
  it is fixed before results.)
- Corrected #180: original six gauges decide: all pass → `revalidated`;
  ≤2 fail (none semantic/TE>4%) → `..._with_limitations`; else `..._invalidated`.
- Corrected #182: ORIGINAL seven gates decide among supported/suggestive/
  not_supported exactly as #182 prereg §8.
- Overall: `allocation_lineage_repair_complete` (all three revalidated/
  supported) | `..._complete_with_material_changes` (any with_limitations/
  suggestive, or |ΔCAGR|>1pp anywhere) | `..._failed` (any invalidated/
  not_supported, or any integrity assert fails).

## 5. No-change list (frozen)

Tiers, zeros, Cash-bias labels, baseline, multipliers, caps, Cash min/max,
bias minimums, normalization, B-2, benchmarks, sensitivities, proxies, costs,
timing, V6.6 bytes/mapping/budget, gates, macro states/thresholds. No
optimizer, no grid search, no leverage, no shorts, no Pine changes, no merges,
no parent-artifact writes. Worse results are REPORTED.

## 6. Deliverables (all paths contain `issue-183`)

- `research/issue-183-lineage-repair-spec.md` (this file)
- `research/issue_183_repair.py` (frozen stdlib: asserts/gate/verdict primitives)
- `research/test_issue_183_repair.py` (+ executed Node mirror test)
- `research/issue_183_replay.mjs` (Phase A/B/C corrected replay + audits)
- `research/generated/issue-183/manifest.json` (frozen-input/hash manifest)
- `research/generated/issue-183/corrected-structural-monthly.csv`
- `research/generated/issue-183/old-vs-corrected-178.csv` (+ `comparison-178.json`)
- `research/generated/issue-183/corrected-implementation-monthly.csv`
- `research/generated/issue-183/preservation-180.json`
- `research/generated/issue-183/corrected-overlay-monthly.csv`
- `research/generated/issue-183/gates-182.json`
- `research/generated/issue-183/state-diagnostics.csv`
- `research/generated/issue-183/era-report.json`
- `research/generated/issue-183/transition-alignment.json`
- `research/generated/issue-183/sensitivity-183.json`
- `research/generated/issue-183/lineage-diff.json`
- `research/generated/issue-183/summary.json`
- `research/decisions/issue-183-lineage-repair-finding.md`

Replay MUST pin parent SHAs, assert §2 gates before computing, reproduce
frozen tier/zero/bias/V6.6 inputs exactly, run determinism self-checks, never
overwrite other issues' artifacts, never touch Pine, never optimize.

## 7. Firewall

After this spec commit and the first replay result, do NOT change: bug
statement, corrected engine, replay scopes, verdict mappings, or any frozen
parent. Failure is REPORTED, never repaired here. Forbidden: parameter
changes, retrospective parent edits, Pine changes, merging.

## 8. Product boundary

Research lineage repair only. Finding MUST contain
`production_authorized=false`. Do not merge.
