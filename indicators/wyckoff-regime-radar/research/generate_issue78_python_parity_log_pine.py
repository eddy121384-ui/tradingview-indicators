#!/usr/bin/env python3
"""Generate Issue #78 Pine-Logs parity harness.

This is exactly the Issue #78 parity export harness plus a log-only transport
block. Classifier calculations are unchanged. It exists because some TradingView
accounts cannot export chart data but can download/copy Pine Logs.
"""
from __future__ import annotations

import argparse
from pathlib import Path

from generate_issue78_python_parity_export_pine import generate as generate_parent
import generate_issue76_forward_behavior_logger_pine as base

HERE = Path(__file__).resolve().parent

FIELDS = [
    ("useYieldLevel", "useYieldLevel ? 1.0 : 0.0"),
    ("formalId", "float(formalId)"),
    ("symATR", "symATR"),
    ("volumeQuality", "volumeQualityScore"),
    ("volumeWeight", "volumeWeightApplied"),
    ("volumeAbsorption", "volumeAbsorptionScore"),
    ("volumeDistribution", "volumeDistributionScore"),
    ("volumeBreakout", "volumeBreakoutConfirmation"),
    ("volumeBreakdown", "volumeBreakdownConfirmation"),
    ("accGate", "accGate * 100.0"),
    ("markupGate", "markupGate * 100.0"),
    ("reaccGate", "reaccGate * 100.0"),
    ("distGate", "distGate * 100.0"),
    ("markdownGate", "markdownGate * 100.0"),
    ("redistGate", "redistGate * 100.0"),
    ("probAcc", "probAcc"),
    ("probMarkup", "probMarkup"),
    ("probReacc", "probReacc"),
    ("probDist", "probDist"),
    ("probMarkdown", "probMarkdown"),
    ("probRedist", "probRedist"),
    ("topId", "float(topId)"),
    ("topGap", "topGap"),
    ("evidence", "evidenceStrength"),
    ("candidateDisplayId", "float(candidateDisplayId)"),
    ("stalePressureBars", "float(stalePressureBars)"),
    ("stalePressureReason", "float(stalePressureReason)"),
]

MARKER = "I78P1"


def _log_block() -> str:
    schema = "ticker|tf|time|open|high|low|close|volume|" + "|".join(name for name, _ in FIELDS)
    pieces = [
        '"I78P1"',
        "syminfo.tickerid",
        "timeframe.period",
        "str.tostring(time)",
        "f_i78pNum(open)",
        "f_i78pNum(high)",
        "f_i78pNum(low)",
        "f_i78pNum(close)",
        "f_i78pNum(volume)",
    ]
    pieces.extend(f"f_i78pNum({expr})" for _, expr in FIELDS)
    expression = ' + "|" + '.join(pieces)
    return f"""
// ============================================================================
// Issue #78 — Python classifier parity Pine Logs transport.
// Schema after I78P1| : {schema}
// Engineering parity only. No policy economics.
// ============================================================================
groupIssue78ParityLog = "研究｜Issue #78 Python Parity Logs"
issue78ParityLogEnabled = input.bool(true, "Enable parity Pine Logs", group=groupIssue78ParityLog)
issue78ParityCaptureBars = input.int(2500, "Parity log capture bars", minval=1200, maxval=3000, group=groupIssue78ParityLog)

f_i78pNum(_x) => na(_x) ? "na" : str.tostring(_x, "#.###############")
issue78ParityInWindow = bar_index >= math.max(last_bar_index - issue78ParityCaptureBars + 1, 0)

if issue78ParityLogEnabled and barstate.isconfirmed and issue78ParityInWindow
    log.info({expression})
""".strip() + "\n"


def generate(source_path: Path) -> str:
    parent = generate_parent(source_path)
    marker = "// Issue #78 — Python classifier parity Pine Logs transport."
    if marker in parent:
        raise RuntimeError("parent parity export unexpectedly already contains log transport")
    text = parent.rstrip() + "\n\n" + _log_block()
    required = (
        '"I78P1" + "|" + syminfo.tickerid',
        'input.int(2500, "Parity log capture bars"',
        "log.info(",
        "f_i78pNum(volume)",
        "f_i78pNum(float(formalId))",
        "f_i78pNum(symATR)",
        "f_i78pNum(volumeQualityScore)",
        "f_i78pNum(float(candidateDisplayId))",
    )
    for token in required:
        if token not in text:
            raise RuntimeError(f"generated parity log harness missing: {token}")
    return text


def main() -> None:
    ap = argparse.ArgumentParser()
    default_source = Path(__file__).resolve().parents[1] / "src" / base.SOURCE_NAME
    default_output = HERE / "generated" / "wyckoff-issue78-python-parity-log.pine"
    ap.add_argument("--source", type=Path, default=default_source)
    ap.add_argument("--output", type=Path, default=default_output)
    args = ap.parse_args()
    rendered = generate(args.source)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(rendered, encoding="utf-8")
    print(args.output)
    print("Issue #78 Python parity Pine Logs harness PASS")


if __name__ == "__main__":
    main()
