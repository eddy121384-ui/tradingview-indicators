#!/usr/bin/env python3
"""Issue #57 reused-data price relevance of +3 transition health."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
import pandas as pd

from diagnose_consensus_formation_and_formal_lag import compute_v06, load_burned_pairs
from diagnose_post_handoff_hold_persistence import build_rows

CHECKPOINT = 3
HORIZONS = (5, 10, 20)
GROUPS = ("healthy_hold", "damaged_retake")


def median_or_none(values: list[float]) -> float | None:
    return float(np.median(values)) if values else None


def price_path_metrics(
    frame: pd.DataFrame,
    index: int,
    direction: float,
    horizon: int,
) -> dict[str, float] | None:
    """Forward price path from an observable checkpoint close.

    Returns direction-aligned close return, MFE and MAE. These are price-path
    quantities, not an executable trade PnL convention.
    """
    if index < 0 or index + horizon >= len(frame):
        return None
    close = pd.to_numeric(frame["close"], errors="coerce").to_numpy(float)
    high = pd.to_numeric(frame["high"], errors="coerce").to_numpy(float)
    low = pd.to_numeric(frame["low"], errors="coerce").to_numpy(float)
    base = float(close[index])
    future = float(close[index + horizon])
    if not np.isfinite(base) or base <= 0.0 or not np.isfinite(future):
        return None
    future_high = high[index + 1 : index + horizon + 1]
    future_low = low[index + 1 : index + horizon + 1]
    if future_high.size == 0 or future_low.size == 0:
        return None
    if not np.isfinite(future_high).any() or not np.isfinite(future_low).any():
        return None

    aligned = float(direction * (future / base - 1.0))
    if direction > 0.0:
        mfe = float(max(0.0, np.nanmax(future_high) / base - 1.0))
        mae = float(max(0.0, 1.0 - np.nanmin(future_low) / base))
    else:
        mfe = float(max(0.0, 1.0 - np.nanmin(future_low) / base))
        mae = float(max(0.0, np.nanmax(future_high) / base - 1.0))
    return {"aligned_return": aligned, "mfe": mfe, "mae": mae}


def build_price_rows(frame: pd.DataFrame) -> list[dict[str, object]]:
    model = compute_v06(frame.copy())
    _, checkpoints = build_rows(model)
    rows: list[dict[str, object]] = []
    for item in checkpoints:
        if int(item["checkpoint"]) != CHECKPOINT:
            continue
        onset = int(item["onset"])
        observation = onset + CHECKPOINT
        if observation >= len(frame):
            continue
        direction = float(item["direction"])
        group = "healthy_hold" if bool(item["lead_held_through_checkpoint"]) else "damaged_retake"
        row: dict[str, object] = {
            "onset": onset,
            "observation": observation,
            "direction": direction,
            "group": group,
            "resolution": str(item["resolution"]),
        }
        for horizon in HORIZONS:
            metrics = price_path_metrics(frame, observation, direction, horizon)
            if metrics is None:
                row[f"aligned_return_{horizon}"] = None
                row[f"mfe_{horizon}"] = None
                row[f"mae_{horizon}"] = None
                row[f"hit_{horizon}"] = None
            else:
                row[f"aligned_return_{horizon}"] = metrics["aligned_return"]
                row[f"mfe_{horizon}"] = metrics["mfe"]
                row[f"mae_{horizon}"] = metrics["mae"]
                row[f"hit_{horizon}"] = bool(metrics["aligned_return"] > 0.0)
        rows.append(row)
    return rows


def summarize_group(rows: list[dict[str, object]]) -> dict[str, object]:
    out: dict[str, object] = {"events": len(rows), "horizons": {}}
    for horizon in HORIZONS:
        valid = [r for r in rows if r.get(f"aligned_return_{horizon}") is not None]
        if not valid:
            out["horizons"][str(horizon)] = {  # type: ignore[index]
                "valid_events": 0,
                "mean_aligned_return": None,
                "median_aligned_return": None,
                "hit_rate": None,
                "mean_mfe": None,
                "mean_mae": None,
                "mean_mfe_minus_mae": None,
            }
            continue
        aligned = [float(r[f"aligned_return_{horizon}"]) for r in valid]
        mfes = [float(r[f"mfe_{horizon}"]) for r in valid]
        maes = [float(r[f"mae_{horizon}"]) for r in valid]
        hits = [bool(r[f"hit_{horizon}"]) for r in valid]
        out["horizons"][str(horizon)] = {  # type: ignore[index]
            "valid_events": len(valid),
            "mean_aligned_return": float(np.mean(aligned)),
            "median_aligned_return": float(np.median(aligned)),
            "hit_rate": float(np.mean(hits)),
            "mean_mfe": float(np.mean(mfes)),
            "mean_mae": float(np.mean(maes)),
            "mean_mfe_minus_mae": float(np.mean(np.asarray(mfes) - np.asarray(maes))),
        }
    return out


def analyze_pair(frame: pd.DataFrame) -> dict[str, object]:
    rows = build_price_rows(frame)
    groups = {g: summarize_group([r for r in rows if r["group"] == g]) for g in GROUPS}
    return {
        "rows": len(frame),
        "start_date": str(frame["date"].iloc[0]),
        "end_date": str(frame["date"].iloc[-1]),
        "eligible_events": len(rows),
        "groups": groups,
    }


def aggregate_pairs(pairs: dict[str, dict[str, object]]) -> dict[str, object]:
    result: dict[str, object] = {
        "eligible_events": int(sum(int(p["eligible_events"]) for p in pairs.values())),
        "group_events": {
            g: int(sum(int(p["groups"][g]["events"]) for p in pairs.values()))  # type: ignore[index]
            for g in GROUPS
        },
        "horizons": {},
    }
    for horizon in HORIZONS:
        hkey = str(horizon)
        h_out: dict[str, object] = {"groups": {}}
        for group in GROUPS:
            metric_lists: dict[str, list[float]] = {
                "mean_aligned_return": [],
                "hit_rate": [],
                "mean_mfe": [],
                "mean_mae": [],
                "mean_mfe_minus_mae": [],
            }
            for pair in pairs.values():
                item = pair["groups"][group]["horizons"][hkey]  # type: ignore[index]
                for metric in metric_lists:
                    value = item.get(metric)
                    if value is not None:
                        metric_lists[metric].append(float(value))
            h_out["groups"][group] = {  # type: ignore[index]
                "median_pair_mean_aligned_return": median_or_none(metric_lists["mean_aligned_return"]),
                "median_pair_hit_rate": median_or_none(metric_lists["hit_rate"]),
                "median_pair_mean_mfe": median_or_none(metric_lists["mean_mfe"]),
                "median_pair_mean_mae": median_or_none(metric_lists["mean_mae"]),
                "median_pair_mean_mfe_minus_mae": median_or_none(metric_lists["mean_mfe_minus_mae"]),
                "pairs_with_metric": len(metric_lists["mean_aligned_return"]),
            }

        return_wins = 0
        hit_wins = 0
        mfe_mae_wins = 0
        comparable = 0
        for pair in pairs.values():
            healthy = pair["groups"]["healthy_hold"]["horizons"][hkey]  # type: ignore[index]
            damaged = pair["groups"]["damaged_retake"]["horizons"][hkey]  # type: ignore[index]
            if healthy.get("mean_aligned_return") is None or damaged.get("mean_aligned_return") is None:
                continue
            comparable += 1
            if float(healthy["mean_aligned_return"]) > float(damaged["mean_aligned_return"]):
                return_wins += 1
            if float(healthy["hit_rate"]) > float(damaged["hit_rate"]):
                hit_wins += 1
            if float(healthy["mean_mfe_minus_mae"]) > float(damaged["mean_mfe_minus_mae"]):
                mfe_mae_wins += 1
        h_out["pair_comparison"] = {
            "comparable_pairs": comparable,
            "healthy_return_wins": return_wins,
            "healthy_hit_rate_wins": hit_wins,
            "healthy_mfe_minus_mae_wins": mfe_mae_wins,
        }
        result["horizons"][hkey] = h_out  # type: ignore[index]
    return result


def build_report() -> dict[str, object]:
    pairs = {pair: analyze_pair(frame) for pair, frame in load_burned_pairs().items()}
    return {
        "schema_version": 1,
        "issue": 57,
        "status": "BURNED_DATA_TRANSITION_HEALTH_PRICE_OUTCOME_ONLY",
        "checkpoint": CHECKPOINT,
        "horizons": list(HORIZONS),
        "pairs": pairs,
        "aggregate": aggregate_pairs(pairs),
        "boundary": "Reused-data price-relevance diagnostic only; no production trading rule or independent OOS claim.",
    }


def pct(v: float | None) -> str:
    return "—" if v is None else f"{100.0 * v:.2f}%"


def render_markdown(report: dict[str, object]) -> str:
    agg = report["aggregate"]  # type: ignore[index]
    lines = [
        "# Issue #57 — Transition health → subsequent price outcomes",
        "",
        "**Reused-data price-relevance study only. Existing v0.6 is unchanged.**",
        "",
        f"- Observable checkpoint: **+{CHECKPOINT} bars after handoff onset**.",
        f"- Eligible unresolved events: **{agg['eligible_events']}**.",
        f"- Healthy / damaged events: **{agg['group_events']['healthy_hold']} / {agg['group_events']['damaged_retake']}**.",
        "- All price outcomes start from the +3 close; pre-checkpoint price movement is excluded.",
        "",
        "## Cross-pair price outcomes",
        "",
        "| Horizon | Group | Aligned return | Hit rate | MFE | MAE | MFE-MAE |",
        "|---|---|---:|---:|---:|---:|---:|",
    ]
    for horizon in HORIZONS:
        h = agg["horizons"][str(horizon)]
        for group in GROUPS:
            g = h["groups"][group]
            lines.append(
                f"| +{horizon} | {group} | {pct(g['median_pair_mean_aligned_return'])} | "
                f"{pct(g['median_pair_hit_rate'])} | {pct(g['median_pair_mean_mfe'])} | "
                f"{pct(g['median_pair_mean_mae'])} | {pct(g['median_pair_mean_mfe_minus_mae'])} |"
            )

    lines += [
        "",
        "## Pair consistency",
        "",
        "| Horizon | Comparable FX | Healthy wins aligned return | Healthy wins hit rate | Healthy wins MFE-MAE |",
        "|---|---:|---:|---:|---:|",
    ]
    for horizon in HORIZONS:
        c = agg["horizons"][str(horizon)]["pair_comparison"]
        lines.append(
            f"| +{horizon} | {c['comparable_pairs']} | {c['healthy_return_wins']} | "
            f"{c['healthy_hit_rate_wins']} | {c['healthy_mfe_minus_mae_wins']} |"
        )

    lines += [
        "",
        "## Per pair — 10-bar aligned return / hit rate",
        "",
        "| Pair | Healthy n | Healthy return | Healthy hit | Damaged n | Damaged return | Damaged hit |",
        "|---|---:|---:|---:|---:|---:|---:|",
    ]
    for pair, result in report["pairs"].items():  # type: ignore[index]
        healthy = result["groups"]["healthy_hold"]
        damaged = result["groups"]["damaged_retake"]
        h10 = healthy["horizons"]["10"]
        d10 = damaged["horizons"]["10"]
        lines.append(
            f"| {pair} | {healthy['events']} | {pct(h10['mean_aligned_return'])} | {pct(h10['hit_rate'])} | "
            f"{damaged['events']} | {pct(d10['mean_aligned_return'])} | {pct(d10['hit_rate'])} |"
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
    args.json_output.write_text(json.dumps(report, indent=2), encoding="utf-8")
    args.md_output.write_text(render_markdown(report), encoding="utf-8")
    print(json.dumps(report["aggregate"], indent=2))


if __name__ == "__main__":
    main()
