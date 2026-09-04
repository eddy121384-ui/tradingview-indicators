#!/usr/bin/env python3
"""Issue #68 Phase B3.3 core trend-bias memory.

This is not executable exposure. It preserves directional regime memory through
Formal 0/1/4 and flips only when the opposite trend family is formally active.
No PnL, sizing, stops, targets, or Flat Action logic are included.
"""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np


@dataclass(frozen=True)
class CoreBiasResult:
    bias: np.ndarray
    events: dict[str, np.ndarray]


def core_bias_v33(formal: np.ndarray, *, warmup: int) -> CoreBiasResult:
    formal = np.asarray(formal, dtype=int)
    n = len(formal)
    if warmup < 0:
        raise ValueError("warmup must be >= 0")

    bias_out = np.zeros(n, dtype=int)
    names = (
        "establish_bull_bias",
        "establish_bear_bias",
        "flip_bull_to_bear",
        "flip_bear_to_bull",
    )
    events = {name: np.zeros(n, dtype=bool) for name in names}

    bias = 0
    for i, raw_stage in enumerate(formal):
        if i < warmup:
            bias = 0
            continue

        stage = int(raw_stage)
        if stage < 0 or stage > 6:
            raise ValueError(f"unexpected Formal stage id: {stage}")

        before = bias
        after = before

        if before == 0:
            if stage == 2:
                after = 1
            elif stage == 5:
                after = -1
            else:
                after = 0
        elif before == 1:
            after = -1 if stage in (5, 6) else 1
        elif before == -1:
            after = 1 if stage in (2, 3) else -1

        if before == 0 and after == 1:
            events["establish_bull_bias"][i] = True
        elif before == 0 and after == -1:
            events["establish_bear_bias"][i] = True
        elif before == 1 and after == -1:
            events["flip_bull_to_bear"][i] = True
        elif before == -1 and after == 1:
            events["flip_bear_to_bull"][i] = True

        bias = after
        bias_out[i] = bias

    return CoreBiasResult(bias=bias_out, events=events)
