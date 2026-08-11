#!/usr/bin/env python3
"""Issue #57 burned-data diagnostic for consensus formation and Formal lag.

Rules are preregistered in:
  decisions/issue-57-consensus-formation-preregistered-diagnostic.md

This script is deliberately price-only and must not be described as independent
OOS validation. It runs the same analysis on frozen v0.5.2.1 and current v0.6.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Callable

import numpy as np
import pandas as pd

from diagnose_v06_top2_directional_consensus import (
    HORIZONS,
    WEIGHT_COLUMNS,
    future_aligned_metrics,
    load_burned_pairs,
    top_ids_and_values,
)
from generate_v06_phase_b_core import load_phase_b_namespace
from price_only_core import PriceOnlyConfig as V05Config
from price_only_core import compute_price_only as compute_v05


HERE = Path(__file__).resolve().parent
PRIMARY_THRESHOLD = 90.0
STRENGTH_BINS = (
    ("<70", -np.inf, 70.0),
    ("70-<80", 70.0, 80.0),
    ("80-<90", 80.0, 90.0),
    ("90-<95", 90.0, 95.0),
    (">=95", 95.0, np.inf),
)
PERSISTENCE_LEVELS = (1, 2, 3)
ADOPTION_HORIZONS = (5, 10, 20)


def compute_v06(frame: pd.DataFrame) -> pd.DataFrame:
    ns = load_phase_b_namespace()
    compute: Callable = ns["compute_price_only"]  # type: ignore[assignment]
    config_cls = ns["PriceOnlyConfig"]
    return compute(frame.copy(), config_cls())


def action_pair_direction(top1: np.ndarray, top2: np.ndarray) -> np.ndarray:
    out = np.zeros(len(top1), dtype=float)
    bull = ((top1 == 2) & (top2 == 3)) | ((top1 == 3) & (top2 == 2))
    bear = ((top1 == 5) & (top2 == 6)) | ((top1 == 6) & (top2 == 5))
    out[bull] = 1.0
    out[bear] = -1.0
    return out


def formal_action_direction(model: pd.DataFrame) -> np.ndarray:
    ids = pd.to_numeric(model["formal_id"], errors="coerce").fillna(0).to_numpy(int)
    out = np.zeros(len(ids), dtype=float)
    out[np.isin(ids, [2, 3])] = 1.0
    out[np.isin(ids, [5, 6])] = -1.0
    return out


def consensus_components(model: pd.DataFrame) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    top1, top2, val1, val2 = top_ids_and_values(model)
    direction = action_pair_direction(top1, top2)
    strength = val1 + val2
    valid = (direction != 0.0) & np.isfinite(strength)
    return direction, strength, top1, top2


def threshold_signal(model: pd.DataFrame, threshold: float = PRIMARY_THRESHOLD) -> np.ndarray:
    direction, strength, _, _ = consensus_components(model)
    return np.where((direction != 0.0) & np.isfinite(strength) & (strength >= threshold), direction, 0.0)


def strength_bin_masks(model: pd.DataFrame) -> dict[str, np.ndarray]:
    direction, strength, _, _ = consensus_components(model)
    masks: dict[str, np.ndarray] = {}
    for label, low, high in STRENGTH_BINS:
        masks[label] = (direction != 0.0) & np.isfinite(strength) & (strength >= low) & (strength < high)
    return masks


def signal_from_mask(direction: np.ndarray, mask: np.ndarray) -> np.ndarray:
    return np.where(mask, direction, 0.0)


def continuous_spearman(frame: pd.DataFrame, model: pd.DataFrame, horizon: int) -> dict[str, float | int | None]:
    direction, strength, _, _ = consensus_components(model)
    close = pd.to_numeric(frame["close"], errors="coerce").to_numpy(float)
    n = len(frame) - horizon
    if n <= 2:
        return {"n": 0, "rho": None}
    valid = (
        (direction[:n] != 0.0)
        & np.isfinite(strength[:n])
        & np.isfinite(close[:n])
        & np.isfinite(close[horizon:])
        & (close[:n] > 0.0)
    )
    if int(np.sum(valid)) < 3:
        return {"n": int(np.sum(valid)), "rho": None}
    aligned = direction[:n] * (close[horizon:] / close[:n] - 1.0)
    x = pd.Series(strength[:n][valid])
    y = pd.Series(aligned[valid])
    rho = x.corr(y, method="spearman")
    return {"n": int(np.sum(valid)), "rho": None if pd.isna(rho) else float(rho)}


def formal_category_signals(model: pd.DataFrame) -> dict[str, np.ndarray]:
    consensus = threshold_signal(model)
    formal = formal_action_direction(model)
    active = consensus != 0.0
    return {
        "formal_aligned": np.where(active & (formal == consensus), consensus, 0.0),
        "formal_transition_or_neutral": np.where(active & (formal == 0.0), consensus, 0.0),
        "formal_opposite": np.where(active & (formal == -consensus), consensus, 0.0),
    }


def adoption_stats(model: pd.DataFrame) -> dict[str, dict[str, float | int | None]]:
    consensus = threshold_signal(model)
    formal = formal_action_direction(model)
    categories = {
        "formal_transition_or_neutral": (consensus != 0.0) & (formal == 0.0),
        "formal_opposite": (consensus != 0.0) & (formal == -consensus),
    }
    out: dict[str, dict[str, float | int | None]] = {}
    for category, mask in categories.items():
        origins = np.flatnonzero(mask)
        row: dict[str, float | int | None] = {"origins": int(len(origins))}
        lags: list[int] = []
        for i in origins:
            max_h = min(max(ADOPTION_HORIZONS), len(model) - 1 - i)
            adopted = None
            for lag in range(1, max_h + 1):
                if formal[i + lag] == consensus[i]:
                    adopted = lag
                    break
            if adopted is not None:
                lags.append(adopted)
        for h in ADOPTION_HORIZONS:
            adopted_h = sum(lag <= h for lag in lags)
            row[f"adopted_within_{h}"] = int(adopted_h)
            row[f"adoption_rate_{h}"] = float(adopted_h / len(origins)) if len(origins) else None
        row["median_adoption_lag_if_adopted_within_20"] = (
            float(np.median([lag for lag in lags if lag <= 20])) if any(lag <= 20 for lag in lags) else None
        )
        out[category] = row
    return out


def persistence_event_signal(model: pd.DataFrame, required_bars: int) -> np.ndarray:
    base = threshold_signal(model)
    out = np.zeros(len(base), dtype=float)
    last_direction = 0.0
    streak = 0
    for i, value in enumerate(base):
        value = float(value)
        if value != 0.0 and value == last_direction:
            streak += 1
        elif value != 0.0:
            last_direction = value
            streak = 1
        else:
            last_direction = 0.0
            streak = 0
        if value != 0.0 and streak == required_bars:
            out[i] = value
    return out


def analyze_model(frame: pd.DataFrame, model: pd.DataFrame) -> dict[str, object]:
    direction, strength, _, _ = consensus_components(model)
    bins = strength_bin_masks(model)

    monotonicity: dict[str, object] = {"bins": {}, "spearman": {}}
    for label, _, _ in STRENGTH_BINS:
        signal = signal_from_mask(direction, bins[label])
        monotonicity["bins"][label] = {  # type: ignore[index]
            str(h): future_aligned_metrics(frame, signal, h) for h in HORIZONS
        }
    monotonicity["spearman"] = {str(h): continuous_spearman(frame, model, h) for h in HORIZONS}

    category_signals = formal_category_signals(model)
    formal_lag = {
        "categories": {
            category: {str(h): future_aligned_metrics(frame, signal, h) for h in HORIZONS}
            for category, signal in category_signals.items()
        },
        "adoption": adoption_stats(model),
    }

    persistence = {
        str(k): {
            "events": int(np.sum(persistence_event_signal(model, k) != 0.0)),
            "horizons": {
                str(h): future_aligned_metrics(frame, persistence_event_signal(model, k), h)
                for h in HORIZONS
            },
        }
        for k in PERSISTENCE_LEVELS
    }

    return {
        "action_pair_bar_share": float(np.mean(direction != 0.0)),
        "primary_90_bar_share": float(np.mean(threshold_signal(model) != 0.0)),
        "strength_summary": {
            "median": float(np.nanmedian(strength[direction != 0.0])) if np.any(direction != 0.0) else None,
            "p90": float(np.nanquantile(strength[direction != 0.0], 0.90)) if np.any(direction != 0.0) else None,
        },
        "monotonicity": monotonicity,
        "formal_lag": formal_lag,
        "persistence": persistence,
    }


def analyze_pair(pair: str, frame: pd.DataFrame) -> dict[str, object]:
    v05 = compute_v05(frame.copy(), V05Config())
    v06 = compute_v06(frame)
    return {
        "rows": len(frame),
        "start_date": str(frame["date"].iloc[0]),
        "end_date": str(frame["date"].iloc[-1]),
        "v05": analyze_model(frame, v05),
        "v06": analyze_model(frame, v06),
    }


def median_or_none(values: list[float]) -> float | None:
    return float(np.median(values)) if values else None


def aggregate(pair_results: dict[str, dict[str, object]], engine: str) -> dict[str, object]:
    bin_rows: dict[str, object] = {}
    for label, _, _ in STRENGTH_BINS:
        horizons: dict[str, object] = {}
        for h in HORIZONS:
            means: list[float] = []
            hits: list[float] = []
            counts = 0
            positive_pairs = 0
            for result in pair_results.values():
                row = result[engine]["monotonicity"]["bins"][label][str(h)]  # type: ignore[index]
                counts += int(row["signal_origins"])
                if row["mean_aligned_return"] is not None:
                    value = float(row["mean_aligned_return"])
                    means.append(value)
                    positive_pairs += int(value > 0.0)
                if row["hit_rate"] is not None:
                    hits.append(float(row["hit_rate"]))
            horizons[str(h)] = {
                "median_pair_mean_aligned_return": median_or_none(means),
                "median_pair_hit_rate": median_or_none(hits),
                "total_origins": counts,
                "positive_pairs": positive_pairs,
                "pair_count": len(pair_results),
            }
        bin_rows[label] = horizons

    spearman: dict[str, object] = {}
    for h in HORIZONS:
        rhos: list[float] = []
        positive = 0
        for result in pair_results.values():
            rho = result[engine]["monotonicity"]["spearman"][str(h)]["rho"]  # type: ignore[index]
            if rho is not None:
                value = float(rho)
                rhos.append(value)
                positive += int(value > 0.0)
        spearman[str(h)] = {
            "median_pair_rho": median_or_none(rhos),
            "positive_pair_rho": positive,
            "comparable_pairs": len(rhos),
        }

    categories: dict[str, object] = {}
    for category in ("formal_aligned", "formal_transition_or_neutral", "formal_opposite"):
        horizons = {}
        for h in HORIZONS:
            means: list[float] = []
            hits: list[float] = []
            origins = 0
            for result in pair_results.values():
                row = result[engine]["formal_lag"]["categories"][category][str(h)]  # type: ignore[index]
                origins += int(row["signal_origins"])
                if row["mean_aligned_return"] is not None:
                    means.append(float(row["mean_aligned_return"]))
                if row["hit_rate"] is not None:
                    hits.append(float(row["hit_rate"]))
            horizons[str(h)] = {
                "median_pair_mean_aligned_return": median_or_none(means),
                "median_pair_hit_rate": median_or_none(hits),
                "total_origins": origins,
            }
        categories[category] = horizons

    adoption: dict[str, object] = {}
    for category in ("formal_transition_or_neutral", "formal_opposite"):
        rows = [result[engine]["formal_lag"]["adoption"][category] for result in pair_results.values()]  # type: ignore[index]
        category_out: dict[str, object] = {"total_origins": int(sum(int(row["origins"]) for row in rows))}
        for h in ADOPTION_HORIZONS:
            rates = [float(row[f"adoption_rate_{h}"]) for row in rows if row[f"adoption_rate_{h}"] is not None]
            category_out[f"median_pair_adoption_rate_{h}"] = median_or_none(rates)
        lags = [
            float(row["median_adoption_lag_if_adopted_within_20"])
            for row in rows
            if row["median_adoption_lag_if_adopted_within_20"] is not None
        ]
        category_out["median_of_pair_median_adoption_lag"] = median_or_none(lags)
        adoption[category] = category_out

    persistence: dict[str, object] = {}
    for k in PERSISTENCE_LEVELS:
        horizons = {}
        total_events = 0
        for result in pair_results.values():
            total_events += int(result[engine]["persistence"][str(k)]["events"])  # type: ignore[index]
        for h in HORIZONS:
            means: list[float] = []
            hits: list[float] = []
            origins = 0
            for result in pair_results.values():
                row = result[engine]["persistence"][str(k)]["horizons"][str(h)]  # type: ignore[index]
                origins += int(row["signal_origins"])
                if row["mean_aligned_return"] is not None:
                    means.append(float(row["mean_aligned_return"]))
                if row["hit_rate"] is not None:
                    hits.append(float(row["hit_rate"]))
            horizons[str(h)] = {
                "median_pair_mean_aligned_return": median_or_none(means),
                "median_pair_hit_rate": median_or_none(hits),
                "total_origins": origins,
            }
        persistence[str(k)] = {"total_events": total_events, "horizons": horizons}

    return {
        "strength_bins": bin_rows,
        "strength_spearman": spearman,
        "formal_categories": categories,
        "formal_adoption": adoption,
        "persistence": persistence,
    }


def build_report() -> dict[str, object]:
    pairs = {pair: analyze_pair(pair, frame) for pair, frame in load_burned_pairs().items()}
    return {
        "schema_version": 1,
        "issue": 57,
        "status": "BURNED_DATA_CONSENSUS_FORMATION_DIAGNOSTIC_ONLY",
        "price_only": True,
        "primary_threshold": PRIMARY_THRESHOLD,
        "strength_bins": [label for label, _, _ in STRENGTH_BINS],
        "persistence_levels": list(PERSISTENCE_LEVELS),
        "engines": {
            "v05": "frozen v0.5.2.1 price-only mirror",
            "v06": "Issue #57 v0.6 price-only core",
        },
        "pairs": pairs,
        "aggregate": {
            "v05": aggregate(pairs, "v05"),
            "v06": aggregate(pairs, "v06"),
        },
        "boundary": "All fixtures are burned; results are hypothesis-development only and cannot validate a live signal.",
    }


def pct(value: float | None) -> str:
    return "—" if value is None else f"{value * 100:.2f}%"


def num(value: float | None) -> str:
    return "—" if value is None else f"{value:.3f}"


def render_markdown(report: dict[str, object]) -> str:
    lines = [
        "# Issue #57 — Consensus formation and Formal-lag diagnostic",
        "",
        "**Burned-data / price-only hypothesis development only. Not independent OOS.**",
        "",
        "Action-compatible pairs are fixed as 2+3 bullish and 5+6 bearish. The user's 90% threshold remains the primary reference.",
        "",
    ]

    for engine in ("v05", "v06"):
        agg = report["aggregate"][engine]  # type: ignore[index]
        lines.extend([
            f"## {engine} — strength monotonicity",
            "",
            "| Strength | H | Median aligned return | Median hit rate | Origins | Positive pairs |",
            "|---|---:|---:|---:|---:|---:|",
        ])
        for label, _, _ in STRENGTH_BINS:
            for h in HORIZONS:
                row = agg["strength_bins"][label][str(h)]
                lines.append(
                    f"| {label} | {h} | {pct(row['median_pair_mean_aligned_return'])} | "
                    f"{pct(row['median_pair_hit_rate'])} | {row['total_origins']} | "
                    f"{row['positive_pairs']}/{row['pair_count']} |"
                )
        lines.extend([
            "",
            "Continuous strength Spearman (pair median):",
            "",
            "| H | Median rho | Positive pair rhos |",
            "|---:|---:|---:|",
        ])
        for h in HORIZONS:
            row = agg["strength_spearman"][str(h)]
            lines.append(f"| {h} | {num(row['median_pair_rho'])} | {row['positive_pair_rho']}/{row['comparable_pairs']} |")

        lines.extend([
            "",
            f"## {engine} — Top2 >=90% by Formal relationship",
            "",
            "| Formal relationship | H | Median aligned return | Median hit rate | Origins |",
            "|---|---:|---:|---:|---:|",
        ])
        for category in ("formal_aligned", "formal_transition_or_neutral", "formal_opposite"):
            for h in HORIZONS:
                row = agg["formal_categories"][category][str(h)]
                lines.append(
                    f"| {category} | {h} | {pct(row['median_pair_mean_aligned_return'])} | "
                    f"{pct(row['median_pair_hit_rate'])} | {row['total_origins']} |"
                )

        lines.extend([
            "",
            "Formal adoption after non-aligned Top2 >=90%:",
            "",
            "| Origin relationship | Origins | Adopt <=5 | Adopt <=10 | Adopt <=20 | Median adoption lag |",
            "|---|---:|---:|---:|---:|---:|",
        ])
        for category in ("formal_transition_or_neutral", "formal_opposite"):
            row = agg["formal_adoption"][category]
            lines.append(
                f"| {category} | {row['total_origins']} | {pct(row['median_pair_adoption_rate_5'])} | "
                f"{pct(row['median_pair_adoption_rate_10'])} | {pct(row['median_pair_adoption_rate_20'])} | "
                f"{num(row['median_of_pair_median_adoption_lag'])} |"
            )

        lines.extend([
            "",
            f"## {engine} — 90% consensus persistence event sensitivity",
            "",
            "| Required streak | H | Median aligned return | Median hit rate | Origins |",
            "|---:|---:|---:|---:|---:|",
        ])
        for k in PERSISTENCE_LEVELS:
            for h in HORIZONS:
                row = agg["persistence"][str(k)]["horizons"][str(h)]
                lines.append(
                    f"| {k} | {h} | {pct(row['median_pair_mean_aligned_return'])} | "
                    f"{pct(row['median_pair_hit_rate'])} | {row['total_origins']} |"
                )
        lines.append("")

    lines.extend([
        "## Interpretation boundary",
        "",
        "Do not choose a threshold or persistence rule because one row looks best. The purpose is to determine whether a stable monotonic or Formal-lag structure exists at all. Any promising rule must be frozen before a new untouched sample is acquired.",
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
