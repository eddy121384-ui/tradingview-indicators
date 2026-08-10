#!/usr/bin/env python3
"""Generate a minimal TradingView parity harness from frozen Wyckoff v0.5.2.1 Pine.

The harness is mechanically derived from the real indicator rather than being a
second hand-written implementation. It forces all auxiliary witnesses off,
keeps the frozen calculation core through formal-state resolution, removes the
original visual/table/alert layer, and exposes only the fields required for the
Issue #55 Pine/Python parity gate.
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
    return calculation_core.rstrip() + "\n\n" + PARITY_PLOTS + "\n"


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
