#!/usr/bin/env python3
"""Post-hoc same-window legacy comparator for Issue #74.

This is not a new preregistered portfolio rule. It compares the marginal
Stagflation override already frozen in Issue #64 (20pp SPY -> GLD) with the
Issue #74 Phase A override (20pp SPY -> SHV) on the exact same return dates.
Both worlds retain their own matching Reflation-only baseline, so the object of
comparison is the incremental Stagflation overlay, not absolute portfolio PnL.
"""
from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np
import pandas as pd

from asset_allocation_phase_a_frozen import load_frozen_transitions, map_regimes_to_outcome_calendar
from issue_64_outcome_snapshot import load_frozen_prices as load_issue64_prices
from issue_74_outcome_snapshot import load_frozen_prices as load_issue74_prices
from issue_74_portfolio import (
    build_core_regime_targets,
    compare_strategies,
    month_start_mask,
    simulate_portfolio,
    summarize_strategies,
    template_change_mask,
)

REFLATION = "Reflation / Inflation Rising"
STAGFLATION = "Stagflation Pressure"
END = pd.Timestamp("2026-08-14")


def _simulate_pair(
    returns: pd.DataFrame,
    regimes: pd.Series,
    *,
    neutral: dict[str, float],
    reflation: dict[str, float],
    stagflation: dict[str, float],
    prefix: str,
    cost_bps: float,
) -> dict[str, pd.DataFrame]:
    assets = tuple(returns.columns)
    baseline_targets, baseline_template = build_core_regime_targets(
        regimes,
        assets=assets,
        neutral=neutral,
        reflation=reflation,
        stagflation=None,
        reflation_regime=REFLATION,
        stagflation_regime=STAGFLATION,
    )
    override_targets, override_template = build_core_regime_targets(
        regimes,
        assets=assets,
        neutral=neutral,
        reflation=reflation,
        stagflation=stagflation,
        reflation_regime=REFLATION,
        stagflation_regime=STAGFLATION,
    )
    monthly = month_start_mask(returns.index)
    baseline_rebalance = (monthly | template_change_mask(baseline_template)).astype(bool)
    override_rebalance = (monthly | template_change_mask(override_template)).astype(bool)
    return {
        f"{prefix}_reflation_only": simulate_portfolio(
            returns, baseline_targets, baseline_rebalance, cost_bps=cost_bps, name=f"{prefix}_reflation_only"
        ),
        f"{prefix}_stagflation_override": simulate_portfolio(
            returns, override_targets, override_rebalance, cost_bps=cost_bps, name=f"{prefix}_stagflation_override"
        ),
    }


def run(output_dir: Path, cost_bps: float = 5.0) -> None:
    gold_prices, gold_manifest = load_issue64_prices(start="2007-01-01", end="2026-08-25")
    cash_prices, cash_manifest = load_issue74_prices(start="2007-01-01", end="2026-08-25")
    common = gold_prices.index.intersection(cash_prices.index)
    common = common[common <= END]
    gold_prices = gold_prices.loc[common]
    cash_prices = cash_prices.loc[common]
    transitions = load_frozen_transitions()
    history = map_regimes_to_outcome_calendar(cash_prices, transitions)
    regimes = history["core_regime"]
    gold_returns = gold_prices[["SPY", "TLT", "GLD"]].pct_change(fill_method=None)
    cash_returns = cash_prices[["SPY", "TLT", "SHV"]].pct_change(fill_method=None)
    valid = gold_returns.notna().all(axis=1) & cash_returns.notna().all(axis=1) & regimes.shift(1).notna()
    dates = valid.index[valid]
    if dates.empty:
        raise RuntimeError("legacy comparator has no common valid dates")
    idx = common[(common >= dates[0]) & (common <= END)]
    regimes = regimes.loc[idx]
    gold_returns = gold_returns.loc[idx]
    cash_returns = cash_returns.loc[idx]

    gold = _simulate_pair(
        gold_returns,
        regimes,
        neutral={"SPY": 0.4, "TLT": 0.4, "GLD": 0.2},
        reflation={"SPY": 0.6, "TLT": 0.2, "GLD": 0.2},
        stagflation={"SPY": 0.2, "TLT": 0.4, "GLD": 0.4},
        prefix="gold",
        cost_bps=cost_bps,
    )
    cash = _simulate_pair(
        cash_returns,
        regimes,
        neutral={"SPY": 0.4, "TLT": 0.4, "SHV": 0.2},
        reflation={"SPY": 0.6, "TLT": 0.2, "SHV": 0.2},
        stagflation={"SPY": 0.2, "TLT": 0.4, "SHV": 0.4},
        prefix="cash",
        cost_bps=cost_bps,
    )
    simulations = {**gold, **cash}
    summary = summarize_strategies(simulations)
    gold_delta = compare_strategies(
        summary, "gold_stagflation_override", "gold_reflation_only", "gold_override_minus_gold_baseline"
    )
    cash_delta = compare_strategies(
        summary, "cash_stagflation_override", "cash_reflation_only", "cash_override_minus_cash_baseline"
    )

    rows: list[dict] = []
    for segment in gold_delta["segment"]:
        g = gold_delta.loc[gold_delta["segment"].eq(segment)].iloc[0]
        c = cash_delta.loc[cash_delta["segment"].eq(segment)].iloc[0]
        row = {
            "segment": segment,
            "first_date": summary.loc[(summary.strategy == "gold_reflation_only") & (summary.segment == segment), "first_date"].iloc[0],
            "last_date": summary.loc[(summary.strategy == "gold_reflation_only") & (summary.segment == segment), "last_date"].iloc[0],
        }
        for metric in ["CAGR", "annualized_return", "annualized_volatility", "Sharpe", "maximum_drawdown", "Calmar", "annualized_turnover", "transaction_cost_drag"]:
            gv = float(g[f"delta_{metric}"])
            cv = float(c[f"delta_{metric}"])
            row[f"gold_incremental_{metric}"] = gv
            row[f"cash_incremental_{metric}"] = cv
            row[f"cash_minus_gold_incremental_{metric}"] = cv - gv
        rows.append(row)
    comparison = pd.DataFrame(rows)

    lagged = regimes.shift(1)
    episode_rows: list[dict] = []
    for label, pair in {
        "gold": (gold["gold_stagflation_override"], gold["gold_reflation_only"]),
        "cash": (cash["cash_stagflation_override"], cash["cash_reflation_only"]),
    }.items():
        active = np.log1p(pair[0]["net_return"]) - np.log1p(pair[1]["net_return"])
        is_stag = lagged.eq(STAGFLATION).reindex(active.index).fillna(False)
        episode_id = is_stag.ne(is_stag.shift(1)).cumsum()
        for era, start, end in [
            ("development_pre2020", None, pd.Timestamp("2019-12-31")),
            ("post2019_reused_exploratory", pd.Timestamp("2020-01-01"), None),
        ]:
            mask = pd.Series(True, index=active.index)
            if start is not None:
                mask &= active.index >= start
            if end is not None:
                mask &= active.index <= end
            era_dates = active.index[mask.to_numpy()]
            stag_dates = era_dates[is_stag.loc[era_dates].to_numpy()]
            episodes = []
            for eid in episode_id.loc[stag_dates].unique():
                dates_e = stag_dates[episode_id.loc[stag_dates].eq(eid).to_numpy()]
                episodes.append((dates_e.min(), dates_e.max(), float(active.loc[dates_e].sum())))
            total = float(active.loc[era_dates].sum())
            if episodes:
                winner = max(episodes, key=lambda item: item[2])
                removed = total - winner[2]
                episode_rows.append({
                    "asset_role": label,
                    "segment": era,
                    "active_log_return": total,
                    "largest_winner_start": winner[0].date().isoformat(),
                    "largest_winner_end": winner[1].date().isoformat(),
                    "largest_winner_active_log_return": winner[2],
                    "active_log_return_ex_largest_winner": removed,
                    "sign_flips_after_removal": bool(total > 0.0 and removed < 0.0),
                })
    episode = pd.DataFrame(episode_rows)

    output_dir.mkdir(parents=True, exist_ok=True)
    summary.to_csv(output_dir / "issue-74-legacy-gold-cash-summary.csv", index=False)
    comparison.to_csv(output_dir / "issue-74-legacy-gold-cash-incremental.csv", index=False)
    episode.to_csv(output_dir / "issue-74-legacy-gold-cash-episodes.csv", index=False)
    full = comparison.loc[comparison.segment.eq("full_reused_history")].iloc[0]
    report = [
        "# Issue #74 — post-hoc same-window Gold vs Cash Stagflation overlay comparator",
        "",
        "This is a diagnostic comparison of already-frozen rules, not a new preregistered rule or a license to tune weights.",
        f"Common evaluation window: {full.first_date} through {full.last_date}. Primary cost: {cost_bps:.1f} bp.",
        f"Issue #64 frozen price SHA: {gold_manifest['snapshot_csv_sha256']}.",
        f"Issue #74 frozen price SHA: {cash_manifest['snapshot_csv_sha256']}.",
        "",
        "Each incremental effect is override minus its own matching Reflation-only baseline on identical dates.",
        "",
        f"Full history Gold incremental: ΔCAGR {full.gold_incremental_CAGR:.4%}, ΔSharpe {full.gold_incremental_Sharpe:.3f}, ΔmaxDD {full.gold_incremental_maximum_drawdown:.4%}, ΔCalmar {full.gold_incremental_Calmar:.3f}.",
        f"Full history Cash incremental: ΔCAGR {full.cash_incremental_CAGR:.4%}, ΔSharpe {full.cash_incremental_Sharpe:.3f}, ΔmaxDD {full.cash_incremental_maximum_drawdown:.4%}, ΔCalmar {full.cash_incremental_Calmar:.3f}.",
        "",
        "Interpretation must still be conditioned on era and leave-largest-episode-out robustness; absolute portfolio levels across the Gold and Cash universes are not the object of this diagnostic.",
    ]
    (output_dir / "issue-74-legacy-gold-cash-report.md").write_text("\n".join(report) + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description="Compare frozen Issue #64 Gold and Issue #74 Cash Stagflation overlays")
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--cost-bps", type=float, default=5.0)
    args = parser.parse_args()
    run(args.output_dir, cost_bps=args.cost_bps)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
