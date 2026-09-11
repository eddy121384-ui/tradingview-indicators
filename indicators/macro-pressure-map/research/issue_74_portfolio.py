#!/usr/bin/env python3
"""Generic deterministic portfolio accounting for Issue #74.

The Issue #64 simulator was intentionally hard-coded to SPY/TLT/GLD. This
module preserves the same accounting semantics while supporting the
preregistered Issue #74 three- and four-asset universes without modifying #64.
"""
from __future__ import annotations

import math
from collections.abc import Sequence

import numpy as np
import pandas as pd


def validate_weights(weights: dict[str, float], assets: Sequence[str], name: str) -> None:
    expected = tuple(assets)
    if set(weights) != set(expected):
        raise ValueError(f"{name} must define exactly {expected}")
    values = np.asarray([float(weights[a]) for a in expected], dtype=float)
    if not np.isfinite(values).all() or (values < 0.0).any():
        raise ValueError(f"{name} contains invalid weights")
    if not np.isclose(values.sum(), 1.0, atol=1e-12):
        raise ValueError(f"{name} weights must sum to one")


def weights_series(weights: dict[str, float], index: pd.DatetimeIndex, assets: Sequence[str]) -> pd.DataFrame:
    validate_weights(weights, assets, "weights_series")
    row = [float(weights[a]) for a in assets]
    return pd.DataFrame(np.tile(row, (len(index), 1)), index=index, columns=list(assets))


def month_start_mask(index: pd.DatetimeIndex) -> pd.Series:
    periods = pd.Series(index.to_period("M"), index=index)
    return periods.ne(periods.shift(1)).astype(bool)


def template_change_mask(template: pd.Series) -> pd.Series:
    previous = template.shift(1)
    valid = template.notna() & previous.notna()
    sentinel = "__missing_template__"
    return (template.fillna(sentinel).ne(previous.fillna(sentinel)) & valid).astype(bool)


def build_core_regime_targets(
    regimes: pd.Series,
    *,
    assets: Sequence[str],
    neutral: dict[str, float],
    reflation: dict[str, float],
    stagflation: dict[str, float] | None,
    reflation_regime: str,
    stagflation_regime: str,
) -> tuple[pd.DataFrame, pd.Series]:
    """Choose today's template from yesterday's known core regime only."""
    assets = tuple(assets)
    validate_weights(neutral, assets, "neutral")
    validate_weights(reflation, assets, "reflation")
    if stagflation is not None:
        validate_weights(stagflation, assets, "stagflation")
    arrays = {
        "neutral": np.asarray([float(neutral[a]) for a in assets], dtype=float),
        "reflation": np.asarray([float(reflation[a]) for a in assets], dtype=float),
    }
    if stagflation is not None:
        arrays["stagflation"] = np.asarray([float(stagflation[a]) for a in assets], dtype=float)

    lagged = regimes.shift(1)
    data = np.tile(arrays["neutral"], (len(regimes), 1))
    template = pd.Series("neutral", index=regimes.index, dtype="object")
    mask_reflation = lagged.eq(reflation_regime).to_numpy()
    data[mask_reflation] = arrays["reflation"]
    template.loc[mask_reflation] = "reflation"
    if stagflation is not None:
        mask_stag = lagged.eq(stagflation_regime).to_numpy()
        data[mask_stag] = arrays["stagflation"]
        template.loc[mask_stag] = "stagflation"
    template.loc[lagged.isna()] = pd.NA
    return pd.DataFrame(data, index=regimes.index, columns=list(assets)), template


def build_severe_inflation_targets(
    regimes: pd.Series,
    raw_ipi: pd.Series,
    *,
    assets: Sequence[str],
    neutral: dict[str, float],
    reflation: dict[str, float],
    stagflation: dict[str, float],
    severe_stagflation: dict[str, float],
    reflation_regime: str,
    stagflation_regime: str,
    inflation_extreme_threshold: float,
) -> tuple[pd.DataFrame, pd.Series]:
    """Phase C target using lagged core regime AND lagged raw IPI threshold."""
    targets, template = build_core_regime_targets(
        regimes,
        assets=assets,
        neutral=neutral,
        reflation=reflation,
        stagflation=stagflation,
        reflation_regime=reflation_regime,
        stagflation_regime=stagflation_regime,
    )
    validate_weights(severe_stagflation, assets, "severe_stagflation")
    lagged_regime = regimes.shift(1)
    lagged_ipi = raw_ipi.shift(1)
    severe = lagged_regime.eq(stagflation_regime) & lagged_ipi.ge(float(inflation_extreme_threshold))
    override = np.asarray([float(severe_stagflation[a]) for a in assets], dtype=float)
    targets.loc[severe, list(assets)] = override
    template.loc[severe] = "severe_inflation_stagflation"
    template.loc[lagged_regime.isna() | lagged_ipi.isna()] = pd.NA
    return targets, template


def simulate_portfolio(
    returns: pd.DataFrame,
    targets: pd.DataFrame,
    rebalance_mask: pd.Series,
    *,
    cost_bps: float,
    name: str,
) -> pd.DataFrame:
    """Self-financing daily portfolio with drifted pre-trade turnover accounting."""
    assets = tuple(returns.columns)
    if not assets or list(targets.columns) != list(assets):
        raise ValueError("returns and targets must have identical non-empty asset columns")
    if not returns.index.equals(targets.index) or not returns.index.equals(rebalance_mask.index):
        raise ValueError("returns, targets and rebalance mask must share the exact index")
    if returns.empty:
        raise ValueError("cannot simulate an empty portfolio")
    if cost_bps < 0.0:
        raise ValueError("cost_bps must be non-negative")

    rows: list[dict] = []
    pretrade_weights: np.ndarray | None = None
    wealth = 1.0
    gross_counterfactual_wealth = 1.0

    for position, date in enumerate(returns.index):
        r = returns.loc[date, list(assets)].to_numpy(float)
        target = targets.loc[date, list(assets)].to_numpy(float)
        if not np.isfinite(r).all() or not np.isfinite(target).all():
            raise ValueError(f"non-finite simulation input on {date}")
        if (target < 0.0).any() or not np.isclose(target.sum(), 1.0, atol=1e-10):
            raise ValueError(f"invalid target weights on {date}")

        wealth_before = wealth
        trade = False
        turnover = 0.0
        cost_fraction = 0.0
        if position == 0:
            invested = target.copy()
        else:
            if pretrade_weights is None:
                raise RuntimeError("missing drifted pre-trade weights")
            invested = pretrade_weights.copy()
            if bool(rebalance_mask.loc[date]):
                trade = True
                turnover = float(0.5 * np.abs(target - invested).sum())
                cost_fraction = float(turnover * cost_bps / 10000.0)
                if cost_fraction >= 1.0:
                    raise ValueError("transaction cost consumes the portfolio")
                wealth *= 1.0 - cost_fraction
                invested = target.copy()

        gross_return = float(np.dot(invested, r))
        if 1.0 + gross_return <= 0.0:
            raise ValueError("portfolio return is <= -100%")
        wealth *= 1.0 + gross_return
        gross_counterfactual_wealth *= 1.0 + gross_return
        net_return = float(wealth / wealth_before - 1.0)
        post = invested * (1.0 + r) / (1.0 + gross_return)
        pretrade_weights = post

        row = {
            "date": date,
            "strategy": name,
            "net_return": net_return,
            "gross_asset_mix_return": gross_return,
            "wealth": wealth,
            "gross_counterfactual_wealth": gross_counterfactual_wealth,
            "trade": trade,
            "scheduled_or_event_rebalance": bool(rebalance_mask.loc[date]),
            "turnover": turnover,
            "cost_fraction": cost_fraction,
        }
        for asset, weight in zip(assets, invested):
            row[f"invested_weight_{asset}"] = float(weight)
        for asset, weight in zip(assets, post):
            row[f"end_weight_{asset}"] = float(weight)
        rows.append(row)
    return pd.DataFrame(rows).set_index("date")


def portfolio_metrics(sim: pd.DataFrame, *, annualization: int = 252) -> dict:
    if sim.empty:
        raise ValueError("cannot summarize empty simulation")
    r = sim["net_return"].to_numpy(float)
    n = len(r)
    ending = float(np.prod(1.0 + r))
    years = n / float(annualization)
    cagr = ending ** (1.0 / years) - 1.0 if years > 0.0 and ending > 0.0 else np.nan
    ann_return = float(np.mean(r) * annualization)
    ann_vol = float(np.std(r, ddof=1) * math.sqrt(annualization)) if n > 1 else np.nan
    sharpe = ann_return / ann_vol if np.isfinite(ann_vol) and ann_vol > 0.0 else np.nan
    wealth = np.concatenate(([1.0], np.cumprod(1.0 + r)))
    drawdown = wealth / np.maximum.accumulate(wealth) - 1.0
    max_drawdown = float(np.min(drawdown))
    calmar = cagr / abs(max_drawdown) if np.isfinite(cagr) and max_drawdown < 0.0 else np.nan
    total_turnover = float(sim["turnover"].sum())
    cost_drag = float(1.0 - np.prod(1.0 - sim["cost_fraction"].to_numpy(float)))
    result = {
        "observations": n,
        "CAGR": float(cagr),
        "annualized_return": ann_return,
        "annualized_volatility": ann_vol,
        "Sharpe": float(sharpe),
        "maximum_drawdown": max_drawdown,
        "Calmar": float(calmar),
        "total_turnover": total_turnover,
        "annualized_turnover": float(total_turnover / years) if years > 0.0 else np.nan,
        "rebalance_count": int(sim["trade"].sum()),
        "transaction_cost_drag": cost_drag,
        "ending_wealth": ending,
    }
    for column in sim.columns:
        if column.startswith("invested_weight_"):
            result[f"average_{column}"] = float(sim[column].mean())
    return result


def segment_sim(sim: pd.DataFrame, start: str | None, end: str | None) -> pd.DataFrame:
    result = sim
    if start is not None:
        result = result.loc[result.index >= pd.Timestamp(start)]
    if end is not None:
        result = result.loc[result.index <= pd.Timestamp(end)]
    return result.copy()


def summarize_strategies(simulations: dict[str, pd.DataFrame], *, annualization: int = 252) -> pd.DataFrame:
    segments = {
        "full_reused_history": (None, None),
        "development_pre2020": (None, "2019-12-31"),
        "post2019_reused_exploratory": ("2020-01-01", None),
    }
    rows: list[dict] = []
    for strategy, sim in simulations.items():
        for segment, (start, end) in segments.items():
            sub = segment_sim(sim, start, end)
            if sub.empty:
                continue
            rows.append({
                "strategy": strategy,
                "segment": segment,
                "first_date": sub.index.min().date().isoformat(),
                "last_date": sub.index.max().date().isoformat(),
                **portfolio_metrics(sub, annualization=annualization),
            })
    return pd.DataFrame(rows)


def compare_strategies(summary: pd.DataFrame, lhs: str, rhs: str, comparison: str) -> pd.DataFrame:
    metrics = ["CAGR", "annualized_return", "annualized_volatility", "Sharpe", "maximum_drawdown", "Calmar", "annualized_turnover", "transaction_cost_drag"]
    rows: list[dict] = []
    for segment in summary["segment"].unique():
        block = summary.loc[summary["segment"].eq(segment)].set_index("strategy")
        if lhs not in block.index or rhs not in block.index:
            continue
        row = {"comparison": comparison, "segment": segment, "lhs": lhs, "rhs": rhs}
        for metric in metrics:
            row[f"delta_{metric}"] = float(block.loc[lhs, metric] - block.loc[rhs, metric])
        rows.append(row)
    return pd.DataFrame(rows)
