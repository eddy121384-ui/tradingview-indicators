#!/usr/bin/env python3
"""Generate the Issue #57 Phase-B stale-decay candidate comparison report."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from diagnose_v06_phase_b_persistence_candidate import run_phase_b_candidate_comparison


HERE = Path(__file__).resolve().parent
DEFAULT_JSON = HERE / "reports" / "issue-57-phase-b-stale-decay-candidate.json"
DEFAULT_MD = HERE / "reports" / "issue-57-phase-b-stale-decay-candidate.md"


def _pct(value: float | None) -> str:
    return "—" if value is None else f"{value * 100.0:.2f}%"


def _num(value: float | int | None, digits: int = 2) -> str:
    if value is None:
        return "—"
    if isinstance(value, int):
        return str(value)
    return f"{value:.{digits}f}"


def build_report() -> dict[str, Any]:
    return {
        **run_phase_b_candidate_comparison(),
        "status": "candidate_engineering_comparison_complete",
        "decision_boundary": (
            "Judge this candidate only on stale-state reduction versus added neutral churn / switching noise. "
            "Do not use trading PnL to accept or reject it."
        ),
    }


def render_markdown(report: dict[str, Any]) -> str:
    a = report["summary"]["phase_a"]
    b = report["summary"]["phase_b_candidate"]
    lines = [
        "# Issue #57 — v0.6 Phase B stale-decay candidate",
        "",
        "Status: **candidate_engineering_comparison_complete**",
        "",
        report["scope"],
        "",
        f"Candidate rule: {report['rule']}",
        "",
        "| Metric | Phase A state machine | Phase B candidate |",
        "|---|---:|---:|",
        f"| Formal zero share | {_pct(a['median_pair_formal_zero_share'])} | {_pct(b['median_pair_formal_zero_share'])} |",
        f"| Formal carry without strong candidate | {_pct(a['median_pair_formal_carry_share'])} | {_pct(b['median_pair_formal_carry_share'])} |",
        f"| Disagreement / strong-candidate bars | {_pct(a['median_pair_disagreement_share_candidate_bars'])} | {_pct(b['median_pair_disagreement_share_candidate_bars'])} |",
        f"| Disagreement-run P90 | {_num(a['median_pair_disagreement_run_p90_bars'])} | {_num(b['median_pair_disagreement_run_p90_bars'])} |",
        f"| Carry-run P90 | {_num(a['median_pair_formal_carry_run_p90_bars'])} | {_num(b['median_pair_formal_carry_run_p90_bars'])} |",
        f"| Adopted switch delay median | {_num(a['median_pair_adopted_switch_delay_bars'])} | {_num(b['median_pair_adopted_switch_delay_bars'])} |",
        f"| Candidate adoption rate | {_pct(a['median_pair_candidate_adoption_rate'])} | {_pct(b['median_pair_candidate_adoption_rate'])} |",
        f"| Formal dwell median | {_num(a['median_pair_formal_dwell_median_bars'])} | {_num(b['median_pair_formal_dwell_median_bars'])} |",
        f"| Neutral-run median | {_num(a['median_pair_zero_run_median_bars'])} | {_num(b['median_pair_zero_run_median_bars'])} |",
        f"| Neutral-run P90 | {_num(a['median_pair_zero_run_p90_bars'])} | {_num(b['median_pair_zero_run_p90_bars'])} |",
        f"| One-bar formal flips | {a['total_one_bar_formal_flips']} | {b['total_one_bar_formal_flips']} |",
        f"| Formal switches | {a['total_formal_switches']} | {b['total_formal_switches']} |",
        f"| Direct nonzero→nonzero switches | {a['total_direct_nonzero_switches']} | {b['total_direct_nonzero_switches']} |",
        f"| Into-neutral transitions | {a['total_into_zero_transitions']} | {b['total_into_zero_transitions']} |",
        "",
        "## Phase B clear-to-neutral reasons",
        "",
    ]
    reasons = b["clear_to_zero_reasons"]
    lines.extend(
        [
            f"- chaos: **{reasons['chaos']}**",
            f"- persistent weak challenger: **{reasons['weak_challenger']}**",
            f"- coexistence pressure: **{reasons['coexist']}**",
            f"- other: **{reasons['other']}**",
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
    parser = argparse.ArgumentParser(description="Generate Issue #57 Phase-B candidate comparison")
    parser.add_argument("--json-output", type=Path, default=DEFAULT_JSON)
    parser.add_argument("--md-output", type=Path, default=DEFAULT_MD)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    report = write_report(args.json_output, args.md_output)
    print(json.dumps(report["summary"], sort_keys=True))


if __name__ == "__main__":
    main()
