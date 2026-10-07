#!/usr/bin/env python3
"""Issue #78 A4: causal Core-2 translation (prior-only ranks) before OOS4.

Discovery analyzer, not fresh OOS validation. OOS3 snapshot ONLY;
OOS4 is never contacted (`oos4_touched=false`).

Raw axes reused exactly from frozen A1/A2 builders by import:
  dir_structure, dir_velocity, extension = abs(dir_velocity).
Retrospective full-history ranks (A2 frame) are used ONLY for fidelity
diagnostics, never as state inputs.

Frozen causal percentile (preregistered): for bar t, over the N prior
ready values of the same stock (expanding window, self excluded):
  pct(t) = (count_strictly_less + 0.5 * count_equal) / N
State unavailable when N < 252 (WARMUP_MIN). Evaluable bars are ready
bars with N >= 252.
"""
from __future__ import annotations

import argparse
import bisect
import json
import math
from pathlib import Path

import numpy as np
import pandas as pd

import analyze_issue78_factorized_classifier_discovery as a0
import analyze_issue78_direction_decomposition_a1 as a1
import analyze_issue78_supply_demand_a2 as a2
from audit_issue119_bbg_oos2_snapshot import audit_snapshot
from smoke_issue119_frozen_classifier import FROZEN_CLASSIFIER_BLOB, load_classifier

EXPECTED_FIGI_SET_SHA = a0.EXPECTED_FIGI_SET_SHA
HORIZONS = a0.HORIZONS
MIN_CELL_BARS = a0.MIN_CELL_BARS
MIN_AGG_STOCKS = a0.MIN_AGG_STOCKS
BLOCKS = a1.BLOCKS
BLOCK_LABELS = a1.BLOCK_LABELS

WARMUP_MIN = 252

_tail_stats = a1._tail_stats
append_cell = a1.append_cell
_block_masks = a1._block_masks
aggregate_a1_cells = a1.aggregate_a1_cells
paired_deltas = a1.paired_deltas


def causal_prior_pct(values: np.ndarray, ready: np.ndarray) -> np.ndarray:
    """Prior-only expanding percentile with tie averaging (frozen formula).

    Reference set at bar t: ready values strictly before t. Self never
    participates. NaN for non-ready bars and when N_prior < WARMUP_MIN.
    """
    values = np.asarray(values, dtype=float)
    ready = np.asarray(ready, dtype=bool)
    out = np.full(len(values), np.nan, dtype=float)
    prior: list = []
    n_prior = 0
    for t in range(len(values)):
        if ready[t] and np.isfinite(values[t]):
            if n_prior >= WARMUP_MIN:
                x = values[t]
                left = bisect.bisect_left(prior, x)
                right = bisect.bisect_right(prior, x)
                out[t] = (left + 0.5 * (right - left)) / n_prior
            bisect.insort(prior, values[t])
            n_prior += 1
    return out


def add_causal_ranks(frame: pd.DataFrame) -> pd.DataFrame:
    out = frame.copy()
    ready = out["ready"].to_numpy(bool)
    out["rank_c_struct"] = causal_prior_pct(
        out["dir_structure"].to_numpy(float), ready
    )
    out["rank_c_ext"] = causal_prior_pct(
        out["extension"].to_numpy(float), ready
    )
    out["causal_ready"] = (
        ready
        & np.isfinite(out["rank_c_struct"].to_numpy(float))
        & np.isfinite(out["rank_c_ext"].to_numpy(float))
    )
    return out


def _causal_masks(frame: pd.DataFrame, hard: bool) -> dict:
    rs = frame["rank_c_struct"].to_numpy(float)
    re_ = frame["rank_c_ext"].to_numpy(float)
    ok = frame["causal_ready"].to_numpy(bool)
    if hard:
        bull = ok & (rs >= 0.80)
        bear = ok & (rs <= 0.20)
        low_ext = re_ <= 0.20
        high_ext = re_ >= 0.80
    else:
        bull = ok & (rs >= 0.70)
        bear = ok & (rs <= 0.30)
        low_ext = re_ <= 0.30
        high_ext = re_ >= 0.70
    return {
        "bull_low": (bull & low_ext, 1.0),
        "bull_high": (bull & high_ext, 1.0),
        "bear_low": (bear & low_ext, -1.0),
        "bear_high": (bear & high_ext, -1.0),
    }


def _retro_masks(frame: pd.DataFrame) -> dict:
    ready = frame["ready"].to_numpy(bool)
    rs = frame["rank_dir_structure"].to_numpy(float)
    re_ = frame["rank_extension"].to_numpy(float)
    return {
        "bull_low": ready & (rs >= 0.80) & (re_ <= 0.20),
        "bull_high": ready & (rs >= 0.80) & (re_ >= 0.80),
        "bear_low": ready & (rs <= 0.20) & (re_ <= 0.20),
        "bear_high": ready & (rs <= 0.20) & (re_ >= 0.80),
    }


def econ_cells(figi: str, frame: pd.DataFrame, meta: dict) -> list[dict]:
    rows = []
    blocks = _block_masks_causal(frame)
    for suffix, hard in (("", True), ("_rel", False)):
        for state, (mask, sign) in _causal_masks(frame, hard).items():
            for h in HORIZONS:
                fwd = frame[f"fwd_{h}"].to_numpy(float)
                for block, bmask in blocks.items():
                    append_cell(
                        rows,
                        figi=figi,
                        block=block,
                        horizon=h,
                        test=f"core{suffix}",
                        state=state,
                        mask=bmask & mask,
                        forward=fwd,
                        direction=sign,
                        meta=meta,
                    )
    return rows


def _block_masks_causal(frame: pd.DataFrame) -> dict:
    ready = frame["causal_ready"].to_numpy(bool)
    dates_block = frame["block"].to_numpy()
    masks = {"ALL": ready}
    for name, _, _ in BLOCKS:
        masks[name] = ready & (dates_block == name)
    return masks


def fidelity_rows(figi: str, frame: pd.DataFrame, meta: dict) -> list[dict]:
    """Per-stock causal-vs-retrospective fidelity (diagnostic only)."""
    rows = []
    evaluable = frame["causal_ready"].to_numpy(bool)
    if evaluable.sum() < MIN_CELL_BARS:
        return rows
    retro = _retro_masks(frame)
    retro_label = np.full(len(frame), "non-core", dtype=object)
    for state, mask in retro.items():
        retro_label[mask & evaluable] = state
    causal = _causal_masks(frame, True)
    causal_label = np.full(len(frame), "non-core", dtype=object)
    for state, (mask, _) in causal.items():
        causal_label[mask] = state
    for score, ccol, rcol in (
        ("dir_structure", "rank_c_struct", "rank_dir_structure"),
        ("extension", "rank_c_ext", "rank_extension"),
    ):
        cc = frame[ccol].to_numpy(float)[evaluable]
        rc = frame[rcol].to_numpy(float)[evaluable]
        pair = pd.DataFrame({"c": cc, "r": rc}).dropna()
        if len(pair) >= MIN_CELL_BARS:
            rho = pair["c"].corr(pair["r"], method="spearman")
            mae = float(np.mean(np.abs(pair["c"] - pair["r"])))
        else:
            rho, mae = math.nan, math.nan
        rows.append(
            {
                "figi": figi,
                "metric": f"{score}_pct_spearman",
                "value": float(rho),
                "bars": int(len(pair)),
                **meta,
            }
        )
        rows.append(
            {
                "figi": figi,
                "metric": f"{score}_pct_mae",
                "value": mae,
                "bars": int(len(pair)),
                **meta,
            }
        )
    for state in ("bull_low", "bull_high", "bear_low", "bear_high"):
        cset = set(np.flatnonzero(causal_label == state).tolist())
        rset = set(np.flatnonzero(retro_label == state).tolist())
        union = cset | rset
        jaccard = len(cset & rset) / len(union) if union else math.nan
        rows.append(
            {
                "figi": figi,
                "metric": f"jaccard_{state}",
                "value": float(jaccard),
                "bars": int(len(cset)),
                **meta,
            }
        )
    # Confusion counts causal(row) x retro(col).
    labels = ("bull_low", "bull_high", "bear_low", "bear_high", "non-core")
    for c_lab in labels:
        for r_lab in labels:
            n = int(
                ((causal_label == c_lab) & (retro_label == r_lab)).sum()
            )
            rows.append(
                {
                    "figi": figi,
                    "metric": f"confusion_{c_lab}_x_{r_lab}",
                    "value": float(n),
                    "bars": int((causal_label == c_lab).sum()),
                    **meta,
                }
            )
    return rows


def fidelity_summary(per_stock: pd.DataFrame) -> pd.DataFrame:
    rows = []
    if per_stock.empty:
        return pd.DataFrame()
    for metric, group in per_stock.groupby("metric", sort=True):
        if metric.startswith("confusion_"):
            vals = pd.to_numeric(group["value"], errors="coerce")
            rows.append(
                {
                    "metric": metric,
                    "kind": "count_sum",
                    "stocks": int(len(vals)),
                    "equal_stock_mean": float(vals.mean()),
                    "total": int(vals.sum()),
                }
            )
            continue
        vals = pd.to_numeric(group["value"], errors="coerce")
        vals = vals[np.isfinite(vals)]
        rows.append(
            {
                "metric": metric,
                "kind": "mean",
                "stocks": int(len(vals)),
                "equal_stock_mean": (
                    float(vals.mean()) if len(vals) else math.nan
                ),
                "median_stock": (
                    float(vals.median()) if len(vals) else math.nan
                ),
            }
        )
    return pd.DataFrame(rows)


PAIRED_SPECS = {
    "core": ("bull_low", "bull_high"),
    "core_bear": ("bear_low", "bear_high"),
    "core_rel": ("bull_low", "bull_high"),
    "core_rel_bear": ("bear_low", "bear_high"),
}


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--universe", type=Path, required=True)
    ap.add_argument("--manifest", type=Path, required=True)
    ap.add_argument("--raw-dir", type=Path, required=True)
    ap.add_argument(
        "--classifier",
        type=Path,
        default=Path("generated/wyckoff-issue78-rc-python.py"),
    )
    ap.add_argument("--out", type=Path, required=True)
    args = ap.parse_args()

    for contact in (args.universe, args.manifest, args.raw_dir):
        assert "oos4" not in str(contact).lower(), "OOS4 firewall"
    audit = audit_snapshot(args.universe, args.manifest, args.raw_dir)
    if not audit["pass"]:
        raise SystemExit("snapshot audit failed")

    universe = pd.read_csv(args.universe)
    if len(universe) != 300 or universe["figi"].nunique() != 300:
        raise AssertionError("universe membership drift")
    cohort_sha = a0.figi_set_sha(universe)
    if cohort_sha != EXPECTED_FIGI_SET_SHA:
        raise AssertionError(f"OOS3 FIGI-set drift: {cohort_sha}")

    classifier, blob = load_classifier(args.classifier)
    if blob != FROZEN_CLASSIFIER_BLOB:
        raise AssertionError("frozen classifier blob drift")

    coverage = []
    econ_rows = []
    fid_rows = []

    for i, meta_row in enumerate(universe.itertuples(index=False), start=1):
        figi = str(meta_row.figi)
        raw_path = args.raw_dir / f"{figi}.csv.gz"
        if not raw_path.exists():
            raise FileNotFoundError(raw_path)
        raw = pd.read_csv(raw_path)
        frame = add_causal_ranks(
            a2.add_within_stock_ranks(a2.build_sd_frame(raw, classifier))
        )
        meta = {
            "sector": str(meta_row.sector),
            "sleeve": str(meta_row.sleeve),
        }
        coverage.append(
            {
                "figi": figi,
                "ticker": str(meta_row.ticker),
                **meta,
                "raw_rows": int(len(frame)),
                "eligible_rows": int(frame["eligible"].sum()),
                "causal_ready_rows": int(frame["causal_ready"].sum()),
            }
        )
        econ_rows.extend(econ_cells(figi, frame, meta))
        fid_rows.extend(fidelity_rows(figi, frame, meta))
        print(
            f"[causal-core2-a4] "
            f"{i}/{len(universe)} {meta_row.ticker} "
            f"eligible={int(frame['eligible'].sum())} "
            f"causal_ready={int(frame['causal_ready'].sum())}",
            flush=True,
        )

    econ_stock = pd.DataFrame(econ_rows)
    econ_summary = aggregate_a1_cells(
        econ_stock, ["test", "state", "block", "horizon"]
    )
    # Paired contrasts need (good,bad) state pairs per test; remap bear.
    bear_stock = econ_stock[
        econ_stock["state"].str.startswith("bear")
    ].assign(test=lambda d: d["test"] + "_bear")
    pair_stock, pair_summary = paired_deltas(
        pd.concat([econ_stock, bear_stock], ignore_index=True),
        PAIRED_SPECS,
    )
    fid_stock = pd.DataFrame(fid_rows)
    fid_summary = fidelity_summary(fid_stock)

    summary = {
        "integrity": {
            "issue": 78,
            "study": "Causal Core-2 Translation A4",
            "role": (
                "post-outcome architecture discovery; "
                "not fresh OOS validation"
            ),
            "classifier_blob": blob,
            "figi_set_sha256": cohort_sha,
            "stocks": int(len(universe)),
            "raw_files": int(audit["completed"]),
            "raw_failures": int(audit["failures"]),
            "horizons": list(HORIZONS),
            "blocks": list(BLOCK_LABELS),
            "min_cell_bars": MIN_CELL_BARS,
            "min_aggregate_stocks": MIN_AGG_STOCKS,
            "oos4_touched": False,
        },
        "a4_frozen": {
            "percentile": "(less + 0.5*equal)/N_prior, prior-ready only",
            "warmup_min_prior_ready": WARMUP_MIN,
            "hard": "struct>=.80/<=.20, ext<=.20/>=.80",
            "relaxed": "70/30",
        },
        "notes": [
            "OOS3 is deliberately reused for discovery "
            "under the 2026-10-05 amendment.",
            "No result from this run is fresh OOS evidence.",
            "Retrospective A3 bins are fidelity reference only, not truth.",
        ],
    }

    args.out.mkdir(parents=True, exist_ok=True)
    for name, df in (
        ("coverage.csv", pd.DataFrame(coverage)),
        ("econ_per_stock.csv", econ_stock),
        ("econ_summary.csv", econ_summary),
        ("paired_delta_per_stock.csv", pair_stock),
        ("paired_delta_summary.csv", pair_summary),
        ("fidelity_per_stock.csv", fid_stock),
        ("fidelity_summary.csv", fid_summary),
    ):
        df.to_csv(args.out / name, index=False)
    (args.out / "summary.json").write_text(
        json.dumps(summary, indent=2, default=str) + "\n", encoding="utf-8"
    )
    print(json.dumps(summary, indent=2, default=str))


if __name__ == "__main__":
    main()
