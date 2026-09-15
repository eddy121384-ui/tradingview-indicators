# Issue #78 — TradingView Position Lifecycle Visualizer

A research-only TradingView visualizer is generated mechanically from the exact frozen Issue #68 RC classifier source. It does not change classifier semantics.

Generated Pine:

`indicators/wyckoff-regime-radar/research/generated/wyckoff-issue78-trend-hold-visualizer.pine`

Purpose: make the current Issue #78 position-lifecycle architecture visible directly on charts instead of only in reports.

## Default view

The visualizer is intentionally simplified after the first comparison build became too cluttered.

By default it shows one signed **final next-bar target exposure** line only. The original classifier dashboard defaults off, and component lines are optional.

Positive exposure = Markup / long-direction target.
Negative exposure = Markdown / short-direction target.
Zero = no primary trend exposure.

Event markers:

- `試` = a new formal trend episode starts with the ramp's initial probe exposure;
- `加` = final target exposure increases;
- `滿` = final target exposure first reaches 100%;
- `減` = final target exposure decreases.

## Participation Ramp selector

Three modes are available for visual comparison:

### Full-at-entry

100% participation cap from the first formal trend bar. This is the original baseline.

### Persistence

Frozen discovery ramp:

- age 0–4: 25%
- age 5–9: 50%
- age 10–19: 75%
- age 20+: 100%

### Excursion-Proof

Frozen discovery ramp:

- favorable excursion <0.5 entry ATR: 25%
- >=0.5 ATR: 50%
- >=1 ATR: 75%
- >=2 ATR: 100%

The ramp only increases its participation cap during an active formal trend episode.

## Damage selector

Choose either the already-frozen:

- Gentle + Damage Latch
- Balanced + Damage Latch

Damage deterioration can lower the damage cap immediately. A reduced damage latch returns toward Full only after the active formal trend prints a new favorable close-path extreme.

## Final target

The actual next-bar exposure is:

`min(participation_cap, damage_latch_cap)`

This makes the full lifecycle visible:

`Probe -> Build -> Confirmed -> Full -> De-risk -> Re-risk -> Flat`

The bottom-right panel shows:

- formal trend direction;
- regime age and favorable MFE from entry;
- current trend-health bucket;
- current participation state;
- current damage cap;
- final signed next-bar target exposure;
- selected ramp x damage architecture.

Optional component lines can be enabled to inspect the participation cap and damage cap separately.

## Causal convention

The exposure shown on bar `t` is the target for the next move `t -> t+1`. A bar cannot retroactively receive the exposure decision created by its own close.

## Important status

This is a **research visualizer, not a production signal**.

Persistence and Excursion-Proof are the two discovery survivors from the first Participation Ramp pass. Neither is selected as production policy. The current nine-market sample is in-sample discovery evidence; any selected architecture still requires new-market / weekly / prospective validation.

GitHub generation and static contract checks pass before the generated Pine is committed. Manual TradingView compile / visual smoke remains required because GitHub cannot compile Pine Script.

Refs #78, #80 and #76.
