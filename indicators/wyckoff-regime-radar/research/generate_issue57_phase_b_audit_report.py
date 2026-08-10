#!/usr/bin/env python3
"""Generate the Issue #57 Phase-B persistence audit report.

No persistence rule is changed by this report. It records the pathology first so
any later confirmation/inertia redesign has an explicit baseline.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from diagnose_v06_state_persistence import run_persistence_audit


HERE = Path(__file__).resolve().parent
DEFAULT_JSON = HERE / "reports" / "issue-57-phase-b-persistence-audit.json"
DEFAULT_MD = HERE / "reports" / "issue-57-phase-b-persistence-audit.md"


def _pct(value: float | None) -> str:
    return "—" if value is None else f"{value * 100.0:.2f}%"


def _num(value: float | int | None, digits: int = 2) -> str:
    if value is None:
        return "—"
    if isinstance(value, int):
        return str(value)
    return f"{value:.{digits}f}"


def build_report() -> dict[str, Any]:
    audit = run_persistence_audit()
    return {
        **audit,
        "status": "audit_complete_pending_persistence_redesign",
        "definitions": {
            "strong_candidate": "internal candidate_id != 0; weak display-only candidates are excluded",
            "candidate_formal_disagreement": "strong candidate exists and differs from formal_id",
            "formal_carry": "formal_id remains nonzero while no strong candidate exists",
            "switch_demand_run": "a contiguous nonzero strong-candidate run whose stage differs from formal_id at run start",
            "adoption_delay": "bars from switch-demand run start until formal_id first adopts that candidate within the same run",
            "one_bar_flip": "formal path A -> B -> A over three consecutive bars",
        },
        "decision_boundary": (
            "This audit does not choose new confirmBars, fast-switch thresholds, or any PnL-optimal rule. "
            "It only identifies where the current formal-state machine is stale, noisy, or appropriately persistent."
        ),
    }


def render_markdown(report: dict[str, Any]) -> str:
    summary = report["summary"]
    lines = [
        "# Issue #57 — v0.6 Phase B persistence audit",
        "",
        "Status: **audit_complete_pending_persistence_redesign**",
        "",
        report["scope"],
        "",
        "No persistence parameter is changed in this report, and no PnL is evaluated.",
        "",
        "## Cross-pair summary",
        "",
        "| Metric | v0.5.2.1 | v0.6 Phase A |",
        "|---|---:|---:|",
    ]

    v05 = summary["v0.5.2.1"]
    v06 = summary["v0.6-phase-a"]
    metrics = [
        ("Strong-candidate bars disagreeing with Formal", "median_pair_disagreement_share_candidate_bars", "pct"),
        ("All bars with Candidate/Formal disagreement", "median_pair_disagreement_share_all_bars", "pct"),
        ("Formal carried with no strong candidate", "median_pair_formal_carry_share", "pct"),
        ("P90 disagreement-run length (bars)", "median_pair_disagreement_run_p90_bars", "num"),
        ("P90 carry-run length (bars)", "median_pair_formal_carry_run_p90_bars", "num"),
        ("Median adopted switch delay (bars)", "median_pair_adopted_switch_delay_bars", "num"),
        ("Candidate-run adoption rate", "median_pair_candidate_adoption_rate", "pct"),
        ("Median formal dwell duration (bars)", "median_pair_formal_dwell_median_bars", "num"),
        ("Total one-bar formal flips", "total_one_bar_formal_flips", "num"),
        ("Total formal switches", "total_formal_switches", "num"),
    ]
    for label, key, kind in metrics:
        formatter = _pct if kind == "pct" else _num
        lines.append(f"| {label} | {formatter(v05[key])} | {formatter(v06[key])} |")

    lines.extend(["", "## Per-pair v0.6 Phase-A state-machine baseline", ""])
    lines.append(
        "| Pair | Disagree / candidate bars | Formal carry | Disagree P90 | Carry P90 | Adopt delay median | Adoption rate | Dwell median | 1-bar flips / switches |"
    )
    lines.append("|---|---:|---:|---:|---:|---:|---:|---:|---:|")
    for row in report["rows"]:
        if row["engine"] != "v0.6-phase-a":
            continue
        adoption = row["candidate_adoption"]
        lines.append(
            "| {pair} | {disagree} | {carry} | {dp90} | {cp90} | {delay} | {adopt} | {dwell} | {flips}/{switches} |".format(
                pair=row["pair"],
                disagree=_pct(row["candidate_formal_disagreement_share_candidate_bars"]),
                carry=_pct(row["formal_carry_without_strong_candidate_share"]),
                dp90=_num(row["candidate_formal_disagreement_run_bars"]["p90"]),
                cp90=_num(row["formal_carry_run_bars"]["p90"]),
                delay=_num(adoption["adopted_delay_bars"]["median"]),
                adopt=_pct(adoption["adoption_rate"]),
                dwell=_num(row["formal_dwell_bars_all_states"]["median"]),
                flips=row["one_bar_formal_flips"],
                switches=row["formal_switches"],
            )
        )

    lines.extend(
        [
            "",
            "## Definitions",
            "",
            "- Candidate/Formal disagreement counts only **strong** internal candidates, not weak display-only candidates.",
            "- Formal carry means a nonzero Formal state remains active while `candidate_id == 0`.",
            "- Adoption delay is measured only when a new strong-candidate run begins in a state different from Formal.",
            "- One-bar flip is the exact pattern `A -> B -> A`.",
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
    parser = argparse.ArgumentParser(description="Generate Issue #57 Phase-B persistence audit")
    parser.add_argument("--json-output", type=Path, default=DEFAULT_JSON)
    parser.add_argument("--md-output", type=Path, default=DEFAULT_MD)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    report = write_report(args.json_output, args.md_output)
    print(json.dumps(report["summary"], sort_keys=True))


if __name__ == "__main__":
    main()
