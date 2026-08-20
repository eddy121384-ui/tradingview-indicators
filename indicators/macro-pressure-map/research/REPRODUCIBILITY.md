# Macro Pressure Map V6.6 — Issue #59 reproducibility contract

Issue #59 separates **durable repository evidence** from **local script outputs**.

## 1. Durable repository evidence

The committed evidence for review and future reference lives under `research/decisions/`:

- `research/decisions/issue-59-matched-incremental.md`
- `research/decisions/issue-59-matched-incremental.json`
- `research/decisions/issue-59-joint-holdout.md` — historical filename; interpretation is exploratory
- `research/decisions/issue-59-final-verdict.md`

The curated matched JSON preserves the exact point estimates and confidence intervals from the verified rerun used for the final Issue #59 synthesis. The Markdown files are human-readable summaries and may round display values.

## 2. Local script outputs

Research scripts may write local generated files to `research/generated/`, but those outputs are **not committed repository evidence** in PR #60. They are disposable rerun products used to verify that the committed decision artifacts agree with the implementation.

Matched conditional study defaults:

- `research/generated/issue-59-matched-incremental.generated.json`
- `research/generated/issue-59-matched-incremental.generated.md`

The matched script refuses to overwrite curated files under `research/decisions/`.

Run from `indicators/macro-pressure-map/research/`:

```bash
python matched_incremental_validation.py \
  --parity-log "/path/to/pine-logs-MPM V6.6 PARITY SRC.csv" \
  --ooc-log "/path/to/pine-logs-MPM V6.6 OOC.csv"
```

Input hashes used for the verified Issue #59 rerun:

- parity log SHA-256: `c0220d4974b2fd0154c4cf8f33b4b3effb27a58e21ee96a1b0109011ce638e3d`
- OOC log SHA-256: `192151f5cf90c7ac067ec63b2aad62749c11766fa7775268bb1ee01fd3b39363`

The joint-axis reused-era script is also a generator. Its output must use exploratory language and include the machine-readable status:

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

## 3. Verification rule

A rerun is a verification step, not a second source of repository truth:

1. verify the two Pine Log hashes above;
2. rerun the research script;
3. compare event counts, point estimates, and confidence intervals against the committed `research/decisions/` artifacts;
4. if they differ beyond display rounding, update the durable decision artifact and explain why.

This contract avoids two failure modes at once: a generator cannot overwrite the curated synthesis, and documentation does not point reviewers to uncommitted files as if they were repository evidence.

## 4. Evidence boundary

The 2020–2026 era was inspected during earlier Issue #59 diagnostics before the synchronized GPI+IPI hypothesis was selected. It is therefore reused historical evidence and must not be represented as a genuinely untouched holdout.

The matched conditional test also does not demonstrate statistically reliable incremental predictive lift from adding the second axis. The current Issue #59 verdict remains:

`descriptive_but_little_incremental_information`

No V6.6 production weight, threshold, lookback, smoothing rule, regime boundary, or component definition is changed by this reproducibility cleanup.
