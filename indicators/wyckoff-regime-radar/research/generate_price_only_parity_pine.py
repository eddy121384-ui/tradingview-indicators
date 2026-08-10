#!/usr/bin/env python3
"""Generate a minimal TradingView parity harness from frozen Wyckoff v0.5.2.1 Pine.

The harness is mechanically derived from the real indicator rather than being a
second hand-written implementation. It forces all auxiliary witnesses off,
keeps the frozen calculation core through formal-state resolution, removes the
original visual/table/alert layer, and exposes only the fields required for the
Issue #55 Pine/Python parity gate.

Because some TradingView plans do not support chart-data export, the generated
harness also renders a compact checkpoint table. A single screenshot is enough
to capture the parity values needed for manual comparison. Checkpoints are
captured on the first daily bar whose close time reaches each target date so FX
session cutovers do not create false missing rows.
"""

from __future__ import annotations

import argparse
import hashlib
from pathlib import Path


FROZEN_SOURCE_BLOB_SHA = "ab6861181a27697ad566c19bf405a0571be2eb1a"
SOURCE_RELATIVE = Path("../src/chase-risk-market-regime-radar-v0.5.2.1.pine")
VISUAL_MARKER = "// Visuals"

PARITY_PLOTS = r'''
// === Issue #55 Price-only parity export ===
// Minimal Data Window/export diagnostics only; no original visuals are kept.
plot(probAcc, "PARITY prob_acc", display=display.data_window)
plot(probMarkup, "PARITY prob_markup", display=display.data_window)
plot(probReacc, "PARITY prob_reacc", display=display.data_window)
plot(probDist, "PARITY prob_dist", display=display.data_window)
plot(probMarkdown, "PARITY prob_markdown", display=display.data_window)
plot(probRedist, "PARITY prob_redist", display=display.data_window)
plot(topGap, "PARITY top_gap", display=display.data_window)
plot(evidenceStrength, "PARITY evidence_strength", display=display.data_window)
plot(float(candidateDisplayId), "PARITY candidate_display_id", display=display.data_window)
plot(float(formalId), "PARITY formal_id", display=display.data_window)
'''.strip()

CHECKPOINT_TABLE = r'''
// === Issue #55 screenshot parity checkpoints ===
// Visual replacement for CSV export. Capture the first daily bar whose close
// time reaches the target date; this is robust to FX session cutover labels.
var int[] cpYear = array.from(2019, 2020, 2021, 2022, 2024, 2026)
var int[] cpMonth = array.from(8, 3, 6, 9, 4, 7)
var int[] cpDay = array.from(1, 20, 1, 28, 16, 30)
var string[] cpTargetDate = array.from("2019-08-01", "2020-03-20", "2021-06-01", "2022-09-28", "2024-04-16", "2026-07-30")
var bool[] cpCaptured = array.new_bool(6, false)
var string[] cpBarDate = array.new_string(6, "—")

var float[] cpClose = array.new_float(6, na)
var float[] cpAcc = array.new_float(6, na)
var float[] cpMarkup = array.new_float(6, na)
var float[] cpReacc = array.new_float(6, na)
var float[] cpDist = array.new_float(6, na)
var float[] cpMarkdown = array.new_float(6, na)
var float[] cpRedist = array.new_float(6, na)
var float[] cpGap = array.new_float(6, na)
var float[] cpEvidence = array.new_float(6, na)
var float[] cpCandidate = array.new_float(6, na)
var float[] cpFormal = array.new_float(6, na)

for i = 0 to 5
    targetTs = timestamp(syminfo.timezone, array.get(cpYear, i), array.get(cpMonth, i), array.get(cpDay, i), 0, 0)
    shouldCapture = not array.get(cpCaptured, i) and time_close >= targetTs
    if shouldCapture
        array.set(cpCaptured, i, true)
        array.set(cpBarDate, i, str.format_time(time_close, "yyyy-MM-dd", syminfo.timezone))
        array.set(cpClose, i, close)
        array.set(cpAcc, i, probAcc)
        array.set(cpMarkup, i, probMarkup)
        array.set(cpReacc, i, probReacc)
        array.set(cpDist, i, probDist)
        array.set(cpMarkdown, i, probMarkdown)
        array.set(cpRedist, i, probRedist)
        array.set(cpGap, i, topGap)
        array.set(cpEvidence, i, evidenceStrength)
        array.set(cpCandidate, i, float(candidateDisplayId))
        array.set(cpFormal, i, float(formalId))

f_cp1(x) => na(x) ? "—" : str.tostring(x, "#.0")
f_cp5(x) => na(x) ? "—" : str.tostring(x, "#.#####")
f_cpid(x) => na(x) ? "—" : str.tostring(math.round(x))

var table cpTable = table.new(position.top_right, 13, 7, border_width=1)
if barstate.islast
    table.cell(cpTable, 0, 0, "Target", text_size=size.tiny)
    table.cell(cpTable, 1, 0, "Bar", text_size=size.tiny)
    table.cell(cpTable, 2, 0, "Close", text_size=size.tiny)
    table.cell(cpTable, 3, 0, "Acc", text_size=size.tiny)
    table.cell(cpTable, 4, 0, "Mk", text_size=size.tiny)
    table.cell(cpTable, 5, 0, "ReAcc", text_size=size.tiny)
    table.cell(cpTable, 6, 0, "Dist", text_size=size.tiny)
    table.cell(cpTable, 7, 0, "Md", text_size=size.tiny)
    table.cell(cpTable, 8, 0, "ReDist", text_size=size.tiny)
    table.cell(cpTable, 9, 0, "Gap", text_size=size.tiny)
    table.cell(cpTable, 10, 0, "Evid", text_size=size.tiny)
    table.cell(cpTable, 11, 0, "Cand", text_size=size.tiny)
    table.cell(cpTable, 12, 0, "Formal", text_size=size.tiny)
    for i = 0 to 5
        row = i + 1
        table.cell(cpTable, 0, row, array.get(cpTargetDate, i), text_size=size.tiny)
        table.cell(cpTable, 1, row, array.get(cpBarDate, i), text_size=size.tiny)
        table.cell(cpTable, 2, row, f_cp5(array.get(cpClose, i)), text_size=size.tiny)
        table.cell(cpTable, 3, row, f_cp1(array.get(cpAcc, i)), text_size=size.tiny)
        table.cell(cpTable, 4, row, f_cp1(array.get(cpMarkup, i)), text_size=size.tiny)
        table.cell(cpTable, 5, row, f_cp1(array.get(cpReacc, i)), text_size=size.tiny)
        table.cell(cpTable, 6, row, f_cp1(array.get(cpDist, i)), text_size=size.tiny)
        table.cell(cpTable, 7, row, f_cp1(array.get(cpMarkdown, i)), text_size=size.tiny)
        table.cell(cpTable, 8, row, f_cp1(array.get(cpRedist, i)), text_size=size.tiny)
        table.cell(cpTable, 9, row, f_cp1(array.get(cpGap, i)), text_size=size.tiny)
        table.cell(cpTable, 10, row, f_cp1(array.get(cpEvidence, i)), text_size=size.tiny)
        table.cell(cpTable, 11, row, f_cpid(array.get(cpCandidate, i)), text_size=size.tiny)
        table.cell(cpTable, 12, row, f_cpid(array.get(cpFormal, i)), text_size=size.tiny)
'''.strip()


def git_blob_sha(content: bytes) -> str:
    header = f"blob {len(content)}\0".encode("ascii")
    return hashlib.sha1(header + content).hexdigest()


def replace_once(text: str, old: str, new: str) -> str:
    count = text.count(old)
    if count != 1:
        raise RuntimeError(f"expected exactly one source match, found {count}: {old[:80]}")
    return text.replace(old, new, 1)


def generate(source_path: Path) -> str:
    raw = source_path.read_bytes()
    actual_blob = git_blob_sha(raw)
    if actual_blob != FROZEN_SOURCE_BLOB_SHA:
        raise RuntimeError(
            "frozen Pine source changed; refusing to silently regenerate parity harness: "
            f"expected {FROZEN_SOURCE_BLOB_SHA}, got {actual_blob}"
        )

    text = raw.decode("utf-8")
    text = replace_once(
        text,
        'indicator("Chase Risk Market Regime Radar v0.5.2.1｜Non-functional Cleanup", shorttitle="ChaseRisk Radar v0.5.2.1", overlay=false, precision=1)',
        'indicator("Chase Risk Radar v0.5.2.1｜Issue #55 Price-only Parity", shorttitle="ChaseRisk #55 Parity", overlay=false, precision=1)',
    )
    text = replace_once(
        text,
        'volumeMode = input.string("Auto", "Volume Mode", options=["Off", "Auto", "Force On", "Tick Volume Proxy"], group=groupVolume)',
        'volumeMode = "Off"  // Issue #55 forced price-only',
    )
    text = replace_once(
        text,
        'mtfMode = input.string("Observe Only", "MTF Mode", options=["Off", "Observe Only", "Auto", "Force On"], group=groupMTF)',
        'mtfMode = "Off"  // Issue #55 forced price-only',
    )
    text = replace_once(
        text,
        'divMode = input.string("Observe Only", "Divergence Mode", options=["Off", "Observe Only", "Auto"], group=groupDivergence)',
        'divMode = "Off"  // Issue #55 forced price-only',
    )
    text = replace_once(
        text,
        'witnessStageBiasMode = input.string("Balanced", "Witness Stage Bias Mode", options=["Conservative", "Balanced", "Aggressive"], group=groupWitness)',
        'witnessStageBiasMode = "Conservative"  // Issue #55 forced price-only',
    )

    if text.count(VISUAL_MARKER) != 1:
        raise RuntimeError("expected exactly one // Visuals marker")

    calculation_core, _ = text.split(VISUAL_MARKER, 1)
    return calculation_core.rstrip() + "\n\n" + PARITY_PLOTS + "\n\n" + CHECKPOINT_TABLE + "\n"


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
