#!/usr/bin/env python3
"""Generate Issue #57 Phase-B stale-decay horizon engineering sweep report."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from diagnose_v06_phase_b_decay_sweep import run_decay_sweep


HERE = Path(__file__).resolve().parent
DEFAULT_JSON = HERE / "reports" / "issue-57-phase-b-decay-horizon-sweep.json"
DEFAULT_MD = HERE / "reports" / "issue-57-phase-b-decay-horizon-sweep.md"


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
        **run_decay_sweep(),
        "status": "engineering_sweep_complete_pending_phase_b_choice",
        "decision_boundary": (
            "Choose among exact 1x/2x/3x multiples of the existing confirm_bars using only the engineering "
            "trade-off between stale carry reduction and added Neutral/switch churn. Do not use PnL."
        ),
    }


def render_markdown(report: dict[str, Any]) -> str:
    summary = report["summary"]
    confirm = report["confirm_bars"]
    lines = [
        "# Issue #57 — v0.6 Phase B stale-decay horizon sweep",
        "",
        "Status: **engineering_sweep_complete_pending_phase_b_choice**",
        "",
        report["scope"],
        "",
        f"Existing `confirm_bars` = **{confirm}**. Candidate stale-decay horizons are exactly **{confirm} / {confirm * 2} / {confirm * 3} bars**.",
        "",
        "| Metric | Phase A | 1× | 2× | 3× |",
        "|---|---:|---:|---:|---:|",
    ]

    keys = ["phase_a", "stale_decay_1x", "stale_decay_2x", "stale_decay_3x"]

    def values(key: str, kind: str = "num") -> str:
        formatter = _pct if kind == "pct" else _num
        return " | ".join(formatter(summary[name][key]) for name in keys)

    lines.extend(
        [
            f"| Formal carry share | {values('median_pair_formal_carry_share', 'pct')} |",
            f"| Formal zero share | {values('median_pair_formal_zero_share', 'pct')} |",
            f"| Carry-run P90 (bars) | {values('median_pair_carry_run_p90_bars')} |",
            f"| Strong-candidate disagreement share | {values('median_pair_disagreement_share_candidate_bars', 'pct')} |",
            f"| Formal dwell median (bars) | {values('median_pair_formal_dwell_median_bars')} |",
            f"| Neutral-run median (bars) | {values('median_pair_zero_run_median_bars')} |",
            f"| Neutral-run P90 (bars) | {values('median_pair_zero_run_p90_bars')} |",
            f"| One-bar formal flips | {values('total_one_bar_formal_flips')} |",
            f"| Total formal switches | {values('total_formal_switches')} |",
            f"| Into-neutral transitions | {values('total_into_zero_transitions')} |",
            "",
            "## Cost of decay relative to Phase A",
            "",
            "| Candidate | Carry reduction | Formal-zero increase | Added Formal switches | Added into-neutral transitions |",
            "|---|---:|---:|---:|---:|",
        ]
    )
    for multiplier in report["multipliers"]:
        row = summary[f"stale_decay_{multiplier}x"]
        lines.append(
            f"| {multiplier}× ({confirm * multiplier} bars) | {_pct(row['carry_reduction_relative'])} | {_num(row['formal_zero_increase_percentage_points'])} pp | {row['additional_formal_switches']} | {row['additional_into_zero_transitions']} |"
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
    parser = argparse.ArgumentParser(description="Generate Issue #57 Phase-B stale-decay sweep")
    parser.add_argument("--json-output", type=Path, default=DEFAULT_JSON)
    parser.add_argument("--md-output", type=Path, default=DEFAULT_MD)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    report = write_report(args.json_output, args.md_output)
    print(json.dumps(report["summary"], sort_keys=True))


if __name__ == "__main__":
    main()
