#!/usr/bin/env python3
"""Export a deterministic K=6 U.S. rates HMM profile for visual inspection.

This module intentionally creates a descriptive, full-sample reference profile.
Historical classifications are retrospective because the frozen model parameters
are fitted through the profile cutoff. After the profile is frozen, forward
filtering itself is causal and can be reproduced in Pine Script.
"""

from __future__ import annotations

import argparse
import json
import math
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable

import numpy as np
from sklearn.preprocessing import StandardScaler

RESEARCH_DIR = Path(__file__).resolve().parent
if str(RESEARCH_DIR) not in sys.path:
    sys.path.insert(0, str(RESEARCH_DIR))

import compare_state_counts
import evaluate_rates_utility

PROFILE_ID = "us-rates-k6-visual-v0.1"
MODEL_KIND = "descriptive_full_sample_reference"
N_STATES = 6
GROUP_SEEDS = (42, 84, 126)
CHECKPOINT_TARGETS = (
    "2008-09-15",
    "2008-12-16",
    "2013-05-22",
    "2016-07-08",
    "2018-11-08",
    "2019-08-27",
    "2020-03-16",
    "2020-08-04",
    "2022-03-16",
    "2022-10-21",
    "2023-10-19",
    "2026-07-30",
)
DRIFT_MAX_ABS_Z_THRESHOLD = 3.0
CONCENTRATION_WINDOW = 126
CONCENTRATION_THRESHOLD = 0.90
EPSILON = 1e-300


@dataclass(frozen=True)
class AlignedCandidate:
    group_seed: int
    selected_seed: int
    attempts: list[dict[str, Any]]
    model: Any
    permutation_to_reference: list[int]
    parameters: dict[str, np.ndarray]
    train_log_likelihood: float


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Export the Issue #24 U.S. rates K=6 visual reference profile"
    )
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--sha256-file", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    return parser.parse_args()


def strict_json(value: Any) -> Any:
    if isinstance(value, dict):
        return {str(key): strict_json(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [strict_json(item) for item in value]
    if isinstance(value, np.ndarray):
        return strict_json(value.tolist())
    if isinstance(value, np.integer):
        return int(value)
    if isinstance(value, (np.floating, float)):
        number = float(value)
        if not math.isfinite(number):
            raise ValueError("profile contains a non-finite number")
        return number
    return value


def parameter_distance(
    left: dict[str, np.ndarray], right: dict[str, np.ndarray]
) -> float:
    mean_rmse = float(np.sqrt(np.mean((left["means"] - right["means"]) ** 2)))
    log_variance_rmse = float(
        np.sqrt(
            np.mean(
                (
                    np.log(np.maximum(left["variances"], 1e-12))
                    - np.log(np.maximum(right["variances"], 1e-12))
                )
                ** 2
            )
        )
    )
    transition_rmse = float(
        np.sqrt(np.mean((left["transition"] - right["transition"]) ** 2))
    )
    start_rmse = float(
        np.sqrt(
            np.mean(
                (left["start_probability"] - right["start_probability"]) ** 2
            )
        )
    )
    return mean_rmse + 0.5 * log_variance_rmse + transition_rmse + 0.25 * start_rmse


def medoid_index(parameter_sets: list[dict[str, np.ndarray]]) -> tuple[int, list[float]]:
    if not parameter_sets:
        raise ValueError("at least one parameter set is required")
    totals = [
        sum(parameter_distance(left, right) for right in parameter_sets)
        for left in parameter_sets
    ]
    index = min(range(len(totals)), key=lambda item: (totals[item], item))
    return index, totals


def risk_scores(means: np.ndarray) -> np.ndarray:
    feature_names = evaluate_rates_utility.FEATURE_NAMES
    change_index = feature_names.index("level_change_bp")
    vol_index = feature_names.index("level_vol_20_bp")
    return means[:, change_index] + 0.75 * means[:, vol_index]


def economic_state_order(means: np.ndarray) -> list[int]:
    if means.shape != (N_STATES, len(evaluate_rates_utility.FEATURE_NAMES)):
        raise ValueError("emission means do not match the K=6 rates feature contract")
    scores = risk_scores(means)
    level_index = evaluate_rates_utility.FEATURE_NAMES.index("curve_level")
    slope_2s10s_index = evaluate_rates_utility.FEATURE_NAMES.index("slope_2s10s")
    slope_5s30s_index = evaluate_rates_utility.FEATURE_NAMES.index("slope_5s30s")
    return sorted(
        range(N_STATES),
        key=lambda state: (
            float(scores[state]),
            float(means[state, level_index]),
            float(means[state, slope_2s10s_index]),
            float(means[state, slope_5s30s_index]),
            state,
        ),
    )


def reorder_parameters(
    parameters: dict[str, np.ndarray], order: Iterable[int]
) -> dict[str, np.ndarray]:
    indices = np.asarray(list(order), dtype=int)
    if sorted(indices.tolist()) != list(range(N_STATES)):
        raise ValueError("state order must be a complete K=6 permutation")
    return {
        "means": np.asarray(parameters["means"], dtype=float)[indices],
        "variances": np.asarray(parameters["variances"], dtype=float)[indices],
        "transition": np.asarray(parameters["transition"], dtype=float)[
            np.ix_(indices, indices)
        ],
        "start_probability": np.asarray(
            parameters["start_probability"], dtype=float
        )[indices],
    }


def validate_parameters(parameters: dict[str, np.ndarray]) -> None:
    means = np.asarray(parameters["means"], dtype=float)
    variances = np.asarray(parameters["variances"], dtype=float)
    transition = np.asarray(parameters["transition"], dtype=float)
    start = np.asarray(parameters["start_probability"], dtype=float)
    expected_features = len(evaluate_rates_utility.FEATURE_NAMES)
    if means.shape != (N_STATES, expected_features):
        raise ValueError("invalid emission-mean dimensions")
    if variances.shape != means.shape:
        raise ValueError("invalid emission-variance dimensions")
    if transition.shape != (N_STATES, N_STATES):
        raise ValueError("invalid transition dimensions")
    if start.shape != (N_STATES,):
        raise ValueError("invalid start-probability dimensions")
    if not np.isfinite(means).all() or not np.isfinite(variances).all():
        raise ValueError("emission parameters must be finite")
    if (variances <= 0.0).any():
        raise ValueError("emission variances must be positive")
    if (transition < 0.0).any() or not np.isfinite(transition).all():
        raise ValueError("transition probabilities must be finite and non-negative")
    if (start < 0.0).any() or not np.isfinite(start).all():
        raise ValueError("start probabilities must be finite and non-negative")
    if not np.allclose(transition.sum(axis=1), 1.0, atol=1e-10):
        raise ValueError("transition rows must sum to one")
    if not np.isclose(start.sum(), 1.0, atol=1e-10):
        raise ValueError("start probabilities must sum to one")


def logsumexp(values: np.ndarray, axis: int) -> np.ndarray:
    maximum = np.max(values, axis=axis, keepdims=True)
    return np.squeeze(
        maximum
        + np.log(np.sum(np.exp(values - maximum), axis=axis, keepdims=True)),
        axis=axis,
    )


def forward_filter_params(
    matrix: np.ndarray, parameters: dict[str, np.ndarray]
) -> np.ndarray:
    validate_parameters(parameters)
    means = parameters["means"]
    variances = parameters["variances"]
    transition = np.clip(parameters["transition"], EPSILON, 1.0)
    start = np.clip(parameters["start_probability"], EPSILON, 1.0)
    difference = matrix[:, None, :] - means[None, :, :]
    log_emission = -0.5 * (
        np.sum(np.log(2.0 * np.pi * variances), axis=1)[None, :]
        + np.sum((difference * difference) / variances[None, :, :], axis=2)
    )
    posterior = np.empty((len(matrix), N_STATES), dtype=float)
    log_alpha = np.log(start) + log_emission[0]
    log_alpha -= logsumexp(log_alpha, axis=0)
    posterior[0] = np.exp(log_alpha)
    log_transition = np.log(transition)
    for index in range(1, len(matrix)):
        log_prior = logsumexp(log_alpha[:, None] + log_transition, axis=0)
        log_alpha = log_prior + log_emission[index]
        log_alpha -= logsumexp(log_alpha, axis=0)
        posterior[index] = np.exp(log_alpha)
    if not np.allclose(posterior.sum(axis=1), 1.0, atol=1e-10):
        raise RuntimeError("posterior probabilities do not sum to one")
    return posterior


def run_lengths(states: np.ndarray) -> list[list[int]]:
    result: list[list[int]] = [[] for _ in range(N_STATES)]
    if not len(states):
        return result
    start = 0
    for index in range(1, len(states) + 1):
        if index == len(states) or states[index] != states[start]:
            result[int(states[start])].append(index - start)
            start = index
    return result


def weighted_feature_means(matrix: np.ndarray, posterior: np.ndarray) -> list[list[float]]:
    return [
        np.average(matrix, axis=0, weights=posterior[:, state])
        .astype(float)
        .tolist()
        for state in range(N_STATES)
    ]


def nearest_checkpoint_indices(dates: np.ndarray) -> list[dict[str, Any]]:
    day_values = np.asarray(dates, dtype="datetime64[D]")
    result = []
    for target_text in CHECKPOINT_TARGETS:
        target = np.datetime64(target_text)
        distance = np.abs((day_values - target).astype("timedelta64[D]").astype(int))
        index = int(np.argmin(distance))
        result.append(
            {
                "requested_date": target_text,
                "actual_date": str(day_values[index]),
                "index": index,
                "calendar_distance_days": int(distance[index]),
            }
        )
    return result


def fit_candidates(matrix: np.ndarray) -> tuple[list[AlignedCandidate], dict[str, Any]]:
    raw_models = []
    raw_records = []
    for group_seed in GROUP_SEEDS:
        model, attempts, selected_seed = compare_state_counts.fit_seed_group(
            matrix, N_STATES, group_seed
        )
        raw_models.append(model)
        raw_records.append((group_seed, selected_seed, attempts))

    reference = raw_models[0]
    candidates = []
    for model, (group_seed, selected_seed, attempts) in zip(raw_models, raw_records):
        permutation = compare_state_counts.state_alignment(reference, model)
        parameters = compare_state_counts.aligned_parameters(model, permutation)
        candidates.append(
            AlignedCandidate(
                group_seed=group_seed,
                selected_seed=selected_seed,
                attempts=attempts,
                model=model,
                permutation_to_reference=permutation,
                parameters=parameters,
                train_log_likelihood=float(model.score(matrix)),
            )
        )

    medoid, distance_totals = medoid_index(
        [candidate.parameters for candidate in candidates]
    )
    diagnostics = {
        "medoid_index": medoid,
        "group_seeds": list(GROUP_SEEDS),
        "restart_offsets": list(compare_state_counts.RESTART_OFFSETS),
        "reference_group_seed": candidates[0].group_seed,
        "representative_rule": (
            "medoid of the three group-best actual fitted models after state alignment; "
            "distance combines emission means, log variances, transition matrix, and start probabilities"
        ),
        "representative_group_seed": candidates[medoid].group_seed,
        "representative_selected_seed": candidates[medoid].selected_seed,
        "distance_totals": distance_totals,
        "candidates": [
            {
                "group_seed": candidate.group_seed,
                "selected_seed": candidate.selected_seed,
                "train_log_likelihood": candidate.train_log_likelihood,
                "permutation_to_reference": candidate.permutation_to_reference,
                "attempts": candidate.attempts,
            }
            for candidate in candidates
        ],
    }
    return candidates, diagnostics


def build_profile(
    input_path: Path, sha_path: Path
) -> tuple[dict[str, Any], dict[str, Any], str]:
    raw, input_sha = evaluate_rates_utility.load_frozen_input(input_path, sha_path)
    panel = evaluate_rates_utility.prepare_panel(raw)
    feature_names = list(evaluate_rates_utility.FEATURE_NAMES)
    scaler = StandardScaler()
    matrix = scaler.fit_transform(panel[feature_names])
    candidates, selection = fit_candidates(matrix)
    medoid = int(selection.pop("medoid_index"))
    representative = candidates[medoid]
    final_order = economic_state_order(representative.parameters["means"])
    parameters = reorder_parameters(representative.parameters, final_order)
    validate_parameters(parameters)
    posterior = forward_filter_params(matrix, parameters)
    dominant = posterior.argmax(axis=1)
    lengths = run_lengths(dominant)
    feature_matrix = panel[feature_names].to_numpy(dtype=float)
    occupancy = np.bincount(dominant, minlength=N_STATES) / len(dominant)
    state_means_raw = weighted_feature_means(feature_matrix, posterior)
    state_means_scaled = weighted_feature_means(matrix, posterior)
    max_abs_z = np.max(np.abs(matrix), axis=1)
    rolling_shares = np.column_stack(
        [
            np.convolve(
                (dominant == state).astype(float),
                np.ones(CONCENTRATION_WINDOW) / CONCENTRATION_WINDOW,
                mode="valid",
            )
            for state in range(N_STATES)
        ]
    )
    rolling_concentration = rolling_shares.max(axis=1)

    checkpoint_rows = []
    for checkpoint in nearest_checkpoint_indices(panel["Date"].to_numpy()):
        index = checkpoint["index"]
        probs = posterior[index]
        checkpoint_rows.append(
            {
                **checkpoint,
                "features": {
                    name: float(panel.iloc[index][name]) for name in feature_names
                },
                "scaled_features": matrix[index].astype(float).tolist(),
                "posterior": probs.astype(float).tolist(),
                "probability_sum": float(probs.sum()),
                "dominant_state": f"R{int(dominant[index]) + 1}",
                "max_abs_feature_z": float(max_abs_z[index]),
            }
        )

    state_rows = []
    final_scores = risk_scores(parameters["means"])
    for state in range(N_STATES):
        state_rows.append(
            {
                "state": f"R{state + 1}",
                "state_index": state,
                "ordering_score": float(final_scores[state]),
                "occupancy_full_sample": float(occupancy[state]),
                "mean_duration_bars": float(np.mean(lengths[state])) if lengths[state] else 0.0,
                "median_duration_bars": float(np.median(lengths[state])) if lengths[state] else 0.0,
                "self_transition_probability": float(parameters["transition"][state, state]),
                "posterior_weighted_feature_mean_raw": state_means_raw[state],
                "posterior_weighted_feature_mean_scaled": state_means_scaled[state],
            }
        )

    profile = {
        "schema_version": 1,
        "profile_id": PROFILE_ID,
        "deployment_status": "visual-inspection-prototype",
        "model_kind": MODEL_KIND,
        "instrument_family": "U.S. Treasury constant-maturity yield curve",
        "supported_timeframe": "1D",
        "chart_reference": "FRED:DGS10",
        "requested_symbols": {
            "DGS2": "FRED:DGS2",
            "DGS5": "FRED:DGS5",
            "DGS10": "FRED:DGS10",
            "DGS30": "FRED:DGS30",
        },
        "provenance": {
            "source_issue": 50,
            "source_pr": 52,
            "frozen_input": str(input_path),
            "decompressed_sha256": input_sha,
            "raw_first_date": str(raw["Date"].iloc[0].date()),
            "raw_last_date": str(raw["Date"].iloc[-1].date()),
            "feature_first_date": str(panel["Date"].iloc[0].date()),
            "feature_last_date": str(panel["Date"].iloc[-1].date()),
            "rows": int(len(panel)),
            "fit_scope": "all frozen feature rows through cutoff",
            "historical_classification": "retrospective_in_sample_description",
            "forward_use_boundary": (
                "fixed parameters are causal only after the profile cutoff; historical colors are not OOS evidence"
            ),
        },
        "feature_names": feature_names,
        "feature_contract": {
            "curve_level": "mean(DGS2, DGS5, DGS10, DGS30), percent",
            "slope_2s10s": "DGS10 - DGS2, percentage points",
            "slope_5s30s": "DGS30 - DGS5, percentage points",
            "level_change_bp": "100 * change(curve_level), basis points",
            "level_vol_20_bp": "population standard deviation of level_change_bp over 20 observed common dates",
            "join": "inner common observed dates; no interpolation in the frozen Python profile",
        },
        "scaler": {
            "fit_scope": "full frozen descriptive sample",
            "mean": scaler.mean_.astype(float).tolist(),
            "scale": scaler.scale_.astype(float).tolist(),
        },
        "selection": selection,
        "state_ordering": {
            "rule": (
                "ascending standardized level_change_bp + 0.75 * standardized level_vol_20_bp; "
                "ties use curve level, 2s10s, 5s30s, then original aligned index"
            ),
            "representative_to_final_order": final_order,
            "state_names": [f"R{state + 1}" for state in range(N_STATES)],
            "semantic_labels_frozen": False,
        },
        "hmm": {
            "state_count": N_STATES,
            "covariance_type": "diag",
            "start_probability": parameters["start_probability"].astype(float).tolist(),
            "transition_matrix": parameters["transition"].astype(float).tolist(),
            "emission_means": parameters["means"].astype(float).tolist(),
            "emission_variances": parameters["variances"].astype(float).tolist(),
            "transition_orientation": "previous_state_row_to_current_state_column",
        },
        "state_diagnostics": state_rows,
        "instability_diagnostics": {
            "feature_drift_statistic": "maximum absolute standardized feature value on the current bar",
            "feature_drift_threshold": DRIFT_MAX_ABS_Z_THRESHOLD,
            "feature_drift_threshold_status": "prototype diagnostic; not a universal statistical law",
            "state_concentration_window_bars": CONCENTRATION_WINDOW,
            "state_concentration_statistic": "maximum rolling dominant-state share across R1-R6",
            "state_concentration_threshold": CONCENTRATION_THRESHOLD,
            "state_concentration_threshold_status": "prototype diagnostic; not a universal statistical law",
            "latest_max_abs_feature_z": float(max_abs_z[-1]),
            "latest_rolling_state_concentration": float(rolling_concentration[-1]),
            "max_rolling_state_concentration": float(rolling_concentration.max()),
        },
        "constraints": {
            "pine_training": False,
            "automatic_refit": False,
            "historical_oos_claim": False,
            "trading_signal_claim": False,
            "strategy_or_pnl_claim": False,
            "semantic_regime_claim": False,
        },
    }
    fixture = {
        "schema_version": 1,
        "fixture_id": f"{PROFILE_ID}-checkpoints",
        "profile_id": PROFILE_ID,
        "input_sha256": input_sha,
        "checkpoints": checkpoint_rows,
    }
    report = markdown_report(profile)
    return strict_json(profile), strict_json(fixture), report


def markdown_report(profile: dict[str, Any]) -> str:
    lines = [
        "# U.S. Rates K=6 visual-reference profile",
        "",
        f"- Profile: `{profile['profile_id']}`",
        f"- Model kind: `{profile['model_kind']}`",
        f"- Frozen input SHA-256: `{profile['provenance']['decompressed_sha256']}`",
        f"- Feature rows: {profile['provenance']['rows']}",
        f"- Feature period: {profile['provenance']['feature_first_date']} through {profile['provenance']['feature_last_date']}",
        f"- Representative seed: {profile['selection']['representative_selected_seed']}",
        "",
        "This is a full-sample descriptive profile for chart inspection. Historical state colors are retrospective and are not out-of-sample evidence.",
        "",
        "| State | Occupancy | Mean duration | Self-transition | Ordering score |",
        "|---|---:|---:|---:|---:|",
    ]
    for row in profile["state_diagnostics"]:
        lines.append(
            f"| {row['state']} | {row['occupancy_full_sample']:.2%} | "
            f"{row['mean_duration_bars']:.2f} | "
            f"{row['self_transition_probability']:.4f} | "
            f"{row['ordering_score']:.4f} |"
        )
    lines += [
        "",
        "## Instability diagnostics",
        "",
        f"- Feature drift warning: max absolute feature z-score >= {profile['instability_diagnostics']['feature_drift_threshold']:.1f}.",
        f"- State concentration warning: max {profile['instability_diagnostics']['state_concentration_window_bars']}-bar dominant-state share >= {profile['instability_diagnostics']['state_concentration_threshold']:.0%}.",
        "- Both thresholds are prototype diagnostics, not universal statistical laws.",
        "",
    ]
    return "\n".join(lines)


def main() -> int:
    args = parse_args()
    profile, fixture, report = build_profile(args.input, args.sha256_file)
    args.output_dir.mkdir(parents=True, exist_ok=True)
    (args.output_dir / "us-rates-k6-visual-v0.1.json").write_text(
        json.dumps(profile, indent=2, ensure_ascii=False, allow_nan=False) + "\n",
        encoding="utf-8",
    )
    (args.output_dir / "us-rates-k6-visual-v0.1-checkpoints.json").write_text(
        json.dumps(fixture, indent=2, ensure_ascii=False, allow_nan=False) + "\n",
        encoding="utf-8",
    )
    (args.output_dir / "us-rates-k6-visual-v0.1.md").write_text(
        report, encoding="utf-8"
    )
    print(report, end="")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (FileNotFoundError, ValueError, RuntimeError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        raise SystemExit(2)
