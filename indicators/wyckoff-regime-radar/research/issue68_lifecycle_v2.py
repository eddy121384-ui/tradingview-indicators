#!/usr/bin/env python3
"""Issue #68 frozen human-review-v2 lifecycle state machine.

This is a mechanical Python port of the canonical TradingView state machine in
archived Issue #61 `generate_issue61_stage_lifecycle_strategy_preview.py`.
It intentionally contains no PnL, sizing, stop search, target search, or
classifier logic.  The repaired Issue #66 C-2 classifier is an upstream input.
"""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np


@dataclass(frozen=True)
class LifecycleResult:
    position: np.ndarray
    armed_dir: np.ndarray
    entry_age: np.ndarray
    entry_level: np.ndarray
    events: dict[str, np.ndarray]
    entry_lag: np.ndarray


def _as_int(values: np.ndarray) -> np.ndarray:
    return np.asarray(values, dtype=int)


def _as_bool(values: np.ndarray) -> np.ndarray:
    return np.asarray(values, dtype=bool)


def _as_float(values: np.ndarray) -> np.ndarray:
    return np.asarray(values, dtype=float)


def lifecycle_v2(
    formal: np.ndarray,
    fresh_up: np.ndarray,
    fresh_down: np.ndarray,
    close: np.ndarray,
    range_high_break: np.ndarray,
    range_low_break: np.ndarray,
    *,
    warmup: int,
    confirm_bars: int,
) -> LifecycleResult:
    """Replay the Issue #61 human-review-v2 lifecycle exactly.

    `position` is the desired position known at each bar close.  It is not an
    executed PnL position; next-bar execution belongs to later research phases.
    """
    formal = _as_int(formal)
    fresh_up = _as_bool(fresh_up)
    fresh_down = _as_bool(fresh_down)
    close = _as_float(close)
    range_high_break = _as_float(range_high_break)
    range_low_break = _as_float(range_low_break)

    n = len(formal)
    if not all(len(x) == n for x in (fresh_up, fresh_down, close, range_high_break, range_low_break)):
        raise ValueError("all lifecycle arrays must have equal length")
    if warmup < 0:
        raise ValueError("warmup must be >= 0")
    if confirm_bars < 1:
        raise ValueError("confirm_bars must be >= 1")

    position_out = np.zeros(n, dtype=int)
    armed_out = np.zeros(n, dtype=int)
    entry_age_out = np.full(n, -1, dtype=int)
    entry_level_out = np.full(n, np.nan, dtype=float)
    entry_lag = np.full(n, np.nan, dtype=float)

    names = (
        "arm_long",
        "arm_short",
        "entry_long",
        "entry_short",
        "early_fail_long",
        "early_fail_short",
        "opposite_exit_long",
        "opposite_exit_short",
        "add_long_candidate",
        "add_short_candidate",
        "cancel_long_arm",
        "cancel_short_arm",
        "direct_transition_long",
        "direct_transition_short",
    )
    events = {name: np.zeros(n, dtype=bool) for name in names}

    position = 0
    armed_dir = 0
    armed_at = -1
    armed_level = float("nan")
    entry_level = float("nan")
    entry_age = -1

    for i in range(n):
        # Canonical Pine uses `issue61Ready = bar_index >= rankLen - 1` and
        # explicitly resets all state on every pre-ready bar.
        if i < warmup:
            position = 0
            armed_dir = 0
            armed_at = -1
            armed_level = float("nan")
            entry_level = float("nan")
            entry_age = -1
            continue

        before = position
        stage = int(formal[i])
        closed_this_bar = False

        # Held trend survives neutral/unresolved and same-side pauses.  Only an
        # explicit opposite Formal family closes it.
        if position == 1 and stage in (4, 5, 6):
            position = 0
            events["opposite_exit_long"][i] = True
            closed_this_bar = True
            entry_level = float("nan")
            entry_age = -1
            armed_dir = 0
            armed_at = -1
            armed_level = float("nan")
        elif position == -1 and stage in (1, 2, 3):
            position = 0
            events["opposite_exit_short"][i] = True
            closed_this_bar = True
            entry_level = float("nan")
            entry_age = -1
            armed_dir = 0
            armed_at = -1
            armed_level = float("nan")

        # Continuation breaks are observation-only ADD? candidates.
        if position == 1 and stage == 2 and fresh_up[i]:
            events["add_long_candidate"][i] = True
        if position == -1 and stage == 5 and fresh_down[i]:
            events["add_short_candidate"][i] = True

        # Early structural invalidation is active only after entry, ages
        # 1..confirm_bars.  The entry bar itself has age 0 and is not tested.
        was_holding = before == position and position != 0
        if was_holding and np.isfinite(entry_level):
            entry_age += 1
            if entry_age <= confirm_bars:
                invalidated = (
                    (position == 1 and np.isfinite(close[i]) and close[i] <= entry_level)
                    or (position == -1 and np.isfinite(close[i]) and close[i] >= entry_level)
                )
                if invalidated:
                    events["early_fail_long"][i] = position == 1
                    events["early_fail_short"][i] = position == -1
                    position = 0
                    closed_this_bar = True
                    entry_level = float("nan")
                    entry_age = -1
                    armed_dir = 0
                    armed_at = -1
                    armed_level = float("nan")
            else:
                entry_level = float("nan")
                entry_age = -1

        # Resolve a previously armed precursor setup before allowing any new
        # setup on the current bar.
        if position == 0 and not closed_this_bar and armed_dir != 0:
            arm_age = i - armed_at
            target = 2 if armed_dir == 1 else 5
            precursor = 1 if armed_dir == 1 else 4
            if arm_age <= confirm_bars and stage == target:
                position = armed_dir
                entry_level = armed_level
                entry_age = 0
                if position == 1:
                    events["entry_long"][i] = True
                else:
                    events["entry_short"][i] = True
                entry_lag[i] = float(arm_age)
                armed_dir = 0
                armed_at = -1
                armed_level = float("nan")
            elif arm_age > confirm_bars or stage not in (precursor, target):
                if armed_dir == 1:
                    events["cancel_long_arm"][i] = True
                else:
                    events["cancel_short_arm"][i] = True
                armed_dir = 0
                armed_at = -1
                armed_level = float("nan")

        # A NEW lifecycle starts only from the precursor stage, except that an
        # exact precursor->target transition with a fresh break is accepted.
        # Crucially, a generic fresh break inside an already-running Stage 2/5
        # is not a flat chase entry.
        if position == 0 and not closed_this_bar and armed_dir == 0:
            prev_stage = int(formal[i - 1]) if i > 0 else 0
            direct_long = fresh_up[i] and stage == 2 and prev_stage == 1
            direct_short = fresh_down[i] and stage == 5 and prev_stage == 4
            if direct_long:
                position = 1
                entry_level = float(range_high_break[i])
                entry_age = 0
                events["entry_long"][i] = True
                events["direct_transition_long"][i] = True
                entry_lag[i] = 0.0
            elif direct_short:
                position = -1
                entry_level = float(range_low_break[i])
                entry_age = 0
                events["entry_short"][i] = True
                events["direct_transition_short"][i] = True
                entry_lag[i] = 0.0
            elif fresh_up[i] and stage == 1:
                armed_dir = 1
                armed_at = i
                armed_level = float(range_high_break[i])
                events["arm_long"][i] = True
            elif fresh_down[i] and stage == 4:
                armed_dir = -1
                armed_at = i
                armed_level = float(range_low_break[i])
                events["arm_short"][i] = True

        position_out[i] = position
        armed_out[i] = armed_dir
        entry_age_out[i] = entry_age
        entry_level_out[i] = entry_level

    return LifecycleResult(
        position=position_out,
        armed_dir=armed_out,
        entry_age=entry_age_out,
        entry_level=entry_level_out,
        events=events,
        entry_lag=entry_lag,
    )


def holding_durations(position: np.ndarray, *, start: int = 0) -> list[int]:
    """Contiguous non-zero desired-position episode lengths."""
    values = np.asarray(position, dtype=int)[start:]
    out: list[int] = []
    current = 0
    length = 0
    for value in values:
        if value == 0:
            if current != 0:
                out.append(length)
            current = 0
            length = 0
        elif value == current:
            length += 1
        else:
            if current != 0:
                out.append(length)
            current = int(value)
            length = 1
    if current != 0:
        out.append(length)
    return out
