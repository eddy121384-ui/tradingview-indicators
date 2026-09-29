#!/usr/bin/env python3
"""Issue #127 — exact V6.6 Reflation modern translation gate.

Uses only hash-frozen modern evidence. No live data.
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
BASE = np.array([0.40, 0.40, 0.10, 0.10], dtype=float)
ACTIVE = np.array([0.45, 0.35, 0.10, 0.10], dtype=float)
PRIMARY_COST_BPS = 5.0
ACTIVE_REGIME = 3


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def load_sources() -> tuple[pd.DataFrame, pd.DataFrame, dict]:
    if sha256_file(TRANSITIONS) != EXPECTED_TRANSITION_SHA:
        raise RuntimeError("transition hash mismatch")
    if sha256_file(SHV_GSG) != EXPECTED_NEW_PRICE_SHA:
        raise RuntimeError("SHV/GSG hash mismatch")

    old, old_meta = load_frozen_prices("2007-01-01", None)
    if old_meta["snapshot_csv_sha256"] != EXPECTED_OLD_PRICE_SHA:
        raise RuntimeError("SPY/TLT/GLD snapshot hash mismatch")

    shv = pd.read_csv(SHV_GSG)
    shv["date"] = pd.to_datetime(shv["date"], errors="raise")
    shv = shv.set_index("date").sort_index()[["SHV"]]
    shv["SHV"] = pd.to_numeric(shv["SHV"], errors="raise").astype(float)

    panel = pd.concat([old[["SPY", "TLT", "GLD"]], shv], axis=1, join="inner").dropna()
    panel = panel.loc[:, list(ASSETS)].sort_index()
    if panel.empty or panel.index.duplicated().any():
        raise RuntimeError("invalid common panel")
    if not np.isfinite(panel.to_numpy(float)).all() or (panel.to_numpy(float) <= 0).any():
        raise RuntimeError("invalid common prices")

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
        raise RuntimeError(f"invalid regime {rid}")
    return rid


def first_rows_each_month(index: pd.DatetimeIndex) -> list[int]:
    periods = index.to_period("M")
    out = []
    last = None
    for i, p in enumerate(periods):
        if p != last:
            out.append(i)
            last = p
    return out


def segment_for_origin(ts: pd.Timestamp) -> str:
    if ts < pd.Timestamp("2020-01-01"):
        return "pre_2020"
    if ts <= pd.Timestamp("2022-12-31"):
        return "covid_inflation_2020_2022"
    return "post_2023"


def target_for_regime(regime_id: int) -> np.ndarray:
    return ACTIVE.copy() if int(regime_id) == ACTIVE_REGIME else BASE.copy()


def build_rows(panel: pd.DataFrame, transitions: pd.DataFrame) -> pd.DataFrame:
    starts = first_rows_each_month(panel.index)
    rows = []
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

        asset_rets = panel.iloc[next_pos].to_numpy(float) / panel.iloc[pos].to_numpy(float) - 1.0
        w = target_for_regime(rid)

        row = {
            "origin_date": origin,
            "signal_date": signal_date,
            "end_date": end_date,
            "regime_id": rid,
            "active": bool(rid == ACTIVE_REGIME),
            "segment": segment_for_origin(origin),
        }
        for asset, ret in zip(ASSETS, asset_rets, strict=True):
            row[f"{asset}_return"] = float(ret)
        for asset, weight in zip(ASSETS, w, strict=True):
            row[f"w_{asset}"] = float(weight)
        rows.append(row)

    out = pd.DataFrame(rows).sort_values("origin_date").reset_index(drop=True)
    if out.empty:
        raise RuntimeError("no eligible monthly rows")
    return out


def apply_returns(rows: pd.DataFrame) -> pd.DataFrame:
    g = rows.copy().sort_values("origin_date").reset_index(drop=True)
    weight_cols = [f"w_{a}" for a in ASSETS]
    ret_cols = [f"{a}_return" for a in ASSETS]
    weights = g[weight_cols].to_numpy(float)
    rets = g[ret_cols].to_numpy(float)

    turnover = np.zeros(len(g), dtype=float)
    if len(g) > 1:
        turnover[1:] = 0.5 * np.abs(weights[1:] - weights[:-1]).sum(axis=1)
    cost = turnover * (PRIMARY_COST_BPS / 10_000.0)

    gross = np.sum(weights * rets, axis=1)
    g["turnover"] = turnover
    g["tactical_cost"] = cost
    g["action_gross_return"] = gross
    g["action_net_return"] = gross - cost
    g["c0_return"] = rets @ BASE
    g["shv_return"] = g["SHV_return"].astype(float)
    g["gross_sleeve_contribution"] = np.where(
        g["active"],
        0.05 * (g["SPY_return"] - g["TLT_return"]),
        0.0,
    )
    return g


def portfolio_metrics(
    returns: np.ndarray | pd.Series,
    shv: np.ndarray | pd.Series,
    *,
    turnover: np.ndarray | None = None,
    cost: np.ndarray | None = None,
    gross: np.ndarray | None = None,
) -> dict:
    r = np.asarray(returns, dtype=float)
    cash = np.asarray(shv, dtype=float)
    mask = np.isfinite(r) & np.isfinite(cash)
    r = r[mask]
    cash = cash[mask]
    n = int(len(r))
    if n == 0:
        raise RuntimeError("empty metric sample")

    wealth = np.cumprod(1.0 + r)
    years = n / 12.0
    cagr = float(wealth[-1] ** (1.0 / years) - 1.0)
    vol = float(np.std(r, ddof=1) * np.sqrt(12.0)) if n >= 2 else math.nan
    excess = r - cash
    ex_sd = float(np.std(excess, ddof=1)) if n >= 2 else math.nan
    sharpe = float(np.mean(excess) / ex_sd * np.sqrt(12.0)) if np.isfinite(ex_sd) and ex_sd > 0 else math.nan

    running = np.maximum.accumulate(wealth)
    dd = wealth / running - 1.0
    maxdd = float(np.min(dd))
    calmar = float(cagr / abs(maxdd)) if maxdd < 0 else math.nan

    out = {
        "n": n,
        "cagr": cagr,
        "annualized_volatility": vol,
        "sharpe_excess_shv": sharpe,
        "max_drawdown": maxdd,
        "calmar": calmar,
        "terminal_wealth": float(wealth[-1]),
    }
    if turnover is not None:
        t = np.asarray(turnover, dtype=float)[mask]
        out["annualized_tactical_turnover"] = float(np.mean(t) * 12.0)
    if cost is not None:
        c = np.asarray(cost, dtype=float)[mask]
        out["cumulative_tactical_cost"] = float(np.sum(c))
    if gross is not None:
        gr = np.asarray(gross, dtype=float)[mask]
        gross_wealth = np.cumprod(1.0 + gr)
        gross_cagr = float(gross_wealth[-1] ** (1.0 / years) - 1.0)
        out["gross_cagr"] = gross_cagr
        out["annualized_cost_drag"] = float(gross_cagr - cagr)
    return out


def evaluate_action(rows: pd.DataFrame) -> dict:
    return portfolio_metrics(
        rows["action_net_return"],
        rows["shv_return"],
        turnover=rows["turnover"].to_numpy(float),
        cost=rows["tactical_cost"].to_numpy(float),
        gross=rows["action_gross_return"].to_numpy(float),
    )


def evaluate_static(rows: pd.DataFrame, weights: np.ndarray) -> dict:
    rets = rows[[f"{a}_return" for a in ASSETS]].to_numpy(float)
    return portfolio_metrics(rets @ weights, rows["SHV_return"])


def diff(a: dict, b: dict) -> dict:
    return {
        "cagr": float(a["cagr"] - b["cagr"]),
        "sharpe": float(a["sharpe_excess_shv"] - b["sharpe_excess_shv"]),
        "max_drawdown": float(a["max_drawdown"] - b["max_drawdown"]),
        "terminal_wealth": float(a["terminal_wealth"] - b["terminal_wealth"]),
    }


def identify_episodes(rows: pd.DataFrame) -> pd.DataFrame:
    g = rows.sort_values("origin_date").reset_index(drop=True)
    episodes = []
    current = []
    last_period = None

    def flush() -> None:
        nonlocal current, last_period
        if not current:
            return
        ep = g.loc[current]
        episodes.append({
            "episode_id": len(episodes) + 1,
            "start_origin": ep["origin_date"].min().date().isoformat(),
            "end_origin": ep["origin_date"].max().date().isoformat(),
            "months": int(len(ep)),
            "gross_contribution": float(ep["gross_sleeve_contribution"].sum()),
        })
        current = []
        last_period = None

    for i, row in g.iterrows():
        if not bool(row["active"]):
            flush()
            continue
        p = pd.Timestamp(row["origin_date"]).to_period("M")
        if current and last_period is not None and p.ordinal != last_period.ordinal + 1:
            flush()
        current.append(i)
        last_period = p
    flush()
    if not episodes:
        return pd.DataFrame(columns=["episode_id","start_origin","end_origin","months","gross_contribution"])
    return pd.DataFrame(episodes)


def revert_episode(raw: pd.DataFrame, start: str, end: str) -> pd.DataFrame:
    g = raw.copy()
    s = pd.Timestamp(start)
    e = pd.Timestamp(end)
    mask = (g["origin_date"] >= s) & (g["origin_date"] <= e)
    for asset, weight in zip(ASSETS, BASE, strict=True):
        g.loc[mask, f"w_{asset}"] = float(weight)
    g.loc[mask, "active"] = False
    return apply_returns(g)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--output-dir", type=Path, required=True)
    args = ap.parse_args()
    out = args.output_dir
    out.mkdir(parents=True, exist_ok=True)

    panel, transitions, provenance = load_sources()
    raw = build_rows(panel, transitions)
    rows = apply_returns(raw)

    avg_weights = rows[[f"w_{a}" for a in ASSETS]].mean().to_numpy(float)
    if not np.isclose(avg_weights.sum(), 1.0, atol=1e-12):
        raise RuntimeError("C1 weights do not sum to one")

    action = evaluate_action(rows)
    c0 = evaluate_static(rows, BASE)
    c1 = evaluate_static(rows, avg_weights)

    segments = {}
    evaluable_segments = []
    positive_segments = []
    for label in ("pre_2020", "covid_inflation_2020_2022", "post_2023"):
        sg = rows.loc[rows["segment"].eq(label)].copy()
        am = int(sg["active"].sum())
        a = evaluate_action(sg)
        b = evaluate_static(sg, BASE)
        c = evaluate_static(sg, avg_weights)
        d = diff(a, b)
        evaluable = am >= 3
        if evaluable:
            evaluable_segments.append(label)
            if d["cagr"] > 0:
                positive_segments.append(label)
        segments[label] = {
            "active_months": am,
            "evaluable": evaluable,
            "action": a,
            "c0": b,
            "c1": c,
            "action_minus_c0": d,
        }

    episodes = identify_episodes(rows)
    positive_eps = episodes.loc[episodes["gross_contribution"] > 0].copy()
    if positive_eps.empty:
        strongest = None
        positive_total = 0.0
        top_share = math.nan
        leaveout = None
        leaveout_adv = math.nan
    else:
        sr = positive_eps.sort_values("gross_contribution", ascending=False).iloc[0]
        positive_total = float(positive_eps["gross_contribution"].sum())
        top_share = float(sr["gross_contribution"] / positive_total)
        strongest = {
            "episode_id": int(sr["episode_id"]),
            "start_origin": str(sr["start_origin"]),
            "end_origin": str(sr["end_origin"]),
            "months": int(sr["months"]),
            "gross_contribution": float(sr["gross_contribution"]),
        }
        leave_rows = revert_episode(raw, strongest["start_origin"], strongest["end_origin"])
        leaveout = evaluate_action(leave_rows)
        leaveout_adv = float(leaveout["cagr"] - c0["cagr"])

    active_months = int(rows["active"].sum())
    episode_count = int(len(episodes))
    full_diff = diff(action, c0)
    c1_diff = diff(action, c1)
    eval_adv = [
        segments[label]["action_minus_c0"]["cagr"]
        for label in evaluable_segments
    ]

    gate = {
        "1_action_cagr_gt_c0": full_diff["cagr"] > 0,
        "2_action_sharpe_gt_c0": full_diff["sharpe"] > 0,
        "3_maxdd_difference_ge_minus_1pp": full_diff["max_drawdown"] >= -0.010,
        "4_active_months_ge_12": active_months >= 12,
        "5_active_episodes_ge_5": episode_count >= 5,
        "6_evaluable_segments_ge_2": len(evaluable_segments) >= 2,
        "7_at_least_2_evaluable_segments_positive": len(positive_segments) >= 2,
        "8_no_evaluable_segment_below_minus_25bp": (
            len(eval_adv) > 0 and min(eval_adv) >= -0.0025
        ),
        "9_strongest_episode_leaveout_positive": (
            leaveout is not None and leaveout_adv > 0
        ),
        "10_top_positive_episode_share_le_50pct": (
            np.isfinite(top_share) and top_share <= 0.50
        ),
        "11_beats_c1_cagr_and_sharpe": (
            c1_diff["cagr"] > 0 and c1_diff["sharpe"] > 0
        ),
    }

    if not (gate["4_active_months_ge_12"] and gate["5_active_episodes_ge_5"] and gate["6_evaluable_segments_ge_2"]):
        verdict = "inconclusive_modern_translation_sample"
    elif all(gate.values()):
        verdict = "exact_v66_reflation_translation_candidate"
    elif full_diff["cagr"] > 0:
        verdict = "modern_direction_positive_but_implementation_not_robust"
    else:
        verdict = "modern_exact_signal_contradicts_long_history_candidate"

    serial = rows.copy()
    for col in ("origin_date","signal_date","end_date"):
        serial[col] = pd.to_datetime(serial[col]).dt.strftime("%Y-%m-%d")
    rows_path = out / "issue-127-monthly-policy.csv"
    serial.to_csv(rows_path, index=False, float_format="%.12g")

    ep_path = out / "issue-127-active-episodes.csv"
    episodes.to_csv(ep_path, index=False, float_format="%.12g")

    result = {
        "schema_version": 1,
        "issue": 127,
        "phase": "exact-v66-reflation-translation",
        "verdict": verdict,
        "production_authorized": False,
        "policy": {
            "base_weights": dict(zip(ASSETS, BASE.tolist(), strict=True)),
            "regime_3_weights": dict(zip(ASSETS, ACTIVE.tolist(), strict=True)),
            "primary_cost_bps": PRIMARY_COST_BPS,
        },
        "sample": {
            "monthly_completed": int(len(rows)),
            "first_origin": rows["origin_date"].min().date().isoformat(),
            "last_origin": rows["origin_date"].max().date().isoformat(),
            "active_months": active_months,
            "episode_count": episode_count,
            "evaluable_segments": evaluable_segments,
            "positive_segments": positive_segments,
        },
        "c1_average_weights": dict(zip(ASSETS, avg_weights.tolist(), strict=True)),
        "full": {
            "action": action,
            "c0": c0,
            "c1": c1,
            "action_minus_c0": full_diff,
            "action_minus_c1": c1_diff,
        },
        "segments": segments,
        "episode_robustness": {
            "strongest_positive_episode": strongest,
            "positive_contribution_total": positive_total,
            "top_positive_episode_share": float(top_share) if np.isfinite(top_share) else math.nan,
            "leaveout_action": leaveout,
            "leaveout_cagr_advantage_vs_c0": float(leaveout_adv) if np.isfinite(leaveout_adv) else math.nan,
        },
        "gate": gate,
        "gate_pass_count": int(sum(bool(v) for v in gate.values())),
        "source_provenance": provenance,
        "output_hashes": {
            "monthly_policy_csv_sha256": sha256_file(rows_path),
            "active_episodes_csv_sha256": sha256_file(ep_path),
        },
    }

    (out / "issue-127-result.json").write_text(
        json.dumps(result, indent=2, ensure_ascii=False, allow_nan=True) + "\n",
        encoding="utf-8",
    )

    print(json.dumps({
        "verdict": verdict,
        "gate": gate,
        "sample": result["sample"],
        "full": result["full"],
        "segments": {
            k: {
                "active_months": v["active_months"],
                "evaluable": v["evaluable"],
                "cagr_advantage": v["action_minus_c0"]["cagr"],
                "sharpe_advantage": v["action_minus_c0"]["sharpe"],
            }
            for k, v in segments.items()
        },
        "episode": result["episode_robustness"],
    }, indent=2, ensure_ascii=False, default=lambda x: bool(x) if isinstance(x, np.bool_) else float(x)))


if __name__ == "__main__":
    main()
