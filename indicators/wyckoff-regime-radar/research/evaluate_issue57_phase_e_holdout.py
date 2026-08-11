#!/usr/bin/env python3
"""One-shot independent cross-market holdout evaluation for Issue #57 Phase E.

This script is intentionally downstream of the committed Phase-E opening record.
It evaluates the frozen v0.6 Phase-A/B core plus the frozen canonical four-state
mapping on USDCAD/USDCHF/EURCHF exactly once, with no parameter tuning.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
import pandas as pd

from evaluate_confidence_calibration_pre_final import MIN_EXP_BIN_N
from evaluate_regime_paths_pre_final import HORIZONS, future_metrics, load_frozen_pair
from evaluate_state_separation_pre_final import METRICS, MIN_GROUP_N, eta_squared
from evaluate_trading_utility_exploratory import (
    PRIMARY_COST_PIPS,
    aggregate_equal_weight,
    donchian55_targets,
    evaluate_targets,
    flat_targets,
    momentum60_targets,
    sma200_targets,
)
from generate_v06_phase_b_core import load_phase_b_namespace
from v06_state_mapping import attach_canonical_four_state


CANONICAL_STATES = (1, 2, 3, 4)
STATE_NAMES = {
    1: "Accumulation family",
    2: "Markup",
    3: "Distribution family",
    4: "Markdown",
}
WEIGHT_COLUMNS = {
    1: "regime_accumulation_family",
    2: "regime_markup",
    3: "regime_distribution_family",
    4: "regime_markdown",
}
PIP_SIZE = {"USDCAD": 0.0001, "USDCHF": 0.0001, "EURCHF": 0.0001}
MATERIAL_SHARE = 0.01
MAX_MEDIAN_HALF_TV = 0.30
MIN_SIGN_STABILITY = 0.50
MIN_STRENGTH_SUCCESS = 0.50


def _phase_b_engine():
    namespace = load_phase_b_namespace()
    return namespace["compute_price_only"], namespace["PriceOnlyConfig"]


def _mean(values) -> float | None:
    arr = np.asarray(values, dtype=float)
    arr = arr[np.isfinite(arr)]
    return float(np.mean(arr)) if len(arr) else None


def _sign(value: float) -> int:
    return 0 if value == 0.0 else (1 if value > 0.0 else -1)


def attach_strength(model: pd.DataFrame) -> pd.DataFrame:
    result = attach_canonical_four_state(model)
    formal = result["canonical_formal_id"].fillna(0).to_numpy(int)
    weights = {state: pd.to_numeric(result[column], errors="coerce").to_numpy(float) for state, column in WEIGHT_COLUMNS.items()}
    support = np.full(len(result), np.nan)
    margin = np.full(len(result), np.nan)
    for i, state in enumerate(formal):
        if state not in CANONICAL_STATES:
            continue
        current = weights[state][i]
        competitors = [weights[other][i] for other in CANONICAL_STATES if other != state]
        if np.isfinite(current) and all(np.isfinite(value) for value in competitors):
            support[i] = current
            margin[i] = current - max(competitors)
    result["regime_support"] = support
    result["regime_margin"] = margin
    return result


def live_window(model: pd.DataFrame) -> tuple[int, int]:
    matrix = np.column_stack(
        [pd.to_numeric(model[WEIGHT_COLUMNS[state]], errors="coerce").to_numpy(float) for state in CANONICAL_STATES]
    )
    live = np.all(np.isfinite(matrix), axis=1) & (np.sum(matrix, axis=1) > 0.0)
    idx = np.flatnonzero(live)
    if not len(idx):
        raise ValueError("no live canonical four-state bars after warm-up")
    return int(idx[0]), int(idx[-1])


def state_shares(formal: np.ndarray, start: int, end: int) -> dict[str, float]:
    values = formal[start : end + 1]
    denominator = len(values)
    return {str(state): float(np.sum(values == state) / denominator) for state in CANONICAL_STATES}


def path_summary(frame: pd.DataFrame, formal: np.ndarray, start: int, end: int, horizon: int) -> dict:
    metrics = future_metrics(frame, horizon)
    last_origin = end - horizon
    states = {}
    retained = []
    for state in CANONICAL_STATES:
        idx = np.array(
            [i for i in range(start, last_origin + 1) if formal[i] == state and np.isfinite(metrics["forward_return"][i])],
            dtype=int,
        )
        row = {"sample_count": int(len(idx))}
        for metric in METRICS:
            values = metrics[metric][idx] if len(idx) else np.array([], dtype=float)
            row[metric + "_mean"] = _mean(values)
        states[str(state)] = row
        if len(idx) >= MIN_GROUP_N:
            retained.append(state)

    eligible = np.array(
        [
            i
            for i in range(start, last_origin + 1)
            if formal[i] in retained and np.isfinite(metrics["forward_return"][i])
        ],
        dtype=int,
    )
    eta = {}
    for metric in METRICS:
        if len(eligible):
            mask = np.isfinite(metrics[metric][eligible])
            idx = eligible[mask]
            eta[metric] = eta_squared(metrics[metric][idx], formal[idx].astype(float)) if len(idx) else None
        else:
            eta[metric] = None

    markup = states["2"]
    markdown = states["4"]
    comparable = markup["sample_count"] >= MIN_GROUP_N and markdown["sample_count"] >= MIN_GROUP_N
    directional = None
    spread = None
    if comparable and markup["forward_return_mean"] is not None and markdown["forward_return_mean"] is not None:
        spread = markup["forward_return_mean"] - markdown["forward_return_mean"]
        directional = spread > 0.0

    return {
        "minimum_group_n": MIN_GROUP_N,
        "retained_states": retained,
        "states": states,
        "eta_squared": eta,
        "directional_sanity": {
            "comparable": comparable,
            "markup_minus_markdown_mean_return": spread,
            "markup_above_markdown": directional,
        },
    }


def half_summary(frame: pd.DataFrame, formal: np.ndarray, start: int, end: int) -> dict:
    return {
        str(horizon): path_summary(frame, formal, start, end, horizon)
        for horizon in HORIZONS
    }


def temporal_stability(frame: pd.DataFrame, formal: np.ndarray, start: int, end: int) -> dict:
    n = end - start + 1
    first_end = start + n // 2 - 1
    second_start = first_end + 1
    first_shares = state_shares(formal, start, first_end)
    second_shares = state_shares(formal, second_start, end)
    tv = 0.5 * sum(abs(first_shares[str(s)] - second_shares[str(s)]) for s in CANONICAL_STATES)
    first_paths = half_summary(frame, formal, start, first_end)
    second_paths = half_summary(frame, formal, second_start, end)

    sign_rows = []
    for horizon in HORIZONS:
        for state in CANONICAL_STATES:
            left = first_paths[str(horizon)]["states"][str(state)]
            right = second_paths[str(horizon)]["states"][str(state)]
            comparable = left["sample_count"] >= MIN_GROUP_N and right["sample_count"] >= MIN_GROUP_N
            same = None
            if comparable and left["forward_return_mean"] is not None and right["forward_return_mean"] is not None:
                same = _sign(left["forward_return_mean"]) == _sign(right["forward_return_mean"])
            sign_rows.append(
                {
                    "horizon": horizon,
                    "state": state,
                    "first_n": left["sample_count"],
                    "second_n": right["sample_count"],
                    "same_return_sign": same,
                }
            )
    comparable_rows = [row for row in sign_rows if row["same_return_sign"] is not None]
    stable_count = sum(bool(row["same_return_sign"]) for row in comparable_rows)
    return {
        "first_half": {"start_index": start, "end_index": first_end, "shares": first_shares},
        "second_half": {"start_index": second_start, "end_index": end, "shares": second_shares},
        "occupancy_total_variation": tv,
        "return_sign_rows": sign_rows,
        "return_sign_comparable_cases": len(comparable_rows),
        "return_sign_stable_cases": stable_count,
        "return_sign_stability_rate": stable_count / len(comparable_rows) if comparable_rows else None,
    }


def strength_persistence(model: pd.DataFrame, formal: np.ndarray, start: int, end: int) -> dict:
    n = end - start + 1
    first_end = start + n // 2 - 1
    second_start = first_end + 1
    fields = {}
    for field in ("regime_support", "regime_margin"):
        values = pd.to_numeric(model[field], errors="coerce").to_numpy(float)
        dev = values[start : first_end + 1]
        dev_formal = formal[start : first_end + 1]
        finite = dev[np.isfinite(dev) & np.isin(dev_formal, CANONICAL_STATES)]
        if len(finite) < MIN_GROUP_N:
            fields[field] = {"cutpoints": None, "horizons": {}}
            continue
        q33, q67 = (float(x) for x in np.quantile(finite, [1 / 3, 2 / 3]))
        horizons = {}
        for horizon in HORIZONS:
            low = []
            high = []
            last_origin = end - horizon
            for i in range(second_start, last_origin + 1):
                if formal[i] not in CANONICAL_STATES or not np.isfinite(values[i]):
                    continue
                persisted = float(formal[i + horizon] == formal[i])
                if values[i] <= q33:
                    low.append(persisted)
                elif values[i] > q67:
                    high.append(persisted)
            comparable = len(low) >= MIN_EXP_BIN_N and len(high) >= MIN_EXP_BIN_N
            low_rate = float(np.mean(low)) if low else None
            high_rate = float(np.mean(high)) if high else None
            horizons[str(horizon)] = {
                "low_n": len(low),
                "high_n": len(high),
                "low_persistence": low_rate,
                "high_persistence": high_rate,
                "comparable": comparable,
                "high_better_than_low": None if not comparable else high_rate > low_rate,
            }
        fields[field] = {"cutpoints": {"q33": q33, "q67": q67}, "horizons": horizons}
    return fields


def v06_targets(model: pd.DataFrame) -> np.ndarray:
    formal = model["canonical_formal_id"].fillna(0).to_numpy(int)
    response = {0: 0.0, 1: 0.0, 2: 1.0, 3: 0.0, 4: -1.0}
    return np.array([response[int(state)] for state in formal], dtype=float)


def strategy_targets(frame: pd.DataFrame, model: pd.DataFrame) -> dict[str, np.ndarray]:
    return {
        "wyckoff_v06_frozen_response": v06_targets(model),
        "sma200": sma200_targets(frame),
        "momentum60": momentum60_targets(frame),
        "donchian55": donchian55_targets(frame),
        "always_flat": flat_targets(frame),
    }


def analyze_pair(pair: str, frame: pd.DataFrame) -> tuple[dict, dict[str, pd.DataFrame]]:
    compute_price_only, config_cls = _phase_b_engine()
    raw = compute_price_only(frame.reset_index(drop=True), config_cls())
    model = attach_strength(raw)
    formal = model["canonical_formal_id"].fillna(0).to_numpy(int)
    start, end = live_window(model)
    shares = state_shares(formal, start, end)
    material = {str(state): shares[str(state)] >= MATERIAL_SHARE for state in CANONICAL_STATES}
    paths = {str(h): path_summary(frame, formal, start, end, h) for h in HORIZONS}
    temporal = temporal_stability(frame, formal, start, end)
    strength = strength_persistence(model, formal, start, end)

    daily_outputs = {}
    strategies = {}
    for name, target in strategy_targets(frame, model).items():
        perf, daily = evaluate_targets(frame, target, start, end, PIP_SIZE[pair], PRIMARY_COST_PIPS)
        strategies[name] = perf
        daily_outputs[name] = daily

    return (
        {
            "rows": len(frame),
            "live_start_index": start,
            "live_end_index": end,
            "live_start_date": str(frame.iloc[start]["date"]),
            "live_end_date": str(frame.iloc[end]["date"]),
            "live_rows": end - start + 1,
            "neutral_share": float(np.mean(formal[start : end + 1] == 0)),
            "state_shares": shares,
            "material_states": material,
            "material_state_count": sum(material.values()),
            "paths": paths,
            "temporal_stability": temporal,
            "strength_persistence": strength,
            "strategies": strategies,
        },
        daily_outputs,
    )


def verdict_summary(pairs: dict, aggregate_strategies: dict) -> dict:
    coverage_each_state = {
        str(state): sum(bool(pair["material_states"][str(state)]) for pair in pairs.values())
        for state in CANONICAL_STATES
    }
    coverage_pass = all(count >= 2 for count in coverage_each_state.values()) and all(
        pair["material_state_count"] >= 3 for pair in pairs.values()
    )

    directional_rows = []
    eta_values = {metric: [] for metric in METRICS}
    for pair_name, pair in pairs.items():
        for horizon in HORIZONS:
            row = pair["paths"][str(horizon)]
            sanity = row["directional_sanity"]["markup_above_markdown"]
            if sanity is not None:
                directional_rows.append(bool(sanity))
            for metric in METRICS:
                value = row["eta_squared"][metric]
                if value is not None:
                    eta_values[metric].append(float(value))
    directional_rate = sum(directional_rows) / len(directional_rows) if directional_rows else None
    directional_pass = directional_rate is not None and directional_rate > 0.50

    tv_values = [pair["temporal_stability"]["occupancy_total_variation"] for pair in pairs.values()]
    median_tv = float(np.median(tv_values))
    sign_comparable = sum(pair["temporal_stability"]["return_sign_comparable_cases"] for pair in pairs.values())
    sign_stable = sum(pair["temporal_stability"]["return_sign_stable_cases"] for pair in pairs.values())
    sign_rate = sign_stable / sign_comparable if sign_comparable else None
    temporal_pass = median_tv <= MAX_MEDIAN_HALF_TV and sign_rate is not None and sign_rate >= MIN_SIGN_STABILITY

    strength_summary = {}
    strength_pass = False
    for field in ("regime_support", "regime_margin"):
        comparable = 0
        better = 0
        for pair in pairs.values():
            for row in pair["strength_persistence"][field]["horizons"].values():
                if row["high_better_than_low"] is not None:
                    comparable += 1
                    better += int(bool(row["high_better_than_low"]))
        rate = better / comparable if comparable else None
        strength_summary[field] = {
            "comparable_cases": comparable,
            "high_better_cases": better,
            "rate": rate,
        }
        if rate is not None and rate > MIN_STRENGTH_SUCCESS:
            strength_pass = True

    robustness_pass = coverage_pass and directional_pass and temporal_pass and strength_pass

    wyckoff = aggregate_strategies["wyckoff_v06_frozen_response"]
    baseline_rows = {}
    incremental_wins = 0
    for baseline in ("sma200", "momentum60", "donchian55"):
        base = aggregate_strategies[baseline]
        return_diff = wyckoff["net_annualized_return"] - base["net_annualized_return"]
        if wyckoff["annualized_sharpe_zero_cash"] is None or base["annualized_sharpe_zero_cash"] is None:
            sharpe_diff = None
            beat_both = False
        else:
            sharpe_diff = wyckoff["annualized_sharpe_zero_cash"] - base["annualized_sharpe_zero_cash"]
            beat_both = return_diff > 0.0 and sharpe_diff > 0.0
        incremental_wins += int(beat_both)
        baseline_rows[baseline] = {
            "net_annualized_return_difference": return_diff,
            "sharpe_difference": sharpe_diff,
            "beats_on_both": beat_both,
        }
    incremental_pass = incremental_wins >= 2

    if not robustness_pass:
        verdict = "unstable_on_independent_fx_pairs"
    elif not incremental_pass:
        verdict = "descriptive_but_not_incremental"
    else:
        verdict = "validated_cross_market_robustness"

    return {
        "verdict": verdict,
        "coverage": {
            "pass": coverage_pass,
            "material_pair_count_by_state": coverage_each_state,
            "material_state_count_by_pair": {name: pair["material_state_count"] for name, pair in pairs.items()},
        },
        "directional_sanity": {
            "pass": directional_pass,
            "positive_cases": int(sum(directional_rows)),
            "comparable_cases": len(directional_rows),
            "rate": directional_rate,
        },
        "temporal_stability": {
            "pass": temporal_pass,
            "median_occupancy_total_variation": median_tv,
            "return_sign_stable_cases": sign_stable,
            "return_sign_comparable_cases": sign_comparable,
            "return_sign_stability_rate": sign_rate,
        },
        "strength_persistence": {"pass": strength_pass, "fields": strength_summary},
        "path_separation_median_eta_squared": {
            metric: (float(np.median(values)) if values else None) for metric, values in eta_values.items()
        },
        "regime_robustness_pass": robustness_pass,
        "incremental_trading_utility": {
            "pass": incremental_pass,
            "baseline_wins_required": 2,
            "baseline_wins": incremental_wins,
            "comparisons": baseline_rows,
        },
    }


def build_report(manifest_path: Path, opening_record: Path, implementation_gate: Path) -> dict:
    if not opening_record.exists():
        raise ValueError("Phase-E opening record missing; refusing to evaluate holdout")
    if not implementation_gate.exists():
        raise ValueError("Pine implementation-gate record missing; refusing to evaluate holdout")
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    expected_status = "SEALED_DO_NOT_EVALUATE_UNTIL_V06_PINE_PARITY_GATE_PASSES"
    if manifest.get("status") != expected_status:
        raise ValueError("Phase-E manifest seal/status changed unexpectedly")
    expected_pairs = ("USDCAD", "USDCHF", "EURCHF")
    if tuple(manifest.get("selection", {}).get("pairs", [])) != expected_pairs:
        raise ValueError("Phase-E pair set changed unexpectedly")
    if any(manifest["pairs"][pair].get("evaluation_status") != "SEALED_NOT_COMPUTED" for pair in expected_pairs):
        raise ValueError("Phase-E manifest evaluation marker changed before one-shot evaluation")

    pairs = {}
    pair_daily = {}
    for pair in expected_pairs:
        frame = load_frozen_pair(manifest_path, manifest["pairs"][pair])
        result, daily = analyze_pair(pair, frame)
        pairs[pair] = result
        pair_daily[pair] = daily
    aggregate_strategies = aggregate_equal_weight(pair_daily)
    summary = verdict_summary(pairs, aggregate_strategies)

    return {
        "schema_version": 1,
        "issue": 57,
        "phase": "E-independent-cross-market-holdout",
        "status": "OPENED_AND_EVALUATED_ONE_SHOT",
        "pairs": pairs,
        "equal_weight_three_pair_strategies": aggregate_strategies,
        "summary": summary,
        "decision_rules": {
            "material_state_share": MATERIAL_SHARE,
            "minimum_path_group_n": MIN_GROUP_N,
            "minimum_strength_bin_n": MIN_EXP_BIN_N,
            "max_median_half_occupancy_tv": MAX_MEDIAN_HALF_TV,
            "minimum_return_sign_stability": MIN_SIGN_STABILITY,
            "minimum_strength_high_beats_low_rate_exclusive": MIN_STRENGTH_SUCCESS,
            "directional_pass": "Markup mean forward return > Markdown in >50% comparable pair×horizon cases",
            "incremental_pass": "Wyckoff beats >=2/3 active baselines on both net annualized return and zero-cash Sharpe",
        },
        "boundary": (
            "This holdout is now consumed. No v0.6 parameter, mapping, persistence rule, strength semantic, response map, "
            "baseline, cost, or verdict rule may be changed and then re-tested on these three pairs as an independent test."
        ),
    }


def render_markdown(report: dict) -> str:
    summary = report["summary"]
    lines = [
        "# Issue #57 — Phase E ONE-SHOT cross-market holdout result",
        "",
        f"Final verdict: **`{summary['verdict']}`**",
        "",
        "The USDCAD / USDCHF / EURCHF holdout is now consumed and may not be reused as an independent test after redesign.",
        "",
        "## Gate scorecard",
        "",
        f"- Coverage: **{'PASS' if summary['coverage']['pass'] else 'FAIL'}** — material pair counts by state: {summary['coverage']['material_pair_count_by_state']}.",
        f"- Directional sanity: **{'PASS' if summary['directional_sanity']['pass'] else 'FAIL'}** — {summary['directional_sanity']['positive_cases']}/{summary['directional_sanity']['comparable_cases']} ({0 if summary['directional_sanity']['rate'] is None else summary['directional_sanity']['rate'] * 100:.1f}%) Markup > Markdown.",
        f"- Temporal stability: **{'PASS' if summary['temporal_stability']['pass'] else 'FAIL'}** — median occupancy TV {summary['temporal_stability']['median_occupancy_total_variation']:.3f}; return-sign stability {summary['temporal_stability']['return_sign_stable_cases']}/{summary['temporal_stability']['return_sign_comparable_cases']}.",
        f"- Regime Support/Margin persistence: **{'PASS' if summary['strength_persistence']['pass'] else 'FAIL'}**.",
        f"- Incremental trading utility: **{'PASS' if summary['incremental_trading_utility']['pass'] else 'FAIL'}** — beats {summary['incremental_trading_utility']['baseline_wins']}/3 baselines on both annualized return and Sharpe.",
        "",
        "## Path separation",
        "",
    ]
    for metric, value in summary["path_separation_median_eta_squared"].items():
        lines.append(f"- {metric}: median eta-squared **{'—' if value is None else f'{value:.3f}'}**")

    lines.extend(["", "## Per-pair state occupancy", "", "| Pair | Neutral | AccFam | Markup | DistFam | Markdown | Material states |", "|---|---:|---:|---:|---:|---:|---:|"])
    for pair, row in report["pairs"].items():
        shares = row["state_shares"]
        lines.append(
            f"| {pair} | {row['neutral_share']*100:.1f}% | {shares['1']*100:.1f}% | {shares['2']*100:.1f}% | "
            f"{shares['3']*100:.1f}% | {shares['4']*100:.1f}% | {row['material_state_count']}/4 |"
        )

    lines.extend(["", "## Frozen-response trading utility — equal-weight three-pair aggregate", "", "| Strategy | Net ann. return | Vol | Sharpe | Max DD | Exposure |", "|---|---:|---:|---:|---:|---:|"])
    for name in ("wyckoff_v06_frozen_response", "sma200", "momentum60", "donchian55", "always_flat"):
        row = report["equal_weight_three_pair_strategies"][name]
        pct = lambda x: "—" if x is None else f"{x*100:.2f}%"
        sharpe = "—" if row["annualized_sharpe_zero_cash"] is None else f"{row['annualized_sharpe_zero_cash']:.2f}"
        lines.append(
            f"| {name} | {pct(row['net_annualized_return'])} | {pct(row['annualized_volatility'])} | {sharpe} | "
            f"{pct(row['max_drawdown'])} | {row['average_absolute_exposure']*100:.1f}% |"
        )

    lines.extend(["", "## Strength persistence", ""])
    for field, row in summary["strength_persistence"]["fields"].items():
        rate = "—" if row["rate"] is None else f"{row['rate']*100:.1f}%"
        lines.append(f"- `{field}`: high bin persists more than low in **{row['high_better_cases']}/{row['comparable_cases']}** comparable pair×horizon cases ({rate}).")

    lines.extend(["", "Boundary: this is a one-shot independent cross-market result. Any further redesign requires a new untouched sample.", ""])
    return "\n".join(lines)


def parse_args() -> argparse.Namespace:
    here = Path(__file__).resolve().parent
    parser = argparse.ArgumentParser()
    parser.add_argument("--manifest", type=Path, default=here / "data" / "issue-57-phase-e-holdout-manifest.json")
    parser.add_argument("--opening-record", type=Path, default=here / "reports" / "issue-57-phase-e-opening.md")
    parser.add_argument("--implementation-gate", type=Path, default=here / "reports" / "issue-57-pine-implementation-gate.md")
    parser.add_argument("--json-output", type=Path)
    parser.add_argument("--md-output", type=Path)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    report = build_report(args.manifest, args.opening_record, args.implementation_gate)
    if args.json_output:
        args.json_output.parent.mkdir(parents=True, exist_ok=True)
        args.json_output.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    if args.md_output:
        args.md_output.parent.mkdir(parents=True, exist_ok=True)
        args.md_output.write_text(render_markdown(report), encoding="utf-8")
    print(json.dumps(report["summary"], indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
