# Issue #57 — Transition Health independent OOS freeze

Status: **FROZEN BEFORE NEW-DATA OUTCOME OBSERVATION**

This note freezes the first independent validation of the reused-data Transition Health candidate discovered in Issue #57.

## Frozen signal

At a bridge handoff onset, the carried stage has already taken a strict lead over the old context stage.

The candidate is **Healthy Transition** only if the carried stage keeps a strict lead over the old context stage on every bar from handoff onset through bar +3.

No other condition is allowed:

- no Top2-strength threshold;
- no companion-stage requirement;
- no Formal-state filter;
- no price/trend filter;
- no retake-severity threshold;
- no post-+3 rescue/reseizure rule.

The signal is observed at the **+3 close**. All price outcomes start from that close.

## Frozen independent sample

Use five FX pairs that do not appear in the Issue #55 / Issue #57 development set and do not appear elsewhere in this repository search at freeze time:

- NZDUSD (`NZDUSD=X`)
- EURGBP (`EURGBP=X`)
- GBPJPY (`GBPJPY=X`)
- AUDJPY (`AUDJPY=X`)
- CADJPY (`CADJPY=X`)

Evaluation era: **2022-01-01 through the latest complete daily bar available at the data-freeze run, capped at 2026-08-14**.

A deterministic CSV snapshot plus SHA-256 manifest must be committed before the result is interpreted as evidence. The downloader may fetch earlier warmup history, but scored events must have their +3 observation date on or after 2022-01-01.

## Frozen outcomes

Evaluate subsequent direction-aligned price behavior from the +3 close over:

- 5 bars
- 10 bars
- 20 bars

For Healthy Transition and Damaged Transition (an old-context retake occurred by +3), report:

- aligned return;
- hit rate;
- aligned MFE;
- aligned MAE;
- MFE minus MAE;
- per-pair event counts and consistency.

The previously observed 10-bar development result is **not** promoted to a special OOS horizon. All 5/10/20 horizons remain co-primary descriptive checks.

## Decision discipline

This run is confirmatory for the frozen Transition Health candidate only.

- Do not change the signal after seeing this sample.
- Do not drop weak pairs.
- Do not tune +1/+2/+4/+5 checkpoints.
- Do not add thresholds to rescue the result.
- If the new sample does not reproduce the development pattern, record the negative result.

The existing v0.6 indicator remains unchanged until this validation is read.
