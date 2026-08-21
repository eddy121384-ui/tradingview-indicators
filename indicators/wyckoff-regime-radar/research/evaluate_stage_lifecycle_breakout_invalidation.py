#!/usr/bin/env python3
"""Issue #61 Phase-D breakout-invalidation stop evaluator.

Rule is frozen in `decisions/issue-61-phase-d-breakout-invalidation-freeze.md`
before PnL inspection.  It overlays the frozen base lifecycle with the structural
level crossed by the fresh break that caused entry; no ATR / percent stop exists.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
import pandas as pd

from diagnose_stage_lifecycle_break_timing import load_frozen_pairs
from evaluate_stage_lifecycle_base import stage_lifecycle_signal, strategy_metrics
from generate_v06_phase_b_core import load_phase_b_namespace


def _matching_fresh(
    direction: int,
    index: int,
    formal: np.ndarray,
    fresh_up: np.ndarray,
    fresh_down: np.ndarray,
) -> bool:
    if direction == 1:
        return int(formal[index]) == 2 and bool(fresh_up[index])
    return int(formal[index]) == 5 and bool(fresh_down[index])


def _entry_anchor(
    index: int,
    direction: int,
    formal: np.ndarray,
    fresh_up: np.ndarray,
    fresh_down: np.ndarray,
    range_high_break: np.ndarray,
    range_low_break: np.ndarray,
    confirm_bars: int,
) -> float:
    """Recover the fresh-break level that caused a frozen base entry."""
    if _matching_fresh(direction, index, formal, fresh_up, fresh_down):
        level = range_high_break[index] if direction == 1 else range_low_break[index]
        return float(level)

    precursor = 1 if direction == 1 else 4
    fresh = fresh_up if direction == 1 else fresh_down
    levels = range_high_break if direction == 1 else range_low_break
    start = max(0, index - confirm_bars)
    for j in range(index - 1, start - 1, -1):
        if int(formal[j]) == precursor and bool(fresh[j]):
            return float(levels[j])
    return float("nan")


def breakout_invalidation_signal(
    base_signal: np.ndarray,
    close: np.ndarray,
    formal: np.ndarray,
    fresh_up: np.ndarray,
    fresh_down: np.ndarray,
    range_high_break: np.ndarray,
    range_low_break: np.ndarray,
    warmup: int,
    confirm_bars: int,
) -> tuple[np.ndarray, dict[str, int]]:
    """Overlay the frozen base lifecycle with failed-breakout invalidation.

    A stopped direction stays flat while the underlying base episode continues.
    It may re-enter only on a new direct fresh break in matching Formal Stage 2/5.
    """
    arrays = (
        close,
        formal,
        fresh_up,
        fresh_down,
        range_high_break,
        range_low_break,
    )
    n = len(base_signal)
    if not all(len(values) == n for values in arrays):
        raise ValueError("all arrays must have equal length")

    out = np.zeros(n, dtype=int)
    position = 0
    entry_level = float("nan")
    stopped_dir = 0
    previous_base = 0

    stats = {
        "long_invalidation_exits": 0,
        "short_invalidation_exits": 0,
        "long_reentries_after_invalidation": 0,
        "short_reentries_after_invalidation": 0,
        "entry_anchor_missing": 0,
    }

    for i in range(n):
        if i < warmup:
            previous_base = int(base_signal[i])
            continue

        base_dir = int(base_signal[i])

        # A base episode ended or changed direction: clear any stop latch and
        # allow the new frozen base episode to establish its own entry anchor.
        if base_dir != previous_base:
            stopped_dir = 0
            if base_dir == 0:
                position = 0
                entry_level = float("nan")
            else:
                position = base_dir
                entry_level = _entry_anchor(
                    i,
                    base_dir,
                    formal,
                    fresh_up,
                    fresh_down,
                    range_high_break,
                    range_low_break,
                    confirm_bars,
                )
                if not np.isfinite(entry_level):
                    stats["entry_anchor_missing"] += 1

        # Underlying base episode remains active but the overlay stopped it.
        # Only a new direct fresh break in the matching trend stage can re-enter.
        elif base_dir != 0 and stopped_dir == base_dir:
            if _matching_fresh(base_dir, i, formal, fresh_up, fresh_down):
                position = base_dir
                stopped_dir = 0
                entry_level = float(
                    range_high_break[i] if base_dir == 1 else range_low_break[i]
                )
                if base_dir == 1:
                    stats["long_reentries_after_invalidation"] += 1
                else:
                    stats["short_reentries_after_invalidation"] += 1
            else:
                position = 0

        # If base remains flat, overlay must remain flat too.
        elif base_dir == 0:
            position = 0
            entry_level = float("nan")
            stopped_dir = 0

        # Invalidation is evaluated only after a position already existed on a
        # previous desired-signal bar.  This prevents same-entry-bar stop-outs.
        was_holding = i > warmup and int(out[i - 1]) == position and position != 0
        if was_holding and np.isfinite(entry_level) and np.isfinite(close[i]):
            invalidated = (
                position == 1 and float(close[i]) <= entry_level
            ) or (
                position == -1 and float(close[i]) >= entry_level
            )
            if invalidated:
                stopped_dir = position
                if position == 1:
                    stats["long_invalidation_exits"] += 1
                else:
                    stats["short_invalidation_exits"] += 1
                position = 0
                entry_level = float("nan")

        out[i] = position
        previous_base = base_dir

    return out, stats


def analyze_pair(frame: pd.DataFrame) -> dict[str, object]:
    ns = load_phase_b_namespace()
    config_type = ns["PriceOnlyConfig"]
    compute_price_only = ns["compute_price_only"]
    config = config_type()
    model = compute_price_only(frame.copy(), config)

    formal = pd.to_numeric(model["formal_id"], errors="coerce").fillna(0).to_numpy(int)
    fresh_up = pd.to_numeric(model["range_break_up"], errors="coerce").fillna(0).to_numpy(float) > 0.5
    fresh_down = pd.to_numeric(model["range_break_dn"], errors="coerce").fillna(0).to_numpy(float) > 0.5
    range_high_break = pd.to_numeric(model["range_high_break"], errors="coerce").to_numpy(float)
    range_low_break = pd.to_numeric(model["range_low_break"], errors="coerce").to_numpy(float)
    close = pd.to_numeric(frame["close"], errors="coerce").to_numpy(float)
    warmup = int(config.rank_len - 1)
    confirm_bars = int(config.confirm_bars)

    base_signal, base_events = stage_lifecycle_signal(
        formal,
        fresh_up,
        fresh_down,
        warmup=warmup,
        confirm_bars=confirm_bars,
    )
    managed, stop_events = breakout_invalidation_signal(
        base_signal,
        close,
        formal,
        fresh_up,
        fresh_down,
        range_high_break,
        range_low_break,
        warmup,
        confirm_bars,
    )

    return {
        "rows": int(len(frame)),
        "warmup_bars": warmup,
        "base_events": base_events,
        "stop_events": stop_events,
        "variants": {
            "stage_lifecycle_base": strategy_metrics(frame, base_signal, warmup),
            "stage_lifecycle_breakout_invalidation": strategy_metrics(frame, managed, warmup),
        },
    }


def _median(values: list[float]) -> float | None:
    return None if not values else float(np.median(values))


def aggregate_pairs(pairs: dict[str, dict[str, object]]) -> dict[str, object]:
    metric_names = (
        "gross_ann_return",
        "gross_ann_vol",
        "gross_sharpe",
        "gross_max_drawdown",
        "net_2bp_ann_return",
        "net_2bp_sharpe",
        "net_2bp_max_drawdown",
        "annualized_turnover",
        "exposure_share",
        "median_hold_bars",
        "entries",
    )
    variants: dict[str, object] = {}
    for variant in ("stage_lifecycle_base", "stage_lifecycle_breakout_invalidation"):
        row: dict[str, object] = {}
        for metric in metric_names:
            values = [
                float(pair["variants"][variant][metric])  # type: ignore[index]
                for pair in pairs.values()
                if pair["variants"][variant][metric] is not None  # type: ignore[index]
            ]
            row[f"median_pair_{metric}"] = _median(values)
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
        managed = pair["variants"]["stage_lifecycle_breakout_invalidation"]  # type: ignore[index]
        wins["managed_gross_return_wins"] += int(float(managed["gross_ann_return"]) > float(base["gross_ann_return"]))
        wins["managed_gross_sharpe_wins"] += int(float(managed["gross_sharpe"]) > float(base["gross_sharpe"]))
        wins["managed_gross_drawdown_wins"] += int(float(managed["gross_max_drawdown"]) > float(base["gross_max_drawdown"]))
        wins["managed_net_2bp_return_wins"] += int(float(managed["net_2bp_ann_return"]) > float(base["net_2bp_ann_return"]))
        wins["managed_net_2bp_sharpe_wins"] += int(float(managed["net_2bp_sharpe"]) > float(base["net_2bp_sharpe"]))
        wins["managed_net_2bp_drawdown_wins"] += int(float(managed["net_2bp_max_drawdown"]) > float(base["net_2bp_max_drawdown"]))

    stop_keys = next(iter(pairs.values()))["stop_events"].keys() if pairs else []  # type: ignore[index]
    stop_events = {
        key: int(sum(int(pair["stop_events"][key]) for pair in pairs.values()))  # type: ignore[index]
        for key in stop_keys
    }
    return {
        "pair_count": len(pairs),
        "variants": variants,
        "wins": wins,
        "stop_events": stop_events,
    }


def build_report() -> dict[str, object]:
    pairs = {pair: analyze_pair(frame) for pair, frame in load_frozen_pairs().items()}
    return {
        "schema_version": 1,
        "issue": 61,
        "status": "PHASE_D_BREAKOUT_INVALIDATION_REUSED_DATA_DEVELOPMENT_ONLY",
        "rule": "close crosses back through the fresh structural-break level that caused entry",
        "execution": "close-observed desired position applied with one-bar lag",
        "pairs": pairs,
        "aggregate": aggregate_pairs(pairs),
        "boundary": "Frozen structural invalidation only. No ATR/percent buffer, target, trailing stop, sizing, or validation claim.",
    }


def pct(value: float | None) -> str:
    return "—" if value is None else f"{100.0 * value:.2f}%"


def num(value: float | None) -> str:
    return "—" if value is None else f"{value:.3f}"


def render_markdown(report: dict[str, object]) -> str:
    agg = report["aggregate"]  # type: ignore[index]
    lines = [
        "# Issue #61 — Phase D breakout-invalidation stop",
        "",
        "**Reused-data development evidence only. Rule frozen before PnL.**",
        "",
        "- Base lifecycle unchanged except for structural failed-breakout exit.",
        "- Long exits when close <= the upside break level that caused entry.",
        "- Short exits when close >= the downside break level that caused entry.",
        "- Re-entry after a stop requires a new matching fresh break.",
        "- No ATR / percent stop, buffer, target, trailing stop, or partial sizing.",
        "",
        "## Median-pair metrics",
        "",
        "| Variant | Gross ann return | Gross Sharpe | Gross max DD | Net 2bp ann return | Net 2bp Sharpe | Net 2bp max DD | Exposure | Turnover/yr | Median hold bars | Entries |",
        "|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for variant in ("stage_lifecycle_base", "stage_lifecycle_breakout_invalidation"):
        row = agg["variants"][variant]
        lines.append(
            f"| {variant} | {pct(row['median_pair_gross_ann_return'])} | {num(row['median_pair_gross_sharpe'])} | "
            f"{pct(row['median_pair_gross_max_drawdown'])} | {pct(row['median_pair_net_2bp_ann_return'])} | "
            f"{num(row['median_pair_net_2bp_sharpe'])} | {pct(row['median_pair_net_2bp_max_drawdown'])} | "
            f"{pct(row['median_pair_exposure_share'])} | {num(row['median_pair_annualized_turnover'])} | "
            f"{num(row['median_pair_median_hold_bars'])} | {num(row['median_pair_entries'])} |"
        )

    w = agg["wins"]
    lines += [
        "",
        "## Incremental consistency: invalidation stop vs base",
        "",
        f"- Gross return better: **{w['managed_gross_return_wins']}/{w['comparable_pairs']}**.",
        f"- Gross Sharpe better: **{w['managed_gross_sharpe_wins']}/{w['comparable_pairs']}**.",
        f"- Gross max drawdown better: **{w['managed_gross_drawdown_wins']}/{w['comparable_pairs']}**.",
        f"- Net 2bp return better: **{w['managed_net_2bp_return_wins']}/{w['comparable_pairs']}**.",
        f"- Net 2bp Sharpe better: **{w['managed_net_2bp_sharpe_wins']}/{w['comparable_pairs']}**.",
        f"- Net 2bp max drawdown better: **{w['managed_net_2bp_drawdown_wins']}/{w['comparable_pairs']}**.",
        "",
        "## Stop events",
        "",
    ]
    for key, value in agg["stop_events"].items():
        lines.append(f"- `{key}`: {value}")

    lines += [
        "",
        "## Per pair",
        "",
        "| Pair | Base return | Stop return | Base Sharpe | Stop Sharpe | Base DD | Stop DD | Base exposure | Stop exposure | Invalidation exits |",
        "|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for pair, result in report["pairs"].items():  # type: ignore[index]
        base = result["variants"]["stage_lifecycle_base"]
        managed = result["variants"]["stage_lifecycle_breakout_invalidation"]
        events = result["stop_events"]
        exits = int(events["long_invalidation_exits"]) + int(events["short_invalidation_exits"])
        lines.append(
            f"| {pair} | {pct(base['gross_ann_return'])} | {pct(managed['gross_ann_return'])} | "
            f"{num(base['gross_sharpe'])} | {num(managed['gross_sharpe'])} | {pct(base['gross_max_drawdown'])} | "
            f"{pct(managed['gross_max_drawdown'])} | {pct(base['exposure_share'])} | {pct(managed['exposure_share'])} | {exits} |"
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
