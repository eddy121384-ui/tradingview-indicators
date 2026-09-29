#!/usr/bin/env python3
"""Issue #121 Phase 1 — ultra-long-history rematch of rejected mappings.

This evaluator reuses the frozen Issue #91 HMRA-v0.1 and source pipeline.
No macro-state parameter is changed here.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import tempfile
from pathlib import Path

import numpy as np
import pandas as pd

from issue_91_phase2_asset_validation import run as run_issue91_phase2

HERE = Path(__file__).resolve().parent
PREREG = HERE / "decisions" / "issue-121-phase1-long-history-rematch-preregistered.md"

SPREADS = {
    "equity_minus_treasury": {
        "left": "equity",
        "right": "treasury",
        "min_return_year": 1928,
    },
    "treasury_minus_cash": {
        "left": "treasury",
        "right": "cash",
        "min_return_year": 1928,
    },
    "gold_minus_cash": {
        "left": "gold",
        "right": "cash",
        "min_return_year": 1975,
    },
}
BOOTSTRAP_REPS = 10_000


def stable_seed(*parts: object) -> int:
    payload = "|".join(str(x) for x in parts).encode("utf-8")
    return int.from_bytes(hashlib.sha256(payload).digest()[:8], "big") & 0xFFFFFFFF


def sign_of(value: float | None) -> int:
    if value is None or not np.isfinite(value) or abs(value) < 1e-15:
        return 0
    return 1 if value > 0 else -1


def ci_excludes_zero(summary: dict) -> bool:
    lo = summary["ci_low"]
    hi = summary["ci_high"]
    return bool(
        np.isfinite(lo)
        and np.isfinite(hi)
        and ((lo > 0 and hi > 0) or (lo < 0 and hi < 0))
    )


def summarize(values: pd.Series | np.ndarray, *, seed: int) -> dict:
    arr = np.asarray(values, dtype=float)
    arr = arr[np.isfinite(arr)]
    n = int(len(arr))
    if n == 0:
        return {
            "n": 0,
            "mean": math.nan,
            "median": math.nan,
            "std": math.nan,
            "positive_fraction": math.nan,
            "ci_low": math.nan,
            "ci_high": math.nan,
        }
    rng = np.random.default_rng(seed)
    idx = rng.integers(0, n, size=(BOOTSTRAP_REPS, n))
    means = arr[idx].mean(axis=1)
    lo, hi = np.quantile(means, [0.025, 0.975])
    return {
        "n": n,
        "mean": float(arr.mean()),
        "median": float(np.median(arr)),
        "std": float(np.std(arr, ddof=1)) if n >= 2 else math.nan,
        "positive_fraction": float(np.mean(arr > 0)),
        "ci_low": float(lo),
        "ci_high": float(hi),
    }


def validate_prereg() -> None:
    s = PREREG.read_text(encoding="utf-8")
    required = [
        "PREREGISTERED BEFORE ISSUE #121 REMATCH CLASSIFICATIONS",
        "state_t -> annual spread return_{t+2}",
        "Equity minus Treasury",
        "Treasury minus Cash",
        "Gold minus Cash",
        "strongest-era share <= 0.50",
        "No Issue #121 rematch classification had been computed",
    ]
    missing = [x for x in required if x not in s]
    if missing:
        raise RuntimeError(f"Issue #121 preregistration guard failed: {missing}")


def load_issue91_evidence() -> tuple[pd.DataFrame, pd.DataFrame, dict]:
    with tempfile.TemporaryDirectory(prefix="issue121-issue91-") as td:
        out = Path(td)
        manifest = run_issue91_phase2(out)
        structural = pd.read_csv(out / "issue-91-phase2-structural-joined.csv")
        causal = pd.read_csv(out / "issue-91-phase2-causal-joined.csv")
    if manifest["hmra_freeze_validated_before_asset_join"] is not True:
        raise RuntimeError("Issue #91 HMRA freeze validation did not pass")
    if manifest["pairings"]["structural"]["rows"] != 98:
        raise RuntimeError("Issue #91 structural row count drift")
    if manifest["pairings"]["strict_causal_t_plus_2"]["last_return_year"] != 2025:
        raise RuntimeError("Issue #91 causal horizon drift")
    return structural, causal, manifest


def add_spread(frame: pd.DataFrame, spread: str) -> pd.DataFrame:
    cfg = SPREADS[spread]
    out = frame.loc[frame["return_year"].ge(cfg["min_return_year"])].copy()
    out["spread"] = pd.to_numeric(out[cfg["left"]], errors="coerce") - pd.to_numeric(
        out[cfg["right"]], errors="coerce"
    )
    return out.loc[np.isfinite(out["spread"])].copy()


def era_diagnostics(sample: pd.DataFrame, candidate_sign: int, spread: str, regime: str) -> dict:
    stats = {}
    eligible = []
    for era_name, g in sample.groupby("era", sort=True):
        st = summarize(
            g["spread"],
            seed=stable_seed(121, "era", spread, regime, era_name),
        )
        stats[str(era_name)] = st
        if st["n"] >= 3:
            eligible.append(str(era_name))

    same_sign = 0
    opposite_large = []
    for era_name in eligible:
        m = stats[era_name]["mean"]
        s = sign_of(m)
        if candidate_sign != 0 and s == candidate_sign:
            same_sign += 1
        if candidate_sign != 0 and s == -candidate_sign and abs(m) > 0.05:
            opposite_large.append(era_name)

    return {
        "stats": stats,
        "eligible_eras": eligible,
        "eligible_era_count": int(len(eligible)),
        "same_sign_eligible_eras": int(same_sign),
        "opposite_large_eras": opposite_large,
    }


def leave_one_era_out(sample: pd.DataFrame, candidate_sign: int) -> dict:
    rows = []
    for era_name in sorted(sample["era"].dropna().astype(str).unique()):
        removed = int(sample["era"].astype(str).eq(era_name).sum())
        left = sample.loc[~sample["era"].astype(str).eq(era_name)].copy()
        if len(left) < 8:
            rows.append({
                "omitted_era": era_name,
                "removed_n": removed,
                "remaining_n": int(len(left)),
                "evaluable": False,
                "mean": math.nan,
                "sign_flip": None,
            })
            continue
        m = float(left["spread"].mean())
        rows.append({
            "omitted_era": era_name,
            "removed_n": removed,
            "remaining_n": int(len(left)),
            "evaluable": True,
            "mean": m,
            "sign_flip": bool(candidate_sign != 0 and sign_of(m) != candidate_sign),
        })
    evaluable = [r for r in rows if r["evaluable"]]
    return {
        "rows": rows,
        "evaluable_count": int(len(evaluable)),
        "any_sign_flip": bool(any(r["sign_flip"] for r in evaluable)),
    }


def era_concentration(sample: pd.DataFrame) -> dict:
    sums = sample.groupby("era", sort=True)["spread"].sum()
    contributions = sums.abs()
    denom = float(contributions.sum())
    if denom <= 0 or not np.isfinite(denom):
        return {
            "by_era_abs_sum": {str(k): float(v) for k, v in contributions.items()},
            "strongest_era": None,
            "strongest_era_share": math.nan,
        }
    strongest = str(contributions.idxmax())
    share = float(contributions.max() / denom)
    return {
        "by_era_abs_sum": {str(k): float(v) for k, v in contributions.items()},
        "strongest_era": strongest,
        "strongest_era_share": share,
    }


def classify_cell(
    structural_sample: pd.DataFrame,
    causal_sample: pd.DataFrame,
    *,
    spread: str,
    regime: str,
) -> dict:
    structural = summarize(
        structural_sample["spread"],
        seed=stable_seed(121, "structural", spread, regime),
    )
    causal = summarize(
        causal_sample["spread"],
        seed=stable_seed(121, "causal", spread, regime),
    )

    causal_sign = sign_of(causal["mean"])
    structural_sign = sign_of(structural["mean"])
    causal_ci = ci_excludes_zero(causal)
    structural_ci = ci_excludes_zero(structural)

    eras = era_diagnostics(causal_sample, causal_sign, spread, regime)
    loeo = leave_one_era_out(causal_sample, causal_sign)
    concentration = era_concentration(causal_sample)

    sufficient = bool(
        causal["n"] >= 8
        and eras["eligible_era_count"] >= 2
        and loeo["evaluable_count"] >= 1
        and np.isfinite(concentration["strongest_era_share"])
    )

    gates = {
        "1_causal_n_ge_8": causal["n"] >= 8,
        "2_causal_mean_nonzero": causal_sign != 0,
        "3_causal_ci_excludes_zero": causal_ci,
        "4_structural_same_sign": structural_sign != 0 and structural_sign == causal_sign,
        "5_at_least_2_eligible_eras": eras["eligible_era_count"] >= 2,
        "6_at_least_2_eligible_eras_same_sign": eras["same_sign_eligible_eras"] >= 2,
        "7_no_large_opposite_era": len(eras["opposite_large_eras"]) == 0,
        "8_leave_one_era_out_never_flips": loeo["evaluable_count"] >= 1 and not loeo["any_sign_flip"],
        "9_leave_one_era_out_evaluable": loeo["evaluable_count"] >= 1,
        "10_strongest_era_share_le_50pct": (
            np.isfinite(concentration["strongest_era_share"])
            and concentration["strongest_era_share"] <= 0.50
        ),
    }

    if not sufficient:
        classification = "inconclusive_long_history_sample"
    elif all(gates.values()):
        classification = "revived_long_history_candidate"
    elif structural["n"] >= 8 and structural_ci and (
        not causal_ci or structural_sign != causal_sign
    ):
        classification = "long_history_structural_but_timing_unstable"
    elif causal["n"] >= 8 and causal_ci and structural_sign == causal_sign:
        classification = "long_history_era_dependent"
    else:
        classification = "remains_unconfirmed"

    direction = None
    if causal_sign > 0:
        direction = f"{SPREADS[spread]['left']} > {SPREADS[spread]['right']}"
    elif causal_sign < 0:
        direction = f"{SPREADS[spread]['right']} > {SPREADS[spread]['left']}"

    return {
        "spread": spread,
        "core_regime": regime,
        "classification": classification,
        "causal_direction": direction,
        "structural": structural,
        "causal": causal,
        "era_diagnostics": eras,
        "leave_one_era_out": loeo,
        "era_concentration": concentration,
        "gates": gates,
    }


def run(output_dir: Path) -> dict:
    validate_prereg()
    output_dir.mkdir(parents=True, exist_ok=True)
    structural_raw, causal_raw, issue91_manifest = load_issue91_evidence()

    cells = (
        structural_raw[["growth_state", "inflation_state", "core_regime"]]
        .drop_duplicates()
        .sort_values(["growth_state", "inflation_state", "core_regime"])
        .reset_index(drop=True)
    )
    if len(cells) != 9:
        raise RuntimeError(f"expected 9 HMRA cells, got {len(cells)}")

    results = []
    for spread in SPREADS:
        s = add_spread(structural_raw, spread)
        c = add_spread(causal_raw, spread)
        for _, cell in cells.iterrows():
            regime = str(cell["core_regime"])
            ss = s.loc[s["core_regime"].eq(regime)].copy()
            cc = c.loc[c["core_regime"].eq(regime)].copy()
            result = classify_cell(ss, cc, spread=spread, regime=regime)
            result["growth_state"] = str(cell["growth_state"])
            result["inflation_state"] = str(cell["inflation_state"])
            results.append(result)

    rows = []
    for r in results:
        rows.append({
            "spread": r["spread"],
            "growth_state": r["growth_state"],
            "inflation_state": r["inflation_state"],
            "core_regime": r["core_regime"],
            "classification": r["classification"],
            "causal_direction": r["causal_direction"],
            "structural_n": r["structural"]["n"],
            "structural_mean": r["structural"]["mean"],
            "structural_ci_low": r["structural"]["ci_low"],
            "structural_ci_high": r["structural"]["ci_high"],
            "causal_n": r["causal"]["n"],
            "causal_mean": r["causal"]["mean"],
            "causal_ci_low": r["causal"]["ci_low"],
            "causal_ci_high": r["causal"]["ci_high"],
            "eligible_eras": r["era_diagnostics"]["eligible_era_count"],
            "same_sign_eras": r["era_diagnostics"]["same_sign_eligible_eras"],
            "opposite_large_eras": "|".join(r["era_diagnostics"]["opposite_large_eras"]),
            "leaveout_evaluable": r["leave_one_era_out"]["evaluable_count"],
            "leaveout_any_sign_flip": r["leave_one_era_out"]["any_sign_flip"],
            "strongest_era": r["era_concentration"]["strongest_era"],
            "strongest_era_share": r["era_concentration"]["strongest_era_share"],
        })
    table = pd.DataFrame(rows)
    table_path = output_dir / "issue-121-rematch-table.csv"
    table.to_csv(table_path, index=False, float_format="%.12g")

    classification_counts = table["classification"].value_counts().sort_index().to_dict()
    revived = table.loc[table["classification"].eq("revived_long_history_candidate")].copy()
    revived_records = revived[
        [
            "spread",
            "core_regime",
            "causal_direction",
            "causal_n",
            "causal_mean",
            "causal_ci_low",
            "causal_ci_high",
            "structural_mean",
            "eligible_eras",
            "same_sign_eras",
            "strongest_era_share",
        ]
    ].to_dict(orient="records")

    result = {
        "schema_version": 1,
        "issue": 121,
        "phase": "phase1-ultra-long-history-rematch",
        "source_backbone": {
            "issue_91_hmra_freeze_validated": bool(
                issue91_manifest["hmra_freeze_validated_before_asset_join"]
            ),
            "damodaran_raw_sha256": issue91_manifest["sources"]["damodaran"]["raw_sha256"],
            "jst_raw_sha256": issue91_manifest["sources"]["jst"]["raw_sha256"],
            "structural_rows": issue91_manifest["pairings"]["structural"]["rows"],
            "causal_rows": issue91_manifest["pairings"]["strict_causal_t_plus_2"]["rows"],
        },
        "spreads": list(SPREADS),
        "cells_per_spread": 9,
        "classification_counts": classification_counts,
        "revived_candidates": revived_records,
        "commodity_status": "source_gate_pending_no_payoff",
        "results": results,
        "output_table_sha256": hashlib.sha256(table_path.read_bytes()).hexdigest(),
        "production_authorized": False,
    }

    result_path = output_dir / "issue-121-result.json"
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
                "classification_counts": classification_counts,
                "revived_candidates": revived_records,
                "commodity_status": result["commodity_status"],
            },
            indent=2,
            ensure_ascii=False,
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
