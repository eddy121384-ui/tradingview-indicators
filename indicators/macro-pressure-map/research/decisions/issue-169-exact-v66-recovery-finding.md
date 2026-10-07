# Issue #169 — Exact V6.6 broad weak-state recovery — finding

- Issue: [#169](https://github.com/eddy121384-ui/tradingview-indicators/issues/169)
- Branch: `research/issue-169-exact-v66-recovery-translation` (isolated worktree)
- Prereg commit (pre-outcome): `a25050461d16f3169870de6635b246133e32607f`
- Frozen lineage: #167 final `8749a4f…` (27 DH triggers, signal +4.45%, control
  +2.11%, incr +2.35pp, CI [−0.55pp,+5.53pp], 8/9 gates, suggestive_not_robust);
  #133 snapshot SHA `1d039235…` (verified); #166 backbones (unmodified).
- Formal verdict: `exact_v66_recovery_translation_not_supported`
- `outcome_data_loaded=true`
- `production_authorized=false`
- `repeated_modern_sample=true`
- `pristine_oos_claim=false`
- Repeated-sample semantic translation only — not independent confirmation.
  Research only; no production/Action-Layer authorization. Do not merge. Do not
  alter #167/#136.

## 1. Exact V6.6 usable period and primary sample

Snapshot: 388 months, 1994-05-31 → 2026-08-31, zero month gaps, header
`date,gpi,ipi,regime`. Primary state (`GPI ≤ +10 AND IPI ≤ +10`) forms
**55 episodes**; **14 independent first triggers** (3 deep, 11 mild);
**14 signals, 117 controls**, all payoff-complete (last trigger admits full
t+2…t+4 window inside backbone coverage through 2026-08/09).

## 2. Primary 3M outcome (t+2 start)

- Signal spread mean **+1.23%**, median −0.10%, positive fraction 0.43 (6/14).
- Control mean **+2.80%**, median +5.16%.
- Incremental (signal − control): **−1.57pp**.
- Legs: Equity mean +3.26%, Treasury mean +2.03%.
- Episode-cluster bootstrap (seed 169, 10,000/10,000 valid): 95% CI
  **[−8.19pp, +5.68pp]**.
- Secondary horizons (descriptive): 1M/6M/12M spreads in results JSON.

## 3. Segments, robustness

- pre-2020: 11 signals / 84 controls, incr **−1.29pp**.
- 2020–2022: 2 / 12, incr **−3.64pp**.
- 2023+: 1 / 21, incr **−0.42pp**.
- Leave-one-trigger-episode-out: 14/14 evaluable, minimum **−4.16pp**
  (no positive LOO run).
- Concentration: strongest positive trigger share **0.454**.
- Delayed t+3 implementation (n 14/117): incremental **−5.44pp**.

## 4. All 9 gates (no rescue)

| # | gate | result |
|---|---|---|
| 1 | ≥8 trigger episodes (14) | PASS |
| 2 | signal mean > 0 (+1.23%) | PASS |
| 3 | incremental > 0 (−1.57pp) | FAIL |
| 4 | bootstrap CI lower > 0 (−8.19pp) | FAIL |
| 5 | ≥2 segments with both arms (3/3) | PASS |
| 6 | ≥2/3 evaluable segments positive (0/3) | FAIL |
| 7 | every evaluable LOO > 0 (min −4.16pp) | FAIL |
| 8 | concentration ≤ 50% (45.4%) | PASS |
| 9 | delayed implementation positive (−5.44pp) | FAIL |

Mapping: gate 1 passes; not all pass; gates 2 AND 3 are not both positive
⇒ `exact_v66_recovery_translation_not_supported`. (Directionally the layer
fails at gate 3 itself: signals underperform controls by 1.57pp.)

## 5. Post-verdict secondaries (descriptive; verdict frozen before execution)

- Native-market t+1 timing (payoff t+1…t+3): signal +1.65% (n=14) vs control
  +2.67% (n=117), incremental −1.02pp — still negative, no rescue.
- SPY/TLT repeat: **unavailable** — no frozen modern SPY/TLT total-return data
  exist in the repository (only unrelated hidden-regime-map Pine/parity
  files); nothing was fetched, per contract.
- Deep vs Mild triggers: deep n=3, mean +3.89%, median +5.73%, pos_frac 0.67
  (eras 2/1/0); mild n=11, mean +0.50%, median −0.11%, pos_frac 0.36
  (eras 9/1/1). Diagnostic only; neither subgroup is validated.
- Cross-layer (exact V6.6 vs frozen DH v0.1, common modern months): 385 common
  months, primary-state agreement 0.63; exact triggers 14 vs DH triggers 27;
  matches ±1m: **0**; ±3m: **5**, median lag 3 mo; matched exact-trigger mean
  +4.59% (n=5) vs unmatched −0.64% (n=9), descriptive only. Date-level
  agreement is low, as #160 requires; the same-direction question is answered
  by the primary gates above (negative).

## 6. Reading

The translated rule does not reproduce the Deep-History direction on exact
V6.6: absolute signal payoffs are mildly positive (+1.23%) but controls —
other weak-state months — do better (+2.80%), in every era, under delay, and
under every leave-one-out perturbation. The economic hypothesis (weak-state +
dual 3M improvement ⇒ equity duration-outperformance) is not supported on the
exact signal layer. This does not overturn #167 (different signal layer,
suggestive result stands as reported).

## 7. Artifacts

- `research/issue-169-exact-v66-recovery-prereg.md` (pre-outcome commit)
- `research/issue_169_exact_v66_recovery.py` (frozen evaluator, pure stdlib)
- `research/test_issue_169_exact_v66_recovery.py` (synthetic-only tests)
- `research/generated/issue-169/recovery-signal-control.csv` (14 signals, 117 controls, all horizons)
- `research/generated/issue-169/recovery-episodes.csv` (55 episodes)
- `research/generated/issue-169/recovery-results.json` (metrics, gates, verdict)
- `research/generated/issue-169/recovery-subgroups.csv` (deep n=3 / mild n=11)
- `research/generated/issue-169/recovery-crosslayer.csv` (agreement, matches, matched/unmatched means)
- `research/generated/issue-169/recovery-secondary.json` (native t+1, SPY/TLT status, cross-layer detail)
- This finding.

## 8. Tests / CI evidence; bugs fixed before finalization

- Python suite is pure-stdlib (no runtime on this machine): PRNG pinned to 5
  Node-derived mulberry32(169) vectors; state/deep/d3 boundaries; first-trigger
  and control-exclusion semantics; payoff compounding/completeness/delay;
  LOO evaluability edge; severity split; four synthetic end-to-end verdict
  panels (supported / inconclusive / not_supported / suggestive), with the
  supported panel constructed so every gate is deterministic (identical signal
  payoffs strictly above every possible control payoff; verified-arbitrary
  bootstrap draws cannot flip it).
- Node mirror executed the real study; a full rerun reproduced verdict, CI,
  and incremental bit-identically (determinism evidence).
- One dead-code fragment removed pre-run; no result-affecting bug was found
  (no date-join or lookahead defect; payoff windows and t+1/t+2 bookkeeping
  verified against the CSV day columns).

## 9. Explicit flags

`outcome_data_loaded=true` (post-prereg #166 backbones + #133 snapshot only).
`production_authorized=false` (no Pine touched; 10 new research files only).
`repeated_modern_sample=true` (2007+ inspected in #133/#136; no OOS claim).
`pristine_oos_claim=false`. Do not merge. Do not alter #167/#136.
