#!/usr/bin/env python3
"""Derive the Issue #57 Phase-B persistence core from Phase A.

Phase B does not shorten strong-candidate confirmation and does not promote weak
candidates. It adds a conservative decay-to-neutral rule: if an existing Formal
state receives sustained chaos, a weak opposing challenger, or coexistence
pressure for ``2 * confirm_bars`` (6 bars under the frozen defaults), the stale
Formal state is cleared to 0. A replacement state still requires the original
strong-candidate confirmation path.

The 2x horizon was selected from the preregistered 1x/2x/3x engineering sweep on
burned history using stale-carry reduction versus Neutral/switch churn only. No
PnL was consulted.
"""

from __future__ import annotations

import argparse
import sys
import types
from pathlib import Path

from generate_v06_price_only_core import render_v06_source


HERE = Path(__file__).resolve().parent
STALE_DECAY_MULTIPLIER = 2

OLD_INERTIA_BLOCK = '''    # Regime inertia: imperative loop mirrors Pine var state exactly.
    formal_id = np.zeros(n, dtype=int)
    candidate_id = np.zeros(n, dtype=int)
    candidate_bars_series = np.zeros(n, dtype=int)
    candidate_display_id = np.where(strong_candidate | weak_candidate, top_id, 0).astype(int)
    confirmed = 0
    candidate = 0
    candidate_bars = 0
    no_regime_bars = 0
    for i in range(n):
        if strong_candidate[i]:
            no_regime_bars = 0
            raw_id = int(top_id[i])
            if raw_id == candidate:
                candidate_bars += 1
            else:
                candidate = raw_id
                candidate_bars = 1
            if candidate_bars >= int(active_confirm_bars[i]):
                confirmed = candidate
        else:
            candidate = 0
            candidate_bars = 0
            if chaos[i]:
                no_regime_bars += 1
                if no_regime_bars >= cfg.confirm_bars:
                    confirmed = 0
            else:
                no_regime_bars = 0
        formal_id[i] = confirmed
        candidate_id[i] = candidate
        candidate_bars_series[i] = candidate_bars'''

NEW_INERTIA_BLOCK = '''    # Phase B persistence redesign: preserve strong-candidate confirmation,
    # but let an unsupported old Formal state decay to neutral after 2x the
    # existing confirm_bars horizon. Weak challengers are never promoted directly.
    formal_id = np.zeros(n, dtype=int)
    candidate_id = np.zeros(n, dtype=int)
    candidate_bars_series = np.zeros(n, dtype=int)
    candidate_display_id = np.where(strong_candidate | weak_candidate, top_id, 0).astype(int)
    stale_pressure_bars_series = np.zeros(n, dtype=int)
    stale_pressure_reason_series = np.zeros(n, dtype=int)
    confirmed = 0
    candidate = 0
    candidate_bars = 0
    stale_pressure_bars = 0
    stale_limit = cfg.confirm_bars * 2
    for i in range(n):
        if strong_candidate[i]:
            stale_pressure_bars = 0
            stale_reason = 0
            raw_id = int(top_id[i])
            if raw_id == candidate:
                candidate_bars += 1
            else:
                candidate = raw_id
                candidate_bars = 1
            if candidate_bars >= int(active_confirm_bars[i]):
                confirmed = candidate
        else:
            candidate = 0
            candidate_bars = 0
            display_id = int(candidate_display_id[i])
            weak_challenger = confirmed != 0 and display_id != 0 and display_id != confirmed
            coexist_pressure = confirmed != 0 and bool(coexist[i]) and display_id == 0
            if bool(chaos[i]) and confirmed != 0:
                stale_reason = 1
            elif weak_challenger:
                stale_reason = 2
            elif coexist_pressure:
                stale_reason = 3
            else:
                stale_reason = 0

            if stale_reason != 0:
                stale_pressure_bars += 1
                if stale_pressure_bars >= stale_limit:
                    confirmed = 0
            else:
                stale_pressure_bars = 0

        formal_id[i] = confirmed
        candidate_id[i] = candidate
        candidate_bars_series[i] = candidate_bars
        stale_pressure_bars_series[i] = stale_pressure_bars
        stale_pressure_reason_series[i] = stale_reason'''

OLD_DIAGNOSTIC_TAIL = '''        "candidate_id": candidate_id,
        "candidate_bars": candidate_bars_series,
        "candidate_display_id": candidate_display_id,
        "formal_id": formal_id,
    }'''
NEW_DIAGNOSTIC_TAIL = '''        "candidate_id": candidate_id,
        "candidate_bars": candidate_bars_series,
        "candidate_display_id": candidate_display_id,
        "formal_id": formal_id,
        "stale_pressure_bars": stale_pressure_bars_series,
        "stale_pressure_reason": stale_pressure_reason_series,
    }'''


def render_phase_b_source() -> str:
    source = render_v06_source()
    for needle, label in (
        (OLD_INERTIA_BLOCK, "Phase-A inertia block"),
        (OLD_DIAGNOSTIC_TAIL, "diagnostic tail"),
    ):
        if source.count(needle) != 1:
            raise RuntimeError(f"Expected exactly one {label}; found {source.count(needle)}")
    source = source.replace(OLD_INERTIA_BLOCK, NEW_INERTIA_BLOCK, 1)
    source = source.replace(OLD_DIAGNOSTIC_TAIL, NEW_DIAGNOSTIC_TAIL, 1)
    return (
        "# PHASE B PERSISTENCE REDESIGN — Issue #57\n"
        "# Parent: mechanically generated v0.6 Phase-A core.\n"
        "# Frozen rule: unsupported Formal states decay to neutral after 2x confirmBars; weak challengers are not promoted.\n\n"
        + source
    )


def load_phase_b_namespace() -> dict[str, object]:
    module_name = "wyckoff_v06_phase_b_generated"
    module = types.ModuleType(module_name)
    module.__file__ = str(HERE / "generated" / "wyckoff-v06-phase-b-core.py")
    module.__package__ = None
    sys.modules[module_name] = module
    exec(compile(render_phase_b_source(), module.__file__, "exec"), module.__dict__)
    return module.__dict__


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate Issue #57 v0.6 Phase-B persistence core")
    parser.add_argument("--output", type=Path, required=True)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(render_phase_b_source(), encoding="utf-8")


if __name__ == "__main__":
    main()
