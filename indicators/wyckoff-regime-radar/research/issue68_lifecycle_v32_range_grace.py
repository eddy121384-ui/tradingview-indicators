#!/usr/bin/env python3
"""Issue #68 Phase B3.2 range-grace lifecycle.

Pure desired-position state machine. No PnL, sizing, stops, targets, or entry
filter changes. B3.2 changes hold/exit semantics only: Formal 1/4 must persist
for inherited `confirm_bars` consecutive Formal bars before an existing trend
position is flattened.
"""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np


@dataclass(frozen=True)
class RangeGraceResult:
    position: np.ndarray
    range_grace_bars: np.ndarray
    events: dict[str, np.ndarray]


def lifecycle_v32_range_grace(
    formal: np.ndarray,
    *,
    warmup: int,
    confirm_bars: int,
) -> RangeGraceResult:
    """Map C-2 Formal stages to B3.2 desired position.

    Entry remains B3-simple:
      flat + Stage 2 -> long
      flat + Stage 5 -> short

    Hold/exit change:
      Stage 1/4 no longer flatten immediately. They advance a range-grace
      counter while a position is held; Flat occurs only when the counter reaches
      `confirm_bars`. Stage 0 preserves both position and the current grace count.
      Same-side trend family resets the grace count. Opposite trend family flips.
    """
    formal = np.asarray(formal, dtype=int)
    n = len(formal)
    if warmup < 0:
        raise ValueError("warmup must be >= 0")
    if confirm_bars < 1:
        raise ValueError("confirm_bars must be >= 1")

    position_out = np.zeros(n, dtype=int)
    grace_out = np.zeros(n, dtype=int)
    names = (
        "enter_long",
        "enter_short",
        "exit_long",
        "exit_short",
        "flip_long_to_short",
        "flip_short_to_long",
        "range_grace_active_long",
        "range_grace_active_short",
        "range_grace_exit_long",
        "range_grace_exit_short",
    )
    events = {name: np.zeros(n, dtype=bool) for name in names}

    position = 0
    grace = 0

    for i, raw_stage in enumerate(formal):
        if i < warmup:
            position = 0
            grace = 0
            continue

        stage = int(raw_stage)
        if stage < 0 or stage > 6:
            raise ValueError(f"unexpected Formal stage id: {stage}")

        before = position
        after = before
        next_grace = grace

        if before == 0:
            next_grace = 0
            if stage == 2:
                after = 1
            elif stage == 5:
                after = -1
            else:
                after = 0

        elif before == 1:
            if stage in (2, 3):
                after = 1
                next_grace = 0
            elif stage in (5, 6):
                after = -1
                next_grace = 0
            elif stage in (1, 4):
                next_grace = grace + 1
                if next_grace >= confirm_bars:
                    after = 0
                    next_grace = 0
                    events["range_grace_exit_long"][i] = True
                else:
                    after = 1
                    events["range_grace_active_long"][i] = True
            elif stage == 0:
                after = 1
                next_grace = grace

        elif before == -1:
            if stage in (5, 6):
                after = -1
                next_grace = 0
            elif stage in (2, 3):
                after = 1
                next_grace = 0
            elif stage in (1, 4):
                next_grace = grace + 1
                if next_grace >= confirm_bars:
                    after = 0
                    next_grace = 0
                    events["range_grace_exit_short"][i] = True
                else:
                    after = -1
                    events["range_grace_active_short"][i] = True
            elif stage == 0:
                after = -1
                next_grace = grace

        if before == 1 and after == -1:
            events["flip_long_to_short"][i] = True
            events["exit_long"][i] = True
            events["enter_short"][i] = True
        elif before == -1 and after == 1:
            events["flip_short_to_long"][i] = True
            events["exit_short"][i] = True
            events["enter_long"][i] = True
        else:
            if before != 1 and after == 1:
                events["enter_long"][i] = True
            if before != -1 and after == -1:
                events["enter_short"][i] = True
            if before == 1 and after != 1:
                events["exit_long"][i] = True
            if before == -1 and after != -1:
                events["exit_short"][i] = True

        position = after
        grace = next_grace
        position_out[i] = position
        grace_out[i] = grace

    return RangeGraceResult(position=position_out, range_grace_bars=grace_out, events=events)


def holding_durations(position: np.ndarray, *, start: int = 0) -> list[int]:
    """Lengths of contiguous non-zero desired-position episodes."""
    values = np.asarray(position, dtype=int)[start:]
    out: list[int] = []
    current = 0
    length = 0
    for value in values:
        value = int(value)
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
            current = value
            length = 1
    if current != 0:
        out.append(length)
    return out
