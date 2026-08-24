#!/usr/bin/env python3
"""Issue #64 Phase B: preregistered Reflation portfolio override test.

This module reads the committed Phase B contract rather than choosing weights at
runtime. It evaluates reused historical evidence only; it does not alter V6.6.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
from pathlib import Path

import numpy as np
import pandas as pd

from asset_allocation_phase_a import ASSETS, build_outcome_prices
from asset_allocation_phase_a_frozen import (
    SIGNAL_LAST_DATE,
    load_frozen_transitions,
    map_regimes_to_outcome_calendar,
)

HERE = Path(__file__).resolve().parent
DEFAULT_CONTRACT = HERE / "decisions" / "issue-64-phase-b-preregistered.json"
DEFAULT_PRICE_END_EXCLUSIVE = "2026-08-15"


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def load_contract(path: Path = DEFAULT_CONTRACT) -> dict:
    contract = json.loads(path.read_text(encoding="utf-8"))
    if contract.get("issue") != 64 or contract.get("phase") != "B":
        raise ValueError("unexpected Phase B contract identity")
    if contract.get("frozen_before_phase_b_portfolio_results_viewed") is not True:
        raise ValueError("Phase B contract must declare pre-result freeze")
    if contract.get("production_v66_parameters_modified") is not False:
        raise ValueError("Phase B may not modify V6.6")
    for name, weights in contract["templates"].items():
        validate_weights(weights, name)
    for name in ("fixed_60_40", "fixed_equal_weight", "fixed_neutral_40_40_20"):
        validate_weights(contract["benchmarks"][name]["weights"], name)
    return contract


def validate_weights(weights: dict[str, float], name: str) -> None:
    if set(weights) != set(ASSETS):
        raise ValueError(f"{name} must define exactly {ASSETS}")
    values = np.asarray([float(weights[a]) for a in ASSETS], dtype=float)
    if not np.isfinite(values).all() or (values < 0.0).any():
        raise ValueError(f"{name} contains invalid weights")
    if not np.isclose(values.sum(), 1.0, atol=1e-12):
        raise ValueError(f"{name} weights must sum to one")


def weights_series(weights: dict[str, float], index: pd.DatetimeIndex) -> pd.DataFrame:
    row = [float(weights[a]) for a in ASSETS]
    return pd.DataFrame(np.tile(row, (len(index), 1)), index=index, columns=list(ASSETS))


def month_start_mask(index: pd.DatetimeIndex) -> pd.Series:
    periods = pd.Series(index.to_period("M"), index=index)
    return periods.ne(periods.shift(1)).astype(bool)


def build_reflation_targets(
    regimes: pd.Series,
    neutral_weights: dict[str, float],
    reflation_weights: dict[str, float],
    override_regime: str,
) -> tuple[pd.DataFrame, pd.Series]:
    """Use only yesterday's regime to choose today's target template."""
    lagged = regimes.shift(1)
    neutral = np.asarray([float(neutral_weights[a]) for a in ASSETS], dtype=float)
    override = np.asarray([float(reflation_weights[a]) for a in ASSETS], dtype=float)
    data = np.tile(neutral, (len(regimes), 1))
    mask = lagged.eq(override_regime).to_numpy()
    data[mask] = override
    targets = pd.DataFrame(data, index=regimes.index, columns=list(ASSETS))
    template = pd.Series(np.where(mask, "reflation", "neutral"), index=regimes.index, dtype="object")
    template.loc[lagged.isna()] = pd.NA
    return targets, template


def causal_inverse_vol_targets(returns: pd.DataFrame, lookback: int) -> pd.DataFrame:
    if lookback < 2:
        raise ValueError("inverse-vol lookback must be at least two rows")
    vol = returns.rolling(lookback, min_periods=lookback).std(ddof=1).shift(1)
    inv = 1.0 / vol.where(vol > 0.0)
    return inv.div(inv.sum(axis=1), axis=0)


def template_change_mask(template: pd.Series) -> pd.Series:
    valid = template.notna()
    changed = template.ne(template.shift(1)) & valid & template.shift(1).notna()
    return changed.astype(bool)


def simulate_portfolio(
    returns: pd.DataFrame,
    targets: pd.DataFrame,
    rebalance_mask: pd.Series,
    *,
    cost_bps: float,
    name: str,
) -> pd.DataFrame:
    """Self-financing portfolio with drifted pre-trade turnover accounting."""
    if not returns.index.equals(targets.index) or not returns.index.equals(rebalance_mask.index):
        raise ValueError("returns, targets and rebalance mask must share the exact index")
    if list(returns.columns) != list(ASSETS) or list(targets.columns) != list(ASSETS):
        raise ValueError("unexpected asset columns")
    if cost_bps < 0.0:
        raise ValueError("cost_bps must be non-negative")
    if returns.empty:
        raise ValueError("cannot simulate an empty portfolio")

    rows: list[dict] = []
    pretrade_weights: np.ndarray | None = None
    wealth = 1.0
    gross_counterfactual_wealth = 1.0

    for position, date in enumerate(returns.index):
        r = returns.loc[date, list(ASSETS)].to_numpy(float)
        target = targets.loc[date, list(ASSETS)].to_numpy(float)
        if not np.isfinite(r).all() or not np.isfinite(target).all():
            raise ValueError(f"non-finite simulation input on {date}")
        if not np.isclose(target.sum(), 1.0, atol=1e-10):
            raise ValueError(f"target weights do not sum to one on {date}")

        wealth_before = wealth
        initial = position == 0
        trade = False
        turnover = 0.0
        cost_fraction = 0.0

        if initial:
            invested = target.copy()
        else:
            if pretrade_weights is None:
                raise RuntimeError("missing drifted pre-trade weights")
            invested = pretrade_weights.copy()
            if bool(rebalance_mask.loc[date]):
                trade = True
                turnover = float(0.5 * np.abs(target - invested).sum())
                cost_fraction = float(turnover * cost_bps / 10000.0)
                if cost_fraction >= 1.0:
                    raise ValueError("transaction cost consumes the portfolio")
                wealth *= 1.0 - cost_fraction
                invested = target.copy()

        gross_return = float(np.dot(invested, r))
        if 1.0 + gross_return <= 0.0:
            raise ValueError("portfolio return is <= -100%")
        wealth *= 1.0 + gross_return
        gross_counterfactual_wealth *= 1.0 + gross_return
        net_return = float(wealth / wealth_before - 1.0)

        post = invested * (1.0 + r) / (1.0 + gross_return)
        pretrade_weights = post
        row = {
            "date": date,
            "strategy": name,
            "net_return": net_return,
            "gross_asset_mix_return": gross_return,
            "wealth": wealth,
            "gross_counterfactual_wealth": gross_counterfactual_wealth,
            "trade": trade,
            "scheduled_or_event_rebalance": bool(rebalance_mask.loc[date]),
            "turnover": turnover,
            "cost_fraction": cost_fraction,
        }
        for asset, weight in zip(ASSETS, invested):
            row[f"invested_weight_{asset}"] = float(weight)
        for asset, weight in zip(ASSETS, post):
            row[f"end_weight_{asset}"] = float(weight)
        rows.append(row)

    result = pd.DataFrame(rows).set_index("date")
    return result


def portfolio_metrics(sim: pd.DataFrame, *, annualization: int = 252) -> dict:
    if sim.empty:
        raise ValueError("cannot summarize empty simulation")
    r = sim["net_return"].to_numpy(float)
    n = len(r)
    ending = float(np.prod(1.0 + r))
    years = n / float(annualization)
    cagr = ending ** (1.0 / years) - 1.0 if years > 0.0 and ending > 0.0 else np.nan
    ann_return = float(np.mean(r) * annualization)
    ann_vol = float(np.std(r, ddof=1) * math.sqrt(annualization)) if n > 1 else np.nan
    sharpe = ann_return / ann_vol if np.isfinite(ann_vol) and ann_vol > 0.0 else np.nan
    wealth = np.cumprod(1.0 + r)
    drawdown = wealth / np.maximum.accumulate(wealth) - 1.0
    max_drawdown = float(np.min(drawdown))
    calmar = cagr / abs(max_drawdown) if np.isfinite(cagr) and max_drawdown < 0.0 else np.nan
    total_turnover = float(sim["turnover"].sum())
    annualized_turnover = float(total_turnover / years) if years > 0.0 else np.nan
    cost_drag = float(1.0 - np.prod(1.0 - sim["cost_fraction"].to_numpy(float)))
    gross_end = float(np.prod(1.0 + sim["gross_asset_mix_return"].to_numpy(float)))
    average_weights = {
        asset: float(sim[f"invested_weight_{asset}"].mean()) for asset in ASSETS
    }
    return {
        "observations": n,
        "CAGR": float(cagr),
        "annualized_return": ann_return,
        "annualized_volatility": ann_vol,
        "Sharpe": float(sharpe),
        "maximum_drawdown": max_drawdown,
        "Calmar": float(calmar),
        "total_turnover": total_turnover,
        "annualized_turnover": annualized_turnover,
        "rebalance_count": int(sim["trade"].sum()),
        "transaction_cost_drag": cost_drag,
        "ending_wealth": ending,
        "ending_wealth_before_cost_counterfactual": gross_end,
        "average_weight_SPY": average_weights["SPY"],
        "average_weight_TLT": average_weights["TLT"],
        "average_weight_GLD": average_weights["GLD"],
    }


def segment_sim(sim: pd.DataFrame, start: str | None, end: str | None) -> pd.DataFrame:
    result = sim
    if start is not None:
        result = result.loc[result.index >= pd.Timestamp(start)]
    if end is not None:
        result = result.loc[result.index <= pd.Timestamp(end)]
    return result.copy()


def summarize_strategies(simulations: dict[str, pd.DataFrame], annualization: int) -> pd.DataFrame:
    segments = {
        "full_reused_history": (None, None),
        "development_pre2020": (None, "2019-12-31"),
        "post2019_reused_exploratory": ("2020-01-01", None),
    }
    rows: list[dict] = []
    for strategy, sim in simulations.items():
        for segment, (start, end) in segments.items():
            sub = segment_sim(sim, start, end)
            if sub.empty:
                continue
            metrics = portfolio_metrics(sub, annualization=annualization)
            rows.append({
                "strategy": strategy,
                "segment": segment,
                "first_date": sub.index.min().date().isoformat(),
                "last_date": sub.index.max().date().isoformat(),
                **metrics,
            })
    return pd.DataFrame(rows)


def incremental_vs_neutral(summary: pd.DataFrame) -> pd.DataFrame:
    metrics = ["CAGR", "annualized_return", "annualized_volatility", "Sharpe", "maximum_drawdown", "Calmar"]
    rows: list[dict] = []
    for segment in summary["segment"].unique():
        block = summary.loc[summary["segment"].eq(segment)].set_index("strategy")
        if "v66_reflation_override" not in block.index or "fixed_neutral_40_40_20" not in block.index:
            continue
        row = {"segment": segment}
        for metric in metrics:
            row[f"delta_{metric}"] = float(
                block.loc["v66_reflation_override", metric] - block.loc["fixed_neutral_40_40_20", metric]
            )
        rows.append(row)
    return pd.DataFrame(rows)


def build_targets(
    eval_index: pd.DatetimeIndex,
    regimes: pd.Series,
    returns_all: pd.DataFrame,
    contract: dict,
) -> tuple[dict[str, pd.DataFrame], dict[str, pd.Series]]:
    strategy_rule = contract["strategy_rule"]
    neutral = contract["templates"][strategy_rule["default_template"]]
    override = contract["templates"][strategy_rule["override_template"]]
    regime_targets, template = build_reflation_targets(
        regimes,
        neutral,
        override,
        strategy_rule["override_regime"],
    )
    regime_targets = regime_targets.loc[eval_index]
    template = template.loc[eval_index]

    monthly = month_start_mask(eval_index)
    event = template_change_mask(template)
    strategy_rebalance = (monthly | event).astype(bool)

    targets: dict[str, pd.DataFrame] = {
        "v66_reflation_override": regime_targets,
        "fixed_60_40": weights_series(contract["benchmarks"]["fixed_60_40"]["weights"], eval_index),
        "fixed_equal_weight": weights_series(contract["benchmarks"]["fixed_equal_weight"]["weights"], eval_index),
        "fixed_neutral_40_40_20": weights_series(contract["benchmarks"]["fixed_neutral_40_40_20"]["weights"], eval_index),
    }
    lookback = int(contract["benchmarks"]["causal_inverse_volatility"]["lookback_trading_rows"])
    inv = causal_inverse_vol_targets(returns_all, lookback).loc[eval_index]
    targets["causal_inverse_volatility"] = inv

    rebalance = {
        "v66_reflation_override": strategy_rebalance,
        "fixed_60_40": monthly,
        "fixed_equal_weight": monthly,
        "fixed_neutral_40_40_20": monthly,
        "causal_inverse_volatility": monthly,
    }
    return targets, rebalance


def determine_eval_index(
    prices: pd.DataFrame,
    history: pd.DataFrame,
    contract: dict,
) -> tuple[pd.DatetimeIndex, pd.DataFrame, pd.Series]:
    cutoff = pd.Timestamp(contract["comparison_window"]["end"])
    prices = prices.loc[prices.index <= cutoff].copy()
    history = history.reindex(prices.index)
    returns_all = prices.pct_change(fill_method=None)
    regimes = history["core_regime"]
    lagged_regime = regimes.shift(1)
    lookback = int(contract["benchmarks"]["causal_inverse_volatility"]["lookback_trading_rows"])
    inv = causal_inverse_vol_targets(returns_all, lookback)
    valid = (
        returns_all.notna().all(axis=1)
        & lagged_regime.notna()
        & inv.notna().all(axis=1)
    )
    valid_dates = valid.index[valid]
    if valid_dates.empty:
        raise RuntimeError("no common Phase B evaluation start")
    start = valid_dates[0]
    eval_index = prices.index[(prices.index >= start) & (prices.index <= cutoff)]
    if not returns_all.loc[eval_index].notna().all(axis=None):
        raise RuntimeError("non-finite common asset returns inside Phase B window")
    if not lagged_regime.loc[eval_index].notna().all():
        raise RuntimeError("missing lagged regime inside Phase B window")
    if not inv.loc[eval_index].notna().all(axis=None):
        raise RuntimeError("missing inverse-vol target inside Phase B window")
    return eval_index, returns_all, regimes


def run_phase_b(start: str, output_dir: Path) -> dict:
    contract = load_contract()
    prices, price_manifest = build_outcome_prices(start, DEFAULT_PRICE_END_EXCLUSIVE)
    transitions = load_frozen_transitions()
    history = map_regimes_to_outcome_calendar(prices, transitions)
    eval_index, returns_all, regimes = determine_eval_index(prices, history, contract)
    returns = returns_all.loc[eval_index, list(ASSETS)]
    targets, rebalance = build_targets(eval_index, regimes, returns_all, contract)

    primary_cost = float(contract["transaction_cost"]["primary_bps_per_one_way_turnover"])
    simulations = {
        name: simulate_portfolio(returns, targets[name], rebalance[name], cost_bps=primary_cost, name=name)
        for name in targets
    }
    annualization = int(contract["metrics"]["annualization_trading_rows"])
    summary = summarize_strategies(simulations, annualization)
    incremental = incremental_vs_neutral(summary)

    sensitivity_costs = sorted(set(
        [primary_cost] + [float(x) for x in contract["transaction_cost"]["sensitivity_bps_per_one_way_turnover"]]
    ))
    sensitivity_rows: list[dict] = []
    for cost in sensitivity_costs:
        for name in ("v66_reflation_override", "fixed_neutral_40_40_20"):
            sim = simulate_portfolio(returns, targets[name], rebalance[name], cost_bps=cost, name=name)
            metrics = portfolio_metrics(sim, annualization=annualization)
            sensitivity_rows.append({"cost_bps": cost, "strategy": name, **metrics})
    sensitivity = pd.DataFrame(sensitivity_rows)

    output_dir.mkdir(parents=True, exist_ok=True)
    daily = pd.concat(
        [sim.reset_index() for sim in simulations.values()],
        axis=0,
        ignore_index=True,
    )
    daily.to_csv(output_dir / "phase-b-daily.csv", index=False, date_format="%Y-%m-%d")
    summary.to_csv(output_dir / "phase-b-summary.csv", index=False)
    incremental.to_csv(output_dir / "phase-b-incremental-vs-neutral.csv", index=False)
    sensitivity.to_csv(output_dir / "phase-b-cost-sensitivity.csv", index=False)

    strategy_template = targets["v66_reflation_override"]
    reflation_template = np.asarray([
        float(contract["templates"][contract["strategy_rule"]["override_template"]][a]) for a in ASSETS
    ])
    reflation_days = int(np.isclose(strategy_template.to_numpy(float), reflation_template, atol=1e-12).all(axis=1).sum())

    manifest = {
        "schema_version": 1,
        "issue": 64,
        "phase": "B",
        "purpose": "preregistered Reflation equity-over-duration portfolio override",
        "contract_path": str(DEFAULT_CONTRACT.relative_to(HERE)),
        "contract_sha256": sha256_file(DEFAULT_CONTRACT),
        "contract_frozen_before_results": True,
        "evidence_status": contract["evidence_status"],
        "price_data": price_manifest,
        "evaluation_first_date": eval_index.min().date().isoformat(),
        "evaluation_last_date": eval_index.max().date().isoformat(),
        "evaluation_rows": int(len(eval_index)),
        "reflation_target_days": reflation_days,
        "primary_cost_bps": primary_cost,
        "v66_parameters_modified": False,
        "stagflation_override_included": False,
        "weight_magnitude_sweep_performed": False,
    }
    (output_dir / "phase-b-manifest.json").write_text(
        json.dumps(manifest, indent=2, ensure_ascii=False, allow_nan=False) + "\n",
        encoding="utf-8",
    )

    full = summary.loc[summary["segment"].eq("full_reused_history")].copy()
    report = [
        "# Issue #64 Phase B — preregistered Reflation override",
        "",
        f"Evaluation: {manifest['evaluation_first_date']} through {manifest['evaluation_last_date']} ({manifest['evaluation_rows']} rows).",
        f"Primary cost: {primary_cost:.1f} bps per 100% one-way turnover.",
        "",
        "This is reused-history exploratory evidence, not untouched OOS confirmation.",
        "",
        "## Full-history summary",
        "",
    ]
    for _, row in full.iterrows():
        report.append(
            f"- {row['strategy']}: CAGR {row['CAGR']:.4%}; vol {row['annualized_volatility']:.4%}; "
            f"Sharpe {row['Sharpe']:.3f}; max DD {row['maximum_drawdown']:.4%}; "
            f"turnover {row['annualized_turnover']:.3f}x/year."
        )
    report.extend(["", "## Incremental vs fixed neutral 40/40/20", ""])
    for _, row in incremental.iterrows():
        report.append(
            f"- {row['segment']}: ΔCAGR {row['delta_CAGR']:.4%}; ΔSharpe {row['delta_Sharpe']:.3f}; "
            f"ΔmaxDD {row['delta_maximum_drawdown']:.4%}; ΔCalmar {row['delta_Calmar']:.3f}."
        )
    (output_dir / "phase-b-report.md").write_text("\n".join(report) + "\n", encoding="utf-8")
    return manifest


def main() -> int:
    parser = argparse.ArgumentParser(description="Issue #64 preregistered Phase B portfolio test")
    parser.add_argument("--start", default="2007-01-01")
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args()
    manifest = run_phase_b(args.start, args.output_dir)
    print(json.dumps(manifest, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
