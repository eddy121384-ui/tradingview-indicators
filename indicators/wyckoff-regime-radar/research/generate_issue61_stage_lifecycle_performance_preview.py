#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path

from generate_issue61_stage_lifecycle_strategy_preview import build as build_visual

HERE = Path(__file__).resolve().parent
OUTPUT = HERE / "generated" / "wyckoff-issue-61-stage-lifecycle-performance-preview.pine"

VISUAL_DECL = 'strategy("Chase Risk Radar v0.6｜Stage Lifecycle Strategy Preview", shorttitle="ChaseRisk v0.6 STRAT", overlay=true, precision=5, pyramiding=0, default_qty_type=strategy.fixed, default_qty_value=1, commission_type=strategy.commission.percent, commission_value=0.02, process_orders_on_close=false, max_labels_count=500, max_lines_count=500)'

PERFORMANCE_DECL = 'strategy("Chase Risk Radar v0.6｜Stage Lifecycle Performance Preview", shorttitle="ChaseRisk v0.6 PERF", overlay=true, precision=5, pyramiding=0, initial_capital=100000, currency=currency.USD, default_qty_type=strategy.percent_of_equity, default_qty_value=50, commission_type=strategy.commission.percent, commission_value=0.02, process_orders_on_close=false, margin_long=100, margin_short=100, max_labels_count=500, max_lines_count=500)'


def build() -> str:
    """Use the exact human-review lifecycle; replace sizing declaration only."""
    text = build_visual()
    if text.count(VISUAL_DECL) != 1:
        raise RuntimeError("expected exactly one visual strategy declaration")
    out = text.replace(VISUAL_DECL, PERFORMANCE_DECL, 1)
    if VISUAL_DECL in out:
        raise RuntimeError("visual declaration remained after performance conversion")
    return out


def main() -> None:
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(build(), encoding="utf-8")
    print(OUTPUT)


if __name__ == "__main__":
    main()
