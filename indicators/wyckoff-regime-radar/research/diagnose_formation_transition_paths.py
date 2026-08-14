#!/usr/bin/env python3
"""Issue #57 burned-data map of structural paths into actionable Top-2 regimes."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
import pandas as pd

from diagnose_consensus_formation_and_formal_lag import (
    compute_v06,
    consensus_components,
    formal_action_direction,
    load_burned_pairs,
)
from diagnose_transition_formation_and_regime_decay import (
    aligned_return,
    adverse_excursion,
    extract_action_episodes,
)

HERE = Path(__file__).resolve().parent
HORIZONS = (5, 10, 20)
ADOPTION_HORIZONS = (5, 10, 20)
CATEGORIES = (
    "semantic_context_bridge",
    "opposite_actionable_flip",
    "one_stage_carry_other",
    "both_stages_new",
)


def median_or_none(values: list[float]) -> float | None:
    return float(np.median(values)) if values else None


def mean_or_none(values: list[float]) -> float | None:
    return float(np.mean(values)) if values else None


def classify_precursor(prior_top1: int, prior_top2: int, new_direction: float) -> str:
    prior = {int(prior_top1), int(prior_top2)}
    if new_direction > 0.0:
        new_pair = {2, 3}
        semantic = ({1, 2}, {1, 3})
        opposite = {5, 6}
    elif new_direction < 0.0:
        new_pair = {5, 6}
        semantic = ({4, 5}, {4, 6})
        opposite = {2, 3}
    else:
        raise ValueError("new_direction must be actionable")

    if prior in semantic:
        return "semantic_context_bridge"
    if prior == opposite:
        return "opposite_actionable_flip"
    if len(prior & new_pair) == 1:
        return "one_stage_carry_other"
    return "both_stages_new"


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


def event_rows(frame: pd.DataFrame, model: pd.DataFrame) -> list[dict[str, object]]:
    direction, _, top1, top2 = consensus_components(model)
    formal = formal_action_direction(model)
    episodes = extract_action_episodes(direction)
    rows: list[dict[str, object]] = []

    for episode in episodes:
        start = int(episode["start"])
        if start <= 0:
            continue
        d = float(episode["direction"])
        duration = int(episode["duration"])
        category = classify_precursor(int(top1[start - 1]), int(top2[start - 1]), d)
        formal_at_onset = float(formal[start])
        if formal_at_onset == d:
            formal_category = "aligned"
        elif formal_at_onset == 0.0:
            formal_category = "neutral_transition"
        else:
            formal_category = "opposite"

        adoption_lag: int | None = None
        if formal_at_onset != d:
            max_lag = min(max(ADOPTION_HORIZONS), len(model) - 1 - start)
            for lag in range(1, max_lag + 1):
                if float(formal[start + lag]) == d:
                    adoption_lag = lag
                    break

        row: dict[str, object] = {
            "start": start,
            "direction": d,
            "duration": duration,
            "category": category,
            "prior_top1": int(top1[start - 1]),
            "prior_top2": int(top2[start - 1]),
            "formal_category_at_onset": formal_category,
            "formal_adoption_lag": adoption_lag,
        }
        for horizon in HORIZONS:
            row[f"survives_{horizon}"] = bool(duration >= horizon)
            row[f"aligned_return_{horizon}"] = aligned_return(frame, start, d, horizon)
        row["mfe_10"] = favorable_excursion(frame, start, d, 10)
        row["mae_10"] = adverse_excursion(frame, start, d, 10)
        rows.append(row)
    return rows


def summarize_category(rows: list[dict[str, object]]) -> dict[str, object]:
    if not rows:
        return {"events": 0}
    out: dict[str, object] = {
        "events": len(rows),
        "median_duration": median_or_none([float(r["duration"]) for r in rows]),
        "formal_aligned_at_onset_rate": float(np.mean([r["formal_category_at_onset"] == "aligned" for r in rows])),
        "formal_neutral_at_onset_rate": float(np.mean([r["formal_category_at_onset"] == "neutral_transition" for r in rows])),
        "formal_opposite_at_onset_rate": float(np.mean([r["formal_category_at_onset"] == "opposite" for r in rows])),
    }
    for h in HORIZONS:
        out[f"survival_rate_{h}"] = float(np.mean([bool(r[f"survives_{h}"]) for r in rows]))
        vals = [float(r[f"aligned_return_{h}"]) for r in rows if r[f"aligned_return_{h}"] is not None]
        out[f"mean_aligned_return_{h}"] = mean_or_none(vals)
    out["mean_mfe_10"] = mean_or_none([float(r["mfe_10"]) for r in rows if r["mfe_10"] is not None])
    out["mean_mae_10"] = mean_or_none([float(r["mae_10"]) for r in rows if r["mae_10"] is not None])

    nonaligned = [r for r in rows if r["formal_category_at_onset"] != "aligned"]
    out["formal_nonaligned_origins"] = len(nonaligned)
    for h in ADOPTION_HORIZONS:
        adopted = [r for r in nonaligned if r["formal_adoption_lag"] is not None and int(r["formal_adoption_lag"]) <= h]
        out[f"formal_adoption_rate_{h}"] = float(len(adopted) / len(nonaligned)) if nonaligned else None
    lags = [int(r["formal_adoption_lag"]) for r in nonaligned if r["formal_adoption_lag"] is not None and int(r["formal_adoption_lag"]) <= 20]
    out["median_formal_adoption_lag_within_20"] = median_or_none([float(v) for v in lags])
    return out


def analyze_pair(frame: pd.DataFrame) -> dict[str, object]:
    model = compute_v06(frame.copy())
    rows = event_rows(frame, model)
    return {
        "rows": len(frame),
        "start_date": str(frame["date"].iloc[0]),
        "end_date": str(frame["date"].iloc[-1]),
        "categories": {cat: summarize_category([r for r in rows if r["category"] == cat]) for cat in CATEGORIES},
    }


def aggregate_pairs(pairs: dict[str, dict[str, object]]) -> dict[str, object]:
    out: dict[str, object] = {}
    metrics = (
        "median_duration",
        "survival_rate_5",
        "survival_rate_10",
        "survival_rate_20",
        "mean_aligned_return_5",
        "mean_aligned_return_10",
        "mean_aligned_return_20",
        "mean_mfe_10",
        "mean_mae_10",
        "formal_aligned_at_onset_rate",
        "formal_neutral_at_onset_rate",
        "formal_opposite_at_onset_rate",
        "formal_adoption_rate_5",
        "formal_adoption_rate_10",
        "formal_adoption_rate_20",
        "median_formal_adoption_lag_within_20",
    )
    for cat in CATEGORIES:
        rows = [p["categories"][cat] for p in pairs.values()]  # type: ignore[index]
        nonempty = [r for r in rows if int(r["events"]) > 0]
        summary: dict[str, object] = {
            "total_events": int(sum(int(r["events"]) for r in nonempty)),
            "pairs_with_events": len(nonempty),
        }
        for metric in metrics:
            vals = [float(r[metric]) for r in nonempty if r.get(metric) is not None]
            summary[f"median_pair_{metric}"] = median_or_none(vals)
        out[cat] = summary
    return out


def build_report() -> dict[str, object]:
    pairs = {pair: analyze_pair(frame) for pair, frame in load_burned_pairs().items()}
    return {
        "schema_version": 1,
        "issue": 57,
        "status": "BURNED_DATA_FORMATION_PATH_BEHAVIOR_MAP_ONLY",
        "engine": "current Issue #57 v0.6 price-only core",
        "event_definition": "first bar of consecutive actionable Top2 episode: 2+3 bull or 5+6 bear",
        "precursor_definition": "immediately preceding bar Top2 pair only",
        "category_precedence": list(CATEGORIES),
        "pairs": pairs,
        "aggregate": aggregate_pairs(pairs),
        "boundary": "Predeclared descriptive categories on burned data. No category may be promoted to a production rule from this report alone.",
    }


def pct(v: float | None) -> str:
    return "—" if v is None else f"{100*v:.2f}%"


def num(v: float | None, d: int = 2) -> str:
    return "—" if v is None else f"{v:.{d}f}"


def render_markdown(report: dict[str, object]) -> str:
    lines = [
        "# Issue #57 — Formation transition-path behavior map",
        "",
        "**Burned-data structural behavior study only. Existing v0.6 is unchanged.**",
        "",
        "The precursor is the immediately previous bar's Top-2 pair. Categories were frozen before running outcomes.",
        "",
        "| Precursor path | Events | Pairs | Median duration | Survive 5 | Survive 10 | 10-bar return | 10-bar MFE | 10-bar MAE | Formal aligned onset | Formal adopt <=5 |",
        "|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|",
    ]
    labels = {
        "semantic_context_bridge": "Semantic context bridge (1→2+3 / 4→5+6)",
        "opposite_actionable_flip": "Direct opposite actionable flip",
        "one_stage_carry_other": "Other one-stage carry",
        "both_stages_new": "Both stages new",
    }
    for cat in CATEGORIES:
        s = report["aggregate"][cat]  # type: ignore[index]
        lines.append(
            f"| {labels[cat]} | {s['total_events']} | {s['pairs_with_events']} | {num(s['median_pair_median_duration'],1)} | "
            f"{pct(s['median_pair_survival_rate_5'])} | {pct(s['median_pair_survival_rate_10'])} | "
            f"{pct(s['median_pair_mean_aligned_return_10'])} | {pct(s['median_pair_mean_mfe_10'])} | "
            f"{pct(s['median_pair_mean_mae_10'])} | {pct(s['median_pair_formal_aligned_at_onset_rate'])} | "
            f"{pct(s['median_pair_formal_adoption_rate_5'])} |"
        )
    lines.extend([
        "",
        "## Boundary",
        "",
        "These are behavior-map comparisons on already-observed data. A visually attractive category is not a validated trading rule and no threshold or model parameter is selected here.",
        "",
    ])
    return "\n".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--json-output", type=Path, default=HERE / "reports" / "issue-57-formation-transition-paths.json")
    parser.add_argument("--md-output", type=Path, default=HERE / "reports" / "issue-57-formation-transition-paths.md")
    args = parser.parse_args()
    report = build_report()
    args.json_output.parent.mkdir(parents=True, exist_ok=True)
    args.md_output.parent.mkdir(parents=True, exist_ok=True)
    args.json_output.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    args.md_output.write_text(render_markdown(report), encoding="utf-8")
    print(json.dumps(report["aggregate"], indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
