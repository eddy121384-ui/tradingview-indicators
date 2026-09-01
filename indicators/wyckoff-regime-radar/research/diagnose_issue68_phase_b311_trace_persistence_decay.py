#!/usr/bin/env python3
"""Issue #68 B3.11 Trace persistence / decay audit. Diagnostic only; no model changes."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

import diagnose_issue66_reciprocal_symmetry as phasea
import diagnose_issue68_phase_b38_raw_feature_attribution as b38

HERE = Path(__file__).resolve().parent
OTHER_COMPONENTS = ("break", "heat", "structure", "extension", "continuation")
RECON_TOL = 1e-9
MIRROR_GATE = 0.99


def _f(model: pd.DataFrame, key: str) -> np.ndarray:
    return pd.to_numeric(model[key], errors="coerce").to_numpy(float)


def rolling_max_source_age(values: np.ndarray, trace: np.ndarray, window: int) -> np.ndarray:
    """Age of the most-recent observation supplying a fixed-window rolling maximum."""
    v = np.asarray(values, dtype=float)
    tr = np.asarray(trace, dtype=float)
    out = np.full(len(v), np.nan, dtype=float)
    for t in range(len(v)):
        if not np.isfinite(tr[t]) or t < window - 1:
            continue
        start = t - window + 1
        seg = v[start : t + 1]
        finite = np.isfinite(seg)
        if not np.any(finite):
            continue
        matches = np.flatnonzero(finite & np.isclose(seg, tr[t], rtol=1e-12, atol=1e-12))
        if len(matches):
            source = start + int(matches[-1])  # most-recent equal maximum wins attribution tie.
        else:
            # Defensive fallback for minute floating transport differences.
            safe = np.where(finite, seg, -np.inf)
            source = start + int(np.argmax(safe))
        out[t] = float(t - source)
    return out


def _runs(mask: np.ndarray) -> list[int]:
    result: list[int] = []
    run = 0
    for flag in np.asarray(mask, dtype=bool):
        if flag:
            run += 1
        elif run:
            result.append(run)
            run = 0
    if run:
        result.append(run)
    return result


def _stats(values: list[float] | np.ndarray) -> dict[str, float | int | None]:
    arr = np.asarray(values, dtype=float)
    arr = arr[np.isfinite(arr)]
    if not len(arr):
        return {"n": 0, "median": None, "p90": None, "max": None}
    return {
        "n": int(len(arr)),
        "median": float(np.median(arr)),
        "p90": float(np.percentile(arr, 90)),
        "max": float(np.max(arr)),
    }


def direction_trace_audit(model: pd.DataFrame, direction: int, warmup: int, window: int) -> dict[str, Any]:
    if direction not in (1, -1):
        raise ValueError(direction)

    fresh = b38.fresh_pair_components(model)["arrays"]
    matrix = np.column_stack([np.asarray(fresh[name], dtype=float) for name in OTHER_COMPONENTS])
    trace_edge = np.asarray(fresh["trace"], dtype=float)
    direct = np.asarray(fresh["direct"], dtype=float)
    reconstructed = np.asarray(fresh["reconstructed"], dtype=float)

    acc_raw0 = _f(model, "b38_acc_raw0")
    dist_raw0 = _f(model, "b38_dist_raw0")
    acc_trace = _f(model, "b38_acc_trace")
    dist_trace = _f(model, "b38_dist_trace")
    acc_age = rolling_max_source_age(acc_raw0, acc_trace, window)
    dist_age = rolling_max_source_age(dist_raw0, dist_trace, window)

    finite = np.all(np.isfinite(matrix), axis=1) & np.isfinite(trace_edge) & np.isfinite(direct)
    scored = finite.copy()
    scored[:warmup] = False

    oriented_other = direction * matrix
    oriented_trace = direction * trace_edge
    oriented_direct = direction * direct
    oriented_no_trace = np.sum(oriented_other, axis=1)

    other5_consensus = scored & np.all(oriented_other > 0.0, axis=1)
    trace_opposes = scored & (oriented_trace < 0.0)
    stale = other5_consensus & trace_opposes
    full_target = scored & (oriented_direct > 0.0)
    no_trace_target = scored & (oriented_no_trace > 0.0)

    sign_flip = scored & (full_target != no_trace_target)
    trace_blocks = scored & no_trace_target & ~full_target
    trace_rescues = scored & ~no_trace_target & full_target
    unexplained_flip = sign_flip & ~(trace_blocks | trace_rescues)

    stale_blocks = stale & ~full_target
    stale_visible_only = stale & full_target
    stale_runs = _runs(stale)
    opposing_age = dist_age if direction == 1 else acc_age
    stale_ages = opposing_age[stale & np.isfinite(opposing_age)].tolist()

    prev_scored = np.roll(scored, 1)
    prev_scored[0] = False
    prev_direct = np.roll(oriented_direct, 1)
    prev_direct[0] = np.nan
    handoff = scored & prev_scored & (prev_direct <= 0.0) & (oriented_direct > 0.0)
    handoff_idx = np.flatnonzero(handoff)
    trace_opp_prev = 0
    trace_opp_now = 0
    handoff_prev_ages: list[float] = []
    for t in handoff_idx:
        if oriented_trace[t - 1] < 0.0:
            trace_opp_prev += 1
            if np.isfinite(opposing_age[t - 1]):
                handoff_prev_ages.append(float(opposing_age[t - 1]))
        if oriented_trace[t] < 0.0:
            trace_opp_now += 1

    recon_err = np.abs(reconstructed - direct)
    return {
        "direction": "bull_s5_to_s2" if direction == 1 else "bear_s2_to_s5",
        "usable_bars": int(np.sum(scored)),
        "other5_consensus_bars": int(np.sum(other5_consensus)),
        "stale_opposition_bars": int(np.sum(stale)),
        "stale_opposition_share_of_other5_consensus": float(np.sum(stale) / np.sum(other5_consensus)) if np.sum(other5_consensus) else 0.0,
        "stale_opposition_runs": _stats(stale_runs),
        "stale_opposing_trace_source_age": _stats(stale_ages),
        "stale_visible_only_bars": int(np.sum(stale_visible_only)),
        "stale_raw_blocking_bars": int(np.sum(stale_blocks)),
        "stale_raw_blocking_share": float(np.sum(stale_blocks) / np.sum(stale)) if np.sum(stale) else 0.0,
        "full_vs_no_trace_sign_flip_bars": int(np.sum(sign_flip)),
        "trace_blocks_target_bars": int(np.sum(trace_blocks)),
        "trace_rescues_target_bars": int(np.sum(trace_rescues)),
        "unexplained_sign_flip_bars": int(np.sum(unexplained_flip)),
        "handoff_events": int(len(handoff_idx)),
        "trace_opposes_at_handoff_t_minus_1": trace_opp_prev,
        "trace_opposes_at_handoff_t": trace_opp_now,
        "trace_opposition_share_at_handoff_t_minus_1": float(trace_opp_prev / len(handoff_idx)) if len(handoff_idx) else 0.0,
        "trace_opposition_share_at_handoff_t": float(trace_opp_now / len(handoff_idx)) if len(handoff_idx) else 0.0,
        "opposing_trace_source_age_at_handoff_t_minus_1": _stats(handoff_prev_ages),
        "max_reconstruction_error": float(np.nanmax(recon_err[finite])) if np.any(finite) else 0.0,
        "_arrays": {
            "stale": stale,
            "sign_flip": sign_flip,
            "handoff": handoff,
            "acc_age": acc_age,
            "dist_age": dist_age,
        },
        "_private": {
            "stale_runs": stale_runs,
            "stale_ages": stale_ages,
            "handoff_prev_ages": handoff_prev_ages,
        },
    }


def _bool_compare(a: np.ndarray, b: np.ndarray, warmup: int) -> dict[str, Any]:
    x = np.asarray(a, dtype=bool)[warmup:]
    y = np.asarray(b, dtype=bool)[warmup:]
    good = x == y
    return {
        "bars": int(len(x)),
        "matches": int(np.sum(good)),
        "agreement": float(np.mean(good)) if len(x) else 1.0,
        "mismatches": int(np.sum(~good)),
    }


def _strip(x: dict[str, Any]) -> dict[str, Any]:
    return {k: v for k, v in x.items() if k not in ("_arrays", "_private")}


def analyze_pair(frame: pd.DataFrame) -> dict[str, Any]:
    inv = phasea.reciprocal_ohlc(frame)
    model, cfg = b38._compute(frame)
    inv_model, inv_cfg = b38._compute(inv)
    warmup = int(cfg.rank_len - 1)
    if warmup != int(inv_cfg.rank_len - 1):
        raise AssertionError("warmup mismatch")
    window = int(cfg.absorb_len)
    if window != int(inv_cfg.absorb_len):
        raise AssertionError("trace-window mismatch")

    bull = direction_trace_audit(model, 1, warmup, window)
    bear = direction_trace_audit(model, -1, warmup, window)
    inv_bull = direction_trace_audit(inv_model, 1, warmup, window)
    inv_bear = direction_trace_audit(inv_model, -1, warmup, window)

    mirror: dict[str, Any] = {}
    for label, a, b in (
        ("bull_vs_inverse_bear", bull, inv_bear),
        ("bear_vs_inverse_bull", bear, inv_bull),
    ):
        mirror[label] = {
            "stale": _bool_compare(a["_arrays"]["stale"], b["_arrays"]["stale"], warmup),
            "sign_flip": _bool_compare(a["_arrays"]["sign_flip"], b["_arrays"]["sign_flip"], warmup),
            "handoff": _bool_compare(a["_arrays"]["handoff"], b["_arrays"]["handoff"], warmup),
        }

    return {
        "warmup": warmup,
        "trace_window": window,
        "bull": _strip(bull),
        "bear": _strip(bear),
        "inverse_bull": _strip(inv_bull),
        "inverse_bear": _strip(inv_bear),
        "mirror": mirror,
        "_private": {
            "bull": bull["_private"],
            "bear": bear["_private"],
        },
    }


def build_report() -> dict[str, Any]:
    pairs = {name: analyze_pair(frame) for name, frame in phasea.load_frozen_pairs().items()}
    agg: dict[str, Any] = {
        "usable_direction_observations": 0,
        "other5_consensus_bars": 0,
        "stale_opposition_bars": 0,
        "stale_visible_only_bars": 0,
        "stale_raw_blocking_bars": 0,
        "full_vs_no_trace_sign_flip_bars": 0,
        "trace_blocks_target_bars": 0,
        "trace_rescues_target_bars": 0,
        "unexplained_sign_flip_bars": 0,
        "handoff_events": 0,
        "trace_opposes_handoff_prev": 0,
        "trace_opposes_handoff_now": 0,
        "max_reconstruction_error": 0.0,
        "pooled_stale_matches": 0,
        "pooled_stale_bars": 0,
        "pooled_sign_flip_matches": 0,
        "pooled_sign_flip_bars": 0,
        "minimum_handoff_event_agreement": 1.0,
    }
    all_runs: list[float] = []
    all_ages: list[float] = []
    all_handoff_ages: list[float] = []

    for p in pairs.values():
        for side in ("bull", "bear"):
            x = p[side]
            agg["usable_direction_observations"] += x["usable_bars"]
            agg["other5_consensus_bars"] += x["other5_consensus_bars"]
            agg["stale_opposition_bars"] += x["stale_opposition_bars"]
            agg["stale_visible_only_bars"] += x["stale_visible_only_bars"]
            agg["stale_raw_blocking_bars"] += x["stale_raw_blocking_bars"]
            agg["full_vs_no_trace_sign_flip_bars"] += x["full_vs_no_trace_sign_flip_bars"]
            agg["trace_blocks_target_bars"] += x["trace_blocks_target_bars"]
            agg["trace_rescues_target_bars"] += x["trace_rescues_target_bars"]
            agg["unexplained_sign_flip_bars"] += x["unexplained_sign_flip_bars"]
            agg["handoff_events"] += x["handoff_events"]
            agg["trace_opposes_handoff_prev"] += x["trace_opposes_at_handoff_t_minus_1"]
            agg["trace_opposes_handoff_now"] += x["trace_opposes_at_handoff_t"]
            agg["max_reconstruction_error"] = max(agg["max_reconstruction_error"], x["max_reconstruction_error"])
            priv = p["_private"][side]
            all_runs.extend(priv["stale_runs"])
            all_ages.extend(priv["stale_ages"])
            all_handoff_ages.extend(priv["handoff_prev_ages"])
        for m in p["mirror"].values():
            agg["pooled_stale_matches"] += m["stale"]["matches"]
            agg["pooled_stale_bars"] += m["stale"]["bars"]
            agg["pooled_sign_flip_matches"] += m["sign_flip"]["matches"]
            agg["pooled_sign_flip_bars"] += m["sign_flip"]["bars"]
            agg["minimum_handoff_event_agreement"] = min(agg["minimum_handoff_event_agreement"], m["handoff"]["agreement"])

    agg["stale_opposition_runs"] = _stats(all_runs)
    agg["stale_opposing_trace_source_age"] = _stats(all_ages)
    agg["opposing_trace_source_age_at_handoff_t_minus_1"] = _stats(all_handoff_ages)
    agg["stale_raw_blocking_share"] = agg["stale_raw_blocking_bars"] / agg["stale_opposition_bars"] if agg["stale_opposition_bars"] else 0.0
    agg["trace_opposition_share_at_handoff_t_minus_1"] = agg["trace_opposes_handoff_prev"] / agg["handoff_events"] if agg["handoff_events"] else 0.0
    agg["trace_opposition_share_at_handoff_t"] = agg["trace_opposes_handoff_now"] / agg["handoff_events"] if agg["handoff_events"] else 0.0
    agg["pooled_stale_mirror_agreement"] = agg["pooled_stale_matches"] / agg["pooled_stale_bars"] if agg["pooled_stale_bars"] else 1.0
    agg["pooled_sign_flip_mirror_agreement"] = agg["pooled_sign_flip_matches"] / agg["pooled_sign_flip_bars"] if agg["pooled_sign_flip_bars"] else 1.0

    primary = (
        agg["max_reconstruction_error"] <= RECON_TOL
        and agg["pooled_stale_mirror_agreement"] >= MIRROR_GATE
        and agg["pooled_sign_flip_mirror_agreement"] >= MIRROR_GATE
        and agg["minimum_handoff_event_agreement"] >= MIRROR_GATE
        and agg["unexplained_sign_flip_bars"] == 0
    )
    clean_pairs = {name: {k: v for k, v in p.items() if k != "_private"} for name, p in pairs.items()}
    return {
        "schema_version": 1,
        "issue": 68,
        "phase": "B3.11",
        "status": "TRACE_PERSISTENCE_DECAY_AUDIT_NO_PERFORMANCE",
        "primary_gate_pass": bool(primary),
        "aggregate": agg,
        "pairs": clean_pairs,
        "boundary": "Frozen 50-bar rolling-max Trace attribution only; no Trace length/weight/decay/reset or model rule is changed.",
    }


def render_markdown(r: dict[str, Any]) -> str:
    a = r["aggregate"]
    rs = a["stale_opposition_runs"]
    ages = a["stale_opposing_trace_source_age"]
    ha = a["opposing_trace_source_age_at_handoff_t_minus_1"]
    lines = [
        "# Issue #68 Phase B3.11 — Trace Persistence / Decay Audit",
        "",
        "Status: **diagnostic only / frozen C-2 / no performance use**",
        "",
        f"Primary engineering gate: **{'PASS' if r['primary_gate_pass'] else 'FAIL'}**",
        f"- stale-opposition bars: **{a['stale_opposition_bars']}** / other-five-consensus **{a['other5_consensus_bars']}**",
        f"- stale Trace that actually keeps total raw on old side: **{a['stale_raw_blocking_bars']}** ({100*a['stale_raw_blocking_share']:.2f}% of stale-opposition bars)",
        f"- all full-vs-no-Trace sign flips: **{a['full_vs_no_trace_sign_flip_bars']}** (blocks target {a['trace_blocks_target_bars']}, rescues target {a['trace_rescues_target_bars']})",
        f"- unexplained sign flips: **{a['unexplained_sign_flip_bars']}**",
        f"- stale run length: median **{rs['median']}**, p90 **{rs['p90']}**, max **{rs['max']}** bars",
        f"- opposing Trace source age on stale bars: median **{ages['median']}**, p90 **{ages['p90']}**, max **{ages['max']}** bars",
        f"- exact raw handoffs: **{a['handoff_events']}**; Trace opposed at t-1 **{a['trace_opposes_handoff_prev']}** ({100*a['trace_opposition_share_at_handoff_t_minus_1']:.1f}%), at t **{a['trace_opposes_handoff_now']}** ({100*a['trace_opposition_share_at_handoff_t']:.1f}%)",
        f"- opposing Trace source age at handoff t-1: median **{ha['median']}**, p90 **{ha['p90']}**, max **{ha['max']}** bars",
        f"- max six-component reconstruction error: **{a['max_reconstruction_error']:.3e}**",
        f"- pooled stale-opposition reciprocal agreement: **{100*a['pooled_stale_mirror_agreement']:.3f}%**",
        f"- pooled full-vs-no-Trace sign-flip reciprocal agreement: **{100*a['pooled_sign_flip_mirror_agreement']:.3f}%**",
        f"- minimum reciprocal exact-handoff agreement: **{100*a['minimum_handoff_event_agreement']:.3f}%**",
        "",
        "## Per-pair Bull diagnostic",
        "",
        "| Pair | Stale bars | Stale blocks raw | Full/no-Trace flips | Handoffs | Trace opposes t-1 |",
        "|---|---:|---:|---:|---:|---:|",
    ]
    for pair, p in r["pairs"].items():
        b = p["bull"]
        lines.append(
            f"| {pair} | {b['stale_opposition_bars']} | {b['stale_raw_blocking_bars']} | {b['full_vs_no_trace_sign_flip_bars']} | {b['handoff_events']} | {b['trace_opposes_at_handoff_t_minus_1']} |"
        )
    lines += ["", "## Boundary", "", r["boundary"], ""]
    return "\n".join(lines)


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser()
    p.add_argument("--report-json", type=Path)
    p.add_argument("--report-md", type=Path)
    return p.parse_args()


def main() -> None:
    args = parse_args()
    report = build_report()
    if args.report_json:
        args.report_json.parent.mkdir(parents=True, exist_ok=True)
        args.report_json.write_text(json.dumps(report, indent=2, sort_keys=True), encoding="utf-8")
    if args.report_md:
        args.report_md.parent.mkdir(parents=True, exist_ok=True)
        args.report_md.write_text(render_markdown(report), encoding="utf-8")
    print(render_markdown(report))
    if not report["primary_gate_pass"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
