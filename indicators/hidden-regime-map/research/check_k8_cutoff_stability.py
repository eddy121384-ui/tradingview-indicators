#!/usr/bin/env python3
"""Check the five-feature SPY K=8 candidate across adjacent sample cutoffs."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

import numpy as np
from sklearn.preprocessing import StandardScaler

import compare_feature_sets
import compare_state_counts
import train_hmm

K = 8
DEFAULT_CUTOFFS = 5
FEATURE_SET = "baseline_er_downside"
EXPANDED_RESTART_OFFSETS = tuple(range(9))


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Check SPY five-feature K=8 stability across adjacent cutoffs"
    )
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--date-column", default="Date")
    parser.add_argument("--open-column", default="Open")
    parser.add_argument("--high-column", default="High")
    parser.add_argument("--low-column", default="Low")
    parser.add_argument("--close-column", default="Close")
    parser.add_argument("--symbol", default="SPY")
    parser.add_argument("--timeframe", default="1D")
    parser.add_argument("--train-fraction", type=float, default=0.80)
    parser.add_argument(
        "--seeds",
        type=int,
        nargs="+",
        default=list(compare_state_counts.DEFAULT_SEEDS),
    )
    parser.add_argument("--cutoffs", type=int, default=DEFAULT_CUTOFFS)
    return parser.parse_args()


def cutoff_positions(rows: int, count: int) -> list[int]:
    if count < 2:
        raise ValueError("cutoffs must be at least 2")
    if rows < count:
        raise ValueError("cutoffs cannot exceed available OHLC rows")
    return list(range(rows - count, rows))


def decision_for_rows(rows: list[dict[str, Any]]) -> dict[str, Any]:
    stable = bool(rows) and all(
        row["status"] == "ok" and row["guardrails"]["passed"] for row in rows
    )
    return {
        "outcome": (
            "stable_with_expanded_restarts"
            if stable
            else "cutoff_sensitive_after_expansion"
        ),
        "tested_cutoffs": len(rows),
        "passing_cutoffs": sum(
            row["status"] == "ok" and row["guardrails"]["passed"] for row in rows
        ),
        "reason": (
            "The five-feature K=8 candidate passed every existing guardrail at every "
            "tested cutoff with the fixed nine-attempt restart schedule."
            if stable
            else "The five-feature K=8 candidate failed at least one existing guardrail "
            "or fit at one or more tested cutoffs despite the fixed nine-attempt "
            "restart schedule."
        ),
    }


def fit_seed_group_expanded(
    matrix: np.ndarray, n_states: int, group_seed: int
) -> tuple[Any, list[dict[str, Any]], int]:
    """Run the frozen nine-attempt schedule and retain the best valid attempt."""
    attempts: list[dict[str, Any]] = []
    successful: list[tuple[float, int, Any]] = []
    for offset in EXPANDED_RESTART_OFFSETS:
        attempt_seed = group_seed + offset
        try:
            model = compare_state_counts.fit_candidate(matrix, n_states, attempt_seed)
            score = float(model.score(matrix))
            attempts.append(
                {
                    "attempt_seed": attempt_seed,
                    "status": "ok",
                    "train_log_likelihood": score,
                    "iterations": int(model.monitor_.iter),
                }
            )
            successful.append((score, attempt_seed, model))
        except Exception as exc:
            attempts.append(
                {
                    "attempt_seed": attempt_seed,
                    "status": "failed",
                    "error": f"{type(exc).__name__}: {exc}",
                }
            )
    if not successful:
        raise compare_state_counts.RestartGroupError(group_seed, attempts)
    _, selected_seed, selected_model = max(
        successful, key=lambda item: (item[0], -item[1])
    )
    return selected_model, attempts, selected_seed


def fit_seed_metrics(
    train_matrix: np.ndarray,
    full_matrix: np.ndarray,
    train_rows: int,
    seed: int,
    observation_matrix: np.ndarray,
    dates: np.ndarray,
    closes: np.ndarray,
) -> tuple[Any | None, dict[str, Any] | None, dict[str, Any] | None]:
    """Fit one expanded restart group; only expected exhaustion becomes data."""
    try:
        model, restart_attempts, selected_attempt_seed = fit_seed_group_expanded(
            train_matrix, K, seed
        )
    except compare_state_counts.RestartGroupError as exc:
        return (
            None,
            None,
            {
                "group_seed": exc.group_seed,
                "error": str(exc),
                "restart_attempts": exc.attempts,
            },
        )

    metrics = compare_state_counts.fit_metrics(
        model,
        full_matrix,
        train_rows,
        seed,
        observation_matrix=observation_matrix,
        dates=dates,
        events=[],
        closes=closes,
    )
    metrics["group_seed"] = seed
    metrics["selected_attempt_seed"] = selected_attempt_seed
    metrics["restart_attempts"] = restart_attempts
    return model, metrics, None


def evaluate_cutoff(
    args: argparse.Namespace,
    raw: Any,
    cutoff_position: int,
    config: train_hmm.FeatureConfig,
) -> dict[str, Any]:
    truncated = raw.iloc[: cutoff_position + 1].reset_index(drop=True)
    baseline = train_hmm.calculate_features(truncated, config)
    enriched = compare_feature_sets.add_path_features(baseline, truncated)
    feature_names = list(compare_feature_sets.FEATURE_SETS[FEATURE_SET])
    train_rows = int(len(enriched) * args.train_fraction)
    if train_rows < 200 or len(enriched) - train_rows < 50:
        raise ValueError(
            "chronological split requires at least 200 training and 50 out-of-sample rows"
        )

    scaler = StandardScaler()
    train_matrix = scaler.fit_transform(enriched.loc[: train_rows - 1, feature_names])
    full_matrix = scaler.transform(enriched[feature_names])
    observation_matrix = enriched[feature_names].to_numpy(dtype=float)
    dates = enriched["date"].dt.tz_localize(None).to_numpy(dtype="datetime64[D]")
    closes = enriched["close"].to_numpy(dtype=float)

    models, fits, failures = [], [], []
    for seed in args.seeds:
        model, metrics, failure = fit_seed_metrics(
            train_matrix,
            full_matrix,
            train_rows,
            seed,
            observation_matrix,
            dates,
            closes,
        )
        if failure is not None:
            failures.append(failure)
            continue
        assert model is not None and metrics is not None
        models.append(model)
        fits.append(metrics)

    cutoff_date = str(truncated.iloc[-1]["date"].date())
    if failures:
        return {
            "cutoff": cutoff_date,
            "status": "failed",
            "sample": {
                "usable_rows": len(enriched),
                "train_rows": train_rows,
                "oos_rows": len(enriched) - train_rows,
            },
            "failures": failures,
        }

    summary = compare_state_counts.summarize_candidate(models, fits)
    seed_diagnostics = [
        {
            "group_seed": fit["group_seed"],
            "selected_attempt_seed": fit["selected_attempt_seed"],
            "minimum_oos_occupancy": min(fit["occupancy_oos"]),
            "rare_state_count_oos": fit["rare_state_count_oos"],
            "occupancy_drift_l1": fit["occupancy_drift_l1"],
            "train_oos_likelihood_drift": fit["train_oos_likelihood_drift"],
        }
        for fit in summary["fits"]
    ]
    return {
        "cutoff": cutoff_date,
        "status": "ok",
        "sample": {
            "usable_rows": len(enriched),
            "train_rows": train_rows,
            "oos_rows": len(enriched) - train_rows,
        },
        "guardrails": summary["guardrails"],
        "seed_diagnostics": seed_diagnostics,
        "worst_seed": {
            "minimum_oos_occupancy": min(
                row["minimum_oos_occupancy"] for row in seed_diagnostics
            ),
            "maximum_rare_state_count_oos": max(
                row["rare_state_count_oos"] for row in seed_diagnostics
            ),
            "maximum_occupancy_drift_l1": max(
                row["occupancy_drift_l1"] for row in seed_diagnostics
            ),
            "maximum_train_oos_likelihood_drift": max(
                row["train_oos_likelihood_drift"] for row in seed_diagnostics
            ),
        },
    }


def markdown_report(result: dict[str, Any]) -> str:
    decision = result["decision"]
    lines = [
        "# SPY five-feature K=8 cutoff-stability decision",
        "",
        f"**Outcome:** `{decision['outcome']}`",
        f"**Passing cutoffs:** {decision['passing_cutoffs']}/{decision['tested_cutoffs']}",
        "",
        decision["reason"],
        "",
        "| Cutoff | Status | Guardrails | Min OOS occupancy | Max rare OOS states | Selected restart seeds |",
        "|---|---|---|---:|---:|---|",
    ]
    for row in result["cutoffs"]:
        if row["status"] != "ok":
            lines.append(
                f"| {row['cutoff']} | failed | incomplete | — | — | — |"
            )
            continue
        failed = ", ".join(row["guardrails"]["failed"]) or "pass"
        attempts = ", ".join(
            f"{item['group_seed']}→{item['selected_attempt_seed']}"
            for item in row["seed_diagnostics"]
        )
        lines.append(
            f"| {row['cutoff']} | ok | {failed} | "
            f"{row['worst_seed']['minimum_oos_occupancy']:.4%} | "
            f"{row['worst_seed']['maximum_rare_state_count_oos']} | {attempts} |"
        )
    lines += [
        "",
        "This diagnostic tests only the fixed five-feature K=8 candidate with the "
        "frozen nine-attempt restart schedule across adjacent sample cutoffs. It does "
        "not compare K=8 against K=3–7 and does not change any guardrail threshold.",
        "",
    ]
    return "\n".join(lines)


def compare(args: argparse.Namespace) -> dict[str, Any]:
    if args.symbol.upper() != "SPY" or args.timeframe.upper() != "1D":
        raise ValueError("cutoff-stability comparison is restricted to SPY 1D")
    if not 0.50 <= args.train_fraction < 1.0:
        raise ValueError("train_fraction must be in [0.50, 1.0)")
    compare_state_counts.validate_seed_groups(args.seeds)
    config = train_hmm.FeatureConfig()
    raw = train_hmm.load_ohlc(args)
    rows = [
        evaluate_cutoff(args, raw, position, config)
        for position in cutoff_positions(len(raw), args.cutoffs)
    ]
    return compare_state_counts.strict_json(
        {
            "schema_version": 2,
            "scope": {
                "symbol": "SPY",
                "timeframe": "1D",
                "feature_set": FEATURE_SET,
                "k": K,
                "cutoffs": args.cutoffs,
                "seeds": args.seeds,
            },
            "method": {
                "train_fraction": args.train_fraction,
                "restart_offsets": list(EXPANDED_RESTART_OFFSETS),
                "selection": "highest finite converged train log likelihood per seed group",
                "guardrail_thresholds": {
                    "rare_state_occupancy": compare_state_counts.RARE_STATE_THRESHOLD,
                    "maximum_train_oos_likelihood_drift": compare_state_counts.MAX_LIKELIHOOD_DRIFT,
                    "maximum_occupancy_drift_l1": compare_state_counts.MAX_OCCUPANCY_DRIFT,
                    "maximum_variance_aware_feature_drift": compare_state_counts.MAX_FEATURE_DISTRIBUTION_DRIFT,
                    "minimum_pairwise_separation": compare_state_counts.MIN_PAIRWISE_SEPARATION,
                    "minimum_oos_mean_duration": compare_state_counts.MIN_OOS_MEAN_DURATION,
                    "maximum_oos_single_bar_share": compare_state_counts.MAX_OOS_SINGLE_BAR_SHARE,
                    "maximum_emission_mean_rmse": compare_state_counts.MAX_EMISSION_MEAN_RMSE,
                    "maximum_transition_rmse": compare_state_counts.MAX_TRANSITION_RMSE,
                    "maximum_oos_occupancy_rmse": compare_state_counts.MAX_OOS_OCCUPANCY_RMSE,
                },
            },
            "cutoffs": rows,
            "decision": decision_for_rows(rows),
        }
    )


def main() -> int:
    args = parse_args()
    result = compare(args)
    args.output_dir.mkdir(parents=True, exist_ok=True)
    json_path = args.output_dir / "k8-cutoff-stability.json"
    report_path = args.output_dir / "k8-cutoff-stability.md"
    json_path.write_text(
        json.dumps(result, indent=2, allow_nan=False) + "\n", encoding="utf-8"
    )
    report_path.write_text(markdown_report(result), encoding="utf-8")
    print(f"decision: {result['decision']['outcome']}")
    print(f"wrote: {json_path}")
    print(f"wrote: {report_path}")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (FileNotFoundError, ValueError, RuntimeError) as exc:
        print(f"error: {exc}")
        raise SystemExit(2)
