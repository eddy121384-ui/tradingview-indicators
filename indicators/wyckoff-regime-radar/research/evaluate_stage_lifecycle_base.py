#!/usr/bin/env python3
"""Issue #61 Phase-B minimal stage-aware lifecycle strategy proxy.

Rules are frozen in decisions/issue-61-phase-a-timing-decision.md before this
module inspects PnL.  No stop, target, partial sizing, leverage, add size, or
breakout threshold is optimized here.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
import pandas as pd

from diagnose_stage_lifecycle_break_timing import load_frozen_pairs
from generate_v06_phase_b_core import load_phase_b_namespace

ANNUALIZATION = 252.0
COST_PER_UNIT_TURNOVER = 0.0002
VARIANTS = ("binary_color", "stage_lifecycle_base")


def binary_color_signal(formal: np.ndarray, warmup: int) -> np.ndarray:
    out = np.zeros(len(formal), dtype=int)
    eligible = np.arange(len(formal)) >= warmup
    out[eligible & np.isin(formal, [1, 2, 3])] = 1
    out[eligible & np.isin(formal, [4, 5, 6])] = -1
    return out


def stage_lifecycle_signal(
    formal: np.ndarray,
    fresh_up: np.ndarray,
    fresh_down: np.ndarray,
    warmup: int,
    confirm_bars: int,
) -> tuple[np.ndarray, dict[str, int]]:
    """Frozen unit-exposure lifecycle state machine.

    Signal is the desired position known at each close.  Execution is handled
    separately with a one-bar lag in strategy_metrics().
    """
    n = len(formal)
    out = np.zeros(n, dtype=int)
    position = 0
    armed_dir = 0
    armed_at = -1

    stats = {
        "bull_setups_armed": 0,
        "bear_setups_armed": 0,
        "bull_setup_confirmed_entries": 0,
        "bear_setup_confirmed_entries": 0,
        "bull_direct_stage2_break_entries": 0,
        "bear_direct_stage5_break_entries": 0,
        "bull_setup_expired_or_cancelled": 0,
        "bear_setup_expired_or_cancelled": 0,
        "long_family_exits": 0,
        "short_family_exits": 0,
        "bull_continuation_break_candidates": 0,
        "bear_continuation_break_candidates": 0,
    }

    for i in range(n):
        if i < warmup:
            out[i] = 0
            continue

        stage = int(formal[i])
        was_holding = position

        # Existing trend-family exposure exits as soon as Formal leaves its
        # allowed trend/consolidation family.  No stop/target is introduced.
        if position == 1 and stage not in (2, 3):
            position = 0
            stats["long_family_exits"] += 1
        elif position == -1 and stage not in (5, 6):
            position = 0
            stats["short_family_exits"] += 1

        # Resolve an existing armed setup before processing a new break pulse.
        if armed_dir != 0:
            age = i - armed_at
            target = 2 if armed_dir == 1 else 5
            precursor = 1 if armed_dir == 1 else 4
            key_cancel = "bull_setup_expired_or_cancelled" if armed_dir == 1 else "bear_setup_expired_or_cancelled"
            key_confirm = "bull_setup_confirmed_entries" if armed_dir == 1 else "bear_setup_confirmed_entries"

            if age <= confirm_bars and stage == target:
                if position == 0:
                    position = armed_dir
                    stats[key_confirm] += 1
                armed_dir = 0
                armed_at = -1
            elif age > confirm_bars or stage not in (precursor, target):
                stats[key_cancel] += 1
                armed_dir = 0
                armed_at = -1

        # Continuation breaks are counted only if exposure existed before this
        # bar; a newly confirmed entry on the same bar is not an add candidate.
        if was_holding == 1 and stage == 2 and bool(fresh_up[i]):
            stats["bull_continuation_break_candidates"] += 1
        if was_holding == -1 and stage == 5 and bool(fresh_down[i]):
            stats["bear_continuation_break_candidates"] += 1

        # Flat entry / setup arming.  A fresh break inside an already-active
        # target trend stage is a direct trend-stage breakout entry/re-entry.
        if position == 0:
            if bool(fresh_up[i]) and stage == 2:
                position = 1
                armed_dir = 0
                armed_at = -1
                stats["bull_direct_stage2_break_entries"] += 1
            elif bool(fresh_down[i]) and stage == 5:
                position = -1
                armed_dir = 0
                armed_at = -1
                stats["bear_direct_stage5_break_entries"] += 1
            elif bool(fresh_up[i]) and stage == 1:
                if armed_dir != 1:
                    if armed_dir == -1:
                        stats["bear_setup_expired_or_cancelled"] += 1
                    stats["bull_setups_armed"] += 1
                armed_dir = 1
                armed_at = i
            elif bool(fresh_down[i]) and stage == 4:
                if armed_dir != -1:
                    if armed_dir == 1:
                        stats["bull_setup_expired_or_cancelled"] += 1
                    stats["bear_setups_armed"] += 1
                armed_dir = -1
                armed_at = i

        out[i] = position

    return out, stats


def annualized_return(returns: np.ndarray) -> float | None:
    if returns.size == 0:
        return None
    terminal = float(np.prod(1.0 + returns))
    if terminal <= 0.0:
        return -1.0
    return float(terminal ** (ANNUALIZATION / returns.size) - 1.0)


def max_drawdown(returns: np.ndarray) -> float | None:
    if returns.size == 0:
        return None
    equity = np.concatenate(([1.0], np.cumprod(1.0 + returns)))
    peaks = np.maximum.accumulate(equity)
    return float(np.min(equity / peaks - 1.0))


def holding_durations(position: np.ndarray) -> list[int]:
    durations: list[int] = []
    current = 0
    length = 0
    for value in position.astype(int):
        if value == 0:
            if current != 0:
                durations.append(length)
            current = 0
            length = 0
        elif value == current:
            length += 1
        else:
            if current != 0:
                durations.append(length)
            current = value
            length = 1
    if current != 0:
        durations.append(length)
    return durations


def strategy_metrics(frame: pd.DataFrame, signal: np.ndarray, warmup: int) -> dict[str, float | int | None]:
    close = pd.to_numeric(frame["close"], errors="coerce").to_numpy(float)
    n = len(close)
    asset_return = np.zeros(n, dtype=float)
    valid = np.isfinite(close[1:]) & np.isfinite(close[:-1]) & (close[:-1] > 0.0)
    asset_return[1:][valid] = close[1:][valid] / close[:-1][valid] - 1.0

    # Signal observed at close t becomes position for t -> t+1, represented as
    # signal[t] applied to the next row's close-to-close return.
    position = np.zeros(n, dtype=float)
    if n > 1:
        position[1:] = signal[:-1]
    turnover = np.zeros(n, dtype=float)
    if n > 1:
        turnover[1:] = np.abs(position[1:] - position[:-1])

    score_mask = np.arange(n) >= max(1, warmup + 1)
    gross_all = position * asset_return
    net_all = gross_all - COST_PER_UNIT_TURNOVER * turnover
    gross = gross_all[score_mask]
    net = net_all[score_mask]
    pos = position[score_mask]
    turn = turnover[score_mask]

    gross_std = float(np.std(gross, ddof=1)) if gross.size > 1 else 0.0
    net_std = float(np.std(net, ddof=1)) if net.size > 1 else 0.0
    years = gross.size / ANNUALIZATION if gross.size else 0.0
    durations = holding_durations(signal[warmup:])

    entries = 0
    reversals = 0
    previous = 0
    for value in signal[warmup:].astype(int):
        if value != 0 and value != previous:
            entries += 1
            if previous == -value:
                reversals += 1
        previous = value

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
        "exposure_share": float(np.mean(np.abs(pos) > 0.0)) if pos.size else None,
        "signal_entries": int(entries),
        "signal_reversals": int(reversals),
        "holding_episodes": int(len(durations)),
        "median_holding_bars": None if not durations else float(np.median(durations)),
    }


def analyze_pair(frame: pd.DataFrame) -> dict[str, object]:
    namespace = load_phase_b_namespace()
    config_type = namespace["PriceOnlyConfig"]
    compute_price_only = namespace["compute_price_only"]
    config = config_type()
    model = compute_price_only(frame.copy(), config)

    formal = pd.to_numeric(model["formal_id"], errors="coerce").fillna(0).to_numpy(int)
    fresh_up = pd.to_numeric(model["range_break_up"], errors="coerce").fillna(0).to_numpy(float) > 0.5
    fresh_down = pd.to_numeric(model["range_break_dn"], errors="coerce").fillna(0).to_numpy(float) > 0.5
    warmup = int(config.rank_len - 1)

    binary = binary_color_signal(formal, warmup)
    lifecycle, lifecycle_events = stage_lifecycle_signal(
        formal,
        fresh_up,
        fresh_down,
        warmup=warmup,
        confirm_bars=int(config.confirm_bars),
    )

    return {
        "rows": int(len(frame)),
        "start_date": str(pd.Timestamp(frame["date"].iloc[0]).date()),
        "end_date": str(pd.Timestamp(frame["date"].iloc[-1]).date()),
        "warmup_bars": warmup,
        "confirm_bars": int(config.confirm_bars),
        "lifecycle_events": lifecycle_events,
        "variants": {
            "binary_color": strategy_metrics(frame, binary, warmup),
            "stage_lifecycle_base": strategy_metrics(frame, lifecycle, warmup),
        },
    }


def median(values: list[float]) -> float | None:
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
        "median_holding_bars",
    )
    variants: dict[str, object] = {}
    for variant in VARIANTS:
        row: dict[str, object] = {}
        for metric in metric_names:
            values = [
                float(pair["variants"][variant][metric])  # type: ignore[index]
                for pair in pairs.values()
                if pair["variants"][variant][metric] is not None  # type: ignore[index]
            ]
            row[f"median_pair_{metric}"] = median(values)
        row["total_signal_entries"] = int(sum(int(pair["variants"][variant]["signal_entries"]) for pair in pairs.values()))  # type: ignore[index]
        variants[variant] = row

    wins = {
        "comparable_pairs": 0,
        "lifecycle_gross_return_wins": 0,
        "lifecycle_gross_sharpe_wins": 0,
        "lifecycle_gross_drawdown_wins": 0,
        "lifecycle_net_2bp_return_wins": 0,
        "lifecycle_net_2bp_sharpe_wins": 0,
        "lifecycle_net_2bp_drawdown_wins": 0,
    }
    for pair in pairs.values():
        base = pair["variants"]["binary_color"]  # type: ignore[index]
        life = pair["variants"]["stage_lifecycle_base"]  # type: ignore[index]
        wins["comparable_pairs"] += 1
        wins["lifecycle_gross_return_wins"] += int(float(life["gross_ann_return"]) > float(base["gross_ann_return"]))
        wins["lifecycle_gross_sharpe_wins"] += int(float(life["gross_sharpe"]) > float(base["gross_sharpe"]))
        wins["lifecycle_gross_drawdown_wins"] += int(float(life["gross_max_drawdown"]) > float(base["gross_max_drawdown"]))
        wins["lifecycle_net_2bp_return_wins"] += int(float(life["net_2bp_ann_return"]) > float(base["net_2bp_ann_return"]))
        wins["lifecycle_net_2bp_sharpe_wins"] += int(float(life["net_2bp_sharpe"]) > float(base["net_2bp_sharpe"]))
        wins["lifecycle_net_2bp_drawdown_wins"] += int(float(life["net_2bp_max_drawdown"]) > float(base["net_2bp_max_drawdown"]))

    event_keys = next(iter(pairs.values()))["lifecycle_events"].keys() if pairs else []  # type: ignore[index]
    lifecycle_events = {
        key: int(sum(int(pair["lifecycle_events"][key]) for pair in pairs.values()))  # type: ignore[index]
        for key in event_keys
    }
    return {"pair_count": len(pairs), "variants": variants, "wins": wins, "lifecycle_events": lifecycle_events}


def build_report() -> dict[str, object]:
    pairs = {pair: analyze_pair(frame) for pair, frame in load_frozen_pairs().items()}
    return {
        "schema_version": 1,
        "issue": 61,
        "status": "PHASE_B_BASE_LIFECYCLE_REUSED_DATA_DEVELOPMENT_ONLY",
        "execution": "close-observed signal applied with one-bar lag to next close-to-close return",
        "cost_sensitivity_per_unit_turnover": COST_PER_UNIT_TURNOVER,
        "variants": list(VARIANTS),
        "pairs": pairs,
        "aggregate": aggregate_pairs(pairs),
        "boundary": "All samples are reused evidence. No stop/target/sizing optimization and no independent validation claim.",
    }


def pct(value: float | None) -> str:
    return "—" if value is None else f"{100.0 * value:.2f}%"


def num(value: float | None) -> str:
    return "—" if value is None else f"{value:.3f}"


def render_markdown(report: dict[str, object]) -> str:
    agg = report["aggregate"]  # type: ignore[index]
    lines = [
        "# Issue #61 — Phase B base stage-lifecycle proxy",
        "",
        "**Reused-data development evidence only. Rules frozen before this PnL comparison.**",
        "",
        "- `binary_color`: stages 1/2/3 long; 4/5/6 short.",
        "- `stage_lifecycle_base`: Stage 1/4 observe; fresh break arms up to confirmBars=3; Stage 2/5 confirms entry; hold only in 2/3 or 5/6; no stops, targets, partial sizing or add leverage.",
        "- Signals are applied with one-bar execution lag.",
        "- 2 bp cost is reported only as fixed sensitivity.",
        "",
        "## Median-pair metrics",
        "",
        "| Variant | Gross ann return | Gross Sharpe | Gross max DD | Net 2bp ann return | Net 2bp Sharpe | Net 2bp max DD | Exposure | Turnover/yr | Median hold bars | Entries |",
        "|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for variant in VARIANTS:
        row = agg["variants"][variant]
        lines.append(
            f"| {variant} | {pct(row['median_pair_gross_ann_return'])} | {num(row['median_pair_gross_sharpe'])} | "
            f"{pct(row['median_pair_gross_max_drawdown'])} | {pct(row['median_pair_net_2bp_ann_return'])} | "
            f"{num(row['median_pair_net_2bp_sharpe'])} | {pct(row['median_pair_net_2bp_max_drawdown'])} | "
            f"{pct(row['median_pair_exposure_share'])} | {num(row['median_pair_annualized_turnover'])} | "
            f"{num(row['median_pair_median_holding_bars'])} | {row['total_signal_entries']} |"
        )

    wins = agg["wins"]
    lines += [
        "",
        "## Pair consistency: lifecycle vs binary color",
        "",
        f"- Gross return better: **{wins['lifecycle_gross_return_wins']}/{wins['comparable_pairs']}**.",
        f"- Gross Sharpe better: **{wins['lifecycle_gross_sharpe_wins']}/{wins['comparable_pairs']}**.",
        f"- Gross max drawdown better: **{wins['lifecycle_gross_drawdown_wins']}/{wins['comparable_pairs']}**.",
        f"- Net 2bp return better: **{wins['lifecycle_net_2bp_return_wins']}/{wins['comparable_pairs']}**.",
        f"- Net 2bp Sharpe better: **{wins['lifecycle_net_2bp_sharpe_wins']}/{wins['comparable_pairs']}**.",
        f"- Net 2bp max drawdown better: **{wins['lifecycle_net_2bp_drawdown_wins']}/{wins['comparable_pairs']}**.",
        "",
        "## Lifecycle event counts",
        "",
    ]
    for key, value in agg["lifecycle_events"].items():
        lines.append(f"- `{key}`: {value}")

    lines += ["", "## Per pair", "", "| Pair | Binary gross return | Lifecycle gross return | Binary Sharpe | Lifecycle Sharpe | Binary DD | Lifecycle DD | Lifecycle exposure | Lifecycle entries |", "|---|---:|---:|---:|---:|---:|---:|---:|---:|"]
    for pair, result in report["pairs"].items():  # type: ignore[index]
        binary = result["variants"]["binary_color"]
        life = result["variants"]["stage_lifecycle_base"]
        lines.append(
            f"| {pair} | {pct(binary['gross_ann_return'])} | {pct(life['gross_ann_return'])} | "
            f"{num(binary['gross_sharpe'])} | {num(life['gross_sharpe'])} | {pct(binary['gross_max_drawdown'])} | "
            f"{pct(life['gross_max_drawdown'])} | {pct(life['exposure_share'])} | {life['signal_entries']} |"
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
