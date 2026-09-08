#!/usr/bin/env python3
"""Issue #68 B3.6 Strong formation blockage audit. No performance metrics."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

import diagnose_issue66_reciprocal_symmetry as phasea
from generate_issue66_phase_c2_stage14_conflict_core import load_phase_c2_namespace
from diagnose_issue68_phase_b35_core_bias_reversal import trend_direction

HERE = Path(__file__).resolve().parent


def _compute(frame: pd.DataFrame):
    ns = load_phase_c2_namespace()
    cfg = ns["PriceOnlyConfig"]()
    return ns["compute_price_only"](frame.copy(), cfg), cfg


def _f(model: pd.DataFrame, key: str) -> np.ndarray:
    return pd.to_numeric(model[key], errors="coerce").to_numpy(float)


def _i(model: pd.DataFrame, key: str) -> np.ndarray:
    return np.nan_to_num(_f(model, key), nan=0.0).astype(int)


def _bool(model: pd.DataFrame, key: str) -> np.ndarray:
    return model[key].astype(bool).to_numpy()


def _bool_mirror(a: np.ndarray, b: np.ndarray, warmup: int) -> dict[str, float | int]:
    x = np.asarray(a, dtype=bool)[warmup:]
    y = np.asarray(b, dtype=bool)[warmup:]
    good = x == y
    return {
        "bars": int(len(x)),
        "mirror_agreement": float(np.mean(good)) if len(x) else 1.0,
        "mismatch_bars": int(np.sum(~good)),
    }


def _dir_mirror(a: np.ndarray, b: np.ndarray, warmup: int) -> dict[str, float | int]:
    x = np.asarray(a, dtype=int)[warmup:]
    y = np.asarray(b, dtype=int)[warmup:]
    good = x == -y
    return {
        "bars": int(len(x)),
        "mirror_agreement": float(np.mean(good)) if len(x) else 1.0,
        "mismatch_bars": int(np.sum(~good)),
    }


def blocker_masks(model: pd.DataFrame, cfg: Any) -> dict[str, np.ndarray]:
    top_dir = trend_direction(_i(model, "top_id"))
    top_trend = top_dir != 0
    strong = _bool(model, "strong_candidate")
    blocked = top_trend & ~strong

    top_value = _f(model, "top_value")
    top_gap = _f(model, "top_gap")
    evidence = _f(model, "evidence_strength")
    conflict = _bool(model, "candidate_conflict")

    dominance = blocked & np.isfinite(top_value) & (top_value < float(cfg.dominant_min))
    gap = blocked & np.isfinite(top_gap) & (top_gap < float(cfg.top_gap_min))
    evidence_block = blocked & np.isfinite(evidence) & (evidence < float(cfg.evidence_min))
    conflict_block = blocked & conflict

    explained = dominance | gap | evidence_block | conflict_block
    # C-2 strongCandidate also requires a usable/sharp state. The generated Python
    # transport does not expose has_sharp directly, so the exact residual of the
    # public strong predicate is labeled NO_SHARP rather than inventing a proxy.
    no_sharp = blocked & ~explained
    unexplained = blocked & ~(explained | no_sharp)

    return {
        "top_trend": top_trend,
        "strong_trend": top_trend & strong,
        "blocked": blocked,
        "dominance": dominance,
        "gap": gap,
        "evidence": evidence_block,
        "conflict": conflict_block,
        "no_sharp": no_sharp,
        "unexplained": unexplained,
    }


def analyze_pair(frame: pd.DataFrame) -> dict[str, Any]:
    inv = phasea.reciprocal_ohlc(frame)
    model, cfg = _compute(frame)
    inv_model, inv_cfg = _compute(inv)
    warmup = int(cfg.rank_len - 1)
    if warmup != int(inv_cfg.rank_len - 1):
        raise AssertionError("warmup mismatch")

    m = blocker_masks(model, cfg)
    im = blocker_masks(inv_model, inv_cfg)
    top_dir = trend_direction(_i(model, "top_id"))
    inv_top_dir = trend_direction(_i(inv_model, "top_id"))
    strong_dir = np.where(_bool(model, "strong_candidate"), top_dir, 0)
    inv_strong_dir = np.where(_bool(inv_model, "strong_candidate"), inv_top_dir, 0)

    scored = slice(warmup, None)
    blocked_n = int(np.sum(m["blocked"][scored]))
    counts = {k: int(np.sum(v[scored])) for k, v in m.items()}
    shares = {
        k: (float(counts[k] / blocked_n) if blocked_n else 0.0)
        for k in ("dominance", "gap", "evidence", "conflict", "no_sharp", "unexplained")
    }
    overlaps = (
        m["dominance"].astype(int)
        + m["gap"].astype(int)
        + m["evidence"].astype(int)
        + m["conflict"].astype(int)
        + m["no_sharp"].astype(int)
    )

    return {
        "warmup": warmup,
        "counts": counts,
        "blocked_shares": shares,
        "multi_blocker_bars": int(np.sum((overlaps > 1)[scored])),
        "top_direction_mirror": _dir_mirror(top_dir, inv_top_dir, warmup),
        "strong_direction_mirror": _dir_mirror(strong_dir, inv_strong_dir, warmup),
        "blocker_mirror": {
            k: _bool_mirror(m[k], im[k], warmup)
            for k in ("dominance", "gap", "evidence", "conflict", "no_sharp")
        },
    }


def build_report() -> dict[str, Any]:
    pairs = {name: analyze_pair(frame) for name, frame in phasea.load_frozen_pairs().items()}
    total = {k: 0 for k in ("top_trend", "strong_trend", "blocked", "dominance", "gap", "evidence", "conflict", "no_sharp", "unexplained")}
    multi = 0
    for p in pairs.values():
        for k in total:
            total[k] += int(p["counts"][k])
        multi += int(p["multi_blocker_bars"])

    blocked = total["blocked"]
    agg_shares = {
        k: (float(total[k] / blocked) if blocked else 0.0)
        for k in ("dominance", "gap", "evidence", "conflict", "no_sharp", "unexplained")
    }
    return {
        "schema_version": 1,
        "issue": 68,
        "phase": "B3.6",
        "status": "STRONG_FORMATION_BLOCKAGE_AUDIT_NO_PERFORMANCE",
        "primary_gate_pass": total["unexplained"] == 0,
        "aggregate": {
            **total,
            "blocker_share_of_blocked": agg_shares,
            "multi_blocker_bars": multi,
        },
        "pairs": pairs,
        "boundary": "Attribution only. Existing C-2 thresholds are read, never changed. No strategy performance metric is computed.",
    }


def render_markdown(r: dict[str, Any]) -> str:
    a = r["aggregate"]
    s = a["blocker_share_of_blocked"]
    lines = [
        "# Issue #68 Phase B3.6 — Strong Formation Blockage Audit",
        "",
        "Status: **diagnostic only / frozen C-2 / no performance use**",
        "",
        f"Primary attribution gate: **{'PASS' if r['primary_gate_pass'] else 'FAIL'}**",
        f"- TOP trend-family bars: **{a['top_trend']}**",
        f"- STRONG trend-family bars: **{a['strong_trend']}**",
        f"- TOP trend but STRONG blocked: **{a['blocked']}**",
        f"- DOMINANCE blocker: **{a['dominance']} ({100*s['dominance']:.1f}% of blocked)**",
        f"- GAP blocker: **{a['gap']} ({100*s['gap']:.1f}% of blocked)**",
        f"- EVIDENCE blocker: **{a['evidence']} ({100*s['evidence']:.1f}% of blocked)**",
        f"- CONFLICT blocker: **{a['conflict']} ({100*s['conflict']:.1f}% of blocked)**",
        f"- inferred NO_SHARP residual: **{a['no_sharp']} ({100*s['no_sharp']:.1f}% of blocked)**",
        f"- unexplained blocked bars: **{a['unexplained']}**",
        f"- multi-blocker bars: **{a['multi_blocker_bars']}**",
        "",
        "## Per pair",
        "",
        "| Pair | Blocked | Dom | Gap | Evidence | Conflict | No-sharp | TOP mirror | STRONG mirror |",
        "|---|---:|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for name, p in r["pairs"].items():
        c = p["counts"]
        lines.append(
            f"| {name} | {c['blocked']} | {c['dominance']} | {c['gap']} | {c['evidence']} | {c['conflict']} | {c['no_sharp']} | "
            f"{100*p['top_direction_mirror']['mirror_agreement']:.2f}% | {100*p['strong_direction_mirror']['mirror_agreement']:.2f}% |"
        )
    lines += ["", "## Boundary", "", r["boundary"], ""]
    return "\n".join(lines)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--json", type=Path, default=HERE / "reports/issue-68-phase-b36-strong-blockage.json")
    ap.add_argument("--md", type=Path, default=HERE / "reports/issue-68-phase-b36-strong-blockage.md")
    args = ap.parse_args()
    report = build_report()
    args.json.parent.mkdir(parents=True, exist_ok=True)
    args.json.write_text(json.dumps(report, indent=2, sort_keys=True), encoding="utf-8")
    args.md.write_text(render_markdown(report), encoding="utf-8")
    print(json.dumps(report["aggregate"], indent=2, sort_keys=True))
    if not report["primary_gate_pass"]:
        raise SystemExit("Issue #68 B3.6 blocker attribution failed")


if __name__ == "__main__":
    main()
