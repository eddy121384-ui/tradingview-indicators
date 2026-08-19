# Macro Pressure Map V6.6 — Issue #59 reproducibility contract

Issue #59 uses two classes of artifacts and keeps them deliberately separate.

## 1. Script-generated evidence

These files are direct outputs of the research scripts and should be reproducible from the stated TradingView Pine Logs.

Matched conditional study defaults:

- `research/generated/issue-59-matched-incremental.generated.json`
- `research/generated/issue-59-matched-incremental.generated.md`

The matched script refuses to overwrite the curated files under `research/decisions/`.

Run from `indicators/macro-pressure-map/research/`:

```bash
python matched_incremental_validation.py \
  --parity-log "/path/to/pine-logs-MPM V6.6 PARITY SRC.csv" \
  --ooc-log "/path/to/pine-logs-MPM V6.6 OOC.csv"
```

Input hashes used for the committed Issue #59 evidence:

- parity log SHA-256: `c0220d4974b2fd0154c4cf8f33b4b3effb27a58e21ee96a1b0109011ce638e3d`
- OOC log SHA-256: `192151f5cf90c7ac067ec63b2aad62749c11766fa7775268bb1ee01fd3b39363`

The joint-axis reused-era script is also a generator. It must write exploratory language and an explicit machine-readable status:

`exploratory_reused_era_not_untouched_holdout`

Example:

```bash
python joint_holdout_validation.py \
  --parity-log "/path/to/pine-logs-MPM V6.6 PARITY SRC.csv" \
  --ooc-log "/path/to/pine-logs-MPM V6.6 OOC.csv" \
  --output-json generated/issue-59-joint-exploratory.generated.json \
  --output-md generated/issue-59-joint-exploratory.generated.md
```

The historical filename `joint_holdout_validation.py` is retained to avoid breaking existing references. Its current interpretation is exploratory reused-era analysis, not untouched OOS validation.

## 2. Curated decision artifacts

These files are human-readable synthesis. They may summarize or round generated values, but they are not the serialization contract of the scripts:

- `research/decisions/issue-59-matched-incremental.md`
- `research/decisions/issue-59-matched-incremental.json`
- `research/decisions/issue-59-joint-holdout.md` — historical filename; interpretation is exploratory
- `research/decisions/issue-59-final-verdict.md`

When a curated memo quotes a generated statistic, it should agree with the generated artifact apart from display rounding.

## 3. Evidence boundary

The 2020–2026 era was inspected during earlier Issue #59 diagnostics before the synchronized GPI+IPI hypothesis was selected. It is therefore reused historical evidence and must not be represented as a genuinely untouched holdout.

The matched conditional test also does not demonstrate statistically reliable incremental predictive lift from adding the second axis. The current Issue #59 verdict remains:

`descriptive_but_little_incremental_information`

No V6.6 production weight, threshold, lookback, smoothing rule, regime boundary, or component definition is changed by this reproducibility cleanup.
