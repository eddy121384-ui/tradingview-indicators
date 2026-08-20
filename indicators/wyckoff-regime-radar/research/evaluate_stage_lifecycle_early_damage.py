#!/usr/bin/env python3
"""Issue #61 Phase-B incremental Early-Damaged lifecycle overlay.

Overlay mechanics are frozen in
`decisions/issue-61-phase-b-early-damage-overlay-freeze.md` before this module
inspects overlay PnL.  The exact Issue #57 Transition Health engine is carried
forward byte-for-byte from archived PR #58.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

import numpy as np
import pandas as pd

from diagnose_stage_lifecycle_break_timing import load_frozen_pairs
from evaluate_stage_lifecycle_base import (
    binary_color_signal,
    stage_lifecycle_signal,
    strategy_metrics,
)
from generate_v06_phase_b_core import load_phase_b_namespace
from transition_health_online import CHECKPOINT, compute_transition_health

HERE = Path(__file__).resolve().parent
VARIANTS = ("binary_color", "stage_lifecycle_base", "stage_lifecycle_plus_early_damage")

FROZEN_TH_BLOBS = {
    "transition_health_online.py": "69c065f3220e5616feee94c177a82d72c32828c1",
    "diagnose_bridge_formation_outcomes.py": "29c495df156cf4d0975fcd7c53e76b754f3f6dc3",
    "diagnose_consensus_formation_and_formal_lag.py": "b512d180766bc10ebb64ea849df2c0faaca7d8a3",
    "diagnose_handoff_weight_behavior.py": "a532a88dbbcf5da52ad783547a6fe4f5d68fc70a",
    "diagnose_transition_formation_and_regime_decay.py": "08b081f5cef4bd77c3edff61a60e0764bec79e5b",
    "diagnose_v06_top2_directional_consensus.py": "12b45fa0cdac2f7c7d34be0242e853af9fce5e43",
}


def git_blob_sha(path: Path) -> str:
    data = path.read_bytes()
    return hashlib.sha1(f"blob {len(data)}\0".encode() + data).hexdigest()


def verify_frozen_transition_health_files() -> None:
    for name, expected in FROZEN_TH_BLOBS.items():
        actual = git_blob_sha(HERE / name)
        if actual != expected:
            raise RuntimeError(f"{name}: frozen Issue #57 blob drifted: {actual} != {expected}")


def early_damage_pulses(th: pd.DataFrame) -> np.ndarray:
    """First observable strict-lead loss during watch ages +1..+3.

    This is the same mechanical definition used by the Issue #57 color-first
    overlay diagnostic: Transition Health keeps `lead_held=False` after the
    first loss, so the True->False transition emits exactly one pulse.
    """
    tracked = th["transition_health_tracked"].to_numpy(bool)
    held = th["transition_health_lead_held"].to_numpy(bool)
    age = pd.to_numeric(th["transition_health_watch_age"], errors="coerce").fillna(0).to_numpy(int)
    out = np.zeros(len(th), dtype=bool)
    for i in range(1, len(th)):
        if tracked[i] and 1 <= age[i] <= CHECKPOINT and held[i - 1] and not held[i]:
            out[i] = True
    return out


def stage_lifecycle_with_early_damage(
    formal: np.ndarray,
    fresh_up: np.ndarray,
    fresh_down: np.ndarray,
    early_damage: np.ndarray,
    th_direction: np.ndarray,
    th_resolution: np.ndarray,
    warmup: int,
    confirm_bars: int,
) -> tuple[np.ndarray, dict[str, int]]:
    """Frozen base lifecycle plus matching Early-Damaged exit/block overlay."""
    n = len(formal)
    arrays = (fresh_up, fresh_down, early_damage, th_direction, th_resolution)
    if any(len(values) != n for values in arrays):
        raise ValueError("all lifecycle/Transition Health arrays must have equal length")

    out = np.zeros(n, dtype=int)
    position = 0
    armed_dir = 0
    armed_at = -1
    blocked_dir = 0

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
        "early_damage_pulses": 0,
        "early_damage_long_exits": 0,
        "early_damage_short_exits": 0,
        "early_damage_bull_setup_cancels": 0,
        "early_damage_bear_setup_cancels": 0,
        "damage_blocks_started_bull": 0,
        "damage_blocks_started_bear": 0,
        "damage_block_resolutions": 0,
        "blocked_bull_entry_attempts": 0,
        "blocked_bear_entry_attempts": 0,
    }

    for i in range(n):
        if i < warmup:
            out[i] = 0
            continue

        stage = int(formal[i])
        was_holding = position

        # Base family exits remain unchanged and happen before overlay handling.
        if position == 1 and stage not in (2, 3):
            position = 0
            stats["long_family_exits"] += 1
        elif position == -1 and stage not in (5, 6):
            position = 0
            stats["short_family_exits"] += 1

        # A frozen TH watch is globally non-overlapping. Its resolution therefore
        # clears the one possible active direction block. No auto re-entry follows.
        if bool(th_resolution[i]) and blocked_dir != 0:
            blocked_dir = 0
            stats["damage_block_resolutions"] += 1

        # Early Damaged starts/refreshes the matching direction block, exits only
        # matching exposure, and cancels only a matching armed setup.
        if bool(early_damage[i]):
            damage_dir = int(th_direction[i])
            if damage_dir not in (-1, 1):
                raise RuntimeError("Early Damaged pulse must retain frozen watch direction")
            stats["early_damage_pulses"] += 1
            if blocked_dir != damage_dir:
                if damage_dir == 1:
                    stats["damage_blocks_started_bull"] += 1
                else:
                    stats["damage_blocks_started_bear"] += 1
            blocked_dir = damage_dir

            if position == damage_dir:
                if damage_dir == 1:
                    stats["early_damage_long_exits"] += 1
                else:
                    stats["early_damage_short_exits"] += 1
                position = 0

            if armed_dir == damage_dir:
                if damage_dir == 1:
                    stats["early_damage_bull_setup_cancels"] += 1
                else:
                    stats["early_damage_bear_setup_cancels"] += 1
                armed_dir = 0
                armed_at = -1

        # Existing armed setup can confirm only if its direction is not currently
        # blocked by the same damaged TH watch.
        if armed_dir != 0:
            age = i - armed_at
            target = 2 if armed_dir == 1 else 5
            precursor = 1 if armed_dir == 1 else 4
            key_cancel = "bull_setup_expired_or_cancelled" if armed_dir == 1 else "bear_setup_expired_or_cancelled"
            key_confirm = "bull_setup_confirmed_entries" if armed_dir == 1 else "bear_setup_confirmed_entries"

            if blocked_dir == armed_dir:
                stats[key_cancel] += 1
                armed_dir = 0
                armed_at = -1
            elif age <= confirm_bars and stage == target:
                if position == 0:
                    position = armed_dir
                    stats[key_confirm] += 1
                armed_dir = 0
                armed_at = -1
            elif age > confirm_bars or stage not in (precursor, target):
                stats[key_cancel] += 1
                armed_dir = 0
                armed_at = -1

        # Continuation events are diagnostics only, same as base. The overlay
        # does not increase unit exposure.
        if was_holding == 1 and stage == 2 and bool(fresh_up[i]):
            stats["bull_continuation_break_candidates"] += 1
        if was_holding == -1 and stage == 5 and bool(fresh_down[i]):
            stats["bear_continuation_break_candidates"] += 1

        if position == 0:
            if bool(fresh_up[i]) and stage in (1, 2) and blocked_dir == 1:
                stats["blocked_bull_entry_attempts"] += 1
            elif bool(fresh_down[i]) and stage in (4, 5) and blocked_dir == -1:
                stats["blocked_bear_entry_attempts"] += 1
            elif bool(fresh_up[i]) and stage == 2:
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


def analyze_pair(frame: pd.DataFrame) -> dict[str, object]:
    verify_frozen_transition_health_files()
    namespace = load_phase_b_namespace()
    config_type = namespace["PriceOnlyConfig"]
    compute_price_only = namespace["compute_price_only"]
    config = config_type()
    model = compute_price_only(frame.copy(), config)

    formal = pd.to_numeric(model["formal_id"], errors="coerce").fillna(0).to_numpy(int)
    fresh_up = pd.to_numeric(model["range_break_up"], errors="coerce").fillna(0).to_numpy(float) > 0.5
    fresh_down = pd.to_numeric(model["range_break_dn"], errors="coerce").fillna(0).to_numpy(float) > 0.5
    warmup = int(config.rank_len - 1)

    th = compute_transition_health(model)
    damage = early_damage_pulses(th)
    th_direction = pd.to_numeric(th["transition_health_direction"], errors="coerce").fillna(0).to_numpy(int)
    th_resolution = th["transition_health_resolution_pulse"].to_numpy(bool)

    binary = binary_color_signal(formal, warmup)
    base, base_events = stage_lifecycle_signal(
        formal, fresh_up, fresh_down, warmup=warmup, confirm_bars=int(config.confirm_bars)
    )
    managed, managed_events = stage_lifecycle_with_early_damage(
        formal,
        fresh_up,
        fresh_down,
        damage,
        th_direction,
        th_resolution,
        warmup=warmup,
        confirm_bars=int(config.confirm_bars),
    )

    return {
        "rows": int(len(frame)),
        "start_date": str(pd.Timestamp(frame["date"].iloc[0]).date()),
        "end_date": str(pd.Timestamp(frame["date"].iloc[-1]).date()),
        "warmup_bars": warmup,
        "confirm_bars": int(config.confirm_bars),
        "transition_health": {
            "early_damage_pulses_after_warmup": int(np.sum(damage[warmup:])),
            "resolution_pulses_after_warmup": int(np.sum(th_resolution[warmup:])),
        },
        "base_events": base_events,
        "managed_events": managed_events,
        "variants": {
            "binary_color": strategy_metrics(frame, binary, warmup),
            "stage_lifecycle_base": strategy_metrics(frame, base, warmup),
            "stage_lifecycle_plus_early_damage": strategy_metrics(frame, managed, warmup),
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
        "median_holding_bars",
    )
    variants: dict[str, object] = {}
    for variant in VARIANTS:
        row: dict[str, object] = {}
        for metric in metric_names:
            vals = [
                float(pair["variants"][variant][metric])  # type: ignore[index]
                for pair in pairs.values()
                if pair["variants"][variant][metric] is not None  # type: ignore[index]
            ]
            row[f"median_pair_{metric}"] = _median(vals)
        row["total_signal_entries"] = int(
            sum(int(pair["variants"][variant]["signal_entries"]) for pair in pairs.values())  # type: ignore[index]
        )
        variants[variant] = row

    wins = {
        "comparable_pairs": len(pairs),
        "managed_gross_return_wins_vs_base": 0,
        "managed_gross_sharpe_wins_vs_base": 0,
        "managed_gross_drawdown_wins_vs_base": 0,
        "managed_net_2bp_return_wins_vs_base": 0,
        "managed_net_2bp_sharpe_wins_vs_base": 0,
        "managed_net_2bp_drawdown_wins_vs_base": 0,
    }
    for pair in pairs.values():
        base = pair["variants"]["stage_lifecycle_base"]  # type: ignore[index]
        managed = pair["variants"]["stage_lifecycle_plus_early_damage"]  # type: ignore[index]
        wins["managed_gross_return_wins_vs_base"] += int(float(managed["gross_ann_return"]) > float(base["gross_ann_return"]))
        wins["managed_gross_sharpe_wins_vs_base"] += int(float(managed["gross_sharpe"]) > float(base["gross_sharpe"]))
        wins["managed_gross_drawdown_wins_vs_base"] += int(float(managed["gross_max_drawdown"]) > float(base["gross_max_drawdown"]))
        wins["managed_net_2bp_return_wins_vs_base"] += int(float(managed["net_2bp_ann_return"]) > float(base["net_2bp_ann_return"]))
        wins["managed_net_2bp_sharpe_wins_vs_base"] += int(float(managed["net_2bp_sharpe"]) > float(base["net_2bp_sharpe"]))
        wins["managed_net_2bp_drawdown_wins_vs_base"] += int(float(managed["net_2bp_max_drawdown"]) > float(base["net_2bp_max_drawdown"]))

    managed_event_keys = next(iter(pairs.values()))["managed_events"].keys() if pairs else []  # type: ignore[index]
    managed_events = {
        key: int(sum(int(pair["managed_events"][key]) for pair in pairs.values()))  # type: ignore[index]
        for key in managed_event_keys
    }
    return {"pair_count": len(pairs), "variants": variants, "wins": wins, "managed_events": managed_events}


def build_report() -> dict[str, object]:
    pairs = {pair: analyze_pair(frame) for pair, frame in load_frozen_pairs().items()}
    return {
        "schema_version": 1,
        "issue": 61,
        "status": "PHASE_B_EARLY_DAMAGE_OVERLAY_REUSED_DATA_DEVELOPMENT_ONLY",
        "execution": "close-observed signal applied with one-bar lag to next close-to-close return",
        "transition_health_engine": "exact Issue #57 archived online state machine",
        "variants": list(VARIANTS),
        "pairs": pairs,
        "aggregate": aggregate_pairs(pairs),
        "boundary": "All samples are reused evidence. Frozen Early-Damaged overlay only; no stop/target/sizing optimization or validation claim.",
    }


def pct(value: float | None) -> str:
    return "—" if value is None else f"{100.0 * value:.2f}%"


def num(value: float | None) -> str:
    return "—" if value is None else f"{value:.3f}"


def render_markdown(report: dict[str, object]) -> str:
    agg = report["aggregate"]  # type: ignore[index]
    lines = [
        "# Issue #61 — Phase B Early-Damaged lifecycle overlay",
        "",
        "**Reused-data development evidence only. Overlay mechanics frozen before PnL.**",
        "",
        "- Base lifecycle is unchanged.",
        "- Exact archived Issue #57 Transition Health engine is used.",
        "- Matching Early Damaged exits and blocks that direction until the same TH watch resolves.",
        "- Resolution does not auto re-enter; a new base lifecycle entry is required.",
        "- Healthy +3 has no entry/re-entry role.",
        "",
        "## Median-pair metrics",
        "",
        "| Variant | Gross ann return | Gross Sharpe | Gross max DD | Net 2bp ann return | Net 2bp Sharpe | Net 2bp max DD | Exposure | Turnover/yr | Entries |",
        "|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for variant in VARIANTS:
        row = agg["variants"][variant]
        lines.append(
            f"| {variant} | {pct(row['median_pair_gross_ann_return'])} | {num(row['median_pair_gross_sharpe'])} | "
            f"{pct(row['median_pair_gross_max_drawdown'])} | {pct(row['median_pair_net_2bp_ann_return'])} | "
            f"{num(row['median_pair_net_2bp_sharpe'])} | {pct(row['median_pair_net_2bp_max_drawdown'])} | "
            f"{pct(row['median_pair_exposure_share'])} | {num(row['median_pair_annualized_turnover'])} | {row['total_signal_entries']} |"
        )

    w = agg["wins"]
    lines += [
        "",
        "## Incremental consistency: Early Damaged vs base lifecycle",
        "",
        f"- Gross return better: **{w['managed_gross_return_wins_vs_base']}/{w['comparable_pairs']}**.",
        f"- Gross Sharpe better: **{w['managed_gross_sharpe_wins_vs_base']}/{w['comparable_pairs']}**.",
        f"- Gross max drawdown better: **{w['managed_gross_drawdown_wins_vs_base']}/{w['comparable_pairs']}**.",
        f"- Net 2bp return better: **{w['managed_net_2bp_return_wins_vs_base']}/{w['comparable_pairs']}**.",
        f"- Net 2bp Sharpe better: **{w['managed_net_2bp_sharpe_wins_vs_base']}/{w['comparable_pairs']}**.",
        f"- Net 2bp max drawdown better: **{w['managed_net_2bp_drawdown_wins_vs_base']}/{w['comparable_pairs']}**.",
        "",
        "## Managed overlay event counts",
        "",
    ]
    for key, value in agg["managed_events"].items():
        lines.append(f"- `{key}`: {value}")

    lines += [
        "",
        "## Per pair",
        "",
        "| Pair | Base return | Managed return | Base Sharpe | Managed Sharpe | Base DD | Managed DD | Base exposure | Managed exposure | Early-damage exits |",
        "|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for pair, result in report["pairs"].items():  # type: ignore[index]
        base = result["variants"]["stage_lifecycle_base"]
        managed = result["variants"]["stage_lifecycle_plus_early_damage"]
        events = result["managed_events"]
        exits = int(events["early_damage_long_exits"]) + int(events["early_damage_short_exits"])
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
