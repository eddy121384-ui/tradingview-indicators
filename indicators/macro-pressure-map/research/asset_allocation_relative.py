"""Pairwise relative-return diagnostics for Issue #64 Phase A."""
from __future__ import annotations

import numpy as np
import pandas as pd

from asset_allocation_phase_a import (
    HORIZONS,
    REGIMES,
    _stable_seed,
    bootstrap_mean_ci,
    embargo_positions,
    forward_returns,
)

PAIRS = (("SPY", "TLT"), ("SPY", "GLD"), ("TLT", "GLD"))


def summarize_relative_returns(history: pd.DataFrame, prices: pd.DataFrame) -> pd.DataFrame:
    """Compare paired forward returns directly inside each frozen regime.

    `return_spread` is asset_a total return minus asset_b total return from the
    same start date. Positive values mean asset_a outperformed asset_b.
    Confidence intervals are bootstrapped from horizon-embargoed starts within
    the regime, not inferred by comparing two standalone asset intervals.
    """
    rows: list[dict] = []
    regimes = history["core_regime"]
    for horizon_name, horizon in HORIZONS.items():
        fwd = forward_returns(prices, horizon)
        for regime in REGIMES:
            regime_mask = regimes.eq(regime).to_numpy()
            for asset_a, asset_b in PAIRS:
                spread = (fwd[asset_a] - fwd[asset_b]).to_numpy(float)
                eligible = regime_mask & np.isfinite(spread)
                all_values = spread[eligible]
                selected = embargo_positions(np.flatnonzero(eligible), horizon)
                embargoed = np.asarray([spread[pos] for pos in selected], dtype=float)
                ci_low, ci_high = bootstrap_mean_ci(
                    embargoed,
                    seed=_stable_seed("issue64-relative", regime, horizon_name, asset_a, asset_b),
                )
                rows.append({
                    "regime": regime,
                    "horizon": horizon_name,
                    "horizon_rows": horizon,
                    "asset_a": asset_a,
                    "asset_b": asset_b,
                    "spread_definition": "total_return_a_minus_total_return_b",
                    "observations_all": int(all_values.size),
                    "mean_return_spread": float(np.mean(all_values)) if all_values.size else np.nan,
                    "median_return_spread": float(np.median(all_values)) if all_values.size else np.nan,
                    "asset_a_outperformance_rate": (
                        float(np.mean(all_values > 0.0)) if all_values.size else np.nan
                    ),
                    "embargoed_observations": int(embargoed.size),
                    "embargoed_mean_return_spread": (
                        float(np.mean(embargoed)) if embargoed.size else np.nan
                    ),
                    "mean_spread_ci95_low": ci_low,
                    "mean_spread_ci95_high": ci_high,
                    "ci_excludes_zero": bool(
                        np.isfinite(ci_low) and np.isfinite(ci_high) and (ci_low > 0.0 or ci_high < 0.0)
                    ),
                })
    return pd.DataFrame(rows)
