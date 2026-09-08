#!/usr/bin/env python3
"""Add preregistered primary-vs-context population summaries to B3.15 reports."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from diagnose_issue68_phase_b315_event_window_stale_memory import summarize_events


def collect_rows(report: dict[str, Any]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for pair in report["pairs"].values():
        for side in ("bull", "bear"):
            rows.extend(pair[side]["events"])
    return rows


def compact(x: dict[str, Any]) -> dict[str, Any]:
    return {
        "events": x["events"],
        "event_related_ma_flip_found": x["event_related_ma_flip_found"],
        "event_related_ma_flip_censored": x["event_related_ma_flip_censored"],
        "old_range_survival": x["old_range_survival"],
        "new_range_delay": x["new_range_delay"],
        "break_release_delay": x["break_release_delay"],
        "stale_overlap_bars": x["stale_overlap_bars"],
        "break_old_overlap_bars": x["break_old_overlap_bars"],
        "break_target_overlap_bars": x["break_target_overlap_bars"],
        "break_zero_overlap_bars": x["break_zero_overlap_bars"],
        "break_old_overlap_share": x["break_old_overlap_share"],
        "new_range_before_old_clear_comparable": x["new_range_before_old_clear_comparable"],
        "new_range_before_old_clear": x["new_range_before_old_clear"],
        "new_range_before_old_clear_share": x["new_range_before_old_clear_share"],
    }


def fmt_timing(x: dict[str, Any]) -> str:
    if x["uncensored"] == 0:
        return f"no uncensored values; censored={x['censored']}"
    return (
        f"median={x['median']:.1f}, p75={x['p75']:.1f}, max={x['max']}, "
        f"uncensored={x['uncensored']}, censored={x['censored']}"
    )


def section(name: str, x: dict[str, Any], interpretation: str) -> list[str]:
    return [
        f"### {name}",
        "",
        f"- events: **{x['events']}**",
        f"- event-related MA flip found / censored: **{x['event_related_ma_flip_found']} / {x['event_related_ma_flip_censored']}**",
        f"- old range-memory survival: **{fmt_timing(x['old_range_survival'])}**",
        f"- target range-evidence delay: **{fmt_timing(x['new_range_delay'])}**",
        f"- Break release delay: **{fmt_timing(x['break_release_delay'])}**",
        f"- stale-overlap bars: **{x['stale_overlap_bars']}**",
        f"- Break old-negative during overlap: **{x['break_old_overlap_bars']} / {x['stale_overlap_bars']} ({100*x['break_old_overlap_share']:.1f}%)**",
        f"- Break target-positive during overlap: **{x['break_target_overlap_bars']}**; zero: **{x['break_zero_overlap_bars']}**",
        f"- target range before old memory clears: **{x['new_range_before_old_clear']} / {x['new_range_before_old_clear_comparable']} ({100*x['new_range_before_old_clear_share']:.1f}%)**",
        f"- interpretation boundary: {interpretation}",
        "",
    ]


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--report-json", type=Path, required=True)
    ap.add_argument("--report-md", type=Path, required=True)
    args = ap.parse_args()

    report = json.loads(args.report_json.read_text(encoding="utf-8"))
    rows = collect_rows(report)
    primary_rows = [r for r in rows if r["population"] == "MA_TARGET_AT_BLOCKER"]
    context_rows = [r for r in rows if r["population"] == "PRE_MA_FLIP_AT_BLOCKER"]
    if len(primary_rows) + len(context_rows) != len(rows):
        raise AssertionError("unexplained B3.15 population row")

    primary = compact(summarize_events(primary_rows))
    context = compact(summarize_events(context_rows))
    report["aggregate"]["primary_ma_target_at_blocker_summary"] = primary
    report["aggregate"]["pre_ma_flip_context_summary"] = context
    args.report_json.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")

    md = args.report_md.read_text(encoding="utf-8").rstrip()
    lines = [md, "", "## Preregistered population split", ""]
    lines += section(
        "Primary causal population — MA already target-side at blocker",
        primary,
        "eligible evidence for stale memory after the market has already moved to the new MA side.",
    )
    lines += section(
        "Context population — blocker occurs before MA flip",
        context,
        "timing context only; these events cannot by themselves prove stale memory after an MA turn.",
    )
    args.report_md.write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")
    print("B3.15 preregistered population split appended")


if __name__ == "__main__":
    main()
