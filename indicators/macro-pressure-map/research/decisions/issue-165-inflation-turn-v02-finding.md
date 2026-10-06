# Issue #165 — Deep-History inflation v0.1 — causal persistence turn layer (v0.2)

- Issue: [#165](https://github.com/eddy121384-ui/tradingview-indicators/issues/165)
- Branch: `research/issue-165-inflation-turn-v02` (isolated worktree; shared checkout untouched)
- Frozen parents: v0.1 model `cc331bf…`, #164 finding `2cbc5fb…`
- Formal verdict: `inflation_turn_v02_failed`
- `outcome_data_loaded=false`
- `production_authorized=false`
- Nothing was altered in I1–I5 sources, weights, scoring, or the Inflation_DH
  level. No asset-return outcome was tested. No merge requested.

## 1. Frozen v0.2 rule (applied exactly)

`I_slow[t] = mean(Inflation_DH[t..t−2])`, `trend3[t] = I_slow[t] − I_slow[t−3]`
(all inputs finite, causal, no interpolation). Candidate turn at t on
trend3 sign change (`>0` from `≤0`, or `<0` from `≥0`); confirmed iff the new
sign still holds at t+1. Stored `economic_turn_month = t` and
`signal_available_month = t+1` (verified programmatically that signal is never
earlier than economic month). No amplitude/hysteresis gates, no window search
in the primary study. Turn-layer evaluable sample: 724 months
(1965-08 → 2026-08).

## 2. Noise reduction (A): insufficient

- v0.2 turns: **134** (vs frozen v0.1 count 182, recomputed identically).
- Reduction: **26.4%** (gate needs ≥30% → FAIL).
- Median/mean dwell: **4 / 5.39 months** (gate needs median ≥6 → FAIL).
- v0.1 turns retained within ±1 mo: 90/182 (49.5%).
- Isolated reversals (next turn ≤3 mo later, opposite direction): 40/133 (**30.1%**).
- The SMA3 layer is only mildly slower than the raw composite rule.

## 3. CPI timing (B): hits without consistency

- CPI turns (frozen rule): 105. Matched (econ months): 91 → hit rate **0.867** (PASS ≥0.75).
- Median/mean lead, economic months: **2 / 2.91**; signal-available months: **2 / 2.98**.
- Direction-consistent share: **0.4615** (42/91; gate needs ≥0.75 → FAIL).
- False v0.2 turns: **43** (gate ≤60 → PASS).
- Unmatched CPI turns (14): 1975-08, 1979-11, 1980-04, 1983-08, 1990-03,
  1992-06, 1992-11, 2001-06, 2002-10, 2010-01, 2010-12, 2013-05, 2022-07, 2023-07.
- The layer finds most CPI turns near-coincidentally (median lead 2) but pairs
  opposite directions over half the time — timing without directional discipline.

## 4. GDP-deflator quarterly (C): best-behaved diagnostic

Quarter-end trend3 sampling (no interpolation), same turn rule: 51 deflator
turns, 63 DH-quarterly turns, 43 matched → hit rate **0.843** (PASS ≥0.70),
median lead **3 mo**, mean 4.53; quarterly direction agreement 0.52 (n=240).

## 5. Episodes (D): 4/8, all misses are 1–2 month lags

| episode | ref turn (src) | v0.2 turn (dir) | signal | lead | pass |
|---|---|---|---|---|---|
| late-60s | 1967-02 deflator | 1966-11 (−) | 1966-12 | +3 | PASS |
| 1973-75 | 1975-01 CPI | 1974-08 (−) | 1974-09 | +5 | PASS |
| 1978-80 | 1980-04 CPI | 1980-05 (−) | 1980-06 | −1 | FAIL |
| 1981-86 trough | 1985-10 CPI | 1985-11 (+) | 1985-12 | −1 | FAIL |
| 1990 | 1990-03 CPI | 1990-05 (−) | 1990-06 | −2 | FAIL |
| 2008 peak | 2008-08 CPI | 2008-10 (−) | 2008-11 | −2 | FAIL |
| 2008 trough | 2009-08 CPI | 2009-04 (+) | 2009-05 | +4 | PASS |
| 2021-22 | 2022-07 CPI | 2022-01 (−) | 2022-02 | +6 | PASS |
| 2023-26 trough | 2025-05 CPI | 2025-07 (+) | 2025-08 | −2 | FAIL |

4/8 pass (gate needs ≥7 → FAIL). Every miss is a 1–2 month lag, and an
existential-preceding reading (any direction-correct turn in [ref−15, ref])
would give 7/8 — disclosed here for transparency. It does not change the
verdict: gates 3, 4, and 7 fail independently of this ambiguity, and the
primary locked rule (nearest turn, lead ∈ [0,15]) is what was frozen by the
report item "nearest economically correct v0.2 turn".

## 6. State preservation (E): verified

Inflation_DH level SHA256 (LF-normalized) `42516418…07dc` matches Issue #160
exactly → gate 1 PASS. The v0.2 layer adds information (smoothing/turns)
without touching the state variable.

## 7. All frozen gates (no rescue)

| # | gate | result |
|---|---|---|
| 1 | level identical to #160 | PASS |
| 2 | turn-layer sample ≥700 mo (724) | PASS |
| 3 | reduction ≥30% vs 182 (26.4%) | FAIL |
| 4 | median dwell ≥6 (4) | FAIL |
| 5 | ≥7/8 episodes direction-correct 0–15 (4/8) | FAIL |
| 6 | CPI hit rate ≥0.75 (0.867) | PASS |
| 7 | direction-consistent ≥0.75 (0.462) | FAIL |
| 8 | false turns ≤60 (43) | PASS |
| 9 | deflator hit rate ≥0.70 (0.843) | PASS |
| 10 | signal never earlier than economic month | PASS |

Formal verdict: `inflation_turn_v02_failed` (sample sufficient, so not
inconclusive; four gates fail).

## 8. Reading

SMA3 persistence filtering moves all diagnostics in the right direction
(fewer turns, fewer false positives than v0.1's 82, kept 4/8 episodes, kept
deflator timing) but not far enough on any structural bar: turns remain
~4-monthly, consistency stays below a coin-flip-plus-noise reading, and
episode coverage is exactly half. The layer is a valid descriptive smoother;
it is not a validated regime-turn signal. Any alternative rule (including
heavier smoothing) needs a new issue.

## 9. Post-verdict sensitivity (descriptive only; verdict frozen above)

| smoother | turns | reduction | med/mean dwell | CPI hit | CPI med lead | consist. | false |
|---|---|---|---|---|---|---|---|
| SMA2 | 149 | 18.1% | 4 / 4.94 | 0.914 | 2 | 0.448 | 53 |
| SMA3 frozen | 134 | 26.4% | 4 / 5.39 | 0.867 | 2 | 0.462 | 43 |
| SMA6 | 83 | 54.4% | 7 / 8.56 | 0.610 | 2.5 | 0.469 | 19 |

Heavier smoothing trades hits for turn-count/dwell/false improvements while
median lead (≈2) and consistency (≈0.46) barely move. Stored in
`inflation-turn-v02-sensitivity.json`; not used for the verdict or any rule.

## 10. Artifacts

- `research/decisions/issue-165-inflation-turn-v02-finding.md` (this file)
- `research/generated/issue-165/inflation-turn-v02-summary.json` (rule, sample,
  noise, CPI/deflator timing, episodes, gates, verdict)
- `research/generated/issue-165/inflation-turn-v02-monthly.csv` (month, DH
  level, I_slow, trend3, turn flags, both dates)
- `research/generated/issue-165/inflation-turn-v02-episodes.csv` (per-episode checks)
- `research/generated/issue-165/inflation-turn-v02-sensitivity.json` (post-verdict SMA2/SMA6 only)

## 11. Workflow evidence and verification

- Isolated worktree at the frozen base; shared checkout untouched.
- DH hash verified before use; CPI/GDPD reuse hashes verified (USIRYY,
  USCPCEPIAC from #160 records; GDPD FNV from #161).
- v0.1 182-turn and CPI 105-turn counts reproduced exactly before comparison.
- Primary verdict was written to the summary JSON before the sensitivity
  script was executed; sensitivity lives in a separate file.
- Verdict-relevant ambiguity (nearest vs existential episode reading) checked:
  verdict invariant (gates 3, 4, 7 fail either way).

## 12. Explicit confirmations

- No asset-return outcome was loaded: no SPY/TLT prices or returns, no
  equity-minus-duration spread, no Issue #136 payoff data — frozen DH series
  plus CPI / GDP-deflator macro benchmarks only.
  `outcome_data_loaded=false`.
- No production code was changed; no v0.1/v0.2 parameter was tuned and no
  alternative primary rule was created. `production_authorized=false`.
- Do not merge.
