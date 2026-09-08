#!/usr/bin/env python3
"""Issue #68 v3.1 entry/hold separation lifecycle.

Entry authorization uses the already-defined C-2 strong stage. Holding/exit remains
Formal-regime driven. No PnL, sizing, stops, targets, breakout handshake, or Early Fail.
"""
from __future__ import annotations

from dataclasses import dataclass
import numpy as np


@dataclass(frozen=True)
class LifecycleV31Result:
    position: np.ndarray
    events: dict[str, np.ndarray]


def lifecycle_v31(formal: np.ndarray, strong_stage: np.ndarray, *, warmup: int) -> LifecycleV31Result:
    formal = np.asarray(formal, dtype=int)
    strong_stage = np.asarray(strong_stage, dtype=int)
    if len(formal) != len(strong_stage):
        raise ValueError("formal and strong_stage must have equal length")

    n = len(formal)
    pos_out = np.zeros(n, dtype=int)
    names = (
        "enter_long", "enter_short", "exit_long", "exit_short",
        "flip_long_to_short", "flip_short_to_long",
        "blocked_long_entry", "blocked_short_entry",
        "hold_long_reaccumulation", "hold_short_redistribution",
    )
    events = {name: np.zeros(n, dtype=bool) for name in names}
    pos = 0

    for i in range(n):
        if i < warmup:
            pos = 0
            continue

        before = pos
        stage = int(formal[i])
        strong = int(strong_stage[i])
        after = before

        if stage == 0:
            after = before
        elif stage in (1, 4):
            after = 0
        elif stage == 3:
            after = 1 if before == 1 else 0
        elif stage == 6:
            after = -1 if before == -1 else 0
        elif stage == 2:
            if before == 1:
                after = 1
            elif strong == 2:
                after = 1
            else:
                after = 0
                events["blocked_long_entry"][i] = True
        elif stage == 5:
            if before == -1:
                after = -1
            elif strong == 5:
                after = -1
            else:
                after = 0
                events["blocked_short_entry"][i] = True
        else:
            after = 0

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

        events["hold_long_reaccumulation"][i] = stage == 3 and before == 1 and after == 1
        events["hold_short_redistribution"][i] = stage == 6 and before == -1 and after == -1
        pos = after
        pos_out[i] = pos

    return LifecycleV31Result(position=pos_out, events=events)
