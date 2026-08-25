#!/usr/bin/env python3
"""Issue #66 Phase B-1 reciprocal-safe representation A/B diagnostic.

Runs the frozen v0.6 Phase-B baseline and the B-1 representation-only variant
on the same already-burned four-FX fixtures and their reciprocal OHLC quotes.
No strategy or profitability statistic is computed.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any, Callable

import numpy as np

import diagnose_issue66_reciprocal_symmetry as phasea
from generate_issue66_phase_b1_representation_core import load_phase_b1_namespace


HERE = Path(__file__).resolve().parent


def build_with_loader(loader: Callable[[], dict[str, object]]) -> dict[str, Any]:
    """Reuse the Phase-A decomposition with an injected core loader."""
    ns = loader()
    compute_price_only = ns["compute_price_only"]
    config_type = ns["PriceOnlyConfig"]
    old_compute = phasea.compute

    def injected(frame):
        cfg = config_type()
        return compute_price_only(frame.copy(), cfg), cfg

    phasea.compute = injected
    try:
        return phasea.build_report()
    finally:
        phasea.compute = old_compute


def mean_numeric_layer(report: dict[str, Any], layer: str) -> float:
    values: list[float] = []
    for row in report["pairs"].values():
        for metric in row["numeric_layers"][layer].values():
            value = metric.get("mae")
            if value is not None:
                values.append(float(value))
    return float(np.mean(values)) if values else float("nan")


def enrich(report: dict[str, Any]) -> dict[str, Any]:
    out = dict(report)
    out["aggregate"] = dict(report["aggregate"])
    out["aggregate"]["representation_numeric_mae"] = mean_numeric_layer(report, "representation")
    return out


def build_report() -> dict[str, Any]:
    baseline = enrich(phasea.build_report())
    variant = enrich(build_with_loader(load_phase_b1_namespace))

    agreement_metrics = (
        "ma_up_to_inverse_down_jaccard",
        "ma_down_to_inverse_up_jaccard",
        "breakout_mode_up_to_inverse_down_jaccard",
        "breakdown_mode_down_to_inverse_up_jaccard",
        "candidate_display_mirror_agreement",
        "formal_stage_mirror_agreement",
        "candidate_transition_pair_mirror_agreement",
        "formal_transition_pair_mirror_agreement",
    )
    mae_metrics = (
        "representation_numeric_mae",
        "raw_stage_vector_mae",
        "stage_gate_vector_mae",
        "effective_stage_vector_mae",
        "probability_stage_vector_mae",
    )

    gains: dict[str, float] = {}
    for key in agreement_metrics:
        gains[key] = float(variant["aggregate"][key] - baseline["aggregate"][key])
    for key in mae_metrics:
        gains[key] = float(baseline["aggregate"][key] - variant["aggregate"][key])

    primary_gate = bool(
        variant["aggregate"]["ma_up_to_inverse_down_jaccard"] >= 0.999999
        and variant["aggregate"]["ma_down_to_inverse_up_jaccard"] >= 0.999999
        and variant["aggregate"]["representation_numeric_mae"]
        < baseline["aggregate"]["representation_numeric_mae"]
    )

    return {
        "schema_version": 1,
        "issue": 66,
        "phase": "B-1",
        "status": "REPRESENTATION_ONLY_RECIPROCAL_AB_REUSED_DATA_NO_PNL",
        "research_boundary": (
            "Engineering symmetry comparison only. No PnL, trade, Sharpe, CAGR, drawdown, "
            "Strategy Tester, Volume, MTF, Divergence, or HMM statistic is computed."
        ),
        "primary_gate_pass": primary_gate,
        "baseline": baseline,
        "variant": variant,
        "symmetry_gain": gains,
    }


def pct(value: float) -> str:
    return f"{value * 100.0:.2f}%"


def num(value: float) -> str:
    return f"{value:.6f}"


def render_markdown(report: dict[str, Any]) -> str:
    b = report["baseline"]["aggregate"]
    v = report["variant"]["aggregate"]
    g = report["symmetry_gain"]
    lines = [
        "# Issue #66 Phase B-1 — Reciprocal-Safe Representation A/B",
        "",
        "Status: **reused frozen data / no PnL**",
        "",
        f"Primary representation gate: **{'PASS' if report['primary_gate_pass'] else 'FAIL'}**",
        "",
        "Only the preregistered representation family differs from the frozen v0.6 Phase-B baseline. Directional heuristics, stage formulas/gates, and persistence are unchanged.",
        "",
        "## Primary layer",
        "",
        "| Metric | Baseline | B-1 | Symmetry gain |",
        "|---|---:|---:|---:|",
        f"| MA cross up → inverse down Jaccard | {pct(b['ma_up_to_inverse_down_jaccard'])} | {pct(v['ma_up_to_inverse_down_jaccard'])} | {pct(g['ma_up_to_inverse_down_jaccard'])} |",
        f"| MA cross down → inverse up Jaccard | {pct(b['ma_down_to_inverse_up_jaccard'])} | {pct(v['ma_down_to_inverse_up_jaccard'])} | {pct(g['ma_down_to_inverse_up_jaccard'])} |",
        f"| Representation numeric MAE | {num(b['representation_numeric_mae'])} | {num(v['representation_numeric_mae'])} | {num(g['representation_numeric_mae'])} lower |",
        "",
        "## Downstream observations (not tuning targets)",
        "",
        "| Metric | Baseline | B-1 | Symmetry gain |",
        "|---|---:|---:|---:|",
        f"| Breakout mode up → inverse down | {pct(b['breakout_mode_up_to_inverse_down_jaccard'])} | {pct(v['breakout_mode_up_to_inverse_down_jaccard'])} | {pct(g['breakout_mode_up_to_inverse_down_jaccard'])} |",
        f"| Breakdown mode down → inverse up | {pct(b['breakdown_mode_down_to_inverse_up_jaccard'])} | {pct(v['breakdown_mode_down_to_inverse_up_jaccard'])} | {pct(g['breakdown_mode_down_to_inverse_up_jaccard'])} |",
        f"| Raw stage-vector MAE | {num(b['raw_stage_vector_mae'])} | {num(v['raw_stage_vector_mae'])} | {num(g['raw_stage_vector_mae'])} lower |",
        f"| Gate-vector MAE | {num(b['stage_gate_vector_mae'])} | {num(v['stage_gate_vector_mae'])} | {num(g['stage_gate_vector_mae'])} lower |",
        f"| Effective stage-vector MAE | {num(b['effective_stage_vector_mae'])} | {num(v['effective_stage_vector_mae'])} | {num(g['effective_stage_vector_mae'])} lower |",
        f"| Probability-vector MAE | {num(b['probability_stage_vector_mae'])} | {num(v['probability_stage_vector_mae'])} | {num(g['probability_stage_vector_mae'])} lower |",
        f"| Candidate-display mirror | {pct(b['candidate_display_mirror_agreement'])} | {pct(v['candidate_display_mirror_agreement'])} | {pct(g['candidate_display_mirror_agreement'])} |",
        f"| Formal mirror | {pct(b['formal_stage_mirror_agreement'])} | {pct(v['formal_stage_mirror_agreement'])} | {pct(g['formal_stage_mirror_agreement'])} |",
        f"| Candidate transition-pair mirror | {pct(b['candidate_transition_pair_mirror_agreement'])} | {pct(v['candidate_transition_pair_mirror_agreement'])} | {pct(g['candidate_transition_pair_mirror_agreement'])} |",
        f"| Formal transition-pair mirror | {pct(b['formal_transition_pair_mirror_agreement'])} | {pct(v['formal_transition_pair_mirror_agreement'])} | {pct(g['formal_transition_pair_mirror_agreement'])} |",
        "",
        "## Boundary",
        "",
        "This report does not authorize threshold equalization or stage-formula changes. If B-1 passes its primary gate, the next experiment may change one additional non-isomorphic primitive family only.",
        "",
    ]
    return "\n".join(lines)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Issue #66 Phase B-1 representation A/B")
    parser.add_argument("--json", type=Path, required=True)
    parser.add_argument("--markdown", type=Path, required=True)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    report = build_report()
    args.json.parent.mkdir(parents=True, exist_ok=True)
    args.markdown.parent.mkdir(parents=True, exist_ok=True)
    args.json.write_text(json.dumps(report, indent=2), encoding="utf-8")
    args.markdown.write_text(render_markdown(report), encoding="utf-8")
    print(json.dumps({
        "primary_gate_pass": report["primary_gate_pass"],
        "baseline": report["baseline"]["aggregate"],
        "variant": report["variant"]["aggregate"],
        "symmetry_gain": report["symmetry_gain"],
    }, indent=2))


if __name__ == "__main__":
    main()
