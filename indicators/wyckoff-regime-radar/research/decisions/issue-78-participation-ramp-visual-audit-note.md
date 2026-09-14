# Issue #78 — Participation Ramp Visual Audit Note

The TradingView research visualizer now includes the two surviving first-pass Participation Ramp candidates.

Default view:

- Participation: `Excursion-Proof`
- Damage management: `Gentle + Latch`
- one final signed target-exposure staircase only;
- component lines hidden by default to reduce clutter.

Selectable Participation modes:

- `Full-at-entry`
- `Persistence`
- `Excursion-Proof`

Selectable Damage modes:

- `Gentle + Latch`
- `Balanced + Latch`

Final next-bar exposure remains:

`min(participation_cap, damage_latch_cap)`

Visual event markers:

- `試`: new formal trend episode / probe start
- `加`: target exposure increases
- `滿`: target first reaches 100%
- `減`: target exposure decreases

Primary manual audit questions:

1. Are 25 -> 50 -> 75 -> 100 upgrades intuitively located on real trend charts?
2. Does Excursion-Proof add materially faster than Persistence on genuinely strong trends?
3. Are there cases where a 0.5 / 1 / 2 ATR proof step visually looks too easy or too late across different markets?
4. Does the damage latch cut exposure at sensible deterioration points after the ramp has built a position?
5. Do re-adds after damage feel operationally tolerable rather than twitchy?
6. Does the same architecture look coherent on both Markup and Markdown without direction-specific tuning?

This is a visual research gate only. No production policy is selected.

Refs #78, #80 and #76.
