# Issue #68 Phase B3.15 — Event-Window / Stale-Memory Audit preregistration

Status: diagnostic only / frozen C-2 / no performance use.

## Question

For the exact B3.14 Break-final-blocker events, how long does old-side range-break memory remain active **after the market's MA relation has actually moved to the new target side**, how quickly does target-side range evidence form, and does Break continue to vote for the old direction during that overlap?

This phase tests timing semantics only. It does **not** assume that `breakoutBars=20` is too long.

## Frozen scope

Reuse mechanically, without changing formulas:

- the same frozen four-FX fixtures and reciprocal transforms;
- the same B3.10 exact S2↔S5 raw-handoff detector;
- the same B3.14 Break-final-blocker population (mechanically expected: 106, never hard-coded as a selection rule);
- the same production C-2 Break decomposition and existing `breakoutBars`, MA lengths, Break weight and thresholds.

No PnL, Strategy Tester metric, return, Sharpe, drawdown, turnover or sizing result may enter this phase.

No tuning/search of:

- `breakoutBars`;
- Break weight;
- MA length;
- Break / range / MA formulas;
- classifier thresholds;
- lifecycle / Core Bias / Exposure;
- Volume / MTF / Divergence / HMM.

## Event clock

For a Break-final-blocker raw handoff on bar `t`, B3.14's blocker evidence is read on `t-1`.

Orient every event toward its new target direction (Bull or Bear).

Define `MA_TARGET_SIDE` from the existing MA50 relation only:

- Bull target: `log_price > ma_log`;
- Bear target: `log_price < ma_log`.

No substitute MA-side proxy may be introduced.

## Event-related MA flip

Each event receives one mechanically defined target-side MA flip or a censored label.

### A. MA is already target-side on `t-1`

The event-related flip is the **first bar of the contiguous target-side MA run that contains `t-1`**. Walk backward from `t-1` until the immediately preceding bar is not target-side.

This is the primary stale-memory population because the market has already crossed to the new MA side before the blocker event.

### B. MA is not target-side on `t-1`

Classify the blocker as `PRE_MA_FLIP_AT_BLOCKER`.

Then, for timing context only, search forward from `t` for the first target-side MA bar **while the oriented fresh S2-vs-S5 raw edge remains on the new target side**. If the raw edge loses the target side first, label the MA flip censored for this handoff spell.

These events are not evidence that old memory stayed stale after an MA turn, because the MA turn had not happened at the blocker clock.

## Measurements after the event-related MA flip

Within the contiguous target-side MA run beginning at the event-related flip:

1. `OLD_RANGE_SURVIVAL_BARS`
   - number of bars from the MA flip until old-side recent range-break memory first becomes inactive;
   - `0` if old range memory is already clear on the flip bar;
   - right-censored if it never clears before the target-side MA run ends.

2. `NEW_RANGE_DELAY_BARS`
   - number of bars from the MA flip until target-side range evidence first becomes positive;
   - `0` if already present on the flip bar;
   - right-censored if it never appears before the target-side MA run ends.

3. `STALE_OVERLAP_BARS`
   - bars where `MA_TARGET_SIDE == true` **and** old-side recent range-break memory remains active.

4. `BREAK_OLD_DURING_STALE_OVERLAP`
   - on each stale-overlap bar, evaluate the existing oriented Break edge;
   - count target-positive, old-negative and zero Break bars;
   - do not invent a new Break threshold.

5. `BREAK_RELEASE_DELAY_BARS`
   - from the MA flip, number of bars until the existing oriented Break edge first becomes strictly target-positive;
   - right-censored if Break never becomes target-positive before the target-side MA run ends.

6. `NEW_RANGE_BEFORE_OLD_CLEAR`
   - whether target-side range evidence forms before old-side range memory clears.

## Primary populations and outputs

Report all 106 mechanically reproduced Break-final-blocker events, but keep causal interpretation split:

- `MA_TARGET_AT_BLOCKER`: MA already new-side on `t-1` — primary stale-memory population;
- `PRE_MA_FLIP_AT_BLOCKER`: MA still old-side on `t-1` — contextual population, not stale-after-turn evidence.

Primary outputs:

- exact Break-final-blocker reproduction count;
- count/share in each population;
- distribution (count, median, p75, max, censored count) of old-range survival, new-range delay and Break-release delay after MA flip;
- total stale-overlap bars and share where Break still votes old direction;
- event share with at least one `MA target + old range memory + Break old` bar;
- share where new range appears before old memory clears;
- per-pair and Bull/Bear breakdown;
- reciprocal agreement for event population labels and uncensored timing values.

## Engineering gates

- Break-final-blocker reproduction must remain exact versus B3.14 / B3.10;
- reciprocal population-label agreement >=99%;
- reciprocal uncensored timing agreement >=99% on comparable mirrored events;
- no unexplained event accounting;
- no performance keys in generated reports.

There is deliberately no gate requiring stale overlap to be long or requiring Break to be the primary reversal-lag cause. A null or weak stale-memory result is acceptable.

## Decision rule

- If the `MA_TARGET_AT_BLOCKER` population shows materially persistent old range memory **and** Break remains old-negative through a meaningful part of that overlap, stale range-memory semantics remains a credible handoff-delay mechanism and may justify a later mechanism-design phase — still before any parameter tuning.
- If old range memory survives but Break usually turns target-positive quickly, the memory is visually stale but not mechanically decisive; demote it.
- If target range evidence is usually delayed longer than old memory decay, investigate target-side range-evidence formation instead of decay.
- If most blocker events remain `PRE_MA_FLIP_AT_BLOCKER`, Break is more likely lagging together with MA structure than independently dragging after the market has crossed.

## Rates / TradingView human review after mechanical pass

After the frozen-FX mechanical audit passes, generate a TradingView audit showing the same clocks for:

- FR10Y 1D, 2021–2024, Bull — primary adverse case;
- JGB10Y 1D, 2021–2024, Bull — rates control;
- EURUSD / frozen FX as control context.

Human review asks only whether the same stale-overlap mechanism is visibly present around adverse handoffs. No parameter changes are permitted from the screenshots.
