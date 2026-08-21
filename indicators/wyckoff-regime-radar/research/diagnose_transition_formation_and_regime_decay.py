#!/usr/bin/env python3
"""Issue #57 burned-data behavior map: transition formation and regime decay.

Purpose
-------
Describe how the existing v0.6 price-only indicator behaves on the seven already-
observed FX fixtures. This is NOT an optimization pass and NOT independent OOS.
No production threshold is selected from this diagnostic.

Two questions are separated deliberately:
1. Formation: when an actionable Top-2 family first forms, do faster weight
   concentration and faster Top-2 strengthening correspond to a more durable
   regime or better direction-aligned price behavior?
2. Decay: once an actionable regime is already alive, do simple deterioration
   signs (Top-2 weakening, entropy rising, opposite structural pressure rising)
   appear before the actionable episode ends?
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
import pandas as pd

from diagnose_consensus_formation_and_formal_lag import (
    compute_v06,
    consensus_components,
    load_burned_pairs,
)
from diagnose_v06_top2_directional_consensus import WEIGHT_COLUMNS


HERE = Path(__file__).resolve().parent
FORMATION_LOOKBACK = 3
HEALTH_LOOKBACK = 3
SURVIVAL_HORIZONS = (5, 10, 20)
RETURN_HORIZONS = (5, 10, 20)


def median_or_none(values: list[float]) -> float | None:
    return float(np.median(values)) if values else None


def mean_or_none(values: list[float]) -> float | None:
    return float(np.mean(values)) if values else None


def spearman_or_none(x: list[float], y: list[float]) -> float | None:
    if len(x) < 3 or len(y) != len(x):
        return None
    xs = pd.Series(x, dtype=float).rank(method="average")
    ys = pd.Series(y, dtype=float).rank(method="average")
    value = xs.corr(ys, method="pearson")
    return None if pd.isna(value) else float(value)


def weight_matrix(model: pd.DataFrame) -> np.ndarray:
    return model.loc[:, WEIGHT_COLUMNS].apply(pd.to_numeric, errors="coerce").to_numpy(float)


def normalized_entropy(model: pd.DataFrame) -> np.ndarray:
    """0 = one stage owns all weight; 1 = six stages are evenly distributed."""
    raw = weight_matrix(model)
    safe = np.where(np.isfinite(raw), np.maximum(raw, 0.0), 0.0)
    totals = safe.sum(axis=1, keepdims=True)
    probs = np.divide(safe, totals, out=np.zeros_like(safe), where=totals > 0.0)
    terms = np.where(probs > 0.0, probs * np.log(probs), 0.0)
    entropy = -terms.sum(axis=1) / np.log(float(len(WEIGHT_COLUMNS)))
    entropy[totals[:, 0] <= 0.0] = np.nan
    return entropy


def opposite_structural_pressure(model: pd.DataFrame, direction: np.ndarray) -> np.ndarray:
    """Opposite half of the six-stage structure, not just the opposite action pair.

    Bullish actionable regime (2+3): warning pressure = stages 4+5+6.
    Bearish actionable regime (5+6): warning pressure = stages 1+2+3.
    """
    w = weight_matrix(model)
    bullish_half = np.nansum(w[:, 0:3], axis=1)
    bearish_half = np.nansum(w[:, 3:6], axis=1)
    out = np.full(len(model), np.nan, dtype=float)
    out[direction > 0.0] = bearish_half[direction > 0.0]
    out[direction < 0.0] = bullish_half[direction < 0.0]
    return out


def extract_action_episodes(direction: np.ndarray) -> list[dict[str, int | float]]:
    episodes: list[dict[str, int | float]] = []
    start: int | None = None
    current = 0.0
    for i, value in enumerate(direction.astype(float)):
        if value != 0.0 and value == current:
            continue
        if current != 0.0 and start is not None:
            end = i - 1
            episodes.append({"start": start, "end": end, "direction": current, "duration": end - start + 1})
        if value != 0.0:
            start = i
            current = value
        else:
            start = None
            current = 0.0
    if current != 0.0 and start is not None:
        end = len(direction) - 1
        episodes.append({"start": start, "end": end, "direction": current, "duration": end - start + 1})
    return episodes


def aligned_return(frame: pd.DataFrame, index: int, direction: float, horizon: int) -> float | None:
    if index + horizon >= len(frame):
        return None
    close = pd.to_numeric(frame["close"], errors="coerce").to_numpy(float)
    base = close[index]
    future = close[index + horizon]
    if not np.isfinite(base) or base <= 0.0 or not np.isfinite(future):
        return None
    return float(direction * (future / base - 1.0))


def adverse_excursion(frame: pd.DataFrame, index: int, direction: float, horizon: int) -> float | None:
    if index + horizon >= len(frame):
        return None
    close = pd.to_numeric(frame["close"], errors="coerce").to_numpy(float)
    high = pd.to_numeric(frame["high"], errors="coerce").to_numpy(float)
    low = pd.to_numeric(frame["low"], errors="coerce").to_numpy(float)
    base = close[index]
    if not np.isfinite(base) or base <= 0.0:
        return None
    if direction > 0.0:
        worst = float(np.nanmin(low[index + 1 : index + horizon + 1]))
        return float(max(0.0, 1.0 - worst / base))
    worst = float(np.nanmax(high[index + 1 : index + horizon + 1]))
    return float(max(0.0, worst / base - 1.0))


def formation_events(frame: pd.DataFrame, model: pd.DataFrame) -> list[dict[str, object]]:
    direction, strength, _, _ = consensus_components(model)
    entropy = normalized_entropy(model)
    episodes = extract_action_episodes(direction)
    rows: list[dict[str, object]] = []
    for episode in episodes:
        start = int(episode["start"])
        if start < FORMATION_LOOKBACK:
            continue
        speed = float(strength[start] - strength[start - FORMATION_LOOKBACK])
        entropy_drop = float(entropy[start - FORMATION_LOOKBACK] - entropy[start])
        if not np.isfinite(speed) or not np.isfinite(entropy_drop):
            continue
        duration = int(episode["duration"])
        row: dict[str, object] = {
            "start": start,
            "direction": float(episode["direction"]),
            "duration": duration,
            "strength": float(strength[start]),
            "strength_change_3": speed,
            "entropy_drop_3": entropy_drop,
            "fast_and_concentrating": bool(speed > 0.0 and entropy_drop > 0.0),
        }
        for horizon in SURVIVAL_HORIZONS:
            row[f"survives_{horizon}"] = bool(duration >= horizon)
        for horizon in RETURN_HORIZONS:
            row[f"aligned_return_{horizon}"] = aligned_return(
                frame, start, float(episode["direction"]), horizon
            )
        rows.append(row)
    return rows


def summarize_formation(rows: list[dict[str, object]]) -> dict[str, object]:
    durations = [float(row["duration"]) for row in rows]
    speeds = [float(row["strength_change_3"]) for row in rows]
    entropy_drops = [float(row["entropy_drop_3"]) for row in rows]

    def corr_with(field: str, values: list[float]) -> float | None:
        x: list[float] = []
        y: list[float] = []
        for row, xv in zip(rows, values):
            target = row.get(field)
            if target is not None and np.isfinite(float(target)):
                x.append(float(xv))
                y.append(float(target))
        return spearman_or_none(x, y)

    groups: dict[str, object] = {}
    for name, selector in (
        ("fast_and_concentrating", lambda r: bool(r["fast_and_concentrating"])),
        ("other_formations", lambda r: not bool(r["fast_and_concentrating"])),
    ):
        selected = [row for row in rows if selector(row)]
        group: dict[str, object] = {
            "events": len(selected),
            "median_duration": median_or_none([float(row["duration"]) for row in selected]),
        }
        for horizon in SURVIVAL_HORIZONS:
            group[f"survival_rate_{horizon}"] = (
                float(np.mean([bool(row[f"survives_{horizon}"]) for row in selected])) if selected else None
            )
        for horizon in RETURN_HORIZONS:
            values = [
                float(row[f"aligned_return_{horizon}"])
                for row in selected
                if row[f"aligned_return_{horizon}"] is not None
            ]
            group[f"mean_aligned_return_{horizon}"] = mean_or_none(values)
        groups[name] = group

    return {
        "events": len(rows),
        "median_duration": median_or_none(durations),
        "rho_strength_change_vs_duration": spearman_or_none(speeds, durations),
        "rho_entropy_drop_vs_duration": spearman_or_none(entropy_drops, durations),
        "rho_strength_change_vs_return_10": corr_with("aligned_return_10", speeds),
        "rho_entropy_drop_vs_return_10": corr_with("aligned_return_10", entropy_drops),
        "groups": groups,
    }


def health_rows(frame: pd.DataFrame, model: pd.DataFrame) -> list[dict[str, object]]:
    direction, strength, _, _ = consensus_components(model)
    entropy = normalized_entropy(model)
    opposite = opposite_structural_pressure(model, direction)
    episodes = extract_action_episodes(direction)
    rows: list[dict[str, object]] = []
    for episode_index, episode in enumerate(episodes):
        start = int(episode["start"])
        end = int(episode["end"])
        d = float(episode["direction"])
        for i in range(start + HEALTH_LOOKBACK, end + 1):
            strength_change = float(strength[i] - strength[i - HEALTH_LOOKBACK])
            entropy_change = float(entropy[i] - entropy[i - HEALTH_LOOKBACK])
            opposite_change = float(opposite[i] - opposite[i - HEALTH_LOOKBACK])
            if not all(np.isfinite(v) for v in (strength_change, entropy_change, opposite_change)):
                continue
            weakening = strength_change < 0.0
            dispersing = entropy_change > 0.0
            opposition_rising = opposite_change > 0.0
            warnings = int(weakening) + int(dispersing) + int(opposition_rising)
            remaining = end - i
            rows.append(
                {
                    "episode": episode_index,
                    "index": i,
                    "direction": d,
                    "warning_count": warnings,
                    "strength_change_3": strength_change,
                    "entropy_change_3": entropy_change,
                    "opposite_pressure_change_3": opposite_change,
                    "ends_within_5": bool(remaining <= 5),
                    "ends_within_10": bool(remaining <= 10),
                    "remaining_bars": remaining,
                    "aligned_return_5": aligned_return(frame, i, d, 5),
                    "adverse_excursion_5": adverse_excursion(frame, i, d, 5),
                }
            )
    return rows


def summarize_health(rows: list[dict[str, object]]) -> dict[str, object]:
    bins: dict[str, object] = {}
    for warnings in range(4):
        selected = [row for row in rows if int(row["warning_count"]) == warnings]
        bins[str(warnings)] = {
            "observations": len(selected),
            "end_within_5_rate": float(np.mean([bool(row["ends_within_5"]) for row in selected])) if selected else None,
            "end_within_10_rate": float(np.mean([bool(row["ends_within_10"]) for row in selected])) if selected else None,
            "median_remaining_bars": median_or_none([float(row["remaining_bars"]) for row in selected]),
            "mean_aligned_return_5": mean_or_none([
                float(row["aligned_return_5"]) for row in selected if row["aligned_return_5"] is not None
            ]),
            "mean_adverse_excursion_5": mean_or_none([
                float(row["adverse_excursion_5"]) for row in selected if row["adverse_excursion_5"] is not None
            ]),
        }

    first_two_plus: list[dict[str, object]] = []
    by_episode: dict[int, list[dict[str, object]]] = {}
    for row in rows:
        by_episode.setdefault(int(row["episode"]), []).append(row)
    for episode_rows in by_episode.values():
        for row in sorted(episode_rows, key=lambda item: int(item["index"])):
            if int(row["warning_count"]) >= 2:
                first_two_plus.append(row)
                break
    first_summary = {
        "events": len(first_two_plus),
        "end_within_5_rate": float(np.mean([bool(row["ends_within_5"]) for row in first_two_plus])) if first_two_plus else None,
        "end_within_10_rate": float(np.mean([bool(row["ends_within_10"]) for row in first_two_plus])) if first_two_plus else None,
        "median_remaining_bars": median_or_none([float(row["remaining_bars"]) for row in first_two_plus]),
        "mean_aligned_return_5": mean_or_none([
            float(row["aligned_return_5"]) for row in first_two_plus if row["aligned_return_5"] is not None
        ]),
        "mean_adverse_excursion_5": mean_or_none([
            float(row["adverse_excursion_5"]) for row in first_two_plus if row["adverse_excursion_5"] is not None
        ]),
    }
    return {"warning_bins": bins, "first_two_plus_warning": first_summary}


def analyze_pair(pair: str, frame: pd.DataFrame) -> dict[str, object]:
    model = compute_v06(frame.copy())
    formation = formation_events(frame, model)
    health = health_rows(frame, model)
    return {
        "rows": len(frame),
        "start_date": str(frame["date"].iloc[0]),
        "end_date": str(frame["date"].iloc[-1]),
        "formation": summarize_formation(formation),
        "health": summarize_health(health),
    }


def aggregate_pairs(pairs: dict[str, dict[str, object]]) -> dict[str, object]:
    formation: dict[str, object] = {
        "total_events": int(sum(int(result["formation"]["events"]) for result in pairs.values())),  # type: ignore[index]
        "median_pair_median_duration": median_or_none([
            float(result["formation"]["median_duration"])
            for result in pairs.values()
            if result["formation"]["median_duration"] is not None  # type: ignore[index]
        ]),
    }
    for key in (
        "rho_strength_change_vs_duration",
        "rho_entropy_drop_vs_duration",
        "rho_strength_change_vs_return_10",
        "rho_entropy_drop_vs_return_10",
    ):
        values = [
            float(result["formation"][key])
            for result in pairs.values()
            if result["formation"][key] is not None  # type: ignore[index]
        ]
        formation[f"median_pair_{key}"] = median_or_none(values)

    formation_groups: dict[str, object] = {}
    for group_name in ("fast_and_concentrating", "other_formations"):
        rows = [result["formation"]["groups"][group_name] for result in pairs.values()]  # type: ignore[index]
        out: dict[str, object] = {"total_events": int(sum(int(row["events"]) for row in rows))}
        for metric in (
            "median_duration",
            "survival_rate_5",
            "survival_rate_10",
            "survival_rate_20",
            "mean_aligned_return_5",
            "mean_aligned_return_10",
            "mean_aligned_return_20",
        ):
            values = [float(row[metric]) for row in rows if row[metric] is not None]
            out[f"median_pair_{metric}"] = median_or_none(values)
        formation_groups[group_name] = out
    formation["groups"] = formation_groups

    health_bins: dict[str, object] = {}
    for warnings in range(4):
        rows = [result["health"]["warning_bins"][str(warnings)] for result in pairs.values()]  # type: ignore[index]
        out: dict[str, object] = {"total_observations": int(sum(int(row["observations"]) for row in rows))}
        for metric in (
            "end_within_5_rate",
            "end_within_10_rate",
            "median_remaining_bars",
            "mean_aligned_return_5",
            "mean_adverse_excursion_5",
        ):
            values = [float(row[metric]) for row in rows if row[metric] is not None]
            out[f"median_pair_{metric}"] = median_or_none(values)
        health_bins[str(warnings)] = out

    first_rows = [result["health"]["first_two_plus_warning"] for result in pairs.values()]  # type: ignore[index]
    first_two: dict[str, object] = {"total_events": int(sum(int(row["events"]) for row in first_rows))}
    for metric in (
        "end_within_5_rate",
        "end_within_10_rate",
        "median_remaining_bars",
        "mean_aligned_return_5",
        "mean_adverse_excursion_5",
    ):
        values = [float(row[metric]) for row in first_rows if row[metric] is not None]
        first_two[f"median_pair_{metric}"] = median_or_none(values)

    return {
        "formation": formation,
        "health": {"warning_bins": health_bins, "first_two_plus_warning": first_two},
    }


def build_report() -> dict[str, object]:
    pairs = {pair: analyze_pair(pair, frame) for pair, frame in load_burned_pairs().items()}
    return {
        "schema_version": 1,
        "issue": 57,
        "status": "BURNED_DATA_BEHAVIOR_MAP_ONLY",
        "engine": "current Issue #57 v0.6 price-only core",
        "formation_lookback_bars": FORMATION_LOOKBACK,
        "health_lookback_bars": HEALTH_LOOKBACK,
        "formation_definition": "first bar of a consecutive actionable Top-2 episode: 2+3 bullish or 5+6 bearish",
        "fast_and_concentrating_definition": "Top-2 strength increased over prior 3 bars AND normalized six-weight entropy fell over prior 3 bars",
        "health_warning_definitions": {
            "top2_weakening": "Top-2 strength is lower than 3 bars earlier",
            "distribution_dispersing": "normalized six-weight entropy is higher than 3 bars earlier",
            "opposite_structural_pressure_rising": "opposite three-stage half (4+5+6 for bull, 1+2+3 for bear) is higher than 3 bars earlier",
        },
        "pairs": pairs,
        "aggregate": aggregate_pairs(pairs),
        "boundary": "Existing burned fixtures are intentionally reused to understand indicator behavior. No threshold is optimized and no independent OOS claim is made.",
    }


def pct(value: float | None) -> str:
    return "—" if value is None else f"{100.0 * value:.2f}%"


def num(value: float | None, digits: int = 3) -> str:
    return "—" if value is None else f"{value:.{digits}f}"


def render_markdown(report: dict[str, object]) -> str:
    agg = report["aggregate"]  # type: ignore[index]
    f = agg["formation"]
    h = agg["health"]
    lines = [
        "# Issue #57 — Transition formation and regime decay behavior map",
        "",
        "**Burned-data behavior study only. Existing v0.6 is not modified. No independent OOS claim.**",
        "",
        "## Formation — does a sudden consensus build matter?",
        "",
        f"Total actionable episode onsets: **{f['total_events']}**",
        f"Median of pair-level median episode duration: **{num(f['median_pair_median_duration'], 1)} bars**",
        "",
        "Continuous pair-median relationships:",
        "",
        "| Formation measurement | Spearman rho |",
        "|---|---:|",
        f"| 3-bar Top2 strength change vs episode duration | {num(f['median_pair_rho_strength_change_vs_duration'])} |",
        f"| 3-bar entropy drop vs episode duration | {num(f['median_pair_rho_entropy_drop_vs_duration'])} |",
        f"| 3-bar Top2 strength change vs 10-bar aligned return | {num(f['median_pair_rho_strength_change_vs_return_10'])} |",
        f"| 3-bar entropy drop vs 10-bar aligned return | {num(f['median_pair_rho_entropy_drop_vs_return_10'])} |",
        "",
        "Sign-only descriptive split (not a production threshold):",
        "",
        "| Group | Events | Median duration | Survive 5 | Survive 10 | Survive 20 | 10-bar aligned return | 20-bar aligned return |",
        "|---|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for name, label in (("fast_and_concentrating", "Strength up + entropy down"), ("other_formations", "Other formations")):
        row = f["groups"][name]
        lines.append(
            f"| {label} | {row['total_events']} | {num(row['median_pair_median_duration'], 1)} | "
            f"{pct(row['median_pair_survival_rate_5'])} | {pct(row['median_pair_survival_rate_10'])} | "
            f"{pct(row['median_pair_survival_rate_20'])} | {pct(row['median_pair_mean_aligned_return_10'])} | "
            f"{pct(row['median_pair_mean_aligned_return_20'])} |"
        )

    lines.extend([
        "",
        "## Regime health — do deterioration warnings appear before the episode ends?",
        "",
        "Each established-regime bar gets 0–3 warnings: Top2 weakening, entropy rising, opposite structural pressure rising.",
        "",
        "| Warning count | Observations | End <=5 bars | End <=10 bars | Median remaining bars | 5-bar aligned return | 5-bar adverse excursion |",
        "|---:|---:|---:|---:|---:|---:|---:|",
    ])
    for warnings in range(4):
        row = h["warning_bins"][str(warnings)]
        lines.append(
            f"| {warnings} | {row['total_observations']} | {pct(row['median_pair_end_within_5_rate'])} | "
            f"{pct(row['median_pair_end_within_10_rate'])} | {num(row['median_pair_median_remaining_bars'], 1)} | "
            f"{pct(row['median_pair_mean_aligned_return_5'])} | {pct(row['median_pair_mean_adverse_excursion_5'])} |"
        )
    first = h["first_two_plus_warning"]
    lines.extend([
        "",
        "Episode-level first occurrence of **2+ simultaneous warnings**:",
        "",
        f"- Events: {first['total_events']}",
        f"- End within 5 bars (pair-median): {pct(first['median_pair_end_within_5_rate'])}",
        f"- End within 10 bars (pair-median): {pct(first['median_pair_end_within_10_rate'])}",
        f"- Median remaining bars (pair-median): {num(first['median_pair_median_remaining_bars'], 1)}",
        f"- 5-bar aligned return (pair-median): {pct(first['median_pair_mean_aligned_return_5'])}",
        f"- 5-bar adverse excursion (pair-median): {pct(first['median_pair_mean_adverse_excursion_5'])}",
        "",
        "## Interpretation boundary",
        "",
        "This report maps behavior. It does not pick an optimal lookback, warning threshold, or trading rule. Any later production change must be a separate decision after the behavior is understood.",
        "",
    ])
    return "\n".join(lines)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--json-output", type=Path, required=True)
    parser.add_argument("--md-output", type=Path, required=True)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    report = build_report()
    args.json_output.parent.mkdir(parents=True, exist_ok=True)
    args.md_output.parent.mkdir(parents=True, exist_ok=True)
    args.json_output.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    args.md_output.write_text(render_markdown(report), encoding="utf-8")
    print(json.dumps(report["aggregate"], indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
