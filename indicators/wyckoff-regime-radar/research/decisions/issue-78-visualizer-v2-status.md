# Issue #78 — Visualizer v2 Status

Status: generated and static-contract checked on `research/issue-78-trend-capture-frontier`.

Generated Pine:

`indicators/wyckoff-regime-radar/research/generated/wyckoff-issue78-trend-hold-visualizer.pine`

The build now visualizes the complete discovery lifecycle:

`Probe -> Build -> Confirmed -> Full -> De-risk -> Re-risk -> Flat`

Default UI intentionally uses a single final target-exposure staircase to reduce clutter. Participation and Damage component lines are optional.

The GitHub generation workflow successfully regenerated the Pine after the Participation Ramp update, which means generator syntax, frozen-source lineage checks, static string contracts and `git diff --check` passed. TradingView Pine compile remains a manual gate.

No production policy selected.
