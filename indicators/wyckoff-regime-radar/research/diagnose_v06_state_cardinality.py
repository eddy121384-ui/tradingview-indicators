#!/usr/bin/env python3
"""Compare 6/4/3 semantic state representations for Issue #57 Phase C.

All history used here is already observed/burned by Issue #55. This is a model-
development diagnostic, not an independent validation. No trading PnL is used.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import numpy as np

from diagnose_v06_boundary_sensitivity import PAIRS, _load_pair
from evaluate_regime_paths_pre_final import HORIZONS, future_metrics
from evaluate_state_separation_pre_final import eta_squared, spearman_from_stage_means
from generate_v06_phase_b_core import load_phase_b_namespace
from v06_live_window import live_window


HERE = Path(__file__).resolve().parent
MANIFEST = HERE / "data" / "issue-55-static-fx-canonical-manifest.json"
MIN_GROUP_N = 20

STATE_MAPS: dict[str, dict[int, int]] = {
    "six_state": {1: 1, 2: 2, 3: 3, 4: 4, 5: 5, 6: 6},
    "four_state": {1: 1, 3: 1, 2: 2, 4: 3, 6: 3, 5: 4},
    "three_state": {1: 1, 3: 1, 4: 1, 6: 1, 2: 2, 5: 3},
}
STATE_LABELS = {
    "six_state": {
        1: "Accumulation",
        2: "Markup",
        3: "Re-accumulation",
        4: "Distribution",
        5: "Markdown",
        6: "Re-distribution",
    },
    "four_state": {1: "Accumulation family", 2: "Markup", 3: "Distribution family", 4: "Markdown"},
    "three_state": {1: "Balance/Transition", 2: "Uptrend", 3: "Downtrend"},
}
SEGMENTS = ("development", "exploratory_oos", "final_oos")


def _map_states(formal: np.ndarray, mapping: dict[int, int]) -> np.ndarray:
    mapped = np.zeros_like(formal, dtype=int)
    for source, target in mapping.items():
        mapped[formal == source] = target
    return mapped


def _entropy_effective_count(mapped: np.ndarray, state_count: int) -> float:
    counts = np.array([np.sum(mapped == state) for state in range(1, state_count + 1)], dtype=float)
    total = float(np.sum(counts))
    if total <= 0.0:
        return 0.0
    probs = counts[counts > 0.0] / total
    entropy = -float(np.sum(probs * np.log(probs)))
    return float(np.exp(entropy))


def _occupancy(mapped: np.ndarray, start: int, end: int, state_count: int) -> dict[str, Any]:
    segment = mapped[start : end + 1]
    n = len(segment)
    shares = {str(state): float(np.mean(segment == state)) for state in range(1, state_count + 1)}
    return {
        "bars": n,
        "formal_zero_share": float(np.mean(segment == 0)) if n else None,
        "shares": shares,
        "populated_state_count_1pct": int(sum(share >= 0.01 for share in shares.values())),
        "populated_state_count_5pct": int(sum(share >= 0.05 for share in shares.values())),
        "effective_state_count": _entropy_effective_count(segment, state_count),
    }


def _horizon_summary(
    mapped: np.ndarray,
    metrics: dict[str, np.ndarray],
    start: int,
    end: int,
    horizon: int,
    state_count: int,
) -> dict[str, Any]:
    last_origin = end - horizon
    if last_origin < start:
        return {"retained_states": [], "state_means": {}, "eta_squared": {}}
    origin_mask = np.zeros(len(mapped), dtype=bool)
    origin_mask[start : last_origin + 1] = True
    valid = origin_mask & (mapped > 0) & np.isfinite(metrics["forward_return"])

    state_means: dict[str, dict[str, float | int | None]] = {}
    retained: list[int] = []
    for state in range(1, state_count + 1):
        mask = valid & (mapped == state)
        n = int(np.sum(mask))
        row: dict[str, float | int | None] = {"n": n}
        for metric in ("forward_return", "mfe", "mae", "realized_vol"):
            selected = metrics[metric][mask]
            selected = selected[np.isfinite(selected)]
            row[metric + "_mean"] = float(np.mean(selected)) if len(selected) else None
        state_means[str(state)] = row
        if n >= MIN_GROUP_N:
            retained.append(state)

    robust = valid & np.isin(mapped, retained)
    eta: dict[str, float | None] = {}
    for metric in ("forward_return", "mfe", "mae", "realized_vol"):
        mask = robust & np.isfinite(metrics[metric])
        eta[metric] = eta_squared(metrics[metric][mask], mapped[mask].astype(float))
    return {"retained_states": retained, "state_means": state_means, "eta_squared": eta}


def _occupancy_l1(left: dict[str, float], right: dict[str, float]) -> float:
    states = sorted(set(left) | set(right))
    return float(sum(abs(float(left.get(state, 0.0)) - float(right.get(state, 0.0))) for state in states))


def _segment_bounds(meta: dict[str, Any], live_start: int) -> dict[str, tuple[int, int]]:
    result: dict[str, tuple[int, int]] = {}
    for segment in SEGMENTS:
        split = meta["splits"][segment]
        start = max(int(split["start_index"]), live_start)
        end = int(split["end_index"])
        if start <= end:
            result[segment] = (start, end)
    return result


def analyze_pair(pair: str, frame, outputs, meta: dict[str, Any]) -> dict[str, Any]:
    _, live_meta = live_window(outputs)
    live_start = int(live_meta["live_start_index"])
    bounds = _segment_bounds(meta, live_start)
    formal = outputs["formal_id"].fillna(0).to_numpy(int)
    metrics_by_horizon = {h: future_metrics(frame, h) for h in HORIZONS}

    representations: dict[str, Any] = {}
    for name, mapping in STATE_MAPS.items():
        mapped = _map_states(formal, mapping)
        state_count = len(set(mapping.values()))
        segments: dict[str, Any] = {}
        for segment, (start, end) in bounds.items():
            occupancy = _occupancy(mapped, start, end, state_count)
            segments[segment] = {
                "start_index": start,
                "end_index": end,
                "occupancy": occupancy,
                "horizons": {
                    str(h): _horizon_summary(mapped, metrics_by_horizon[h], start, end, h, state_count)
                    for h in HORIZONS
                },
            }

        stability: dict[str, Any] = {}
        comparisons = (("development", "exploratory_oos"), ("exploratory_oos", "final_oos"))
        for left_name, right_name in comparisons:
            if left_name not in segments or right_name not in segments:
                continue
            key = f"{left_name}_to_{right_name}"
            stability[key] = {
                "occupancy_l1": _occupancy_l1(
                    segments[left_name]["occupancy"]["shares"],
                    segments[right_name]["occupancy"]["shares"],
                ),
                "horizons": {},
            }
            for h in HORIZONS:
                left_h = segments[left_name]["horizons"][str(h)]
                right_h = segments[right_name]["horizons"][str(h)]
                left_means = {
                    int(state): float(row["forward_return_mean"])
                    for state, row in left_h["state_means"].items()
                    if int(state) in left_h["retained_states"] and row["forward_return_mean"] is not None
                }
                right_means = {
                    int(state): float(row["forward_return_mean"])
                    for state, row in right_h["state_means"].items()
                    if int(state) in right_h["retained_states"] and row["forward_return_mean"] is not None
                }
                rank = spearman_from_stage_means(left_means, right_means)
                common = sorted(set(left_means) & set(right_means))
                same_sign = sum(
                    int(np.sign(left_means[state]) == np.sign(right_means[state])) for state in common
                )
                stability[key]["horizons"][str(h)] = {
                    "rank_rho": rank["rho"],
                    "common_state_count": len(common),
                    "same_sign_count": same_sign,
                    "same_sign_rate": same_sign / len(common) if common else None,
                }
        representations[name] = {
            "state_count": state_count,
            "labels": STATE_LABELS[name],
            "segments": segments,
            "stability": stability,
        }

    return {"pair": pair, "live_start": live_start, "representations": representations}


def _median(values: list[float]) -> float | None:
    return float(np.median(values)) if values else None


def run_cardinality_audit() -> dict[str, Any]:
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    compute = load_phase_b_namespace()["compute_price_only"]
    pairs: list[dict[str, Any]] = []
    for pair in PAIRS:
        frame = _load_pair(pair)
        outputs = compute(frame)
        pairs.append(analyze_pair(pair, frame, outputs, manifest["pairs"][pair]))

    summary: dict[str, Any] = {}
    for representation in STATE_MAPS:
        state_count = len(set(STATE_MAPS[representation].values()))
        rep_summary: dict[str, Any] = {"state_count": state_count, "segments": {}, "stability": {}}
        for segment in SEGMENTS:
            populated_1: list[float] = []
            populated_5: list[float] = []
            effective: list[float] = []
            eta_by_h = {str(h): [] for h in HORIZONS}
            complete = 0
            available = 0
            for pair_row in pairs:
                seg = pair_row["representations"][representation]["segments"].get(segment)
                if seg is None:
                    continue
                available += 1
                occ = seg["occupancy"]
                populated_1.append(float(occ["populated_state_count_1pct"]))
                populated_5.append(float(occ["populated_state_count_5pct"]))
                effective.append(float(occ["effective_state_count"]))
                complete += int(int(occ["populated_state_count_1pct"]) == state_count)
                for h in HORIZONS:
                    eta = seg["horizons"][str(h)]["eta_squared"].get("forward_return")
                    if eta is not None:
                        eta_by_h[str(h)].append(float(eta))
            rep_summary["segments"][segment] = {
                "pair_count": available,
                "median_populated_states_1pct": _median(populated_1),
                "median_populated_states_5pct": _median(populated_5),
                "median_effective_state_count": _median(effective),
                "all_states_populated_1pct_pair_rate": complete / available if available else None,
                "median_forward_return_eta_squared": {
                    str(h): _median(eta_by_h[str(h)]) for h in HORIZONS
                },
            }

        for comparison in ("development_to_exploratory_oos", "exploratory_oos_to_final_oos"):
            occ_shift: list[float] = []
            rho_by_h = {str(h): [] for h in HORIZONS}
            sign_num = {str(h): 0 for h in HORIZONS}
            sign_den = {str(h): 0 for h in HORIZONS}
            for pair_row in pairs:
                stability = pair_row["representations"][representation]["stability"].get(comparison)
                if stability is None:
                    continue
                occ_shift.append(float(stability["occupancy_l1"]))
                for h in HORIZONS:
                    row = stability["horizons"][str(h)]
                    if row["rank_rho"] is not None:
                        rho_by_h[str(h)].append(float(row["rank_rho"]))
                    sign_num[str(h)] += int(row["same_sign_count"])
                    sign_den[str(h)] += int(row["common_state_count"])
            rep_summary["stability"][comparison] = {
                "median_occupancy_l1_shift": _median(occ_shift),
                "median_forward_return_rank_rho": {
                    str(h): _median(rho_by_h[str(h)]) for h in HORIZONS
                },
                "forward_return_sign_stability_rate": {
                    str(h): (sign_num[str(h)] / sign_den[str(h)] if sign_den[str(h)] else None)
                    for h in HORIZONS
                },
            }
        summary[representation] = rep_summary

    return {
        "issue": 57,
        "phase": "C-state-cardinality",
        "scope": (
            "Already-observed/burned Issue #55 history using frozen v0.6 Phase-B 2x stale decay. "
            "6/4/3 semantic mappings were declared before this analysis. No PnL and no independent validation claim."
        ),
        "mappings": STATE_MAPS,
        "labels": STATE_LABELS,
        "pairs": pairs,
        "summary": summary,
    }


def main() -> None:
    print(json.dumps(run_cardinality_audit(), indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
