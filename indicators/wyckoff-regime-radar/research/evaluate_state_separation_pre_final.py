#!/usr/bin/env python3
"""Measure six-state path separation and stability before final OOS for Issue #55.

This diagnostic deliberately ignores the semantic names of the Wyckoff stages.
It asks a more forgiving question: does the formal state label explain a stable
amount of variation in the future path, regardless of whether a state named
"Markup" actually points upward?

Only development and exploratory OOS are used. The model is never computed on
final-OOS rows, and forward windows may not cross split boundaries.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
import pandas as pd

from evaluate_regime_paths_pre_final import HORIZONS, future_metrics, load_frozen_pair
from price_only_core import STAGE_NAMES, PriceOnlyConfig, compute_price_only


SPLITS = ("development", "exploratory_oos")
STAGES = tuple(range(1, 7))
METRICS = ("forward_return", "mfe", "mae", "realized_vol")
MIN_GROUP_N = 20


def eta_squared(values: np.ndarray, groups: np.ndarray) -> float | None:
    """One-way ANOVA eta-squared without a significance claim."""
    finite = np.isfinite(values) & np.isfinite(groups)
    values = values[finite]
    groups = groups[finite]
    if len(values) < 2 or len(np.unique(groups)) < 2:
        return None
    overall = float(np.mean(values))
    total_ss = float(np.sum((values - overall) ** 2))
    if total_ss <= 0.0:
        return 0.0
    between_ss = 0.0
    for group in np.unique(groups):
        selected = values[groups == group]
        between_ss += len(selected) * (float(np.mean(selected)) - overall) ** 2
    return between_ss / total_ss


def _rank(values: dict[int, float]) -> dict[int, float]:
    if not values:
        return {}
    series = pd.Series(values, dtype=float)
    ranked = series.rank(method="average")
    return {int(stage): float(rank) for stage, rank in ranked.items()}


def spearman_from_stage_means(left: dict[int, float], right: dict[int, float]) -> dict:
    common = sorted(set(left) & set(right))
    if len(common) < 3:
        return {"common_stage_count": len(common), "rho": None, "stages": common}
    left_rank = _rank({stage: left[stage] for stage in common})
    right_rank = _rank({stage: right[stage] for stage in common})
    x = np.array([left_rank[stage] for stage in common], dtype=float)
    y = np.array([right_rank[stage] for stage in common], dtype=float)
    if np.std(x) == 0 or np.std(y) == 0:
        rho = None
    else:
        rho = float(np.corrcoef(x, y)[0, 1])
    return {"common_stage_count": len(common), "rho": rho, "stages": common}


def sign_stability(left: dict[int, float], right: dict[int, float]) -> dict:
    common = sorted(set(left) & set(right))
    stable = 0
    rows = []
    for stage in common:
        a = left[stage]
        b = right[stage]
        sign_a = 0 if a == 0 else (1 if a > 0 else -1)
        sign_b = 0 if b == 0 else (1 if b > 0 else -1)
        same = sign_a == sign_b
        stable += int(same)
        rows.append({"stage": stage, "development_mean": a, "exploratory_mean": b, "same_sign": same})
    return {"common_stage_count": len(common), "same_sign_count": stable, "rows": rows}


def split_horizon_summary(
    metrics: dict[str, np.ndarray],
    formal: np.ndarray,
    start: int,
    end: int,
    horizon: int,
) -> dict:
    last_origin = end - horizon
    if last_origin < start:
        return {"eligible_origin_rows": 0, "states": {}, "metric_eta_squared": {name: None for name in METRICS}}

    index_mask = np.zeros(len(formal), dtype=bool)
    index_mask[start : last_origin + 1] = True
    valid_state = np.isin(formal, STAGES)
    finite_return = np.isfinite(metrics["forward_return"])
    base_mask = index_mask & valid_state & finite_return

    states = {}
    retained_stages = []
    for stage in STAGES:
        mask = base_mask & (formal == stage)
        n = int(np.sum(mask))
        row = {"sample_count": n}
        for metric in METRICS:
            selected = metrics[metric][mask]
            selected = selected[np.isfinite(selected)]
            row[metric + "_mean"] = float(np.mean(selected)) if len(selected) else None
        states[str(stage)] = row
        if n >= MIN_GROUP_N:
            retained_stages.append(stage)

    robust_mask = base_mask & np.isin(formal, retained_stages)
    eta = {}
    for metric in METRICS:
        metric_mask = robust_mask & np.isfinite(metrics[metric])
        eta[metric] = eta_squared(metrics[metric][metric_mask], formal[metric_mask].astype(float))

    return {
        "eligible_origin_rows": int(np.sum(base_mask)),
        "minimum_group_n": MIN_GROUP_N,
        "retained_stages": retained_stages,
        "retained_stage_count": len(retained_stages),
        "states": states,
        "metric_eta_squared": eta,
    }


def analyze_pair(frame: pd.DataFrame, meta: dict) -> dict:
    exploratory_end = int(meta["splits"]["exploratory_oos"]["end_index"])
    pre_final = frame.iloc[: exploratory_end + 1].copy().reset_index(drop=True)
    model = compute_price_only(pre_final, PriceOnlyConfig())
    formal = pd.to_numeric(model["formal_id"], errors="coerce").fillna(0).to_numpy(int)
    metrics_by_horizon = {h: future_metrics(pre_final, h) for h in HORIZONS}

    split_results = {}
    for split_name in SPLITS:
        split = meta["splits"][split_name]
        start = int(split["start_index"])
        end = int(split["end_index"])
        split_results[split_name] = {
            "start_date": split["start_date"],
            "end_date": split["end_date"],
            "horizons": {
                str(h): split_horizon_summary(metrics_by_horizon[h], formal, start, end, h)
                for h in HORIZONS
            },
        }

    stability = {}
    for horizon in HORIZONS:
        dev = split_results["development"]["horizons"][str(horizon)]
        exp = split_results["exploratory_oos"]["horizons"][str(horizon)]
        dev_means = {
            stage: dev["states"][str(stage)]["forward_return_mean"]
            for stage in dev["retained_stages"]
            if dev["states"][str(stage)]["forward_return_mean"] is not None
        }
        exp_means = {
            stage: exp["states"][str(stage)]["forward_return_mean"]
            for stage in exp["retained_stages"]
            if exp["states"][str(stage)]["forward_return_mean"] is not None
        }
        stability[str(horizon)] = {
            "forward_return_stage_rank": spearman_from_stage_means(dev_means, exp_means),
            "forward_return_sign": sign_stability(dev_means, exp_means),
        }

    return {
        "model_rows_computed": len(pre_final),
        "final_oos_rows_computed": 0,
        "splits": split_results,
        "development_to_exploratory_stability": stability,
    }


def aggregate(report_pairs: dict) -> dict:
    horizons = {}
    for horizon in HORIZONS:
        metric_summary = {}
        for metric in METRICS:
            exp_values = []
            dev_values = []
            for pair_report in report_pairs.values():
                exp_eta = pair_report["splits"]["exploratory_oos"]["horizons"][str(horizon)]["metric_eta_squared"][metric]
                dev_eta = pair_report["splits"]["development"]["horizons"][str(horizon)]["metric_eta_squared"][metric]
                if exp_eta is not None:
                    exp_values.append(exp_eta)
                if dev_eta is not None:
                    dev_values.append(dev_eta)
            metric_summary[metric] = {
                "development_pair_median_eta_squared": float(np.median(dev_values)) if dev_values else None,
                "exploratory_pair_median_eta_squared": float(np.median(exp_values)) if exp_values else None,
                "exploratory_pairs_comparable": len(exp_values),
            }
        rhos = []
        sign_stable = 0
        sign_total = 0
        for pair_report in report_pairs.values():
            stability = pair_report["development_to_exploratory_stability"][str(horizon)]
            rho = stability["forward_return_stage_rank"]["rho"]
            if rho is not None:
                rhos.append(rho)
            sign = stability["forward_return_sign"]
            sign_stable += sign["same_sign_count"]
            sign_total += sign["common_stage_count"]
        horizons[str(horizon)] = {
            "metrics": metric_summary,
            "median_forward_return_stage_rank_rho": float(np.median(rhos)) if rhos else None,
            "rank_comparable_pairs": len(rhos),
            "forward_return_sign_stability": {
                "same_sign_count": sign_stable,
                "common_stage_count": sign_total,
                "rate": sign_stable / sign_total if sign_total else None,
            },
        }
    return {"horizons": horizons}


def build_report(manifest_path: Path) -> dict:
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    if manifest.get("final_oos_status") != "SEALED_DO_NOT_EVALUATE":
        raise ValueError("refusing to run without final-OOS seal")
    pairs = {
        pair: analyze_pair(load_frozen_pair(manifest_path, meta), meta)
        for pair, meta in manifest["pairs"].items()
    }
    return {
        "schema_version": 1,
        "issue": 55,
        "status": "pre_final_state_separation_stability_analysis",
        "minimum_group_n": MIN_GROUP_N,
        "stage_names": {str(stage): STAGE_NAMES[stage] for stage in STAGES},
        "final_oos_status": "SEALED_NOT_COMPUTED",
        "pairs": pairs,
        "aggregate": aggregate(pairs),
        "interpretation": (
            "Eta-squared is descriptive variance explained by the formal state among stages with at least 20 eligible bars. "
            "Rank/sign stability compare development with exploratory OOS and intentionally ignore the semantic stage names."
        ),
        "boundary": "No final-OOS model output, no final-OOS price path, and no trading-utility claim.",
    }


def render_markdown(report: dict) -> str:
    lines = [
        "# Issue #55 — Pre-final state-separation scorecard",
        "",
        "Final OOS remains **SEALED / NOT COMPUTED**.",
        "",
        "This deliberately ignores whether labels such as Markup/Markdown are semantically correct. The question is only whether the formal-state label separates future paths and whether that separation is stable from Development to Exploratory OOS.",
        "",
        f"Only states with at least **{report['minimum_group_n']}** eligible bars enter eta-squared/rank comparisons.",
        "",
        "| Pair | H | States n≥20 Dev→Exp | Return η² Dev→Exp | MFE η² Dev→Exp | MAE η² Dev→Exp | Vol η² Dev→Exp | Return-rank ρ | Sign stable |",
        "|---|---:|---|---|---|---|---|---:|---:|",
    ]
    for pair, pair_report in report["pairs"].items():
        for horizon in HORIZONS:
            dev = pair_report["splits"]["development"]["horizons"][str(horizon)]
            exp = pair_report["splits"]["exploratory_oos"]["horizons"][str(horizon)]
            stability = pair_report["development_to_exploratory_stability"][str(horizon)]
            rho = stability["forward_return_stage_rank"]["rho"]
            sign = stability["forward_return_sign"]
            def f_eta(metric: str) -> str:
                a = dev["metric_eta_squared"][metric]
                b = exp["metric_eta_squared"][metric]
                left = "—" if a is None else f"{a:.3f}"
                right = "—" if b is None else f"{b:.3f}"
                return f"{left}→{right}"
            rho_text = "—" if rho is None else f"{rho:.2f}"
            sign_text = f"{sign['same_sign_count']}/{sign['common_stage_count']}" if sign["common_stage_count"] else "—"
            lines.append(
                f"| {pair} | {horizon} | {dev['retained_stage_count']}→{exp['retained_stage_count']} | "
                f"{f_eta('forward_return')} | {f_eta('mfe')} | {f_eta('mae')} | {f_eta('realized_vol')} | "
                f"{rho_text} | {sign_text} |"
            )

    lines.extend(["", "## Aggregate exploratory separation", ""])
    lines.append("| H | Return median η² | MFE median η² | MAE median η² | Vol median η² | Median return-rank ρ | Return-sign stability |")
    lines.append("|---:|---:|---:|---:|---:|---:|---:|")
    for horizon in HORIZONS:
        agg = report["aggregate"]["horizons"][str(horizon)]
        def m(metric: str) -> str:
            value = agg["metrics"][metric]["exploratory_pair_median_eta_squared"]
            return "—" if value is None else f"{value:.3f}"
        rho = agg["median_forward_return_stage_rank_rho"]
        sign = agg["forward_return_sign_stability"]
        sign_text = "—" if sign["rate"] is None else f"{sign['same_sign_count']}/{sign['common_stage_count']} ({sign['rate'] * 100:.1f}%)"
        lines.append(
            f"| {horizon} | {m('forward_return')} | {m('mfe')} | {m('mae')} | {m('realized_vol')} | "
            f"{'—' if rho is None else f'{rho:.2f}'} | {sign_text} |"
        )
    lines.extend([
        "",
        "Interpretation boundary: eta-squared is descriptive, not a significance test; high separation that fails Development→Exploratory stability is not treated as validated regime information.",
        "",
        "Boundary: Development + Exploratory OOS only. Final OOS remains sealed.",
        "",
    ])
    return "\n".join(lines)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    here = Path(__file__).resolve().parent
    parser.add_argument("--manifest", type=Path, default=here / "data" / "issue-55-static-fx-canonical-manifest.json")
    parser.add_argument("--json-output", type=Path)
    parser.add_argument("--md-output", type=Path)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    report = build_report(args.manifest)
    if args.json_output:
        args.json_output.parent.mkdir(parents=True, exist_ok=True)
        args.json_output.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    if args.md_output:
        args.md_output.parent.mkdir(parents=True, exist_ok=True)
        args.md_output.write_text(render_markdown(report), encoding="utf-8")
    print(json.dumps(report["aggregate"], indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
