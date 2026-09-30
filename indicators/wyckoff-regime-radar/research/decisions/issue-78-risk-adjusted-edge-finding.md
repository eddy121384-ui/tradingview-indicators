# Issue #78 — Risk-Adjusted Edge / Equal-Volatility Audit Finding

## Scope

This finding executes the frozen preregistration in `issue-78-risk-adjusted-edge-preregistration.md`.

The audit asks:

> **Do the frozen exposure-control rules improve normalized return per unit of risk, or do they mostly look safer because they carry less exposure?**

Accepted sample:

- 68,118 Issue #76 event rows;
- 1,624 completed known-start Markup / Markdown episodes;
- nine daily markets;
- causal next-move exposure timing;
- zero strategy return outside completed active trend episodes.

All returns remain direction-aligned underlying movement in episode-entry ATR units. They are not executable dollar returns.

## Result 1 — Defensive overlays reduce risk, but reduce return even more

All-sample equal-market metrics:

| Policy | Ann. normalized return | Ann. vol | Sharpe-like | Sortino-like | Max DD | 5% ES | Ann. turnover |
|---|---:|---:|---:|---:|---:|---:|---:|
| Formal Hold | 3.097 | 17.391 | **0.176** | **0.254** | 73.70 | -2.331 | 12.18 |
| Simple / No de-risk | 2.630 | 15.617 | 0.170 | 0.242 | 68.61 | -2.228 | 8.75 |
| Progressive / No de-risk | 2.643 | 15.403 | **0.174** | 0.246 | 66.95 | -2.195 | **8.61** |
| Simple / Warning-First | 2.012 | 12.940 | 0.155 | 0.223 | 58.81 | -1.776 | 10.80 |
| Progressive / Warning-First | 1.982 | 12.710 | 0.155 | 0.223 | 56.85 | -1.739 | 10.73 |
| Simple / Gentle | 1.583 | 11.276 | 0.141 | 0.209 | 53.13 | -1.509 | 13.70 |
| Progressive / Gentle | 1.627 | 11.193 | 0.145 | 0.214 | 52.19 | -1.485 | 13.16 |
| Simple / Balanced | 0.979 | 9.861 | 0.105 | 0.160 | 53.68 | -1.312 | 17.99 |
| Progressive / Balanced | 1.040 | 9.791 | 0.113 | 0.171 | 52.77 | -1.291 | 17.21 |

The pattern is monotone:

- more defensive management lowers volatility, drawdown and left-tail loss;
- normalized mean return falls faster than volatility;
- Sharpe-like and Sortino-like ratios therefore decline as de-risking becomes more aggressive.

This is risk reduction, but not evidence of Sharpe improvement.

## Result 2 — Equal-volatility scaling does not reveal hidden alpha

Within each market, every policy was scaled diagnostically to Formal Hold volatility.

Equal-market annualized normalized return at Formal Hold volatility:

- Formal Hold: **3.097**
- Progressive / No de-risk: **2.901**
- Simple / No de-risk: **2.848**
- Simple / Warning-First: **2.769**
- Progressive / Warning-First: **2.767**
- Progressive / Gentle: **2.706**
- Simple / Gentle: **2.624**
- Progressive / Balanced: **2.111**
- Simple / Balanced: **1.988**

No frozen exposure-control policy exceeds Formal Hold on the equal-market equal-volatility comparison.

The same conclusion appears if the logic is reversed and policies are scaled to Formal Hold mean return:

- Simple / No de-risk would require about **1.177×** scale and would reach roughly **18.39** annualized vol;
- Progressive / No de-risk would require about **1.172×** scale and would reach roughly **18.05** vol;
- Formal Hold vol is about **17.39**.

Thus the lower-volatility add-risk policies do not preserve enough return to dominate Formal Hold at the same return target.

## Result 3 — Progressive add-risk without de-risk is the closest call

Progressive / No de-risk is the strongest low-complexity risk-control compromise in this audit:

- retains about **85.4%** of Formal Hold annualized normalized return;
- retains about **88.6%** of Formal Hold volatility;
- Sharpe-like ratio is **0.174 vs 0.176**;
- max drawdown falls about **9.2%**;
- 5% expected shortfall improves about **5.8%**;
- annualized turnover falls about **29%**.

Its Sharpe improves versus Formal Hold in **5/9 markets**, but the equal-market mean Sharpe is still slightly lower and equal-vol return is lower by about **0.196 normalized ATR/year**.

Therefore it is reasonable to call this a **near-Sharpe-neutral risk-path improvement**, not a risk-adjusted alpha result.

Simple / No de-risk is similar but slightly weaker:

- Sharpe **0.170 vs 0.176** Formal Hold;
- Sharpe improves in **4/9 markets**;
- max drawdown improves in **7/9**;
- 5% expected shortfall improves in **9/9**.

## Result 4 — Warning-First is useful for tail control, not for Sharpe

Relative to the corresponding no-de-risk add-risk policy:

### Simple family

Warning-First:

- reduces annualized volatility by about **2.68** normalized units;
- reduces equal-market max drawdown by about **9.80 ATR**;
- improves 5% expected shortfall in **9/9 markets**;
- improves max drawdown in **8/9 markets**;
- but Sharpe improves in only **3/9 markets**;
- equal-vol scaled return improves in only **3/9 markets**;
- equal-market Sharpe falls by about **0.016**.

### Progressive family

Warning-First:

- reduces annualized volatility by about **2.69**;
- reduces max drawdown by about **10.11 ATR**;
- improves 5% expected shortfall in **9/9 markets**;
- improves max drawdown in **8/9**;
- but Sharpe improves in only **3/9**;
- equal-vol return improves in only **3/9**;
- equal-market Sharpe falls by about **0.019**.

Warning-First therefore has genuine defensive value, but the current sample does not show that it earns more normalized return per unit of volatility.

## Result 5 — Gentle and Balanced increasingly overpay for protection

Gentle and Balanced continue the same frontier:

- stronger drawdown / left-tail protection;
- further deterioration in Sharpe and equal-vol return;
- materially higher turnover, especially under Balanced.

For both add-risk families:

- Gentle improves 5% expected shortfall in **9/9 markets**, but Sharpe improves in only **3/9**;
- Balanced improves 5% expected shortfall in **9/9**, but Sharpe improves in only **2/9**.

Balanced is particularly unattractive as a Sharpe candidate because it combines the largest return sacrifice with the highest turnover.

## Result 6 — The risk-adjusted ordering is temporally unstable

The add-risk-only policies look better than Formal Hold in earlier eras, then worse in the most recent era.

Equal-market Sharpe-like ratio:

### 2010–2014

- Formal Hold: **0.433**
- Simple / No de-risk: **0.478**
- Progressive / No de-risk: **0.476**

### 2015–2019

- Formal Hold: **-0.020**
- Simple / No de-risk: **0.024**
- Progressive / No de-risk: **0.019**

### 2020–2026

- Formal Hold: **0.057**
- Simple / No de-risk: **0.026**
- Progressive / No de-risk: **0.031**

Participation control therefore improves the risk-adjusted path in some regimes, including the previously difficult 2015–2019 slice, but the advantage reverses in 2020–2026.

This fails a temporal-stability test for a universal Sharpe claim.

Warning-First does not repair this instability. Relative to no de-risk, its Sharpe effect is negative in 2010–2014 and 2015–2019, and approximately flat / mixed in 2020–2026.

## Result 7 — Direction diagnostics show the underlying edge is asymmetric

Formal Hold equal-market Sharpe-like ratio:

- Markdown: **0.226**
- Markup: **0.008**

Add-risk-only policies slightly improve the weak Markup Sharpe but reduce the stronger Markdown Sharpe.

This asymmetry is descriptive only. No separate directional policy is introduced.

It is another reason not to claim a universal risk-adjusted alpha from the current in-sample evidence.

## Research decision

### Supported

1. **Exposure controls materially reshape risk.** Drawdown and left-tail reductions are real and broad across markets.
2. **Progressive / No de-risk is the strongest current simplicity-vs-risk compromise.** It is nearly Sharpe-neutral while lowering drawdown, tail risk and turnover.
3. **Warning-First is a legitimate defensive overlay** when the objective function values drawdown / tail control more than maximum Sharpe.

### Not supported

The current nine-market daily discovery sample does **not** support the claim that the de-risk overlays create risk-adjusted alpha in the Sharpe / equal-vol sense.

> **Return falls more than volatility under the defensive overlays. Equal-vol scaling does not recover a return advantage.**

Do not describe Warning-First, Gentle or Balanced as alpha enhancers.

## Practical interpretation

The answer depends on the desk's objective function:

- if the objective is **maximum in-sample Sharpe-like ratio**, Formal Hold remains the benchmark leader;
- if the objective is **near-preserved Sharpe with lower drawdown / tail / turnover**, Progressive / No de-risk is the cleaner current candidate;
- if the objective places a premium on **drawdown and left-tail containment**, Warning-First is useful, but that protection has a measurable expected-return cost.

This is a meaningful risk-management result even though it is not a Sharpe-alpha result.

## Next gate

Do not search more ATR thresholds or exposure percentages in-sample.

Freeze the surviving policies and test whether the near-Sharpe-neutral participation benefit and defensive tail benefit generalize to genuinely new evidence:

- new markets / asset classes;
- weekly data;
- prospective observations;
- eventually instrument-mapped executable returns with transaction costs.

Refs #78, #80 and #76.
