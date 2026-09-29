#!/usr/bin/env python3
"""Issue #113 — sparse state-only Action Layer production sizing gate.

Runs only against hash-frozen repository inputs. No live data.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
from pathlib import Path

import numpy as np
import pandas as pd

from issue_64_outcome_snapshot import load_frozen_prices

HERE = Path(__file__).resolve().parent
DATA = HERE / "data"

TRANSITIONS = DATA / "issue-64-frozen-regime-transitions.csv"
SHV_GSG = DATA / "issue-109-shv-gsg-adjusted-prices.csv"

EXPECTED_TRANSITION_SHA = "80446bbcb91be8b18eb0b95e62466edf892e4c04087696a04532f0fe214698af"
EXPECTED_OLD_PRICE_SHA = "3a7f590c146f9eda5920b6968fe86c9c3cc1887db35597f2d639a1c76b6e5a57"
EXPECTED_NEW_PRICE_SHA = "7dbfe3cff58be172098aa09b9c86fd70a23672834f5829e4b650c94cf72d6833"
SIGNAL_CUTOFF = pd.Timestamp("2026-08-14")

ASSETS = ("SPY", "TLT", "GLD", "SHV")
BASE_WEIGHTS = np.array([0.40, 0.40, 0.10, 0.10], dtype=float)
PRIMARY_COST_BPS = 5.0
DIAGNOSTIC_COST_BPS = (0.0, 10.0)

TARGETS = {
    7: np.array([0.40, 0.40, 0.15, 0.05], dtype=float),
    8: np.array([0.45, 0.35, 0.15, 0.05], dtype=float),
    9: np.array([0.40, 0.40, 0.15, 0.05], dtype=float),
}

REGIME_NAMES = {
    1: "Goldilocks / Disinflationary Expansion",
    2: "Benign Expansion / Stable Inflation",
    3: "Reflation / Inflation Rising",
    4: "Disinflationary Drift",
    5: "Neutral / Range-bound Macro",
    6: "Inflation Pressure without Growth Confirmation",
    7: "Slowdown / Disinflation",
    8: "Growth Slowdown / Stable Inflation",
    9: "Stagflation Pressure",
}


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def load_sources() -> tuple[pd.DataFrame, pd.DataFrame, dict]:
    if sha256_file(TRANSITIONS) != EXPECTED_TRANSITION_SHA:
        raise RuntimeError("Issue #64 transition hash mismatch")
    if sha256_file(SHV_GSG) != EXPECTED_NEW_PRICE_SHA:
        raise RuntimeError("Issue #109 SHV/GSG hash mismatch")

    old, old_meta = load_frozen_prices("2007-01-01", None)
    if old_meta["snapshot_csv_sha256"] != EXPECTED_OLD_PRICE_SHA:
        raise RuntimeError("Issue #64 SPY/TLT/GLD hash mismatch")

    shv = pd.read_csv(SHV_GSG)
    shv["date"] = pd.to_datetime(shv["date"], errors="raise")
    shv = shv.set_index("date").sort_index()[["SHV"]]
    shv["SHV"] = pd.to_numeric(shv["SHV"], errors="raise").astype(float)

    panel = pd.concat([old[["SPY", "TLT", "GLD"]], shv], axis=1, join="inner").dropna()
    panel = panel.loc[:, list(ASSETS)].sort_index()
    if panel.empty or panel.index.duplicated().any():
        raise RuntimeError("invalid common SPY/TLT/GLD/SHV panel")
    if not np.isfinite(panel.to_numpy(float)).all() or (panel.to_numpy(float) <= 0).any():
        raise RuntimeError("non-finite/negative prices in common panel")

    transitions = pd.read_csv(TRANSITIONS)
    transitions["start_date"] = pd.to_datetime(transitions["start_date"], errors="raise")
    transitions["regime_id"] = pd.to_numeric(transitions["regime_id"], errors="raise").astype(int)
    transitions = transitions.sort_values("start_date").reset_index(drop=True)

    meta = {
        "old_prices": old_meta,
        "shv_gsg_sha256": EXPECTED_NEW_PRICE_SHA,
        "transition_sha256": EXPECTED_TRANSITION_SHA,
        "common_rows": int(len(panel)),
        "common_first_date": panel.index.min().date().isoformat(),
        "common_last_date": panel.index.max().date().isoformat(),
    }
    return panel, transitions, meta


def state_on_date(transitions: pd.DataFrame, date: pd.Timestamp) -> int | None:
    if date > SIGNAL_CUTOFF:
        return None
    starts = transitions["start_date"].to_numpy(dtype="datetime64[ns]")
    pos = int(np.searchsorted(starts, np.datetime64(date), side="right") - 1)
    if pos < 0:
        return None
    rid = int(transitions.iloc[pos]["regime_id"])
    if rid < 1 or rid > 9:
        raise RuntimeError(f"invalid regime id {rid}")
    return rid


def first_rows_each_month(index: pd.DatetimeIndex) -> list[int]:
    periods = index.to_period("M")
    out: list[int] = []
    last = None
    for i, p in enumerate(periods):
        if p != last:
            out.append(i)
            last = p
    return out


def target_for_regime(regime_id: int) -> np.ndarray:
    return TARGETS.get(int(regime_id), BASE_WEIGHTS).copy()


def segment_for_origin(ts: pd.Timestamp) -> str:
    if ts < pd.Timestamp("2020-01-01"):
        return "pre_2020"
    if ts <= pd.Timestamp("2022-12-31"):
        return "covid_inflation_2020_2022"
    return "post_2023"


def build_monthly_rows(panel: pd.DataFrame, transitions: pd.DataFrame) -> pd.DataFrame:
    starts = first_rows_each_month(panel.index)
    rows: list[dict] = []

    for j in range(len(starts) - 1):
        pos = starts[j]
        next_pos = starts[j + 1]
        if pos <= 0:
            continue
        origin = pd.Timestamp(panel.index[pos])
        signal_date = pd.Timestamp(panel.index[pos - 1])
        end_date = pd.Timestamp(panel.index[next_pos])
        rid = state_on_date(transitions, signal_date)
        if rid is None:
            continue

        r = panel.iloc[next_pos].to_numpy(float) / panel.iloc[pos].to_numpy(float) - 1.0
        w = target_for_regime(rid)

        row = {
            "origin_date": origin,
            "signal_date": signal_date,
            "end_date": end_date,
            "regime_id": rid,
            "regime": REGIME_NAMES[rid],
            "segment": segment_for_origin(origin),
        }
        for asset, ret in zip(ASSETS, r, strict=True):
            row[f"{asset}_return"] = float(ret)
        for asset, weight in zip(ASSETS, w, strict=True):
            row[f"w_{asset}"] = float(weight)
        rows.append(row)

    out = pd.DataFrame(rows).sort_values("origin_date").reset_index(drop=True)
    if out.empty:
        raise RuntimeError("no eligible monthly portfolio rows")
    return out


def recompute_action_returns(rows: pd.DataFrame, cost_bps: float) -> pd.DataFrame:
    g = rows.copy().sort_values("origin_date").reset_index(drop=True)
    weight_cols = [f"w_{a}" for a in ASSETS]
    ret_cols = [f"{a}_return" for a in ASSETS]

    weights = g[weight_cols].to_numpy(float)
    asset_rets = g[ret_cols].to_numpy(float)
    gross = np.sum(weights * asset_rets, axis=1)

    turnover = np.zeros(len(g), dtype=float)
    if len(g) > 1:
        turnover[1:] = 0.5 * np.sum(np.abs(weights[1:] - weights[:-1]), axis=1)

    cost = turnover * (float(cost_bps) / 10_000.0)
    g["turnover"] = turnover
    g["tactical_cost"] = cost
    g["al_gross_return"] = gross
    g["al_net_return"] = gross - cost
    g["c0_return"] = asset_rets @ BASE_WEIGHTS
    g["shv_return"] = g["SHV_return"].astype(float)

    g["equity_duration_sleeve"] = np.where(
        g["regime_id"].eq(8),
        0.05 * (g["SPY_return"] - g["TLT_return"]),
        0.0,
    )
    g["gold_cash_sleeve"] = np.where(
        g["regime_id"].isin([7, 8, 9]),
        0.05 * (g["GLD_return"] - g["SHV_return"]),
        0.0,
    )
    return g


def portfolio_metrics(
    returns: np.ndarray,
    shv_returns: np.ndarray,
    *,
    turnover: np.ndarray | None = None,
    tactical_cost: np.ndarray | None = None,
    gross_returns: np.ndarray | None = None,
) -> dict:
    r = np.asarray(returns, dtype=float)
    cash = np.asarray(shv_returns, dtype=float)
    mask = np.isfinite(r) & np.isfinite(cash)
    r = r[mask]
    cash = cash[mask]
    n = len(r)
    if n == 0:
        return {"n": 0}

    wealth = np.cumprod(1.0 + r)
    years = n / 12.0
    cagr = float(wealth[-1] ** (1.0 / years) - 1.0) if wealth[-1] > 0 else math.nan
    vol = float(np.std(r, ddof=1) * np.sqrt(12.0)) if n >= 2 else math.nan
    excess = r - cash
    ex_std = float(np.std(excess, ddof=1)) if n >= 2 else math.nan
    sharpe = float(np.mean(excess) / ex_std * np.sqrt(12.0)) if ex_std and ex_std > 0 else math.nan

    running = np.maximum.accumulate(wealth)
    dd = wealth / running - 1.0
    max_dd = float(np.min(dd))
    calmar = float(cagr / abs(max_dd)) if max_dd < 0 and np.isfinite(cagr) else math.nan

    out = {
        "n": int(n),
        "cagr": cagr,
        "annualized_vol": vol,
        "sharpe_excess_shv": sharpe,
        "max_drawdown": max_dd,
        "calmar": calmar,
        "terminal_wealth": float(wealth[-1]),
    }

    if turnover is not None:
        t = np.asarray(turnover, dtype=float)[mask]
        out["annualized_tactical_turnover"] = float(np.mean(t) * 12.0)
    if tactical_cost is not None:
        c = np.asarray(tactical_cost, dtype=float)[mask]
        out["total_tactical_cost"] = float(np.sum(c))
    if gross_returns is not None:
        gr = np.asarray(gross_returns, dtype=float)[mask]
        gross_wealth = np.cumprod(1.0 + gr)
        gross_cagr = float(gross_wealth[-1] ** (1.0 / years) - 1.0)
        out["gross_cagr"] = gross_cagr
        out["annualized_cost_drag"] = float(gross_cagr - cagr)
    return out


def evaluate_static(rows: pd.DataFrame, weights: np.ndarray) -> dict:
    asset_rets = rows[[f"{a}_return" for a in ASSETS]].to_numpy(float)
    r = asset_rets @ weights
    return portfolio_metrics(r, rows["SHV_return"].to_numpy(float))


def evaluate_action(rows: pd.DataFrame) -> dict:
    return portfolio_metrics(
        rows["al_net_return"].to_numpy(float),
        rows["shv_return"].to_numpy(float),
        turnover=rows["turnover"].to_numpy(float),
        tactical_cost=rows["tactical_cost"].to_numpy(float),
        gross_returns=rows["al_gross_return"].to_numpy(float),
    )


def target_key(row: pd.Series) -> tuple[float, ...]:
    return tuple(round(float(row[f"w_{a}"]), 8) for a in ASSETS)


def identify_active_episodes(rows: pd.DataFrame) -> pd.DataFrame:
    g = rows.sort_values("origin_date").reset_index(drop=True)
    base_key = tuple(BASE_WEIGHTS.tolist())
    episodes: list[dict] = []

    current: list[int] = []
    current_key: tuple[float, ...] | None = None
    current_last_period: pd.Period | None = None
    eid = 0

    def flush() -> None:
        nonlocal current, current_key, current_last_period, eid
        if not current:
            return
        eid += 1
        ep = g.loc[current]
        contribution = float((ep["al_net_return"] - ep["c0_return"]).sum())
        episodes.append({
            "episode_id": eid,
            "target_key": "/".join(f"{x:.2f}" for x in current_key or ()),
            "start_origin": ep["origin_date"].min().date().isoformat(),
            "end_origin": ep["origin_date"].max().date().isoformat(),
            "months": int(len(ep)),
            "contribution_sum": contribution,
        })
        current = []
        current_key = None
        current_last_period = None

    for i, row in g.iterrows():
        key = target_key(row)
        period = pd.Timestamp(row["origin_date"]).to_period("M")
        active = key != base_key
        consecutive = current_last_period is not None and period.ordinal == current_last_period.ordinal + 1

        if not active:
            flush()
            continue

        if current and (key != current_key or not consecutive):
            flush()

        if not current:
            current_key = key
        current.append(i)
        current_last_period = period

    flush()
    if not episodes:
        return pd.DataFrame(columns=["episode_id","target_key","start_origin","end_origin","months","contribution_sum"])
    return pd.DataFrame(episodes).sort_values("episode_id").reset_index(drop=True)


def leaveout_strongest_episode(rows: pd.DataFrame, episodes: pd.DataFrame, cost_bps: float) -> tuple[pd.DataFrame, dict]:
    positive = episodes.loc[episodes["contribution_sum"] > 0].copy()
    if positive.empty:
        return rows.copy(), {
            "episode_id": None,
            "top_positive_share": math.nan,
            "positive_contribution_total": 0.0,
        }

    strongest = positive.sort_values("contribution_sum", ascending=False).iloc[0]
    total_positive = float(positive["contribution_sum"].sum())
    top_share = float(strongest["contribution_sum"] / total_positive) if total_positive > 0 else math.nan

    start = pd.Timestamp(strongest["start_origin"])
    end = pd.Timestamp(strongest["end_origin"])
    modified = rows.copy()
    mask = (modified["origin_date"] >= start) & (modified["origin_date"] <= end)
    for asset, weight in zip(ASSETS, BASE_WEIGHTS, strict=True):
        modified.loc[mask, f"w_{asset}"] = float(weight)
    modified = recompute_action_returns(modified, cost_bps)

    meta = {
        "episode_id": int(strongest["episode_id"]),
        "start_origin": strongest["start_origin"],
        "end_origin": strongest["end_origin"],
        "months": int(strongest["months"]),
        "contribution_sum": float(strongest["contribution_sum"]),
        "positive_contribution_total": total_positive,
        "top_positive_share": top_share,
    }
    return modified, meta


def metric_diff(a: dict, b: dict) -> dict:
    keys = ["cagr", "sharpe_excess_shv", "max_drawdown", "terminal_wealth"]
    return {k: float(a[k] - b[k]) for k in keys}


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--output-dir", type=Path, required=True)
    args = ap.parse_args()
    out = args.output_dir
    out.mkdir(parents=True, exist_ok=True)

    panel, transitions, provenance = load_sources()
    raw_rows = build_monthly_rows(panel, transitions)
    rows = recompute_action_returns(raw_rows, PRIMARY_COST_BPS)

    avg_weights = rows[[f"w_{a}" for a in ASSETS]].mean(axis=0).to_numpy(float)
    if not np.isclose(avg_weights.sum(), 1.0, atol=1e-12):
        raise RuntimeError("C1 average weights do not sum to one")

    c0_full = evaluate_static(rows, BASE_WEIGHTS)
    c1_full = evaluate_static(rows, avg_weights)
    al_full = evaluate_action(rows)

    segments: dict[str, dict] = {}
    for seg in ("pre_2020", "covid_inflation_2020_2022", "post_2023"):
        sg = rows.loc[rows["segment"].eq(seg)].copy()
        segments[seg] = {
            "action": evaluate_action(sg),
            "c0": evaluate_static(sg, BASE_WEIGHTS),
            "c1": evaluate_static(sg, avg_weights),
        }
        segments[seg]["action_minus_c0"] = metric_diff(segments[seg]["action"], segments[seg]["c0"])

    episodes = identify_active_episodes(rows)
    leave_rows, strongest = leaveout_strongest_episode(raw_rows, episodes, PRIMARY_COST_BPS)
    leave_metrics = evaluate_action(leave_rows)
    leave_cagr_adv = float(leave_metrics["cagr"] - c0_full["cagr"])

    diagnostics = {}
    for bps in DIAGNOSTIC_COST_BPS:
        dg = recompute_action_returns(raw_rows, bps)
        diagnostics[f"{int(bps)}bps"] = evaluate_action(dg)

    sleeve = {
        "equity_duration_sum": float(rows["equity_duration_sleeve"].sum()),
        "equity_duration_annualized_mean": float(rows["equity_duration_sleeve"].mean() * 12.0),
        "gold_cash_sum": float(rows["gold_cash_sleeve"].sum()),
        "gold_cash_annualized_mean": float(rows["gold_cash_sleeve"].mean() * 12.0),
        "total_tactical_cost": float(rows["tactical_cost"].sum()),
    }

    cagr_adv = float(al_full["cagr"] - c0_full["cagr"])
    sharpe_adv = float(al_full["sharpe_excess_shv"] - c0_full["sharpe_excess_shv"])
    maxdd_diff = float(al_full["max_drawdown"] - c0_full["max_drawdown"])
    seg_cagr_adv = {
        seg: float(item["action"]["cagr"] - item["c0"]["cagr"])
        for seg, item in segments.items()
    }

    gate = {
        "1_full_cagr_adv_ge_25bp": cagr_adv >= 0.0025,
        "2_full_sharpe_adv_ge_005": sharpe_adv >= 0.05,
        "3_maxdd_not_worse_by_gt_15pp": maxdd_diff >= -0.015,
        "4_at_least_2_of_3_segments_positive": sum(v > 0 for v in seg_cagr_adv.values()) >= 2,
        "5_no_segment_below_minus_50bp": min(seg_cagr_adv.values()) >= -0.005,
        "6_strongest_episode_leaveout_positive": leave_cagr_adv > 0,
        "7_beats_c1_on_cagr_and_sharpe": (
            al_full["cagr"] > c1_full["cagr"]
            and al_full["sharpe_excess_shv"] > c1_full["sharpe_excess_shv"]
        ),
    }

    insufficient = any(segments[s]["action"]["n"] < 24 for s in segments)
    if insufficient:
        verdict = "inconclusive_insufficient_sample"
    elif all(gate.values()):
        verdict = "production_action_layer_candidate"
    elif cagr_adv > 0:
        verdict = "economically_positive_but_not_robust_enough"
    else:
        verdict = "no_material_production_value"

    serial = rows.copy()
    for c in ("origin_date", "signal_date", "end_date"):
        serial[c] = pd.to_datetime(serial[c]).dt.strftime("%Y-%m-%d")
    rows_path = out / "issue-113-monthly-portfolio.csv"
    serial.to_csv(rows_path, index=False, float_format="%.12g")

    episodes_path = out / "issue-113-active-episodes.csv"
    episodes.to_csv(episodes_path, index=False, float_format="%.12g")

    result = {
        "schema_version": 1,
        "issue": 113,
        "phase": "production-action-layer-sizing-gate",
        "verdict": verdict,
        "primary_cost_bps": PRIMARY_COST_BPS,
        "base_weights": dict(zip(ASSETS, BASE_WEIGHTS.tolist(), strict=True)),
        "c1_average_weights": dict(zip(ASSETS, avg_weights.tolist(), strict=True)),
        "full": {
            "action": al_full,
            "c0": c0_full,
            "c1": c1_full,
            "action_minus_c0": metric_diff(al_full, c0_full),
            "cagr_advantage": cagr_adv,
            "sharpe_advantage": sharpe_adv,
            "maxdd_difference": maxdd_diff,
        },
        "segments": segments,
        "segment_cagr_advantage": seg_cagr_adv,
        "episode_robustness": {
            "strongest_positive_episode": strongest,
            "leaveout_action": leave_metrics,
            "leaveout_cagr_advantage": leave_cagr_adv,
        },
        "sleeve_attribution": sleeve,
        "cost_diagnostics": diagnostics,
        "production_gate": gate,
        "production_gate_pass_count": int(sum(bool(v) for v in gate.values())),
        "source_provenance": provenance,
        "rows": {
            "monthly_completed": int(len(rows)),
            "first_origin": rows["origin_date"].min().date().isoformat(),
            "last_origin": rows["origin_date"].max().date().isoformat(),
            "active_months": int((rows[[f"w_{a}" for a in ASSETS]].to_numpy(float) != BASE_WEIGHTS).any(axis=1).sum()),
            "episode_count": int(len(episodes)),
        },
        "output_hashes": {
            "monthly_portfolio_csv_sha256": sha256_file(rows_path),
            "active_episodes_csv_sha256": sha256_file(episodes_path),
        },
        "production_authorized": verdict == "production_action_layer_candidate",
    }

    result_path = out / "issue-113-result.json"
    result_path.write_text(json.dumps(result, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps({
        "verdict": verdict,
        "gate": gate,
        "full": {
            "cagr_advantage": cagr_adv,
            "sharpe_advantage": sharpe_adv,
            "maxdd_difference": maxdd_diff,
        },
        "segment_cagr_advantage": seg_cagr_adv,
        "leaveout_cagr_advantage": leave_cagr_adv,
        "output": str(result_path),
    }, indent=2))


if __name__ == "__main__":
    main()
