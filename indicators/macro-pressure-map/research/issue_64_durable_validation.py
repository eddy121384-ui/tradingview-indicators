#!/usr/bin/env python3
"""Fail-closed regenerated-evidence binding for Issue #64 Phase A and Phase B."""
from __future__ import annotations

import json
import math
from pathlib import Path

import pandas as pd

ASSETS = ("SPY", "TLT", "GLD")
FULL_SEGMENT = "full_reused_history"


def _reject_constant(value: str) -> None:
    raise ValueError(f"non-finite JSON constant is not permitted: {value}")


def strict_load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"), parse_constant=_reject_constant)


def _finite(name: str, value: object) -> float:
    result = float(value)
    if not math.isfinite(result):
        raise RuntimeError(f"{name} must be finite, got {value!r}")
    return result


def _close(name: str, actual: object, expected: object, tolerance: float) -> None:
    a = _finite(f"{name}.actual", actual)
    e = _finite(f"{name}.expected", expected)
    error = abs(a - e)
    if not math.isfinite(error) or error > tolerance:
        raise RuntimeError(
            f"durable evidence drifted at {name}: actual={a}, expected={e}, "
            f"error={error}, tolerance={tolerance}"
        )


def _single_row(table: pd.DataFrame, name: str, **filters: object) -> pd.Series:
    mask = pd.Series(True, index=table.index)
    for column, value in filters.items():
        if column not in table.columns:
            raise ValueError(f"{name} missing required column {column}")
        mask &= table[column].eq(value)
    rows = table.loc[mask]
    if len(rows) != 1:
        raise RuntimeError(f"expected one {name} row for {filters}, found {len(rows)}")
    return rows.iloc[0]


def _pair_assets(comparison: str) -> tuple[str, str]:
    prefix = comparison.split(" total return minus ")
    if len(prefix) != 2:
        raise ValueError(f"unsupported pair comparison: {comparison}")
    return prefix[0], prefix[1].split(" total return")[0]


def _validate_phase_a_pair(
    stability: pd.DataFrame,
    section_name: str,
    section: dict,
    tolerance: float,
) -> int:
    asset_a, asset_b = _pair_assets(section["comparison"])
    checked = 0
    for horizon, key in (("1M", "one_month"), ("3M", "three_month"), ("6M", "six_month")):
        row = _single_row(
            stability,
            "Phase A relative stability",
            regime=section["regime"],
            horizon=horizon,
            asset_a=asset_a,
            asset_b=asset_b,
        )
        expected = section[key]
        mapping = {
            "development_mean_spread": "development_mean_spread",
            "post2019_mean_spread": "post2019_mean_spread",
        }
        for durable_key, column in mapping.items():
            _close(f"phase_a.{section_name}.{key}.{durable_key}", row[column], expected[durable_key], tolerance)
            checked += 1
        for side, low_col, high_col in (
            ("development", "development_ci_low", "development_ci_high"),
            ("post2019", "post2019_ci_low", "post2019_ci_high"),
        ):
            durable_ci = expected[f"{side}_nominal_ci95"]
            _close(f"phase_a.{section_name}.{key}.{side}_ci_low", row[low_col], durable_ci[0], tolerance)
            _close(f"phase_a.{section_name}.{key}.{side}_ci_high", row[high_col], durable_ci[1], tolerance)
            checked += 2
        for side, column in (("development", "development_n"), ("post2019", "post2019_n")):
            durable_key = f"{side}_n"
            if durable_key in expected:
                if int(row[column]) != int(expected[durable_key]):
                    raise RuntimeError(
                        f"Phase A durable sample count drifted at {section_name}/{key}/{durable_key}: "
                        f"{int(row[column])} != {int(expected[durable_key])}"
                    )
                checked += 1
    return checked


def validate_phase_a_generated_evidence(output_dir: Path, decision_path: Path) -> dict:
    decision = strict_load_json(decision_path)
    if int(decision.get("schema_version", 0)) < 4:
        raise RuntimeError("Phase A durable decision must use regenerated-evidence schema >= 4")
    binding = decision["regenerated_evidence_binding"]
    tolerance = _finite("phase_a.numeric_tolerance", binding["numeric_tolerance"])
    if tolerance <= 0.0:
        raise RuntimeError("Phase A numeric tolerance must be positive")

    leaders = pd.read_csv(output_dir / "phase-a-segment-leader-stability.csv")
    stability = pd.read_csv(output_dir / "phase-a-segment-relative-stability.csv")
    temporal = decision["temporal_stability"]

    if len(leaders) != int(temporal["regime_horizon_leader_comparisons"]):
        raise RuntimeError("Phase A leader-comparison count drifted")
    if int(leaders["same_leader"].sum()) != int(temporal["same_leader_pre2020_vs_post2019"]):
        raise RuntimeError("Phase A same-leader count drifted")
    dev_counts = leaders["leader_asset_dev"].value_counts().to_dict()
    post_counts = leaders["leader_asset_post"].value_counts().to_dict()
    for asset in ASSETS:
        if int(dev_counts.get(asset, 0)) != int(temporal["development_leader_counts"][asset]):
            raise RuntimeError(f"Phase A development leader count drifted for {asset}")
        if int(post_counts.get(asset, 0)) != int(temporal["post2019_leader_counts"][asset]):
            raise RuntimeError(f"Phase A post-2019 leader count drifted for {asset}")

    if len(stability) != int(temporal["pairwise_regime_horizon_comparisons"]):
        raise RuntimeError("Phase A pairwise comparison count drifted")
    if int(stability["same_point_sign"].sum()) != int(temporal["same_pairwise_point_sign"]):
        raise RuntimeError("Phase A same-sign count drifted")
    if int(stability["both_intervals_exclude_zero_same_direction"].sum()) != int(
        temporal["both_segments_nominal_ci_excludes_zero_same_direction"]
    ):
        raise RuntimeError("Phase A same-direction nominal-CI count drifted")
    by_regime = stability.groupby("regime")["same_point_sign"].sum().to_dict()
    for regime, expected in temporal["same_point_sign_by_regime"].items():
        if int(by_regime.get(regime, 0)) != int(expected):
            raise RuntimeError(f"Phase A same-sign regime count drifted for {regime}")

    check_count = 0
    for name in (
        "selected_phase_b_hypothesis",
        "secondary_exploratory_hypothesis",
        "important_instability_example",
    ):
        check_count += _validate_phase_a_pair(stability, name, decision[name], tolerance)

    selected = decision["selected_phase_b_hypothesis"]
    if selected["regime"] != "Reflation / Inflation Rising" or selected["comparison"] != "SPY total return minus TLT total return":
        raise RuntimeError("Phase A selected Phase B hypothesis identity drifted")
    if decision["phase_a_decision"]["nine_cell_historical_winner_mapping_rejected"] is not True:
        raise RuntimeError("Phase A durable decision no longer rejects nine-cell historical winner mapping")

    return {
        "validated": True,
        "leader_comparisons": int(len(leaders)),
        "same_leaders": int(leaders["same_leader"].sum()),
        "pairwise_comparisons": int(len(stability)),
        "same_pairwise_sign": int(stability["same_point_sign"].sum()),
        "named_pair_value_checks": int(check_count),
        "numeric_tolerance": tolerance,
    }


def validate_phase_b_generated_evidence(phase_dir: Path, decision_path: Path) -> dict:
    decision = strict_load_json(decision_path)
    if int(decision.get("schema_version", 0)) < 7:
        raise RuntimeError("Phase B durable decision must use regenerated-evidence schema >= 7")
    binding = decision["regenerated_evidence_binding"]
    tolerance = _finite("phase_b.numeric_tolerance", binding["numeric_tolerance"])
    if tolerance <= 0.0:
        raise RuntimeError("Phase B numeric tolerance must be positive")

    summary = pd.read_csv(phase_dir / "phase-b-summary.csv")
    incremental = pd.read_csv(phase_dir / "phase-b-incremental-vs-neutral.csv")
    costs = pd.read_csv(phase_dir / "phase-b-cost-sensitivity.csv")
    exposure = strict_load_json(phase_dir / "phase-b-posthoc-exposure-match.json")
    episodes = strict_load_json(phase_dir / "phase-b-posthoc-timing-concentration.json")
    asset = pd.read_csv(phase_dir / "phase-b-asset-contribution.csv")
    regime = pd.read_csv(phase_dir / "phase-b-regime-allocation-contribution.csv")
    reconciliation = pd.read_csv(phase_dir / "phase-b-contribution-reconciliation.csv")
    price_manifest = strict_load_json(phase_dir / "phase-b-outcome-prices-manifest.json")

    primary = decision["primary_full_history_result"]
    checks = 0
    for strategy, durable_key in (
        ("v66_reflation_override", "v66_reflation_override"),
        ("fixed_neutral_40_40_20", "fixed_neutral_40_40_20"),
        ("causal_inverse_volatility", "causal_inverse_volatility_context"),
    ):
        row = _single_row(summary, "Phase B summary", strategy=strategy, segment=FULL_SEGMENT)
        expected = primary[durable_key]
        for key in ("CAGR", "Sharpe", "maximum_drawdown", "Calmar"):
            _close(f"phase_b.primary.{durable_key}.{key}", row[key], expected[key], tolerance)
            checks += 1
        if durable_key == "v66_reflation_override":
            for key in ("annualized_turnover", "transaction_cost_drag"):
                _close(f"phase_b.primary.{durable_key}.{key}", row[key], expected[key], tolerance)
                checks += 1
            if int(row["rebalance_count"]) != int(expected["rebalance_count"]):
                raise RuntimeError("Phase B rebalance count drifted")
            checks += 1

    inc = _single_row(incremental, "Phase B incremental", segment=FULL_SEGMENT)
    for key, expected in primary["incremental_vs_neutral"].items():
        _close(f"phase_b.incremental.{key}", inc[key], expected, tolerance)
        checks += 1

    cost_expect = decision["cost_sensitivity"]
    for durable_key, bps, strategy in (
        ("strategy_CAGR_0bp", 0.0, "v66_reflation_override"),
        ("strategy_CAGR_5bp", 5.0, "v66_reflation_override"),
        ("strategy_CAGR_10bp", 10.0, "v66_reflation_override"),
        ("neutral_CAGR_10bp", 10.0, "fixed_neutral_40_40_20"),
    ):
        row = _single_row(costs, "Phase B cost sensitivity", cost_bps=bps, strategy=strategy)
        _close(f"phase_b.cost.{durable_key}", row["CAGR"], cost_expect[durable_key], tolerance)
        checks += 1

    exposure_rows = {row["segment"]: row for row in exposure["comparison_rows"]}
    exposure_bound = _finite(
        "phase_b.exposure_match_bound",
        binding["exposure_match_max_abs_invested_weight_mismatch_bound"],
    )
    for segment, expected in decision["posthoc_realized_exposure_match"].items():
        if segment in {"noncausal_attribution_only", "matching_basis"}:
            continue
        actual = exposure_rows[segment]
        mismatch = _finite(
            f"phase_b.exposure.{segment}.mismatch",
            actual["max_abs_invested_weight_mismatch"],
        )
        if mismatch > exposure_bound:
            raise RuntimeError(f"Phase B realized-exposure match exceeds bound in {segment}")
        for key in (
            "max_abs_invested_weight_mismatch",
            "delta_CAGR",
            "delta_Sharpe",
            "delta_maximum_drawdown",
            "delta_Calmar",
        ):
            _close(f"phase_b.exposure.{segment}.{key}", actual[key], expected[key], tolerance)
            checks += 1

    contribution = decision["portfolio_contribution_audit"]
    generated_source = price_manifest["source"]["runtime_manifest"]
    if generated_source["snapshot_csv_sha256"] != contribution["price_snapshot_csv_sha256"]:
        raise RuntimeError("Phase B contribution frozen-price SHA drifted")
    expected_c = contribution["full_history_v66_reflation_override"]
    strategy_row = _single_row(summary, "Phase B summary", strategy="v66_reflation_override", segment=FULL_SEGMENT)
    _close(
        "phase_b.contribution.annualized_arithmetic_net_return",
        strategy_row["annualized_return"],
        expected_c["annualized_arithmetic_net_return"],
        tolerance,
    )
    checks += 1
    for asset_name in ASSETS:
        row = _single_row(
            asset,
            "Phase B asset contribution",
            strategy="v66_reflation_override",
            segment=FULL_SEGMENT,
            component=asset_name,
        )
        _close(
            f"phase_b.contribution.asset.{asset_name}",
            row["annualized_arithmetic_contribution"],
            expected_c["annualized_asset_contribution"][asset_name],
            tolerance,
        )
        checks += 1
    cost_row = _single_row(
        asset,
        "Phase B asset contribution",
        strategy="v66_reflation_override",
        segment=FULL_SEGMENT,
        component="transaction_cost_residual",
    )
    _close(
        "phase_b.contribution.transaction_cost_residual",
        cost_row["annualized_arithmetic_contribution"],
        expected_c["annualized_transaction_cost_residual"],
        tolerance,
    )
    checks += 1
    reflation = _single_row(
        regime,
        "Phase B regime contribution",
        strategy="v66_reflation_override",
        segment=FULL_SEGMENT,
        executed_lagged_regime="Reflation / Inflation Rising",
    )
    for asset_name in ASSETS:
        _close(
            f"phase_b.contribution.reflation_weight.{asset_name}",
            reflation[f"average_invested_weight_{asset_name}"],
            expected_c["reflation_realized_average_allocation"][asset_name],
            tolerance,
        )
        checks += 1
    _close(
        "phase_b.contribution.reflation_net",
        reflation["annualized_net_return_contribution"],
        expected_c["reflation_annualized_net_return_contribution"],
        tolerance,
    )
    checks += 1
    slowdown = _single_row(
        regime,
        "Phase B regime contribution",
        strategy="v66_reflation_override",
        segment=FULL_SEGMENT,
        executed_lagged_regime="Slowdown / Disinflation",
    )
    _close(
        "phase_b.contribution.slowdown_net",
        slowdown["annualized_net_return_contribution"],
        expected_c["slowdown_disinflation_annualized_net_return_contribution"],
        tolerance,
    )
    checks += 1
    neutral_reflation = _single_row(
        regime,
        "Phase B regime contribution",
        strategy="fixed_neutral_40_40_20",
        segment=FULL_SEGMENT,
        executed_lagged_regime="Reflation / Inflation Rising",
    )
    _close(
        "phase_b.contribution.fixed_neutral_reflation_net",
        neutral_reflation["annualized_net_return_contribution"],
        contribution["full_history_fixed_neutral_reflation_regime_contribution"],
        tolerance,
    )
    checks += 1
    recon_tol = _finite(
        "phase_b.contribution_reconciliation_tolerance",
        binding["contribution_reconciliation_tolerance"],
    )
    max_asset_recon = _finite(
        "phase_b.max_asset_reconciliation",
        reconciliation["asset_reconciliation_error"].abs().max(),
    )
    max_regime_recon = _finite(
        "phase_b.max_regime_reconciliation",
        reconciliation["regime_reconciliation_error"].abs().max(),
    )
    if max_asset_recon > recon_tol or max_regime_recon > recon_tol:
        raise RuntimeError("Phase B contribution reconciliation exceeds durable bound")
    _close(
        "phase_b.contribution.max_asset_reconciliation_error",
        max_asset_recon,
        contribution["max_abs_asset_reconciliation_error"],
        tolerance,
    )
    _close(
        "phase_b.contribution.max_regime_reconciliation_error",
        max_regime_recon,
        contribution["max_abs_regime_reconciliation_error"],
        tolerance,
    )
    checks += 2

    durable_episode = decision["posthoc_episode_concentration"]
    if _finite("phase_b.replay_error", episodes["phase_b_replay_max_abs_net_return_error"]) > _finite(
        "phase_b.replay_bound", durable_episode["phase_b_replay_max_abs_net_return_error_bound"]
    ):
        raise RuntimeError("Phase B replay error exceeds durable bound")
    episode_rows = {row["segment"]: row for row in episodes["summary_rows"]}
    for segment in ("development_pre2020", "post2019_reused_exploratory"):
        actual = episode_rows[segment]
        expected = durable_episode[segment]
        episode_name = f"{actual['largest_positive_episode_start']} through {actual['largest_positive_episode_end']}"
        if episode_name != expected["largest_positive_episode"]:
            raise RuntimeError(f"Phase B largest episode drifted in {segment}")
        if int(actual["reflation_episodes"]) != int(expected["reflation_episodes"]):
            raise RuntimeError(f"Phase B episode count drifted in {segment}")
        if int(actual["positive_reflation_episodes"]) != int(expected["positive_reflation_episodes"]):
            raise RuntimeError(f"Phase B positive episode count drifted in {segment}")
        mapping = {
            "normal_active_log_return": actual["normal_active_log_return"],
            "largest_positive_episode_active_log_including_exit_day": actual["screening_active_log_contribution_including_exit_day"],
            "top1_share_of_positive_episode_contribution": actual["top1_share_of_positive_episode_contribution"],
            "active_log_after_removing_largest_positive_episode": actual["active_log_after_removing_largest_positive_reflation_episode"],
            "leaveout_delta_CAGR": actual["incremental_after_leaveout"]["delta_CAGR"],
            "leaveout_delta_Sharpe": actual["incremental_after_leaveout"]["delta_Sharpe"],
            "leaveout_control_max_abs_invested_weight_mismatch": actual["leaveout_realized_exposure_matching"]["max_abs_invested_weight_mismatch"],
        }
        for key, value in mapping.items():
            _close(f"phase_b.episode.{segment}.{key}", value, expected[key], tolerance)
            checks += 1

    if decision["decision"]["recent_timing_robustness_demonstrated"] is not False:
        raise RuntimeError("Phase B durable robustness verdict drifted")

    return {
        "validated": True,
        "numeric_checks": int(checks),
        "numeric_tolerance": tolerance,
        "max_abs_exposure_mismatch": max(
            _finite("phase_b.exposure_mismatch", row["max_abs_invested_weight_mismatch"])
            for row in exposure_rows.values()
        ),
        "max_abs_asset_reconciliation_error": max_asset_recon,
        "max_abs_regime_reconciliation_error": max_regime_recon,
    }
