#!/usr/bin/env python3
"""Issue #66 Phase B-1: derive a reciprocal-safe representation core.

This generator starts from the frozen v0.6 Phase-B research core and changes
only the preregistered representation family. Directional heuristics, stage
weights/gates, persistence, and all strategy concepts remain untouched.
"""

from __future__ import annotations

import argparse
import sys
import types
from pathlib import Path

from generate_v06_phase_b_core import render_phase_b_source


HERE = Path(__file__).resolve().parent

OLD_HEAT_REPRESENTATION = '''    ma = rolling_sma(close, cfg.ma_len)
    atr_v = atr(high, low, close, cfg.atr_len)
    dist_atr = safe_div(close - ma, atr_v)'''

NEW_HEAT_REPRESENTATION = '''    # Issue #66 B-1 representation: geometric MA + reciprocal-invariant log ATR.
    log_high = np.log(np.where(high > 0.0, high, np.nan))
    log_low = np.log(np.where(low > 0.0, low, np.nan))
    ma_log = rolling_sma(log_price, cfg.ma_len)
    ma = np.exp(ma_log)
    atr_v = atr(high, low, close, cfg.atr_len)  # retained for frozen v0.6 boundary primitives
    sym_atr = atr(log_high, log_low, log_price, cfg.atr_len)
    dist_atr = safe_div(log_price - ma_log, sym_atr)'''

OLD_MATURITY_REPRESENTATION = '''    maturity_ma = rolling_sma(close, cfg.maturity_ma_len)
    maturity_atr = atr(high, low, close, cfg.maturity_atr_len)
    maturity_dist_atr = safe_div(close - maturity_ma, maturity_atr)'''

NEW_MATURITY_REPRESENTATION = '''    maturity_ma_log = rolling_sma(log_price, cfg.maturity_ma_len)
    maturity_ma = np.exp(maturity_ma_log)
    maturity_atr = atr(high, low, close, cfg.maturity_atr_len)  # retained diagnostic compatibility
    maturity_sym_atr = atr(log_high, log_low, log_price, cfg.maturity_atr_len)
    maturity_dist_atr = safe_div(log_price - maturity_ma_log, maturity_sym_atr)'''

OLD_LOW_VOL_REPRESENTATION = "    atr_pct = safe_div(atr_v, close) * 100.0"
NEW_LOW_VOL_REPRESENTATION = "    atr_pct = sym_atr * 100.0"

OLD_MA_CROSS = '''    ma_cross_up = crossover(close, ma)
    ma_cross_dn = crossunder(close, ma)'''
NEW_MA_CROSS = '''    ma_cross_up = crossover(log_price, ma_log)
    ma_cross_dn = crossunder(log_price, ma_log)'''

OLD_RANGE_WIDTH = "    range_width_atr = safe_div(range_width, atr_v)"
NEW_RANGE_WIDTH = '''    range_width_log = np.log(range_high) - np.log(range_low)
    range_width_atr = safe_div(range_width_log, sym_atr)'''

OLD_MA_SPREAD = "    ma_spread_atr = safe_div(ma - maturity_ma, atr_v)"
NEW_MA_SPREAD = "    ma_spread_atr = safe_div(ma_log - maturity_ma_log, sym_atr)"

DIAGNOSTIC_ANCHOR = '        "range_score": range_score,\n'
DIAGNOSTIC_INSERT = (
    '        "issue66_b1_ma_log": ma_log,\n'
    '        "issue66_b1_maturity_ma_log": maturity_ma_log,\n'
    '        "issue66_b1_sym_atr": sym_atr,\n'
    '        "issue66_b1_maturity_sym_atr": maturity_sym_atr,\n'
    '        "issue66_b1_dist_atr": dist_atr,\n'
    '        "issue66_b1_maturity_dist_atr": maturity_dist_atr,\n'
    '        "issue66_b1_atr_pct": atr_pct,\n'
    '        "issue66_b1_range_width_atr": range_width_atr,\n'
    '        "issue66_b1_ma_spread_atr": ma_spread_atr,\n'
)


def render_phase_b1_source() -> str:
    source = render_phase_b_source()
    replacements = (
        (OLD_HEAT_REPRESENTATION, NEW_HEAT_REPRESENTATION, "heat representation"),
        (OLD_MATURITY_REPRESENTATION, NEW_MATURITY_REPRESENTATION, "maturity representation"),
        (OLD_LOW_VOL_REPRESENTATION, NEW_LOW_VOL_REPRESENTATION, "low-vol representation"),
        (OLD_MA_CROSS, NEW_MA_CROSS, "MA-cross representation"),
        (OLD_RANGE_WIDTH, NEW_RANGE_WIDTH, "range-width representation"),
        (OLD_MA_SPREAD, NEW_MA_SPREAD, "MA-spread representation"),
    )
    for old, new, label in replacements:
        count = source.count(old)
        if count != 1:
            raise RuntimeError(f"Expected exactly one {label}; found {count}")
        source = source.replace(old, new, 1)

    if source.count(DIAGNOSTIC_ANCHOR) != 1:
        raise RuntimeError(
            f"Expected exactly one diagnostic anchor; found {source.count(DIAGNOSTIC_ANCHOR)}"
        )
    source = source.replace(DIAGNOSTIC_ANCHOR, DIAGNOSTIC_ANCHOR + DIAGNOSTIC_INSERT, 1)

    return (
        "# ISSUE #66 PHASE B-1 — RECIPROCAL-SAFE REPRESENTATION\n"
        "# Parent: frozen v0.6 Phase-B research core.\n"
        "# Delta only: geometric/log MA representation, log-space ATR distances/volatility,\n"
        "# reciprocal-safe MA crosses, range-width scale, and MA-spread scale.\n"
        "# Directional heuristics, stage formulas/gates, persistence, and strategy logic are unchanged.\n\n"
        + source
    )


def load_phase_b1_namespace() -> dict[str, object]:
    module_name = "wyckoff_issue66_phase_b1_generated"
    module = types.ModuleType(module_name)
    module.__file__ = str(HERE / "generated" / "wyckoff-issue66-phase-b1-representation-core.py")
    module.__package__ = None
    sys.modules[module_name] = module
    exec(compile(render_phase_b1_source(), module.__file__, "exec"), module.__dict__)
    return module.__dict__


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate Issue #66 Phase B-1 representation core")
    parser.add_argument("--output", type=Path, required=True)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(render_phase_b1_source(), encoding="utf-8")


if __name__ == "__main__":
    main()
