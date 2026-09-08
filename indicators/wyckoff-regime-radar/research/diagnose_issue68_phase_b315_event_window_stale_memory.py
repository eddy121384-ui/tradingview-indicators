#!/usr/bin/env python3
"""Issue #68 B3.15 event-window / stale-memory audit. Diagnostic only."""
from __future__ import annotations

import argparse
import json
from collections import Counter
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

import diagnose_issue66_reciprocal_symmetry as phasea
import diagnose_issue68_phase_b38_raw_feature_attribution as b38
import diagnose_issue68_phase_b310_s5_vs_s2_local_duel as b310
import diagnose_issue68_phase_b314_break_evidence_memory as b314

HERE = Path(__file__).resolve().parent
GATE = 0.99
BREAK_ID = list(b310.COMPONENTS).index("break")


def first_false_from(start: int, end: int, mask: np.ndarray) -> int | None:
    for i in range(start, end):
        if not bool(mask[i]):
            return i
    return None


def first_true_from(start: int, end: int, mask: np.ndarray) -> int | None:
    for i in range(start, end):
        if bool(mask[i]):
            return i
    return None


def find_event_ma_flip(
    t: int,
    ma_target: np.ndarray,
    oriented_direct: np.ndarray,
    warmup: int,
) -> tuple[int | None, str]:
    """Return event-related target-side MA flip and population label.

    If MA is target-side on t-1, return the start of that contiguous MA run.
    Otherwise search forward only while the fresh raw edge stays target-positive.
    """
    p = t - 1
    if bool(ma_target[p]):
        j = p
        while j > warmup and bool(ma_target[j - 1]):
            j -= 1
        return j, "MA_TARGET_AT_BLOCKER"

    j = t
    n = len(ma_target)
    while j < n and np.isfinite(oriented_direct[j]) and oriented_direct[j] > 0.0:
        if bool(ma_target[j]):
            return j, "PRE_MA_FLIP_AT_BLOCKER"
        j += 1
    return None, "PRE_MA_FLIP_AT_BLOCKER"


def measure_window(
    flip: int | None,
    ma_target: np.ndarray,
    old_range_mem: np.ndarray,
    new_range: np.ndarray,
    break_target_edge: np.ndarray,
) -> dict[str, Any]:
    if flip is None:
        return {
            "ma_flip_found": False,
            "ma_flip": None,
            "ma_run_end": None,
            "old_range_survival_bars": None,
            "old_range_survival_censored": True,
            "new_range_delay_bars": None,
            "new_range_delay_censored": True,
            "break_release_delay_bars": None,
            "break_release_delay_censored": True,
            "stale_overlap_bars": 0,
            "break_old_overlap_bars": 0,
            "break_target_overlap_bars": 0,
            "break_zero_overlap_bars": 0,
            "has_stale_overlap_break_old": False,
            "new_range_before_old_clear": None,
        }

    n = len(ma_target)
    end = flip
    while end < n and bool(ma_target[end]):
        end += 1

    old_clear = first_false_from(flip, end, old_range_mem)
    new_first = first_true_from(flip, end, new_range)
    break_release = None
    for i in range(flip, end):
        v = break_target_edge[i]
        if np.isfinite(v) and v > 0.0:
            break_release = i
            break

    idx = np.arange(flip, end, dtype=int)
    overlap = idx[old_range_mem[flip:end]]
    vals = break_target_edge[overlap] if len(overlap) else np.array([], dtype=float)
    old_n = int(np.sum(vals < 0.0))
    target_n = int(np.sum(vals > 0.0))
    zero_n = int(np.sum(vals == 0.0))

    return {
        "ma_flip_found": True,
        "ma_flip": int(flip),
        "ma_run_end": int(end),
        "old_range_survival_bars": None if old_clear is None else int(old_clear - flip),
        "old_range_survival_censored": old_clear is None,
        "new_range_delay_bars": None if new_first is None else int(new_first - flip),
        "new_range_delay_censored": new_first is None,
        "break_release_delay_bars": None if break_release is None else int(break_release - flip),
        "break_release_delay_censored": break_release is None,
        "stale_overlap_bars": int(len(overlap)),
        "break_old_overlap_bars": old_n,
        "break_target_overlap_bars": target_n,
        "break_zero_overlap_bars": zero_n,
        "has_stale_overlap_break_old": bool(old_n > 0),
        "new_range_before_old_clear": (
            None if new_first is None or old_clear is None else bool(new_first < old_clear)
        ),
    }


def audit_direction(model: pd.DataFrame, direction: int, warmup: int) -> dict[str, Any]:
    fresh = b38.fresh_pair_components(model)
    duel = b310.direction_duel_from_arrays(fresh["arrays"], direction, warmup)
    hand = duel["_arrays"]["handoff"]
    blocker = duel["_arrays"]["final_blocker_id"]
    events = np.flatnonzero(hand & (blocker == BREAK_ID))

    sides = b314.side_arrays(model, direction)
    logp = b314.f(model, "b314_log_price")
    malog = b314.f(model, "b314_ma_log")
    ma_target = logp > malog if direction == 1 else logp < malog
    old_range_mem = np.isfinite(sides["old"]["recent_range"]) & (sides["old"]["recent_range"] > 0.0)
    new_range = np.isfinite(sides["target"]["range"]) & (sides["target"]["range"] > 0.0)
    oriented_direct = direction * np.asarray(fresh["arrays"]["direct"], dtype=float)
    break_target_edge = direction * np.asarray(fresh["arrays"]["break"], dtype=float)

    rows: list[dict[str, Any]] = []
    population = Counter()
    for t in events:
        flip, pop = find_event_ma_flip(int(t), ma_target, oriented_direct, warmup)
        w = measure_window(flip, ma_target, old_range_mem, new_range, break_target_edge)
        population[pop] += 1
        rows.append(
            {
                "index": int(t),
                "population": pop,
                "ma_target_at_blocker": bool(ma_target[t - 1]),
                "old_range_memory_at_blocker": bool(old_range_mem[t - 1]),
                "new_range_at_blocker": bool(new_range[t - 1]),
                "break_old_at_blocker": bool(np.isfinite(break_target_edge[t - 1]) and break_target_edge[t - 1] < 0.0),
                **w,
            }
        )

    return {
        "direction": "bull_s5_to_s2" if direction == 1 else "bear_s2_to_s5",
        "break_final_blocker_events": int(len(events)),
        "expected_break_final_blocker_events": int(duel["final_blocker_counts"]["break"]),
        "population_counts": dict(population),
        "_events": rows,
    }


def _summary(values: list[int], censored: int) -> dict[str, Any]:
    if not values:
        return {"uncensored": 0, "censored": int(censored), "median": None, "p75": None, "max": None}
    a = np.asarray(values, dtype=float)
    return {
        "uncensored": int(len(values)),
        "censored": int(censored),
        "median": float(np.median(a)),
        "p75": float(np.percentile(a, 75)),
        "max": int(np.max(a)),
    }


def summarize_events(rows: list[dict[str, Any]]) -> dict[str, Any]:
    n = len(rows)
    stale_rows = [r for r in rows if r["population"] == "MA_TARGET_AT_BLOCKER"]
    flip_found = [r for r in rows if r["ma_flip_found"]]

    def timing(key: str, censor_key: str) -> dict[str, Any]:
        vals = [int(r[key]) for r in flip_found if r[key] is not None]
        cens = sum(int(bool(r[censor_key])) for r in flip_found)
        return _summary(vals, cens)

    overlap = sum(int(r["stale_overlap_bars"]) for r in flip_found)
    old_overlap = sum(int(r["break_old_overlap_bars"]) for r in flip_found)
    target_overlap = sum(int(r["break_target_overlap_bars"]) for r in flip_found)
    zero_overlap = sum(int(r["break_zero_overlap_bars"]) for r in flip_found)
    causal_event_n = sum(int(bool(r["has_stale_overlap_break_old"])) for r in stale_rows)
    compare = [r for r in flip_found if r["new_range_before_old_clear"] is not None]
    new_before = sum(int(bool(r["new_range_before_old_clear"])) for r in compare)

    return {
        "events": n,
        "ma_target_at_blocker": len(stale_rows),
        "ma_target_at_blocker_share": (len(stale_rows) / n if n else 0.0),
        "pre_ma_flip_at_blocker": n - len(stale_rows),
        "event_related_ma_flip_found": len(flip_found),
        "event_related_ma_flip_censored": n - len(flip_found),
        "old_range_survival": timing("old_range_survival_bars", "old_range_survival_censored"),
        "new_range_delay": timing("new_range_delay_bars", "new_range_delay_censored"),
        "break_release_delay": timing("break_release_delay_bars", "break_release_delay_censored"),
        "stale_overlap_bars": overlap,
        "break_old_overlap_bars": old_overlap,
        "break_target_overlap_bars": target_overlap,
        "break_zero_overlap_bars": zero_overlap,
        "break_old_overlap_share": (old_overlap / overlap if overlap else 0.0),
        "primary_stale_population_with_break_old_overlap": causal_event_n,
        "primary_stale_population_with_break_old_overlap_share": (
            causal_event_n / len(stale_rows) if stale_rows else 0.0
        ),
        "new_range_before_old_clear_comparable": len(compare),
        "new_range_before_old_clear": new_before,
        "new_range_before_old_clear_share": (new_before / len(compare) if compare else 0.0),
    }


def mirror_compare(a: dict[str, Any], c: dict[str, Any]) -> dict[str, Any]:
    amap = {x["index"]: x for x in a["_events"]}
    cmap = {x["index"]: x for x in c["_events"]}
    common = sorted(set(amap) & set(cmap))
    pop_matches = sum(int(amap[i]["population"] == cmap[i]["population"]) for i in common)

    timing_keys = ("old_range_survival_bars", "new_range_delay_bars", "break_release_delay_bars")
    timing_total = 0
    timing_matches = 0
    for i in common:
        for k in timing_keys:
            av = amap[i][k]
            cv = cmap[i][k]
            if av is not None and cv is not None:
                timing_total += 1
                timing_matches += int(av == cv)

    return {
        "events_a": len(amap),
        "events_b": len(cmap),
        "comparable_events": len(common),
        "population_matches": pop_matches,
        "population_agreement": (pop_matches / len(common) if common else 1.0),
        "timing_comparable": timing_total,
        "timing_matches": timing_matches,
        "timing_agreement": (timing_matches / timing_total if timing_total else 1.0),
    }


def clean_direction(x: dict[str, Any]) -> dict[str, Any]:
    rows = x["_events"]
    return {
        k: v for k, v in x.items() if k != "_events"
    } | {"summary": summarize_events(rows), "events": rows}


def analyze_pair(frame: pd.DataFrame) -> dict[str, Any]:
    inv = phasea.reciprocal_ohlc(frame)
    model, cfg = b314.compute(frame)
    imodel, icfg = b314.compute(inv)
    warmup = int(cfg.rank_len - 1)
    if warmup != int(icfg.rank_len - 1):
        raise AssertionError("warmup mismatch")

    bull = audit_direction(model, 1, warmup)
    bear = audit_direction(model, -1, warmup)
    ibull = audit_direction(imodel, 1, warmup)
    ibear = audit_direction(imodel, -1, warmup)

    return {
        "warmup": warmup,
        "bull": clean_direction(bull),
        "bear": clean_direction(bear),
        "mirror": {
            "bull_vs_inverse_bear": mirror_compare(bull, ibear),
            "bear_vs_inverse_bull": mirror_compare(bear, ibull),
        },
    }


def build_report() -> dict[str, Any]:
    pairs = {name: analyze_pair(frame) for name, frame in phasea.load_frozen_pairs().items()}
    all_rows: list[dict[str, Any]] = []
    reproduced = 0
    expected = 0
    minimum_pop = 1.0
    timing_matches = 0
    timing_comparable = 0
    per_pair: dict[str, Any] = {}

    for name, p in pairs.items():
        rows = []
        for side in ("bull", "bear"):
            x = p[side]
            reproduced += int(x["break_final_blocker_events"])
            expected += int(x["expected_break_final_blocker_events"])
            rows.extend(x["events"])
            all_rows.extend(x["events"])
        per_pair[name] = summarize_events(rows)
        for m in p["mirror"].values():
            minimum_pop = min(minimum_pop, float(m["population_agreement"]))
            timing_matches += int(m["timing_matches"])
            timing_comparable += int(m["timing_comparable"])

    agg = summarize_events(all_rows)
    agg["break_final_blocker_events"] = reproduced
    agg["expected_break_final_blocker_events"] = expected
    agg["event_reproduction_delta"] = reproduced - expected
    agg["minimum_population_mirror_agreement"] = minimum_pop
    agg["timing_mirror_matches"] = timing_matches
    agg["timing_mirror_comparable"] = timing_comparable
    agg["timing_mirror_agreement"] = timing_matches / timing_comparable if timing_comparable else 1.0

    gate = (
        agg["event_reproduction_delta"] == 0
        and agg["minimum_population_mirror_agreement"] >= GATE
        and agg["timing_mirror_agreement"] >= GATE
    )
    return {
        "issue": 68,
        "phase": "B3.15",
        "status": "EVENT_WINDOW_STALE_MEMORY_NO_PERFORMANCE",
        "primary_gate_pass": bool(gate),
        "aggregate": agg,
        "per_pair": per_pair,
        "pairs": pairs,
        "boundary": "Event-window timing attribution only; frozen C-2 and all classifier parameters remain unchanged.",
    }


def _fmt_timing(x: dict[str, Any]) -> str:
    if x["uncensored"] == 0:
        return f"no uncensored values; censored={x['censored']}"
    return (
        f"median={x['median']:.1f}, p75={x['p75']:.1f}, max={x['max']}, "
        f"uncensored={x['uncensored']}, censored={x['censored']}"
    )


def render_markdown(r: dict[str, Any]) -> str:
    a = r["aggregate"]
    lines = [
        "# Issue #68 Phase B3.15 — Event-Window / Stale-Memory Audit",
        "",
        "Status: **diagnostic only / frozen C-2 / no performance use**",
        "",
        f"Primary engineering gate: **{'PASS' if r['primary_gate_pass'] else 'FAIL'}**",
        f"- Break final-blocker events: **{a['break_final_blocker_events']}**",
        f"- mechanically expected from B3.14/B3.10: **{a['expected_break_final_blocker_events']}**",
        f"- reproduction delta: **{a['event_reproduction_delta']}**",
        f"- minimum reciprocal population-label agreement: **{100*a['minimum_population_mirror_agreement']:.3f}%**",
        f"- reciprocal uncensored timing agreement: **{100*a['timing_mirror_agreement']:.3f}%** ({a['timing_mirror_matches']}/{a['timing_mirror_comparable']})",
        "",
        "## Blocker clock split",
        "",
        f"- MA already target-side at blocker (`t-1`): **{a['ma_target_at_blocker']} / {a['events']} ({100*a['ma_target_at_blocker_share']:.1f}%)**",
        f"- PRE_MA_FLIP_AT_BLOCKER: **{a['pre_ma_flip_at_blocker']}**",
        f"- event-related MA flip found: **{a['event_related_ma_flip_found']}**; censored: **{a['event_related_ma_flip_censored']}**",
        "",
        "## Timing after event-related MA flip",
        "",
        f"- old range-memory survival: **{_fmt_timing(a['old_range_survival'])}**",
        f"- target range-evidence delay: **{_fmt_timing(a['new_range_delay'])}**",
        f"- Break release delay: **{_fmt_timing(a['break_release_delay'])}**",
        "",
        "## Stale overlap behavior",
        "",
        f"- stale-overlap bars (`MA target + old range memory`): **{a['stale_overlap_bars']}**",
        f"- Break still old-negative on stale-overlap bars: **{a['break_old_overlap_bars']} ({100*a['break_old_overlap_share']:.1f}%)**",
        f"- Break target-positive on stale-overlap bars: **{a['break_target_overlap_bars']}**",
        f"- Break zero on stale-overlap bars: **{a['break_zero_overlap_bars']}**",
        f"- primary stale-population events with at least one old-negative Break overlap: **{a['primary_stale_population_with_break_old_overlap']} / {a['ma_target_at_blocker']} ({100*a['primary_stale_population_with_break_old_overlap_share']:.1f}%)**",
        f"- target range appears before old memory clears: **{a['new_range_before_old_clear']} / {a['new_range_before_old_clear_comparable']} ({100*a['new_range_before_old_clear_share']:.1f}%)**",
        "",
        "## Per-pair event-window summary",
        "",
        "| Pair | Events | MA target @ blocker | Share | Stale overlap bars | Break-old overlap share |",
        "|---|---:|---:|---:|---:|---:|",
    ]
    for name, x in r["per_pair"].items():
        lines.append(
            f"| {name} | {x['events']} | {x['ma_target_at_blocker']} | {100*x['ma_target_at_blocker_share']:.1f}% | {x['stale_overlap_bars']} | {100*x['break_old_overlap_share']:.1f}% |"
        )
    lines += ["", "## Boundary", "", r["boundary"], ""]
    return "\n".join(lines)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--report-json", type=Path, required=True)
    ap.add_argument("--report-md", type=Path, required=True)
    args = ap.parse_args()
    report = build_report()
    args.report_json.parent.mkdir(parents=True, exist_ok=True)
    args.report_md.parent.mkdir(parents=True, exist_ok=True)
    args.report_json.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
    args.report_md.write_text(render_markdown(report), encoding="utf-8")
    if not report["primary_gate_pass"]:
        raise SystemExit("B3.15 engineering gate failed")
    print(render_markdown(report))


if __name__ == "__main__":
    main()
