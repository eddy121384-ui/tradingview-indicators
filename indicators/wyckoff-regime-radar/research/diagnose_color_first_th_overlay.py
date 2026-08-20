#!/usr/bin/env python3
"""Issue #57 reused-data strategy proxy: Formal color first, TH as risk overlay."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
import pandas as pd

from diagnose_consensus_formation_and_formal_lag import compute_v06, load_burned_pairs
from evaluate_transition_health_independent_oos import load_frozen_pairs
from transition_health_online import CHECKPOINT, compute_transition_health

ANNUALIZATION = 252.0
COST_PER_UNIT_TURNOVER = 0.0002  # 2 bp, preregistered sensitivity only.
BULL_STAGES = {1, 2, 3}
BEAR_STAGES = {4, 5, 6}
VARIANTS = ("color_only", "color_plus_th_gate")


def formal_color_direction(model: pd.DataFrame) -> np.ndarray:
    ids = pd.to_numeric(model["formal_id"], errors="coerce").fillna(0).to_numpy(int)
    out = np.zeros(len(ids), dtype=int)
    out[np.isin(ids, list(BULL_STAGES))] = 1
    out[np.isin(ids, list(BEAR_STAGES))] = -1
    return out


def early_damage_pulses(th: pd.DataFrame) -> np.ndarray:
    """First observable loss of carried>context during age +1..+3.

    The online state machine keeps `lead_held=False` after the first loss, so the
    true->false transition creates one pulse without adding a new threshold.
    """
    tracked = th["transition_health_tracked"].to_numpy(bool)
    held = th["transition_health_lead_held"].to_numpy(bool)
    age = pd.to_numeric(th["transition_health_watch_age"], errors="coerce").fillna(0).to_numpy(int)
    out = np.zeros(len(th), dtype=bool)
    for i in range(1, len(th)):
        if tracked[i] and 1 <= age[i] <= CHECKPOINT and held[i - 1] and not held[i]:
            out[i] = True
    return out


def managed_color_signal(
    color_direction: np.ndarray,
    th: pd.DataFrame,
) -> tuple[np.ndarray, dict[str, int]]:
    """Apply the frozen Early-Damaged block / later-Healthy re-risk rule."""
    direction = pd.to_numeric(th["transition_health_direction"], errors="coerce").fillna(0).to_numpy(int)
    healthy = th["transition_health_healthy_pulse"].to_numpy(bool)
    early_damage = early_damage_pulses(th)

    out = np.zeros(len(color_direction), dtype=int)
    blocked = False
    blocked_dir = 0
    blocks = 0
    rerisks = 0

    for i, color_dir in enumerate(color_direction.astype(int)):
        prev_color = int(color_direction[i - 1]) if i > 0 else 0
        if i == 0 or color_dir != prev_color:
            blocked = False
            blocked_dir = 0

        if color_dir == 0:
            blocked = False
            blocked_dir = 0

        if early_damage[i] and color_dir != 0 and int(direction[i]) == color_dir:
            if not blocked or blocked_dir != color_dir:
                blocks += 1
            blocked = True
            blocked_dir = color_dir

        if (
            healthy[i]
            and blocked
            and color_dir != 0
            and blocked_dir == color_dir
            and int(direction[i]) == color_dir
        ):
            blocked = False
            blocked_dir = 0
            rerisks += 1

        out[i] = 0 if blocked else color_dir

    return out, {"early_damage_blocks": blocks, "healthy_rerisks": rerisks}


def color_entry_count(color_direction: np.ndarray, score_mask: np.ndarray) -> int:
    count = 0
    for i, value in enumerate(color_direction.astype(int)):
        previous = int(color_direction[i - 1]) if i > 0 else 0
        if score_mask[i] and value != 0 and value != previous:
            count += 1
    return count


def max_drawdown(returns: np.ndarray) -> float | None:
    if returns.size == 0:
        return None
    equity = np.cumprod(1.0 + returns)
    peaks = np.maximum.accumulate(np.concatenate(([1.0], equity)))
    drawdowns = np.concatenate(([1.0], equity)) / peaks - 1.0
    return float(np.min(drawdowns))


def annualized_return(returns: np.ndarray) -> float | None:
    if returns.size == 0:
        return None
    terminal = float(np.prod(1.0 + returns))
    if terminal <= 0.0:
        return -1.0
    return float(terminal ** (ANNUALIZATION / returns.size) - 1.0)


def strategy_metrics(
    frame: pd.DataFrame,
    signal: np.ndarray,
    score_start: str | None = None,
    score_end: str | None = None,
) -> dict[str, float | int | None]:
    """One-bar-lag close-to-close strategy proxy with fixed cost sensitivity."""
    close = pd.to_numeric(frame["close"], errors="coerce").to_numpy(float)
    dates = pd.to_datetime(frame["date"], errors="raise")
    n = len(frame)
    if len(signal) != n:
        raise ValueError("signal length must match frame")

    asset_return = np.zeros(n, dtype=float)
    valid_close = np.isfinite(close[1:]) & np.isfinite(close[:-1]) & (close[:-1] > 0.0)
    asset_return[1:][valid_close] = close[1:][valid_close] / close[:-1][valid_close] - 1.0

    position = np.zeros(n, dtype=float)
    if n > 1:
        position[1:] = signal[:-1]
    turnover = np.zeros(n, dtype=float)
    if n > 1:
        turnover[1:] = np.abs(position[1:] - position[:-1])

    score_mask = np.arange(n) >= 1
    if score_start is not None:
        score_mask &= dates >= pd.Timestamp(score_start)
    if score_end is not None:
        score_mask &= dates <= pd.Timestamp(score_end)
    score_mask &= np.isfinite(asset_return)

    gross_all = position * asset_return
    net_all = gross_all - COST_PER_UNIT_TURNOVER * turnover
    gross = gross_all[score_mask]
    net = net_all[score_mask]
    pos = position[score_mask]
    turn = turnover[score_mask]

    if gross.size == 0:
        return {
            "observations": 0,
            "gross_ann_return": None,
            "gross_ann_vol": None,
            "gross_sharpe": None,
            "gross_max_drawdown": None,
            "net_2bp_ann_return": None,
            "net_2bp_sharpe": None,
            "net_2bp_max_drawdown": None,
            "annualized_turnover": None,
            "exposure_share": None,
        }

    gross_std = float(np.std(gross, ddof=1)) if gross.size > 1 else 0.0
    net_std = float(np.std(net, ddof=1)) if net.size > 1 else 0.0
    years = gross.size / ANNUALIZATION
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
        "exposure_share": float(np.mean(np.abs(pos) > 0.0)),
    }


def pair_analysis(
    frame: pd.DataFrame,
    score_start: str | None,
    score_end: str | None,
) -> dict[str, object]:
    local = frame.copy().reset_index(drop=True)
    local["date"] = pd.to_datetime(local["date"], errors="raise")
    model = compute_v06(local.copy())
    color = formal_color_direction(model)
    th = compute_transition_health(model)
    managed, event_counts = managed_color_signal(color, th)

    dates = pd.to_datetime(local["date"], errors="raise")
    score_signal_mask = np.ones(len(local), dtype=bool)
    if score_start is not None:
        score_signal_mask &= dates >= pd.Timestamp(score_start)
    if score_end is not None:
        score_signal_mask &= dates <= pd.Timestamp(score_end)

    early = early_damage_pulses(th)
    th_dir = pd.to_numeric(th["transition_health_direction"], errors="coerce").fillna(0).to_numpy(int)
    healthy = th["transition_health_healthy_pulse"].to_numpy(bool)
    matched_early = early & (th_dir == color) & (color != 0) & score_signal_mask
    matched_healthy = healthy & (th_dir == color) & (color != 0) & score_signal_mask

    return {
        "rows": len(local),
        "start_date": str(dates.iloc[0].date()),
        "end_date": str(dates.iloc[-1].date()),
        "score_start": score_start,
        "score_end": score_end,
        "color_entries": color_entry_count(color, score_signal_mask),
        "matched_early_damage_events": int(np.sum(matched_early)),
        "matched_healthy_events": int(np.sum(matched_healthy)),
        **event_counts,
        "variants": {
            "color_only": strategy_metrics(local, color, score_start, score_end),
            "color_plus_th_gate": strategy_metrics(local, managed, score_start, score_end),
        },
    }


def _median(values: list[float]) -> float | None:
    return float(np.median(values)) if values else None


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
        "exposure_share",
    )
    variants: dict[str, object] = {}
    for variant in VARIANTS:
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
        "comparable_pairs": 0,
        "managed_gross_return_wins": 0,
        "managed_gross_sharpe_wins": 0,
        "managed_gross_drawdown_wins": 0,
        "managed_net_2bp_return_wins": 0,
        "managed_net_2bp_sharpe_wins": 0,
        "managed_net_2bp_drawdown_wins": 0,
    }
    for pair in pairs.values():
        base = pair["variants"]["color_only"]  # type: ignore[index]
        managed = pair["variants"]["color_plus_th_gate"]  # type: ignore[index]
        required = (
            base["gross_ann_return"], managed["gross_ann_return"],
            base["gross_sharpe"], managed["gross_sharpe"],
            base["gross_max_drawdown"], managed["gross_max_drawdown"],
        )
        if any(v is None for v in required):
            continue
        wins["comparable_pairs"] += 1
        wins["managed_gross_return_wins"] += int(float(managed["gross_ann_return"]) > float(base["gross_ann_return"]))
        wins["managed_gross_sharpe_wins"] += int(float(managed["gross_sharpe"]) > float(base["gross_sharpe"]))
        wins["managed_gross_drawdown_wins"] += int(float(managed["gross_max_drawdown"]) > float(base["gross_max_drawdown"]))
        if base["net_2bp_ann_return"] is not None and managed["net_2bp_ann_return"] is not None:
            wins["managed_net_2bp_return_wins"] += int(float(managed["net_2bp_ann_return"]) > float(base["net_2bp_ann_return"]))
        if base["net_2bp_sharpe"] is not None and managed["net_2bp_sharpe"] is not None:
            wins["managed_net_2bp_sharpe_wins"] += int(float(managed["net_2bp_sharpe"]) > float(base["net_2bp_sharpe"]))
        if base["net_2bp_max_drawdown"] is not None and managed["net_2bp_max_drawdown"] is not None:
            wins["managed_net_2bp_drawdown_wins"] += int(float(managed["net_2bp_max_drawdown"]) > float(base["net_2bp_max_drawdown"]))

    return {
        "pair_count": len(pairs),
        "color_entries": int(sum(int(pair["color_entries"]) for pair in pairs.values())),
        "early_damage_blocks": int(sum(int(pair["early_damage_blocks"]) for pair in pairs.values())),
        "healthy_rerisks": int(sum(int(pair["healthy_rerisks"]) for pair in pairs.values())),
        "variants": variants,
        "wins": wins,
    }


def build_report() -> dict[str, object]:
    development_frames = load_burned_pairs()
    _, later_frames = load_frozen_pairs()

    development = {
        pair: pair_analysis(frame, None, None)
        for pair, frame in development_frames.items()
    }
    later_reused = {
        pair: pair_analysis(frame, "2022-01-01", "2026-08-13")
        for pair, frame in later_frames.items()
    }
    combined = {**development, **later_reused}

    return {
        "schema_version": 1,
        "issue": 57,
        "status": "REUSED_DATA_COLOR_FIRST_TH_OVERLAY_DIAGNOSTIC_ONLY",
        "formal_color_mapping": {"bull": [1, 2, 3], "bear": [4, 5, 6], "flat": [0]},
        "execution": "bar-close signal, applied to next bar close-to-close return",
        "cost_sensitivity_per_unit_turnover": COST_PER_UNIT_TURNOVER,
        "cohorts": {
            "development_7fx": {
                "pairs": development,
                "aggregate": aggregate_pairs(development),
            },
            "later_reused_5fx_2022_2026": {
                "pairs": later_reused,
                "aggregate": aggregate_pairs(later_reused),
            },
            "combined_12fx": {
                "pairs": combined,
                "aggregate": aggregate_pairs(combined),
            },
        },
        "boundary": "All observations are reused for this new overlay hypothesis. This is not independent OOS validation and does not justify production trading rules.",
    }


def pct(value: float | None) -> str:
    return "—" if value is None else f"{100.0 * value:.2f}%"


def num(value: float | None) -> str:
    return "—" if value is None else f"{value:.3f}"


def render_markdown(report: dict[str, object]) -> str:
    lines = [
        "# Issue #57 — Color-first regime + Transition Health risk overlay",
        "",
        "**Reused-data strategy-proxy diagnostic only. No production rule change.**",
        "",
        "- Formal color: stages 1/2/3 = bull, 4/5/6 = bear, 0 = flat.",
        "- Color is acted on immediately in signal time; position applies one bar later.",
        "- Early Damaged blocks the matching color direction; later matching Healthy re-risks.",
        "- Healthy does not delay an unblocked color entry.",
        "- Fixed cost sensitivity: 2 bp per unit absolute position change.",
        "",
    ]

    for cohort_name in ("development_7fx", "later_reused_5fx_2022_2026", "combined_12fx"):
        cohort = report["cohorts"][cohort_name]  # type: ignore[index]
        agg = cohort["aggregate"]
        lines += [
            f"## {cohort_name}",
            "",
            f"Pairs: **{agg['pair_count']}** | Color entries: **{agg['color_entries']}** | Early-Damaged blocks: **{agg['early_damage_blocks']}** | Healthy re-risks: **{agg['healthy_rerisks']}**",
            "",
            "| Variant | Gross ann ret | Gross Sharpe | Gross max DD | Net 2bp ann ret | Net 2bp Sharpe | Net 2bp max DD | Ann turnover | Exposure |",
            "|---|---:|---:|---:|---:|---:|---:|---:|---:|",
        ]
        for variant in VARIANTS:
            row = agg["variants"][variant]
            lines.append(
                f"| {variant} | {pct(row['median_pair_gross_ann_return'])} | {num(row['median_pair_gross_sharpe'])} | "
                f"{pct(row['median_pair_gross_max_drawdown'])} | {pct(row['median_pair_net_2bp_ann_return'])} | "
                f"{num(row['median_pair_net_2bp_sharpe'])} | {pct(row['median_pair_net_2bp_max_drawdown'])} | "
                f"{num(row['median_pair_annualized_turnover'])} | {pct(row['median_pair_exposure_share'])} |"
            )
        wins = agg["wins"]
        lines += [
            "",
            f"Managed wins (gross) — return **{wins['managed_gross_return_wins']}/{wins['comparable_pairs']}**, "
            f"Sharpe **{wins['managed_gross_sharpe_wins']}/{wins['comparable_pairs']}**, "
            f"drawdown **{wins['managed_gross_drawdown_wins']}/{wins['comparable_pairs']}**.",
            f"Managed wins (2bp) — return **{wins['managed_net_2bp_return_wins']}/{wins['comparable_pairs']}**, "
            f"Sharpe **{wins['managed_net_2bp_sharpe_wins']}/{wins['comparable_pairs']}**, "
            f"drawdown **{wins['managed_net_2bp_drawdown_wins']}/{wins['comparable_pairs']}**.",
            "",
        ]

    lines += [
        "## Per-pair gross comparison",
        "",
        "| Cohort | Pair | Color ret | Managed ret | Color Sharpe | Managed Sharpe | Color DD | Managed DD | Blocks | Re-risks |",
        "|---|---|---:|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for cohort_name in ("development_7fx", "later_reused_5fx_2022_2026"):
        for pair, result in report["cohorts"][cohort_name]["pairs"].items():  # type: ignore[index]
            base = result["variants"]["color_only"]
            managed = result["variants"]["color_plus_th_gate"]
            lines.append(
                f"| {cohort_name} | {pair} | {pct(base['gross_ann_return'])} | {pct(managed['gross_ann_return'])} | "
                f"{num(base['gross_sharpe'])} | {num(managed['gross_sharpe'])} | {pct(base['gross_max_drawdown'])} | "
                f"{pct(managed['gross_max_drawdown'])} | {result['early_damage_blocks']} | {result['healthy_rerisks']} |"
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
    args.md_output.parent.mkdir(parents=True, exist_ok=True)
    args.json_output.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    args.md_output.write_text(render_markdown(report), encoding="utf-8")
    print(json.dumps({name: cohort["aggregate"] for name, cohort in report["cohorts"].items()}, indent=2))


if __name__ == "__main__":
    main()
