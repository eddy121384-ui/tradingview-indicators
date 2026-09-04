#!/usr/bin/env python3
"""Issue #68 B3.9 raw-formulation competitor attribution. Diagnostic only."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

import diagnose_issue68_phase_b38_raw_feature_attribution as b38

HERE = Path(__file__).resolve().parent
STAGE_MIRROR = {1: 4, 2: 5, 3: 6, 4: 1, 5: 2, 6: 3}


def _raw_matrix(model: pd.DataFrame) -> np.ndarray:
    return b38._raw_matrix(model)


def _direction_spec(direction: int) -> dict[str, Any]:
    if direction == 1:
        return {
            "name": "bull",
            "target": [2, 3],
            "fresh": 2,
            "continuation": 3,
            "competitors": [1, 4, 5, 6],
        }
    if direction == -1:
        return {
            "name": "bear",
            "target": [5, 6],
            "fresh": 5,
            "continuation": 6,
            "competitors": [4, 1, 2, 3],
        }
    raise ValueError(direction)


def _winner_stage(raw: np.ndarray) -> np.ndarray:
    # np.argmax preserves the classifier's strict first-stage tie priority.
    return np.argmax(raw, axis=1) + 1


def direction_audit(model: pd.DataFrame, direction: int, warmup: int, keep_masks: bool = False) -> dict[str, Any]:
    spec = _direction_spec(direction)
    raw = _raw_matrix(model)
    finite = np.all(np.isfinite(raw), axis=1)
    scored = finite.copy()
    scored[:warmup] = False

    target_cols = np.asarray(spec["target"], dtype=int) - 1
    target_subchoice_pos = np.argmax(raw[:, target_cols], axis=1)
    target_stage = np.asarray(spec["target"], dtype=int)[target_subchoice_pos]
    target_raw = np.max(raw[:, target_cols], axis=1)

    fresh_raw = raw[:, int(spec["fresh"]) - 1]
    continuation_raw = raw[:, int(spec["continuation"]) - 1]
    fresh_leads = fresh_raw >= continuation_raw

    winner = _winner_stage(raw)
    competitor_cols = np.asarray(spec["competitors"], dtype=int) - 1
    competitor_max = np.max(raw[:, competitor_cols], axis=1)
    raw_adv = target_raw > competitor_max
    raw_loss = scored & ~raw_adv

    exact_counts: dict[str, int] = {}
    pairwise_suppress: dict[str, int] = {}
    pairwise_margin: dict[str, dict[str, float | int]] = {}

    for stage in spec["competitors"]:
        comp = raw[:, stage - 1]
        suppress = scored & (comp >= target_raw)
        exact_counts[str(stage)] = int(np.sum(raw_loss & (winner == stage)))
        pairwise_suppress[str(stage)] = int(np.sum(suppress))
        margins = target_raw[suppress] - comp[suppress]
        pairwise_margin[str(stage)] = {
            "bars": int(np.sum(suppress)),
            "median_target_minus_competitor": float(np.nanmedian(margins)) if len(margins) else 0.0,
            "mean_target_minus_competitor": float(np.nanmean(margins)) if len(margins) else 0.0,
        }

    target_tie_priority = raw_loss & np.isin(winner, np.asarray(spec["target"], dtype=int))
    attributed = np.zeros(len(raw), dtype=bool)
    for stage in spec["competitors"]:
        attributed |= raw_loss & (winner == stage)
    attributed |= target_tie_priority
    unexplained = raw_loss & ~attributed

    loss_n = int(np.sum(raw_loss))
    fresh_on_loss = int(np.sum(raw_loss & (target_stage == int(spec["fresh"]))))
    continuation_on_loss = int(np.sum(raw_loss & (target_stage == int(spec["continuation"]))))

    out: dict[str, Any] = {
        "direction": spec["name"],
        "usable_bars": int(np.sum(scored)),
        "raw_adv_bars": int(np.sum(scored & raw_adv)),
        "raw_loss_bars": loss_n,
        "raw_loss_share": float(loss_n / np.sum(scored)) if np.sum(scored) else 0.0,
        "target_substage_on_loss": {
            "fresh_stage": int(spec["fresh"]),
            "continuation_stage": int(spec["continuation"]),
            "fresh": fresh_on_loss,
            "continuation": continuation_on_loss,
            "fresh_share": float(fresh_on_loss / loss_n) if loss_n else 0.0,
        },
        "exact_raw_winner_on_loss": {
            "competitor_stage_counts": exact_counts,
            "target_tie_priority": int(np.sum(target_tie_priority)),
            "unexplained": int(np.sum(unexplained)),
        },
        "pairwise_competitor_suppression": pairwise_suppress,
        "pairwise_margin_on_suppression": pairwise_margin,
        "fresh_target_lead_share_all_scored": float(np.mean(fresh_leads[scored])) if np.any(scored) else 0.0,
    }
    if keep_masks:
        out["_masks"] = {
            "scored": scored,
            "raw_adv": raw_adv,
            "fresh_leads": fresh_leads,
            "winner": winner,
            "target_stage": target_stage,
            "pairwise_pass": {
                str(stage): target_raw > raw[:, stage - 1] for stage in spec["competitors"]
            },
        }
    return out


def _agreement(a: np.ndarray, b: np.ndarray, mask: np.ndarray) -> dict[str, float | int]:
    good = np.asarray(a)[mask] == np.asarray(b)[mask]
    return {
        "bars": int(np.sum(mask)),
        "agreement": float(np.mean(good)) if len(good) else 1.0,
        "mismatch_bars": int(np.sum(~good)),
    }


def analyze_pair(frame: pd.DataFrame) -> dict[str, Any]:
    inverse = b38.phasea.reciprocal_ohlc(frame)
    model, cfg = b38._compute(frame)
    inv_model, inv_cfg = b38._compute(inverse)
    warmup = int(cfg.rank_len - 1)
    if warmup != int(inv_cfg.rank_len - 1):
        raise AssertionError("warmup mismatch")

    bull = direction_audit(model, 1, warmup, keep_masks=True)
    bear = direction_audit(model, -1, warmup, keep_masks=True)
    inv_bull = direction_audit(inv_model, 1, warmup, keep_masks=True)
    inv_bear = direction_audit(inv_model, -1, warmup, keep_masks=True)

    bm = bull["_masks"]
    ibm = inv_bear["_masks"]
    comparable = np.asarray(bm["scored"], dtype=bool) & np.asarray(ibm["scored"], dtype=bool)

    winner_mapped = np.vectorize(STAGE_MIRROR.get)(np.asarray(bm["winner"], dtype=int))
    winner_mirror = _agreement(winner_mapped, np.asarray(ibm["winner"], dtype=int), comparable)
    raw_adv_mirror = _agreement(np.asarray(bm["raw_adv"]), np.asarray(ibm["raw_adv"]), comparable)
    fresh_mirror = _agreement(np.asarray(bm["fresh_leads"]), np.asarray(ibm["fresh_leads"]), comparable)

    pairwise_mirror: dict[str, Any] = {}
    for bull_stage in (1, 4, 5, 6):
        inv_bear_stage = STAGE_MIRROR[bull_stage]
        pairwise_mirror[f"bull_vs_s{bull_stage}__inverse_bear_vs_s{inv_bear_stage}"] = _agreement(
            np.asarray(bm["pairwise_pass"][str(bull_stage)]),
            np.asarray(ibm["pairwise_pass"][str(inv_bear_stage)]),
            comparable,
        )

    for obj in (bull, bear, inv_bull, inv_bear):
        obj.pop("_masks", None)

    return {
        "warmup": warmup,
        "bull": bull,
        "bear": bear,
        "inverse_bull": inv_bull,
        "inverse_bear": inv_bear,
        "mirror": {
            "exact_raw_winner_stage": winner_mirror,
            "raw_adv": raw_adv_mirror,
            "fresh_target": fresh_mirror,
            "pairwise": pairwise_mirror,
        },
    }


def build_report() -> dict[str, Any]:
    pairs = {name: analyze_pair(frame) for name, frame in b38.phasea.load_frozen_pairs().items()}

    aggregate = {
        "usable_direction_observations": 0,
        "raw_loss_bars": 0,
        "unexplained": 0,
        "target_tie_priority": 0,
        "exact_competitor_winner_counts": {str(i): 0 for i in range(1, 7)},
        "pairwise_suppression_counts": {str(i): 0 for i in range(1, 7)},
        "fresh_target_on_loss": 0,
        "continuation_target_on_loss": 0,
    }
    mirror_min = 1.0
    exact_winner_mirror_min = 1.0

    for p in pairs.values():
        for side in ("bull", "bear"):
            x = p[side]
            aggregate["usable_direction_observations"] += int(x["usable_bars"])
            aggregate["raw_loss_bars"] += int(x["raw_loss_bars"])
            aggregate["unexplained"] += int(x["exact_raw_winner_on_loss"]["unexplained"])
            aggregate["target_tie_priority"] += int(x["exact_raw_winner_on_loss"]["target_tie_priority"])
            aggregate["fresh_target_on_loss"] += int(x["target_substage_on_loss"]["fresh"])
            aggregate["continuation_target_on_loss"] += int(x["target_substage_on_loss"]["continuation"])
            for stage, count in x["exact_raw_winner_on_loss"]["competitor_stage_counts"].items():
                aggregate["exact_competitor_winner_counts"][stage] += int(count)
            for stage, count in x["pairwise_competitor_suppression"].items():
                aggregate["pairwise_suppression_counts"][stage] += int(count)

        exact_winner_mirror_min = min(
            exact_winner_mirror_min,
            float(p["mirror"]["exact_raw_winner_stage"]["agreement"]),
        )
        mirror_min = min(mirror_min, exact_winner_mirror_min)
        mirror_min = min(mirror_min, float(p["mirror"]["raw_adv"]["agreement"]))
        mirror_min = min(mirror_min, float(p["mirror"]["fresh_target"]["agreement"]))
        for m in p["mirror"]["pairwise"].values():
            mirror_min = min(mirror_min, float(m["agreement"]))

    loss_n = int(aggregate["raw_loss_bars"])
    aggregate["fresh_target_share_on_loss"] = (
        float(aggregate["fresh_target_on_loss"] / loss_n) if loss_n else 0.0
    )
    aggregate["minimum_reciprocal_boolean_agreement"] = mirror_min
    aggregate["minimum_exact_raw_winner_stage_mirror_agreement"] = exact_winner_mirror_min

    accounted = (
        sum(int(v) for v in aggregate["exact_competitor_winner_counts"].values())
        + int(aggregate["target_tie_priority"])
        + int(aggregate["unexplained"])
    )
    aggregate["exact_winner_accounting_delta"] = int(accounted - loss_n)

    primary = (
        int(aggregate["unexplained"]) == 0
        and int(aggregate["exact_winner_accounting_delta"]) == 0
        and float(aggregate["minimum_reciprocal_boolean_agreement"]) >= 0.99
        and float(aggregate["minimum_exact_raw_winner_stage_mirror_agreement"]) >= 0.99
    )

    return {
        "schema_version": 1,
        "issue": 68,
        "phase": "B3.9",
        "status": "RAW_FORMULATION_ATTRIBUTION_NO_PERFORMANCE",
        "primary_gate_pass": bool(primary),
        "aggregate": aggregate,
        "pairs": pairs,
        "boundary": "Exact raw-stage competitor and target-substage attribution only. No classifier formula, weight, threshold, gate, persistence, Core Bias, Exposure, or strategy-performance rule is changed or optimized.",
    }


def render_markdown(report: dict[str, Any]) -> str:
    a = report["aggregate"]
    lines = [
        "# Issue #68 Phase B3.9 — Raw Formulation Attribution",
        "",
        "Status: **diagnostic only / frozen C-2 / no performance use**",
        "",
        f"Primary engineering gate: **{'PASS' if report['primary_gate_pass'] else 'FAIL'}**",
        f"- usable direction observations: **{a['usable_direction_observations']}**",
        f"- raw-loss observations: **{a['raw_loss_bars']}**",
        f"- unexplained exact raw winner: **{a['unexplained']}**",
        f"- target-tie-priority technical cases: **{a['target_tie_priority']}**",
        f"- exact winner accounting delta: **{a['exact_winner_accounting_delta']}**",
        f"- fresh target share while target family loses: **{100*a['fresh_target_share_on_loss']:.1f}%**",
        f"- minimum reciprocal boolean agreement: **{100*a['minimum_reciprocal_boolean_agreement']:.3f}%**",
        f"- minimum exact raw-winner-stage mirror agreement: **{100*a['minimum_exact_raw_winner_stage_mirror_agreement']:.3f}%**",
        "",
        "## Exact competitor raw winner counts on target-family loss",
        "",
    ]
    for stage, count in a["exact_competitor_winner_counts"].items():
        if count:
            lines.append(f"- Stage {stage}: **{count}**")
    lines += ["", "## Pairwise suppression counts (overlap allowed)", ""]
    for stage, count in a["pairwise_suppression_counts"].items():
        if count:
            lines.append(f"- Stage {stage}: **{count}**")

    lines += [
        "",
        "## Per-pair Bull attribution",
        "",
        "| Pair | Bull loss | Fresh target on loss | S1 winner | S4 winner | S5 winner | S6 winner |",
        "|---|---:|---:|---:|---:|---:|---:|",
    ]
    for name, p in report["pairs"].items():
        x = p["bull"]
        c = x["exact_raw_winner_on_loss"]["competitor_stage_counts"]
        lines.append(
            f"| {name} | {x['raw_loss_bars']} | {x['target_substage_on_loss']['fresh']} | {c.get('1',0)} | {c.get('4',0)} | {c.get('5',0)} | {c.get('6',0)} |"
        )

    lines += ["", "## Boundary", "", report["boundary"], ""]
    return "\n".join(lines)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--json", type=Path, default=HERE / "reports/issue-68-phase-b39-raw-formulation-attribution.json")
    ap.add_argument("--md", type=Path, default=HERE / "reports/issue-68-phase-b39-raw-formulation-attribution.md")
    args = ap.parse_args()

    report = build_report()
    args.json.parent.mkdir(parents=True, exist_ok=True)
    args.json.write_text(json.dumps(report, indent=2, sort_keys=True), encoding="utf-8")
    args.md.write_text(render_markdown(report), encoding="utf-8")
    print(json.dumps(report["aggregate"], indent=2, sort_keys=True))
    if not report["primary_gate_pass"]:
        raise SystemExit("Issue #68 B3.9 raw formulation attribution gate failed")


if __name__ == "__main__":
    main()
