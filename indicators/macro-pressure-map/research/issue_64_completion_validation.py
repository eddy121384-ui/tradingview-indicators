#!/usr/bin/env python3
"""Completion-level fail-closed bindings for Issue #64 durable evidence.

This module covers verdict-bearing fields that are intentionally broader than the
phase-specific validators: the full Phase A regime/horizon leader grid and all
named-hypothesis sample counts, the required fixed Phase B benchmarks, and the
Phase C 0/5/10 bp cost-sensitivity table.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import pandas as pd

from issue_64_durable_validation import FULL_SEGMENT, _close, _finite, _single_row, strict_load_json

HERE = Path(__file__).resolve().parent
PHASE_A_DECISION = HERE / "decisions" / "issue-64-phase-a.json"
PHASE_B_DECISION = HERE / "decisions" / "issue-64-phase-b.json"
PHASE_C_DECISION = HERE / "decisions" / "issue-64-phase-c.json"


def validate_phase_a_completion(phase_a_dir: Path) -> dict:
    decision = strict_load_json(PHASE_A_DECISION)
    if int(decision.get("schema_version", 0)) < 5:
        raise RuntimeError("Phase A completion binding requires decision schema >= 5")
    tolerance = _finite(
        "phase_a.completion.numeric_tolerance",
        decision["regenerated_evidence_binding"]["numeric_tolerance"],
    )
    if tolerance <= 0.0:
        raise RuntimeError("Phase A completion tolerance must be positive")

    leaders = pd.read_csv(phase_a_dir / "phase-a-segment-leader-stability.csv")
    stability = pd.read_csv(phase_a_dir / "phase-a-segment-relative-stability.csv")
    expected_grid = decision["temporal_stability"]["leader_grid"]
    if len(expected_grid) != 27 or len(leaders) != 27:
        raise RuntimeError("Phase A leader grid must contain exactly 27 regime/horizon cells")

    actual_keys = set(zip(leaders["regime"], leaders["horizon"]))
    expected_keys = {(row["regime"], row["horizon"]) for row in expected_grid}
    if len(expected_keys) != 27 or actual_keys != expected_keys:
        raise RuntimeError("Phase A regime/horizon leader-grid identity drifted")

    leader_checks = 0
    for expected in expected_grid:
        row = _single_row(
            leaders,
            "Phase A leader grid",
            regime=expected["regime"],
            horizon=expected["horizon"],
        )
        if row["leader_asset_dev"] != expected["development_leader"]:
            raise RuntimeError(
                f"Phase A development leader drifted for {expected['regime']}/{expected['horizon']}"
            )
        if row["leader_asset_post"] != expected["post2019_leader"]:
            raise RuntimeError(
                f"Phase A post-2019 leader drifted for {expected['regime']}/{expected['horizon']}"
            )
        if bool(row["same_leader"]) is not bool(expected["same_leader"]):
            raise RuntimeError(
                f"Phase A same-leader flag drifted for {expected['regime']}/{expected['horizon']}"
            )
        _close(
            f"phase_a.leader_grid.{expected['regime']}.{expected['horizon']}.development_mean_return",
            row["leader_embargoed_mean_return_dev"],
            expected["development_mean_return"],
            tolerance,
        )
        _close(
            f"phase_a.leader_grid.{expected['regime']}.{expected['horizon']}.post2019_mean_return",
            row["leader_embargoed_mean_return_post"],
            expected["post2019_mean_return"],
            tolerance,
        )
        if int(row["leader_embargoed_observations_dev"]) != int(expected["development_n"]):
            raise RuntimeError(
                f"Phase A development leader sample count drifted for {expected['regime']}/{expected['horizon']}"
            )
        if int(row["leader_embargoed_observations_post"]) != int(expected["post2019_n"]):
            raise RuntimeError(
                f"Phase A post-2019 leader sample count drifted for {expected['regime']}/{expected['horizon']}"
            )
        leader_checks += 7

    named_count_checks = 0
    for section_name in (
        "selected_phase_b_hypothesis",
        "secondary_exploratory_hypothesis",
        "important_instability_example",
    ):
        section = decision[section_name]
        comparison = section["comparison"].split(" total return minus ")
        if len(comparison) != 2:
            raise RuntimeError(f"unsupported Phase A comparison in {section_name}")
        asset_a = comparison[0]
        asset_b = comparison[1].split(" total return")[0]
        for horizon, key in (("1M", "one_month"), ("3M", "three_month"), ("6M", "six_month")):
            expected = section[key]
            for durable_key in ("development_n", "post2019_n"):
                if durable_key not in expected:
                    raise RuntimeError(
                        f"Phase A durable decision is missing required {durable_key} in {section_name}/{key}"
                    )
            row = _single_row(
                stability,
                "Phase A named hypothesis",
                regime=section["regime"],
                horizon=horizon,
                asset_a=asset_a,
                asset_b=asset_b,
            )
            if int(row["development_n"]) != int(expected["development_n"]):
                raise RuntimeError(f"Phase A development_n drifted in {section_name}/{key}")
            if int(row["post2019_n"]) != int(expected["post2019_n"]):
                raise RuntimeError(f"Phase A post2019_n drifted in {section_name}/{key}")
            named_count_checks += 2

    return {
        "validated": True,
        "leader_grid_cells": 27,
        "leader_grid_checks": leader_checks,
        "named_hypothesis_sample_count_checks": named_count_checks,
        "numeric_tolerance": tolerance,
    }


def validate_phase_b_completion(phase_b_dir: Path) -> dict:
    decision = strict_load_json(PHASE_B_DECISION)
    if int(decision.get("schema_version", 0)) < 8:
        raise RuntimeError("Phase B completion binding requires decision schema >= 8")
    tolerance = _finite(
        "phase_b.completion.numeric_tolerance",
        decision["regenerated_evidence_binding"]["numeric_tolerance"],
    )
    summary = pd.read_csv(phase_b_dir / "phase-b-summary.csv")
    primary = decision["primary_full_history_result"]
    checks = 0
    for strategy, durable_key in (
        ("fixed_60_40", "fixed_60_40"),
        ("fixed_equal_weight", "fixed_equal_weight"),
    ):
        row = _single_row(summary, "Phase B required fixed benchmark", strategy=strategy, segment=FULL_SEGMENT)
        expected = primary[durable_key]
        for key in (
            "CAGR",
            "Sharpe",
            "maximum_drawdown",
            "Calmar",
            "annualized_turnover",
            "transaction_cost_drag",
        ):
            _close(f"phase_b.benchmark.{durable_key}.{key}", row[key], expected[key], tolerance)
            checks += 1
        if int(row["rebalance_count"]) != int(expected["rebalance_count"]):
            raise RuntimeError(f"Phase B benchmark rebalance count drifted for {strategy}")
        checks += 1
    return {
        "validated": True,
        "required_fixed_benchmarks": ["fixed_60_40", "fixed_equal_weight"],
        "numeric_checks": checks,
        "numeric_tolerance": tolerance,
    }


def validate_phase_c_completion(phase_c_dir: Path) -> dict:
    decision = strict_load_json(PHASE_C_DECISION)
    if int(decision.get("schema_version", 0)) < 6:
        raise RuntimeError("Phase C completion binding requires decision schema >= 6")
    binding = decision["regenerated_evidence_binding"]
    tolerance = _finite(
        "phase_c.cost_sensitivity_value_tolerance",
        binding["cost_sensitivity_value_tolerance"],
    )
    if tolerance <= 0.0:
        raise RuntimeError("Phase C cost-sensitivity tolerance must be positive")

    costs = pd.read_csv(phase_c_dir / "phase-c-cost-sensitivity.csv")
    expected_table = decision["cost_sensitivity_full_history"]
    expected_keys = {
        0.0: "zero_bps",
        5.0: "five_bps",
        10.0: "ten_bps",
    }
    required_pairs = {(bps, strategy) for bps in expected_keys for strategy in ("phase_c_combined", "phase_b_reflation_only")}
    actual_pairs = set(zip(costs["cost_bps"].astype(float), costs["strategy"]))
    if not required_pairs.issubset(actual_pairs):
        raise RuntimeError("Phase C cost-sensitivity table is missing a required 0/5/10 bp strategy row")

    checks = 0
    for bps, durable_key in expected_keys.items():
        expected = expected_table[durable_key]
        for strategy, prefix in (
            ("phase_c_combined", "phase_c"),
            ("phase_b_reflation_only", "phase_b"),
        ):
            row = _single_row(costs, "Phase C cost sensitivity", cost_bps=bps, strategy=strategy)
            for metric in ("CAGR", "Sharpe"):
                _close(
                    f"phase_c.cost.{durable_key}.{prefix}_{metric}",
                    row[metric],
                    expected[f"{prefix}_{metric}"],
                    tolerance,
                )
                checks += 1
    return {
        "validated": True,
        "cost_rows_checked": 6,
        "numeric_checks": checks,
        "numeric_tolerance": tolerance,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Issue #64 completion-level durable evidence validation")
    parser.add_argument("--phase-a-dir", type=Path, required=True)
    parser.add_argument("--phase-b-dir", type=Path, required=True)
    parser.add_argument("--phase-c-dir", type=Path, required=True)
    args = parser.parse_args()
    result = {
        "phase_a": validate_phase_a_completion(args.phase_a_dir),
        "phase_b": validate_phase_b_completion(args.phase_b_dir),
        "phase_c": validate_phase_c_completion(args.phase_c_dir),
    }
    print(json.dumps(result, indent=2, allow_nan=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
