#!/usr/bin/env python3
"""Shared live-window helper for Issue #57 state-machine diagnostics.

Persistence/churn statistics should not treat the long indicator warm-up as a
real No-Regime episode. The live window begins at the first bar where the six
stage weights have a positive top weight (`top_value > 0`).
"""

from __future__ import annotations

from typing import Any

import numpy as np
import pandas as pd


def live_window(outputs: pd.DataFrame) -> tuple[pd.DataFrame, dict[str, Any]]:
    if "top_value" not in outputs.columns:
        raise ValueError("outputs must contain top_value")
    top = outputs["top_value"].to_numpy(float)
    valid = np.isfinite(top) & (top > 0.0)
    indices = np.flatnonzero(valid)
    if len(indices) == 0:
        raise ValueError("no live regime-weight bar found")
    start = int(indices[0])
    sliced = outputs.iloc[start:].copy().reset_index(drop=True)
    metadata: dict[str, Any] = {
        "live_start_index": start,
        "live_bars": len(sliced),
    }
    if "date" in outputs.columns:
        metadata["live_start_date"] = str(outputs.iloc[start]["date"])
        metadata["live_end_date"] = str(outputs.iloc[-1]["date"])
    return sliced, metadata
