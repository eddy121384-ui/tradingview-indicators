#!/usr/bin/env python3
"""Issue #57 burned-data behavior map for early bridge-state formation.

Definitions are frozen in:
  decisions/issue-57-bridge-formation-behavior-map.md

This is descriptive research on already-observed FX fixtures. It does not tune or
change the production indicator and it is not independent OOS validation.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
import pandas as pd

from diagnose_consensus_formation_and_formal_lag import (
    action_pair_direction,
    compute_v06,
    formal_action_direction,
    load_burned_pairs,
)
from diagnose_transition_formation_and_regime_decay import (
    adverse_excursion,
    aligned_return,
    normalized_entropy,
    weight_matrix,
)
from diagnose_v06_top2_directional_consensus import top_ids_and_values


HERE = Path(__file__).resolve().parent
MAX_WATCH_BARS = 20
HORIZONS = (5, 10, 20)
PRIMARY_GROUP_HORIZON = 10
CHANGE_LOOKBACK = 3


def median_or_none(values: list[float]) -> float | None:
    return float(np.median(values)) if values else None


def mean_or_none(values: list[float]) -> float | None:
    return float(np.mean(values)) if values else None


def bridge_direction(top1: np.ndarray, top2: np.ndarray) -> np.ndarray:
    """+1 for 1+2/1+3, -1 for 4+5/4+6, otherwise 0."""
    out = np.zeros(len(top1), dtype=float)
    bull = (
        ((top1 == 1) & np.isin(top2, [2, 3]))
        | ((top2 == 1) & np.isin(top1, [2, 3]))
    )
    bear = (
        ((top1 == 4) & np.isin(top2, [5, 6]))
        | ((top2 == 4) & np.isin(top1, [5, 6]))
    )
    out[bull] = 1.0
    out[bear] = -1.0
    return out


def favorable_excursion(frame: pd.DataFrame, index: int, direction: float, horizon: int) -> float | None:
    if index + horizon >= len(frame):
        return None
    close = pd.to_numeric(frame["close"], errors="coerce").to_numpy(float)
    high = pd.to_numeric(frame["high"], errors="coerce").to_numpy(float)
    low = pd.to_numeric(frame["low"], errors="coerce").to_numpy(float)
    base = close[index]
    if not np.isfinite(base) or base <= 0.0:
        return None
    if direction > 0.0:
        best = float(np.nanmax(high[index + 1 : index + horizon + 1]))
        return float(max(0.0, best / base - 1.0))
    best = float(np.nanmin(low[index + 1 : index + horizon + 1]))
    return float(max(0.0, 1.0 - best / base))


def extract_bridge_watches(bridge: np.ndarray, actionable: np.ndarray) -> list[dict[str, object]]:
    """Non-overlapping bridge watches, resolved by same/opposite actionable or timeout.

    Tail onsets without a full 20-bar observation window are excluded.
    """
    rows: list[dict[str, object]] = []
    i = 0
    n = len(bridge)
    while i < n:
        d = float(bridge[i])
        if d == 0.0:
            i += 1
            continue
        if i + MAX_WATCH_BARS >= n:
            break

        success_lag: int | None = None
        opposite_lag: int | None = None
        resolution_index = i + MAX_WATCH_BARS
        resolution = "timeout"
        for lag in range(1, MAX_WATCH_BARS + 1):
            value = float(actionable[i + lag])
            if value == d:
                success_lag = lag
                resolution_index = i + lag
                resolution = "same_direction_actionable"
                break
            if value == -d:
                opposite_lag = lag
                resolution_index = i + lag
                resolution = "opposite_actionable"
                break

        rows.append(
            {
                "onset": i,
                "direction": d,
                "resolution": resolution,
                "resolution_lag": resolution_index - i,
                "success_lag": success_lag,
                "opposite_lag": opposite_lag,
                "success_within_5": success_lag is not None and success_lag <= 5,
                "success_within_10": success_lag is not None and success_lag <= 10,
                "success_within_20": success_lag is not None and success_lag <= 20,
            }
        )
        i = resolution_index + 1
    return rows


def formal_category(formal: float, direction: float) -> str:
    if formal == direction:
        return "aligned"
    if formal == -direction:
        return "opposite"
    return "neutral_transition"


def enrich_watch_rows(frame: pd.DataFrame, model: pd.DataFrame) -> list[dict[str, object]]:
    top1, top2, val1, val2 = top_ids_and_values(model)
    bridge = bridge_direction(top1, top2)
    actionable = action_pair_direction(top1, top2)
    watches = extract_bridge_watches(bridge, actionable)
    w = weight_matrix(model)
    entropy = normalized_entropy(model)
    formal = formal_action_direction(model)
    strength = val1 + val2

    rows: list[dict[str, object]] = []
    for watch in watches:
        i = int(watch["onset"])
        d = float(watch["direction"])
        if d > 0.0:
            context_weight = float(w[i, 0])
            target_family_weight = float(w[i, 1] + w[i, 2])
            same_side_pressure = float(np.nansum(w[i, 0:3]))
            opposite_pressure = float(np.nansum(w[i, 3:6]))
        else:
            context_weight = float(w[i, 3])
            target_family_weight = float(w[i, 4] + w[i, 5])
            same_side_pressure = float(np.nansum(w[i, 3:6]))
            opposite_pressure = float(np.nansum(w[i, 0:3]))

        row = dict(watch)
        row.update(
            {
                "top2_strength": float(strength[i]),
                "entropy": float(entropy[i]),
                "context_weight": context_weight,
                "target_family_weight": target_family_weight,
                "same_side_pressure": same_side_pressure,
                "opposite_pressure": opposite_pressure,
                "formal_category": formal_category(float(formal[i]), d),
                "aligned_return_5": aligned_return(frame, i, d, 5),
                "aligned_return_10": aligned_return(frame, i, d, 10),
                "aligned_return_20": aligned_return(frame, i, d, 20),
                "mfe_10": favorable_excursion(frame, i, d, 10),
                "mae_10": adverse_excursion(frame, i, d, 10),
            }
        )
        if i >= CHANGE_LOOKBACK:
            j = i - CHANGE_LOOKBACK
            if d > 0.0:
                prior_same = float(np.nansum(w[j, 0:3]))
                prior_opp = float(np.nansum(w[j, 3:6]))
            else:
                prior_same = float(np.nansum(w[j, 3:6]))
                prior_opp = float(np.nansum(w[j, 0:3]))
            row.update(
                {
                    "top2_strength_change_3": float(strength[i] - strength[j]),
                    "entropy_change_3": float(entropy[i] - entropy[j]),
                    "same_side_pressure_change_3": same_side_pressure - prior_same,
                    "opposite_pressure_change_3": opposite_pressure - prior_opp,
                }
            )
        else:
            row.update(
                {
                    "top2_strength_change_3": None,
                    "entropy_change_3": None,
                    "same_side_pressure_change_3": None,
                    "opposite_pressure_change_3": None,
                }
            )
        rows.append(row)
    return rows


def summarize_group(rows: list[dict[str, object]]) -> dict[str, object]:
    out: dict[str, object] = {"events": len(rows)}
    metric_names = (
        "top2_strength",
        "entropy",
        "context_weight",
        "target_family_weight",
        "same_side_pressure",
        "opposite_pressure",
        "top2_strength_change_3",
        "entropy_change_3",
        "same_side_pressure_change_3",
        "opposite_pressure_change_3",
    )
    for name in metric_names:
        vals = [float(r[name]) for r in rows if r.get(name) is not None and np.isfinite(float(r[name]))]
        out[f"median_{name}"] = median_or_none(vals)
    for horizon in HORIZONS:
        vals = [
            float(r[f"aligned_return_{horizon}"])
            for r in rows
            if r.get(f"aligned_return_{horizon}") is not None
        ]
        out[f"mean_aligned_return_{horizon}"] = mean_or_none(vals)
    out["mean_mfe_10"] = mean_or_none([float(r["mfe_10"]) for r in rows if r.get("mfe_10") is not None])
    out["mean_mae_10"] = mean_or_none([float(r["mae_10"]) for r in rows if r.get("mae_10") is not None])
    for category in ("aligned", "neutral_transition", "opposite"):
        out[f"formal_{category}_rate"] = (
            float(np.mean([r["formal_category"] == category for r in rows])) if rows else None
        )
    return out


def summarize_pair(rows: list[dict[str, object]]) -> dict[str, object]:
    success_lags = [int(r["success_lag"]) for r in rows if r.get("success_lag") is not None]
    out: dict[str, object] = {
        "events": len(rows),
        "bull_events": sum(float(r["direction"]) > 0.0 for r in rows),
        "bear_events": sum(float(r["direction"]) < 0.0 for r in rows),
        "opposite_failure_rate": (
            float(np.mean([r["resolution"] == "opposite_actionable" for r in rows])) if rows else None
        ),
        "timeout_rate": float(np.mean([r["resolution"] == "timeout" for r in rows])) if rows else None,
        "median_success_lag_within_20": median_or_none([float(v) for v in success_lags]),
    }
    for horizon in HORIZONS:
        out[f"success_rate_{horizon}"] = (
            float(np.mean([bool(r[f"success_within_{horizon}"]) for r in rows])) if rows else None
        )
    success10 = [r for r in rows if bool(r["success_within_10"])]
    no_success10 = [r for r in rows if not bool(r["success_within_10"])]
    out["groups"] = {
        "success_within_10": summarize_group(success10),
        "no_success_within_10": summarize_group(no_success10),
    }
    return out


def analyze_pair(pair: str, frame: pd.DataFrame) -> dict[str, object]:
    model = compute_v06(frame.copy())
    rows = enrich_watch_rows(frame, model)
    return {
        "rows": len(frame),
        "start_date": str(frame["date"].iloc[0]),
        "end_date": str(frame["date"].iloc[-1]),
        "summary": summarize_pair(rows),
    }


def aggregate_pairs(pairs: dict[str, dict[str, object]]) -> dict[str, object]:
    summaries = [result["summary"] for result in pairs.values()]  # type: ignore[index]
    out: dict[str, object] = {
        "total_events": int(sum(int(s["events"]) for s in summaries)),
        "pairs_with_events": int(sum(int(s["events"]) > 0 for s in summaries)),
        "total_bull_events": int(sum(int(s["bull_events"]) for s in summaries)),
        "total_bear_events": int(sum(int(s["bear_events"]) for s in summaries)),
    }
    for metric in (
        "success_rate_5",
        "success_rate_10",
        "success_rate_20",
        "opposite_failure_rate",
        "timeout_rate",
        "median_success_lag_within_20",
    ):
        vals = [float(s[metric]) for s in summaries if s.get(metric) is not None]
        out[f"median_pair_{metric}"] = median_or_none(vals)

    groups: dict[str, object] = {}
    for group_name in ("success_within_10", "no_success_within_10"):
        group_rows = [s["groups"][group_name] for s in summaries]  # type: ignore[index]
        g: dict[str, object] = {"total_events": int(sum(int(x["events"]) for x in group_rows))}
        keys = [k for k in group_rows[0].keys() if k != "events"] if group_rows else []
        for key in keys:
            vals = [float(x[key]) for x in group_rows if x.get(key) is not None]
            g[f"median_pair_{key}"] = median_or_none(vals)
        groups[group_name] = g
    out["groups"] = groups
    return out


def build_report() -> dict[str, object]:
    pairs = {pair: analyze_pair(pair, frame) for pair, frame in load_burned_pairs().items()}
    return {
        "schema_version": 1,
        "issue": 57,
        "status": "BURNED_DATA_BRIDGE_BEHAVIOR_MAP_ONLY",
        "engine": "current Issue #57 v0.6 price-only core",
        "bridge_definition": "bull 1+2/1+3; bear 4+5/4+6; unordered Candidate+Secondary pair",
        "resolution_definition": "non-overlapping watch; same actionable success, opposite actionable failure, else 20-bar timeout",
        "horizons": list(HORIZONS),
        "primary_group_horizon": PRIMARY_GROUP_HORIZON,
        "pairs": pairs,
        "aggregate": aggregate_pairs(pairs),
        "boundary": "Existing burned fixtures are reused to understand current indicator behavior. No production threshold or rule is selected.",
    }


def pct(value: float | None) -> str:
    return "—" if value is None else f"{100.0 * value:.2f}%"


def num(value: float | None, digits: int = 2) -> str:
    return "—" if value is None else f"{value:.{digits}f}"


def render_markdown(report: dict[str, object]) -> str:
    agg = report["aggregate"]  # type: ignore[index]
    success = agg["groups"]["success_within_10"]
    fail = agg["groups"]["no_success_within_10"]
    lines = [
        "# Issue #57 — Early bridge formation behavior map",
        "",
        "**Burned-data structural study only. Existing v0.6 is unchanged.**",
        "",
        "## Conversion",
        "",
        f"- Non-overlapping bridge watches: **{agg['total_events']}** across **{agg['pairs_with_events']}** FX pairs.",
        f"- Bull / bear events: **{agg['total_bull_events']} / {agg['total_bear_events']}**.",
        f"- Median pair conversion to same-direction actionable within 5 bars: **{pct(agg['median_pair_success_rate_5'])}**.",
        f"- Within 10 bars: **{pct(agg['median_pair_success_rate_10'])}**.",
        f"- Within 20 bars: **{pct(agg['median_pair_success_rate_20'])}**.",
        f"- Median pair median lag when conversion occurs by 20: **{num(agg['median_pair_median_success_lag_within_20'], 1)} bars**.",
        f"- Opposite-actionable first: **{pct(agg['median_pair_opposite_failure_rate'])}**; timeout: **{pct(agg['median_pair_timeout_rate'])}**.",
        "",
        "## What differs at bridge onset? (success within 10 vs not)",
        "",
        "| Metric | Success <=10 | No success <=10 |",
        "|---|---:|---:|",
        f"| Events | {success['total_events']} | {fail['total_events']} |",
        f"| Top2 strength | {num(success['median_pair_median_top2_strength'])} | {num(fail['median_pair_median_top2_strength'])} |",
        f"| Six-stage entropy | {num(success['median_pair_median_entropy'], 3)} | {num(fail['median_pair_median_entropy'], 3)} |",
        f"| Context-stage weight | {num(success['median_pair_median_context_weight'])} | {num(fail['median_pair_median_context_weight'])} |",
        f"| Target-family weight | {num(success['median_pair_median_target_family_weight'])} | {num(fail['median_pair_median_target_family_weight'])} |",
        f"| Same-side pressure | {num(success['median_pair_median_same_side_pressure'])} | {num(fail['median_pair_median_same_side_pressure'])} |",
        f"| Opposite pressure | {num(success['median_pair_median_opposite_pressure'])} | {num(fail['median_pair_median_opposite_pressure'])} |",
        f"| 3-bar same-side pressure change | {num(success['median_pair_median_same_side_pressure_change_3'])} | {num(fail['median_pair_median_same_side_pressure_change_3'])} |",
        f"| Formal already aligned | {pct(success['median_pair_formal_aligned_rate'])} | {pct(fail['median_pair_formal_aligned_rate'])} |",
        f"| Formal neutral/transition | {pct(success['median_pair_formal_neutral_transition_rate'])} | {pct(fail['median_pair_formal_neutral_transition_rate'])} |",
        f"| 10-bar aligned return | {pct(success['median_pair_mean_aligned_return_10'])} | {pct(fail['median_pair_mean_aligned_return_10'])} |",
        f"| 10-bar MFE | {pct(success['median_pair_mean_mfe_10'])} | {pct(fail['median_pair_mean_mfe_10'])} |",
        f"| 10-bar MAE | {pct(success['median_pair_mean_mae_10'])} | {pct(fail['median_pair_mean_mae_10'])} |",
        "",
        "## Per pair",
        "",
        "| Pair | Events | Success <=5 | <=10 | <=20 | Median success lag |",
        "|---|---:|---:|---:|---:|---:|",
    ]
    for pair, result in report["pairs"].items():  # type: ignore[index]
        s = result["summary"]
        lines.append(
            f"| {pair} | {s['events']} | {pct(s['success_rate_5'])} | {pct(s['success_rate_10'])} | {pct(s['success_rate_20'])} | {num(s['median_success_lag_within_20'], 1)} |"
        )
    lines.extend(
        [
            "",
            "## Boundary",
            "",
            "This map describes already-observed data. Differences between successful and failed bridges are hypotheses about indicator behavior, not validated entry rules.",
            "",
        ]
    )
    return "\n".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--json-output", type=Path)
    parser.add_argument("--md-output", type=Path)
    args = parser.parse_args()
    report = build_report()
    if args.json_output:
        args.json_output.parent.mkdir(parents=True, exist_ok=True)
        args.json_output.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    if args.md_output:
        args.md_output.parent.mkdir(parents=True, exist_ok=True)
        args.md_output.write_text(render_markdown(report), encoding="utf-8")
    print(json.dumps(report["aggregate"], indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
