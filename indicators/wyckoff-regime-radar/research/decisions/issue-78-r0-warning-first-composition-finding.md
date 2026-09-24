# Issue #78 — R0 + Warning-First Composition Study Finding
## Evidence-based add-risk × frozen deterioration management

## Scope

This finding executes the preregistered composition study in:

`issue-78-r0-warning-first-composition-preregistration.md`

No composition result was inspected before the preregistration.

The study combines two already-frozen layers:

1. **R0 evidence-based participation**
   - 25% Probe from fresh formal Markup / Markdown entry;
   - P0 / P1 / P2 earn 100% Full at t+3;
   - P3 and episodes without a usable B3 breakout remain at Probe.

2. **Warning-First deterioration management**
   - tolerate giveback <2 entry ATR;
   - 2–4 ATR -> reduce earned exposure by 25pp;
   - 4+ ATR -> reduce by 50pp;
   - minimum positive exposure remains 25%;
   - reductions latch;
   - only a new favorable close-path extreme clears the latch.

The management layer is active from episode entry and is not reset at breakout or t+3.

Primary comparison:

> **R0 + No De-risk vs R0 + Warning-First**

Gentle and Balanced remain frozen secondary comparators only.

All returns are normalized underlying-move units, not executable futures / cash PnL.

## Frozen sample reproduced exactly

The accepted Issue #76 logger files reproduce:

- 68,118 events;
- 1,624 completed formal trend episodes;
- 997 B3 breakout events;
- 236 P1 / P2 events;
- P0 = 411;
- P1 = 110;
- P2 = 126;
- P3 = 350.

Maximum OHLC reconstruction error is approximately 5.6e-14.

## 1. Whole-system result: Warning-First materially reshapes risk

Equal-market complete-path results:

| Policy | Ann. return | Ann. vol | Sharpe-like | Sortino-like | Max DD | 5% ES | Avg exposure | Ann. turnover | Equal-vol return vs R0 |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| R0 No De-risk | 1.4623 | 11.8544 | 0.1187 | 0.1666 | 58.03 | -1.8556 | 0.4862 | 5.1400 | 1.4623 |
| R0 Warning-First | 1.2984 | 9.4771 | 0.1200 | 0.1667 | 40.39 | -1.4458 | 0.4109 | 6.2144 | 1.6404 |
| R0 Gentle | 1.2434 | 8.0403 | 0.1315 | 0.1863 | 32.28 | -1.1898 | 0.3464 | 7.6658 | 1.8650 |
| R0 Balanced | 0.8818 | 6.7134 | 0.1065 | 0.1507 | 33.04 | -0.9838 | 0.2598 | 10.7472 | 1.5929 |

Relative to R0 No De-risk, Warning-First changes the whole path by approximately:

- annualized normalized return: **-11.2%**;
- annualized volatility: **-20.1%**;
- maximum drawdown: **-30.4%**;
- 5% ES magnitude: **-22.1%**;
- equal-vol annualized return: **+12.2%**;
- annualized turnover: **+20.9%**.

This is not merely “less exposure gives less return.”

At equalized R0 volatility, Warning-First's return is higher in the aggregate sample.

## 2. Cross-market breadth: tail / drawdown protection is much broader than return improvement

Warning-First minus R0 No De-risk:

### Annualized return

- equal-market delta: **-0.1639**
- median market delta: **-0.2283**
- Warning-First higher in **3/9 markets**

### Sharpe-like

- delta: **+0.0013**
- positive in **5/9**

### Sortino-like

- delta: **+0.0001**
- positive in **5/9**

### Maximum drawdown

- delta: **-17.64**
- drawdown improves in **9/9 markets**

### 5% expected shortfall

- delta: **+0.4099**
- improves in **9/9 markets**

### Equal-vol annualized return

- delta: **+0.1781**
- improves in **5/9 markets**

### Turnover

- delta: **+1.074**
- turnover rises in **9/9 markets**

Interpretation:

> Warning-First's risk protection is extremely broad, but its return / risk-adjusted improvement is not equally broad.

## 3. Failed / small trends improve universally

For MFE <4 ATR episodes:

- R0 No De-risk: **-0.9538 ATR**
- R0 Warning-First: **-0.8708 ATR**

Improvement:

> **+0.0829 ATR**

Direction is favorable in **9/9 markets**.

So the deterioration layer does what it was designed to do:

> once a formal trend starts failing, it reduces the damage from keeping full earned exposure.

The effect is modest because many failed episodes never earn Full under the R0 evidence layer.

## 4. Middle trends benefit more strongly

For MFE 4–8 ATR:

- R0 No De-risk: **-0.9142 ATR**
- R0 Warning-First: **-0.5398 ATR**

Improvement:

> **+0.3744 ATR**

Direction is favorable in **8/9 markets**.

This is an important composition result.

The R0 evidence layer does not by itself prevent substantial giveback in medium-strength trends. Warning-First materially reduces that damage.

## 5. Large-trend harvest is the cost

For MFE >=8 ATR:

- R0 No De-risk: **+6.1524 ATR**
- R0 Warning-First: **+5.1812 ATR**

Warning-First retains approximately:

> **84.2% of R0 large-trend harvest**

but gives up:

> **0.9711 ATR**

on an equal-market basis.

R0 beats Warning-First in **8/9 markets** in the large-trend slice.

This is the same structural tradeoff seen in earlier Issue #78 management work:

> the system buys protection by trimming exposure during deep but recoverable pullbacks inside genuine trends.

## 6. Warning-First remains a middle frontier, not the most defensive policy

Relative to Gentle:

- Warning-First keeps more average exposure: 0.411 vs 0.346;
- retains more large-trend harvest: 5.181 vs 4.528 ATR;
- has lower annualized turnover: 6.214 vs 7.666;
- but Gentle has lower volatility / drawdown / ES and higher full-sample Sharpe / equal-vol return.

Balanced is more defensive still but gives up substantially more raw return and has the highest turnover.

Therefore the three management layers retain the expected qualitative ordering:

> **No de-risk = gross-harvest extreme**  
> **Warning-First = middle / lower-churn defensive point**  
> **Gentle = more defensive / higher-churn point**  
> **Balanced = strongest exposure suppression, weak gross-return efficiency**

No single in-sample scalar is used to choose among them.

## 7. Promotion-time diagnostic: the management layer is not secretly resetting at t+3

Across the 647 P0 / P1 / P2 episodes that earn Full at t+3:

Warning-First is already latched at the promotion close in approximately:

> **14.7%** of episodes on an equal-market basis.

Mean actual exposure immediately after the R0 promotion is:

> **94.9%**

rather than mechanically resetting to 100%.

This confirms the intended composition semantics:

> new evidence can increase earned participation, but it does not erase already-observed damage.

No special t+3 reset is introduced.

## 8. Mandatory temporal audit: the composition is not stable enough to become default

This is the key failure.

### 2010–2014

Warning-First versus R0:

- annualized return delta: **-1.0377**
- Sharpe delta: **-0.0412**
- equal-vol return delta: **-0.3728**
- ES improves in **9/9**
- max drawdown improves in **8/9**

### 2015–2019

Warning-First versus R0:

- annualized return delta: **-0.6555**
- Sharpe delta: **-0.0713**
- equal-vol return delta: **-0.6590**
- Warning-First beats R0 annual return in only **2/9 markets**
- Sharpe improves in only **1/9**
- equal-vol return improves in only **1/9**
- ES still improves in **9/9**
- max drawdown improves in **8/9**

### 2020–2026

Warning-First versus R0:

- annualized return delta: **+0.1401**
- Sharpe delta: **+0.0224**
- equal-vol return delta: **+0.2177**
- return / Sharpe / equal-vol direction favorable in **6/9**
- ES improves in **9/9**
- max drawdown improves in **9/9**

This is a material regime dependence.

The aggregate equal-vol benefit is driven much more by the later sample than by a stable historical relationship.

The mandatory 2015–2019 stress era therefore blocks promotion of Warning-First as the universal default management layer.

## 9. Direction split does not justify separate rules

### Markup

Warning-First minus R0:

- annualized return: **+0.0594**
- equal-vol return: **+0.0800**
- ES improves in 9/9;
- max drawdown improves in 8/9.

### Markdown

Warning-First minus R0:

- annualized return: **-0.2233**
- equal-vol return: **+0.1289**
- ES improves in 9/9;
- max drawdown improves in 9/9.

Risk protection is broad in both directions, but raw-return behavior differs.

Per the preregistration:

> **do not create separate Markup / Markdown management rules.**

## 10. Tail concentration is not worsened

Equal-market share of positive episode harvest contributed by the top 1% winners:

- R0 No De-risk: **15.48%**
- Warning-First: **14.83%**

After removing each market's single best episode:

- R0 No De-risk mean episode harvest: **+0.0774 ATR**
- Warning-First: **+0.0817 ATR**

So the Warning-First risk result is not being purchased through greater dependence on one or two giant trends.

This is supportive, but does not repair the temporal failure.

## Decision

### Do not make Warning-First the universal default management layer

The preregistered default-promotion gate is not met.

Warning-First has strong and broad defensive value:

- lower drawdown in essentially every market;
- better 5% ES in every market;
- lower volatility;
- universal failed/small-trend protection;
- strong middle-trend protection;
- modestly better aggregate equal-vol return.

But it also:

- lowers raw return in 6/9 markets;
- gives up roughly 16% of large-trend harvest;
- increases turnover;
- fails to improve Sharpe / equal-vol return broadly in 2010–2014;
- fails clearly in the mandatory 2015–2019 stress era.

Therefore the correct classification is:

> **R0 + Warning-First survives as an optional defensive / risk-budget overlay, not as the universal default.**

### Current frozen frontier

Retain:

1. **R0 + No De-risk**
   - current gross-harvest / simplest management baseline.

2. **R0 + Warning-First**
   - current lower-risk, lower-churn defensive challenger.

Keep Gentle only as a secondary more-defensive benchmark.

Balanced does not merit promotion from this composition pass.

## State-machine interpretation

The current discovery architecture is:

Wyckoff Markup / Markdown  
→ 25% Probe  
→ Breakout  
→ 3-bar Acceptance / Follow-through  
→ P0 / P1 / P2 / P3  
→ P0 / P1 / P2: R0 earns Full at t+3  
→ P3: remain Probe  
→ optional Warning-First deterioration layer:
  - <2 ATR giveback: tolerate
  - 2–4 ATR: reduce 25pp
  - 4+ ATR: reduce 50pp
  - new favorable extreme: reset latch
→ formal regime loss: exit

Resume R5 / R1 remains a confidence / diagnostic state, not a required add-risk gate.

## Stop-rule consequence

Do **not** invent Warning-First v2 on this daily in-sample dataset.

Do not add:

- new giveback levels;
- special t+3 reset;
- P0 / P1 / P2-specific management;
- Markup / Markdown-specific management;
- new deterioration features.

The next legitimate research gate is genuinely new evidence:

> **freeze R0 No De-risk and R0 + Warning-First, then challenge both on weekly and/or prospective / heterogeneous OOS data.**

This composition study does not support further same-sample threshold work.

PR #80 remains Draft / open / unmerged.

Refs #78, #80, #76.
