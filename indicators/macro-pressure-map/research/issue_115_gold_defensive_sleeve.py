#!/usr/bin/env python3
"""Issue #115 — post-hoc Gold > Cash defensive sleeve robustness.

This study is explicitly selected from Issue #113 attribution.
All data are reused development evidence. No live data.
"""
from __future__ import annotations

import argparse
import json
import math
from pathlib import Path

import numpy as np
import pandas as pd

from issue_113_action_layer_sizing import (
    ASSETS,
    BASE_WEIGHTS,
    DIAGNOSTIC_COST_BPS,
    PRIMARY_COST_BPS,
    build_monthly_rows as build_issue113_monthly_rows,
    evaluate_action,
    evaluate_static,
    first_rows_each_month,
    identify_active_episodes,
    load_sources,
    portfolio_metrics,
    recompute_action_returns,
    segment_for_origin,
    sha256_file,
    state_on_date,
)

ACTIVE_STATES = (7, 8, 9)
GOLD_TARGET = np.array([0.40, 0.40, 0.15, 0.05], dtype=float)


def gold_target(regime_id: int, active_states: tuple[int, ...] = ACTIVE_STATES) -> np.ndarray:
    return GOLD_TARGET.copy() if int(regime_id) in set(active_states) else BASE_WEIGHTS.copy()


def build_gold_monthly_rows(
    panel: pd.DataFrame,
    transitions: pd.DataFrame,
    *,
    active_states: tuple[int, ...] = ACTIVE_STATES,
) -> pd.DataFrame:
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

        asset_rets = panel.iloc[next_pos].to_numpy(float) / panel.iloc[pos].to_numpy(float) - 1.0
        weights = gold_target(rid, active_states)

        row = {
            "origin_date": origin,
            "signal_date": signal_date,
            "end_date": end_date,
            "regime_id": int(rid),
            "segment": segment_for_origin(origin),
        }
        for asset, ret in zip(ASSETS, asset_rets, strict=True):
            row[f"{asset}_return"] = float(ret)
        for asset, weight in zip(ASSETS, weights, strict=True):
            row[f"w_{asset}"] = float(weight)
        rows.append(row)

    out = pd.DataFrame(rows).sort_values("origin_date").reset_index(drop=True)
    if out.empty:
        raise RuntimeError("no eligible Issue #115 monthly rows")
    return out


def apply_returns(rows: pd.DataFrame, cost_bps: float) -> pd.DataFrame:
    g = rows.copy().sort_values("origin_date").reset_index(drop=True)
    weight_cols = [f"w_{a}" for a in ASSETS]
    ret_cols = [f"{a}_return" for a in ASSETS]

    weights = g[weight_cols].to_numpy(float)
    asset_rets = g[ret_cols].to_numpy(float)

    gross = np.sum(weights * asset_rets, axis=1)
    turnover = np.zeros(len(g), dtype=float)
    if len(g) > 1:
        turnover[1:] = 0.5 * np.sum(np.abs(weights[1:] - weights[:-1]), axis=1)
    tactical_cost = turnover * (float(cost_bps) / 10_000.0)

    g["turnover"] = turnover
    g["tactical_cost"] = tactical_cost
    g["al_gross_return"] = gross
    g["al_net_return"] = gross - tactical_cost
    g["c0_return"] = asset_rets @ BASE_WEIGHTS
    g["shv_return"] = g["SHV_return"].astype(float)
    g["gold_cash_contribution"] = np.where(
        g["regime_id"].isin(list(ACTIVE_STATES)),
        0.05 * (g["GLD_return"] - g["SHV_return"]),
        0.0,
    )
    return g


def action_metrics(rows: pd.DataFrame) -> dict:
    return portfolio_metrics(
        rows["al_net_return"].to_numpy(float),
        rows["shv_return"].to_numpy(float),
        turnover=rows["turnover"].to_numpy(float),
        tactical_cost=rows["tactical_cost"].to_numpy(float),
        gross_returns=rows["al_gross_return"].to_numpy(float),
    )


def metric_diff(a: dict, b: dict) -> dict:
    return {
        key: float(a[key] - b[key])
        for key in ("cagr", "sharpe_excess_shv", "max_drawdown", "terminal_wealth")
    }


def leaveout_strongest_episode(
    raw_rows: pd.DataFrame,
    evaluated_rows: pd.DataFrame,
    episodes: pd.DataFrame,
) -> tuple[pd.DataFrame, dict]:
    positive = episodes.loc[episodes["contribution_sum"] > 0].copy()
    if positive.empty:
        return evaluated_rows.copy(), {
            "episode_id": None,
            "positive_contribution_total": 0.0,
            "top_positive_share": math.nan,
        }

    strongest = positive.sort_values("contribution_sum", ascending=False).iloc[0]
    total_positive = float(positive["contribution_sum"].sum())
    top_share = float(strongest["contribution_sum"] / total_positive)

    start = pd.Timestamp(strongest["start_origin"])
    end = pd.Timestamp(strongest["end_origin"])
    modified = raw_rows.copy()
    mask = (modified["origin_date"] >= start) & (modified["origin_date"] <= end)
    for asset, weight in zip(ASSETS, BASE_WEIGHTS, strict=True):
        modified.loc[mask, f"w_{asset}"] = float(weight)

    reevaluated = apply_returns(modified, PRIMARY_COST_BPS)
    meta = {
        "episode_id": int(strongest["episode_id"]),
        "start_origin": strongest["start_origin"],
        "end_origin": strongest["end_origin"],
        "months": int(strongest["months"]),
        "contribution_sum": float(strongest["contribution_sum"]),
        "positive_contribution_total": total_positive,
        "top_positive_share": top_share,
    }
    return reevaluated, meta


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--output-dir", type=Path, required=True)
    args = ap.parse_args()
    out = args.output_dir
    out.mkdir(parents=True, exist_ok=True)

    panel, transitions, provenance = load_sources()

    gold_raw = build_gold_monthly_rows(panel, transitions)
    gold = apply_returns(gold_raw, PRIMARY_COST_BPS)

    # Frozen Issue #113 full sparse overlay comparator.
    c2_raw = build_issue113_monthly_rows(panel, transitions)
    c2 = recompute_action_returns(c2_raw, PRIMARY_COST_BPS)

    if not gold["origin_date"].equals(c2["origin_date"]):
        raise RuntimeError("Issue #115 and #113 monthly origins do not align")

    avg_weights = gold[[f"w_{a}" for a in ASSETS]].mean(axis=0).to_numpy(float)
    if not np.isclose(avg_weights.sum(), 1.0, atol=1e-12):
        raise RuntimeError("C1 average weights do not sum to one")

    gold_full = action_metrics(gold)
    c0_full = evaluate_static(gold, BASE_WEIGHTS)
    c1_full = evaluate_static(gold, avg_weights)
    c2_full = evaluate_action(c2)

    segments: dict[str, dict] = {}
    for seg in ("pre_2020", "covid_inflation_2020_2022", "post_2023"):
        gg = gold.loc[gold["segment"].eq(seg)].copy()
        cc2 = c2.loc[c2["segment"].eq(seg)].copy()
        segments[seg] = {
            "gold_only": action_metrics(gg),
            "c0": evaluate_static(gg, BASE_WEIGHTS),
            "c1": evaluate_static(gg, avg_weights),
            "c2_issue113": evaluate_action(cc2),
        }
        segments[seg]["gold_minus_c0"] = metric_diff(segments[seg]["gold_only"], segments[seg]["c0"])

    episodes = identify_active_episodes(gold)
    leave_rows, strongest = leaveout_strongest_episode(gold_raw, gold, episodes)
    leave_metrics = action_metrics(leave_rows)
    leave_cagr_adv = float(leave_metrics["cagr"] - c0_full["cagr"])

    leave_one_state_out: dict[str, dict] = {}
    for removed in ACTIVE_STATES:
        keep = tuple(x for x in ACTIVE_STATES if x != removed)
        raw = build_gold_monthly_rows(panel, transitions, active_states=keep)
        evaluated = apply_returns(raw, PRIMARY_COST_BPS)
        m = action_metrics(evaluated)
        leave_one_state_out[f"remove_regime_{removed}"] = {
            "active_states": list(keep),
            "metrics": m,
            "cagr_advantage_vs_c0": float(m["cagr"] - c0_full["cagr"]),
            "sharpe_advantage_vs_c0": float(m["sharpe_excess_shv"] - c0_full["sharpe_excess_shv"]),
            "maxdd_difference_vs_c0": float(m["max_drawdown"] - c0_full["max_drawdown"]),
        }

    state_contribution: dict[str, dict] = {}
    for rid in ACTIVE_STATES:
        mask = gold["regime_id"].eq(rid)
        contrib = np.where(mask, 0.05 * (gold["GLD_return"] - gold["SHV_return"]), 0.0)
        state_contribution[str(rid)] = {
            "active_months": int(mask.sum()),
            "gross_contribution_sum": float(np.sum(contrib)),
            "annualized_mean_over_full_sample": float(np.mean(contrib) * 12.0),
        }

    diagnostics: dict[str, dict] = {}
    for bps in DIAGNOSTIC_COST_BPS:
        diag = apply_returns(gold_raw, bps)
        diagnostics[f"{int(bps)}bps"] = action_metrics(diag)

    cagr_adv = float(gold_full["cagr"] - c0_full["cagr"])
    sharpe_adv = float(gold_full["sharpe_excess_shv"] - c0_full["sharpe_excess_shv"])
    maxdd_diff = float(gold_full["max_drawdown"] - c0_full["max_drawdown"])
    seg_adv = {
        seg: float(item["gold_only"]["cagr"] - item["c0"]["cagr"])
        for seg, item in segments.items()
    }

    gate = {
        "1_full_cagr_adv_ge_25bp": cagr_adv >= 0.0025,
        "2_full_sharpe_adv_ge_005": sharpe_adv >= 0.05,
        "3_maxdd_not_worse_by_gt_15pp": maxdd_diff >= -0.015,
        "4_all_3_segments_positive_cagr_adv": all(v > 0 for v in seg_adv.values()),
        "5_min_segment_cagr_adv_ge_0": min(seg_adv.values()) >= 0.0,
        "6_strongest_episode_leaveout_positive": leave_cagr_adv > 0.0,
        "7_beats_c1_on_cagr_and_sharpe": (
            gold_full["cagr"] > c1_full["cagr"]
            and gold_full["sharpe_excess_shv"] > c1_full["sharpe_excess_shv"]
        ),
        "8_all_leave_one_state_out_positive": all(
            item["cagr_advantage_vs_c0"] > 0.0 for item in leave_one_state_out.values()
        ),
    }

    insufficient = any(segments[s]["gold_only"]["n"] < 24 for s in segments)
    if insufficient:
        verdict = "gold_defensive_sleeve_inconclusive"
    elif all(gate.values()):
        verdict = "gold_defensive_sleeve_robust_candidate"
    elif cagr_adv > 0:
        verdict = "gold_defensive_sleeve_economically_positive_but_posthoc_not_robust"
    else:
        verdict = "gold_defensive_sleeve_no_material_value"

    serial = gold.copy()
    for c in ("origin_date", "signal_date", "end_date"):
        serial[c] = pd.to_datetime(serial[c]).dt.strftime("%Y-%m-%d")
    rows_path = out / "issue-115-gold-monthly-portfolio.csv"
    serial.to_csv(rows_path, index=False, float_format="%.12g")

    episodes_path = out / "issue-115-gold-active-episodes.csv"
    episodes.to_csv(episodes_path, index=False, float_format="%.12g")

    result = {
        "schema_version": 1,
        "issue": 115,
        "phase": "posthoc-gold-defensive-sleeve-robustness",
        "posthoc_selected": True,
        "verdict": verdict,
        "production_authorized": False,
        "primary_cost_bps": PRIMARY_COST_BPS,
        "active_states": list(ACTIVE_STATES),
        "base_weights": dict(zip(ASSETS, BASE_WEIGHTS.tolist(), strict=True)),
        "gold_target": dict(zip(ASSETS, GOLD_TARGET.tolist(), strict=True)),
        "c1_average_weights": dict(zip(ASSETS, avg_weights.tolist(), strict=True)),
        "full": {
            "gold_only": gold_full,
            "c0": c0_full,
            "c1": c1_full,
            "c2_issue113": c2_full,
            "gold_minus_c0": metric_diff(gold_full, c0_full),
            "gold_minus_c1": metric_diff(gold_full, c1_full),
            "gold_minus_c2": metric_diff(gold_full, c2_full),
            "cagr_advantage_vs_c0": cagr_adv,
            "sharpe_advantage_vs_c0": sharpe_adv,
            "maxdd_difference_vs_c0": maxdd_diff,
        },
        "segments": segments,
        "segment_cagr_advantage_vs_c0": seg_adv,
        "episode_robustness": {
            "strongest_positive_episode": strongest,
            "leaveout_gold_only": leave_metrics,
            "leaveout_cagr_advantage_vs_c0": leave_cagr_adv,
        },
        "leave_one_state_out": leave_one_state_out,
        "state_contribution": state_contribution,
        "cost_diagnostics": diagnostics,
        "production_gate": gate,
        "production_gate_pass_count": int(sum(bool(v) for v in gate.values())),
        "rows": {
            "monthly_completed": int(len(gold)),
            "first_origin": gold["origin_date"].min().date().isoformat(),
            "last_origin": gold["origin_date"].max().date().isoformat(),
            "active_months": int(gold["regime_id"].isin(list(ACTIVE_STATES)).sum()),
            "episode_count": int(len(episodes)),
        },
        "source_provenance": provenance,
        "output_hashes": {
            "monthly_portfolio_csv_sha256": sha256_file(rows_path),
            "active_episodes_csv_sha256": sha256_file(episodes_path),
        },
        "interpretation_boundary": (
            "Post-hoc selected from Issue #113 attribution; even a full gate pass is not independent OOS confirmation."
        ),
    }

    result_path = out / "issue-115-result.json"
    result_path.write_text(json.dumps(result, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps({
        "verdict": verdict,
        "gate": gate,
        "full": {
            "cagr_advantage_vs_c0": cagr_adv,
            "sharpe_advantage_vs_c0": sharpe_adv,
            "maxdd_difference_vs_c0": maxdd_diff,
            "gold_minus_c2_cagr": result["full"]["gold_minus_c2"]["cagr"],
            "gold_minus_c2_sharpe": result["full"]["gold_minus_c2"]["sharpe_excess_shv"],
        },
        "segment_cagr_advantage_vs_c0": seg_adv,
        "leaveout_cagr_advantage_vs_c0": leave_cagr_adv,
        "leave_one_state_out": {
            k: v["cagr_advantage_vs_c0"] for k, v in leave_one_state_out.items()
        },
        "output": str(result_path),
    }, indent=2))


if __name__ == "__main__":
    main()
