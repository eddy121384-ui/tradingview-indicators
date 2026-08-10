#!/usr/bin/env python3
"""Mechanically derive the v0.6 Phase-A research core from frozen v0.5.2.1.

The generator deliberately performs small, auditable transformations instead of
copying the full mirror and editing it by hand. The frozen Pine source is not
touched. The v0.5 Python mirror is also not modified by this module.
"""

from __future__ import annotations

import argparse
import hashlib
import sys
import types
from pathlib import Path


HERE = Path(__file__).resolve().parent
BASELINE = HERE / "price_only_core.py"
EXPECTED_BASELINE_GIT_BLOB_SHA = "b7d1c7e02194e46e162c999854aff6907bd5be3d"

IMPORT_ANCHOR = "import pandas as pd\n"
IMPORT_BLOCK = '''\ntry:\n    from .v06_boundary_scores import (\n        soft_above_range_score,\n        soft_below_range_score,\n        soft_hold_strength,\n        soft_no_break_high_score,\n        soft_no_break_low_score,\n    )\nexcept ImportError:  # direct script execution / generated-module execution\n    from v06_boundary_scores import (  # type: ignore\n        soft_above_range_score,\n        soft_below_range_score,\n        soft_hold_strength,\n        soft_no_break_high_score,\n        soft_no_break_low_score,\n    )\n'''

OLD_LOW = "    no_break_low_score = np.where(close > prev_abs_low, 100.0, 0.0)"
OLD_HIGH = "    no_break_high_score = np.where(close < prev_abs_high, 100.0, 0.0)"
NEW_LOW = "    no_break_low_score = soft_no_break_low_score(close, prev_abs_low, atr_v)"
NEW_HIGH = "    no_break_high_score = soft_no_break_high_score(close, prev_abs_high, atr_v)"

OLD_RANGE_CONT = '''    range_cont_up = np.where(sustained_above, 100.0, np.where(above_prev_range, 80.0, np.where(recent_break_up, 65.0, np.where(close > range_mid, 35.0, 0.0))))
    range_cont_dn = np.where(sustained_below, 100.0, np.where(below_prev_range, 80.0, np.where(recent_break_dn, 65.0, np.where(close < range_mid, 35.0, 0.0))))'''
NEW_RANGE_CONT = '''    above_prev_range_score = soft_above_range_score(close, prev_range_high, atr_v)
    below_prev_range_score = soft_below_range_score(close, prev_range_low, atr_v)
    sustained_above_score = soft_hold_strength(above_prev_range_score, cfg.continuation_hold_bars)
    sustained_below_score = soft_hold_strength(below_prev_range_score, cfg.continuation_hold_bars)
    range_cont_up_base = np.where(recent_break_up, 65.0, np.where(close > range_mid, 35.0, 0.0))
    range_cont_dn_base = np.where(recent_break_dn, 65.0, np.where(close < range_mid, 35.0, 0.0))
    range_cont_up = np.maximum(
        range_cont_up_base,
        np.maximum(
            np.nan_to_num(above_prev_range_score, nan=0.0) * 0.80,
            np.nan_to_num(sustained_above_score, nan=0.0),
        ),
    )
    range_cont_dn = np.maximum(
        range_cont_dn_base,
        np.maximum(
            np.nan_to_num(below_prev_range_score, nan=0.0) * 0.80,
            np.nan_to_num(sustained_below_score, nan=0.0),
        ),
    )'''

DIAGNOSTIC_ANCHOR = '        "range_score": range_score,\n'
DIAGNOSTIC_INSERT = (
    '        "no_break_low_score": no_break_low_score,\n'
    '        "no_break_high_score": no_break_high_score,\n'
    '        "prev_range_high": prev_range_high,\n'
    '        "prev_range_low": prev_range_low,\n'
    '        "above_prev_range": above_prev_range.astype(float),\n'
    '        "below_prev_range": below_prev_range.astype(float),\n'
    '        "above_prev_range_score": above_prev_range_score,\n'
    '        "below_prev_range_score": below_prev_range_score,\n'
    '        "sustained_above_score": sustained_above_score,\n'
    '        "sustained_below_score": sustained_below_score,\n'
    '        "range_break_up": range_break_up.astype(float),\n'
    '        "range_break_dn": range_break_dn.astype(float),\n'
    '        "recent_break_up": recent_break_up.astype(float),\n'
    '        "recent_break_dn": recent_break_dn.astype(float),\n'
    '        "range_cont_up": range_cont_up,\n'
    '        "range_cont_dn": range_cont_dn,\n'
    '        "breakout_score": breakout_score,\n'
    '        "explicit_breakdown_score": explicit_breakdown_score,\n'
    '        "breakout_gate": breakout_gate,\n'
    '        "explicit_breakdown_gate": explicit_breakdown_gate,\n'
    '        "range_cont_up_gate": range_cont_up_gate,\n'
    '        "range_cont_dn_gate": range_cont_dn_gate,\n'
    '        "markup_continuation_score": markup_continuation_score,\n'
    '        "markdown_continuation_score": markdown_continuation_score,\n'
    '        "breakout_markup_gate": breakout_markup_gate,\n'
    '        "breakdown_markdown_gate": breakdown_markdown_gate,\n'
    '        "markup_cont_gate": markup_cont_gate,\n'
    '        "markdown_cont_gate": markdown_cont_gate,\n'
    '        "markup_gate": markup_gate,\n'
    '        "markdown_gate": markdown_gate,\n'
)


def git_blob_sha(data: bytes) -> str:
    header = f"blob {len(data)}\0".encode()
    return hashlib.sha1(header + data).hexdigest()


def render_v06_source(baseline_path: Path = BASELINE) -> str:
    raw = baseline_path.read_bytes()
    actual = git_blob_sha(raw)
    if actual != EXPECTED_BASELINE_GIT_BLOB_SHA:
        raise RuntimeError(
            "Frozen v0.5 research mirror moved; refusing mechanical v0.6 transform: "
            f"expected {EXPECTED_BASELINE_GIT_BLOB_SHA}, got {actual}"
        )

    source = raw.decode("utf-8")
    for needle, label in (
        (IMPORT_ANCHOR, "import anchor"),
        (OLD_LOW, "low hard threshold"),
        (OLD_HIGH, "high hard threshold"),
        (OLD_RANGE_CONT, "range continuation hard-threshold block"),
        (DIAGNOSTIC_ANCHOR, "diagnostic anchor"),
    ):
        if source.count(needle) != 1:
            raise RuntimeError(f"Expected exactly one {label}; found {source.count(needle)}")

    source = source.replace(IMPORT_ANCHOR, IMPORT_ANCHOR + IMPORT_BLOCK, 1)
    source = source.replace(OLD_LOW, NEW_LOW, 1)
    source = source.replace(OLD_HIGH, NEW_HIGH, 1)
    source = source.replace(OLD_RANGE_CONT, NEW_RANGE_CONT, 1)
    source = source.replace(DIAGNOSTIC_ANCHOR, DIAGNOSTIC_ANCHOR + DIAGNOSTIC_INSERT, 1)

    banner = (
        "# GENERATED EXPERIMENTAL CORE — Issue #57 / v0.6 Phase A\n"
        "# Mechanical delta from frozen v0.5.2.1 research mirror:\n"
        "#   1) noBreakLowScore: binary 0/100 -> continuous ATR-scaled score\n"
        "#   2) noBreakHighScore: binary 0/100 -> continuous ATR-scaled score\n"
        "#   3) prior-range continuation: boolean 65/80/100 cliff -> continuous ATR-scaled hold strength\n"
        "# Additional emitted columns are diagnostics only; they do not change calculations.\n"
        "# No state-count, formal-state persistence, witness, or trading-rule changes.\n\n"
    )
    return banner + source


def load_v06_namespace() -> dict[str, object]:
    module_name = "wyckoff_v06_generated"
    module = types.ModuleType(module_name)
    module.__file__ = str(HERE / "generated" / "wyckoff-v06-price-only-core.py")
    module.__package__ = None
    sys.modules[module_name] = module
    exec(compile(render_v06_source(), module.__file__, "exec"), module.__dict__)
    return module.__dict__


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate Issue #57 v0.6 Phase-A research core")
    parser.add_argument("--output", type=Path, required=True)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(render_v06_source(), encoding="utf-8")


if __name__ == "__main__":
    main()
