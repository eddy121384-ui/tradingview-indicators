#!/usr/bin/env python3
"""Generate the deterministic Issue #57 Phase-C state-cardinality report."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from diagnose_v06_state_cardinality import HORIZONS, SEGMENTS, run_cardinality_audit


HERE = Path(__file__).resolve().parent
DEFAULT_JSON = HERE / "reports" / "issue-57-phase-c-state-cardinality.json"
DEFAULT_MD = HERE / "reports" / "issue-57-phase-c-state-cardinality.md"


def _pct(value: float | None) -> str:
    return "—" if value is None else f"{value * 100.0:.1f}%"


def _num(value: float | int | None, digits: int = 3) -> str:
    if value is None:
        return "—"
    if isinstance(value, int):
        return str(value)
    return f"{value:.{digits}f}"


def build_report() -> dict[str, Any]:
    audit = run_cardinality_audit()
    return {
        **audit,
        "status": "cardinality_audit_complete_pending_phase_c_decision",
        "decision_boundary": (
            "Prefer the smallest predeclared representation that materially improves state coverage and temporal "
            "stability while retaining nontrivial future-path separation. Do not choose from trading PnL. The "
            "Issue #55 final-OOS period is burned development evidence here, not an independent validation sample."
        ),
    }


def render_markdown(report: dict[str, Any]) -> str:
    summary = report["summary"]
    names = ("six_state", "four_state", "three_state")
    labels = {"six_state": "6-state", "four_state": "4-state", "three_state": "3-state"}
    lines = [
        "# Issue #57 — v0.6 Phase C state-cardinality audit",
        "",
        "Status: **cardinality_audit_complete_pending_phase_c_decision**",
        "",
        report["scope"],
        "",
        "Mappings were declared before this analysis:",
        "",
        "- **6-state:** original six stages.",
        "- **4-state:** Accumulation + Re-accumulation / Markup / Distribution + Re-distribution / Markdown.",
        "- **3-state:** Balance/Transition (1/3/4/6) / Uptrend (2) / Downtrend (5).",
        "",
        "## State coverage",
        "",
    ]

    for segment in SEGMENTS:
        lines.extend(
            [
                f"### {segment}",
                "",
                "| Representation | Target states | Median populated >=1% | Median populated >=5% | Effective states | All target states >=1% pair rate |",
                "|---|---:|---:|---:|---:|---:|",
            ]
        )
        for name in names:
            row = summary[name]["segments"][segment]
            lines.append(
                f"| {labels[name]} | {summary[name]['state_count']} | {_num(row['median_populated_states_1pct'], 1)} | {_num(row['median_populated_states_5pct'], 1)} | {_num(row['median_effective_state_count'])} | {_pct(row['all_states_populated_1pct_pair_rate'])} |"
            )
        lines.append("")

    lines.extend(["## Forward-return separation (median eta-squared across pairs)", ""])
    lines.append("| Segment | Representation | 5 | 10 | 20 | 60 |")
    lines.append("|---|---|---:|---:|---:|---:|")
    for segment in SEGMENTS:
        for name in names:
            eta = summary[name]["segments"][segment]["median_forward_return_eta_squared"]
            lines.append(
                f"| {segment} | {labels[name]} | "
                + " | ".join(_num(eta[str(h)]) for h in HORIZONS)
                + " |"
            )

    lines.extend(["", "## Temporal stability", ""])
    for comparison in ("development_to_exploratory_oos", "exploratory_oos_to_final_oos"):
        lines.extend(
            [
                f"### {comparison}",
                "",
                "| Representation | Occupancy L1 shift | Return-rank rho 5/10/20/60 | Return-sign stability 5/10/20/60 |",
                "|---|---:|---|---|",
            ]
        )
        for name in names:
            row = summary[name]["stability"][comparison]
            rhos = row["median_forward_return_rank_rho"]
            signs = row["forward_return_sign_stability_rate"]
            rho_text = " / ".join(_num(rhos[str(h)], 2) for h in HORIZONS)
            sign_text = " / ".join(_pct(signs[str(h)]) for h in HORIZONS)
            lines.append(
                f"| {labels[name]} | {_num(row['median_occupancy_l1_shift'])} | {rho_text} | {sign_text} |"
            )
        lines.append("")

    lines.extend(
        [
            "## Decision boundary",
            "",
            report["decision_boundary"],
            "",
        ]
    )
    return "\n".join(lines)


def write_report(json_path: Path = DEFAULT_JSON, md_path: Path = DEFAULT_MD) -> dict[str, Any]:
    report = build_report()
    json_path.parent.mkdir(parents=True, exist_ok=True)
    md_path.parent.mkdir(parents=True, exist_ok=True)
    json_path.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    md_path.write_text(render_markdown(report), encoding="utf-8")
    return report


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate Issue #57 Phase-C state-cardinality report")
    parser.add_argument("--json-output", type=Path, default=DEFAULT_JSON)
    parser.add_argument("--md-output", type=Path, default=DEFAULT_MD)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    report = write_report(args.json_output, args.md_output)
    print(json.dumps(report["summary"], sort_keys=True))


if __name__ == "__main__":
    main()
