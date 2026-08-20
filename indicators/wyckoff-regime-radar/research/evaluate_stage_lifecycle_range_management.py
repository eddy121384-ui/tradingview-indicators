#!/usr/bin/env python3
"""Issue #61 Phase-C range-managed stage lifecycle.

The rule is frozen in `decisions/issue-61-phase-c-range-risk-freeze.md` before
this evaluator inspects PnL.  Existing rangeScore=70 full-gate semantics are
reused; exposure is 1.0 or 0.5 only, with no stop/target/leverage optimization.
"""
from __future__ import annotations

import argparse
import json

import numpy as np
import pandas as pd

from diagnose_stage_lifecycle_break_timing import load_frozen_pairs
from evaluate_stage_lifecycle_base import (
    ANNUALIZATION,
    COST_PER_UNIT_TURNOVER,
    annualized_return,
    max_drawdown,
    stage_lifecycle_signal,
)
from generate_v06_phase_b_core import load_phase_b_namespace

STRONG_RANGE = 70.0
CORE_EXPOSURE = 0.5


def range_managed_exposure(
    base_signal: np.ndarray,
    formal: np.ndarray,
    range_score: np.ndarray,
    fresh_up: np.ndarray,
    fresh_down: np.ndarray,
    warmup: int,
) -> tuple[np.ndarray, dict[str, int]]:
    n = len(base_signal)
    if not all(len(values) == n for values in (formal, range_score, fresh_up, fresh_down)):
        raise ValueError("all arrays must have equal length")

    exposure = np.zeros(n, dtype=float)
    reduced = False
    stats = {
        "long_reductions": 0,
        "short_reductions": 0,
        "long_readds": 0,
        "short_readds": 0,
        "new_long_episodes": 0,
        "new_short_episodes": 0,
    }

    for i in range(n):
        if i < warmup:
            continue

        direction = int(base_signal[i])
        previous_direction = int(base_signal[i - 1]) if i > warmup else 0

        if direction == 0:
            reduced = False
            exposure[i] = 0.0
            continue

        new_episode = previous_direction != direction
        if new_episode:
            reduced = False
            if direction == 1:
                stats["new_long_episodes"] += 1
            else:
                stats["new_short_episodes"] += 1
            # Frozen rule: a newly opened base episode always begins at full size,
            # even if rangeScore is already high on that close.
            exposure[i] = float(direction)
            continue

        matching_break = (
            (direction == 1 and int(formal[i]) == 2 and bool(fresh_up[i]))
            or (direction == -1 and int(formal[i]) == 5 and bool(fresh_down[i]))
        )

        # Same-bar precedence: renewed fresh break restores/keeps full exposure.
        if matching_break:
            if reduced:
                if direction == 1:
                    stats["long_readds"] += 1
                else:
                    stats["short_readds"] += 1
            reduced = False
        elif not reduced and np.isfinite(range_score[i]) and float(range_score[i]) >= STRONG_RANGE:
            reduced = True
            if direction == 1:
                stats["long_reductions"] += 1
            else:
                stats["short_reductions"] += 1

        exposure[i] = direction * (CORE_EXPOSURE if reduced else 1.0)

    return exposure, stats


def strategy_metrics_fractional(frame: pd.DataFrame, desired_exposure: np.ndarray, warmup: int) -> dict[str, float | int | None]:
    close = pd.to_numeric(frame["close"], errors="coerce").to_numpy(float)
    n = len(close)
    asset_return = np.zeros(n, dtype=float)
    valid = np.isfinite(close[1:]) & np.isfinite(close[:-1]) & (close[:-1] > 0.0)
    asset_return[1:][valid] = close[1:][valid] / close[:-1][valid] - 1.0

    actual = np.zeros(n, dtype=float)
    if n > 1:
        actual[1:] = desired_exposure[:-1]
    turnover = np.zeros(n, dtype=float)
    if n > 1:
        turnover[1:] = np.abs(actual[1:] - actual[:-1])

    score_mask = np.arange(n) >= max(1, warmup + 1)
    gross_all = actual * asset_return
    net_all = gross_all - COST_PER_UNIT_TURNOVER * turnover
    gross = gross_all[score_mask]
    net = net_all[score_mask]
    pos = actual[score_mask]
    turn = turnover[score_mask]

    gross_std = float(np.std(gross, ddof=1)) if gross.size > 1 else 0.0
    net_std = float(np.std(net, ddof=1)) if net.size > 1 else 0.0
    years = gross.size / ANNUALIZATION if gross.size else 0.0

    return {
        "observations": int(gross.size),
        "gross_ann_return": annualized_return(gross),
        "gross_ann_vol": float(gross_std * np.sqrt(ANNUALIZATION)),
        "gross_sharpe": None if gross_std <= 0.0 else float(np.mean(gross) / gross_std * np.sqrt(ANNUALIZATION)),
        "gross_max_drawdown": max_drawdown(gross),
        "net_2bp_ann_return": annualized_return(net),
        "net_2bp_sharpe": None if net_std <= 0.0 else float(np.mean(net) / net_std * np.sqrt(ANNUALIZATION)),
        "net_2bp_max_drawdown": max_drawdown(net),
        "annualized_turnover": None if years <= 0.0 else float(np.sum(turn) / years),
        "nonzero_exposure_share": None if pos.size == 0 else float(np.mean(np.abs(pos) > 0.0)),
        "average_absolute_exposure": None if pos.size == 0 else float(np.mean(np.abs(pos))),
        "half_exposure_share": None if pos.size == 0 else float(np.mean(np.isclose(np.abs(pos), CORE_EXPOSURE))),
        "full_exposure_share": None if pos.size == 0 else float(np.mean(np.isclose(np.abs(pos), 1.0))),
    }


def analyze_pair(frame: pd.DataFrame) -> dict[str, object]:
    ns = load_phase_b_namespace()
    config_type = ns["PriceOnlyConfig"]
    compute_price_only = ns["compute_price_only"]
    config = config_type()
    model = compute_price_only(frame.copy(), config)

    formal = pd.to_numeric(model["formal_id"], errors="coerce").fillna(0).to_numpy(int)
    range_score = pd.to_numeric(model["range_score"], errors="coerce").to_numpy(float)
    fresh_up = pd.to_numeric(model["range_break_up"], errors="coerce").fillna(0).to_numpy(float) > 0.5
    fresh_down = pd.to_numeric(model["range_break_dn"], errors="coerce").fillna(0).to_numpy(float) > 0.5
    warmup = int(config.rank_len - 1)
    base_signal, base_events = stage_lifecycle_signal(
        formal, fresh_up, fresh_down, warmup=warmup, confirm_bars=int(config.confirm_bars)
    )
    managed, management_events = range_managed_exposure(
        base_signal, formal, range_score, fresh_up, fresh_down, warmup
    )

    return {
        "rows": int(len(frame)),
        "warmup_bars": warmup,
        "base_events": base_events,
        "management_events": management_events,
        "variants": {
            "stage_lifecycle_base": strategy_metrics_fractional(frame, base_signal.astype(float), warmup),
            "stage_lifecycle_range_managed": strategy_metrics_fractional(frame, managed, warmup),
        },
    }


def _median(values: list[float]) -> float | None:
    return None if not values else float(np.median(values))


def aggregate_pairs(pairs: dict[str, dict[str, object]]) -> dict[str, object]:
    metrics = (
        "gross_ann_return",
        "gross_ann_vol",
        "gross_sharpe",
        "gross_max_drawdown",
        "net_2bp_ann_return",
        "net_2bp_sharpe",
        "net_2bp_max_drawdown",
        "annualized_turnover",
        "nonzero_exposure_share",
        "average_absolute_exposure",
        "half_exposure_share",
        "full_exposure_share",
    )
    variants: dict[str, object] = {}
    for variant in ("stage_lifecycle_base", "stage_lifecycle_range_managed"):
        row: dict[str, object] = {}
        for metric in metrics:
            vals = [
                float(pair["variants"][variant][metric])  # type: ignore[index]
                for pair in pairs.values()
                if pair["variants"][variant][metric] is not None  # type: ignore[index]
            ]
            row[f"median_pair_{metric}"] = _median(vals)
        variants[variant] = row

    wins = {
        "comparable_pairs": len(pairs),
        "managed_gross_return_wins": 0,
        "managed_gross_sharpe_wins": 0,
        "managed_gross_drawdown_wins": 0,
        "managed_net_2bp_return_wins": 0,
        "managed_net_2bp_sharpe_wins": 0,
        "managed_net_2bp_drawdown_wins": 0,
    }
    for pair in pairs.values():
        base = pair["variants"]["stage_lifecycle_base"]  # type: ignore[index]
        managed = pair["variants"]["stage_lifecycle_range_managed"]  # type: ignore[index]
        wins["managed_gross_return_wins"] += int(float(managed["gross_ann_return"]) > float(base["gross_ann_return"]))
        wins["managed_gross_sharpe_wins"] += int(float(managed["gross_sharpe"]) > float(base["gross_sharpe"]))
        wins["managed_gross_drawdown_wins"] += int(float(managed["gross_max_drawdown"]) > float(base["gross_max_drawdown"]))
        wins["managed_net_2bp_return_wins"] += int(float(managed["net_2bp_ann_return"]) > float(base["net_2bp_ann_return"]))
        wins["managed_net_2bp_sharpe_wins"] += int(float(managed["net_2bp_sharpe"]) > float(base["net_2bp_sharpe"]))
        wins["managed_net_2bp_drawdown_wins"] += int(float(managed["net_2bp_max_drawdown"]) > float(base["net_2bp_max_drawdown"]))

    event_keys = next(iter(pairs.values()))["management_events"].keys() if pairs else []  # type: ignore[index]
    management_events = {
        key: int(sum(int(pair["management_events"][key]) for pair in pairs.values()))  # type: ignore[index]
        for key in event_keys
    }
    return {"pair_count": len(pairs), "variants": variants, "wins": wins, "management_events": management_events}


def build_report() -> dict[str, object]:
    pairs = {pair: analyze_pair(frame) for pair, frame in load_frozen_pairs().items()}
    return {
        "schema_version": 1,
        "issue": 61,
        "status": "PHASE_C_RANGE_MANAGEMENT_REUSED_DATA_DEVELOPMENT_ONLY",
        "strong_range_threshold": STRONG_RANGE,
        "core_exposure": CORE_EXPOSURE,
        "execution": "close-observed desired exposure applied with one-bar lag",
        "pairs": pairs,
        "aggregate": aggregate_pairs(pairs),
        "boundary": "Frozen inherited rangeScore=70 and semantic 50/50 split. Reused development data only; no tuning or validation claim.",
    }


def pct(value: float | None) -> str:
    return "—" if value is None else f"{100.0 * value:.2f}%"


def num(value: float | None) -> str:
    return "—" if value is None else f"{value:.3f}"


def render_markdown(report: dict[str, object]) -> str:
    agg = report["aggregate"]  # type: ignore[index]
    lines = [
        "# Issue #61 — Phase C range-managed lifecycle",
        "",
        "**Reused-data development evidence only. Rule frozen before PnL.**",
        "",
        "- Base lifecycle unchanged.",
        "- Strong Trend Consolidation = existing `rangeScore >= 70` full range gate.",
        "- Exposure reduces 1.0 → 0.5; no automatic restore when rangeScore falls.",
        "- Fresh matching break in Formal Stage 2/5 restores 0.5 → 1.0.",
        "- No stop, target, trailing stop, leverage, or optimized fraction.",
        "",
        "## Median-pair metrics",
        "",
        "| Variant | Gross ann return | Gross Sharpe | Gross max DD | Net 2bp ann return | Net 2bp Sharpe | Net 2bp max DD | Avg abs exposure | Nonzero exposure | Turnover/yr | Half exposure |",
        "|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for variant in ("stage_lifecycle_base", "stage_lifecycle_range_managed"):
        row = agg["variants"][variant]
        lines.append(
            f"| {variant} | {pct(row['median_pair_gross_ann_return'])} | {num(row['median_pair_gross_sharpe'])} | "
            f"{pct(row['median_pair_gross_max_drawdown'])} | {pct(row['median_pair_net_2bp_ann_return'])} | "
            f"{num(row['median_pair_net_2bp_sharpe'])} | {pct(row['median_pair_net_2bp_max_drawdown'])} | "
            f"{pct(row['median_pair_average_absolute_exposure'])} | {pct(row['median_pair_nonzero_exposure_share'])} | "
            f"{num(row['median_pair_annualized_turnover'])} | {pct(row['median_pair_half_exposure_share'])} |"
        )

    w = agg["wins"]
    lines += [
        "",
        "## Incremental consistency: range-managed vs base",
        "",
        f"- Gross return better: **{w['managed_gross_return_wins']}/{w['comparable_pairs']}**.",
        f"- Gross Sharpe better: **{w['managed_gross_sharpe_wins']}/{w['comparable_pairs']}**.",
        f"- Gross max drawdown better: **{w['managed_gross_drawdown_wins']}/{w['comparable_pairs']}**.",
        f"- Net 2bp return better: **{w['managed_net_2bp_return_wins']}/{w['comparable_pairs']}**.",
        f"- Net 2bp Sharpe better: **{w['managed_net_2bp_sharpe_wins']}/{w['comparable_pairs']}**.",
        f"- Net 2bp max drawdown better: **{w['managed_net_2bp_drawdown_wins']}/{w['comparable_pairs']}**.",
        "",
        "## Management events",
        "",
    ]
    for key, value in agg["management_events"].items():
        lines.append(f"- `{key}`: {value}")

    lines += [
        "",
        "## Per pair",
        "",
        "| Pair | Base return | Managed return | Base Sharpe | Managed Sharpe | Base DD | Managed DD | Managed avg exposure | Reductions | Re-adds |",
        "|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for pair, result in report["pairs"].items():  # type: ignore[index]
        base = result["variants"]["stage_lifecycle_base"]
        managed = result["variants"]["stage_lifecycle_range_managed"]
        events = result["management_events"]
        reductions = int(events["long_reductions"]) + int(events["short_reductions"])
        readds = int(events["long_readds"]) + int(events["short_readds"])
        lines.append(
            f"| {pair} | {pct(base['gross_ann_return'])} | {pct(managed['gross_ann_return'])} | "
            f"{num(base['gross_sharpe'])} | {num(managed['gross_sharpe'])} | {pct(base['gross_max_drawdown'])} | "
            f"{pct(managed['gross_max_drawdown'])} | {pct(managed['average_absolute_exposure'])} | {reductions} | {readds} |"
        )

    lines += ["", "## Boundary", "", str(report["boundary"]), ""]
    return "\n".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--json-output", type=Path, required=True)
    parser.add_argument("--md-output", type=Path, required=True)
    args = parser.parse_args()
    report = build_report()
    args.json_output.parent.mkdir(parents=True, exist_ok=True)
    args.json_output.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    args.md_output.write_text(render_markdown(report), encoding="utf-8")
    print(json.dumps(report["aggregate"], indent=2))


if __name__ == "__main__":
    main()
