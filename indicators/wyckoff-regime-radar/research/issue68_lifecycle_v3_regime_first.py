#!/usr/bin/env python3
"""Issue #68 regime-first lifecycle v3.

Pure desired-position state machine. No PnL, sizing, stops, targets, breakout
entry gates, ARM handshake, or Early Fail logic.
"""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np


@dataclass(frozen=True)
class RegimeFirstResult:
    position: np.ndarray
    events: dict[str, np.ndarray]


def lifecycle_v3_regime_first(formal: np.ndarray, *, warmup: int) -> RegimeFirstResult:
    """Map C-2 Formal stages to a regime-first desired position.

    Stage semantics:
      2 -> long
      5 -> short
      1/4 -> flat
      3 -> hold long only; otherwise flat
      6 -> hold short only; otherwise flat
      0 -> preserve prior state
    """
    formal = np.asarray(formal, dtype=int)
    n = len(formal)
    if warmup < 0:
        raise ValueError("warmup must be >= 0")

    position_out = np.zeros(n, dtype=int)
    names = (
        "enter_long",
        "enter_short",
        "exit_long",
        "exit_short",
        "flip_long_to_short",
        "flip_short_to_long",
        "hold_long_reaccumulation",
        "hold_short_redistribution",
    )
    events = {name: np.zeros(n, dtype=bool) for name in names}

    position = 0
    for i, raw_stage in enumerate(formal):
        if i < warmup:
            position = 0
            continue

        stage = int(raw_stage)
        before = position

        if stage == 0:
            after = before
        elif stage == 1 or stage == 4:
            after = 0
        elif stage == 2:
            after = 1
        elif stage == 5:
            after = -1
        elif stage == 3:
            after = 1 if before == 1 else 0
        elif stage == 6:
            after = -1 if before == -1 else 0
        else:
            raise ValueError(f"unexpected Formal stage id: {stage}")

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

        if stage == 3 and before == 1 and after == 1:
            events["hold_long_reaccumulation"][i] = True
        if stage == 6 and before == -1 and after == -1:
            events["hold_short_redistribution"][i] = True

        position = after
        position_out[i] = position

    return RegimeFirstResult(position=position_out, events=events)


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
