# VolFair+DH macro-factor lag sensitivity — results (2026-10-21)

**Status:** executed under the frozen prereg `research/volfair_macro_lag_sensitivity_prereg.md` at commit `d215075820b6507df09f143b5e0ac59650f1bc7e`; GPT prereg review comment `#6307050459` approved execution; GPT result audit `#6309472230` accepted the numerical findings and required one procedural correction, applied in §8.1. Research only, `production_authorized=false`. Draft PR #206, stacked on PR #204; **no merge, no Pine, no modification of PR #201/#204 artifacts.**

- Parents (reused unchanged): PR #201 head `2ee8fc99158f8a566d98168f757f6b3f1af5a931`, PR #204 head `6497c5436c8e8fd84cca5f685b810092b4b9d2a8`, issue #183 final `411835c`.
- Engine: `research/volfair_macro_lag_sensitivity.mjs`; mechanics: `research/test_volfair_macro_lag_sensitivity.mjs` (**64/64 PASS**); independent mirror: `research/volfair_macro_lag_sensitivity_mirror.mjs` (**0 checks failed**).
- Panel: 714 consecutive months `1967-03..2026-08`; 2bp main / 10bp sensitivity; initial deployment free; 3 inherited stale months (`2025-10`, `2025-11`, `2026-01`).
- **Fail-stop honoured:** `L=0` reproduced PR #204 before `L=1,2,3` were evaluated. No parameter was tuned, no lag dropped, no control redefined, no extra variant added.

**Bottom line (descriptive):** all four predeclared lags clear all three precommitted gates against their own matched control, so the frozen overall label is `lag_robust_descriptively_supported`. The measured gap **does not decay** with extra delay: it rises from `+0.0551` (L=0) to `+0.0796` (L=2) and dips to `+0.0780` (L=3). **No crisis loses its defense** by the precommitted definition (`D_0,c ≥ 0` and `D_L,c < 0`) at any lag. The one window that never showed defense against the matched control is **2020**, at every lag including L=0; **E2 (1980–1999)** is the only era that fails at L=0 and L=1 and it turns positive at L=2/L=3.

This label is a descriptive summary of one revised-vintage, non-PIT hindsight exercise with no p-values and no multiplicity correction. It is **not** statistical evidence, not causal proof of macro predictiveness, and not a tradability claim. It must **not** be read as "delaying the macro signal improves the strategy".

## 1. What was varied, and what was not

One variable only: an additional calendar-month publication/availability delay `L ∈ {0,1,2,3}` applied to the **already-applied** defensive factor, never to `signal_month` and never to the raw B-2 state.

```
s_L[m] = A[m - L]              A = frozen applied factor s_macro
w_L[m] = w_vol[m] * s_L[m]     calendar-month arithmetic, not row offsets
```

- `L=0` is the PR #204 replication point and uses the frozen 6-decimal `vol_dh` column.
- The shift is applied to the applied factor, so it cannot add a second B-2/availability lag. B-2 was **not** re-run.
- Warm-up uses only existing #183 history `1966-05..1967-02`; the earliest month needed (for `L=3`) is `1966-12`. No sample extension, no new data, no future state.
- The three inherited gaps are carried exactly as frozen (stored `s`, all `=1`); no interpolation, no later observation, no calendar compression.
- Per-lag control, defined separately for each `L`: `k_L = mean_714(w_L)/mean_714(w_vol)`, `w_ctrl,L = min(1, k_L × w_vol)`.

| Lag | k_L | mean equity (leg) | mean equity (control) | cap-binding months |
|---|---:|---:|---:|---:|
| L=0 | 0.910909106352 | 82.6139% | 82.6139% | 0 |
| L=1 | 0.909694217243 | 82.5037% | 82.5037% | 0 |
| L=2 | 0.909597456328 | 82.4950% | 82.4950% | 0 |
| L=3 | 0.909182118032 | 82.4573% | 82.4573% | 0 |

`k_L` uses full-sample information: the control is a **descriptive hindsight counterfactual, not an ex-ante or live-tradable strategy**. Note how little `k_L` moves across lags (0.9109 → 0.9092) — the four controls are nearly the same portfolio.

## 2. L=0 replication gate vs PR #204 (fail-stop)

| Check | Observed | Tolerance | Pass |
|---|---:|---:|---|
| `volfair` / `vol_dh` weights vs #204 | `0` / `0` | ≤ 2e-6 | yes |
| `vol_ctrl` weights vs #204 | `4.685e-7` | ≤ 2e-6 | yes |
| 2bp net returns (VolFair / leg / control) | `5.000e-7` / `5.000e-7` / `4.998e-7` | ≤ 1e-6 | yes |
| 10bp net returns (VolFair / leg / control) | `5.000e-7` / `5.000e-7` / `4.998e-7` | ≤ 1e-6 | yes |
| full / era / crisis metrics vs #204 JSON (deep leaf compare) | `0` mismatches | ≤ 1e-9 | yes |
| #204 verdict and gate values | `volfair_timing_value_descriptively_supported`, 3/4 eras, 5/6 crises | exact | yes |
| `k_0` | `0.9109091063518062` | ≤ 1e-12 | yes |

The gate passed, so evaluating `L>0` was permitted. Had any row failed, the study would have stopped without adjusting anything.

## 3. Headline results (2bp, n=714)

| Series | CAGR | Sharpe-like | MaxDD | avg equity | turnover/yr | switches |
|---|---:|---:|---:|---:|---:|---:|
| VolFair | 10.4361% | 0.4768 | −41.2024% | 90.6939% | 101.41% | 220 |
| L0 leg | 10.6131% | 0.5320 | −29.8958% | 82.6139% | 103.68% | 257 |
| L0 control | 9.9835% | 0.4768 | −37.5075% | 82.6139% | 92.38% | 220 |
| L1 leg | 10.7715% | 0.5437 | −28.2880% | 82.5037% | 100.82% | 263 |
| L1 control | 9.9772% | 0.4768 | −37.4558% | 82.5037% | 92.25% | 220 |
| L2 leg | 10.9250% | 0.5564 | −27.0373% | 82.4950% | 102.41% | 260 |
| L2 control | 9.9767% | 0.4768 | −37.4516% | 82.4950% | 92.24% | 220 |
| L3 leg | 10.9106% | 0.5549 | −27.8299% | 82.4573% | 102.54% | 266 |
| L3 control | 9.9746% | 0.4768 | −37.4339% | 82.4573% | 92.20% | 220 |

Remaining full-period fields (2bp):

| Series | ann vol | worst month | up part | down part | missed up | avoided loss | terminal × |
|---|---:|---:|---:|---:|---:|---:|---:|
| VolFair | 13.39% | −22.59% | 90.80% | 90.49% | 206.8pp | 162.0pp | 367.37 |
| L0 leg | 11.96% | −18.48% | 83.51% | 81.13% | 324.1pp | 276.8pp | 404.10 |
| L0 control | 12.20% | −20.53% | 82.71% | 82.43% | 320.6pp | 241.2pp | 287.73 |
| L1 leg | 11.97% | −18.48% | 83.57% | 80.74% | 319.9pp | 281.3pp | 440.00 |
| L1 control | 12.18% | −20.50% | 82.60% | 82.32% | 322.1pp | 242.2pp | 286.76 |
| L2 leg | 11.93% | −18.48% | 83.61% | 80.65% | 317.9pp | 287.4pp | 477.82 |
| L2 control | 12.18% | −20.50% | 82.59% | 82.31% | 322.2pp | 242.3pp | 286.68 |
| L3 leg | 11.95% | −18.48% | 83.40% | 80.89% | 317.5pp | 286.3pp | 474.13 |
| L3 control | 12.18% | −20.49% | 82.55% | 82.27% | 322.8pp | 242.7pp | 286.35 |

Participation is the mean equity weight in positive/negative equity months. Missed upside / avoided loss are summed uncompounded gross shortfalls, not utility.

### 3.1 Comparison 1 — each delayed leg vs classic VolFair (total effect, descriptive only)

| Lag | ΔSharpe | ΔMaxDD pp | ΔCAGR pp |
|---|---:|---:|---:|
| L=0 | +0.0551 | +11.31 | +0.18 |
| L=1 | +0.0668 | +12.91 | +0.34 |
| L=2 | +0.0796 | +14.17 | +0.49 |
| L=3 | +0.0781 | +13.37 | +0.47 |

These are **not** a gate and were never used to select a lag. They include the exposure reduction itself.

### 3.2 Comparison 2 — each delayed leg vs its own matched control (the precommitted gates)

| Lag | ΔSharpe (2bp) | ΔMaxDD pp (2bp) | ΔCAGR pp (2bp) | gates 2bp | ΔSharpe (10bp) | ΔMaxDD pp (10bp) | ΔCAGR pp (10bp) | gates 10bp |
|---|---:|---:|---:|---|---:|---:|---:|---|
| L=0 | +0.0551 | +7.61 | +0.63 | 3/3 | +0.0543 | +7.35 | +0.62 | 3/3 |
| L=1 | +0.0668 | +9.17 | +0.79 | 3/3 | +0.0661 | +8.87 | +0.79 | 3/3 |
| L=2 | +0.0796 | +10.41 | +0.95 | 3/3 | +0.0789 | +10.40 | +0.94 | 3/3 |
| L=3 | +0.0780 | +9.60 | +0.94 | 3/3 | +0.0773 | +9.58 | +0.93 | 3/3 |

Gate thresholds (frozen): ΔSharpe ≥ +0.02, ΔMaxDD ≥ +1.0pp, ΔCAGR ≥ −0.10pp/yr. Note the CAGR gate is one-sided and loose: a flat CAGR clears it.

### 3.3 Comparison 4 (part) — decay relative to the L=0 replication point

| Lag | ΔSharpe | ΔSharpe − Δ_0 | ΔMaxDD pp | ΔMaxDD − Δ_0 | ΔCAGR pp | ΔCAGR − Δ_0 | leg Sharpe − L0 | leg MaxDD − L0 |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| L=0 | +0.0551 | 0.0000 | +7.61 | 0.00 | +0.63 | 0.00 | 0.0000 | 0.0000% |
| L=1 | +0.0668 | **+0.0117** | +9.17 | **+1.56** | +0.79 | **+0.16** | +0.0117 | +1.6079% |
| L=2 | +0.0796 | **+0.0245** | +10.41 | **+2.80** | +0.95 | **+0.32** | +0.0245 | +2.8585% |
| L=3 | +0.0780 | **+0.0229** | +9.60 | **+1.99** | +0.94 | **+0.31** | +0.0229 | +2.0660% |

**There is no performance decay to report.** Every delayed version is *at or above* the L=0 gap on all three metrics. Sharpe is neither monotonically declining nor monotonically rising (`0.0551 → 0.0668 → 0.0796 → 0.0780`): it peaks at L=2 and dips marginally at L=3. Monotonicity was never a gate and is not used to select a lag. The whole spread (0.055–0.080 Sharpe) is well inside what a single path with no error bars can distinguish.

### 3.4 The most important caveat: the delay barely changes anything

The applied factor `s` is a slow-moving discrete state multiplier with only **five realised values** across 714 months: `1.000000` (400 months), `0.822222` (123), `0.500000` (76), `0.940667` (60), `0.911111` (55). An extra 1–3 month delay therefore usually lands on the same state:

| Lag | months where `s_L == s_0` | share | months where leg weight differs from L=0 | max abs weight gap |
|---|---:|---:|---:|---:|
| L=1 | 650 / 714 | 91.0% | 78 / 714 | 0.500000 |
| L=2 | 586 / 714 | 82.1% | 141 / 714 | 0.500000 |
| L=3 | 531 / 714 | 74.4% | 192 / 714 | 0.500000 |

So the finding is essentially: **the applied defensive factor is persistent enough that 1–3 months of additional publication delay changes its value in only 9–26% of months, and over this sample those changes were not harmful.** That is a statement about factor persistence and about the specific state-change dates, **not** evidence that delay helps. (For reference, VolFair's own weight changes in 220 of 713 month steps.)

## 4. Eras (mandatory; within-era wealth reset)

ΔSharpe leg − control, by era:

| Lag | E1 1967-03..1979-12 | E2 1980-01..1999-12 | E3 2000-01..2019-12 | E4 2020-01..2026-08 | positive |
|---|---:|---:|---:|---:|---|
| L=0 | +0.1213 | **−0.0203** | +0.0756 | +0.0303 | 3/4 |
| L=1 | +0.1297 | **−0.0033** | +0.0859 | +0.0374 | 3/4 |
| L=2 | +0.1336 | +0.0272 | +0.1011 | +0.0158 | 4/4 |
| L=3 | +0.1070 | +0.0302 | +0.1020 | +0.0366 | 4/4 |

Full era detail (Sharpe | CAGR | MaxDD), 2bp; era sizes E1 n=154, E2 n=240, E3 n=240, E4 n=80:

| Series | E1 | E2 | E3 | E4 |
|---|---|---|---|---|
| VolFair | 0.0845 \| 6.3987% \| −41.2024% | 0.6145 \| 15.8144% \| −24.2388% | 0.5504 \| 7.2647% \| −36.0473% | 0.7380 \| 12.2679% \| −16.3153% |
| L0 leg | 0.2058 \| 8.1593% \| −26.9895% | 0.5944 \| 14.6741% \| −19.8339% | 0.6263 \| 7.6911% \| −29.8958% | 0.7679 \| 12.3221% \| −14.5567% |
| L0 control | 0.0845 \| 6.4809% \| −37.5075% | 0.6147 \| 15.1150% \| −22.0362% | 0.5507 \| 6.8059% \| −32.8823% | 0.7376 \| 11.4726% \| −14.8778% |
| L1 leg | 0.2142 \| 8.2716% \| −27.5063% | 0.6114 \| 14.9687% \| −19.8339% | 0.6366 \| 7.7726% \| −28.2880% | 0.7750 \| 12.4126% \| −14.5567% |
| L1 control | 0.0845 \| 6.4819% \| −37.4558% | 0.6147 \| 15.1054% \| −22.0061% | 0.5507 \| 6.7996% \| −32.8382% | 0.7376 \| 11.4617% \| −14.8581% |
| L2 leg | 0.2181 \| 8.3283% \| −27.0373% | 0.6419 \| 15.4204% \| −19.8339% | 0.6518 \| 7.8564% \| −25.1226% | 0.7534 \| 12.1051% \| −14.5567% |
| L2 control | 0.0845 \| 6.4820% \| −37.4516% | 0.6147 \| 15.1046% \| −22.0037% | 0.5507 \| 6.7991% \| −32.8347% | 0.7376 \| 11.4608% \| −14.8565% |
| L3 leg | 0.1915 \| 7.9612% \| −27.8299% | 0.6449 \| 15.5084% \| −19.8339% | 0.6527 \| 7.8607% \| −26.1906% | 0.7742 \| 12.4383% \| −14.5567% |
| L3 control | 0.0845 \| 6.4823% \| −37.4339% | 0.6147 \| 15.1013% \| −21.9934% | 0.5507 \| 6.7969% \| −32.8197% | 0.7376 \| 11.4571% \| −14.8498% |

**Which era fails:** E2 (1980–1999) at L=0 and L=1 (ΔSharpe −0.0203 and −0.0033). It is the only era failure, and it is not a delay effect — it is already present at the replication point. At L=2/L=3 all four eras are positive. Era consistency uses Sharpe only; era rows are contiguous slices with wealth reset at era start (parent #201 convention), so era turnover/switches include the boundary step.

## 5. Crises (mandatory; within-window wealth reset)

Compounded net return, 2bp (window sizes: 1973-74 n=24, 1987 n=5, 2000-02 n=32, 2007-09 n=18, 2020 n=3, 2022 n=12):

| Series | 1973-74 | 1987 | 2000-02 | 2007-09 | 2020 | 2022 |
|---|---:|---:|---:|---:|---:|---:|
| VolFair | −39.0170% | −18.3334% | −26.4969% | −21.4755% | −14.1561% | −12.7177% |
| L0 leg | −24.8891% | −14.4967% | −20.6477% | −14.5698% | −14.1561% | −10.6049% |
| L0 control | −35.2734% | −16.4039% | −23.6333% | −19.5117% | −12.9129% | −11.4699% |
| L1 leg | −25.4208% | −14.4967% | −18.6915% | −15.3070% | −14.1561% | −10.2205% |
| L1 control | −35.2210% | −16.3776% | −23.5937% | −19.4847% | −12.8959% | −11.4528% |
| L2 leg | −24.9384% | −14.4967% | −14.8485% | −15.2480% | −14.1561% | −10.2205% |
| L2 control | −35.2168% | −16.3756% | −23.5906% | −19.4825% | −12.8945% | −11.4515% |
| L3 leg | −25.7537% | −14.4997% | −16.2987% | −13.7295% | −14.1561% | −10.2205% |
| L3 control | −35.1989% | −16.3666% | −23.5770% | −19.4733% | −12.8887% | −11.4456% |

Crisis consistency (`ret(w_L,c) ≥ ret(control,c)`): **5/6 at every lag**, identical set — 1973-74, 1987, 2000-02, 2007-09, 2022. The single failure is **2020 at every lag**, including L=0.

### 5.1 Comparison 4 (part) — crisis-defense matrix `D_L,c = ret(w_L,c) − ret(w_ctrl,L,c)`, full 6×4

| Crisis | L=0 | L=1 | L=2 | L=3 | Δ(L1−L0) | Δ(L2−L0) | Δ(L3−L0) |
|---|---:|---:|---:|---:|---:|---:|---:|
| 1973-74 | +10.3842% | +9.8002% | +10.2784% | +9.4452% | −0.5840% | −0.1058% | −0.9391% |
| 1987 | +1.9071% | +1.8809% | +1.8788% | +1.8669% | −0.0262% | −0.0283% | −0.0402% |
| 2000-02 | +2.9857% | +4.9022% | **+8.7421%** | +7.2783% | +1.9165% | +5.7564% | +4.2926% |
| 2007-09 | +4.9419% | +4.1777% | +4.2346% | +5.7438% | −0.7642% | −0.7073% | +0.8019% |
| 2020 | **−1.2433%** | **−1.2603%** | **−1.2616%** | **−1.2674%** | −0.0170% | −0.0184% | −0.0242% |
| 2022 | +0.8650% | +1.2323% | +1.2310% | +1.2251% | +0.3673% | +0.3659% | +0.3601% |

Secondary context required by the prereg, `ret(w_L,c) − ret(VolFair,c)`:

| Crisis | L=0 | L=1 | L=2 | L=3 |
|---|---:|---:|---:|---:|
| 1973-74 | +14.1278% | +13.5962% | +14.0786% | +13.2633% |
| 1987 | +3.8367% | +3.8367% | +3.8367% | +3.8337% |
| 2000-02 | +5.8493% | +7.8054% | +11.6485% | +10.1982% |
| 2007-09 | +6.9057% | +6.1685% | +6.2275% | +7.7460% |
| 2020 | +0.0000% | +0.0000% | +0.0000% | +0.0000% |
| 2022 | +2.1128% | +2.4971% | +2.4971% | +2.4971% |

### 5.2 Crisis-defense disappearance

Precommitted definition: a defense **disappears** at `L>0` when `D_0,c ≥ 0` and `D_L,c < 0`.

| Lag | disappeared | weakened (same sign, reduced) |
|---|---|---|
| L=1 | **none** | 1973-74, 1987, 2007-09, 2020 |
| L=2 | **none** | 1973-74, 1987, 2007-09, 2020 |
| L=3 | **none** | 1973-74, 1987, 2020 |

**No crisis loses its defensive value under the precommitted definition at any lag.** Weakening is real but small in the windows that weaken: 1973-74 falls from +10.38pp to +9.45pp at L=3, 1987 from +1.91pp to +1.87pp, 2007-09 is non-monotone (−0.76pp at L=1/L=2 but +0.80pp at L=3).

Two counter-movements are worth stating plainly:

- **2000-02 strengthens sharply with delay** (+2.99pp at L=0 to +8.74pp at L=2). This single window contributes most of the overall "no decay" result and is the main reason the delay looks harmless-to-helpful.
- **2020 is defensive failure at every lag, and it is not a delay effect.** `D_0,2020 = −1.24%` already. In 2020-02..04 the leg's average equity was 52.43% versus the control's 47.76% — the matched control was *less* exposed than the delayed leg, because `k_0 × w_vol` reduced exposure further while the applied factor stayed at 1 in that window (leg return is identical to VolFair there: secondary context +0.0000%).

## 6. Cost sensitivity (2bp vs 10bp)

The 10bp sensitivity case reproduces the same ordering and the same verdict: every lag clears 3/3 gates (see §3.2), and the 10bp control Sharpe is pinned at ~0.4709 for all four lags while the legs sit at 0.5251 (L=0) to 0.5497 (L=2).

| Series | CAGR | Sharpe-like | MaxDD | avg equity |
|---|---:|---:|---:|---:|
| VolFair | 10.3475% | 0.4709 | −41.2920% | 90.6939% |
| L0 leg | 10.5223% | 0.5251 | −30.2442% | 82.6139% |
| L0 control | 9.9031% | 0.4709 | −37.5941% | 82.6139% |
| L1 leg | 10.6831% | 0.5370 | −28.6764% | 82.5037% |
| L1 control | 9.8969% | 0.4709 | −37.5423% | 82.5037% |
| L2 leg | 10.8354% | 0.5497 | −27.1350% | 82.4950% |
| L2 control | 9.8964% | 0.4709 | −37.5381% | 82.4950% |
| L3 leg | 10.8207% | 0.5481 | −27.9429% | 82.4573% |
| L3 control | 9.8943% | 0.4709 | −37.5204% | 82.4573% |

Widening costs from 2bp to 10bp costs the legs roughly 0.09–0.10pp of CAGR and ~0.007 of Sharpe, and costs the controls slightly less — but it never flips a gate at any lag. Costs are still far too small to be the binding constraint here.

## 7. Frozen labels and verdicts

Per-lag verdict mapping (§6.2) and overall label (§6.3), evaluated on the 2bp primary case:

| Lag | gates | eras | crises | label |
|---|---|---|---|---|
| L=0 | 3/3 | 3/4 | 5/6 | `lag_0_timing_value_descriptively_supported` |
| L=1 | 3/3 | 3/4 | 5/6 | `lag_1_timing_value_descriptively_supported` |
| L=2 | 3/3 | 4/4 | 5/6 | `lag_2_timing_value_descriptively_supported` |
| L=3 | 3/3 | 4/4 | 5/6 | `lag_3_timing_value_descriptively_supported` |

**Overall: `lag_robust_descriptively_supported`** — every one of `L=1,2,3` passed all three gates and both consistency checks. Per the prereg this label is a descriptive summary, **not** chosen by the best-performing lag, and not a statistical test.

## 8. Integrity checks and reproducibility

All §7 prereg integrity checks passed; any failure would have stopped the study.

| Check | Observed |
|---|---|
| Panel | 714 rows, first `1967-03`, last `2026-08`, every consecutive calendar month exactly once |
| Returns finite and > −100% | all 714 months |
| `vol_dh` vs `volfair × s_macro` (6-decimal storage) | `7.169e-7` ≤ 2e-6 |
| `s_macro` vs `min(1, E_DH/0.45)` | `3.333e-7` ≤ 2e-6 |
| `E_DH` vs frozen #178 matrix equity | `5.551e-17` ≤ 5e-5 |
| Panel equity / cash vs frozen upstream sources | `0` / `0` |
| VolFair vs independent daily recomputation | `4.967e-5` (w_fair stored at 4 decimals) |
| Stale months | exactly `2025-10`, `2025-11`, `2026-01`; stored value equals last valid factor; not present in #183 |
| Warm-up | 724-month calendar map `1966-05..2026-08`; overlap 711 observed months at `3.333e-7` ≤ 2e-6 |
| Lag availability | every `m−L` for `L=0..3` resolves inside `1966-05..2026-08`; every shifted factor finite and in `[0.5, 1]` |
| Control integrity | `0 < k_L < 1`, zero cap-binding months, mean-exposure equality `< 1e-9`, `0 ≤ w_L ≤ w_vol ≤ 1` |
| B-2 provenance | #183 timeline consumed as-is; not re-run, not shifted |
| Fail-stop execution order | asserted: L=0 weights → L=0 P&L → gate → then L=1,2,3 weights and P&L |
| Determinism | two engine runs byte-identical (JSON and CSV) |

### 8.1 Execution-order correction (GPT audit `#6309472230`)

The first execution (`211fcb1`) computed **all four lags' weights in one pass in §6 and all four lags' P&L in one loop in §7, before §9 ran the L=0 replication gate**. The gate did gate *acceptance and publication* of the results, but it did **not** gate the *computation* of L>0 returns. The prereg and the approval require L=0 to reproduce #204 "before any L>0 is evaluated", and the earlier claim that the engine did so was therefore **not literally true**. This is disclosed rather than glossed over.

It was corrected structurally rather than by wording. The engine now:

1. builds **only** the L=0 replication point (`buildLag(0)`);
2. prices **only** VolFair, `L0` and `C0`;
3. runs the L=0 replication gate against #204 and throws on any mismatch;
4. only then builds and prices `L=1,2,3` (§9b).

The realised sequence is recorded in `integrity.execution_order` and asserted, including that the gate event index precedes every `L{1,2,3}_pnl_computed` event. `test_volfair_macro_lag_sensitivity.mjs` checks this order **and** includes a negative control proving the ordering predicate rejects a genuine violation, so the fail-stop claim is falsifiable rather than asserted. Observed trace:

```
lag_0_weights_and_control_built, VolFair_pnl_computed, L0_pnl_computed, C0_pnl_computed,
l0_replication_gate_passed, lag_1_weights_and_control_built, L1_pnl_computed, C1_pnl_computed,
lag_2_weights_and_control_built, L2_pnl_computed, C2_pnl_computed,
lag_3_weights_and_control_built, L3_pnl_computed, C3_pnl_computed
```

**Re-running changed nothing.** All 714-month primary results, era/crisis numbers, gates, decay values and the overall label are bit-for-bit identical to `211fcb1`: 2403 numeric and primitive leaves compared with maximum difference `0`, zero missing keys, zero changed values, and the monthly audit CSV is **byte-identical** (SHA256 `1F92A8E7E207F137C5554741FDBF5386744BF978DEA85F7645E64023A62A5778`). Only the two new audit fields (`integrity.execution_order`, `integrity.execution_order_enforced`) differ. No threshold, weight formula, control definition or result was altered.

**Tests:** `test_volfair_macro_lag_sensitivity.mjs` — **64/64 PASS**, covering calendar-shift arithmetic and year boundaries, inclusive frozen gate semantics at the exact thresholds, verdict/label mapping, synthetic per-lag control mechanics, warm-up availability (the three months needed for L=3 resolve to `s=0.5`), stale carry with no calendar compression, no-future-leak, **fail-stop execution order with a negative control**, mirror execution and byte-level determinism.

**Independent mirror:** `volfair_macro_lag_sensitivity_mirror.mjs` re-derives the calendar shift, the four controls, every 2bp/10bp net, and the full-period metrics from the published audit CSV along a separate code path with no engine import. Max absolute differences: calendar shift `0`, control reconstruction `5.6e-17`, per-lag `k` `3.1e-9`, 2bp net `5.3e-7`, 10bp net `5.4e-7`, full-period metrics `3.5e-7` — all at 6-decimal audit-storage level. **0 checks failed.**

**Second independent implementation (corroboration, not committed):** while this run was starting, a separately authored implementation of the same prereg produced its artifacts in the working tree from a concurrent session. Those files were hashed and moved out of the repository (never committed) before this run began. That implementation's monthly audit CSV is **byte-identical to the one committed here** (SHA256 `1F92A8E7E207F137C5554741FDBF5386744BF978DEA85F7645E64023A62A5778`), and its legs, controls, gates, decay values and 6×4 crisis matrix agree with this run's JSON to `0` absolute difference. This is a strong independent-check signal, but it is **two implementations of one preregistration, not two studies**: it corroborates that the arithmetic was implemented faithfully, and says nothing about whether the design is a valid test.

## 9. Verdict and honest scope

**The delayed macro factor retains its descriptive advantage at L=1, 2 and 3 months in this historical panel, and no crisis window loses its defense.** The advantage does not decay; it is largest at L=2.

What this does **not** license:

- It is **not** evidence that delaying the macro signal is beneficial, and the frozen criteria never allowed selecting L=2 or L=3. The result is dominated by the factor's persistence (§3.4) and by a single window (2000-02) that improves with delay.
- Revisions to disclosed numbers must not be read as an improvement claim.
- `L=1,2,3` are **overlapping, highly correlated specifications of the same 714 months**, not independent tests. Four correlated looks with no p-values and no multiplicity correction cannot support a statistical claim; the "robust" label describes direction and gate-clearing only.
- `k_L` uses full-sample information. The controls are hindsight mean-matched counterfactuals, not tradable portfolios.
- **Revised-vintage, non-PIT.** #189 found full nine-state PIT not identifiable (G5 has no continuous first-reported vintage; I3/I4 are not equivalent; I5 matches at the tested tolerance with a residual SA-basis caveat). This experiment delays only the already-applied factor; it does not delay the underlying macro releases, re-estimate states, re-run B-2, or reconstruct what an investor could have known. It is a publication/availability delay stress test, **not** a point-in-time backtest, and it **cannot repair historical data-revision bias**. Release-day timing, vintage revisions, benchmark revisions and real-time publication calendars are not modelled.
- Revised-vintage limitations from #201/#204 remain (French/CRSP revisions, TB3MS/1200 cash-proxy timing, CIZ-era daily file, monthly rounding). The L=0 replication target is the #204 frozen artifact, so an error shared with #204 would not be caught by this gate.

`production_authorized=false`. No Pine change, no merge, no edit to PR #201/#204.
