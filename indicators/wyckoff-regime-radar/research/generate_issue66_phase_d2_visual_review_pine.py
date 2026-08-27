#!/usr/bin/env python3
"""Generate Issue #66 Phase D-2 production-shell visual-review Pine.

D-2 uses the same accepted C-2 calculation transformation as D-1 but retains
the immutable v0.5.2.1 visual/dashboard/alert shell. Auxiliary witnesses remain
forced off so the displayed state is the runtime-validated price-only C-2 core.
"""
from __future__ import annotations

import argparse
from pathlib import Path

from generate_issue66_phase_d1_parity_pine import (
    FROZEN_SOURCE_BLOB_SHA,
    SOURCE_RELATIVE,
    VISUAL_MARKER,
    apply_issue66_c2,
    git_blob_sha,
    replace_once,
)

HERE = Path(__file__).resolve().parent

ORIGINAL_TITLE = (
    'indicator("Chase Risk Market Regime Radar v0.5.2.1｜Non-functional Cleanup", '
    'shorttitle="ChaseRisk Radar v0.5.2.1", overlay=false, precision=1)'
)
D2_TITLE = (
    'indicator("Chase Risk Market Regime Radar｜Issue #66 C-2 Visual Review", '
    'shorttitle="ChaseRisk #66 C2 Visual", overlay=false, precision=1)'
)


def generate(source_path: Path) -> str:
    raw = source_path.read_bytes()
    actual_blob = git_blob_sha(raw)
    if actual_blob != FROZEN_SOURCE_BLOB_SHA:
        raise RuntimeError(
            "frozen Pine source changed; refusing Issue #66 D-2 generation: "
            f"expected {FROZEN_SOURCE_BLOB_SHA}, got {actual_blob}"
        )

    text = raw.decode("utf-8")
    text = replace_once(text, ORIGINAL_TITLE, D2_TITLE)

    # Keep D-2 visually rich but classifier-pure: exactly the C-2 price-only mode
    # already validated in D-1/D-1B runtime parity.
    text = replace_once(
        text,
        'volumeMode = input.string("Auto", "Volume Mode", options=["Off", "Auto", "Force On", "Tick Volume Proxy"], group=groupVolume)',
        'volumeMode = "Off"  // Issue #66 D-2 forced price-only visual review',
    )
    text = replace_once(
        text,
        'mtfMode = input.string("Observe Only", "MTF Mode", options=["Off", "Observe Only", "Auto", "Force On"], group=groupMTF)',
        'mtfMode = "Off"  // Issue #66 D-2 forced price-only visual review',
    )
    text = replace_once(
        text,
        'divMode = input.string("Observe Only", "Divergence Mode", options=["Off", "Observe Only", "Auto"], group=groupDivergence)',
        'divMode = "Off"  // Issue #66 D-2 forced price-only visual review',
    )
    text = replace_once(
        text,
        'witnessStageBiasMode = input.string("Balanced", "Witness Stage Bias Mode", options=["Conservative", "Balanced", "Aggressive"], group=groupWitness)',
        'witnessStageBiasMode = "Conservative"  // Issue #66 D-2 forced price-only visual review',
    )

    text = apply_issue66_c2(text)

    if text.count(VISUAL_MARKER) != 1:
        raise RuntimeError("D-2 expected exactly one // Visuals marker")
    if "PARITY formal_id" in text or "Issue #66 Phase D-1 parity export" in text:
        raise RuntimeError("D-2 unexpectedly contains D-1 parity export")
    if "D1B|" in text or "Phase D-1B Pine Logs transport" in text:
        raise RuntimeError("D-2 unexpectedly contains D-1B log transport")

    return text.rstrip() + "\n"


def main() -> None:
    ap = argparse.ArgumentParser(description="Generate Issue #66 C-2 visual-review Pine")
    ap.add_argument("--source", type=Path, default=HERE / SOURCE_RELATIVE)
    ap.add_argument("--output", type=Path, required=True)
    args = ap.parse_args()
    rendered = generate(args.source)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(rendered, encoding="utf-8")


if __name__ == "__main__":
    main()
