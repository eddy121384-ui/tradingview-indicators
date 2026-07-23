#!/usr/bin/env python3
"""Compare deterministic diagonal-Gaussian HMM candidates from K=3 through K=8.

The comparison is research-only.  It preserves the existing features and
chronological split, and uses causal posteriors for state diagnostics.  State
labels are aligned by emission distributions before reproducibility metrics are
calculated; raw hmmlearn state indices are never compared between fits.
"""

from __future__ import annotations

import argparse
import json
import math
import sys
from dataclasses import asdict
from pathlib import Path
from typing import Any, Iterable

import numpy as np
from hmmlearn.hmm import GaussianHMM
from scipy.optimize import linear_sum_assignment
from sklearn.preprocessing import StandardScaler

RESEARCH_DIR = Path(__file__).resolve().parent
if str(RESEARCH_DIR) not in sys.path:
    sys.path.insert(0, str(RESEARCH_DIR))
import train_hmm

DEFAULT_STATE_COUNTS = tuple(range(3, 9))
DEFAULT_SEEDS = (42, 84, 126)
RARE_STATE_THRESHOLD = 0.02
MAX_LIKELIHOOD_DRIFT = 1.0
MAX_OCCUPANCY_DRIFT = 0.50
MAX_FEATURE_MEAN_DRIFT = 1.0
MIN_PAIRWISE_SEPARATION = 1.0
MIN_OOS_MEAN_DURATION = 1.50
MAX_OOS_SINGLE_BAR_SHARE = 0.75
MAX_EMISSION_MEAN_RMSE = 0.50
MAX_TRANSITION_RMSE = 0.15
MAX_OOS_OCCUPANCY_RMSE = 0.10
NEGATIVE_CONVERGENCE_DELTA_TOLERANCE = 1e-6


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Compare SPY 1D HMM state counts K=3..8")
    parser.add_argument("--input", type=Path, required=True, help="chronological SPY OHLC CSV")
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--date-column", default="Date")
    parser.add_argument("--open-column", default="Open")
    parser.add_argument("--high-column", default="High")
    parser.add_argument("--low-column", default="Low")
    parser.add_argument("--close-column", default="Close")
    parser.add_argument("--symbol", default="SPY")
    parser.add_argument("--timeframe", default="1D")
    parser.add_argument("--train-fraction", type=float, default=0.80)
    parser.add_argument("--seeds", type=int, nargs="+", default=list(DEFAULT_SEEDS))
    return parser.parse_args()


def candidate_state_counts(start: int = 3, stop: int = 8) -> list[int]:
    if start < 2 or stop < start:
        raise ValueError("state-count range must satisfy 2 <= start <= stop")
    return list(range(start, stop + 1))


def fit_candidate(matrix: np.ndarray, n_states: int, seed: int) -> GaussianHMM:
    model = GaussianHMM(
        n_components=n_states,
        covariance_type="diag",
        n_iter=500,
        tol=1e-4,
        random_state=seed,
        algorithm="viterbi",
        implementation="log",
    )
    model.fit(matrix)
    if not model.monitor_.converged:
        raise RuntimeError("HMM fit did not converge")
    history = list(model.monitor_.history)
    likelihood_delta = history[-1] - history[-2] if len(history) >= 2 else 0.0
    if likelihood_delta < -NEGATIVE_CONVERGENCE_DELTA_TOLERANCE:
        raise RuntimeError(
            "HMM convergence reported a negative likelihood delta: "
            f"{likelihood_delta:.12g}"
        )
    score = float(model.score(matrix))
    if not np.isfinite(score):
        raise RuntimeError("non-finite train log likelihood")
    return model


def variances(model: GaussianHMM) -> np.ndarray:
    value = np.asarray(model.covars_, dtype=float)
    return np.diagonal(value, axis1=1, axis2=2) if value.ndim == 3 else value


def alignment_cost(reference: GaussianHMM, candidate: GaussianHMM) -> np.ndarray:
    """Symmetric diagonal-Gaussian distance used only to resolve label switching."""
    ref_var, cand_var = variances(reference), variances(candidate)
    delta = reference.means_[:, None, :] - candidate.means_[None, :, :]
    scale = 0.5 * (ref_var[:, None, :] + cand_var[None, :, :])
    mean_term = np.sum(delta * delta / scale, axis=2)
    variance_term = np.sum(
        np.abs(np.log(ref_var[:, None, :] / cand_var[None, :, :])), axis=2
    )
    return mean_term + variance_term


def state_alignment(reference: GaussianHMM, candidate: GaussianHMM) -> list[int]:
    if reference.n_components != candidate.n_components:
        raise ValueError("state alignment requires equal state counts")
    reference_rows, candidate_columns = linear_sum_assignment(
        alignment_cost(reference, candidate)
    )
    permutation = np.empty(reference.n_components, dtype=int)
    permutation[reference_rows] = candidate_columns
    return permutation.tolist()


def aligned_parameters(model: GaussianHMM, permutation: Iterable[int]) -> dict[str, np.ndarray]:
    order = np.asarray(list(permutation), dtype=int)
    if sorted(order.tolist()) != list(range(model.n_components)):
        raise ValueError("alignment must be a complete state permutation")
    return {
        "means": np.asarray(model.means_)[order],
        "variances": variances(model)[order],
        "transition": np.asarray(model.transmat_)[np.ix_(order, order)],
        "start_probability": np.asarray(model.startprob_)[order],
    }


def run_lengths(states: np.ndarray, n_states: int) -> list[list[int]]:
    result: list[list[int]] = [[] for _ in range(n_states)]
    if not len(states):
        return result
    start = 0
    for index in range(1, len(states) + 1):
        if index == len(states) or states[index] != states[start]:
            result[int(states[start])].append(index - start)
            start = index
    return result


def state_feature_means(
    matrix: np.ndarray, posterior: np.ndarray
) -> list[list[float] | None]:
    result: list[list[float] | None] = []
    for state in range(posterior.shape[1]):
        weights = posterior[:, state]
        total = float(weights.sum())
        result.append(
            np.average(matrix, axis=0, weights=weights).tolist()
            if total > 0.0
            else None
        )
    return result


def single_bar_shares(lengths: list[list[int]]) -> list[float]:
    return [
        float(np.mean(np.asarray(state_lengths) == 1)) if state_lengths else 1.0
        for state_lengths in lengths
    ]


def minimum_pairwise_separation(model: GaussianHMM) -> float:
    """Minimum symmetric Mahalanobis separation between emission means."""
    model_variances = variances(model)
    distances = []
    for left in range(model.n_components):
        for right in range(left + 1, model.n_components):
            pooled = 0.5 * (model_variances[left] + model_variances[right])
            delta = model.means_[left] - model.means_[right]
            distances.append(float(np.sqrt(np.sum(delta * delta / pooled))))
    return min(distances)


def information_criteria(log_likelihood: float, rows: int, states: int, features: int) -> tuple[float, float]:
    parameters = (states - 1) + states * (states - 1) + 2 * states * features
    aic = 2 * parameters - 2 * log_likelihood
    bic = math.log(rows) * parameters - 2 * log_likelihood
    return float(aic), float(bic)


def fit_metrics(
    model: GaussianHMM,
    full_matrix: np.ndarray,
    train_rows: int,
    seed: int,
    observation_matrix: np.ndarray | None = None,
) -> dict[str, Any]:
    train = full_matrix[:train_rows]
    oos = full_matrix[train_rows:]
    train_ll = float(model.score(train))
    # Difference of forward likelihoods conditions OOS on the chronological
    # training history instead of restarting the chain at the split boundary.
    full_ll = float(model.score(full_matrix))
    oos_ll = full_ll - train_ll
    if not np.isfinite([train_ll, full_ll, oos_ll]).all():
        raise RuntimeError("train or OOS log likelihood is non-finite")
    aic, bic = information_criteria(train_ll, len(train), model.n_components, train.shape[1])
    posterior = train_hmm.forward_filter(model, full_matrix)
    observations = full_matrix if observation_matrix is None else observation_matrix
    if observations.shape != full_matrix.shape:
        raise ValueError("observation matrix must match the scaled feature matrix")
    dominant = posterior.argmax(axis=1)
    durations_train = run_lengths(dominant[:train_rows], model.n_components)
    durations_oos = run_lengths(dominant[train_rows:], model.n_components)
    occupancy_train = np.bincount(dominant[:train_rows], minlength=model.n_components) / train_rows
    occupancy_oos = np.bincount(dominant[train_rows:], minlength=model.n_components) / len(oos)
    feature_means_train = state_feature_means(
        observations[:train_rows], posterior[:train_rows]
    )
    feature_means_oos = state_feature_means(
        observations[train_rows:], posterior[train_rows:]
    )
    return {
        "seed": seed,
        "converged": bool(model.monitor_.converged),
        "iterations": int(model.monitor_.iter),
        "final_likelihood_delta": (
            float(model.monitor_.history[-1] - model.monitor_.history[-2])
            if len(model.monitor_.history) >= 2
            else 0.0
        ),
        "train_log_likelihood_per_observation": train_ll / len(train),
        "oos_log_likelihood_per_observation": oos_ll / len(oos),
        "train_oos_likelihood_drift": abs(train_ll / len(train) - oos_ll / len(oos)),
        "aic": aic,
        "bic": bic,
        "occupancy_train": occupancy_train.tolist(),
        "occupancy_oos": occupancy_oos.tolist(),
        "occupancy_drift_l1": float(np.abs(occupancy_train - occupancy_oos).sum()),
        "mean_state_duration_train": [
            float(np.mean(item)) if item else 0.0 for item in durations_train
        ],
        "mean_state_duration_oos": [
            float(np.mean(item)) if item else 0.0 for item in durations_oos
        ],
        "single_bar_share_train": single_bar_shares(durations_train),
        "single_bar_share_oos": single_bar_shares(durations_oos),
        "posterior_feature_mean_train": feature_means_train,
        "posterior_feature_mean_oos": feature_means_oos,
        "feature_mean_drift_l2": [
            float(np.linalg.norm(np.asarray(train_mean) - np.asarray(oos_mean)))
            for train_mean, oos_mean in zip(feature_means_train, feature_means_oos)
        ],
        "emission_mean": np.asarray(model.means_).tolist(),
        "emission_variance": variances(model).tolist(),
        "self_transition": np.diag(model.transmat_).tolist(),
        "rare_state_count_train": int((occupancy_train < RARE_STATE_THRESHOLD).sum()),
        "rare_state_count_oos": int((occupancy_oos < RARE_STATE_THRESHOLD).sum()),
        "minimum_pairwise_separation": minimum_pairwise_separation(model),
    }


def align_metric_lists(metrics: dict[str, Any], permutation: list[int]) -> dict[str, Any]:
    result = dict(metrics)
    for key in (
        "occupancy_train",
        "occupancy_oos",
        "mean_state_duration_train",
        "mean_state_duration_oos",
        "single_bar_share_train",
        "single_bar_share_oos",
        "posterior_feature_mean_train",
        "posterior_feature_mean_oos",
        "feature_mean_drift_l2",
        "emission_mean",
        "emission_variance",
        "self_transition",
    ):
        values = result[key]
        result[key] = [values[index] for index in permutation]
    return result


def summarize_candidate(models: list[GaussianHMM], fits: list[dict[str, Any]]) -> dict[str, Any]:
    reference_index = min(range(len(fits)), key=lambda index: fits[index]["seed"])
    reference = models[reference_index]
    reference_parameters = aligned_parameters(reference, range(reference.n_components))
    aligned_fits, parameter_differences = [], []
    for model, metrics in zip(models, fits):
        permutation = state_alignment(reference, model)
        aligned_fits.append({**align_metric_lists(metrics, permutation), "alignment_to_reference": permutation})
        parameters = aligned_parameters(model, permutation)
        aligned = aligned_fits[-1]
        reference_fit = align_metric_lists(fits[reference_index], list(range(reference.n_components)))
        parameter_differences.append(
            {
                "emission_mean_rmse": float(np.sqrt(np.mean((parameters["means"] - reference_parameters["means"]) ** 2))),
                "emission_variance_rmse": float(np.sqrt(np.mean((parameters["variances"] - reference_parameters["variances"]) ** 2))),
                "transition_rmse": float(np.sqrt(np.mean((parameters["transition"] - reference_parameters["transition"]) ** 2))),
                "train_occupancy_rmse": float(np.sqrt(np.mean((np.asarray(aligned["occupancy_train"]) - np.asarray(reference_fit["occupancy_train"])) ** 2))),
                "oos_occupancy_rmse": float(np.sqrt(np.mean((np.asarray(aligned["occupancy_oos"]) - np.asarray(reference_fit["occupancy_oos"])) ** 2))),
                "train_duration_rmse": float(np.sqrt(np.mean((np.asarray(aligned["mean_state_duration_train"]) - np.asarray(reference_fit["mean_state_duration_train"])) ** 2))),
                "oos_duration_rmse": float(np.sqrt(np.mean((np.asarray(aligned["mean_state_duration_oos"]) - np.asarray(reference_fit["mean_state_duration_oos"])) ** 2))),
                "self_transition_rmse": float(np.sqrt(np.mean((np.asarray(aligned["self_transition"]) - np.asarray(reference_fit["self_transition"])) ** 2))),
            }
        )
    scalar_keys = (
        "train_log_likelihood_per_observation", "oos_log_likelihood_per_observation",
        "train_oos_likelihood_drift",
        "aic", "bic", "occupancy_drift_l1", "rare_state_count_train",
        "rare_state_count_oos", "minimum_pairwise_separation",
    )
    aggregate = {
        key: {"mean": float(np.mean([fit[key] for fit in aligned_fits])), "std": float(np.std([fit[key] for fit in aligned_fits]))}
        for key in scalar_keys
    }
    aggregate["reproducibility"] = {
        key: {"mean": float(np.mean([row[key] for row in parameter_differences])), "max": float(np.max([row[key] for row in parameter_differences]))}
        for key in parameter_differences[0]
    }
    aggregate["state_ranges"] = {
        key: {
            "minimum": np.min(np.asarray([fit[key] for fit in aligned_fits]), axis=0).tolist(),
            "maximum": np.max(np.asarray([fit[key] for fit in aligned_fits]), axis=0).tolist(),
        }
        for key in (
            "occupancy_train",
            "occupancy_oos",
            "mean_state_duration_train",
            "mean_state_duration_oos",
            "single_bar_share_train",
            "single_bar_share_oos",
            "self_transition",
            "feature_mean_drift_l2",
        )
    }
    summary = {
        "reference_seed": fits[reference_index]["seed"],
        "fits": aligned_fits,
        "aggregate": aggregate,
    }
    summary["guardrails"] = evaluate_guardrails(summary)
    return summary


def evaluate_guardrails(candidate: dict[str, Any]) -> dict[str, Any]:
    aggregate = candidate["aggregate"]
    reproducibility = aggregate["reproducibility"]
    state_ranges = aggregate["state_ranges"]
    checks = {
        "all_fits_converged": all(fit["converged"] for fit in candidate["fits"]),
        "non_negative_convergence_delta": all(
            fit["final_likelihood_delta"] >= -NEGATIVE_CONVERGENCE_DELTA_TOLERANCE
            for fit in candidate["fits"]
        ),
        "oos_likelihood_drift": aggregate["train_oos_likelihood_drift"]["mean"]
        <= MAX_LIKELIHOOD_DRIFT,
        "occupancy_drift": aggregate["occupancy_drift_l1"]["mean"]
        <= MAX_OCCUPANCY_DRIFT,
        "feature_drift": max(state_ranges["feature_mean_drift_l2"]["maximum"])
        <= MAX_FEATURE_MEAN_DRIFT,
        "no_rare_train_states": aggregate["rare_state_count_train"]["mean"] == 0,
        "no_rare_oos_states": aggregate["rare_state_count_oos"]["mean"] == 0,
        "state_separation": aggregate["minimum_pairwise_separation"]["mean"]
        >= MIN_PAIRWISE_SEPARATION,
        "oos_duration": min(state_ranges["mean_state_duration_oos"]["minimum"])
        >= MIN_OOS_MEAN_DURATION,
        "oos_noise": max(state_ranges["single_bar_share_oos"]["maximum"])
        <= MAX_OOS_SINGLE_BAR_SHARE,
        "emission_reproducibility": reproducibility["emission_mean_rmse"]["max"]
        <= MAX_EMISSION_MEAN_RMSE,
        "transition_reproducibility": reproducibility["transition_rmse"]["max"]
        <= MAX_TRANSITION_RMSE,
        "oos_occupancy_reproducibility": reproducibility["oos_occupancy_rmse"]["max"]
        <= MAX_OOS_OCCUPANCY_RMSE,
    }
    return {
        "passed": all(checks.values()),
        "checks": checks,
        "failed": [name for name, passed in checks.items() if not passed],
    }


def choose_outcome(candidates: list[dict[str, Any]]) -> dict[str, Any]:
    incomplete = [row["k"] for row in candidates if row["status"] != "ok"]
    if incomplete:
        return {
            "outcome": "inconclusive",
            "selected_k": None,
            "reason": f"Incomplete deterministic fits for K={incomplete}; every K must be complete.",
        }
    eligible = [row for row in candidates if row["guardrails"]["passed"]]
    if not eligible:
        return {
            "outcome": "inconclusive",
            "selected_k": None,
            "reason": "No candidate clears every model-selection guardrail.",
        }
    best_aic = min(eligible, key=lambda row: (row["aggregate"]["aic"]["mean"], row["k"]))["k"]
    best_bic = min(eligible, key=lambda row: (row["aggregate"]["bic"]["mean"], row["k"]))["k"]
    best_oos = max(
        eligible,
        key=lambda row: (row["aggregate"]["oos_log_likelihood_per_observation"]["mean"], -row["k"]),
    )["k"]
    if len({best_aic, best_bic, best_oos}) != 1:
        return {
            "outcome": "inconclusive",
            "selected_k": None,
            "reason": (
                "Selection evidence conflicts: "
                f"AIC favors K={best_aic}, BIC favors K={best_bic}, "
                f"and OOS likelihood favors K={best_oos}."
            ),
        }
    best = next(row for row in eligible if row["k"] == best_aic)
    k = best["k"]
    outcome = "retain_k3" if k == 3 else "select_k6" if k == 6 else "select_other_k"
    return {
        "outcome": outcome,
        "selected_k": k,
        "reason": (
            "AIC, BIC, and OOS likelihood agree after the candidate cleared "
            "every model-selection guardrail."
        ),
    }


def strict_json(value: Any) -> Any:
    if isinstance(value, dict): return {key: strict_json(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)): return [strict_json(item) for item in value]
    if isinstance(value, (np.integer,)): return int(value)
    if isinstance(value, (np.floating, float)): return float(value) if math.isfinite(float(value)) else None
    return value


def markdown_report(result: dict[str, Any]) -> str:
    decision = result["decision"]
    lines = ["# SPY 1D HMM state-count decision", "", f"**Outcome:** `{decision['outcome']}`", f"**Selected K:** {decision['selected_k'] if decision['selected_k'] is not None else 'none'}", "", decision["reason"], "", "| K | status | guardrails | train LL/obs | OOS LL/obs | AIC | BIC | OOS rare | drift L1 | separation |", "|---:|---|---|---:|---:|---:|---:|---:|---:|---:|"]
    for row in result["candidates"]:
        if row["status"] != "ok":
            lines.append(f"| {row['k']} | failed | incomplete | — | — | — | — | — | — | — |")
            continue
        agg = row["aggregate"]
        failed = ", ".join(row["guardrails"]["failed"]) or "pass"
        lines.append(f"| {row['k']} | ok | {failed} | {agg['train_log_likelihood_per_observation']['mean']:.4f} | {agg['oos_log_likelihood_per_observation']['mean']:.4f} | {agg['aic']['mean']:.1f} | {agg['bic']['mean']:.1f} | {agg['rare_state_count_oos']['mean']:.2f} | {agg['occupancy_drift_l1']['mean']:.3f} | {agg['minimum_pairwise_separation']['mean']:.3f} |")
    lines += ["", "The JSON retains convergence deltas, posterior-weighted train/OOS feature means, emissions, occupancy, duration and single-bar noise, self-transition, drift, pairwise separation, every guardrail result, and aligned-seed reproducibility.", "", "Raw state indices were not compared across fits; each seed was aligned to the lowest-seed fit of the same K by its Gaussian emissions. Any incomplete K or disagreement among AIC, BIC, and OOS likelihood forces an inconclusive result.", ""]
    return "\n".join(lines)


def compare(args: argparse.Namespace) -> dict[str, Any]:
    if args.symbol.upper() != "SPY" or args.timeframe.upper() != "1D":
        raise ValueError("Issue #26 comparison is restricted to SPY 1D")
    if not 0.50 <= args.train_fraction < 1.0:
        raise ValueError("train_fraction must be in [0.50, 1.0)")
    if len(set(args.seeds)) != len(args.seeds) or not args.seeds:
        raise ValueError("seeds must be a non-empty unique list")
    config = train_hmm.FeatureConfig()
    raw = train_hmm.load_ohlc(args)
    features = train_hmm.calculate_features(raw, config)
    train_rows = int(len(features) * args.train_fraction)
    if train_rows < 200 or len(features) - train_rows < 50:
        raise ValueError("chronological split requires at least 200 training and 50 out-of-sample rows")
    scaler = StandardScaler()
    train_matrix = scaler.fit_transform(features.loc[:train_rows - 1, train_hmm.FEATURE_NAMES])
    full_matrix = scaler.transform(features[train_hmm.FEATURE_NAMES])
    observation_matrix = features[train_hmm.FEATURE_NAMES].to_numpy(dtype=float)
    candidates = []
    for k in candidate_state_counts():
        models, fits, failures = [], [], []
        for seed in args.seeds:
            try:
                model = fit_candidate(train_matrix, k, seed)
                models.append(model)
                fits.append(
                    fit_metrics(
                        model,
                        full_matrix,
                        train_rows,
                        seed,
                        observation_matrix=observation_matrix,
                    )
                )
            except Exception as exc:
                failures.append({"seed": seed, "error": f"{type(exc).__name__}: {exc}"})
        if failures:
            candidates.append({"k": k, "status": "failed", "failures": failures})
        else:
            candidates.append({"k": k, "status": "ok", **summarize_candidate(models, fits)})
    result = {
        "schema_version": 1, "scope": {"symbol": "SPY", "timeframe": "1D", "state_counts": list(DEFAULT_STATE_COUNTS), "seeds": args.seeds},
        "method": {"features": train_hmm.FEATURE_NAMES, "feature_config": asdict(config), "train_fraction": args.train_fraction, "covariance_type": "diag", "inference": "causal_forward_filter", "alignment": "minimum-cost symmetric diagonal-Gaussian emission distance within equal K", "guardrail_thresholds": {"rare_state_occupancy": RARE_STATE_THRESHOLD, "maximum_train_oos_likelihood_drift": MAX_LIKELIHOOD_DRIFT, "maximum_occupancy_drift_l1": MAX_OCCUPANCY_DRIFT, "maximum_feature_mean_drift_l2": MAX_FEATURE_MEAN_DRIFT, "minimum_pairwise_separation": MIN_PAIRWISE_SEPARATION, "minimum_oos_mean_duration": MIN_OOS_MEAN_DURATION, "maximum_oos_single_bar_share": MAX_OOS_SINGLE_BAR_SHARE, "maximum_emission_mean_rmse": MAX_EMISSION_MEAN_RMSE, "maximum_transition_rmse": MAX_TRANSITION_RMSE, "maximum_oos_occupancy_rmse": MAX_OOS_OCCUPANCY_RMSE, "negative_convergence_delta_tolerance": NEGATIVE_CONVERGENCE_DELTA_TOLERANCE}},
        "sample": {"usable_rows": len(features), "train_rows": train_rows, "oos_rows": len(features) - train_rows}, "candidates": candidates,
    }
    result["decision"] = choose_outcome(candidates)
    return strict_json(result)


def main() -> int:
    args = parse_args()
    result = compare(args)
    args.output_dir.mkdir(parents=True, exist_ok=True)
    json_path = args.output_dir / "state-count-comparison.json"
    report_path = args.output_dir / "state-count-decision.md"
    json_path.write_text(json.dumps(result, indent=2, allow_nan=False) + "\n", encoding="utf-8")
    report_path.write_text(markdown_report(result), encoding="utf-8")
    print(f"decision: {result['decision']['outcome']}")
    print(f"wrote: {json_path}")
    print(f"wrote: {report_path}")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (FileNotFoundError, ValueError, RuntimeError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        raise SystemExit(2)
