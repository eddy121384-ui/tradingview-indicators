#!/usr/bin/env python3
"""Issue #68 B3.14 Break evidence-memory audit. Diagnostic only."""
from __future__ import annotations

import argparse
import json
import sys
import types
from collections import Counter
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

import diagnose_issue66_reciprocal_symmetry as phasea
import diagnose_issue68_phase_b38_raw_feature_attribution as b38
import diagnose_issue68_phase_b310_s5_vs_s2_local_duel as b310

HERE = Path(__file__).resolve().parent
GATE = 0.99
BREAK_ID = list(b310.COMPONENTS).index("break")
ANCHOR = b38.INSTRUMENT_ANCHOR
INSERT = '''        "b314_breakout_range_evidence": breakout_range_evidence,
        "b314_breakout_ma_evidence": breakout_ma_evidence,
        "b314_breakout_mode_up": breakout_mode_up,
        "b314_breakdown_range_evidence": breakdown_range_evidence,
        "b314_breakdown_ma_evidence": breakdown_ma_evidence,
        "b314_breakdown_mode_dn": breakdown_mode_dn,
        "b314_recent_range_break_up_strength": recent_range_break_up_strength,
        "b314_recent_range_break_dn_strength": recent_range_break_dn_strength,
        "b314_recent_ma_cross_up": recent_ma_cross_up,
        "b314_recent_ma_cross_dn": recent_ma_cross_dn,
        "b314_log_price": log_price,
        "b314_ma_log": ma_log,
'''


def load_namespace() -> dict[str, object]:
    source = b38.render_phase_c2_source()
    if source.count(ANCHOR) != 1:
        raise RuntimeError(f"expected one diagnostic anchor; found {source.count(ANCHOR)}")
    source = source.replace(ANCHOR, b38.INSTRUMENT_INSERT + INSERT + ANCHOR, 1)
    name = "wyckoff_issue68_b314_instrumented_c2"
    module = types.ModuleType(name)
    module.__file__ = str(HERE / "generated" / "wyckoff-issue68-b314-instrumented-c2.py")
    module.__package__ = None
    sys.modules[name] = module
    exec(compile(source, module.__file__, "exec"), module.__dict__)
    return module.__dict__


def compute(frame: pd.DataFrame):
    ns = load_namespace()
    cfg = ns["PriceOnlyConfig"]()
    return ns["compute_price_only"](frame.copy(), cfg), cfg


def f(model: pd.DataFrame, key: str) -> np.ndarray:
    return pd.to_numeric(model[key], errors="coerce").to_numpy(float)


def b(model: pd.DataFrame, key: str) -> np.ndarray:
    s = model[key]
    if s.dtype == bool:
        return s.to_numpy(bool)
    return s.fillna(False).astype(bool).to_numpy()


def source_family(mode: bool, range_ev: float, ma_ev: float, tol: float = 1e-12) -> str:
    if mode:
        return "mode"
    r = float(range_ev) if np.isfinite(range_ev) else 0.0
    m = float(ma_ev) if np.isfinite(ma_ev) else 0.0
    if r <= tol and m <= tol:
        return "none"
    if abs(r - m) <= tol:
        return "tie"
    return "range" if r > m else "ma"


def side_arrays(model: pd.DataFrame, direction: int) -> dict[str, np.ndarray]:
    up = {
        "range": f(model, "b314_breakout_range_evidence"),
        "ma": f(model, "b314_breakout_ma_evidence"),
        "mode": b(model, "b314_breakout_mode_up"),
        "recent_range": f(model, "b314_recent_range_break_up_strength"),
        "recent_ma": b(model, "b314_recent_ma_cross_up"),
    }
    dn = {
        "range": f(model, "b314_breakdown_range_evidence"),
        "ma": f(model, "b314_breakdown_ma_evidence"),
        "mode": b(model, "b314_breakdown_mode_dn"),
        "recent_range": f(model, "b314_recent_range_break_dn_strength"),
        "recent_ma": b(model, "b314_recent_ma_cross_dn"),
    }
    return {"target": up if direction == 1 else dn, "old": dn if direction == 1 else up}


def audit_direction(model: pd.DataFrame, direction: int, warmup: int) -> dict[str, Any]:
    fresh = b38.fresh_pair_components(model)
    duel = b310.direction_duel_from_arrays(fresh["arrays"], direction, warmup)
    hand = duel["_arrays"]["handoff"]
    blocker = duel["_arrays"]["final_blocker_id"]
    events = np.flatnonzero(hand & (blocker == BREAK_ID))
    expected_events = int(duel["final_blocker_counts"]["break"])
    sides = side_arrays(model, direction)
    logp = f(model, "b314_log_price")
    malog = f(model, "b314_ma_log")

    labels = {
        "old_memory_active": 0,
        "old_range_memory_active": 0,
        "old_ma_memory_active": 0,
        "old_mode_active": 0,
        "new_range_present": 0,
        "new_ma_present": 0,
        "new_mode_active": 0,
        "current_ma_target_side": 0,
        "current_ma_target_side_and_old_memory": 0,
    }
    target_sources: Counter[str] = Counter()
    old_sources: Counter[str] = Counter()
    source_pairs: Counter[str] = Counter()
    event_rows: list[dict[str, Any]] = []

    for t in events:
        p = int(t - 1)
        target = sides["target"]
        old = sides["old"]
        old_range_mem = bool(np.isfinite(old["recent_range"][p]) and old["recent_range"][p] > 0.0)
        old_ma_mem = bool(old["recent_ma"][p])
        old_mem = old_range_mem or old_ma_mem
        old_mode = bool(old["mode"][p])
        new_range = bool(np.isfinite(target["range"][p]) and target["range"][p] > 0.0)
        new_ma = bool(np.isfinite(target["ma"][p]) and target["ma"][p] > 0.0)
        new_mode = bool(target["mode"][p])
        ma_target = bool(logp[p] > malog[p]) if direction == 1 else bool(logp[p] < malog[p])
        ts = source_family(new_mode, target["range"][p], target["ma"][p])
        os = source_family(old_mode, old["range"][p], old["ma"][p])

        vals = {
            "old_memory_active": old_mem,
            "old_range_memory_active": old_range_mem,
            "old_ma_memory_active": old_ma_mem,
            "old_mode_active": old_mode,
            "new_range_present": new_range,
            "new_ma_present": new_ma,
            "new_mode_active": new_mode,
            "current_ma_target_side": ma_target,
            "current_ma_target_side_and_old_memory": ma_target and old_mem,
        }
        for k, v in vals.items():
            labels[k] += int(v)
        target_sources[ts] += 1
        old_sources[os] += 1
        source_pairs[f"{ts}->{os}"] += 1
        event_rows.append({"index": int(t), **vals, "target_source": ts, "old_source": os})

    n = len(events)
    return {
        "direction": "bull_s5_to_s2" if direction == 1 else "bear_s2_to_s5",
        "break_final_blocker_events": n,
        "expected_break_final_blocker_events": expected_events,
        "event_reproduction_delta": int(n - expected_events),
        "labels": {k: {"count": v, "share": (v / n if n else 0.0)} for k, v in labels.items()},
        "target_source_counts": dict(target_sources),
        "old_source_counts": dict(old_sources),
        "source_pair_counts": dict(source_pairs),
        "_arrays": {"handoff": hand, "blocker": blocker},
        "_events": event_rows,
    }


def compare_events(a: dict[str, Any], c: dict[str, Any]) -> dict[str, Any]:
    amap = {x["index"]: x for x in a["_events"]}
    cmap = {x["index"]: x for x in c["_events"]}
    common = sorted(set(amap) & set(cmap))
    bool_keys = [
        "old_memory_active", "old_range_memory_active", "old_ma_memory_active",
        "old_mode_active", "new_range_present", "new_ma_present", "new_mode_active",
        "current_ma_target_side", "current_ma_target_side_and_old_memory",
    ]
    boolean_total = len(common) * len(bool_keys)
    boolean_matches = sum(int(amap[i][k] == cmap[i][k]) for i in common for k in bool_keys)
    non_tie = [
        i for i in common
        if amap[i]["target_source"] != "tie" and amap[i]["old_source"] != "tie"
        and cmap[i]["target_source"] != "tie" and cmap[i]["old_source"] != "tie"
    ]
    source_matches = sum(
        int(amap[i]["target_source"] == cmap[i]["target_source"] and amap[i]["old_source"] == cmap[i]["old_source"])
        for i in non_tie
    )
    return {
        "events_a": len(amap),
        "events_b": len(cmap),
        "comparable_events": len(common),
        "boolean_matches": boolean_matches,
        "boolean_total": boolean_total,
        "boolean_agreement": boolean_matches / boolean_total if boolean_total else 1.0,
        "source_comparable_non_tie": len(non_tie),
        "source_matches": source_matches,
        "source_agreement": source_matches / len(non_tie) if non_tie else 1.0,
    }


def clean(x: dict[str, Any]) -> dict[str, Any]:
    return {k: v for k, v in x.items() if k not in ("_arrays", "_events")}


def analyze_pair(frame: pd.DataFrame) -> dict[str, Any]:
    inv = phasea.reciprocal_ohlc(frame)
    model, cfg = compute(frame)
    imodel, icfg = compute(inv)
    warmup = int(cfg.rank_len - 1)
    if warmup != int(icfg.rank_len - 1):
        raise AssertionError("warmup mismatch")
    bull = audit_direction(model, 1, warmup)
    bear = audit_direction(model, -1, warmup)
    ibull = audit_direction(imodel, 1, warmup)
    ibear = audit_direction(imodel, -1, warmup)
    return {
        "warmup": warmup,
        "bull": clean(bull),
        "bear": clean(bear),
        "mirror": {
            "bull_vs_inverse_bear": compare_events(bull, ibear),
            "bear_vs_inverse_bull": compare_events(bear, ibull),
        },
    }


def build_report() -> dict[str, Any]:
    pairs = {name: analyze_pair(frame) for name, frame in phasea.load_frozen_pairs().items()}
    agg: dict[str, Any] = {
        "break_final_blocker_events": 0,
        "expected_break_final_blocker_events": 0,
        "event_reproduction_abs_delta": 0,
        "label_counts": Counter(),
        "target_sources": Counter(),
        "old_sources": Counter(),
        "source_pairs": Counter(),
        "minimum_boolean_mirror_agreement": 1.0,
        "pooled_source_matches": 0,
        "pooled_source_comparable": 0,
    }
    for p in pairs.values():
        for side in ("bull", "bear"):
            x = p[side]
            n = int(x["break_final_blocker_events"])
            agg["break_final_blocker_events"] += n
            agg["expected_break_final_blocker_events"] += int(x["expected_break_final_blocker_events"])
            agg["event_reproduction_abs_delta"] += abs(int(x["event_reproduction_delta"]))
            for k, v in x["labels"].items():
                agg["label_counts"][k] += int(v["count"])
            agg["target_sources"].update(x["target_source_counts"])
            agg["old_sources"].update(x["old_source_counts"])
            agg["source_pairs"].update(x["source_pair_counts"])
        for m in p["mirror"].values():
            agg["minimum_boolean_mirror_agreement"] = min(
                agg["minimum_boolean_mirror_agreement"], float(m["boolean_agreement"])
            )
            agg["pooled_source_matches"] += int(m["source_matches"])
            agg["pooled_source_comparable"] += int(m["source_comparable_non_tie"])

    n = int(agg["break_final_blocker_events"])
    counts = dict(agg["label_counts"])
    agg["label_counts"] = counts
    agg["label_shares"] = {k: (v / n if n else 0.0) for k, v in counts.items()}
    agg["target_sources"] = dict(agg["target_sources"])
    agg["old_sources"] = dict(agg["old_sources"])
    agg["source_pairs"] = dict(agg["source_pairs"])
    c = int(agg["pooled_source_comparable"])
    agg["pooled_source_agreement"] = agg["pooled_source_matches"] / c if c else 1.0
    primary = (
        agg["event_reproduction_abs_delta"] == 0
        and agg["minimum_boolean_mirror_agreement"] >= GATE
        and agg["pooled_source_agreement"] >= GATE
    )
    return {
        "issue": 68,
        "phase": "B3.14",
        "status": "BREAK_EVIDENCE_MEMORY_NO_PERFORMANCE",
        "primary_gate_pass": bool(primary),
        "aggregate": agg,
        "pairs": pairs,
        "boundary": "Break source/memory attribution only; no C-2 or performance rule changed.",
    }


def render_markdown(r: dict[str, Any]) -> str:
    a = r["aggregate"]
    lines = [
        "# Issue #68 Phase B3.14 — Break Evidence Memory Audit", "",
        "Status: **diagnostic only / frozen C-2 / no performance use**", "",
        f"Primary engineering gate: **{'PASS' if r['primary_gate_pass'] else 'FAIL'}**",
        f"- Break final-blocker events: **{a['break_final_blocker_events']}**",
        f"- B3.10 mechanically expected Break blockers: **{a['expected_break_final_blocker_events']}**",
        f"- event reproduction absolute delta: **{a['event_reproduction_abs_delta']}**",
        f"- minimum reciprocal boolean attribution: **{100*a['minimum_boolean_mirror_agreement']:.3f}%**",
        f"- pooled source-family reciprocal agreement: **{100*a['pooled_source_agreement']:.3f}%** ({a['pooled_source_matches']}/{a['pooled_source_comparable']})",
        "", "## Event labels", "",
    ]
    for k, v in a["label_counts"].items():
        lines.append(f"- {k}: **{v}** ({100*a['label_shares'][k]:.1f}%)")
    lines += ["", "## Target-side winning Break source", ""]
    for k, v in sorted(a["target_sources"].items()):
        lines.append(f"- {k}: **{v}**")
    lines += ["", "## Old-side winning Break source", ""]
    for k, v in sorted(a["old_sources"].items()):
        lines.append(f"- {k}: **{v}**")
    lines += ["", "## Source-pair matrix", ""]
    for k, v in sorted(a["source_pairs"].items(), key=lambda kv: (-kv[1], kv[0])):
        lines.append(f"- {k}: **{v}**")
    lines += ["", "## Boundary", "", r["boundary"], ""]
    return "\n".join(lines)


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--report-json", type=Path)
    p.add_argument("--report-md", type=Path)
    z = p.parse_args()
    r = build_report()
    if z.report_json:
        z.report_json.parent.mkdir(parents=True, exist_ok=True)
        z.report_json.write_text(json.dumps(r, indent=2), encoding="utf-8")
    if z.report_md:
        z.report_md.parent.mkdir(parents=True, exist_ok=True)
        z.report_md.write_text(render_markdown(r), encoding="utf-8")
    print(render_markdown(r))
    raise SystemExit(0 if r["primary_gate_pass"] else 1)


if __name__ == "__main__":
    main()
