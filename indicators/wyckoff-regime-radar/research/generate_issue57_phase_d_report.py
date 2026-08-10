#!/usr/bin/env python3
"""Generate deterministic Issue #57 Phase-D four-state strength report."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from diagnose_v06_canonical_strength import STRENGTH_FIELDS, run_strength_audit


HERE = Path(__file__).resolve().parent
DEFAULT_JSON = HERE / "reports" / "issue-57-phase-d-canonical-strength.json"
DEFAULT_MD = HERE / "reports" / "issue-57-phase-d-canonical-strength.md"

FIELD_LABELS = {
    "canonical_formal_support": "Formal Support",
    "canonical_formal_margin": "Formal Margin",
    "canonical_concentration": "Weight Concentration",
}


def _pct(value: float | None) -> str:
    return "—" if value is None else f"{value * 100.0:.1f}%"


def _num(value: float | int | None, digits: int = 4) -> str:
    if value is None:
        return "—"
    if isinstance(value, int):
        return str(value)
    return f"{value:.{digits}f}"


def build_report() -> dict[str, Any]:
    audit = run_strength_audit()
    return {
        **audit,
        "status": "strength_calibration_audit_complete_pending_phase_d_decision",
        "decision_boundary": (
            "A metric may be called confidence only if Development-derived Low/Medium/High bins show repeatable "
            "high>low and preferably monotonic improvement in later observed segments for both state retention and "
            "directional Markup/Markdown outcomes. Otherwise retain descriptive names such as Support, Margin, or "
            "Concentration and do not present them as probability/confidence."
        ),
    }


def render_markdown(report: dict[str, Any]) -> str:
    lines = [
        "# Issue #57 — v0.6 Phase D canonical strength audit",
        "",
        "Status: **strength_calibration_audit_complete_pending_phase_d_decision**",
        "",
        report["scope"],
        "",
        "Development defines Low / Medium / High terciles per pair and canonical Formal state. Those cut points are then applied unchanged to the two later, already-observed segments.",
        "",
        "The question is deliberately strict: does a higher score reliably mean a more persistent classification and a more directionally aligned Markup/Markdown outcome?",
        "",
    ]

    for segment in ("exploratory_oos", "final_oos"):
        lines.extend(
            [
                f"## {segment}",
                "",
                "| Metric | Retention: high>low | Retention monotonic | Median high-low retention | Direction: high>low | Direction monotonic | Median high-low aligned return |",
                "|---|---:|---:|---:|---:|---:|---:|",
            ]
        )
        for field in STRENGTH_FIELDS:
            retention = report["summary"][segment][field]["formal_retention"]
            direction = report["summary"][segment][field]["directional_aligned_return"]
            lines.append(
                f"| {FIELD_LABELS[field]} | "
                f"{retention['high_better_cases']}/{retention['comparable_cases']} ({_pct(retention['high_better_rate'])}) | "
                f"{retention['monotonic_cases']}/{retention['monotonic_comparable_cases']} ({_pct(retention['monotonic_rate'])}) | "
                f"{_num(retention['median_high_minus_low'])} | "
                f"{direction['high_better_cases']}/{direction['comparable_cases']} ({_pct(direction['high_better_rate'])}) | "
                f"{direction['monotonic_cases']}/{direction['monotonic_comparable_cases']} ({_pct(direction['monotonic_rate'])}) | "
                f"{_num(direction['median_high_minus_low'])} |"
            )
        lines.append("")

    lines.extend(
        [
            "## Metric definitions",
            "",
            "- **Formal Support:** four-state weight assigned to the currently confirmed Formal regime.",
            "- **Formal Margin:** Formal Support minus the strongest competing four-state weight. It can be negative when inertia is carrying a stale Formal label.",
            "- **Weight Concentration:** normalized inverse entropy of the four canonical weights; high means the weight vector is concentrated, regardless of which state is Formal.",
            "",
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
    parser = argparse.ArgumentParser(description="Generate Issue #57 Phase-D canonical strength report")
    parser.add_argument("--json-output", type=Path, default=DEFAULT_JSON)
    parser.add_argument("--md-output", type=Path, default=DEFAULT_MD)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    report = write_report(args.json_output, args.md_output)
    print(json.dumps(report["summary"], sort_keys=True))


if __name__ == "__main__":
    main()
