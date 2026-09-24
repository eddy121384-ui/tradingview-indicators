#!/usr/bin/env python3
"""Generate the Issue #78 Pine reference export used for Python parity tests.

This is an engineering-only helper. It starts from the exact frozen Issue #68
RC source, keeps classifier semantics unchanged, applies the already-reviewed
MTF Observe-Only memory safeguard, and exposes the reference series needed to
verify a scalable Python port.

It is NOT an OOS strategy logger and contains no policy economics.
"""
from __future__ import annotations

import argparse
from pathlib import Path

import generate_issue76_forward_behavior_logger_pine as base
import generate_issue78_heterogeneous_oos1_logger_pine as oos1

DECL_NEW = (
    'indicator("Wyckoff Regime Radar｜Issue #78 Python Parity Export", '
    'shorttitle="#78 PY PARITY", overlay=false, precision=10, calc_bars_count=10000)'
)

PARITY_BLOCK = r'''
// ============================================================================
// Issue #78 — Python classifier parity export.
// Engineering reference only. No policy / PnL / OOS outcome logic.
// Export the chart data so the same OHLCV bars can be replayed in Python.
// ============================================================================
groupIssue78Parity = "研究｜Issue #78 Python Parity Export"
issue78ParityEnabled = input.bool(true, "Enable parity channels", group=groupIssue78Parity)

plot(issue78ParityEnabled ? formalId : na, "PARITY formalId")
plot(issue78ParityEnabled ? confirmedId : na, "PARITY confirmedId")
plot(issue78ParityEnabled ? symATR : na, "PARITY symATR")
plot(issue78ParityEnabled ? (useYieldLevel ? 1.0 : 0.0) : na, "PARITY useYieldLevel")
plot(issue78ParityEnabled ? volume : na, "PARITY volume")
'''


def replace_once(text: str, old: str, new: str, label: str) -> str:
    if text.count(old) != 1:
        raise RuntimeError(f"{label} missing or duplicated")
    return text.replace(old, new, 1)


def generate(source_path: Path) -> str:
    source_bytes = source_path.read_bytes()
    actual_blob = base.git_blob_sha(source_bytes)
    if actual_blob != base.FROZEN_SOURCE_BLOB:
        raise RuntimeError(
            f"frozen source blob mismatch: expected {base.FROZEN_SOURCE_BLOB}, got {actual_blob}"
        )

    source = source_bytes.decode("utf-8")
    candidate = replace_once(source, base.DECL_OLD, DECL_NEW, "indicator declaration")

    frozen_mtf_default = 'mtfMode = input.string("Observe Only"'
    if frozen_mtf_default not in candidate:
        raise RuntimeError("frozen MTF default drifted from Observe Only")

    for old, new in oos1.LIGHTWEIGHT_MTF_REPLACEMENTS:
        candidate = replace_once(candidate, old, new, "MTF observe-only request")

    candidate = replace_once(
        candidate,
        base.ANCHOR,
        PARITY_BLOCK + "\n" + base.ANCHOR,
        "Visuals anchor",
    )

    required = (
        "formalId = confirmedId",
        "symATR  = ta.rma(modelTR, atrLen)",
        'mtfMode = input.string("Observe Only"',
        'plot(issue78ParityEnabled ? formalId : na, "PARITY formalId")',
        'plot(issue78ParityEnabled ? symATR : na, "PARITY symATR")',
        "calc_bars_count=10000",
    )
    for token in required:
        if token not in candidate:
            raise RuntimeError(f"generated parity export missing required token: {token}")

    if "request.security_lower_tf" in candidate:
        raise RuntimeError("lower-timeframe request leaked into memory-safe parity export")

    return candidate


def main() -> None:
    ap = argparse.ArgumentParser()
    default_source = Path(__file__).resolve().parents[1] / "src" / base.SOURCE_NAME
    default_output = (
        Path(__file__).resolve().parent
        / "generated"
        / "wyckoff-issue78-python-parity-export.pine"
    )
    ap.add_argument("--source", type=Path, default=default_source)
    ap.add_argument("--output", type=Path, default=default_output)
    args = ap.parse_args()

    candidate = generate(args.source)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(candidate, encoding="utf-8")
    print(args.output)
    print("Issue #78 Python parity export generator PASS")


if __name__ == "__main__":
    main()
