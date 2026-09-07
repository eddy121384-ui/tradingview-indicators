#!/usr/bin/env python3
"""Evaluate preregistered Issue #74 Phase C from frozen evidence only."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
import pandas as pd

from asset_allocation_phase_a_frozen import load_frozen_transitions, map_regimes_to_outcome_calendar
from evaluate_issue_74_defensive_overlay import common_evaluation, load_contract
from issue_74_outcome_snapshot import load_frozen_prices
from issue_74_portfolio import (
    build_core_regime_targets,
    build_severe_inflation_targets,
    compare_strategies,
    month_start_mask,
    simulate_portfolio,
    summarize_strategies,
    template_change_mask,
)
import issue_74_severe_inflation as severe_evidence

HERE = Path(__file__).resolve().parent


def four_asset_phase_b_templates(contract: dict) -> tuple[dict[str, float], dict[str, float], dict[str, float]]:
    b = contract["phase_b"]["templates"]
    neutral = {"SPY": float(b["neutral"]["SPY"]), "TLT": float(b["neutral"]["TLT"]), "SHV": float(b["neutral"]["SHV"]), "GSG": 0.0}
    reflation = {"SPY": float(b["reflation"]["SPY"]), "TLT": float(b["reflation"]["TLT"]), "SHV": float(b["reflation"]["SHV"]), "GSG": 0.0}
    stag = {"SPY": float(b["stagflation_defensive"]["SPY"]), "TLT": float(b["stagflation_defensive"]["TLT"]), "SHV": float(b["stagflation_defensive"]["SHV"]), "GSG": 0.0}
    return neutral, reflation, stag


def episode_concentration(active_log: pd.Series, active_mask: pd.Series) -> pd.DataFrame:
    rows: list[dict] = []
    segments = {
        "full_reused_history": (None, None),
        "development_pre2020": (None, "2019-12-31"),
        "post2019_reused_exploratory": ("2020-01-01", None),
    }
    active_mask = active_mask.reindex(active_log.index).fillna(False).astype(bool)
    episode_id = active_mask.ne(active_mask.shift(1)).cumsum()
    for segment, (start, end) in segments.items():
        mask = pd.Series(True, index=active_log.index)
        if start is not None:
            mask &= active_log.index >= pd.Timestamp(start)
        if end is not None:
            mask &= active_log.index <= pd.Timestamp(end)
        dates = active_log.index[mask.to_numpy()]
        active_dates = dates[active_mask.loc[dates].to_numpy()]
        episodes: list[dict] = []
        for _, group in pd.Series(active_dates, index=active_dates).groupby(episode_id.loc[active_dates]):
            edates = pd.DatetimeIndex(group.to_numpy())
            if len(edates) == 0:
                continue
            episodes.append({
                "start": edates.min(),
                "end": edates.max(),
                "observations": len(edates),
                "active_log_return": float(active_log.loc[edates].sum()),
            })
        total = float(active_log.loc[active_dates].sum()) if len(active_dates) else np.nan
        winner = max(episodes, key=lambda x: x["active_log_return"]) if episodes else None
        removed = total - float(winner["active_log_return"]) if winner else total
        rows.append({
            "segment": segment,
            "active_log_return_all": total,
            "activation_episodes": len(episodes),
            "largest_winning_episode_start": winner["start"].date().isoformat() if winner else None,
            "largest_winning_episode_end": winner["end"].date().isoformat() if winner else None,
            "largest_winning_episode_observations": int(winner["observations"]) if winner else 0,
            "largest_winning_episode_active_log_return": float(winner["active_log_return"]) if winner else np.nan,
            "active_log_return_ex_largest_winner": float(removed),
            "sign_flips_after_removal": bool(np.isfinite(total) and total > 0.0 and removed < 0.0),
        })
    return pd.DataFrame(rows)


def reporting_tables(
    sims: dict[str, pd.DataFrame],
    returns: pd.DataFrame,
    lagged_regime: pd.Series,
    assets: tuple[str, ...],
    annualization: int,
) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """Emit preregistered asset/regime allocation and contribution diagnostics."""
    segments = {
        "full_reused_history": (None, None),
        "development_pre2020": (None, "2019-12-31"),
        "post2019_reused_exploratory": ("2020-01-01", None),
    }
    asset_rows: list[dict] = []
    regime_rows: list[dict] = []
    recon_rows: list[dict] = []
    for strategy, sim in sims.items():
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
            segment_regime = lagged_regime.loc[dates]
            for regime in sorted(segment_regime.dropna().unique()):
                rdates = dates[segment_regime.eq(regime).to_numpy()]
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


def run(output_dir: Path) -> dict:
    contract = load_contract()
    prices, price_manifest = load_frozen_prices(start="2007-01-01", end="2026-08-25")
    transitions = load_frozen_transitions()
    history = map_regimes_to_outcome_calendar(prices, transitions)
    eval_index, returns_all, regimes = common_evaluation(prices, history)
    assets = ("SPY", "TLT", "SHV", "GSG")
    returns = returns_all.loc[eval_index, list(assets)]

    severe_flag_full, severe_manifest = severe_evidence.severe_flag_on_calendar(regimes.index)
    threshold = float(contract["source_dependency"]["v66_inflation_extreme_threshold"])
    raw_ipi_gate = severe_flag_full.astype(float) * threshold

    neutral, reflation, stag = four_asset_phase_b_templates(contract)
    severe_template = {a: float(contract["phase_c"]["templates"]["severe_inflation_stagflation"][a]) for a in assets}
    reflation_regime = contract["core_regimes"]["reflation"]
    stagflation_regime = contract["core_regimes"]["stagflation"]

    b_targets, b_template = build_core_regime_targets(
        regimes,
        assets=assets,
        neutral=neutral,
        reflation=reflation,
        stagflation=stag,
        reflation_regime=reflation_regime,
        stagflation_regime=stagflation_regime,
    )
    c_targets, c_template = build_severe_inflation_targets(
        regimes,
        raw_ipi_gate,
        assets=assets,
        neutral=neutral,
        reflation=reflation,
        stagflation=stag,
        severe_stagflation=severe_template,
        reflation_regime=reflation_regime,
        stagflation_regime=stagflation_regime,
        inflation_extreme_threshold=threshold,
    )
    b_targets, c_targets = b_targets.loc[eval_index], c_targets.loc[eval_index]
    b_template, c_template = b_template.loc[eval_index], c_template.loc[eval_index]

    monthly = month_start_mask(eval_index)
    b_rebalance = (monthly | template_change_mask(b_template)).astype(bool)
    c_rebalance = (monthly | template_change_mask(c_template)).astype(bool)
    cost = float(contract["execution"]["primary_cost_bps_per_one_way_turnover"])
    sims = {
        "phase_b_defensive_cash_4asset": simulate_portfolio(returns, b_targets, b_rebalance, cost_bps=cost, name="phase_b_defensive_cash_4asset"),
        "phase_c_severe_inflation_commodity": simulate_portfolio(returns, c_targets, c_rebalance, cost_bps=cost, name="phase_c_severe_inflation_commodity"),
    }
    annualization = int(contract["execution"]["annualization_trading_rows"])
    summary = summarize_strategies(sims, annualization=annualization)
    comparison = compare_strategies(summary, "phase_c_severe_inflation_commodity", "phase_b_defensive_cash_4asset", "phase_c_minus_phase_b")

    sensitivity_rows: list[dict] = []
    for bps in sorted({0.0, cost, 10.0}):
        local = {
            "phase_b_defensive_cash_4asset": simulate_portfolio(returns, b_targets, b_rebalance, cost_bps=bps, name="phase_b_defensive_cash_4asset"),
            "phase_c_severe_inflation_commodity": simulate_portfolio(returns, c_targets, c_rebalance, cost_bps=bps, name="phase_c_severe_inflation_commodity"),
        }
        block = summarize_strategies(local, annualization=annualization)
        cmp = compare_strategies(block, "phase_c_severe_inflation_commodity", "phase_b_defensive_cash_4asset", "phase_c_minus_phase_b")
        for row in cmp.itertuples(index=False):
            sensitivity_rows.append({"cost_bps": bps, **row._asdict()})
    sensitivity = pd.DataFrame(sensitivity_rows)

    activation = c_template.eq("severe_inflation_stagflation")
    expected_activation = regimes.shift(1).loc[eval_index].eq(stagflation_regime) & severe_flag_full.shift(1).loc[eval_index].fillna(False)
    if not activation.equals(expected_activation.astype(bool)):
        raise AssertionError("Phase C activation differs from preregistered lagged Stagflation + IPI>=60 rule")

    active_log = np.log1p(sims["phase_c_severe_inflation_commodity"]["net_return"]) - np.log1p(sims["phase_b_defensive_cash_4asset"]["net_return"])
    concentration = episode_concentration(active_log, activation)

    phase_b_sim = sims["phase_b_defensive_cash_4asset"]
    phase_c_sim = sims["phase_c_severe_inflation_commodity"]
    realized_asset_delta = pd.DataFrame(index=eval_index)
    for asset in assets:
        realized_asset_delta[asset] = (
            phase_c_sim[f"invested_weight_{asset}"] - phase_b_sim[f"invested_weight_{asset}"]
        ) * returns[asset]
    realized_gross_delta = phase_c_sim["gross_asset_mix_return"] - phase_b_sim["gross_asset_mix_return"]
    realized_cost_delta = (
        (phase_c_sim["net_return"] - phase_c_sim["gross_asset_mix_return"])
        - (phase_b_sim["net_return"] - phase_b_sim["gross_asset_mix_return"])
    )
    realized_net_delta = phase_c_sim["net_return"] - phase_b_sim["net_return"]
    attribution_recon = realized_asset_delta.sum(axis=1) - realized_gross_delta
    net_recon = realized_gross_delta + realized_cost_delta - realized_net_delta
    if float(attribution_recon.abs().max()) > 2e-12:
        raise AssertionError("Phase C realized-weight attribution does not reconcile to gross return difference")
    if float(net_recon.abs().max()) > 2e-12:
        raise AssertionError("Phase C gross plus cost attribution does not reconcile to net return difference")

    attribution_rows: list[dict] = []
    for segment, (start, end) in {
        "full_reused_history": (None, None),
        "development_pre2020": (None, "2019-12-31"),
        "post2019_reused_exploratory": ("2020-01-01", None),
    }.items():
        segment_mask = pd.Series(True, index=eval_index)
        if start is not None:
            segment_mask &= eval_index >= pd.Timestamp(start)
        if end is not None:
            segment_mask &= eval_index <= pd.Timestamp(end)
        segment_dates = eval_index[segment_mask.to_numpy()]
        active_dates = segment_dates[activation.loc[segment_dates].to_numpy()]
        inactive_dates = segment_dates[~activation.loc[segment_dates].to_numpy()]
        nonzero_inactive_gross_dates = inactive_dates[realized_gross_delta.loc[inactive_dates].abs().to_numpy() > 1e-15]
        nonzero_inactive_cost_dates = inactive_dates[realized_cost_delta.loc[inactive_dates].abs().to_numpy() > 1e-15]
        nonzero_inactive_net_dates = inactive_dates[realized_net_delta.loc[inactive_dates].abs().to_numpy() > 1e-15]

        gross_all = realized_gross_delta.loc[segment_dates]
        gross_active = realized_gross_delta.loc[active_dates]
        gross_inactive = realized_gross_delta.loc[inactive_dates]
        cost_all = realized_cost_delta.loc[segment_dates]
        cost_active = realized_cost_delta.loc[active_dates]
        cost_inactive = realized_cost_delta.loc[inactive_dates]
        net_all = realized_net_delta.loc[segment_dates]
        net_active = realized_net_delta.loc[active_dates]
        net_inactive = realized_net_delta.loc[inactive_dates]
        row = {
            "segment": segment,
            "segment_rows": int(len(segment_dates)),
            "activation_rows": int(len(active_dates)),
            "inactive_rows_with_nonzero_realized_gross_delta": int(len(nonzero_inactive_gross_dates)),
            "inactive_rows_with_nonzero_cost_delta": int(len(nonzero_inactive_cost_dates)),
            "inactive_rows_with_nonzero_net_delta": int(len(nonzero_inactive_net_dates)),
            "mean_daily_realized_gross_phase_c_minus_phase_b": float(gross_all.mean()) if len(segment_dates) else np.nan,
            "cumulative_arithmetic_realized_gross_phase_c_minus_phase_b": float(gross_all.sum()) if len(segment_dates) else 0.0,
            "annualized_arithmetic_realized_gross_phase_c_minus_phase_b_over_all_segment_rows": float(gross_all.mean() * annualization) if len(segment_dates) else np.nan,
            "cumulative_active_state_realized_gross_delta": float(gross_active.sum()) if len(active_dates) else 0.0,
            "cumulative_inactive_residual_realized_gross_delta": float(gross_inactive.sum()) if len(inactive_dates) else 0.0,
            "cumulative_transaction_cost_residual_delta": float(cost_all.sum()) if len(segment_dates) else 0.0,
            "cumulative_active_state_transaction_cost_residual_delta": float(cost_active.sum()) if len(active_dates) else 0.0,
            "cumulative_inactive_transaction_cost_residual_delta": float(cost_inactive.sum()) if len(inactive_dates) else 0.0,
            "cumulative_arithmetic_net_phase_c_minus_phase_b": float(net_all.sum()) if len(segment_dates) else 0.0,
            "cumulative_active_state_net_delta": float(net_active.sum()) if len(active_dates) else 0.0,
            "cumulative_inactive_net_delta": float(net_inactive.sum()) if len(inactive_dates) else 0.0,
            "annualized_arithmetic_net_phase_c_minus_phase_b_over_all_segment_rows": float(net_all.mean() * annualization) if len(segment_dates) else np.nan,
            "max_abs_daily_attribution_reconciliation": float(attribution_recon.loc[segment_dates].abs().max()) if len(segment_dates) else 0.0,
            "max_abs_daily_net_reconciliation": float(net_recon.loc[segment_dates].abs().max()) if len(segment_dates) else 0.0,
        }
        for asset in assets:
            contribution_all = realized_asset_delta.loc[segment_dates, asset]
            contribution_active = realized_asset_delta.loc[active_dates, asset]
            contribution_inactive = realized_asset_delta.loc[inactive_dates, asset]
            row[f"cumulative_realized_weight_delta_contribution_{asset}"] = float(contribution_all.sum()) if len(segment_dates) else 0.0
            row[f"cumulative_active_state_weight_delta_contribution_{asset}"] = float(contribution_active.sum()) if len(active_dates) else 0.0
            row[f"cumulative_inactive_residual_weight_delta_contribution_{asset}"] = float(contribution_inactive.sum()) if len(inactive_dates) else 0.0
        attribution_rows.append(row)
    attribution = pd.DataFrame(attribution_rows)

    lagged_regime = regimes.shift(1).loc[eval_index]
    asset_contrib, regime_contrib, reporting_recon = reporting_tables(
        sims, returns, lagged_regime, assets, annualization
    )
    if reporting_recon[["max_abs_daily_asset_mix_reconciliation", "max_abs_daily_net_reconciliation"]].to_numpy(float).max() > 2e-12:
        raise AssertionError("Issue #74 Phase C preregistered reporting tables do not reconcile")

    output_dir.mkdir(parents=True, exist_ok=True)
    summary.to_csv(output_dir / "issue-74-phase-c-summary.csv", index=False)
    comparison.to_csv(output_dir / "issue-74-phase-c-comparison.csv", index=False)
    sensitivity.to_csv(output_dir / "issue-74-phase-c-cost-sensitivity.csv", index=False)
    concentration.to_csv(output_dir / "issue-74-phase-c-episode-concentration.csv", index=False)
    attribution.to_csv(output_dir / "issue-74-phase-c-attribution.csv", index=False)
    asset_contrib.to_csv(output_dir / "issue-74-phase-c-asset-contribution.csv", index=False)
    regime_contrib.to_csv(output_dir / "issue-74-phase-c-regime-contribution.csv", index=False)
    reporting_recon.to_csv(output_dir / "issue-74-phase-c-reporting-reconciliation.csv", index=False)
    pd.DataFrame({
        "date": eval_index,
        "core_regime": regimes.loc[eval_index].to_numpy(),
        "severe_inflation_today": severe_flag_full.loc[eval_index].to_numpy(),
        "phase_c_template": c_template.to_numpy(),
        "phase_c_active": activation.to_numpy(),
        "phase_b_net_return": phase_b_sim["net_return"].to_numpy(),
        "phase_c_net_return": phase_c_sim["net_return"].to_numpy(),
        "phase_c_minus_phase_b_gross_delta": realized_gross_delta.to_numpy(),
        "phase_c_minus_phase_b_cost_residual_delta": realized_cost_delta.to_numpy(),
        "phase_c_minus_phase_b_net_delta": realized_net_delta.to_numpy(),
    }).to_csv(output_dir / "issue-74-phase-c-daily.csv", index=False, date_format="%Y-%m-%d")

    manifest = {
        "schema_version": 2,
        "issue": 74,
        "phase": "C",
        "purpose": "preregistered severe-inflation commodity satellite",
        "evidence_status": contract["evidence_status"],
        "evaluation_first_date": eval_index.min().date().isoformat(),
        "evaluation_last_date": eval_index.max().date().isoformat(),
        "evaluation_rows": int(len(eval_index)),
        "activation_rows": int(activation.sum()),
        "activation_first_date": activation.index[activation].min().date().isoformat() if activation.any() else None,
        "activation_last_date": activation.index[activation].max().date().isoformat() if activation.any() else None,
        "primary_cost_bps": cost,
        "threshold": threshold,
        "threshold_source": "existing V6.6 inflationExtremeThreshold",
        "severe_evidence": severe_manifest,
        "price_data": price_manifest,
        "reporting_contract_completed": {
            "average_allocation_by_regime": True,
            "asset_contribution": True,
            "regime_contribution": True,
            "episode_concentration": True,
            "leave_largest_winning_episode_out": True,
            "exposure_matched_attribution_where_feasible": True,
        },
        "v66_parameters_modified": False,
        "optimizer_used": False,
        "weight_sweep_performed": False,
        "commodity_momentum_used": False,
        "oil_only_rescue_test_used": False,
    }
    (output_dir / "issue-74-phase-c-manifest.json").write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    full = comparison.loc[comparison["segment"].eq("full_reused_history")].iloc[0]
    report = [
        "# Issue #74 — preregistered Phase C severe-inflation commodity satellite",
        "",
        f"Evaluation: {manifest['evaluation_first_date']} through {manifest['evaluation_last_date']} ({manifest['evaluation_rows']} rows).",
        f"Activation: lagged Stagflation Pressure AND lagged raw IPI >= +60; {manifest['activation_rows']} active rows.",
        f"Primary cost: {cost:.1f} bp per 100% one-way turnover.",
        "",
        "All history remains reused/development evidence, not untouched OOS confirmation.",
        "",
        "## Full reused-history incremental result: Phase C minus Phase B",
        "",
        f"- ΔCAGR {full.delta_CAGR:.6%}",
        f"- ΔSharpe {full.delta_Sharpe:.6f}",
        f"- Δmax drawdown {full.delta_maximum_drawdown:.6%}",
        f"- ΔCalmar {full.delta_Calmar:.6f}",
        f"- Δannualized turnover {full.delta_annualized_turnover:.6f}x/year",
        "",
        "Gross attribution uses realized invested weights from both simulations on every evaluation row. Transaction-cost residual and net-return deltas are reported separately, including inactive exit/reconvergence rows.",
        "",
        "Episode concentration is deliberately active-state only; inactive exit costs are not assigned to episodes and remain represented in the complete net/cost attribution and overall strategy metrics.",
        "",
        "Per-regime average invested allocations and net contributions are emitted for both Phase B and Phase C, together with standalone asset contribution and reconciliation tables, as required by the preregistered reporting contract.",
        "",
        "No thresholds, weights, V6.6 formulas, commodity momentum filters, or rescue assets were changed after seeing results.",
    ]
    (output_dir / "issue-74-phase-c-report.md").write_text("\n".join(report) + "\n", encoding="utf-8")
    return manifest


def main() -> int:
    parser = argparse.ArgumentParser(description="Evaluate Issue #74 preregistered Phase C")
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args()
    print(json.dumps(run(args.output_dir), indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
