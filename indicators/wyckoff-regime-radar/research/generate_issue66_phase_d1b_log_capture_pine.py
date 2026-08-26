#!/usr/bin/env python3
"""Generate Issue #66 Phase D-1B Pine-Logs runtime capture harness.

D-1B is exactly the accepted D-1 generated C-2 parity Pine plus a log-only
transport block. It does not modify classifier calculations.
"""
from __future__ import annotations

import argparse
from pathlib import Path

from generate_issue66_phase_d1_parity_pine import SOURCE_RELATIVE, generate as generate_d1

HERE = Path(__file__).resolve().parent

FIELDS = [
    ("speed_rank", "speedRank"),
    ("accel_rank", "accelRank"),
    ("dist_rank", "distRank"),
    ("heat_up", "heatUp"),
    ("panic_heat_dn", "panicHeatDn"),
    ("maturity_up", "maturityUp"),
    ("maturity_dn", "maturityDn"),
    ("range_score", "rangeScore"),
    ("downside_exhaustion", "downsideExhaustion"),
    ("upside_exhaustion", "upsideExhaustion"),
    ("support_holding", "supportHolding"),
    ("resistance_holding", "resistanceHolding"),
    ("markup_extension_score", "markupExtensionScore"),
    ("markdown_extension_score", "markdownExtensionScore"),
    ("markup_continuation_score", "markupContinuationScore"),
    ("markdown_continuation_score", "markdownContinuationScore"),
    ("acc_gate", "accGate * 100.0"),
    ("markup_gate", "markupGate * 100.0"),
    ("reacc_gate", "reaccGate * 100.0"),
    ("dist_gate", "distGate * 100.0"),
    ("markdown_gate", "markdownGate * 100.0"),
    ("redist_gate", "redistGate * 100.0"),
    ("prob_acc", "probAcc"),
    ("prob_markup", "probMarkup"),
    ("prob_reacc", "probReacc"),
    ("prob_dist", "probDist"),
    ("prob_markdown", "probMarkdown"),
    ("prob_redist", "probRedist"),
    ("top_id", "float(topId)"),
    ("top_value", "topVal"),
    ("top_gap", "topGap"),
    ("evidence_strength", "evidenceStrength"),
    ("candidate_display_id", "float(candidateDisplayId)"),
    ("formal_id", "float(formalId)"),
    ("stale_pressure_bars", "float(stalePressureBars)"),
    ("stale_pressure_reason", "float(stalePressureReason)"),
]


def _log_block() -> str:
    schema = "time|open|high|low|close|" + "|".join(name for name, _ in FIELDS)
    pieces = [
        '"D1B|"',
        'str.tostring(time)',
        'f_d1bNum(open)',
        'f_d1bNum(high)',
        'f_d1bNum(low)',
        'f_d1bNum(close)',
    ]
    pieces.extend(f"f_d1bNum({expr})" for _, expr in FIELDS)
    expression = ' + "|" + '.join(pieces)
    return f'''

// === Issue #66 Phase D-1B Pine Logs transport ===
// Schema after D1B| : {schema}
d1bCaptureBars = input.int(1200, "D1B Pine Logs capture bars", minval=800, maxval=3000)
f_d1bNum(_x) => na(_x) ? "na" : str.tostring(_x, "#.###############")
d1bInCaptureWindow = bar_index >= math.max(last_bar_index - d1bCaptureBars + 1, 0)
if barstate.isconfirmed and d1bInCaptureWindow
    log.info({expression})
'''.rstrip() + "\n"


def generate(source_path: Path) -> str:
    parent = generate_d1(source_path)
    marker = "// === Issue #66 Phase D-1B Pine Logs transport ==="
    if marker in parent:
        raise RuntimeError("D-1 parent unexpectedly already contains D-1B log transport")
    return parent.rstrip() + "\n" + _log_block()


def main() -> None:
    ap = argparse.ArgumentParser(description="Generate Issue #66 D-1B Pine Logs capture harness")
    ap.add_argument("--source", type=Path, default=HERE / SOURCE_RELATIVE)
    ap.add_argument("--output", type=Path, required=True)
    args = ap.parse_args()
    rendered = generate(args.source)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(rendered, encoding="utf-8")


if __name__ == "__main__":
    main()
