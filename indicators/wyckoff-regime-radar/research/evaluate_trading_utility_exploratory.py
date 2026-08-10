#!/usr/bin/env python3
"""Evaluate the frozen Issue #55 response map on Exploratory OOS only.

The executable rules are frozen in:
``decisions/issue-55-final-oos-response-map-and-baselines.md``.

This script must not compute Final-OOS model outputs. It uses the frozen
canonical data only through the Exploratory-OOS end, applies the exact response
map and simple baselines, uses close-to-next-close one-bar-lagged execution, and
charges the preregistered 1-pip-per-unit-turnover primary cost.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
import pandas as pd

from evaluate_regime_paths_pre_final import load_frozen_pair
from price_only_core import PriceOnlyConfig, compute_price_only


WYCKOFF_RESPONSE = {0: 0.0, 1: 0.0, 2: 1.0, 3: 1.0, 4: 0.0, 5: -1.0, 6: -1.0}
PIP_SIZE = {"EURUSD": 0.0001, "GBPUSD": 0.0001, "AUDUSD": 0.0001, "USDJPY": 0.01}
ANNUALIZATION = 252.0
PRIMARY_COST_PIPS = 1.0


def wyckoff_targets(model: pd.DataFrame) -> np.ndarray:
    formal = pd.to_numeric(model["formal_id"], errors="coerce").fillna(0).to_numpy(int)
    return np.array([WYCKOFF_RESPONSE.get(int(stage), 0.0) for stage in formal], dtype=float)


def sma200_targets(frame: pd.DataFrame) -> np.ndarray:
    close = pd.to_numeric(frame["close"], errors="coerce")
    ma = close.rolling(200, min_periods=200).mean()
    target = np.where(close > ma, 1.0, np.where(close < ma, -1.0, 0.0))
    target[~np.isfinite(ma.to_numpy(float))] = 0.0
    return target.astype(float)


def momentum60_targets(frame: pd.DataFrame) -> np.ndarray:
    close = pd.to_numeric(frame["close"], errors="coerce")
    momentum = close / close.shift(60) - 1.0
    target = np.where(momentum > 0.0, 1.0, np.where(momentum < 0.0, -1.0, 0.0))
    target[~np.isfinite(momentum.to_numpy(float))] = 0.0
    return target.astype(float)


def donchian55_targets(frame: pd.DataFrame) -> np.ndarray:
    close = pd.to_numeric(frame["close"], errors="coerce").to_numpy(float)
    high = pd.to_numeric(frame["high"], errors="coerce")
    low = pd.to_numeric(frame["low"], errors="coerce")
    prior_high = high.shift(1).rolling(55, min_periods=55).max().to_numpy(float)
    prior_low = low.shift(1).rolling(55, min_periods=55).min().to_numpy(float)
    target = np.zeros(len(frame), dtype=float)
    current = 0.0
    for i in range(len(frame)):
        if np.isfinite(prior_high[i]) and np.isfinite(prior_low[i]):
            if close[i] > prior_high[i]:
                current = 1.0
            elif close[i] < prior_low[i]:
                current = -1.0
        target[i] = current
    return target


def flat_targets(frame: pd.DataFrame) -> np.ndarray:
    return np.zeros(len(frame), dtype=float)


def strategy_targets(frame: pd.DataFrame, model: pd.DataFrame) -> dict[str, np.ndarray]:
    return {
        "wyckoff_frozen_response": wyckoff_targets(model),
        "always_flat": flat_targets(frame),
        "sma200": sma200_targets(frame),
        "momentum60": momentum60_targets(frame),
        "donchian55": donchian55_targets(frame),
    }


def max_drawdown(daily_returns: np.ndarray) -> float | None:
    finite = daily_returns[np.isfinite(daily_returns)]
    if not len(finite):
        return None
    wealth = np.cumprod(1.0 + finite)
    peaks = np.maximum.accumulate(np.concatenate(([1.0], wealth)))[:-1]
    drawdowns = wealth / peaks - 1.0
    return float(np.min(drawdowns))


def performance_metrics(
    gross_returns: np.ndarray,
    net_returns: np.ndarray,
    exposure: np.ndarray,
    turnover: np.ndarray,
    costs: np.ndarray,
) -> dict:
    finite = np.isfinite(net_returns) & np.isfinite(gross_returns)
    gross = gross_returns[finite]
    net = net_returns[finite]
    exp = exposure[finite]
    turn = turnover[finite]
    cost = costs[finite]
    n = len(net)
    if not n:
        raise ValueError("no evaluable strategy rows")

    def compounded(values: np.ndarray) -> float:
        return float(np.prod(1.0 + values) - 1.0)

    gross_cum = compounded(gross)
    net_cum = compounded(net)
    gross_wealth = 1.0 + gross_cum
    net_wealth = 1.0 + net_cum
    gross_ann = float(gross_wealth ** (ANNUALIZATION / n) - 1.0) if gross_wealth > 0 else None
    net_ann = float(net_wealth ** (ANNUALIZATION / n) - 1.0) if net_wealth > 0 else None
    vol = float(np.std(net, ddof=1) * np.sqrt(ANNUALIZATION)) if n > 1 else 0.0
    sharpe = float(np.mean(net) / np.std(net, ddof=1) * np.sqrt(ANNUALIZATION)) if n > 1 and np.std(net, ddof=1) > 0 else None
    return {
        "observations": n,
        "gross_cumulative_return": gross_cum,
        "net_cumulative_return": net_cum,
        "gross_annualized_return": gross_ann,
        "net_annualized_return": net_ann,
        "annualized_volatility": vol,
        "annualized_sharpe_zero_cash": sharpe,
        "max_drawdown": max_drawdown(net),
        "average_absolute_exposure": float(np.mean(np.abs(exp))),
        "total_turnover": float(np.sum(turn)),
        "position_change_count": int(np.sum(turn > 0.0)),
        "total_cost_return_units": float(np.sum(cost)),
        "compounded_cost_drag": gross_cum - net_cum,
        "positive_day_rate": float(np.mean(net > 0.0)),
    }


def evaluate_targets(
    frame: pd.DataFrame,
    target: np.ndarray,
    start_index: int,
    end_index: int,
    pip_size: float,
    cost_pips: float = PRIMARY_COST_PIPS,
) -> tuple[dict, pd.DataFrame]:
    """Trade target[t] from close[t] to close[t+1]; never cross split end."""
    close = pd.to_numeric(frame["close"], errors="coerce").to_numpy(float)
    if len(target) != len(frame):
        raise ValueError("target length mismatch")
    if start_index < 0 or end_index >= len(frame) or start_index >= end_index:
        raise ValueError("invalid evaluation boundary")

    rows = []
    previous_target = float(target[start_index - 1]) if start_index > 0 else 0.0
    for origin in range(start_index, end_index):
        position = float(target[origin])
        next_return = close[origin + 1] / close[origin] - 1.0
        turnover = abs(position - previous_target)
        cost = turnover * cost_pips * pip_size / close[origin]
        gross = position * next_return
        net = gross - cost
        rows.append(
            {
                "origin_index": origin,
                "origin_date": str(frame.iloc[origin]["date"]),
                "next_date": str(frame.iloc[origin + 1]["date"]),
                "position": position,
                "turnover": turnover,
                "gross_return": gross,
                "cost_return": cost,
                "net_return": net,
            }
        )
        previous_target = position

    daily = pd.DataFrame(rows)
    metrics = performance_metrics(
        daily["gross_return"].to_numpy(float),
        daily["net_return"].to_numpy(float),
        daily["position"].to_numpy(float),
        daily["turnover"].to_numpy(float),
        daily["cost_return"].to_numpy(float),
    )
    return metrics, daily


def analyze_pair(pair: str, frame: pd.DataFrame, meta: dict) -> tuple[dict, dict[str, pd.DataFrame]]:
    exp = meta["splits"]["exploratory_oos"]
    exp_start, exp_end = int(exp["start_index"]), int(exp["end_index"])
    # Hard final seal: the model never receives a Final-OOS row.
    pre_final = frame.iloc[: exp_end + 1].copy().reset_index(drop=True)
    model = compute_price_only(pre_final, PriceOnlyConfig())
    targets = strategy_targets(pre_final, model)
    results = {}
    daily_outputs = {}
    for name, target in targets.items():
        metrics, daily = evaluate_targets(
            pre_final,
            target,
            exp_start,
            exp_end,
            PIP_SIZE[pair],
            PRIMARY_COST_PIPS,
        )
        results[name] = metrics
        daily_outputs[name] = daily
    return (
        {
            "exploratory_start_date": exp["start_date"],
            "exploratory_end_date": exp["end_date"],
            "model_rows_computed": len(pre_final),
            "final_oos_rows_computed": 0,
            "primary_cost_pips_per_unit_turnover": PRIMARY_COST_PIPS,
            "pip_size": PIP_SIZE[pair],
            "strategies": results,
        },
        daily_outputs,
    )


def aggregate_equal_weight(pair_daily: dict[str, dict[str, pd.DataFrame]]) -> dict:
    strategy_names = list(next(iter(pair_daily.values())).keys())
    aggregate = {}
    for strategy in strategy_names:
        pieces = []
        for pair, strategies in pair_daily.items():
            daily = strategies[strategy].copy()
            daily = daily[["origin_date", "net_return", "gross_return", "position", "turnover", "cost_return"]]
            daily = daily.rename(
                columns={
                    "net_return": f"net_{pair}",
                    "gross_return": f"gross_{pair}",
                    "position": f"position_{pair}",
                    "turnover": f"turnover_{pair}",
                    "cost_return": f"cost_{pair}",
                }
            )
            pieces.append(daily)
        merged = pieces[0]
        for piece in pieces[1:]:
            merged = merged.merge(piece, on="origin_date", how="inner")
        net_cols = [col for col in merged if col.startswith("net_")]
        gross_cols = [col for col in merged if col.startswith("gross_")]
        position_cols = [col for col in merged if col.startswith("position_")]
        turnover_cols = [col for col in merged if col.startswith("turnover_")]
        cost_cols = [col for col in merged if col.startswith("cost_")]
        net = merged[net_cols].mean(axis=1).to_numpy(float)
        gross = merged[gross_cols].mean(axis=1).to_numpy(float)
        exposure = merged[position_cols].abs().mean(axis=1).to_numpy(float)
        # Portfolio turnover and costs are averaged across four equal-weight sleeves.
        turnover = merged[turnover_cols].mean(axis=1).to_numpy(float)
        costs = merged[cost_cols].mean(axis=1).to_numpy(float)
        aggregate[strategy] = performance_metrics(gross, net, exposure, turnover, costs)
    return aggregate


def build_report(manifest_path: Path) -> dict:
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    if manifest.get("final_oos_status") != "SEALED_DO_NOT_EVALUATE":
        raise ValueError("refusing to run: Final-OOS seal missing")

    pairs = {}
    pair_daily = {}
    for pair, meta in manifest["pairs"].items():
        pair_result, daily = analyze_pair(pair, load_frozen_pair(manifest_path, meta), meta)
        pairs[pair] = pair_result
        pair_daily[pair] = daily

    aggregate = aggregate_equal_weight(pair_daily)
    wyckoff = aggregate["wyckoff_frozen_response"]
    baseline_comparison = {}
    for baseline in ("sma200", "momentum60", "donchian55"):
        base = aggregate[baseline]
        baseline_comparison[baseline] = {
            "net_annualized_return_difference": (
                None
                if wyckoff["net_annualized_return"] is None or base["net_annualized_return"] is None
                else wyckoff["net_annualized_return"] - base["net_annualized_return"]
            ),
            "sharpe_difference": (
                None
                if wyckoff["annualized_sharpe_zero_cash"] is None or base["annualized_sharpe_zero_cash"] is None
                else wyckoff["annualized_sharpe_zero_cash"] - base["annualized_sharpe_zero_cash"]
            ),
        }

    return {
        "schema_version": 1,
        "issue": 55,
        "status": "exploratory_oos_trading_utility_frozen_rules",
        "response_map": {str(key): value for key, value in WYCKOFF_RESPONSE.items()},
        "execution": "signal at close t holds target over close t -> close t+1; no same-bar future use",
        "primary_cost_pips_per_unit_turnover": PRIMARY_COST_PIPS,
        "final_oos_status": "SEALED_NOT_COMPUTED",
        "pairs": pairs,
        "equal_weight_four_pair_aggregate": aggregate,
        "wyckoff_vs_baseline": baseline_comparison,
        "boundary": (
            "Exploratory OOS only under the already-committed frozen response map/baselines. "
            "Final-OOS model rows and price returns are not computed. These exploratory results may not change "
            "the frozen mapping, baseline lookbacks, lag, or primary cost."
        ),
    }


def render_markdown(report: dict) -> str:
    lines = [
        "# Issue #55 — Exploratory-OOS trading utility under frozen rules",
        "",
        "Final OOS remains **SEALED / NOT COMPUTED**.",
        "",
        "Rules were committed before this report: formal-state response map, one-bar lag, 1-pip-per-unit-turnover primary cost, SMA200 / Momentum60 / Donchian55 baselines.",
        "",
        "## Equal-weight four-pair aggregate",
        "",
        "| Strategy | Net ann. return | Net vol | Sharpe | Max DD | Avg abs exposure | Turnover | Cost drag |",
        "|---|---:|---:|---:|---:|---:|---:|---:|",
    ]
    aggregate = report["equal_weight_four_pair_aggregate"]
    for name in ("wyckoff_frozen_response", "sma200", "momentum60", "donchian55", "always_flat"):
        row = aggregate[name]
        def pct(value):
            return "—" if value is None else f"{value * 100:.2f}%"
        sharpe = "—" if row["annualized_sharpe_zero_cash"] is None else f"{row['annualized_sharpe_zero_cash']:.2f}"
        lines.append(
            f"| {name} | {pct(row['net_annualized_return'])} | {pct(row['annualized_volatility'])} | "
            f"{sharpe} | {pct(row['max_drawdown'])} | {row['average_absolute_exposure'] * 100:.1f}% | "
            f"{row['total_turnover']:.1f} | {pct(row['compounded_cost_drag'])} |"
        )

    lines.extend(["", "## Per pair — Wyckoff frozen response", ""])
    lines.append("| Pair | Net ann. return | Sharpe | Max DD | Exposure | Turnover |")
    lines.append("|---|---:|---:|---:|---:|---:|")
    for pair, pair_result in report["pairs"].items():
        row = pair_result["strategies"]["wyckoff_frozen_response"]
        def pct(value):
            return "—" if value is None else f"{value * 100:.2f}%"
        sharpe = "—" if row["annualized_sharpe_zero_cash"] is None else f"{row['annualized_sharpe_zero_cash']:.2f}"
        lines.append(
            f"| {pair} | {pct(row['net_annualized_return'])} | {sharpe} | {pct(row['max_drawdown'])} | "
            f"{row['average_absolute_exposure'] * 100:.1f}% | {row['total_turnover']:.1f} |"
        )

    lines.extend(["", "## Wyckoff minus baseline (equal-weight aggregate)", ""])
    lines.append("| Baseline | Ann. return difference | Sharpe difference |")
    lines.append("|---|---:|---:|")
    for baseline, diff in report["wyckoff_vs_baseline"].items():
        ret = diff["net_annualized_return_difference"]
        sharpe = diff["sharpe_difference"]
        lines.append(
            f"| {baseline} | {'—' if ret is None else f'{ret * 100:.2f}%'} | "
            f"{'—' if sharpe is None else f'{sharpe:.2f}'} |"
        )

    lines.extend([
        "",
        "Boundary: Exploratory OOS only. These results cannot be used to alter the frozen Final-OOS response map or baselines.",
        "",
    ])
    return "\n".join(lines)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    here = Path(__file__).resolve().parent
    parser.add_argument("--manifest", type=Path, default=here / "data" / "issue-55-static-fx-canonical-manifest.json")
    parser.add_argument("--json-output", type=Path)
    parser.add_argument("--md-output", type=Path)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    report = build_report(args.manifest)
    if args.json_output:
        args.json_output.parent.mkdir(parents=True, exist_ok=True)
        args.json_output.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    if args.md_output:
        args.md_output.parent.mkdir(parents=True, exist_ok=True)
        args.md_output.write_text(render_markdown(report), encoding="utf-8")
    print(json.dumps(report["equal_weight_four_pair_aggregate"], indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
