#!/usr/bin/env python3
"""Generate the warm-up-excluded Issue #57 Phase-B decision report."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from diagnose_v06_phase_b_live_window import run_live_window_audit


HERE = Path(__file__).resolve().parent
DEFAULT_JSON = HERE / "reports" / "issue-57-phase-b-live-window.json"
DEFAULT_MD = HERE / "reports" / "issue-57-phase-b-live-window.md"


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
        **run_live_window_audit(),
        "status": "live_window_engineering_sweep_complete_pending_phase_b_choice",
        "decision_boundary": (
            "Use this warm-up-excluded report, not the superseded raw-history neutral statistics, "
            "to choose the Phase-B stale-decay horizon. Choice must be based on stale carry versus "
            "Neutral/switch churn, not PnL."
        ),
    }


def render_markdown(report: dict[str, Any]) -> str:
    summary = report["summary"]
    confirm = report["confirm_bars"]
    carry = report["phase_a_carry_decomposition"]
    keys = ["phase_a", "stale_decay_1x", "stale_decay_2x", "stale_decay_3x"]

    def vals(key: str, kind: str = "num") -> str:
        fn = _pct if kind == "pct" else _num
        return " | ".join(fn(summary[name][key]) for name in keys)

    lines = [
        "# Issue #57 — v0.6 Phase B live-window persistence decision",
        "",
        "Status: **live_window_engineering_sweep_complete_pending_phase_b_choice**",
        "",
        report["scope"],
        "",
        "The earlier raw-history Neutral statistics are superseded for the Phase-B choice because they included the long indicator warm-up.",
        "",
        "## Live windows",
        "",
        "| Pair | First live index | First live date | Live bars |",
        "|---|---:|---|---:|",
    ]
    for row in report["live_windows"]:
        lines.append(
            f"| {row['pair']} | {row['live_start_index']} | {row.get('live_start_date', '—')} | {row['live_bars']} |"
        )

    lines.extend(
        [
            "",
            "## Phase-A Formal carry after warm-up",
            "",
            f"Formal carry share: **{_pct(carry['formal_carry_share'])}** of live bars.",
            "",
            "| Carry category | Share of live carry | Share of all live bars |",
            "|---|---:|---:|",
        ]
    )
    labels = {
        "chaos": "Chaos pending clear",
        "weak_challenger": "Weak opposing challenger",
        "weak_same_state": "Weak support for current Formal",
        "coexist_no_display": "Coexistence / no display",
        "neutral_no_candidate": "Neutral no candidate",
    }
    for key, label in labels.items():
        row = carry["categories"][key]
        lines.append(
            f"| {label} | {_pct(row['share_of_live_carry_bars'])} | {_pct(row['share_of_all_live_bars'])} |"
        )

    lines.extend(
        [
            "",
            "Weak-challenger follow-through after warm-up:",
            "",
            "| Window | Eligible runs | Formal adopts | Strong candidate emerges |",
            "|---|---:|---:|---:|",
        ]
    )
    for window in ("5", "10"):
        row = carry["weak_challenger_followthrough"][window]
        lines.append(
            f"| {window} bars | {row['eligible_runs']} | {_pct(row['formal_adoption_rate'])} | {_pct(row['strong_candidate_emergence_rate'])} |"
        )

    lines.extend(
        [
            "",
            "## Warm-up-excluded stale-decay sweep",
            "",
            f"Existing `confirm_bars` = **{confirm}**; candidate horizons = **{confirm} / {confirm * 2} / {confirm * 3} bars**.",
            "",
            "| Metric | Phase A | 1× | 2× | 3× |",
            "|---|---:|---:|---:|---:|",
            f"| Formal carry share | {vals('median_pair_formal_carry_share', 'pct')} |",
            f"| Formal zero share | {vals('median_pair_formal_zero_share', 'pct')} |",
            f"| Carry-run P90 | {vals('median_pair_carry_run_p90_bars')} |",
            f"| Disagreement / strong-candidate bars | {vals('median_pair_disagreement_share_candidate_bars', 'pct')} |",
            f"| Formal dwell median | {vals('median_pair_formal_dwell_median_bars')} |",
            f"| Neutral-run median | {vals('median_pair_zero_run_median_bars')} |",
            f"| Neutral-run P90 | {vals('median_pair_zero_run_p90_bars')} |",
            f"| One-bar Formal flips | {vals('total_one_bar_formal_flips')} |",
            f"| Total Formal switches | {vals('total_formal_switches')} |",
            f"| Into-Neutral transitions | {vals('total_into_zero_transitions')} |",
            "",
            "## Engineering cost relative to Phase A",
            "",
            "| Candidate | Carry reduction | Formal-zero increase | Added switches | Added into-Neutral |",
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
    parser = argparse.ArgumentParser(description="Generate warm-up-excluded Phase-B report")
    parser.add_argument("--json-output", type=Path, default=DEFAULT_JSON)
    parser.add_argument("--md-output", type=Path, default=DEFAULT_MD)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    report = write_report(args.json_output, args.md_output)
    print(json.dumps(report["summary"], sort_keys=True))


if __name__ == "__main__":
    main()
