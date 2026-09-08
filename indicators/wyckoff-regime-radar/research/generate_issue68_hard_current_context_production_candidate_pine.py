#!/usr/bin/env python3
"""Generate the full C-2 Issue #68 HARD current-context production candidate.

This generator starts from the immutable v0.5.2.1 production Pine, applies the
accepted Issue #57 / Issue #66 C-2 lineage while preserving production witness
modes, visuals, tables, and alerts, then applies ONLY the exact symmetric
Issue #68 HARD current-context routing repair to S1/S4.

It also performs a deterministic line-diff contract check against the full C-2
baseline. No research-only price-only forcing, parity plots, Fresh labels,
stateful grace, tuning, or strategy logic is permitted.
"""
from __future__ import annotations

import argparse
from collections import Counter
import difflib
from pathlib import Path
import re

import generate_issue66_phase_d1_parity_pine as issue66
from generate_price_only_parity_pine import (
    FROZEN_SOURCE_BLOB_SHA,
    SOURCE_RELATIVE,
    VISUAL_MARKER,
    git_blob_sha,
    replace_once,
)


HARD_COMMENT = "// Issue #68 HARD current-context cap — exact symmetric production candidate."
CURRENT_BEAR = "currentBearGate = f_gate(bearBg, 35.0, 75.0)"
CURRENT_BULL = "currentBullGate = f_gate(bullBg, 35.0, 75.0)"
CTX_DOWN = "ctxDownExGate = math.min(downsideExhaustionGate, currentBearGate)"
CTX_UP = "ctxUpExGate = math.min(upsideExhaustionGate, currentBullGate)"

OLD_ACC_GATE = "accGate      = rangeGate * bearBackgroundForAccGate * downsideExhaustionGate * supportHoldingGate * nonMarkdownContinuationGate"
NEW_ACC_GATE = "accGate      = rangeGate * bearBackgroundForAccGate * ctxDownExGate * supportHoldingGate * nonMarkdownContinuationGate"
OLD_DIST_GATE = "distGate     = rangeGate * bullBackgroundForDistGate * upsideExhaustionGate * resistanceHoldingGate * nonMarkupContinuationGate"
NEW_DIST_GATE = "distGate     = rangeGate * bullBackgroundForDistGate * ctxUpExGate * resistanceHoldingGate * nonMarkupContinuationGate"

BACKGROUND_ANCHOR = (
    "matureBullGate = f_gate(bullMaturityTrace, 60.0, 85.0)  // retained diagnostic compatibility\n"
    "bearBackgroundForAccGate = f_gate(math.max(bearBg, bearMaturityTrace), 35.0, 75.0)\n"
    "bullBackgroundForDistGate = f_gate(math.max(bullBg, bullMaturityTrace), 35.0, 75.0)"
)
BACKGROUND_WITH_HARD = BACKGROUND_ANCHOR + "\n" + "\n".join(
    [HARD_COMMENT, CURRENT_BEAR, CURRENT_BULL, CTX_DOWN, CTX_UP]
)

EXPECTED_REMOVED = Counter([OLD_ACC_GATE, OLD_DIST_GATE])
EXPECTED_ADDED = Counter(
    [HARD_COMMENT, CURRENT_BEAR, CURRENT_BULL, CTX_DOWN, CTX_UP, NEW_ACC_GATE, NEW_DIST_GATE]
)

PLOT_CALL_RE = re.compile(
    r"(?m)^\s*(?:plot|plotshape|plotchar|plotcandle|plotbar|bgcolor|barcolor|fill|alertcondition)\s*\("
)


def read_frozen_source(source_path: Path) -> str:
    raw = source_path.read_bytes()
    actual_blob = git_blob_sha(raw)
    if actual_blob != FROZEN_SOURCE_BLOB_SHA:
        raise RuntimeError(
            "frozen Pine source changed; refusing Issue #68 production-candidate generation: "
            f"expected {FROZEN_SOURCE_BLOB_SHA}, got {actual_blob}"
        )
    return raw.decode("utf-8")


def generate_c2_baseline(source_path: Path) -> str:
    """Build full accepted C-2 while preserving production witness/visual layers."""
    text = read_frozen_source(source_path)
    text = issue66.apply_issue66_c2(text)

    required_production_tokens = (
        'volumeMode = input.string("Auto", "Volume Mode"',
        'mtfMode = input.string("Observe Only", "MTF Mode"',
        'divMode = input.string("Observe Only", "Divergence Mode"',
        'witnessStageBiasMode = input.string("Balanced", "Witness Stage Bias Mode"',
        VISUAL_MARKER,
        "alertcondition(formalChanged",
        "request.security_lower_tf",
        OLD_ACC_GATE,
        OLD_DIST_GATE,
    )
    for token in required_production_tokens:
        if token not in text:
            raise RuntimeError(f"full C-2 production baseline missing token: {token}")

    forbidden_harness_tokens = (
        "Issue #66 forced price-only",
        "PARITY prob_acc",
        "Issue #68 Fresh-S1",
        "STATEFUL CTX",
    )
    for token in forbidden_harness_tokens:
        if token in text:
            raise RuntimeError(f"research/parity harness leakage into full C-2 baseline: {token}")

    return text


def apply_hard_current_context(c2_text: str) -> str:
    """Apply only the exact symmetric S1/S4 direct-routing repair."""
    text = replace_once(c2_text, BACKGROUND_ANCHOR, BACKGROUND_WITH_HARD)
    text = replace_once(text, OLD_ACC_GATE, NEW_ACC_GATE)
    text = replace_once(text, OLD_DIST_GATE, NEW_DIST_GATE)
    return text


def diff_payloads(baseline: str, candidate: str) -> tuple[Counter[str], Counter[str]]:
    removed: Counter[str] = Counter()
    added: Counter[str] = Counter()
    for line in difflib.ndiff(baseline.splitlines(), candidate.splitlines()):
        if line.startswith("- "):
            removed[line[2:]] += 1
        elif line.startswith("+ "):
            added[line[2:]] += 1
    return removed, added


def validate_candidate(baseline: str, candidate: str) -> None:
    removed, added = diff_payloads(baseline, candidate)
    if removed != EXPECTED_REMOVED:
        raise RuntimeError(f"unexpected C-2 removals: {removed!r}")
    if added != EXPECTED_ADDED:
        raise RuntimeError(f"unexpected C-2 additions: {added!r}")

    for token in (CURRENT_BEAR, CURRENT_BULL, CTX_DOWN, CTX_UP, NEW_ACC_GATE, NEW_DIST_GATE):
        if candidate.count(token) != 1:
            raise RuntimeError(f"expected exactly one HARD token: {token}")

    # Exact mirror / monotonic cap algebra.
    if "math.min(downsideExhaustionGate, currentBearGate)" not in candidate:
        raise RuntimeError("missing S1 HARD min cap")
    if "math.min(upsideExhaustionGate, currentBullGate)" not in candidate:
        raise RuntimeError("missing S4 HARD min cap")

    # No new state, lookback, tuning input, request, PnL, or strategy call may be
    # introduced by the Issue #68 added lines.
    added_text = "\n".join(added.elements())
    for forbidden in ("var ", "input.", "request.", "strategy.", "close[", "high[", "low[", "time["):
        if forbidden in added_text:
            raise RuntimeError(f"forbidden construct introduced by HARD patch: {forbidden}")

    # Production witness modes and visual/alert layer must remain byte-identical
    # outside the explicitly whitelisted HARD diff.
    production_tokens = (
        'volumeMode = input.string("Auto", "Volume Mode"',
        'mtfMode = input.string("Observe Only", "MTF Mode"',
        'divMode = input.string("Observe Only", "Divergence Mode"',
        'witnessStageBiasMode = input.string("Balanced", "Witness Stage Bias Mode"',
        VISUAL_MARKER,
        "alertcondition(formalChanged",
        "request.security_lower_tf",
    )
    for token in production_tokens:
        if token not in candidate:
            raise RuntimeError(f"production layer lost token: {token}")

    # Plot-generating call footprint must be unchanged from full C-2.
    baseline_plot_calls = len(PLOT_CALL_RE.findall(baseline))
    candidate_plot_calls = len(PLOT_CALL_RE.findall(candidate))
    if candidate_plot_calls != baseline_plot_calls:
        raise RuntimeError(
            f"plot-generating call footprint changed: C-2={baseline_plot_calls}, candidate={candidate_plot_calls}"
        )

    if "strategy.entry" in candidate or "strategy.close" in candidate or "strategy(" in candidate:
        raise RuntimeError("strategy/PnL logic leaked into production candidate")

    if "Issue #66 forced price-only" in candidate or "PARITY prob_acc" in candidate:
        raise RuntimeError("price-only/parity harness leaked into production candidate")


def unified_diff_text(baseline: str, candidate: str) -> str:
    return "\n".join(
        difflib.unified_diff(
            baseline.splitlines(),
            candidate.splitlines(),
            fromfile="full-c2-baseline.pine",
            tofile="issue68-hard-production-candidate.pine",
            lineterm="",
        )
    ) + "\n"


def generate(source_path: Path) -> tuple[str, str]:
    baseline = generate_c2_baseline(source_path)
    candidate = apply_hard_current_context(baseline)
    validate_candidate(baseline, candidate)
    return candidate, unified_diff_text(baseline, candidate)


def main() -> None:
    ap = argparse.ArgumentParser(description="Generate Issue #68 full C-2 HARD production candidate")
    ap.add_argument("--source", type=Path, default=Path(__file__).resolve().parent / SOURCE_RELATIVE)
    ap.add_argument("--output", type=Path, required=True)
    ap.add_argument("--diff-output", type=Path)
    args = ap.parse_args()

    candidate, diff_text = generate(args.source)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(candidate, encoding="utf-8")
    if args.diff_output is not None:
        args.diff_output.parent.mkdir(parents=True, exist_ok=True)
        args.diff_output.write_text(diff_text, encoding="utf-8")

    print(args.output)
    if args.diff_output is not None:
        print(args.diff_output)
    print("Issue #68 HARD production-candidate deterministic diff PASS")


if __name__ == "__main__":
    main()
