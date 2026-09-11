# Issue #78 — TradingView Trend Hold Lab Visualizer

A research-only TradingView visualizer is now generated from the exact frozen Issue #68 RC classifier source. It does not change classifier semantics.

Generated Pine:

`indicators/wyckoff-regime-radar/research/generated/wyckoff-issue78-trend-hold-visualizer.pine`

Purpose: make the current Issue #78 discovery architecture visible directly on charts instead of only in reports.

## What it shows

- the original formal regime background / classifier context;
- signed next-bar target exposure for the preregistered **Gentle + Damage Latch** and **Balanced + Damage Latch** candidates;
- positive exposure for Markup, negative exposure for Markdown, zero for non-primary trend regimes;
- regime age in bars;
- giveback from the current regime favorable close-path extreme in episode-entry ATR units;
- current trend-health bucket using the frozen discovery landmarks `<0.5 / 0.5–1 / 1–2 / 2–4 / 4+ ATR`;
- de-risk markers;
- re-risk markers when the damage latch is released after a new favorable close-path extreme;
- a bottom-right research panel summarizing the live state.

The original large classifier dashboard defaults off in this research build so the Issue #78 panel is easier to inspect; it can still be re-enabled from settings.

## Causal convention

The exposure shown on bar `t` is the target for the next move `t -> t+1`. A bar cannot retroactively receive the exposure decision created by its own close.

Damage-latch recovery follows the preregistered rule: deterioration can reduce exposure immediately; reduced exposure does not automatically increase just because giveback improves. Full exposure is restored only after the still-active formal trend prints a new favorable close-path extreme.

## Important status

This is a **research visualizer, not a production signal**. Gentle and Balanced are discovery candidates, not selected policy. Participation-ramp research is still unresolved and is intentionally not smuggled into this visualizer.

Manual TradingView compile / visual smoke remains the next gate because GitHub static checks cannot compile Pine Script.

Refs #78, #80 and #76.
