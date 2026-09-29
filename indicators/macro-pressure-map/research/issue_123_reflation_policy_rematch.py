#!/usr/bin/env python3
"""Issue #123 — Reflation Equity > Treasury long-history policy rematch."""
from __future__ import annotations

import argparse
import hashlib
import json
import math
from pathlib import Path

import numpy as np
import pandas as pd

from issue_121_long_history_rematch import load_issue91_evidence

HERE = Path(__file__).resolve().parent
PREREG = HERE / "decisions" / "issue-123-reflation-policy-preregistered.md"

REFLATION = "Reflation / Inflation Rising"
BASE = np.array([0.50, 0.50], dtype=float)
ACTIVE = np.array([0.55, 0.45], dtype=float)
PRIMARY_COST_BPS = 5.0

BROAD_ERAS = (
    ("1928_1945", 1928, 1945),
    ("1946_1979", 1946, 1979),
    ("1980_1999", 1980, 1999),
    ("2000_2023", 2000, 2023),
)


def validate_prereg() -> None:
    s = PREREG.read_text(encoding="utf-8")
    required = [
        "PREREGISTERED BEFORE ISSUE #123 POLICY PERFORMANCE RESULTS",
        "Equity 0.55",
        "Treasury 0.45",
        "state_t -> full-calendar-year return_t+2",
        "strongest positive episode share <=0.50",
        "No Issue #123 policy performance result had been computed",
    ]
    missing = [x for x in required if x not in s]
    if missing:
        raise RuntimeError(f"Issue #123 prereg guard failed: {missing}")


def broad_era(signal_year: int) -> str:
    for label, start, end in BROAD_ERAS:
        if start <= int(signal_year) <= end:
            return label
    return "out_of_range"


def target_for_regime(regime: str) -> np.ndarray:
    return ACTIVE.copy() if str(regime) == REFLATION else BASE.copy()


def prepare_rows(causal: pd.DataFrame) -> pd.DataFrame:
    required = {
        "state_year",
        "return_year",
        "core_regime",
        "era",
        "equity",
        "treasury",
        "cash",
    }
    missing = required.difference(causal.columns)
    if missing:
        raise RuntimeError(f"missing Issue #91 causal columns: {sorted(missing)}")

    g = causal.copy().sort_values("return_year").reset_index(drop=True)
    if g["return_year"].duplicated().any():
        raise RuntimeError("duplicate causal return year")
    if not (g["return_year"].astype(int) - g["state_year"].astype(int)).eq(2).all():
        raise RuntimeError("strict causal t+2 alignment drift")

    weights = np.vstack([target_for_regime(x) for x in g["core_regime"]])
    g["w_equity"] = weights[:, 0]
    g["w_treasury"] = weights[:, 1]
    g["active"] = g["core_regime"].eq(REFLATION)
    g["broad_era"] = g["state_year"].astype(int).map(broad_era)
    if g["broad_era"].eq("out_of_range").any():
        raise RuntimeError("causal row fell outside frozen broad eras")
    return g


def apply_targets(rows: pd.DataFrame, *, reset_initial_turnover: bool = True) -> pd.DataFrame:
    g = rows.copy().sort_values("return_year").reset_index(drop=True)
    w = g[["w_equity", "w_treasury"]].to_numpy(float)
    r = g[["equity", "treasury"]].to_numpy(float)

    turnover = np.zeros(len(g), dtype=float)
    if len(g) > 1:
        turnover[1:] = 0.5 * np.abs(w[1:] - w[:-1]).sum(axis=1)
    if not reset_initial_turnover and len(g):
        turnover[0] = 0.5 * np.abs(w[0] - BASE).sum()

    gross = (w * r).sum(axis=1)
    cost = turnover * (PRIMARY_COST_BPS / 10_000.0)

    g["turnover"] = turnover
    g["tactical_cost"] = cost
    g["action_gross_return"] = gross
    g["action_net_return"] = gross - cost
    g["c0_return"] = 0.50 * g["equity"] + 0.50 * g["treasury"]
    g["episode_gross_increment"] = np.where(
        g["active"],
        0.05 * (g["equity"] - g["treasury"]),
        0.0,
    )
    return g


def static_returns(rows: pd.DataFrame, weights: np.ndarray) -> np.ndarray:
    r = rows[["equity", "treasury"]].to_numpy(float)
    return r @ np.asarray(weights, dtype=float)


def portfolio_metrics(
    returns: np.ndarray | pd.Series,
    cash: np.ndarray | pd.Series,
    *,
    turnover: np.ndarray | None = None,
    tactical_cost: np.ndarray | None = None,
) -> dict:
    x = np.asarray(returns, dtype=float)
    rf = np.asarray(cash, dtype=float)
    mask = np.isfinite(x) & np.isfinite(rf)
    x = x[mask]
    rf = rf[mask]
    n = int(len(x))
    if n == 0:
        raise RuntimeError("empty portfolio metric sample")
    if np.any(x <= -1.0):
        raise RuntimeError("portfolio return <= -100%")

    wealth = np.cumprod(1.0 + x)
    terminal = float(wealth[-1])
    cagr = float(terminal ** (1.0 / n) - 1.0)
    mean = float(np.mean(x))
    vol = float(np.std(x, ddof=1)) if n >= 2 else math.nan

    excess = x - rf
    excess_sd = float(np.std(excess, ddof=1)) if n >= 2 else math.nan
    sharpe = float(np.mean(excess) / excess_sd) if np.isfinite(excess_sd) and excess_sd > 0 else math.nan

    wealth_with_start = np.concatenate([[1.0], wealth])
    peak = np.maximum.accumulate(wealth_with_start)
    dd = wealth_with_start / peak - 1.0
    maxdd = float(np.min(dd))
    calmar = float(cagr / abs(maxdd)) if maxdd < 0 else math.nan

    result = {
        "n": n,
        "cagr": cagr,
        "arithmetic_mean": mean,
        "annual_volatility": vol,
        "sharpe_excess_cash": sharpe,
        "max_drawdown": maxdd,
        "calmar": calmar,
        "terminal_wealth": terminal,
    }

    if turnover is not None:
        t = np.asarray(turnover, dtype=float)[mask]
        result["annualized_tactical_turnover"] = float(np.mean(t))
    if tactical_cost is not None:
        c = np.asarray(tactical_cost, dtype=float)[mask]
        result["cumulative_tactical_cost"] = float(np.sum(c))
    return result


def metrics_for_rows(rows: pd.DataFrame, c1_weights: np.ndarray) -> dict:
    evaluated = apply_targets(rows, reset_initial_turnover=True)
    action = portfolio_metrics(
        evaluated["action_net_return"],
        evaluated["cash"],
        turnover=evaluated["turnover"],
        tactical_cost=evaluated["tactical_cost"],
    )
    c0 = portfolio_metrics(evaluated["c0_return"], evaluated["cash"])
    c1_returns = static_returns(evaluated, c1_weights)
    c1 = portfolio_metrics(c1_returns, evaluated["cash"])
    return {
        "action": action,
        "c0": c0,
        "c1": c1,
        "action_minus_c0": {
            "cagr": float(action["cagr"] - c0["cagr"]),
            "sharpe": float(action["sharpe_excess_cash"] - c0["sharpe_excess_cash"]),
            "max_drawdown": float(action["max_drawdown"] - c0["max_drawdown"]),
            "terminal_wealth": float(action["terminal_wealth"] - c0["terminal_wealth"]),
        },
        "action_minus_c1": {
            "cagr": float(action["cagr"] - c1["cagr"]),
            "sharpe": float(action["sharpe_excess_cash"] - c1["sharpe_excess_cash"]),
        },
    }


def identify_episodes(rows: pd.DataFrame) -> pd.DataFrame:
    g = rows.sort_values("return_year").reset_index(drop=True)
    episodes = []
    current = []
    last_year = None

    def flush(items: list[int]) -> None:
        if not items:
            return
        sub = g.loc[items]
        episodes.append({
            "episode_id": len(episodes) + 1,
            "start_return_year": int(sub["return_year"].min()),
            "end_return_year": int(sub["return_year"].max()),
            "start_signal_year": int(sub["state_year"].min()),
            "end_signal_year": int(sub["state_year"].max()),
            "active_years": int(len(sub)),
            "gross_contribution": float(sub["episode_gross_increment"].sum()),
        })

    for idx, row in g.iterrows():
        if not bool(row["active"]):
            flush(current)
            current = []
            last_year = None
            continue
        y = int(row["return_year"])
        if current and last_year is not None and y != last_year + 1:
            flush(current)
            current = []
        current.append(idx)
        last_year = y
    flush(current)
    return pd.DataFrame(episodes)


def revert_mask(rows: pd.DataFrame, mask: pd.Series) -> pd.DataFrame:
    g = rows.copy()
    g.loc[mask, "w_equity"] = BASE[0]
    g.loc[mask, "w_treasury"] = BASE[1]
    g.loc[mask, "active"] = False
    return g


def full_policy_metrics(rows: pd.DataFrame, c1_weights: np.ndarray) -> dict:
    evaluated = apply_targets(rows, reset_initial_turnover=True)
    action = portfolio_metrics(
        evaluated["action_net_return"],
        evaluated["cash"],
        turnover=evaluated["turnover"],
        tactical_cost=evaluated["tactical_cost"],
    )
    c0 = portfolio_metrics(evaluated["c0_return"], evaluated["cash"])
    c1 = portfolio_metrics(static_returns(evaluated, c1_weights), evaluated["cash"])
    return {
        "action": action,
        "c0": c0,
        "c1": c1,
        "action_minus_c0": {
            "cagr": float(action["cagr"] - c0["cagr"]),
            "sharpe": float(action["sharpe_excess_cash"] - c0["sharpe_excess_cash"]),
            "max_drawdown": float(action["max_drawdown"] - c0["max_drawdown"]),
        },
        "action_minus_c1": {
            "cagr": float(action["cagr"] - c1["cagr"]),
            "sharpe": float(action["sharpe_excess_cash"] - c1["sharpe_excess_cash"]),
        },
    }


def run(output_dir: Path) -> dict:
    validate_prereg()
    output_dir.mkdir(parents=True, exist_ok=True)

    _, causal, issue91_manifest = load_issue91_evidence()
    rows = prepare_rows(causal)
    evaluated = apply_targets(rows, reset_initial_turnover=True)

    c1_weights = evaluated[["w_equity", "w_treasury"]].mean().to_numpy(float)
    if not np.isclose(c1_weights.sum(), 1.0, atol=1e-12):
        raise RuntimeError("C1 weights do not sum to one")

    full = full_policy_metrics(rows, c1_weights)

    broad = {}
    for label, _, _ in BROAD_ERAS:
        sub = rows.loc[rows["broad_era"].eq(label)].copy()
        m = metrics_for_rows(sub, c1_weights)
        broad[label] = {
            "signal_year_first": int(sub["state_year"].min()),
            "signal_year_last": int(sub["state_year"].max()),
            "return_year_first": int(sub["return_year"].min()),
            "return_year_last": int(sub["return_year"].max()),
            "active_years": int(sub["active"].sum()),
            **m,
        }

    fine_leaveouts = {}
    for era_name in sorted(rows.loc[rows["active"], "era"].dropna().astype(str).unique()):
        mask = rows["era"].astype(str).eq(era_name) & rows["active"]
        modified = revert_mask(rows, mask)
        m = full_policy_metrics(modified, c1_weights)
        fine_leaveouts[era_name] = {
            "removed_active_years": int(mask.sum()),
            "cagr_advantage_vs_c0": m["action_minus_c0"]["cagr"],
            "sharpe_advantage_vs_c0": m["action_minus_c0"]["sharpe"],
            "action": m["action"],
        }

    episodes = identify_episodes(evaluated)
    positive = episodes.loc[episodes["gross_contribution"] > 0].copy()
    if positive.empty:
        strongest = None
        strongest_share = math.nan
        episode_leaveout = None
    else:
        strongest_row = positive.sort_values("gross_contribution", ascending=False).iloc[0]
        total_positive = float(positive["gross_contribution"].sum())
        strongest_share = float(strongest_row["gross_contribution"] / total_positive)
        strongest = {
            k: (
                int(strongest_row[k])
                if k in {
                    "episode_id",
                    "start_return_year",
                    "end_return_year",
                    "start_signal_year",
                    "end_signal_year",
                    "active_years",
                }
                else float(strongest_row[k])
            )
            for k in strongest_row.index
        }
        mask = (
            rows["return_year"].between(
                strongest["start_return_year"], strongest["end_return_year"]
            )
            & rows["active"]
        )
        modified = revert_mask(rows, mask)
        episode_leaveout = full_policy_metrics(modified, c1_weights)

    evaluable_broad = [
        label for label, x in broad.items() if x["action"]["n"] >= 8
    ]
    positive_broad = [
        label
        for label in evaluable_broad
        if broad[label]["action_minus_c0"]["cagr"] > 0
    ]
    min_broad_adv = min(
        (broad[label]["action_minus_c0"]["cagr"] for label in evaluable_broad),
        default=math.nan,
    )

    gate = {
        "1_action_cagr_gt_c0": full["action_minus_c0"]["cagr"] > 0,
        "2_action_sharpe_gt_c0": full["action_minus_c0"]["sharpe"] > 0,
        "3_maxdd_difference_ge_minus_1pp": full["action_minus_c0"]["max_drawdown"] >= -0.010,
        "4_at_least_3_broad_eras_evaluable": len(evaluable_broad) >= 3,
        "5_at_least_3_broad_eras_positive_cagr_adv": len(positive_broad) >= 3,
        "6_no_broad_era_cagr_disadvantage_below_minus_25bp": (
            len(evaluable_broad) > 0 and min_broad_adv >= -0.0025
        ),
        "7_strongest_episode_leaveout_positive_cagr_adv": (
            episode_leaveout is not None
            and episode_leaveout["action_minus_c0"]["cagr"] > 0
        ),
        "8_strongest_positive_episode_share_le_50pct": (
            np.isfinite(strongest_share) and strongest_share <= 0.50
        ),
        "9_action_beats_c1_cagr_and_sharpe": (
            full["action_minus_c1"]["cagr"] > 0
            and full["action_minus_c1"]["sharpe"] > 0
        ),
        "10_all_fine_era_leaveouts_positive_cagr_adv": (
            len(fine_leaveouts) > 0
            and all(x["cagr_advantage_vs_c0"] > 0 for x in fine_leaveouts.values())
        ),
    }

    if len(evaluable_broad) < 3:
        verdict = "inconclusive_policy_sample"
    elif all(gate.values()):
        verdict = "long_history_reflation_policy_candidate"
    elif full["action_minus_c0"]["cagr"] > 0:
        verdict = "economically_positive_but_policy_robustness_failed"
    else:
        verdict = "no_material_policy_value"

    serial = evaluated.copy()
    rows_path = output_dir / "issue-123-annual-policy.csv"
    serial.to_csv(rows_path, index=False, float_format="%.12g")

    episodes_path = output_dir / "issue-123-active-episodes.csv"
    episodes.to_csv(episodes_path, index=False, float_format="%.12g")

    result = {
        "schema_version": 1,
        "issue": 123,
        "phase": "reflation-equity-treasury-policy-rematch",
        "verdict": verdict,
        "production_authorized": False,
        "policy": {
            "base": {"equity": 0.50, "treasury": 0.50},
            "reflation": {"equity": 0.55, "treasury": 0.45},
            "primary_cost_bps": PRIMARY_COST_BPS,
            "timing": "state_t_to_return_t_plus_2",
        },
        "sample": {
            "rows": int(len(rows)),
            "signal_year_first": int(rows["state_year"].min()),
            "signal_year_last": int(rows["state_year"].max()),
            "return_year_first": int(rows["return_year"].min()),
            "return_year_last": int(rows["return_year"].max()),
            "active_years": int(rows["active"].sum()),
            "episode_count": int(len(episodes)),
        },
        "c1_average_weights": {
            "equity": float(c1_weights[0]),
            "treasury": float(c1_weights[1]),
        },
        "full": full,
        "broad_eras": broad,
        "evaluable_broad_eras": evaluable_broad,
        "positive_broad_eras": positive_broad,
        "fine_era_leaveouts": fine_leaveouts,
        "episode_robustness": {
            "strongest_positive_episode": strongest,
            "strongest_positive_episode_share": float(strongest_share)
            if np.isfinite(strongest_share)
            else math.nan,
            "leaveout": episode_leaveout,
        },
        "gate": gate,
        "gate_pass_count": int(sum(bool(x) for x in gate.values())),
        "source_backbone": {
            "hmra_freeze_validated": bool(
                issue91_manifest["hmra_freeze_validated_before_asset_join"]
            ),
            "damodaran_raw_sha256": issue91_manifest["sources"]["damodaran"]["raw_sha256"],
            "jst_raw_sha256": issue91_manifest["sources"]["jst"]["raw_sha256"],
        },
        "output_hashes": {
            "annual_policy_csv_sha256": hashlib.sha256(rows_path.read_bytes()).hexdigest(),
            "active_episodes_csv_sha256": hashlib.sha256(
                episodes_path.read_bytes()
            ).hexdigest(),
        },
    }

    result_path = output_dir / "issue-123-result.json"
    result_path.write_text(
        json.dumps(
            result,
            indent=2,
            ensure_ascii=False,
            allow_nan=True,
            default=lambda x: bool(x) if isinstance(x, np.bool_) else float(x),
        )
        + "\n",
        encoding="utf-8",
    )

    print(
        json.dumps(
            {
                "verdict": verdict,
                "gate": gate,
                "full": full,
                "broad_cagr_adv": {
                    k: v["action_minus_c0"]["cagr"] for k, v in broad.items()
                },
                "fine_leaveout_cagr_adv": {
                    k: v["cagr_advantage_vs_c0"]
                    for k, v in fine_leaveouts.items()
                },
                "episode": result["episode_robustness"],
            },
            indent=2,
            ensure_ascii=False,
            default=lambda x: bool(x) if isinstance(x, np.bool_) else float(x),
        )
    )
    return result


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--output-dir", type=Path, required=True)
    args = ap.parse_args()
    run(args.output_dir)


if __name__ == "__main__":
    main()
