# Issue #78 — Progressive Exposure State Machine First-Pass Preregistration

## Purpose

Freeze the first causal progressive de-risk / re-risk comparison **before** looking at its results on the accepted nine-market discovery sample.

This is discovery research, not OOS validation and not a production trading rule.

## Universe and semantics

Reuse the accepted Issue #76 nine-market daily sample. Primary aggregation is equal-market and cross-asset. Markup and Markdown are direction-aligned so positive means favorable to the active trend.

No classifier parameter, feed, representation, or market-specific setting may change in this pass.

## Causal timing

At close of bar `t`, compute current giveback from the running favorable extreme of the active formal trend episode using information available through `t` only.

The exposure selected from that health bucket applies to the **next** one-bar move `t -> t+1`.

If the formal trend regime is no longer active, target exposure is zero. If health later improves while the same formal episode remains alive, exposure may increase again according to the same frozen mapping. No hindsight re-entry is allowed.

## Frozen health buckets

Use the already-discovered Issue #76 entry-ATR giveback buckets unchanged:

1. `<0.5 ATR`
2. `0.5–1 ATR`
3. `1–2 ATR`
4. `2–4 ATR`
5. `4+ ATR`

These boundaries are not tuned in Issue #78 first pass.

## Frozen candidate exposure ladders

Exposure is expressed as absolute fraction of full directional target risk; sign comes from Markup vs Markdown.

| Health bucket | Formal hold | Gentle | Balanced | Defensive |
|---|---:|---:|---:|---:|
| <0.5 ATR | 1.00 | 1.00 | 1.00 | 1.00 |
| 0.5–1 ATR | 1.00 | 1.00 | 0.75 | 0.50 |
| 1–2 ATR | 1.00 | 0.75 | 0.50 | 0.25 |
| 2–4 ATR | 1.00 | 0.50 | 0.25 | 0.00 |
| 4+ ATR | 1.00 | 0.25 | 0.00 | 0.00 |

`Formal hold` is the slow/high-giveback baseline. The other three are intentionally simple, monotone, memoryless ladders. If giveback shrinks, they automatically re-risk; if giveback worsens, they de-risk.

No ladder may be altered after results are seen in this first pass.

## Primary measurements

Per completed known-start Markup / Markdown episode:

- direction-aligned full-hold return in episode-entry ATR units;
- maximum favorable close-path excursion (MFE) in entry ATR units;
- exposure-weighted harvested directional move for each ladder;
- harvested move / MFE for episodes with positive MFE (descriptive capture ratio; may exceed 100% when active de-risk/re-risk avoids pullbacks);
- average exposure and fraction of bars below full exposure;
- total exposure turnover `sum(abs(delta exposure))`, including initial entry and final flattening;
- de-risk transition count and re-risk transition count;
- count of flat -> positive re-entries;
- longest consecutive under-exposed period.

Report all episodes, plus fixed large-trend slices with episode MFE `>=4 ATR` and `>=8 ATR`, matching the already-used discovery landmarks.

## Frontier interpretation

Do not rank candidates by Sharpe or choose a winner from a single scalar score.

The first-pass question is whether a simple progressive ladder can move the frontier in a useful direction:

- retain more directional trend harvest than a permanent early exit;
- surrender less to terminal reversals than Formal Hold;
- keep re-risk / turnover frequency operationally tolerable;
- behave similarly across markets without asset-specific parameters.

A candidate that improves retained trend harvest only by extreme turnover is not automatically better.

## Anti-overfit guardrails

- no new giveback thresholds;
- no search over arbitrary exposure weights;
- no separate long/short ladder optimization;
- no asset-class-specific ladders;
- no stop/target optimization;
- no classifier retuning;
- no selecting only favorable markets or date windows;
- results from this sample remain discovery evidence only.

If one simple ladder looks promising, freeze it before testing new markets / asset classes / weekly data / prospective observations.

Refs #78 and #76.
