# Issue #39 — Hidden Regime research-core assessment

## Decision

The existing Hidden Regime research core is trustworthy enough to begin Issue #40's no-HMM versus HMM trading-utility experiments.

This decision does **not** select a production state count, approve the K=8 candidate, establish identical-input Python-to-Pine parity, or make any profitability claim. It means the causal feature, fitting, inference, alignment, diagnostics, decision, provenance, and validation machinery is sufficiently explicit and auditable to use the existing candidates as research inputs in the next milestone.

## Scope and method

This assessment reviewed the current committed Hidden Regime implementation and the completed contracts in Issues #26, #28, #31, #33, and #35, together with the earlier training, characterization, and Pine-parity work.

Primary evidence includes:

- `research/train_hmm.py`
- `research/characterize_states.py`
- `research/compare_state_counts.py`
- `research/compare_feature_sets.py`
- `research/check_k8_cutoff_stability.py`
- `research/check_k8_restart_sensitivity.py`
- the matching `test_*.py` files
- `models/spy-1d-v0.1.json`
- `pine/hidden-regime-map-spy-parity.pine`
- `research/fixtures/spy-1d-parity-checkpoints.json`
- `research/spy-1d-pine-parity-report.md`
- `research/decisions/issue-35-expanded-restart-cutoff-gate.md`
- `.github/workflows/hidden-regime-market-validation.yml`
- `README.md` and `PROJECT_CHARTER.md`

No new K sweep, feature experiment, restart expansion, threshold change, or Pine productization work was performed.

## Evidence map

| Research-core requirement | Concrete evidence | Assessment |
|---|---|---|
| Causal features and warm-up | `train_hmm.calculate_features()` uses shifted/rolling price history; `compare_feature_sets.calculate_path_features()` uses trailing 20-bar displacement, path length, and downside variance while preserving warm-up NaNs. Formula and zero-denominator tests were added in PR #29. | Verified. No future observation enters a model feature. |
| Chronological train/OOS split | `train_hmm.py` calculates a fixed chronological split and enforces minimum training/OOS row counts. | Verified. |
| Training-only scaling | `StandardScaler.fit_transform()` is applied only to training rows; the fitted scaler then transforms the full sample. The same contract is reused by the comparison pipeline. | Verified. |
| Fitting convergence and deterministic restarts | `compare_state_counts.py` fixes independent seed groups, rejects overlapping attempt sets, retains every successful/failed restart, rejects non-finite and insufficiently converged fits, and selects the highest finite train likelihood deterministically. | Verified. |
| Causal forward filtering and normalization | `train_hmm.forward_filter()` performs log-space alpha recursion and normalizes on every row. The committed profile and parity tests check probability dimensions and row sums. | Verified. |
| State alignment | `compare_state_counts.state_alignment()` uses an emission-distribution cost and Hungarian assignment before state-level comparisons. Raw HMM state IDs are not compared across fits. | Verified. |
| State characterization | `characterize_states.py` separates full/train/OOS descriptions, preserves contradictions, and keeps forward returns/event windows post-fit and diagnostic-only. PRs #20 and #21 added explicit coverage and strict JSON behavior. | Verified. |
| K and feature-set comparison | PR #27 added K=3–8 comparison with worst-seed guardrails. PRs #29 and #30 added exactly three causal feature sets and a symmetric 10% materiality policy. Likelihood alone cannot select a richer model. | Verified. |
| Cutoff and restart sensitivity | PR #32 added five adjacent cutoff checks. PR #34 diagnosed the original three-restart schedule as insufficient at one cutoff. PR #36 repeated nine restarts over all five frozen cutoffs and preserved all 135 attempts. | Verified; the result is a limitation, not a reporting defect. |
| Frozen-input provenance and data drift | The Issue #35 durable decision is tied to Run #58 artifact `hidden-regime-SPY` (`8590548073`) and `ohlc.csv` SHA-256 `016448a0492769c527a8dc8e24d60fbda4c4e0e4bbdbcf27506caf30b76dddc4`. A later live download with tiny historical revisions was rejected as a substitute. | Verified. |
| Python-to-Pine fixed-parameter contract | `spy-1d-v0.1.json`, the Pine v6 forward filter, checkpoint fixture, comparator, tests, and parity report form an auditable fixed-profile contract. | Verified with a formal limitation: the manual cross-platform result is `feed mismatch`, not identical-input parity. |
| Automated validation | `Hidden Regime Market Validation` runs the full unittest discovery in SPY and TLT matrix jobs, then trains, characterizes, and runs SPY feature/K and cutoff diagnostics. | Verified as repository infrastructure. |

## Historical decision chain

### Issue #26 / PR #27 — state-count comparison

The three-feature K=3–8 comparison was intentionally inconclusive. K=7 and K=8 led some fit metrics but failed OOS stability guardrails; the result redirected the work toward feature sufficiency instead of forcing a preferred K.

### Issue #28 / PRs #29 and #30 — feature sufficiency

The five-feature `baseline_er_downside` candidate materially improved normalized separation and occupancy consistency and could select K=8 internally under the corrected symmetric materiality policy. Refreshed data nevertheless exposed a 1.968% OOS state occupancy, so productization remained paused.

### Issue #31 / PR #32 — adjacent cutoffs

The five-feature K=8 candidate passed four of five adjacent cutoffs and failed one rare-state guardrail. The machine outcome was `cutoff_sensitive`.

### Issue #33 / PR #34 — restart diagnosis

An expanded restart sweep recovered a passing solution at the originally failing cutoff, showing that the original three-attempt schedule was insufficient for that one sample. The shared schedule was not changed from this single diagnostic.

### Issue #35 / PR #36 — frozen five-cutoff promotion gate

The nine-attempt schedule was then tested across the same five cutoffs on the hash-verified Run #58 input. The final result remained `cutoff_sensitive_after_expansion`: four of five cutoffs passed, while 2026-07-21 produced 1.9680% minimum OOS occupancy below the unchanged 2% guardrail.

This is credible negative evidence. It shows that the tooling can reject an attractive candidate without threshold relaxation or live-data cherry-picking.

## Verified capabilities

The research core can now:

1. calculate causal observations with explicit warm-up behavior;
2. separate training and OOS data chronologically;
3. fit scaling and HMM parameters on training data only;
4. retain deterministic seed/restart provenance and fitting failures;
5. compute causal, normalized forward-filtered posteriors;
6. align arbitrary HMM state indices before comparing fits;
7. characterize states without feeding ex-post returns or events back into the model;
8. compare K and feature sets with explicit worst-seed guardrails;
9. diagnose cutoff, restart, rare-state, drift, separation, duration, and reproducibility behavior;
10. freeze and checksum decision inputs;
11. expose a fixed-profile Python/Pine comparison contract;
12. preserve negative results and unsupported claims.

## Known limitations

- The five-feature SPY 1D K=8 candidate is not cutoff-stable under the frozen promotion gate. It passed 4/5 cutoffs; the failing cutoff had 1.9680% minimum OOS occupancy.
- The expanded `[0..8]` restart schedule was not promoted. The shared research schedule remains `[0,1,2]`.
- No final production K or production profile has been selected.
- `spy-1d-v0.1` is a K=3 Pine parity reference with `deployment_status: pine-parity-spike-only`; it is not the final market taxonomy.
- Small historical adjusted-OHLC revisions can change the selected local optimum and guardrail result.
- Yahoo-adjusted Python OHLC and TradingView dividend-adjusted OHLC differ. The formal Pine result remains `feed mismatch`; identical-input inference parity is not established.
- The current evidence does not prove HMM trading value, walk-forward profitability, controlled drawdown, or cross-asset generalization.
- Issue #24 remains a bounded indicator prototype rather than production approval.

These limitations affect model selection and product claims, but they do not invalidate the research machinery or prevent Issue #40 from comparing existing defensible candidates against transparent no-HMM baselines.

## Unresolved blockers

None were found in the committed evidence for causal features, chronological scaling, fitting, forward filtering, alignment, metrics, provenance, or deterministic decision output.

A final production K/profile is deliberately **not** required before Issue #40. Trading utility is now part of model selection under the project charter; continuing HMM-internal tuning before that comparison would risk optimizing diagnostics without proving usefulness.

## Issue #40 readiness

`can_start_issue_40 = true`.

Issue #40 should treat current models as research candidates, not approved production profiles. At minimum it should compare:

- a transparent no-HMM baseline;
- the frozen K=3 reference where applicable;
- the five-feature K=8 candidate, with its cutoff/restart limitations carried forward;
- a simpler non-HMM regime filter where useful.

The experiment must preserve chronological OOS separation and must not use the final evaluation set to repair the model after results are observed.

## Validation

Required command:

```bash
python -m unittest discover -s indicators/hidden-regime-map/research -p "test_*.py"
```

The current execution runtime could not obtain a repository checkout because outbound `git clone` access was blocked by its proxy. Therefore no local full-suite pass is claimed.

The Issue #39 Draft PR ran Hidden Regime Market Validation Run #66 (`30343837925`) on head `8e1969dee2cbdb76a06d9e3bceddc26485fc4411` and completed successfully:

- SPY and TLT both passed the `Run Hidden Regime unit tests` step;
- SPY and TLT both passed download, training, characterization, summary, and artifact upload;
- SPY also passed the complete feature-set/state-count comparison and five-cutoff K=8 diagnostic;
- the workflow's final failure gate was skipped because no required research step failed.

The GitHub connector's decoded log view was truncated before the unittest summary line, so the exact test count was not available. No count is inferred or invented; the workflow step conclusions are the durable evidence.

Machine-readable status validation:

```bash
python -m json.tool indicators/hidden-regime-map/research/decisions/issue-39-research-core-status.json
```

The authored JSON was parsed and serialized successfully before upload.

## Final status

`complete_with_known_limitations`
