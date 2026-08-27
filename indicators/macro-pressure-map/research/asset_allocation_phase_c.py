#!/usr/bin/env python3
"""Issue #64 Phase C: preregistered Stagflation gold-over-equity override.

Primary question: does adding the frozen Stagflation 20/40/40 template provide
incremental value beyond the already-frozen Phase B Reflation-only strategy?
All available history is reused/development exploratory evidence.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
import pandas as pd

import asset_allocation_phase_b as phase_b
from asset_allocation_phase_a import ASSETS
from asset_allocation_phase_a_frozen import load_frozen_transitions, map_regimes_to_outcome_calendar
from asset_allocation_phase_b_snapshot import resolve_exact_prices

HERE = Path(__file__).resolve().parent
DEFAULT_CONTRACT = HERE / "decisions" / "issue-64-phase-c-preregistered.json"
REFLATION_REGIME = "Reflation / Inflation Rising"
STAGFLATION_REGIME = "Stagflation Pressure"


def load_contract(path: Path = DEFAULT_CONTRACT) -> dict:
    contract = json.loads(path.read_text(encoding="utf-8"))
    if contract.get("issue") != 64 or contract.get("phase") != "C":
        raise ValueError("unexpected Phase C contract identity")
    if contract.get("frozen_before_phase_c_portfolio_results_viewed") is not True:
        raise ValueError("Phase C contract must declare pre-result freeze")
    if contract.get("production_v66_parameters_modified") is not False:
        raise ValueError("Phase C may not modify V6.6")
    for name, weights in contract["templates"].items():
        phase_b.validate_weights(weights, name)
    if float(contract["primary_cost_bps"]) != 5.0:
        raise ValueError("unexpected Phase C primary cost")
    return contract


def build_three_state_targets(
    regimes: pd.Series,
    *,
    neutral: dict[str, float],
    reflation: dict[str, float],
    stagflation: dict[str, float],
    include_reflation: bool,
    include_stagflation: bool,
) -> tuple[pd.DataFrame, pd.Series]:
    """Use yesterday's known regime to choose today's frozen target template."""
    lagged = regimes.shift(1)
    arrays = {
        "neutral": np.asarray([float(neutral[a]) for a in ASSETS], dtype=float),
        "reflation": np.asarray([float(reflation[a]) for a in ASSETS], dtype=float),
        "stagflation": np.asarray([float(stagflation[a]) for a in ASSETS], dtype=float),
    }
    data = np.tile(arrays["neutral"], (len(regimes), 1))
    template = pd.Series("neutral", index=regimes.index, dtype="object")

    if include_reflation:
        mask = lagged.eq(REFLATION_REGIME).to_numpy()
        data[mask] = arrays["reflation"]
        template.loc[mask] = "reflation"
    if include_stagflation:
        mask = lagged.eq(STAGFLATION_REGIME).to_numpy()
        data[mask] = arrays["stagflation"]
        template.loc[mask] = "stagflation"

    template.loc[lagged.isna()] = pd.NA
    targets = pd.DataFrame(data, index=regimes.index, columns=list(ASSETS))
    return targets, template


def comparison_table(
    summary: pd.DataFrame,
    *,
    lhs: str,
    rhs: str,
    comparison: str,
) -> pd.DataFrame:
    metrics = [
        "CAGR",
        "annualized_return",
        "annualized_volatility",
        "Sharpe",
        "maximum_drawdown",
        "Calmar",
        "annualized_turnover",
        "transaction_cost_drag",
    ]
    rows: list[dict] = []
    for segment in summary["segment"].unique():
        block = summary.loc[summary["segment"].eq(segment)].set_index("strategy")
        if lhs not in block.index or rhs not in block.index:
            continue
        row = {"comparison": comparison, "segment": segment, "lhs": lhs, "rhs": rhs}
        for metric in metrics:
            row[f"delta_{metric}"] = float(block.loc[lhs, metric] - block.loc[rhs, metric])
        rows.append(row)
    return pd.DataFrame(rows)


def run_phase_c(start: str, output_dir: Path) -> dict:
    contract = load_contract()
    phase_b_contract = phase_b.load_contract()
    prices, price_manifest = resolve_exact_prices(start)
    transitions = load_frozen_transitions()
    history = map_regimes_to_outcome_calendar(prices, transitions)
    eval_index, returns_all, regimes = phase_b.determine_eval_index(prices, history, phase_b_contract)
    returns = returns_all.loc[eval_index, list(ASSETS)]

    neutral = contract["templates"]["neutral"]
    reflation = contract["templates"]["reflation"]
    stagflation = contract["templates"]["stagflation"]

    combined_targets, combined_template = build_three_state_targets(
        regimes,
        neutral=neutral,
        reflation=reflation,
        stagflation=stagflation,
        include_reflation=True,
        include_stagflation=True,
    )
    reflation_targets, reflation_template = build_three_state_targets(
        regimes,
        neutral=neutral,
        reflation=reflation,
        stagflation=stagflation,
        include_reflation=True,
        include_stagflation=False,
    )
    stag_only_targets, stag_only_template = build_three_state_targets(
        regimes,
        neutral=neutral,
        reflation=reflation,
        stagflation=stagflation,
        include_reflation=False,
        include_stagflation=True,
    )

    monthly = phase_b.month_start_mask(eval_index)
    targets = {
        "phase_c_combined": combined_targets.loc[eval_index],
        "phase_b_reflation_only": reflation_targets.loc[eval_index],
        "stagflation_only": stag_only_targets.loc[eval_index],
        "fixed_neutral_40_40_20": phase_b.weights_series(neutral, eval_index),
    }
    rebalance = {
        "phase_c_combined": (monthly | phase_b.template_change_mask(combined_template.loc[eval_index])).astype(bool),
        "phase_b_reflation_only": (monthly | phase_b.template_change_mask(reflation_template.loc[eval_index])).astype(bool),
        "stagflation_only": (monthly | phase_b.template_change_mask(stag_only_template.loc[eval_index])).astype(bool),
        "fixed_neutral_40_40_20": monthly,
    }

    primary_cost = float(contract["primary_cost_bps"])
    simulations = {
        name: phase_b.simulate_portfolio(
            returns,
            targets[name],
            rebalance[name],
            cost_bps=primary_cost,
            name=name,
        )
        for name in targets
    }
    annualization = 252
    summary = phase_b.summarize_strategies(simulations, annualization)
    primary = comparison_table(
        summary,
        lhs="phase_c_combined",
        rhs="phase_b_reflation_only",
        comparison="phase_c_combined_minus_phase_b_reflation_only",
    )
    diagnostic = comparison_table(
        summary,
        lhs="stagflation_only",
        rhs="fixed_neutral_40_40_20",
        comparison="stagflation_only_minus_fixed_neutral",
    )
    comparisons = pd.concat([primary, diagnostic], ignore_index=True)

    sensitivity_rows: list[dict] = []
    for cost in sorted(set(float(x) for x in contract["cost_sensitivity_bps"])):
        for name in ("phase_c_combined", "phase_b_reflation_only"):
            sim = phase_b.simulate_portfolio(
                returns,
                targets[name],
                rebalance[name],
                cost_bps=cost,
                name=name,
            )
            sensitivity_rows.append({
                "cost_bps": cost,
                "strategy": name,
                **phase_b.portfolio_metrics(sim, annualization=annualization),
            })
    sensitivity = pd.DataFrame(sensitivity_rows)

    lagged = regimes.shift(1).loc[eval_index]
    output_dir.mkdir(parents=True, exist_ok=True)
    daily = pd.concat([sim.reset_index() for sim in simulations.values()], ignore_index=True)
    daily.to_csv(output_dir / "phase-c-daily.csv", index=False, date_format="%Y-%m-%d")
    summary.to_csv(output_dir / "phase-c-summary.csv", index=False)
    comparisons.to_csv(output_dir / "phase-c-incremental.csv", index=False)
    sensitivity.to_csv(output_dir / "phase-c-cost-sensitivity.csv", index=False)

    manifest = {
        "schema_version": 1,
        "issue": 64,
        "phase": "C",
        "purpose": "preregistered incremental Stagflation gold-over-equity override",
        "contract_path": str(DEFAULT_CONTRACT.relative_to(HERE)),
        "contract_sha256": phase_b.sha256_file(DEFAULT_CONTRACT),
        "contract_frozen_before_results": True,
        "preregistration_issue_comment_id": contract["preregistration_issue_comment_id"],
        "evidence_status": contract["evidence_status"],
        "price_data": price_manifest,
        "evaluation_first_date": eval_index.min().date().isoformat(),
        "evaluation_last_date": eval_index.max().date().isoformat(),
        "evaluation_rows": int(len(eval_index)),
        "primary_cost_bps": primary_cost,
        "lagged_stagflation_target_days": int(lagged.eq(STAGFLATION_REGIME).sum()),
        "lagged_reflation_target_days": int(lagged.eq(REFLATION_REGIME).sum()),
        "v66_parameters_modified": False,
        "weight_magnitude_sweep_performed": False,
        "optimizer_used": False,
    }
    (output_dir / "phase-c-manifest.json").write_text(
        json.dumps(manifest, indent=2, ensure_ascii=False, allow_nan=False) + "\n",
        encoding="utf-8",
    )

    full = summary.loc[summary["segment"].eq("full_reused_history")]
    full_primary = primary.loc[primary["segment"].eq("full_reused_history")].iloc[0]
    report = [
        "# Issue #64 Phase C — preregistered Stagflation override",
        "",
        f"Evaluation: {manifest['evaluation_first_date']} through {manifest['evaluation_last_date']} ({manifest['evaluation_rows']} rows).",
        f"Primary cost: {primary_cost:.1f} bps per 100% one-way turnover.",
        "",
        "All results are reused/development exploratory evidence, not untouched OOS confirmation.",
        "",
        "## Full-history strategies",
        "",
    ]
    for row in full.itertuples(index=False):
        report.append(
            f"- {row.strategy}: CAGR {row.CAGR:.4%}; Sharpe {row.Sharpe:.3f}; "
            f"max DD {row.maximum_drawdown:.4%}; Calmar {row.Calmar:.3f}; "
            f"turnover {row.annualized_turnover:.3f}x/year."
        )
    report.extend([
        "",
        "## Primary incremental Phase C minus Phase B",
        "",
        f"- ΔCAGR {full_primary['delta_CAGR']:.4%}; ΔSharpe {full_primary['delta_Sharpe']:.3f}; "
        f"ΔmaxDD {full_primary['delta_maximum_drawdown']:.4%}; ΔCalmar {full_primary['delta_Calmar']:.3f}; "
        f"Δturnover {full_primary['delta_annualized_turnover']:.3f}x/year.",
        "",
        "A positive primary result must still pass exposure-matched and episode-concentration diagnostics before interpretation.",
    ])
    (output_dir / "phase-c-report.md").write_text("\n".join(report) + "\n", encoding="utf-8")
    return manifest


def main() -> int:
    parser = argparse.ArgumentParser(description="Issue #64 preregistered Phase C portfolio test")
    parser.add_argument("--start", default="2007-01-01")
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args()
    print(json.dumps(run_phase_c(args.start, args.output_dir), indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
