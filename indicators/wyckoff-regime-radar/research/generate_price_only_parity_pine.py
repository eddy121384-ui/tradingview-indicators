#!/usr/bin/env python3
"""Generate a TradingView parity harness from frozen Wyckoff v0.5.2.1 Pine.

The harness is mechanically derived from the real indicator instead of being a
second hand-written Pine implementation. It forces all auxiliary witnesses off
and adds Data Window plots for price-only research fields.
"""

from __future__ import annotations

import argparse
import hashlib
from pathlib import Path


FROZEN_SOURCE_BLOB_SHA = "ab6861181a27697ad566c19bf405a0571be2eb1a"
SOURCE_RELATIVE = Path("../src/chase-risk-market-regime-radar-v0.5.2.1.pine")

PARITY_PLOTS = r'''
// === Issue #55 Price-only parity export ===
// Generated mechanically from the frozen v0.5.2.1 source. These plots are
// Data Window/export diagnostics only; they do not alter state calculations.
plot(speedRank, "PARITY speed_rank", display=display.data_window)
plot(accelRank, "PARITY accel_rank", display=display.data_window)
plot(distRank, "PARITY dist_rank", display=display.data_window)
plot(heatUp, "PARITY heat_up", display=display.data_window)
plot(panicHeatDn, "PARITY panic_heat_dn", display=display.data_window)
plot(maturityUp, "PARITY maturity_up", display=display.data_window)
plot(maturityDn, "PARITY maturity_dn", display=display.data_window)
plot(rangeScore, "PARITY range_score", display=display.data_window)
plot(downsideExhaustion, "PARITY downside_exhaustion", display=display.data_window)
plot(upsideExhaustion, "PARITY upside_exhaustion", display=display.data_window)
plot(supportHolding, "PARITY support_holding", display=display.data_window)
plot(resistanceHolding, "PARITY resistance_holding", display=display.data_window)
plot(markupExtensionScore, "PARITY markup_extension", display=display.data_window)
plot(markdownExtensionScore, "PARITY markdown_extension", display=display.data_window)
plot(markupContinuationScore, "PARITY markup_continuation", display=display.data_window)
plot(markdownContinuationScore, "PARITY markdown_continuation", display=display.data_window)
plot(accGate * 100.0, "PARITY acc_gate_pct", display=display.data_window)
plot(markupGate * 100.0, "PARITY markup_gate_pct", display=display.data_window)
plot(reaccGate * 100.0, "PARITY reacc_gate_pct", display=display.data_window)
plot(distGate * 100.0, "PARITY dist_gate_pct", display=display.data_window)
plot(markdownGate * 100.0, "PARITY markdown_gate_pct", display=display.data_window)
plot(redistGate * 100.0, "PARITY redist_gate_pct", display=display.data_window)
plot(probAcc, "PARITY prob_acc", display=display.data_window)
plot(probMarkup, "PARITY prob_markup", display=display.data_window)
plot(probReacc, "PARITY prob_reacc", display=display.data_window)
plot(probDist, "PARITY prob_dist", display=display.data_window)
plot(probMarkdown, "PARITY prob_markdown", display=display.data_window)
plot(probRedist, "PARITY prob_redist", display=display.data_window)
plot(topVal, "PARITY top_value", display=display.data_window)
plot(topGap, "PARITY top_gap", display=display.data_window)
plot(evidenceStrength, "PARITY evidence_strength", display=display.data_window)
plot(float(topId), "PARITY top_id", display=display.data_window)
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
    marker = "// Visuals"
    if text.count(marker) != 1:
        raise RuntimeError("expected exactly one // Visuals marker")
    text = text.replace(marker, PARITY_PLOTS + "\n\n" + marker, 1)
    return text


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
