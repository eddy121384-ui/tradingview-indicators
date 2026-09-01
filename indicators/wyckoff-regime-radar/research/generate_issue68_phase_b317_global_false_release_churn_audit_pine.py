#!/usr/bin/env python3
"""Generate Issue #68 B3.17 global false-release / churn TradingView audit."""
from __future__ import annotations

import argparse
from pathlib import Path

import generate_issue68_phase_b316_counterfactual_stale_range_release_audit_pine as b316
from generate_price_only_parity_pine import SOURCE_RELATIVE, replace_once

HERE = Path(__file__).resolve().parent
OLD_DECL = 'indicator("Chase Risk Radar｜Issue #68 B3.16 Stale-Range Release", shorttitle="ChaseRisk #68 B316", overlay=false, precision=2)'
NEW_DECL = 'indicator("Chase Risk Radar｜Issue #68 B3.17 Global Churn", shorttitle="ChaseRisk #68 B317", overlay=false, precision=2)'

BODY = r'''

// Issue #68 B3.17 diagnostic only: global safety audit of the frozen B3.16 shadow.
// Existing B3.16 bands remain above. Extra bands below confirm observed handoffs,
// run-level false-release completion, and repeated advance episodes within one MA-side run.
bool issue68B317ObsTarget = issue68B316ObsRaw > 0.0
bool issue68B317ObsHandoff = issue68B316Ready and issue68B317ObsTarget and not issue68B317ObsTarget[1]
bool issue68B317RunStart = issue68B316Ready and issue68B316MaTarget and not issue68B316MaTarget[1]
bool issue68B317RunEnd = issue68B316Ready and not issue68B316MaTarget and issue68B316MaTarget[1]
bool issue68B317AdvanceStart = issue68B316AdvancedRaw and not issue68B316AdvancedRaw[1]

var int issue68B317PendingAdvanceEpisodes = 0
var int issue68B317RunAdvanceEpisodes = 0
bool issue68B317FlipFlopStart = false
bool issue68B317FalseReleaseConfirm = false

if issue68B317RunStart
    issue68B317PendingAdvanceEpisodes := 0
    issue68B317RunAdvanceEpisodes := 0

if issue68B316MaTarget
    if issue68B317AdvanceStart
        issue68B317PendingAdvanceEpisodes += 1
        issue68B317RunAdvanceEpisodes += 1
        issue68B317FlipFlopStart := issue68B317RunAdvanceEpisodes > 1
    if issue68B317ObsHandoff
        issue68B317PendingAdvanceEpisodes := 0

if issue68B317RunEnd
    issue68B317FalseReleaseConfirm := issue68B317PendingAdvanceEpisodes > 0
    issue68B317PendingAdvanceEpisodes := 0
    issue68B317RunAdvanceEpisodes := 0

float issue68B317ObsHandoffC = -1.0
float issue68B317FalseC = -2.0
float issue68B317FlipC = -3.0

p317ObsHandoffHi = plot(issue68B316Ready ? issue68B317ObsHandoffC + half : na, "B317 OBS HANDOFF top", color=color.new(colNeutral, 100))
p317ObsHandoffLo = plot(issue68B316Ready ? issue68B317ObsHandoffC - half : na, "B317 OBS HANDOFF bottom", color=color.new(colNeutral, 100))
p317FalseHi = plot(issue68B316Ready ? issue68B317FalseC + half : na, "B317 FALSE RELEASE CONFIRM top", color=color.new(colNeutral, 100))
p317FalseLo = plot(issue68B316Ready ? issue68B317FalseC - half : na, "B317 FALSE RELEASE CONFIRM bottom", color=color.new(colNeutral, 100))
p317FlipHi = plot(issue68B316Ready ? issue68B317FlipC + half : na, "B317 FLIPFLOP START top", color=color.new(colNeutral, 100))
p317FlipLo = plot(issue68B316Ready ? issue68B317FlipC - half : na, "B317 FLIPFLOP START bottom", color=color.new(colNeutral, 100))

fill(p317ObsHandoffHi, p317ObsHandoffLo, color=issue68B317ObsHandoff ? color.new(color.aqua, 0) : color.new(colNeutral, 82), title="B317 OBS HANDOFF band")
fill(p317FalseHi, p317FalseLo, color=issue68B317FalseReleaseConfirm ? color.new(colRed, 0) : color.new(colNeutral, 82), title="B317 FALSE RELEASE CONFIRM band")
fill(p317FlipHi, p317FlipLo, color=issue68B317FlipFlopStart ? color.new(color.fuchsia, 0) : color.new(colNeutral, 82), title="B317 FLIPFLOP START band")

plot(issue68B317PendingAdvanceEpisodes, "B317 pending advance episodes", display=display.data_window)
plot(issue68B317RunAdvanceEpisodes, "B317 advance episodes in current MA run", display=display.data_window)
'''.strip()


def generate(source: Path) -> str:
    out = b316.generate(source)
    out = replace_once(out, OLD_DECL, NEW_DECL)
    out = out.rstrip() + "\n\n" + BODY + "\n"
    for token in (
        "B316 OBS RAW band",
        "B316 SHADOW RAW band",
        "B316 STALE OVERLAP band",
        "B316 RAW ADVANCE band",
        "B317 OBS HANDOFF band",
        "B317 FALSE RELEASE CONFIRM band",
        "B317 FLIPFLOP START band",
    ):
        if token not in out:
            raise RuntimeError(f"missing B3.17 audit token: {token}")
    if "strategy." in out:
        raise RuntimeError("strategy token leaked into B3.17 diagnostic")
    return out


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--source", type=Path, default=HERE / SOURCE_RELATIVE)
    ap.add_argument("--output", type=Path, required=True)
    args = ap.parse_args()
    text = generate(args.source)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(text, encoding="utf-8")
    print(args.output)


if __name__ == "__main__":
    main()
