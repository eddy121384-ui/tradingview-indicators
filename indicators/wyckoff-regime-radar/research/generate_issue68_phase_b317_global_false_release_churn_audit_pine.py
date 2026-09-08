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

# B3.17 no longer carries the whole B3.16 visual museum.  The B3.16 calculations
# remain frozen and are reused below, but old Break/New-Range/Blocker bands are
# removed so TradingView stays comfortably below the 64-plot limit.
DROP_PREFIXES = (
    "p1h = plot(", "p1l = plot(",      # B316 OBS BREAK
    "p2h = plot(", "p2l = plot(",      # B316 SHADOW BREAK
    "p6h = plot(", "p6l = plot(",      # B316 NEW RANGE
    "p7h = plot(", "p7l = plot(",      # B316 BREAK RELEASE
    "p9h = plot(", "p9l = plot(",      # B316 BREAK BLOCKER
    "fill(p1h, p1l,", "fill(p2h, p2l,",
    "fill(p6h, p6l,", "fill(p7h, p7l,", "fill(p9h, p9l,",
    "plot(issue68B316ObsBreak,", "plot(issue68B316ShadowBreak,",
)

BODY = r'''

// Issue #68 B3.17 diagnostic only: global safety audit of the frozen B3.16 shadow.
// Lean visual: keep only OBS RAW / SHADOW RAW / STALE OVERLAP / RAW ADVANCE
// from B3.16, then add three single-plot event markers for the B3.17 safety gate.
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

// Single plots instead of top/bottom+fill bands: three plot counts total.
plot(issue68B317ObsHandoff ? 0.0 : na, "B317 OBS HANDOFF", color=color.aqua, linewidth=4, style=plot.style_circles)
plot(issue68B317FalseReleaseConfirm ? -1.0 : na, "B317 FALSE RELEASE CONFIRM", color=colRed, linewidth=4, style=plot.style_circles)
plot(issue68B317FlipFlopStart ? -2.0 : na, "B317 FLIPFLOP START", color=color.fuchsia, linewidth=4, style=plot.style_circles)
'''.strip()


def slim_b316_visual(text: str) -> str:
    lines = []
    for line in text.splitlines():
        stripped = line.strip()
        if any(stripped.startswith(prefix) for prefix in DROP_PREFIXES):
            continue
        lines.append(line)
    return "\n".join(lines)


def generate(source: Path) -> str:
    out = b316.generate(source)
    out = replace_once(out, OLD_DECL, NEW_DECL)
    out = slim_b316_visual(out)
    out = out.rstrip() + "\n\n" + BODY + "\n"

    # Only the four B3.16 bands needed by the B3.17 safety question survive.
    for token in (
        "B316 OBS RAW band",
        "B316 SHADOW RAW band",
        "B316 STALE OVERLAP band",
        "B316 RAW ADVANCE band",
        '"B317 OBS HANDOFF"',
        '"B317 FALSE RELEASE CONFIRM"',
        '"B317 FLIPFLOP START"',
    ):
        if token not in out:
            raise RuntimeError(f"missing B3.17 audit token: {token}")

    for removed in (
        "B316 OBS BREAK band",
        "B316 SHADOW BREAK band",
        "B316 NEW RANGE band",
        "B316 BREAK RELEASE band",
        "B316 BREAK FINAL BLOCKER band",
    ):
        if removed in out:
            raise RuntimeError(f"legacy B3.16 visual leaked into B3.17: {removed}")

    if "strategy." in out:
        raise RuntimeError("strategy token leaked into B3.17 diagnostic")

    # Conservative source-level plot budget guard.  Dynamic fills also consume
    # TradingView plot counts, so count them explicitly and leave headroom.
    budget = out.count("plot(") + out.count("plotshape(") + out.count("plotchar(") + out.count("fill(")
    if budget > 58:
        raise RuntimeError(f"B3.17 visual plot budget too high: {budget} > 58")
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
