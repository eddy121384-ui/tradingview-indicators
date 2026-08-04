# U.S. Rates K=6 visual-profile workflow

This directory contains the deterministic generation path for Issue #24.

1. `export_rates_k6_visual.py` verifies the frozen Issue #50 rates input, calculates the declared five curve features, fits the three deterministic K=6 restart groups, aligns them, selects one actual fitted medoid model, orders the states deterministically, and writes the versioned profile, checkpoint fixture, and report.
2. `generate_rates_k6_pine.py` validates the profile dimensions and writes the Pine v6 visual prototype with the exact frozen parameters.
3. `hidden-regime-rates-k6-visual.yml` reproduces both outputs and uploads them as an artifact.

The initial profile is deliberately fitted on the full frozen sample through July 2026 so the human-inspection chart includes both pre-2022 and post-2022 rate environments. Historical regime colors are therefore retrospective in-sample descriptions, not historical OOS evidence.

Do not hand-edit generated model parameters or Pine parameter arrays. Change the declared fitting, ordering, or visualization contract in the source and regenerate instead.
