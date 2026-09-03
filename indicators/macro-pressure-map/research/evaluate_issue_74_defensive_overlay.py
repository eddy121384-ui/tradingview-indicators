#!/usr/bin/env python3
"""Evaluate preregistered Issue #74 Phases A/B, and fail closed for Phase C.

This evaluator consumes only committed frozen outcome prices and frozen Issue
#64 core-regime transitions. It never downloads outcome data. Phase C remains
blocked until the exact daily raw IPI evidence required for IPI >= +60 is also
frozen from the prior hash-matching Pine parity log.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
import pandas as pd

from asset_allocation_phase_a_frozen import load_frozen_transitions, map_regimes_to_outcome_calendar
from issue_74_outcome_snapshot import load_frozen_prices
from issue_74_portfolio import (
    build_core_regime_targets,
    compare_strategies,
    month_start_mask,
    simulate_portfolio,
    summarize_strategies,
    template_change_mask,
)
import issue_74_severe_inflation as severe_evidence

HERE = Path(__file__).resolve().parent
CONTRACT_PATH = HERE / "decisions" / "issue-74-defensive-overlay-preregistered.json"
EVAL_END = pd.Timestamp("2026-08-14")


def load_contract() -> dict:
    contract = json.loads(CONTRACT_PATH.read_text(encoding="utf-8"))
    if contract.get("issue") != 74 or contract.get("frozen_before_issue_74_portfolio_results_viewed") is not True:
        raise ValueError("Issue #74 preregistration identity/freeze is invalid")
    if contract.get("production_v66_parameters_modified") is not False:
        raise ValueError("Issue #74 may not modify production V6.6")
    if float(contract["source_dependency"]["v66_inflation_extreme_threshold"]) != 60.0:
        raise ValueError("Issue #74 severe inflation threshold must remain V6.6 +60")
    return contract


def common_evaluation(
    prices: pd.DataFrame,
    history: pd.DataFrame,
) -> tuple[pd.DatetimeIndex, pd.DataFrame, pd.Series]:
    prices = prices.loc[prices.index <= EVAL_END].copy()
    history = history.reindex(prices.index)
    returns_all = prices.pct_change(fill_method=None)
    regimes = history["core_regime"]
    lagged = regimes.shift(1)
    valid = returns_all.notna().all(axis=1) & lagged.notna()
    dates = valid.index[valid]
    if dates.empty:
        raise RuntimeError("Issue #74 has no common finite evaluation dates")
    eval_index = prices.index[(prices.index >= dates[0]) & (prices.index <= EVAL_END)]
    if not returns_all.loc[eval_index].notna().all(axis=None) or not lagged.loc[eval_index].notna().all():
        raise RuntimeError("Issue #74 evaluation window contains missing returns or lagged regime")
    return eval_index, returns_all, regimes


def _templates_for_assets(template_block: dict, names: list[str], assets: tuple[str, ...]) -> dict[str, dict[str, float]]:
    return {name: {asset: float(template_block[name][asset]) for asset in assets} for name in names}


def build_phase_ab_targets(
    eval_index: pd.DatetimeIndex,
    regimes: pd.Series,
    contract: dict,
) -> tuple[dict[str, pd.DataFrame], dict[str, pd.Series], dict[str, pd.Series]]:
    assets = ("SPY", "TLT", "SHV")
    reflation_regime = contract["core_regimes"]["reflation"]
    stagflation_regime = contract["core_regimes"]["stagflation"]
    phase_a = contract["phase_a"]["templates"]
    phase_b = contract["phase_b"]["templates"]

    neutral = {a: float(phase_a["neutral"][a]) for a in assets}
    reflation = {a: float(phase_a["reflation"][a]) for a in assets}
    stag_a = {a: float(phase_a["stagflation_cash_substitution"][a]) for a in assets}
    stag_b = {a: float(phase_b["stagflation_defensive"][a]) for a in assets}

    refl_targets, refl_template = build_core_regime_targets(
        regimes,
        assets=assets,
        neutral=neutral,
        reflation=reflation,
        stagflation=None,
        reflation_regime=reflation_regime,
        stagflation_regime=stagflation_regime,
    )
    a_targets, a_template = build_core_regime_targets(
        regimes,
        assets=assets,
        neutral=neutral,
        reflation=reflation,
        stagflation=stag_a,
        reflation_regime=reflation_regime,
        stagflation_regime=stagflation_regime,
    )
    b_targets, b_template = build_core_regime_targets(
        regimes,
        assets=assets,
        neutral=neutral,
        reflation=reflation,
        stagflation=stag_b,
        reflation_regime=reflation_regime,
        stagflation_regime=stagflation_regime,
    )
    fixed = pd.DataFrame(np.tile([neutral[a] for a in assets], (len(regimes), 1)), index=regimes.index, columns=list(assets))
    fixed_template = pd.Series("neutral", index=regimes.index, dtype="object")

    targets = {
        "fixed_neutral": fixed.loc[eval_index],
        "reflation_only": refl_targets.loc[eval_index],
        "phase_a_cash_substitution": a_targets.loc[eval_index],
        "phase_b_defensive_cash": b_targets.loc[eval_index],
    }
    templates = {
        "fixed_neutral": fixed_template.loc[eval_index],
        "reflation_only": refl_template.loc[eval_index],
        "phase_a_cash_substitution": a_template.loc[eval_index],
        "phase_b_defensive_cash": b_template.loc[eval_index],
    }
    monthly = month_start_mask(eval_index)
    rebalance = {
        "fixed_neutral": monthly,
        "reflation_only": (monthly | template_change_mask(templates["reflation_only"])).astype(bool),
        "phase_a_cash_substitution": (monthly | template_change_mask(templates["phase_a_cash_substitution"])).astype(bool),
        "phase_b_defensive_cash": (monthly | template_change_mask(templates["phase_b_defensive_cash"])).astype(bool),
    }
    return targets, rebalance, templates


def contribution_tables(
    simulations: dict[str, pd.DataFrame],
    returns: pd.DataFrame,
    lagged_regime: pd.Series,
    annualization: int,
) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    segments = {
        "full_reused_history": (None, None),
        "development_pre2020": (None, "2019-12-31"),
        "post2019_reused_exploratory": ("2020-01-01", None),
    }
    asset_rows: list[dict] = []
    regime_rows: list[dict] = []
    recon_rows: list[dict] = []
    for strategy, sim in simulations.items():
        assets = tuple(returns.columns)
        gross_asset_daily = pd.DataFrame(index=sim.index)
        for asset in assets:
            gross_asset_daily[asset] = sim[f"invested_weight_{asset}"] * returns.loc[sim.index, asset]
        asset_recon = gross_asset_daily.sum(axis=1) - sim["gross_asset_mix_return"]
        cost_residual = sim["net_return"] - sim["gross_asset_mix_return"]
        for segment, (start, end) in segments.items():
            mask = pd.Series(True, index=sim.index)
            if start is not None:
                mask &= sim.index >= pd.Timestamp(start)
            if end is not None:
                mask &= sim.index <= pd.Timestamp(end)
            dates = sim.index[mask.to_numpy()]
            if len(dates) == 0:
                continue
            for asset in assets:
                series = gross_asset_daily.loc[dates, asset]
                asset_rows.append({
                    "strategy": strategy,
                    "segment": segment,
                    "asset": asset,
                    "annualized_arithmetic_contribution": float(series.mean() * annualization),
                    "cumulative_arithmetic_contribution": float(series.sum()),
                })
            cost = cost_residual.loc[dates]
            asset_rows.append({
                "strategy": strategy,
                "segment": segment,
                "asset": "transaction_cost_residual",
                "annualized_arithmetic_contribution": float(cost.mean() * annualization),
                "cumulative_arithmetic_contribution": float(cost.sum()),
            })
            regimes = lagged_regime.loc[dates]
            for regime in sorted(regimes.dropna().unique()):
                rdates = dates[regimes.eq(regime).to_numpy()]
                if len(rdates) == 0:
                    continue
                row = {
                    "strategy": strategy,
                    "segment": segment,
                    "regime": regime,
                    "observations": int(len(rdates)),
                    "annualized_net_contribution": float(sim.loc[rdates, "net_return"].sum() / len(dates) * annualization),
                    "cumulative_net_contribution": float(sim.loc[rdates, "net_return"].sum()),
                }
                for asset in assets:
                    row[f"average_invested_weight_{asset}"] = float(sim.loc[rdates, f"invested_weight_{asset}"].mean())
                regime_rows.append(row)
            net = sim.loc[dates, "net_return"]
            accounted = gross_asset_daily.loc[dates].sum(axis=1) + cost_residual.loc[dates]
            recon_rows.append({
                "strategy": strategy,
                "segment": segment,
                "max_abs_daily_asset_mix_reconciliation": float(asset_recon.loc[dates].abs().max()),
                "max_abs_daily_net_reconciliation": float((net - accounted).abs().max()),
            })
    return pd.DataFrame(asset_rows), pd.DataFrame(regime_rows), pd.DataFrame(recon_rows)


def episode_concentration(
    simulations: dict[str, pd.DataFrame],
    lagged_regime: pd.Series,
    *,
    lhs: str,
    rhs: str,
    comparison: str,
    stagflation_regime: str,
) -> pd.DataFrame:
    left = simulations[lhs]["net_return"]
    right = simulations[rhs]["net_return"]
    active_log = np.log1p(left) - np.log1p(right)
    regime = lagged_regime.reindex(active_log.index)
    is_stag = regime.eq(stagflation_regime)
    episode_id = is_stag.ne(is_stag.shift(1)).cumsum()
    rows: list[dict] = []
    segments = {
        "full_reused_history": (None, None),
        "development_pre2020": (None, "2019-12-31"),
        "post2019_reused_exploratory": ("2020-01-01", None),
    }
    for segment, (start, end) in segments.items():
        mask = pd.Series(True, index=active_log.index)
        if start is not None:
            mask &= active_log.index >= pd.Timestamp(start)
        if end is not None:
            mask &= active_log.index <= pd.Timestamp(end)
        seg_dates = active_log.index[mask.to_numpy()]
        stag_dates = seg_dates[is_stag.loc[seg_dates].to_numpy()]
        episodes: list[dict] = []
        for _, dates_series in pd.Series(stag_dates, index=stag_dates).groupby(episode_id.loc[stag_dates]):
            dates = pd.DatetimeIndex(dates_series.to_numpy())
            if len(dates) == 0:
                continue
            episodes.append({
                "start": dates.min(),
                "end": dates.max(),
                "observations": len(dates),
                "active_log_return": float(active_log.loc[dates].sum()),
            })
        total = float(active_log.loc[seg_dates].sum()) if len(seg_dates) else np.nan
        if episodes:
            winner = max(episodes, key=lambda item: item["active_log_return"])
            removed = total - float(winner["active_log_return"])
            rows.append({
                "comparison": comparison,
                "segment": segment,
                "active_log_return_all": total,
                "stagflation_episodes": len(episodes),
                "largest_winning_episode_start": winner["start"].date().isoformat(),
                "largest_winning_episode_end": winner["end"].date().isoformat(),
                "largest_winning_episode_observations": int(winner["observations"]),
                "largest_winning_episode_active_log_return": float(winner["active_log_return"]),
                "active_log_return_ex_largest_winner": float(removed),
                "sign_flips_after_removal": bool(np.isfinite(total) and total > 0.0 and removed < 0.0),
            })
        else:
            rows.append({
                "comparison": comparison,
                "segment": segment,
                "active_log_return_all": total,
                "stagflation_episodes": 0,
                "largest_winning_episode_start": None,
                "largest_winning_episode_end": None,
                "largest_winning_episode_observations": 0,
                "largest_winning_episode_active_log_return": np.nan,
                "active_log_return_ex_largest_winner": total,
                "sign_flips_after_removal": False,
            })
    return pd.DataFrame(rows)


def run(output_dir: Path) -> dict:
    contract = load_contract()
    prices, price_manifest = load_frozen_prices(start="2007-01-01", end="2026-08-25")
    transitions = load_frozen_transitions()
    history = map_regimes_to_outcome_calendar(prices, transitions)
    eval_index, returns_all, regimes = common_evaluation(prices, history)
    returns = returns_all.loc[eval_index, ["SPY", "TLT", "SHV"]]
    targets, rebalance, templates = build_phase_ab_targets(eval_index, regimes, contract)
    cost = float(contract["execution"]["primary_cost_bps_per_one_way_turnover"])
    simulations = {
        name: simulate_portfolio(returns, target, rebalance[name], cost_bps=cost, name=name)
        for name, target in targets.items()
    }
    annualization = int(contract["execution"]["annualization_trading_rows"])
    summary = summarize_strategies(simulations, annualization=annualization)
    comparisons = pd.concat([
        compare_strategies(summary, "phase_a_cash_substitution", "reflation_only", "phase_a_minus_reflation_only"),
        compare_strategies(summary, "phase_b_defensive_cash", "phase_a_cash_substitution", "phase_b_minus_phase_a"),
        compare_strategies(summary, "phase_b_defensive_cash", "reflation_only", "phase_b_minus_reflation_only"),
    ], ignore_index=True)

    sensitivity_rows: list[dict] = []
    sensitivity_costs = [0.0, cost, 10.0]
    for bps in sorted(set(sensitivity_costs)):
        sims = {
            name: simulate_portfolio(returns, target, rebalance[name], cost_bps=bps, name=name)
            for name, target in targets.items()
        }
        block = summarize_strategies(sims, annualization=annualization)
        for row in block.itertuples(index=False):
            sensitivity_rows.append({"cost_bps": bps, **row._asdict()})
    sensitivity = pd.DataFrame(sensitivity_rows)

    lagged_regime = regimes.shift(1).loc[eval_index]
    asset_contrib, regime_contrib, reconciliation = contribution_tables(
        simulations, returns, lagged_regime, annualization
    )
    concentration = pd.concat([
        episode_concentration(
            simulations,
            lagged_regime,
            lhs="phase_a_cash_substitution",
            rhs="reflation_only",
            comparison="phase_a_minus_reflation_only",
            stagflation_regime=contract["core_regimes"]["stagflation"],
        ),
        episode_concentration(
            simulations,
            lagged_regime,
            lhs="phase_b_defensive_cash",
            rhs="phase_a_cash_substitution",
            comparison="phase_b_minus_phase_a",
            stagflation_regime=contract["core_regimes"]["stagflation"],
        ),
    ], ignore_index=True)

    if reconciliation[["max_abs_daily_asset_mix_reconciliation", "max_abs_daily_net_reconciliation"]].to_numpy(float).max() > 2e-12:
        raise AssertionError("Issue #74 contribution accounting does not reconcile")

    output_dir.mkdir(parents=True, exist_ok=True)
    daily = pd.concat([sim.reset_index() for sim in simulations.values()], ignore_index=True)
    daily.to_csv(output_dir / "issue-74-phase-ab-daily.csv", index=False, date_format="%Y-%m-%d")
    summary.to_csv(output_dir / "issue-74-phase-ab-summary.csv", index=False)
    comparisons.to_csv(output_dir / "issue-74-phase-ab-comparisons.csv", index=False)
    sensitivity.to_csv(output_dir / "issue-74-phase-ab-cost-sensitivity.csv", index=False)
    asset_contrib.to_csv(output_dir / "issue-74-phase-ab-asset-contribution.csv", index=False)
    regime_contrib.to_csv(output_dir / "issue-74-phase-ab-regime-contribution.csv", index=False)
    reconciliation.to_csv(output_dir / "issue-74-phase-ab-reconciliation.csv", index=False)
    concentration.to_csv(output_dir / "issue-74-phase-ab-episode-concentration.csv", index=False)

    phase_c_available = severe_evidence.available()
    phase_c_gate = {
        "status": "READY" if phase_c_available else "BLOCKED_MISSING_EXACT_DAILY_IPI_EVIDENCE",
        "required_condition": "lagged Stagflation Pressure AND lagged raw IPI >= +60.0",
        "threshold_source": "existing V6.6 inflationExtremeThreshold",
        "core_regime_data_sufficient": True,
        "committed_issue_64_sparse_axis_audit_sufficient_for_phase_c": False,
        "portfolio_phase_c_calculated": False,
    }
    (output_dir / "issue-74-phase-c-gate.json").write_text(
        json.dumps(phase_c_gate, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )

    manifest = {
        "schema_version": 1,
        "issue": 74,
        "phase": "A+B",
        "purpose": "preregistered cash substitution and defensive cash overlay",
        "contract_path": str(CONTRACT_PATH.relative_to(HERE)),
        "contract_frozen_before_results": True,
        "evidence_status": contract["evidence_status"],
        "price_data": price_manifest,
        "evaluation_first_date": eval_index.min().date().isoformat(),
        "evaluation_last_date": eval_index.max().date().isoformat(),
        "evaluation_rows": int(len(eval_index)),
        "primary_cost_bps": cost,
        "v66_parameters_modified": False,
        "optimizer_used": False,
        "weight_sweep_performed": False,
        "commodity_momentum_used": False,
        "phase_c": phase_c_gate,
    }
    (output_dir / "issue-74-phase-ab-manifest.json").write_text(
        json.dumps(manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )

    full = summary.loc[summary["segment"].eq("full_reused_history")]
    full_cmp = comparisons.loc[comparisons["segment"].eq("full_reused_history")]
    report = [
        "# Issue #74 — preregistered cash-defense overlay Phase A/B",
        "",
        f"Evaluation: {manifest['evaluation_first_date']} through {manifest['evaluation_last_date']} ({manifest['evaluation_rows']} rows).",
        f"Primary cost: {cost:.1f} bp per 100% one-way turnover.",
        "",
        "All results are reused/development historical evidence, not untouched OOS confirmation.",
        "",
        "## Full reused-history strategies",
        "",
    ]
    for row in full.itertuples(index=False):
        report.append(
            f"- {row.strategy}: CAGR {row.CAGR:.4%}; Sharpe {row.Sharpe:.3f}; max DD {row.maximum_drawdown:.4%}; Calmar {row.Calmar:.3f}; turnover {row.annualized_turnover:.3f}x/year."
        )
    report.extend(["", "## Preregistered incremental comparisons", ""])
    for row in full_cmp.itertuples(index=False):
        report.append(
            f"- {row.comparison}: ΔCAGR {row.delta_CAGR:.4%}; ΔSharpe {row.delta_Sharpe:.3f}; ΔmaxDD {row.delta_maximum_drawdown:.4%}; ΔCalmar {row.delta_Calmar:.3f}."
        )
    report.extend([
        "",
        "## Phase C gate",
        "",
        f"- {phase_c_gate['status']}. Phase C portfolio PnL was not calculated.",
    ])
    (output_dir / "issue-74-phase-ab-report.md").write_text("\n".join(report) + "\n", encoding="utf-8")
    return manifest


def main() -> int:
    parser = argparse.ArgumentParser(description="Evaluate Issue #74 preregistered Phase A/B")
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args()
    print(json.dumps(run(args.output_dir), indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
