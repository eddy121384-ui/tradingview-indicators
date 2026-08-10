#!/usr/bin/env python3
"""Generate the deterministic Issue #57 Phase-A boundary-robustness report.

The report intentionally contains no return, PnL, or Final-OOS evaluation. It
summarizes local counterfactual continuity on the already-observed Issue #55
Development-era fixtures so the v0.6 structural redesign can be audited without
mining GitHub Actions logs.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from diagnose_v06_boundary_sensitivity import run_sweep
from diagnose_v06_breakout20_sensitivity import run_breakout20_sweep
from generate_v06_price_only_core import EXPECTED_BASELINE_GIT_BLOB_SHA
from v06_boundary_scores import SOFT_BOUNDARY_WIDTH_ATR


HERE = Path(__file__).resolve().parent
DEFAULT_JSON = HERE / "reports" / "issue-57-phase-a-boundary-robustness.json"
DEFAULT_MD = HERE / "reports" / "issue-57-phase-a-boundary-robustness.md"


def _ratio(new: float | None, old: float | None) -> float | None:
    if new is None or old is None or old == 0.0:
        return None
    return float(new / old)


def _reduction_pct(new: float | None, old: float | None) -> float | None:
    ratio = _ratio(new, old)
    return None if ratio is None else float((1.0 - ratio) * 100.0)


def _compact_case(row: dict[str, Any]) -> dict[str, Any]:
    return {
        "pair": row["pair"],
        "side": row["side"],
        "date": row["date"],
        "v05_probability_l1_jump": row["v05_probability_l1_jump"],
        "v06_probability_l1_jump": row["v06_probability_l1_jump"],
        "v05_top": row.get("v05_top", [row.get("v05_top_id_below"), row.get("v05_top_id_above")]),
        "v06_top": row.get("v06_top", [row.get("v06_top_id_below"), row.get("v06_top_id_above")]),
        "v05_candidate": row.get(
            "v05_candidate",
            [row.get("v05_candidate_below"), row.get("v05_candidate_above")],
        ),
        "v06_candidate": row.get(
            "v06_candidate",
            [row.get("v06_candidate_below"), row.get("v06_candidate_above")],
        ),
    }


def build_report() -> dict[str, Any]:
    boundary50 = run_sweep()
    breakout20 = run_breakout20_sweep()

    summary50 = boundary50["summary"]
    summary20 = breakout20["summary"]
    worst50 = max(boundary50["cases"], key=lambda row: float(row["v06_probability_l1_jump"]))
    worst20 = breakout20["worst_toggled_case"]

    return {
        "issue": 57,
        "phase": "A",
        "status": "diagnostic_complete_pending_phase_review",
        "scope": {
            "purpose": "local boundary robustness only",
            "data": "Issue #55 Development-era frozen FX inputs",
            "pnl_evaluated": False,
            "final_oos_evaluated": False,
            "old_final_oos_is_burned": True,
        },
        "preservation": {
            "v05_python_mirror_git_blob_sha": EXPECTED_BASELINE_GIT_BLOB_SHA,
            "v05_pine_modified": False,
        },
        "design": {
            "soft_boundary_width_atr": SOFT_BOUNDARY_WIDTH_ATR,
            "selection_basis": "fixed engineering transition width; not selected from trading PnL",
            "changed_boundary_families": [
                "50-bar no-break score",
                "50-bar structural continuation strength",
                "20-bar range-break evidence strength",
                "range-break downstream gates",
            ],
            "intentionally_unchanged": [
                "MA-cross evidence semantics",
                "breakout/breakdown mode semantics",
                "formal-state confirmation and persistence",
                "state cardinality",
                "Volume/MTF/Divergence/HMM",
                "trading response map",
            ],
        },
        "boundary_50bar": {
            "summary": summary50,
            "median_probability_l1_reduction_pct": _reduction_pct(
                float(summary50["median_v06_probability_l1_jump"]),
                float(summary50["median_v05_probability_l1_jump"]),
            ),
            "median_dist_markdown_reduction_pct": _reduction_pct(
                float(summary50["median_v06_dist_markdown_jump"]),
                float(summary50["median_v05_dist_markdown_jump"]),
            ),
            "worst_v06_case": _compact_case(worst50),
        },
        "breakout_20bar": {
            "summary": summary20,
            "median_probability_l1_reduction_pct": _reduction_pct(
                float(summary20["median_v06_l1_all"]),
                float(summary20["median_v05_l1_all"]),
            ),
            "worst_toggled_case": _compact_case(worst20) if worst20 is not None else None,
            "worst_toggled_path": worst20.get("v06_path") if worst20 is not None else None,
        },
        "interpretation_boundary": (
            "A lower local discontinuity is evidence of improved numerical/feed robustness only. "
            "It is not evidence of predictive utility, profitability, calibrated confidence, or "
            "successful independent OOS validation."
        ),
    }


def _fmt(value: float | None, digits: int = 6) -> str:
    return "—" if value is None else f"{value:.{digits}f}"


def render_markdown(report: dict[str, Any]) -> str:
    s50 = report["boundary_50bar"]["summary"]
    s20 = report["breakout_20bar"]["summary"]
    w50 = report["boundary_50bar"]["worst_v06_case"]
    w20 = report["breakout_20bar"]["worst_toggled_case"]

    lines = [
        "# Issue #57 — v0.6 Phase A boundary robustness",
        "",
        "Status: **diagnostic_complete_pending_phase_review**",
        "",
        "This report measures local price-boundary continuity only. It does **not** evaluate PnL or reuse the burned Issue #55 Final OOS as an independent test.",
        "",
        "## Preservation / design boundary",
        "",
        f"- Frozen v0.5 Python mirror blob: `{report['preservation']['v05_python_mirror_git_blob_sha']}`",
        "- Frozen v0.5.2.1 Pine source: unchanged.",
        f"- Soft transition width: **{report['design']['soft_boundary_width_atr']:.2f} ATR**; fixed as an engineering width, not selected from trading PnL.",
        "- Formal-state persistence, state count, witnesses, HMM, and trading response remain unchanged in Phase A.",
        "",
        "## 50-bar structural boundary counterfactual",
        "",
        "| Metric | v0.5 | v0.6 |",
        "|---|---:|---:|",
        f"| Median six-weight L1 jump | {_fmt(float(s50['median_v05_probability_l1_jump']))} | {_fmt(float(s50['median_v06_probability_l1_jump']))} |",
        f"| Median Distribution+Markdown jump | {_fmt(float(s50['median_v05_dist_markdown_jump']))} | {_fmt(float(s50['median_v06_dist_markdown_jump']))} |",
        f"| Named no-break primitive jump | {_fmt(float(s50['v05_hard_primitive_jump']))} | {_fmt(float(s50['median_v06_soft_primitive_jump']))} |",
        "",
        f"- Median six-weight discontinuity reduction: **{_fmt(report['boundary_50bar']['median_probability_l1_reduction_pct'], 3)}%**.",
        f"- v0.6 lower/equal/higher cases: **{s50['v06_probability_jump_lower_cases']} / {s50['v06_probability_jump_equal_cases']} / {s50['v06_probability_jump_higher_cases']}**.",
        f"- Worst remaining v0.6 case: **{w50['pair']} {w50['side']} {w50['date']}**, L1 jump **{_fmt(float(w50['v06_probability_l1_jump']))}**.",
        "",
        "## 20-bar breakout / breakdown counterfactual",
        "",
        "| Metric | v0.5 | v0.6 |",
        "|---|---:|---:|",
        f"| Median six-weight L1 jump, all cases | {_fmt(float(s20['median_v05_l1_all']))} | {_fmt(float(s20['median_v06_l1_all']))} |",
        f"| Max v0.6 jump among actual event toggles | — | {_fmt(s20['max_v06_l1_toggled'])} |",
        "",
        f"- Event toggles: **{s20['event_toggle_cases']} / {s20['case_count']}**; isolated from the 50-bar transition band: **{s20['event_toggle_isolated_from_50bar_band_cases']}**.",
        f"- Median six-weight discontinuity reduction: **{_fmt(report['breakout_20bar']['median_probability_l1_reduction_pct'], 3)}%**.",
    ]
    if w20 is not None:
        lines.append(
            f"- Worst remaining toggled case: **{w20['pair']} {w20['side']} {w20['date']}**, L1 jump **{_fmt(float(w20['v06_probability_l1_jump']))}**."
        )

    lines.extend(
        [
            "",
            "## Interpretation boundary",
            "",
            report["interpretation_boundary"],
            "",
            "Phase A should be accepted or expanded based on the residual discontinuity shown above. Do not infer trading improvement from this report.",
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
    parser = argparse.ArgumentParser(description="Generate Issue #57 Phase-A robustness report")
    parser.add_argument("--json-output", type=Path, default=DEFAULT_JSON)
    parser.add_argument("--md-output", type=Path, default=DEFAULT_MD)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    report = write_report(args.json_output, args.md_output)
    print(json.dumps(report["boundary_50bar"]["summary"], sort_keys=True))
    print(json.dumps(report["breakout_20bar"]["summary"], sort_keys=True))


if __name__ == "__main__":
    main()
