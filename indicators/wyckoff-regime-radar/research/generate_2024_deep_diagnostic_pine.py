#!/usr/bin/env python3
"""Generate a focused 2024-04-16 TradingView diagnostic harness for Issue #55.

This layers one compact table onto the already-mechanical price-only parity
harness. It does not add plots or change the frozen calculation core. The table
captures intermediate values on the first OANDA daily bar whose close time
reaches 2024-04-16, allowing the Distribution-vs-Markdown divergence to be
localized against the Python/Yahoo diagnostic.
"""

from __future__ import annotations

import argparse
from pathlib import Path

from generate_price_only_parity_pine import SOURCE_RELATIVE, generate as generate_base


DEEP_TABLE = r'''
// === Issue #55 2024-04-16 deep divergence diagnostic ===
// No extra plots: one compact table captures the intermediate decision chain.
var bool deepCaptured = false
var string deepBarDate = "—"

var float dSpeedRank = na
var float dAccelRank = na
var float dDistRank = na
var float dHeatUp = na
var float dPanicHeat = na
var float dMatUp = na
var float dMatDn = na
var float dRangeScore = na

var float dUpExh = na
var float dResistHold = na
var float dDistRaw = na
var float dDistGatePct = na
var float dDistEff = na
var float dProbDist = na
var float dTopGap = na
var float dEvidence = na

var float dDownExh = na
var float dSupportHold = na
var float dMdExt = na
var float dMdCont = na
var float dMdRaw = na
var float dMdGatePct = na
var float dMdEff = na
var float dProbMd = na

deepTs = timestamp(syminfo.timezone, 2024, 4, 16, 0, 0)
if not deepCaptured and time_close >= deepTs
    deepCaptured := true
    deepBarDate := str.format_time(time_close, "yyyy-MM-dd", syminfo.timezone)

    dSpeedRank := speedRank
    dAccelRank := accelRank
    dDistRank := distRank
    dHeatUp := heatUp
    dPanicHeat := panicHeatDn
    dMatUp := maturityUp
    dMatDn := maturityDn
    dRangeScore := rangeScore

    dUpExh := upsideExhaustion
    dResistHold := resistanceHolding
    dDistRaw := distRaw
    dDistGatePct := distGate * 100.0
    dDistEff := distEff
    dProbDist := probDist
    dTopGap := topGap
    dEvidence := evidenceStrength

    dDownExh := downsideExhaustion
    dSupportHold := supportHolding
    dMdExt := markdownExtensionScore
    dMdCont := markdownContinuationScore
    dMdRaw := markdownRaw
    dMdGatePct := markdownGate * 100.0
    dMdEff := markdownEff
    dProbMd := probMarkdown

var table deepTable = table.new(position.bottom_right, 6, 9, border_width=1)
if barstate.islast
    table.cell(deepTable, 0, 0, "2024 deep", text_size=size.tiny)
    table.cell(deepTable, 1, 0, deepBarDate, text_size=size.tiny)
    table.cell(deepTable, 2, 0, "Dist path", text_size=size.tiny)
    table.cell(deepTable, 3, 0, "TV", text_size=size.tiny)
    table.cell(deepTable, 4, 0, "Markdown path", text_size=size.tiny)
    table.cell(deepTable, 5, 0, "TV", text_size=size.tiny)

    table.cell(deepTable, 0, 1, "SpeedRank", text_size=size.tiny)
    table.cell(deepTable, 1, 1, f_cp1(dSpeedRank), text_size=size.tiny)
    table.cell(deepTable, 2, 1, "UpExh", text_size=size.tiny)
    table.cell(deepTable, 3, 1, f_cp1(dUpExh), text_size=size.tiny)
    table.cell(deepTable, 4, 1, "DownExh", text_size=size.tiny)
    table.cell(deepTable, 5, 1, f_cp1(dDownExh), text_size=size.tiny)

    table.cell(deepTable, 0, 2, "AccelRank", text_size=size.tiny)
    table.cell(deepTable, 1, 2, f_cp1(dAccelRank), text_size=size.tiny)
    table.cell(deepTable, 2, 2, "ResistHold", text_size=size.tiny)
    table.cell(deepTable, 3, 2, f_cp1(dResistHold), text_size=size.tiny)
    table.cell(deepTable, 4, 2, "SupportHold", text_size=size.tiny)
    table.cell(deepTable, 5, 2, f_cp1(dSupportHold), text_size=size.tiny)

    table.cell(deepTable, 0, 3, "DistRank", text_size=size.tiny)
    table.cell(deepTable, 1, 3, f_cp1(dDistRank), text_size=size.tiny)
    table.cell(deepTable, 2, 3, "DistRaw", text_size=size.tiny)
    table.cell(deepTable, 3, 3, f_cp1(dDistRaw), text_size=size.tiny)
    table.cell(deepTable, 4, 3, "MdExt", text_size=size.tiny)
    table.cell(deepTable, 5, 3, f_cp1(dMdExt), text_size=size.tiny)

    table.cell(deepTable, 0, 4, "HeatUp", text_size=size.tiny)
    table.cell(deepTable, 1, 4, f_cp1(dHeatUp), text_size=size.tiny)
    table.cell(deepTable, 2, 4, "DistGate%", text_size=size.tiny)
    table.cell(deepTable, 3, 4, f_cp1(dDistGatePct), text_size=size.tiny)
    table.cell(deepTable, 4, 4, "MdCont", text_size=size.tiny)
    table.cell(deepTable, 5, 4, f_cp1(dMdCont), text_size=size.tiny)

    table.cell(deepTable, 0, 5, "PanicHeat", text_size=size.tiny)
    table.cell(deepTable, 1, 5, f_cp1(dPanicHeat), text_size=size.tiny)
    table.cell(deepTable, 2, 5, "DistEff", text_size=size.tiny)
    table.cell(deepTable, 3, 5, f_cp1(dDistEff), text_size=size.tiny)
    table.cell(deepTable, 4, 5, "MdRaw", text_size=size.tiny)
    table.cell(deepTable, 5, 5, f_cp1(dMdRaw), text_size=size.tiny)

    table.cell(deepTable, 0, 6, "MatUp", text_size=size.tiny)
    table.cell(deepTable, 1, 6, f_cp1(dMatUp), text_size=size.tiny)
    table.cell(deepTable, 2, 6, "ProbDist", text_size=size.tiny)
    table.cell(deepTable, 3, 6, f_cp1(dProbDist), text_size=size.tiny)
    table.cell(deepTable, 4, 6, "MdGate%", text_size=size.tiny)
    table.cell(deepTable, 5, 6, f_cp1(dMdGatePct), text_size=size.tiny)

    table.cell(deepTable, 0, 7, "MatDn", text_size=size.tiny)
    table.cell(deepTable, 1, 7, f_cp1(dMatDn), text_size=size.tiny)
    table.cell(deepTable, 2, 7, "TopGap", text_size=size.tiny)
    table.cell(deepTable, 3, 7, f_cp1(dTopGap), text_size=size.tiny)
    table.cell(deepTable, 4, 7, "MdEff", text_size=size.tiny)
    table.cell(deepTable, 5, 7, f_cp1(dMdEff), text_size=size.tiny)

    table.cell(deepTable, 0, 8, "RangeScore", text_size=size.tiny)
    table.cell(deepTable, 1, 8, f_cp1(dRangeScore), text_size=size.tiny)
    table.cell(deepTable, 2, 8, "Evidence", text_size=size.tiny)
    table.cell(deepTable, 3, 8, f_cp1(dEvidence), text_size=size.tiny)
    table.cell(deepTable, 4, 8, "ProbMd", text_size=size.tiny)
    table.cell(deepTable, 5, 8, f_cp1(dProbMd), text_size=size.tiny)
'''.strip()


def generate(source_path: Path) -> str:
    return generate_base(source_path).rstrip() + "\n\n" + DEEP_TABLE + "\n"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    default_source = Path(__file__).resolve().parent / SOURCE_RELATIVE
    parser.add_argument("--source", type=Path, default=default_source)
    parser.add_argument("--output", type=Path, required=True)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    generated = generate(args.source)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(generated, encoding="utf-8")


if __name__ == "__main__":
    main()
