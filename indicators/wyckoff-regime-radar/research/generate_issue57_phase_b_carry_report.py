#!/usr/bin/env python3
"""Generate the Issue #57 Phase-B Formal-carry decomposition report."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from diagnose_v06_carry_challengers import run_carry_challenger_audit


HERE = Path(__file__).resolve().parent
DEFAULT_JSON = HERE / "reports" / "issue-57-phase-b-carry-decomposition.json"
DEFAULT_MD = HERE / "reports" / "issue-57-phase-b-carry-decomposition.md"


def _pct(value: float | None) -> str:
    return "—" if value is None else f"{value * 100.0:.2f}%"


def _num(value: float | int | None, digits: int = 2) -> str:
    if value is None:
        return "—"
    if isinstance(value, int):
        return str(value)
    return f"{value:.{digits}f}"


def build_report() -> dict[str, Any]:
    audit = run_carry_challenger_audit()
    return {
        **audit,
        "status": "carry_decomposition_complete_pending_phase_b_decision",
        "decision_boundary": (
            "Use this decomposition to decide whether Phase B should change confirmation delay, weak-challenger "
            "handling, or stale-state decay. Do not select a rule from trading PnL."
        ),
    }


def render_markdown(report: dict[str, Any]) -> str:
    agg = report["aggregate"]
    lines = [
        "# Issue #57 — v0.6 Phase B Formal-carry decomposition",
        "",
        "Status: **carry_decomposition_complete_pending_phase_b_decision**",
        "",
        report["scope"],
        "",
        f"Across all four pairs, Formal is carried with no strong candidate on **{_pct(agg['formal_carry_share'])}** of bars.",
        "",
        "## What those carry bars actually are",
        "",
        "| Carry category | Bars | Share of carry | Share of all bars |",
        "|---|---:|---:|---:|",
    ]
    labels = {
        "chaos": "Chaos while old Formal has not yet cleared",
        "weak_challenger": "Weak challenger differs from Formal",
        "weak_same_state": "Weak candidate supports existing Formal",
        "coexist_no_display": "Coexistence / no displayed candidate",
        "neutral_no_candidate": "Non-chaos, no displayed candidate",
    }
    for key, label in labels.items():
        row = agg["categories"][key]
        lines.append(
            f"| {label} | {row['bars']} | {_pct(row['share_of_carry_bars'])} | {_pct(row['share_of_all_bars'])} |"
        )

    lines.extend(
        [
            "",
            "## Weak-challenger follow-through",
            "",
            "A weak challenger is a displayed candidate that differs from Formal but did not qualify as a strong internal candidate.",
            "",
            "| Look-ahead after weak-challenger run | Eligible runs | Formal adopts challenger | Strong challenger emerges | Runs length >=2: Formal adopts |",
            "|---|---:|---:|---:|---:|",
        ]
    )
    for window in ("5", "10"):
        row = agg["weak_challenger_followthrough"][window]
        lines.append(
            f"| {window} bars | {row['eligible_runs']} | {_pct(row['formal_adoption_rate'])} | {_pct(row['strong_candidate_emergence_rate'])} | {_pct(row['formal_adoption_rate_length_ge_2'])} |"
        )

    lines.extend(["", "## Per-pair carry tails", ""])
    lines.append(
        "| Pair | Carry share | Weak challenger share of carry | Weak challenger run median / P90 / max | Neutral-no-candidate P90 / max |"
    )
    lines.append("|---|---:|---:|---:|---:|")
    for row in report["rows"]:
        weak = row["categories"]["weak_challenger"]
        neutral = row["categories"]["neutral_no_candidate"]
        weak_run = row["weak_challenger_runs"]
        lines.append(
            "| {pair} | {carry} | {weak_share} | {wmed} / {wp90} / {wmax} | {np90} / {nmax} |".format(
                pair=row["pair"],
                carry=_pct(row["formal_carry_share"]),
                weak_share=_pct(weak["share_of_carry_bars"]),
                wmed=_num(weak_run["median"]),
                wp90=_num(weak_run["p90"]),
                wmax=_num(weak_run["max"]),
                np90=_num(neutral["run_length_bars"]["p90"]),
                nmax=_num(neutral["run_length_bars"]["max"]),
            )
        )

    lines.extend(
        [
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
    parser = argparse.ArgumentParser(description="Generate Issue #57 Phase-B carry decomposition")
    parser.add_argument("--json-output", type=Path, default=DEFAULT_JSON)
    parser.add_argument("--md-output", type=Path, default=DEFAULT_MD)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    report = write_report(args.json_output, args.md_output)
    print(json.dumps(report["aggregate"], sort_keys=True))


if __name__ == "__main__":
    main()
