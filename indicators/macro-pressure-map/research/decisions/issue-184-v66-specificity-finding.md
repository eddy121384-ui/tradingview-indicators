# Issue #184 — V6.6 overlay specificity — Finding

- Issue: [#184](https://github.com/eddy121384-ui/tradingview-indicators/issues/184)
- Branch: `research/issue-184-v66-overlay-specificity`
- Base: `411835cc9e3a00d0f5d998df9fb2058d8a917e96` (#183 final)
- Prereg: `6da9a3611c3b16b8e602711bd9f1e3f3678ceb6a` (committed BEFORE any C/D return)
- Verdict: **`v66_overlay_risk_control_supported_but_timing_not_specific`**
- `production_authorized=false`. Research only. No merge. No Pine change.

## Question

Does the frozen V6.6 ±5pp Equity↔Cash overlay contain genuine timing
information, or does ordinary Equity de-risking explain its risk improvement?

## Design (frozen prereg §§1–12)

- A = corrected structural baseline, no overlay (frozen #183 tradable A col
  pre-cost; post-cost A_post = A_pre − structural turnover × 0.0002).
- B = actual V6.6 overlay post-cost (frozen #183 tradable C col; 0 mismatches
  at 1e-12 on reproduction of A_pre/B_pre/B_post over all 232 months).
- C = exposure-matched constant de-risk: `d = 3.051724137931045`pp
  (Aeq 45.6778448276 − Beq 42.6261206897, weights-only, no returns used),
  same constant every month, pro-rata non-zero Equity scaling, zeros kept,
  no V6.6 read in the C code path, same 2bp cost convention.
  Exposure match |avgEq(C) − avgEq(B)| ≈ 1e-13pp (tolerance 0.01pp).
- D = ALL 231 non-zero circular shifts of the frozen 232-signal sequence
  (35 risk-on / 163 risk-off / 34 neutral), same ±5pp rule, timing, costs,
  baseline. Shift: month i gets `S[((i−k) mod 232 + 232) mod 232]`, k = 1..231.
- Panel: 232 months, 2007-02-01 → 2026-08-01, research/tradable dates identical,
  0 drops. Segments pre-2020 / 2020–2022 / 2023+; frozen ±3mo B-2 transition
  windows (36 transitions; 172 inside / 60 outside).

## Results (post-cost tradable panel)

| metric | A | B (actual) | C (constant) | B−C |
|---|---|---|---|---|
| CAGR | 8.1261% | 7.8228% | 7.8020% | +0.021pp |
| vol ann | 7.7783% | 7.2994% | 7.3120% | −0.013pp |
| Sharpe-like | 0.85160 | 0.86385 | 0.85989 | +0.0040 |
| MaxDD | −16.453% | −15.119% | −14.633% | −0.486pp |
| worst month | — | −6.144% (2020-03) | −6.394% (2020-03) | +0.250pp |
| downside vol | — | 4.3088% | 4.3456% | −0.037pp |
| turnover ann | 35.93% | 57.11% | 35.68% | +21.43pp |
| avg Equity / Cash | 45.68 / 19.09 | 42.63 / 22.14 | 42.63 / 22.14 | — |
| B−C monthly corr | — | — | — | 0.9974 |

- S1 (risk benefit vs A): vol, MaxDD, downside all better for B → TRUE.
- S2 (vs exposure-matched): Sharpe +0.004 ≥ −0.02; MaxDD −0.486pp ≥ −1.0pp → TRUE.
- Placebo ranks for B (higher = better; ties count for B):
  CAGR 61.5, Sharpe 72.3, MaxDD 32.0, downside 78.8, worst-month 100.
  Only 1/4 ≥ 90 (worst-month) → S3 (≥2 @90) FALSE; partial (≥1 @75) TRUE.
- S4 turnover B−C 21.43pp ≤ 40pp → TRUE.
- S5 worst segment B−C −0.062pp ≥ −1.0; worst state (n≥12) −0.222pp ≥ −3.0 → TRUE.
- Tree: S1∧S2∧¬S3∧S4∧S5 →
  `v66_overlay_risk_control_supported_but_timing_not_specific`.

Placebo medians: CAGR 7.793%, Sharpe 0.8550, MaxDD −14.521%, downside 4.364%,
worst −6.145%. B beats 61/72/32/79/100% of shifts respectively.

Segments B−C (CAGR pp): pre-2020 −0.044, 2020–2022 +0.377, 2023+ −0.062 —
no catastrophe; B helps most in 2020–2022. Transition inside/outside
mean(B−C) reported in `transition-diagnostics.json` (windows frozen 36/172/60).

## Interpretation

- The overlay's risk improvement over the structural baseline is REAL
  (lower vol, shallower MaxDD, lower downside) and SURVIVES exposure matching:
  constant de-risking does not beat it on Sharpe, and B is slightly better on
  CAGR/vol/downside/worst-month with only MaxDD 0.49pp worse.
- But TIMING SPECIFICITY FAILS the strong test: B is ordinary-to-good inside
  the placebo distribution (61st/72nd/32nd/79th percentiles), reaching the top
  decile only on worst-month — where the rank is inflated by ties (≈70% of
  shifts place risk-off on 2020-03 and tie B at −6.144%). MaxDD is
  below-median (32nd): the actual calendar alignment does not protect drawdown
  better than the same signals shifted in time.
- Correct conclusion is de-risking value WITHOUT timing specificity — NOT
  information value, NOT no-value. No rescue rule is proposed in this issue.

## Verification

- A/B reproduction 0 mismatches (1e-12) over 232 months.
- Exposure recomputation weights-only matches prereg within 1e-9pp; C match
  within 1e-13pp.
- 231/231 placebos evaluated, none dropped/selected.
- 15 Python tests OK (`test_issue_184_specificity.py`); 10 Node mirror PASS.
- Determinism: rerunning the committed builder is byte-identical across all
  10 generated files (hash-verified).
- Parents unmodified; V6.6 bytes untouched; no optimizer/grid/retune;
  no leverage/shorts; no production code.

## Limitations

- Single 232-month panel (2007-02+); not pristine OOS (V6.6 lineage known).
- Cost model is the frozen 2bp turnover proxy, not live slippage.
- Worst-month rank 100 reflects mass ties at 2020-03, disclosed above.
- C turnover (35.68%) differs 0.25pp from structural (35.93%) because the
  pro-rata share of `d` varies with monthly E — expected, disclosed, method
  unchanged from prereg.

## Deliverables

- Prereg: `research/issue-184-v66-specificity-prereg.md`
- Primitives/tests: `research/issue_184_specificity.py`,
  `research/test_issue_184_specificity.py`, `research/test_issue_184_mirror.mjs`
- Builder: `research/issue_184_build.mjs`
- Outputs: `research/generated/issue-184/` (manifest, exposure,
  control-monthly, placebo-distribution, percentile-ranks, comparison-ABC,
  segment/transition/state diagnostics, summary)
- This finding.

`production_authorized=false`
