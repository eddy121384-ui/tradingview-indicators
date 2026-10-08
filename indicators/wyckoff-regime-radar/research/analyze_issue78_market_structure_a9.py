#!/usr/bin/env python3
"""Issue #78 A9: market-structure dimension audit + HMM benchmark.

Discovery on recovered OOS3 under the frozen A9-r2 preregistration
(`decisions/issue-78-market-structure-a9-preregistration.md`). D3
(Compression/Expansion: 20-day realised log-return volatility, NATR20 as the
single robustness measure) and D4 (Path Efficiency: ER20) are new simple
causal descriptors evaluated against frozen Core-2 (reused by import, never
modified). The HMM is a benchmark only; the Atlas stays primary.

All percentiles reuse the frozen A4 `causal_prior_pct` (same-stock,
prior-ready only, current bar excluded, 252 minimum, tie averaging). All
eligibility reuses the frozen A2 `ready` gate. No scans, no tuning, no ML
beyond the preregistered pooled diagonal-Gaussian EM (numpy only).
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
from pathlib import Path

import numpy as np
import pandas as pd

import analyze_issue78_factorized_classifier_discovery as a0
import analyze_issue78_direction_decomposition_a1 as a1
import analyze_issue78_supply_demand_a2 as a2
import analyze_issue78_causal_core2_a4 as a4
from audit_issue119_bbg_oos2_snapshot import audit_snapshot
from smoke_issue119_frozen_classifier import FROZEN_CLASSIFIER_BLOB, load_classifier

EXPECTED_FIGI_SET_SHA = a0.EXPECTED_FIGI_SET_SHA
HORIZONS = a0.HORIZONS
MIN_CELL_BARS = a0.MIN_CELL_BARS
MIN_AGG_STOCKS = a0.MIN_AGG_STOCKS
BLOCKS = a1.BLOCKS
BLOCK_LABELS = a1.BLOCK_LABELS

WARMUP_MIN = 252
D3_RV_SPAN = 20
D3_ATR_SPAN = 20
ER_SPAN = 20
MI_BINS = 10

LOW_MAX = 0.30
HIGH_MIN = 0.70
HARD_LOW = 0.20
HARD_HIGH = 0.80

NOVEL_SPEARMAN_MAX = 0.50
NOVEL_MI_MAX = 0.10
PATH_SD_FRAC = 0.10
PATH_SIGN_FRAC = 0.60
TRIM_FRAC = 0.01

HMM_KS = (2, 3, 4, 5)
HMM_TRAIN_END = "2015-01-01"
HMM_MAX_ITER = 200
HMM_TOL = 1e-6
HMM_SEED = 7
HMM_MIN_OCC = 0.05
HMM_MIN_PERSIST = 0.80
HMM_MAX_DRIFT = 1.0
HMM_CONVERGE_C = 2.0 / 3.0
HMM_CONVERGE_NMI = 0.25
HMM_UNSTABLE_FRAC = 2.0 / 3.0

PATH_PROPS = ("fwd", "lret", "abs", "fvol", "mfe", "mae", "cont", "rev")
GATE_PROPS = tuple(f"{p}_10" for p in PATH_PROPS) + ("futer_20",)
DIMS = ("d3", "d3_rob", "d4")
DIM_RANK_COL = {"d3": "rank_c_d3", "d3_rob": "rank_c_d3_rob", "d4": "rank_c_d4"}
DIM_LABEL = {
    "d3": "D3 Compression/Expansion (primary: RV20)",
    "d3_rob": "D3 robustness (NATR20)",
    "d4": "D4 Path Efficiency (ER20)",
}

_tail_stats = a1._tail_stats
causal_prior_pct = a4.causal_prior_pct
BLOCK_NAMES = tuple(name for name, _, _ in BLOCKS)


def _numeric(frame: pd.DataFrame, name: str) -> np.ndarray:
    return pd.to_numeric(frame[name], errors="coerce").to_numpy(float)


# --------------------------------------------------------------------------
# Frozen D3 / D4 primitives
# --------------------------------------------------------------------------

def wilder_atr(
    high: np.ndarray, low: np.ndarray, close: np.ndarray,
    span: int = D3_ATR_SPAN,
) -> np.ndarray:
    """Gap-safe Wilder ATR (RMA, alpha=1/span, SMA seed), strictly causal.

    The last known close carries the true range across missing bars and the
    running ATR state survives a missing bar (a missing bar emits NaN and
    does not erase the state). Without the carry, a single interior NaN close
    permanently NaN-ed the rest of a stock's ATR series.
    """
    high = np.asarray(high, dtype=float)
    low = np.asarray(low, dtype=float)
    close = np.asarray(close, dtype=float)
    n = len(close)
    prev_close = pd.Series(close).ffill().shift(1).to_numpy(float)
    valid_tr = (
        np.isfinite(high)
        & np.isfinite(low)
        & (high > 0)
        & (low > 0)
        & (high >= low)
    )
    tr = np.maximum.reduce(
        [
            high - low,
            np.abs(high - prev_close),
            np.abs(low - prev_close),
        ]
    )
    tr = np.where(valid_tr, tr, np.nan)
    atr = np.full(n, np.nan)
    buffer: list[float] = []
    state = math.nan
    alpha = 1.0 / span
    for t in range(n):
        x = tr[t]
        if not np.isfinite(x):
            continue
        if not np.isfinite(state):
            buffer.append(float(x))
            if len(buffer) == span:
                state = float(np.mean(buffer))
                atr[t] = state
            continue
        state = state * (1.0 - alpha) + float(x) * alpha
        atr[t] = state
    return atr


def realized_vol(close: np.ndarray, span: int = D3_RV_SPAN) -> np.ndarray:
    """Sample stdev (ddof=1) of the last `span` daily log-return increments."""
    close = np.asarray(close, dtype=float)
    logc = np.where(close > 0, np.log(np.where(close > 0, close, 1.0)), np.nan)
    step = pd.Series(logc).diff()
    return (
        step.rolling(span, min_periods=span)
        .std(ddof=1)
        .to_numpy(float)
    )


def efficiency_ratio(close: np.ndarray, span: int = ER_SPAN) -> np.ndarray:
    """|close[t]-close[t-span]| / sum |1-bar moves| over the same span."""
    close = np.asarray(close, dtype=float)
    step = np.abs(np.diff(close, prepend=np.nan))
    num = np.abs(close - pd.Series(close).shift(span).to_numpy(float))
    den = (
        pd.Series(step)
        .rolling(span, min_periods=span)
        .sum()
        .to_numpy(float)
    )
    with np.errstate(invalid="ignore", divide="ignore"):
        out = np.where(
            np.isfinite(num) & np.isfinite(den) & (den > 0), num / den, np.nan
        )
    return out


def _bin_pct(rank: np.ndarray) -> np.ndarray:
    """Frozen descriptive bins: LOW <= 0.30, MID, HIGH >= 0.70."""
    rank = np.asarray(rank, dtype=float)
    lab = np.full(len(rank), "", dtype=object)
    lab[np.isfinite(rank) & (rank <= LOW_MAX)] = "LOW"
    lab[np.isfinite(rank) & (rank > LOW_MAX) & (rank < HIGH_MIN)] = "MID"
    lab[np.isfinite(rank) & (rank >= HIGH_MIN)] = "HIGH"
    return lab


def _bin_code(rank: np.ndarray) -> np.ndarray:
    rank = np.asarray(rank, dtype=float)
    code = np.full(len(rank), -1, dtype=np.int8)
    code[np.isfinite(rank) & (rank <= LOW_MAX)] = 0
    code[np.isfinite(rank) & (rank > LOW_MAX) & (rank < HIGH_MIN)] = 1
    code[np.isfinite(rank) & (rank >= HIGH_MIN)] = 2
    return code


def rank_bins(values: np.ndarray, n_bins: int = MI_BINS) -> np.ndarray:
    ranks = pd.Series(values).rank(method="average", pct=True).to_numpy(float)
    bins = np.floor(ranks * n_bins).astype(int)
    return np.clip(bins, 0, n_bins - 1)


def mutual_info(x: np.ndarray, y: np.ndarray) -> float:
    """Discrete MI in nats with Miller-Madow correction (frozen)."""
    mask = np.isfinite(x) & np.isfinite(y)
    x, y = x[mask], y[mask]
    n = len(x)
    if n < 10:
        return math.nan
    bx, by = rank_bins(x), rank_bins(y)
    joint = np.zeros((MI_BINS, MI_BINS))
    np.add.at(joint, (bx, by), 1)
    joint /= n
    px, py = joint.sum(axis=1), joint.sum(axis=0)
    mi = 0.0
    nonzero = 0
    for i in range(MI_BINS):
        for j in range(MI_BINS):
            if joint[i, j] > 0:
                nonzero += 1
                mi += joint[i, j] * math.log(joint[i, j] / (px[i] * py[j]))
    return mi + (nonzero - 1) / (2 * n)


# --------------------------------------------------------------------------
# Frame builder
# --------------------------------------------------------------------------

def build_structure_frame(raw: pd.DataFrame, classifier) -> pd.DataFrame:
    """All A9 columns for one stock: D1-D4 causal coords + frozen outcomes."""
    core = a4.add_causal_ranks(
        a2.add_within_stock_ranks(a2.build_sd_frame(raw, classifier))
    )
    frame = core.copy()
    # A2's frame does not carry raw OHLC: align a sorted copy of the input.
    ohlc = raw.copy()
    ohlc["date"] = pd.to_datetime(ohlc["date"], errors="coerce")
    ohlc = ohlc.sort_values("date").reset_index(drop=True)
    if len(ohlc) != len(frame) or not np.array_equal(
        ohlc["date"].to_numpy(), frame["date"].to_numpy()
    ):
        raise AssertionError("raw/core row drift")
    high = _numeric(ohlc, "high")
    low = _numeric(ohlc, "low")
    close = _numeric(ohlc, "close")
    logc = frame["close_coord"].to_numpy(float)
    scale = frame["scale"].to_numpy(float)
    base_ready = frame["ready"].to_numpy(bool)

    rv20 = realized_vol(close)
    atr20 = wilder_atr(high, low, close)
    natr20 = np.where(np.isfinite(atr20) & (close > 0), atr20 / close, np.nan)
    er20 = efficiency_ratio(close)

    d3_meas = base_ready & np.isfinite(rv20)
    d3_meas_rob = base_ready & np.isfinite(natr20)
    d4_meas = base_ready & np.isfinite(er20)
    frame["rv20"] = rv20
    frame["atr20"] = atr20
    frame["natr20"] = natr20
    frame["er20"] = er20
    frame["rank_c_d3"] = causal_prior_pct(rv20, d3_meas)
    frame["rank_c_d3_rob"] = causal_prior_pct(natr20, d3_meas_rob)
    frame["rank_c_d4"] = causal_prior_pct(er20, d4_meas)
    frame["d3_ready"] = d3_meas & np.isfinite(frame["rank_c_d3"].to_numpy(float))
    frame["d3_rob_ready"] = d3_meas_rob & np.isfinite(
        frame["rank_c_d3_rob"].to_numpy(float)
    )
    frame["d4_ready"] = d4_meas & np.isfinite(frame["rank_c_d4"].to_numpy(float))
    frame["atlas_ready"] = (
        frame["causal_ready"].to_numpy(bool)
        & frame["d3_ready"].to_numpy(bool)
        & frame["d4_ready"].to_numpy(bool)
    )

    # ---- frozen future-path outcomes (strictly post-observation) ----
    add_path_outcomes(frame, logc, close, scale)
    return frame


def add_path_outcomes(
    out: pd.DataFrame, logc: np.ndarray, close: np.ndarray, scale: np.ndarray
) -> None:
    """Frozen Q2 outcomes: the value at bar t uses only bars t+1..t+h."""
    logc = np.asarray(logc, dtype=float)
    close = np.asarray(close, dtype=float)
    scale = np.asarray(scale, dtype=float)
    ser = pd.Series(logc)
    step = ser.diff()
    absstep = pd.Series(np.abs(np.diff(close, prepend=np.nan)))
    trail = np.sign(logc - ser.shift(ER_SPAN).to_numpy(float))
    out["trail20"] = trail
    for h in HORIZONS:
        future = ser.shift(-h).to_numpy(float)
        lret = future - logc
        out[f"lret_{h}"] = lret
        out[f"abs_{h}"] = np.abs(lret)
        if h > 1:
            roll_std = step.rolling(h, min_periods=h).std(ddof=1)
        else:
            roll_std = pd.Series(np.full(len(ser), np.nan))
        out[f"fvol_{h}"] = roll_std.shift(-h).to_numpy(float)
        rmax = ser.rolling(h, min_periods=h).max().shift(-h).to_numpy(float)
        rmin = ser.rolling(h, min_periods=h).min().shift(-h).to_numpy(float)
        exc_hi, exc_lo = rmax - logc, rmin - logc
        with np.errstate(invalid="ignore", divide="ignore"):
            out[f"mfe_{h}"] = np.where(scale > 0, exc_hi / scale, np.nan)
            out[f"mae_{h}"] = np.where(scale > 0, exc_lo / scale, np.nan)
        out[f"mfe_raw_{h}"] = exc_hi
        out[f"mae_raw_{h}"] = exc_lo
        sgn = np.sign(lret)
        valid = (trail != 0) & (sgn != 0) & np.isfinite(lret)
        out[f"cont_{h}"] = np.where(valid, (sgn == trail).astype(float), np.nan)
        out[f"rev_{h}"] = np.where(valid, (sgn == -trail).astype(float), np.nan)
    # forward path efficiency over the next ER_SPAN bars (raw close endpoints)
    num = np.abs(pd.Series(close).shift(-ER_SPAN).to_numpy(float) - close)
    den = (
        absstep.rolling(ER_SPAN, min_periods=ER_SPAN)
        .sum()
        .shift(-ER_SPAN)
        .to_numpy(float)
    )
    out["futer_20"] = np.where(
        np.isfinite(num) & np.isfinite(den) & (den > 0), num / den, np.nan
    )


# --------------------------------------------------------------------------
# Redundancy (Q1)
# --------------------------------------------------------------------------

REDUNDANCY_PAIRS = (
    ("d3_rv_vs_struct", "rv20", "dir_structure"),
    ("d3_rv_vs_ext", "rv20", "extension"),
    ("d4_vs_struct", "er20", "dir_structure"),
    ("d4_vs_ext", "er20", "extension"),
    ("d3_rv_vs_d4", "rv20", "er20"),
    ("d3_natr_vs_struct", "natr20", "dir_structure"),
    ("d3_natr_vs_ext", "natr20", "extension"),
    ("d3_rv_vs_d3_natr", "rv20", "natr20"),
    ("d3_natr_vs_d4", "natr20", "er20"),
)


def redundancy_rows(figi: str, frame: pd.DataFrame, meta: dict) -> list[dict]:
    rows = []
    ready = frame["atlas_ready"].to_numpy(bool)
    block = frame["block"].to_numpy()
    for pair, left, right in REDUNDANCY_PAIRS:
        xa = frame[left].to_numpy(float)
        xb = frame[right].to_numpy(float)
        for scope in ("ALL",) + BLOCK_NAMES:
            mask = ready if scope == "ALL" else (ready & (block == scope))
            m = mask & np.isfinite(xa) & np.isfinite(xb)
            if m.sum() < MIN_CELL_BARS:
                continue
            rows.append(
                {
                    "figi": figi,
                    "pair": pair,
                    "scope": scope,
                    "scope_kind": "ALL" if scope == "ALL" else "block",
                    "bars": int(m.sum()),
                    "spearman": float(
                        pd.Series(xa[m]).corr(pd.Series(xb[m]), method="spearman")
                    ),
                    "mutual_info_nats": float(mutual_info(xa[m], xb[m])),
                    **meta,
                }
            )
    return rows


def redundancy_summary(per_stock: pd.DataFrame) -> pd.DataFrame:
    rows = []
    if per_stock.empty:
        return pd.DataFrame()
    for (pair, scope, kind), group in per_stock.groupby(
        ["pair", "scope", "scope_kind"], sort=True
    ):
        rho = pd.to_numeric(group["spearman"], errors="coerce").to_numpy(float)
        mi = pd.to_numeric(group["mutual_info_nats"], errors="coerce").to_numpy(float)
        rho = rho[np.isfinite(rho)]
        mi = mi[np.isfinite(mi)]
        rows.append(
            {
                "pair": pair,
                "scope": scope,
                "scope_kind": kind,
                "stocks": int(len(rho)),
                "equal_stock_mean_spearman": float(rho.mean()) if len(rho) else math.nan,
                "median_stock_spearman": float(np.median(rho)) if len(rho) else math.nan,
                "equal_stock_mean_abs_spearman": (
                    float(np.abs(rho).mean()) if len(rho) else math.nan
                ),
                "share_abs_spearman_ge_0p50": (
                    float((np.abs(rho) >= NOVEL_SPEARMAN_MAX).mean())
                    if len(rho)
                    else math.nan
                ),
                "equal_stock_mean_mi_nats": float(mi.mean()) if len(mi) else math.nan,
            }
        )
    return pd.DataFrame(rows)


# --------------------------------------------------------------------------
# Future-path cells / maps / conditional cells
# --------------------------------------------------------------------------

def _cell_stats(vals: np.ndarray, mask: np.ndarray) -> dict | None:
    stats = _tail_stats(np.asarray(vals, dtype=float)[mask])
    if stats["bars"] < MIN_CELL_BARS:
        return None
    return stats


def path_cells(figi: str, frame: pd.DataFrame, meta: dict, dim: str) -> list[dict]:
    """ALL-scope cells (3 states x 4 horizons x 8 props + futer20)."""
    rows = []
    ready = frame["atlas_ready"].to_numpy(bool)
    bins = _bin_pct(frame[DIM_RANK_COL[dim]].to_numpy(float))
    columns = [(f"{p}_{h}", h) for h in HORIZONS for p in PATH_PROPS]
    columns.append(("futer_20", 20))
    for state in ("LOW", "MID", "HIGH"):
        smask = ready & (bins == state)
        if smask.sum() < MIN_CELL_BARS:
            continue
        for col, h in columns:
            stats = _cell_stats(frame[col].to_numpy(float), smask)
            if stats is None:
                continue
            rows.append(
                {
                    "figi": figi,
                    "block": "ALL",
                    "scope_kind": "ALL",
                    "horizon": h,
                    "test": f"path_{dim}_{col.rsplit('_', 1)[0]}",
                    "state": state,
                    **stats,
                    **meta,
                }
            )
    return rows


def path_scope_cells(figi: str, frame: pd.DataFrame, meta: dict, dim: str) -> list[dict]:
    """Block and sleeve scope cells (LOW/HIGH x h10 x 8 props)."""
    rows = []
    ready = frame["atlas_ready"].to_numpy(bool)
    bins = _bin_pct(frame[DIM_RANK_COL[dim]].to_numpy(float))
    groups = [(name, "block", ready & (frame["block"].to_numpy() == name))
              for name in BLOCK_NAMES]
    groups.append((str(meta["sleeve"]), "sleeve", ready))
    for name, kind, gmask in groups:
        for state in ("LOW", "HIGH"):
            smask = gmask & (bins == state)
            if smask.sum() < MIN_CELL_BARS:
                continue
            for p in PATH_PROPS:
                col = f"{p}_10"
                stats = _cell_stats(frame[col].to_numpy(float), smask)
                if stats is None:
                    continue
                rows.append(
                    {
                        "figi": figi,
                        "block": name,
                        "scope_kind": kind,
                        "horizon": 10,
                        "test": f"path_{dim}_{p}",
                        "state": state,
                        **stats,
                        **meta,
                    }
                )
    return rows


def _trim(values: np.ndarray) -> np.ndarray:
    if len(values) < 3:
        return values
    lo, hi = np.percentile(values, [100 * TRIM_FRAC, 100 * (1 - TRIM_FRAC)])
    return values[(values >= lo) & (values <= hi)]


def separation_rows(figi: str, frame: pd.DataFrame, meta: dict, dim: str) -> list[dict]:
    """Per-stock LOW-vs-HIGH deltas for the shared separation rule."""
    rows = []
    ready = frame["atlas_ready"].to_numpy(bool)
    bins = _bin_pct(frame[DIM_RANK_COL[dim]].to_numpy(float))
    block = frame["block"].to_numpy()
    sleeve = str(meta["sleeve"])
    specs = [("ALL", "ALL", ready)]
    specs += [(name, "block", ready & (block == name)) for name in BLOCK_NAMES]
    specs.append((sleeve, "sleeve", ready))
    with np.errstate(invalid="ignore"):
        for name, kind, gmask in specs:
            if kind == "ALL":
                columns = [(f"{p}_{h}", h) for h in HORIZONS for p in PATH_PROPS]
                columns.append(("futer_20", 20))
            else:
                columns = [(f"{p}_10", 10) for p in PATH_PROPS]
            for col, h in columns:
                vals = frame[col].to_numpy(float)
                lo = vals[gmask & (bins == "LOW")]
                hi = vals[gmask & (bins == "HIGH")]
                lo = lo[np.isfinite(lo)]
                hi = hi[np.isfinite(hi)]
                if len(lo) < MIN_CELL_BARS or len(hi) < MIN_CELL_BARS:
                    continue
                lo_t, hi_t = _trim(lo), _trim(hi)
                rows.append(
                    {
                        "figi": figi,
                        "dim": dim,
                        "property": col,
                        "horizon": h,
                        "scope": name,
                        "scope_kind": kind,
                        "low_bars": int(len(lo)),
                        "high_bars": int(len(hi)),
                        "low_mean": float(lo.mean()),
                        "high_mean": float(hi.mean()),
                        "delta": float(hi.mean() - lo.mean()),
                        "delta_trimmed": float(hi_t.mean() - lo_t.mean()),
                        **meta,
                    }
                )
    return rows


def separation_summary(per_stock: pd.DataFrame, pooled_sd: dict) -> pd.DataFrame:
    rows = []
    if per_stock.empty:
        return pd.DataFrame()
    for (dim, prop, horizon, scope, kind), group in per_stock.groupby(
        ["dim", "property", "horizon", "scope", "scope_kind"], sort=True
    ):
        delta = pd.to_numeric(group["delta"], errors="coerce").to_numpy(float)
        trimmed = pd.to_numeric(group["delta_trimmed"], errors="coerce").to_numpy(float)
        ok = np.isfinite(delta)
        delta, trimmed = delta[ok], trimmed[np.isfinite(trimmed)]
        n = len(delta)
        sd = pooled_sd.get(prop, math.nan)
        mean_delta = float(delta.mean()) if n else math.nan
        sign_frac = (
            float(np.mean(np.sign(delta) == np.sign(mean_delta))) if n else math.nan
        )
        trimmed_sign_ok = bool(
            len(trimmed) and np.sign(trimmed.mean()) == np.sign(mean_delta)
        )
        separated = bool(
            n >= MIN_AGG_STOCKS
            and np.isfinite(sd)
            and sd > 0
            and abs(mean_delta) >= PATH_SD_FRAC * sd
            and sign_frac >= PATH_SIGN_FRAC
            and trimmed_sign_ok
        )
        rows.append(
            {
                "dim": dim,
                "property": prop,
                "horizon": int(horizon),
                "scope": scope,
                "scope_kind": kind,
                "stocks": n,
                "equal_stock_mean_delta": mean_delta,
                "pooled_sd": sd,
                "abs_delta_over_sd": (
                    abs(mean_delta) / sd if np.isfinite(sd) and sd > 0 else math.nan
                ),
                "stock_sign_fraction": sign_frac,
                "trimmed_sign_ok": trimmed_sign_ok,
                "separated": separated,
                "adequate": bool(n >= MIN_AGG_STOCKS),
            }
        )
    return pd.DataFrame(rows)


def conditional_rows(figi: str, frame: pd.DataFrame, meta: dict, dim: str) -> list[dict]:
    """D LOW-vs-HIGH deltas inside the hard Core-2 cells (h10 gate props)."""
    rows = []
    ready = frame["atlas_ready"].to_numpy(bool)
    struct = frame["rank_c_struct"].to_numpy(float)
    ext = frame["rank_c_ext"].to_numpy(float)
    bins = _bin_pct(frame[DIM_RANK_COL[dim]].to_numpy(float))
    cores = {
        "bull_low": ready & (struct >= HARD_HIGH) & (ext <= HARD_LOW),
        "bull_high": ready & (struct >= HARD_HIGH) & (ext >= HARD_HIGH),
        "bear_low": ready & (struct <= HARD_LOW) & (ext <= HARD_LOW),
        "bear_high": ready & (struct <= HARD_LOW) & (ext >= HARD_HIGH),
    }
    for core, cmask in cores.items():
        for prop in GATE_PROPS:
            vals = frame[prop].to_numpy(float)
            lo = vals[cmask & (bins == "LOW")]
            hi = vals[cmask & (bins == "HIGH")]
            lo = lo[np.isfinite(lo)]
            hi = hi[np.isfinite(hi)]
            if len(lo) < MIN_CELL_BARS or len(hi) < MIN_CELL_BARS:
                continue
            rows.append(
                {
                    "figi": figi,
                    "dim": dim,
                    "core": core,
                    "property": prop,
                    "low_bars": int(len(lo)),
                    "high_bars": int(len(hi)),
                    "low_mean": float(lo.mean()),
                    "high_mean": float(hi.mean()),
                    "delta": float(hi.mean() - lo.mean()),
                    **meta,
                }
            )
    return rows


def conditional_summary(per_stock: pd.DataFrame) -> pd.DataFrame:
    rows = []
    if per_stock.empty:
        return pd.DataFrame()
    for (dim, core, prop), group in per_stock.groupby(
        ["dim", "core", "property"], sort=True
    ):
        delta = pd.to_numeric(group["delta"], errors="coerce").to_numpy(float)
        delta = delta[np.isfinite(delta)]
        rows.append(
            {
                "dim": dim,
                "core": core,
                "property": prop,
                "stocks": int(len(delta)),
                "equal_stock_mean_delta": (
                    float(delta.mean()) if len(delta) else math.nan
                ),
                "stock_sign_fraction": (
                    float(np.mean(np.sign(delta) == np.sign(delta.mean())))
                    if len(delta)
                    else math.nan
                ),
                "adequate": bool(len(delta) >= MIN_AGG_STOCKS),
            }
        )
    return pd.DataFrame(rows)


MAP_SPECS = (
    ("structure", "extension"),
    ("extension", "compression"),
    ("structure", "efficiency"),
    ("compression", "efficiency"),
)
MAP_COORDS = {
    "structure": "rank_c_struct",
    "extension": "rank_c_ext",
    "compression": "rank_c_d3",
    "efficiency": "rank_c_d4",
}


def map_cells(figi: str, frame: pd.DataFrame, meta: dict) -> list[dict]:
    rows = []
    ready = frame["atlas_ready"].to_numpy(bool)
    binned = {
        key: _bin_pct(frame[col].to_numpy(float))
        for key, col in MAP_COORDS.items()
    }
    for ax, ay in MAP_SPECS:
        for sa in ("LOW", "MID", "HIGH"):
            for sb in ("LOW", "MID", "HIGH"):
                mask = ready & (binned[ax] == sa) & (binned[ay] == sb)
                if mask.sum() < MIN_CELL_BARS:
                    continue
                for prop in GATE_PROPS:
                    stats = _cell_stats(frame[prop].to_numpy(float), mask)
                    if stats is None:
                        continue
                    rows.append(
                        {
                            "figi": figi,
                            "block": "ALL",
                            "scope_kind": "ALL",
                            "horizon": 10 if prop != "futer_20" else 20,
                            "test": f"map_{ax}_x_{ay}_{prop}",
                            "state": f"{sa}/{sb}",
                            **stats,
                            **meta,
                        }
                    )
    return rows


# --------------------------------------------------------------------------
# Pooled property scale
# --------------------------------------------------------------------------

def _pooled_acc_update(acc: dict, frame: pd.DataFrame) -> None:
    ready = frame["atlas_ready"].to_numpy(bool)
    for prop in GATE_PROPS + tuple(f"{p}_{h}" for h in (1, 5, 20) for p in PATH_PROPS):
        vals = frame[prop].to_numpy(float)[ready]
        vals = vals[np.isfinite(vals)]
        if not len(vals):
            continue
        slot = acc.setdefault(prop, [0, 0.0, 0.0])
        slot[0] += int(len(vals))
        slot[1] += float(vals.sum())
        slot[2] += float((vals * vals).sum())


def pooled_sd_from_acc(acc: dict) -> dict:
    out = {}
    for prop, (n, total, total_sq) in acc.items():
        if n > 1:
            var = (total_sq - total * total / n) / (n - 1)
            out[prop] = float(math.sqrt(max(var, 0.0)))
        else:
            out[prop] = math.nan
    return out


# --------------------------------------------------------------------------
# HMM: pooled diagonal-Gaussian EM (numpy only)
# --------------------------------------------------------------------------

def _logsumexp(a: np.ndarray, axis=None, keepdims: bool = False) -> np.ndarray:
    m = np.max(a, axis=axis, keepdims=True)
    out = np.log(np.sum(np.exp(a - m), axis=axis, keepdims=True)) + m
    if not keepdims:
        out = np.squeeze(out, axis=axis)
    return out


def _log_emissions(seq: np.ndarray, mu: np.ndarray, var: np.ndarray) -> np.ndarray:
    diff = seq[:, None, :] - mu[None, :, :]
    return -0.5 * (
        np.sum(diff**2 / var[None, :, :], axis=2)
        + np.sum(np.log(2 * math.pi * var[None, :, :]), axis=2)
    )


def _init_params(seqs: list[np.ndarray], n_states: int, seed: int = HMM_SEED):
    rng = np.random.default_rng(seed)
    pooled = np.concatenate(seqs, axis=0)
    D = pooled.shape[1]
    qs = np.linspace(0.05, 0.95, n_states)
    mu = np.stack([np.quantile(pooled, q, axis=0) for q in qs], axis=0)
    mu = mu + rng.normal(0, 1e-6, size=(n_states, D))
    var = np.tile(pooled.var(axis=0) + 1e-6, (n_states, 1))
    pi = np.full(n_states, 1.0 / n_states)
    A = np.full((n_states, n_states), 1.0 / n_states)
    return pi, A, mu, var


def _em_step_scalar(seqs, pi, A, mu, var) -> tuple[float, np.ndarray, ...]:
    """Reference EM step (per-sequence forward-backward), kept for the
    vectorised-vs-reference equivalence test."""
    K, D = mu.shape
    logpi = np.log(pi + 1e-300)
    logA = np.log(A + 1e-300)
    ll = 0.0
    pi_num = np.zeros(K)
    A_num = np.zeros((K, K))
    A_den = np.zeros(K)
    mu_num = np.zeros((K, D))
    mu_den = np.zeros(K)
    var_num = np.zeros((K, D))
    for seq in seqs:
        T = len(seq)
        logB = _log_emissions(seq, mu, var)
        alpha = np.zeros((T, K))
        alpha[0] = logpi + logB[0]
        for t in range(1, T):
            alpha[t] = logB[t] + _logsumexp(alpha[t - 1][:, None] + logA, axis=0)
        ll += float(_logsumexp(alpha[-1]))
        beta = np.zeros((T, K))
        for t in range(T - 2, -1, -1):
            beta[t] = _logsumexp(
                logA + logB[t + 1][None, :] + beta[t + 1][None, :], axis=1
            )
        log_gamma = alpha + beta
        log_gamma -= _logsumexp(log_gamma, axis=1, keepdims=True)
        gamma = np.exp(log_gamma)
        for t in range(T - 1):
            m = (
                alpha[t][:, None]
                + logA
                + logB[t + 1][None, :]
                + beta[t + 1][None, :]
            )
            A_num += np.exp(m - _logsumexp(m))
        A_den += gamma[:-1].sum(axis=0)
        pi_num += gamma[0]
        mu_num += gamma.T @ seq
        mu_den += gamma.sum(axis=0)
        var_num += (
            gamma.T @ (seq**2)
            - 2 * mu * (gamma.T @ seq)
            + (gamma.sum(axis=0)[:, None]) * (mu**2)
        )
    pi_new = pi_num / max(pi_num.sum(), 1e-300)
    A_new = np.where(
        A_den[:, None] > 0, A_num / np.maximum(A_den[:, None], 1e-300), A
    )
    A_new = A_new / np.maximum(A_new.sum(axis=1, keepdims=True), 1e-300)
    mu_new = mu_num / np.maximum(mu_den[:, None], 1e-300)
    var_new = np.maximum(var_num / np.maximum(mu_den[:, None], 1e-300), 1e-6)
    return ll, pi_new, A_new, mu_new, var_new


def _em_step_fast(seqs, pi, A, mu, var) -> tuple[float, np.ndarray, ...]:
    """Mathematically identical EM step, vectorised across sequences."""
    S = len(seqs)
    K, D = mu.shape
    lens = np.array([len(s) for s in seqs], dtype=int)
    Tmax = int(lens.max())
    pad = np.zeros((S, Tmax, D))
    for i, s in enumerate(seqs):
        pad[i, : len(s)] = s
    const = np.sum(np.log(2 * math.pi * var), axis=1)
    logpi = np.log(pi + 1e-300)
    logA = np.log(A + 1e-300)

    def logB_at(t: int) -> np.ndarray:
        x = pad[:, t, :]
        diff = x[:, None, :] - mu[None, :, :]
        return -0.5 * (np.sum(diff**2 / var[None, :, :], axis=2) + const[None, :])

    alpha = np.zeros((S, Tmax, K))
    for t in range(Tmax):
        act = lens > t
        lb = logB_at(t)
        if t == 0:
            a = logpi[None, :] + lb
        else:
            a = lb + _logsumexp(
                alpha[:, t - 1, :][:, :, None] + logA[None, :, :], axis=1
            )
        a[~act] = 0.0
        alpha[:, t, :] = a
    ll = 0.0
    for i in range(S):
        ll += float(_logsumexp(alpha[i, lens[i] - 1, :]))

    beta_next = np.zeros((S, K))
    pi_num = np.zeros(K)
    A_num = np.zeros((K, K))
    A_den = np.zeros(K)
    mu_num = np.zeros((K, D))
    mu_den = np.zeros(K)
    var_num = np.zeros((K, D))
    for t in range(Tmax - 1, -1, -1):
        act = lens > t
        next_act = lens > (t + 1)
        if t == Tmax - 1:
            beta = np.zeros((S, K))
        else:
            lb_next = logB_at(t + 1)
            beta = _logsumexp(
                logA[None, :, :] + lb_next[:, None, :] + beta_next[:, None, :],
                axis=2,
            )
            # a sequence's backward message is 0 at its own last bar
            beta = np.where(next_act[:, None], beta, 0.0)
        log_gamma = alpha[:, t, :] + beta
        log_gamma[~act] = 0.0
        log_gamma -= _logsumexp(log_gamma, axis=1, keepdims=True)
        gamma = np.exp(log_gamma)
        gamma[~act] = 0.0
        if t < Tmax - 1:
            lb_next = logB_at(t + 1)
            m = (
                alpha[:, t, :][:, :, None]
                + logA[None, :, :]
                + lb_next[:, None, :]
                + beta_next[:, None, :]
            )
            flat = _logsumexp(m.reshape(S, -1), axis=1)
            xi = np.exp(m - flat[:, None, None])
            # only true within-sequence transitions (t -> t+1 both observed)
            xi = np.where(next_act[:, None, None], xi, 0.0)
            A_num += xi.sum(axis=0)
            A_den += np.where(next_act[:, None], gamma, 0.0).sum(axis=0)
        if t == 0:
            pi_num += gamma.sum(axis=0)
        x = pad[:, t, :]
        mu_num += gamma.T @ x
        mu_den += gamma.sum(axis=0)
        var_num += (
            gamma.T @ (x**2)
            - 2 * mu * (gamma.T @ x)
            + (gamma.sum(axis=0)[:, None]) * (mu**2)
        )
        beta_next = beta
    pi_new = pi_num / max(pi_num.sum(), 1e-300)
    A_new = np.where(
        A_den[:, None] > 0, A_num / np.maximum(A_den[:, None], 1e-300), A
    )
    A_new = A_new / np.maximum(A_new.sum(axis=1, keepdims=True), 1e-300)
    mu_new = mu_num / np.maximum(mu_den[:, None], 1e-300)
    var_new = np.maximum(var_num / np.maximum(mu_den[:, None], 1e-300), 1e-6)
    return ll, pi_new, A_new, mu_new, var_new


def _em_fit(seqs, n_states, stepper="fast", max_iter=HMM_MAX_ITER, verbose=True):
    step = _em_step_fast if stepper == "fast" else _em_step_scalar
    pi, A, mu, var = _init_params(seqs, n_states)
    n_total = int(sum(len(s) for s in seqs))
    prev_ll = -np.inf
    it = 0
    for it in range(max_iter):
        ll, pi, A, mu, var = step(seqs, pi, A, mu, var)
        if verbose and it % 10 == 0:
            print(f"[hmm-em] K={n_states} iter={it} ll={ll:.1f}", flush=True)
        if np.isfinite(prev_ll) and abs(ll - prev_ll) < HMM_TOL * max(1.0, abs(ll)):
            prev_ll = ll
            if verbose:
                print(
                    f"[hmm-em] K={n_states} converged iter={it} ll={ll:.1f}",
                    flush=True,
                )
            break
        prev_ll = ll
    D = mu.shape[1]
    n_params = (n_states - 1) + 2 * n_states * D + n_states * (n_states - 1)
    bic = -2 * prev_ll + n_params * math.log(n_total)
    return {
        "K": int(n_states),
        "pi": pi,
        "A": A,
        "mu": mu,
        "var": var,
        "train_ll": float(prev_ll),
        "bic": float(bic),
        "n_train": n_total,
        "n_params": int(n_params),
        "iters": int(it) + 1,
        "n_transitions": int(sum(len(s) - 1 for s in seqs)),
    }


def _viterbi(seq: np.ndarray, model: dict) -> np.ndarray:
    K = model["K"]
    mu, var, A, pi = model["mu"], model["var"], model["A"], model["pi"]
    logB = _log_emissions(seq, mu, var)
    log_pi = np.log(pi + 1e-300)
    log_A = np.log(A + 1e-300)
    T = len(seq)
    delta = np.zeros((T, K))
    psi = np.zeros((T, K), dtype=int)
    delta[0] = log_pi + logB[0]
    for t in range(1, T):
        cand = delta[t - 1][:, None] + log_A
        psi[t] = np.argmax(cand, axis=0)
        delta[t] = logB[t] + cand[psi[t], np.arange(K)]
    path = np.zeros(T, dtype=int)
    path[-1] = int(np.argmax(delta[-1]))
    for t in range(T - 2, -1, -1):
        path[t] = psi[t + 1, path[t + 1]]
    return path


def contiguous_runs(idx: np.ndarray) -> list[np.ndarray]:
    if len(idx) == 0:
        return []
    breaks = np.flatnonzero(np.diff(idx) > 1)
    bounds = [0, *(breaks + 1).tolist(), len(idx)]
    return [idx[a:b] for a, b in zip(bounds[:-1], bounds[1:])]


def _normalise(counts: np.ndarray) -> np.ndarray:
    total = counts.sum()
    return counts / total if total else counts


# --------------------------------------------------------------------------
# Cohort collection
# --------------------------------------------------------------------------

def collect_cohort(universe_path: Path, manifest_path: Path, raw_dir: Path,
                   classifier_path: Path, expected_figi_sha: str,
                   limit: int = 0, offset: int = 0) -> dict:
    audit = audit_snapshot(universe_path, manifest_path, raw_dir)
    if not audit["pass"]:
        raise SystemExit("snapshot audit failed")
    universe = pd.read_csv(universe_path)
    if len(universe) != 300 or universe["figi"].nunique() != 300:
        raise AssertionError("universe membership drift")
    cohort_sha = a0.figi_set_sha(universe)
    if cohort_sha != expected_figi_sha:
        raise AssertionError(f"cohort FIGI-set drift: {cohort_sha}")
    if limit:
        # plumbing smoke test only; the frozen A9 run passes no limit
        universe = universe.iloc[offset: offset + limit].reset_index(drop=True)
    classifier, blob = load_classifier(classifier_path)
    if blob != FROZEN_CLASSIFIER_BLOB:
        raise AssertionError("frozen classifier blob drift")

    sleeves = sorted({str(s) for s in universe["sleeve"].tolist()})
    sleeve_code = {s: i for i, s in enumerate(sleeves)}
    block_code = {name: i for i, name in enumerate(BLOCK_NAMES)}
    cut = np.datetime64(HMM_TRAIN_END)

    coverage, redun, sep, cond, path_all, path_scope, maps = [], [], [], [], [], [], []
    pooled_acc: dict = {}
    hmm_entries = []

    for i, meta_row in enumerate(universe.itertuples(index=False), start=1):
        figi = str(meta_row.figi)
        raw_path = raw_dir / f"{figi}.csv.gz"
        if not raw_path.exists():
            raise FileNotFoundError(raw_path)
        raw = pd.read_csv(raw_path)
        frame = build_structure_frame(raw, classifier)
        meta = {"sector": str(meta_row.sector), "sleeve": str(meta_row.sleeve)}
        ready = frame["atlas_ready"].to_numpy(bool)
        dates = frame["date"].to_numpy()
        blocks = frame["block"].to_numpy()
        coverage.append(
            {
                "figi": figi,
                "ticker": str(meta_row.ticker),
                **meta,
                "raw_rows": int(len(frame)),
                "base_ready_rows": int(frame["ready"].sum()),
                "atlas_ready_rows": int(ready.sum()),
                "d3_ready_rows": int(frame["d3_ready"].sum()),
                "natr_ready_rows": int(frame["d3_rob_ready"].sum()),
                "d4_ready_rows": int(frame["d4_ready"].sum()),
                "post_cut_atlas_ready_rows": int((ready & (dates >= cut)).sum()),
            }
        )
        redun.extend(redundancy_rows(figi, frame, meta))
        for dim in DIMS:
            path_all.extend(path_cells(figi, frame, meta, dim))
            path_scope.extend(path_scope_cells(figi, frame, meta, dim))
            sep.extend(separation_rows(figi, frame, meta, dim))
            cond.extend(conditional_rows(figi, frame, meta, dim))
        maps.extend(map_cells(figi, frame, meta))
        _pooled_acc_update(pooled_acc, frame)

        block_ids = np.array(
            [block_code.get(str(b), -1) for b in blocks], dtype=np.int8
        )
        coords = frame[
            ["rank_c_struct", "rank_c_ext", "rank_c_d3", "rank_c_d4"]
        ].to_numpy(float)
        hmm_entries.append(
            {
                "figi": figi,
                "sleeve_code": sleeve_code[str(meta_row.sleeve)],
                "coords": coords,
                "ready": ready,
                "train_mask": ready & (dates < cut),
                "block_ids": block_ids,
                "split": (dates >= cut).astype(np.int8),
                "props": np.column_stack(
                    [frame[p].to_numpy(float) for p in GATE_PROPS]
                ).astype(np.float32),
                "bin_codes": np.column_stack(
                    [_bin_code(coords[:, j]) for j in range(4)]
                ).astype(np.int8),
            }
        )
        print(
            f"[market-structure-a9] {i}/{len(universe)} {meta_row.ticker} "
            f"base_ready={int(frame['ready'].sum())} "
            f"atlas_ready={int(ready.sum())}",
            flush=True,
        )

    return {
        "audit": audit,
        "universe": universe,
        "limit": int(limit),
        "blob": blob,
        "figi_set_sha256": cohort_sha,
        "sleeves": sleeves,
        "block_code": block_code,
        "cut": cut,
        "pooled_sd": pooled_sd_from_acc(pooled_acc),
        "pooled_acc": pooled_acc,
        "coverage": pd.DataFrame(coverage),
        "redundancy_per_stock": pd.DataFrame(redun),
        "separation_per_stock": pd.DataFrame(sep),
        "conditional_per_stock": pd.DataFrame(cond),
        "path_all_per_stock": pd.DataFrame(path_all),
        "path_scope_per_stock": pd.DataFrame(path_scope),
        "map_per_stock": pd.DataFrame(maps),
        "hmm_entries": hmm_entries,
    }


# --------------------------------------------------------------------------
# HMM fit + decode + diagnostics
# --------------------------------------------------------------------------

def hmm_train_sequences(entries: list[dict]) -> list[np.ndarray]:
    seqs = []
    for entry in entries:
        idx = np.flatnonzero(entry["train_mask"])
        for run in contiguous_runs(idx):
            if len(run) >= 2:
                seqs.append(entry["coords"][run])
    return seqs


def fit_hmm(entries: list[dict], ks=HMM_KS, verbose: bool = True):
    train_raw = hmm_train_sequences(entries)
    if not train_raw:
        raise SystemExit("no HMM training sequences")
    pooled = np.concatenate(train_raw, axis=0)
    mean = pooled.mean(axis=0)
    std = pooled.std(axis=0)
    std = np.where(std > 0, std, 1.0)
    train_std = [(s - mean) / std for s in train_raw]
    fits = [_em_fit(train_std, k, verbose=verbose) for k in ks]
    best = min(fits, key=lambda f: (round(f["bic"], 9), f["K"]))
    return best, fits, mean, std, train_std


def hmm_model_rows(fits) -> list[dict]:
    return [
        {
            "K": f["K"],
            "bic": f["bic"],
            "train_ll": f["train_ll"],
            "n_train": f["n_train"],
            "n_params": f["n_params"],
            "iters": f["iters"],
        }
        for f in fits
    ]


def decode_hmm(model: dict, entries: list[dict], mean, std) -> dict:
    """Decode every atlas_ready bar (contiguous runs only), no refit."""
    figi_id, state, run_id, split, block_id, sleeve_id = [], [], [], [], [], []
    joint_bin, std_coords, raw_coords = [], [], []
    prop_cols = []
    run_counter = 0
    for fid, entry in enumerate(entries):
        idx = np.flatnonzero(entry["ready"])
        if len(idx) < 1:
            continue
        std_seq = (entry["coords"][idx] - mean) / std
        for run in contiguous_runs(idx):
            if len(run) < 2:
                run_counter += 1
                continue
            pos = np.searchsorted(idx, run)
            path = _viterbi(std_seq[pos[0]: pos[-1] + 1], model)
            n = len(run)
            run_counter += 1
            figi_id.append(np.full(n, fid, dtype=np.int16))
            state.append(path.astype(np.int8))
            run_id.append(np.full(n, run_counter, dtype=np.int32))
            split.append(entry["split"][run].astype(np.int8))
            block_id.append(entry["block_ids"][run])
            sleeve_id.append(np.full(n, entry["sleeve_code"], dtype=np.int8))
            joint_bin.append(entry["bin_codes"][run])
            std_coords.append(std_seq[pos[0]: pos[-1] + 1].astype(np.float32))
            raw_coords.append(entry["coords"][run].astype(np.float32))
            prop_cols.append(entry["props"][run])
    return {
        "figi_id": np.concatenate(figi_id),
        "state": np.concatenate(state),
        "run_id": np.concatenate(run_id),
        "split": np.concatenate(split),
        "block_id": np.concatenate(block_id),
        "sleeve_id": np.concatenate(sleeve_id),
        "joint_bin": np.concatenate(joint_bin),
        "std_coords": np.concatenate(std_coords),
        "raw_coords": np.concatenate(raw_coords),
        "props": np.concatenate(prop_cols),
    }


def hmm_diagnostics(model: dict, dec: dict, entries: list[dict], mean, std,
                    block_code: dict, sleeves: list[str],
                    pooled_sd: dict) -> dict:
    K = model["K"]
    state = dec["state"].astype(int)
    split = dec["split"].astype(int)
    n_bars = len(state)
    joint = dec["joint_bin"]
    joint_id = (
        (joint[:, 0].astype(int) * 3 + joint[:, 1].astype(int)) * 3
        + joint[:, 2].astype(int)
    ) * 3 + joint[:, 3].astype(int)
    joint_id = np.clip(joint_id, 0, 80)

    def occ(split_code: int) -> np.ndarray:
        counts = np.bincount(state[split == split_code], minlength=K).astype(float)
        return _normalise(counts)

    occ_train, occ_eval = occ(0), occ(1)

    # empirical transitions inside contiguous runs
    same_run = dec["run_id"][1:] == dec["run_id"][:-1]
    trans_counts = np.zeros((K, K))
    ev = np.zeros((K, K))
    a_idx = state[:-1][same_run]
    b_idx = state[1:][same_run]
    split_pair = split[1:][same_run]
    for a, b, sp in zip(a_idx, b_idx, split_pair):
        trans_counts[a, b] += 1
        if sp == 1:
            ev[a, b] += 1
    trans = np.divide(
        trans_counts, np.maximum(trans_counts.sum(axis=1, keepdims=True), 1e-300)
    )
    trans_eval = np.divide(
        ev, np.maximum(ev.sum(axis=1, keepdims=True), 1e-300)
    )
    persistence_eval = np.diag(trans_eval)

    # centroids (standardised = model units; raw = percentiles)
    cent_std = np.zeros((2, K, 4))
    cent_raw = np.zeros((2, K, 4))
    for sp in (0, 1):
        m = split == sp
        for k in range(K):
            mk = m & (state == k)
            if mk.sum():
                cent_std[sp, k] = dec["std_coords"][mk].mean(axis=0)
                cent_raw[sp, k] = dec["raw_coords"][mk].mean(axis=0)

    drift = (
        np.abs(model["mu"] - cent_std[1]).max(axis=1)
        if occ_eval.sum()
        else np.full(K, np.inf)
    )

    # dominant Atlas joint bin + purity + NMI
    dominant = np.zeros((2, K), dtype=int)
    purity = np.zeros((2, K))
    for sp in (0, 1):
        m = split == sp
        for k in range(K):
            mk = m & (state == k)
            if mk.sum():
                counts = np.bincount(joint_id[mk], minlength=81).astype(float)
                dominant[sp, k] = int(np.argmax(counts))
                purity[sp, k] = float(counts.max() / counts.sum())
    ev_mask = split == 1
    mi = 0.0
    if ev_mask.sum():
        joint_counts = np.zeros((K, 81))
        for k, jb in zip(state[ev_mask], joint_id[ev_mask]):
            joint_counts[k, jb] += 1
        joint_counts /= joint_counts.sum()
        pk = joint_counts.sum(axis=1)
        pj = joint_counts.sum(axis=0)
        for k in range(K):
            for j in range(81):
                if joint_counts[k, j] > 0:
                    mi += joint_counts[k, j] * math.log(
                        joint_counts[k, j] / (pk[k] * pj[j])
                    )
    # transition entropy-style normalisation
    h_state = 0.0
    for k in range(K):
        v = 0.0
        for k2 in range(K):
            if trans_eval[k, k2] > 0:
                v -= trans_eval[k, k2] * math.log(trans_eval[k, k2])
        h_state += occ_eval[k] * v
    persistence_term = float(np.sum(occ_eval * persistence_eval))
    nmi = mi / max(1e-12, -sum(p * math.log(p) for p in occ_eval if p > 0))

    # per (figi, state, split) means of gate properties, for pair separation
    n_props = dec["props"].shape[1]
    fid = dec["figi_id"].astype(int)
    counts = np.zeros((len(entries), 2, K))
    sums = np.zeros((len(entries), 2, K, n_props))
    np.add.at(counts, (fid, split, state), 1.0)
    for j in range(n_props):
        np.add.at(sums[:, :, :, j], (fid, split, state), dec["props"][:, j])

    reproducible = []
    for k in range(K):
        ok = (
            occ_eval[k] >= HMM_MIN_OCC
            and occ_train[k] >= HMM_MIN_OCC
            and persistence_eval[k] >= HMM_MIN_PERSIST
            and drift[k] <= HMM_MAX_DRIFT
        )
        reproducible.append(bool(ok))

    # adds-structure pairs
    pair_rows = []
    for a in range(K):
        for b in range(a + 1, K):
            if not (reproducible[a] and reproducible[b]):
                continue
            if dominant[1, a] != dominant[1, b] or dominant[0, a] != dominant[0, b]:
                continue
            n_sep = 0
            detail = []
            for j, prop in enumerate(GATE_PROPS):
                sd = pooled_sd.get(prop, math.nan)
                if not (np.isfinite(sd) and sd > 0):
                    continue
                signs = []
                mags = []
                for sp in (0, 1):
                    ca = counts[:, sp, a]
                    cb = counts[:, sp, b]
                    sa = sums[:, sp, a, j]
                    sb = sums[:, sp, b, j]
                    ok = (ca >= MIN_CELL_BARS) & (cb >= MIN_CELL_BARS)
                    if ok.sum() < MIN_AGG_STOCKS:
                        signs.append(0)
                        mags.append(0.0)
                        continue
                    per_stock = sa[ok] / ca[ok] - sb[ok] / cb[ok]
                    delta = float(per_stock.mean())
                    sign_frac = float(
                        np.mean(np.sign(per_stock) == np.sign(delta))
                    ) if delta != 0 else 0.0
                    separated = (
                        abs(delta) >= PATH_SD_FRAC * sd
                        and sign_frac >= PATH_SIGN_FRAC
                    )
                    signs.append(np.sign(delta) if separated else 0)
                    mags.append(delta)
                agreed = (
                    signs[0] != 0 and signs[1] != 0 and signs[0] == signs[1]
                )
                if agreed:
                    n_sep += 1
                detail.append(
                    {
                        "property": prop,
                        "delta_train": mags[0],
                        "delta_eval": mags[1],
                        "separated_both": bool(agreed),
                    }
                )
            pair_rows.append(
                {
                    "state_a": a,
                    "state_b": b,
                    "dominant_bin": int(dominant[1, a]),
                    "separated_properties": int(n_sep),
                    "adds_structure": bool(n_sep >= 2),
                    "detail": detail,
                }
            )

    block_occ = {}
    for name, code in block_code.items():
        m = dec["block_id"] == code
        block_occ[name] = (
            _normalise(np.bincount(state[m], minlength=K).astype(float)).tolist()
            if m.any()
            else []
        )
    sleeve_occ = {}
    for code, name in enumerate(sleeves):
        m = dec["sleeve_id"] == code
        sleeve_occ[name] = (
            _normalise(np.bincount(state[m], minlength=K).astype(float)).tolist()
            if m.any()
            else []
        )

    return {
        "K": K,
        "n_bars_decoded": int(n_bars),
        "occupancy_train": occ_train.tolist(),
        "occupancy_eval": occ_eval.tolist(),
        "persistence_eval": persistence_eval.tolist(),
        "transition_model": model["A"].tolist(),
        "transition_eval_empirical": trans_eval.tolist(),
        "centroids_std_train": cent_std[0].tolist(),
        "centroids_std_eval": cent_std[1].tolist(),
        "centroids_raw_train": cent_raw[0].tolist(),
        "centroids_raw_eval": cent_raw[1].tolist(),
        "centroid_drift": drift.tolist(),
        "dominant_bin_train": dominant[0].tolist(),
        "dominant_bin_eval": dominant[1].tolist(),
        "dominant_bin_stable": bool(
            np.mean(dominant[0] == dominant[1]) if K else False
        ),
        "atlas_purity_eval": purity[1].tolist(),
        "nmi_state_atlas": float(nmi),
        "mi_state_atlas_nats": float(mi),
        "mean_persistence_eval": persistence_term,
        "max_single_state_share_eval": float(occ_eval.max()),
        "reproducible": reproducible,
        "n_reproducible": int(sum(reproducible)),
        "dominant_bin_agreement": float(
            np.mean([
                1.0 if reproducible[k] and dominant[0, k] == dominant[1, k] else 0.0
                for k in range(K)
            ])
        ),
        "block_occupancy": block_occ,
        "sleeve_occupancy": sleeve_occ,
        "pair_tests": pair_rows,
        "counts": counts,
        "sums": sums,
    }


def hmm_verdict(diag: dict) -> dict:
    K = diag["K"]
    occ_train = np.asarray(diag["occupancy_train"])
    occ_eval = np.asarray(diag["occupancy_eval"])
    r = np.asarray(diag["reproducible"])
    n_r = int(r.sum())
    effective = int((occ_train >= HMM_MIN_OCC).sum())
    if effective < 2 or float(occ_eval.max()) > 0.95:
        verdict = "HMM_INSUFFICIENT"
        reason = (
            f"effective states with training occupancy>=0.05 = {effective}; "
            f"max eval occupancy = {occ_eval.max():.3f}"
        )
    elif n_r / K < HMM_UNSTABLE_FRAC:
        verdict = "HMM_UNSTABLE"
        reason = f"reproducible states {n_r}/{K} below 2/3"
    elif any(p["adds_structure"] for p in diag["pair_tests"]):
        verdict = "HMM_ADDS_STABLE_STRUCTURE"
        reason = "a reproducible state pair with the same dominant Atlas bin separates >=2 gate properties with train/eval sign agreement"
    elif (
        diag["dominant_bin_agreement"] >= HMM_CONVERGE_C
        and diag["nmi_state_atlas"] >= HMM_CONVERGE_NMI
    ):
        verdict = "HMM_CONVERGES_WITH_ATLAS"
        reason = (
            f"dominant-bin agreement {diag['dominant_bin_agreement']:.3f} and "
            f"NMI(state;Atlas) {diag['nmi_state_atlas']:.3f}"
        )
    else:
        verdict = "HMM_UNSTABLE"
        reason = (
            f"dominant-bin agreement {diag['dominant_bin_agreement']:.3f}, "
            f"NMI {diag['nmi_state_atlas']:.3f}"
        )
    return {"verdict": verdict, "reason": reason, "K": K, "n_reproducible": n_r}


# --------------------------------------------------------------------------
# Gate evaluation
# --------------------------------------------------------------------------

CLASS_ORDER = {
    "INSUFFICIENT": 0,
    "REJECT_REDUNDANT": 1,
    "REJECT_UNSTABLE": 2,
    "KEEP_AS_DESCRIPTIVE_ONLY": 3,
    "KEEP_AS_ATLAS_DIMENSION": 4,
}
PAIR_FOR_DIM = {
    "d3": ("d3_rv_vs_struct", "d3_rv_vs_ext"),
    "d3_rob": ("d3_natr_vs_struct", "d3_natr_vs_ext"),
    "d4": ("d4_vs_struct", "d4_vs_ext"),
}




def resolve_d3(primary: dict, robustness: dict) -> dict:
    order = CLASS_ORDER
    weaker = (
        primary
        if order[primary["classification"]] <= order[robustness["classification"]]
        else robustness
    )
    return {
        "headline": weaker["classification"],
        "primary_classification": primary["classification"],
        "robustness_classification": robustness["classification"],
        "weaker_of": weaker["dim"],
        "note": (
            "D3 headline = the weaker of the primary (RV20) and robustness "
            "(NATR20) classifications (frozen anti-cherry-pick rule)."
        ),
    }


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def _write_csv(path: Path, frame: pd.DataFrame) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    frame.to_csv(path, index=False)


def redundancy_sleeve_summary(per_stock: pd.DataFrame) -> pd.DataFrame:
    rows = []
    if per_stock.empty:
        return pd.DataFrame()
    all_scope = per_stock[per_stock["scope"] == "ALL"]
    for (pair, sleeve), group in all_scope.groupby(["pair", "sleeve"], sort=True):
        rho = pd.to_numeric(group["spearman"], errors="coerce").to_numpy(float)
        mi = pd.to_numeric(group["mutual_info_nats"], errors="coerce").to_numpy(float)
        rho, mi = rho[np.isfinite(rho)], mi[np.isfinite(mi)]
        rows.append(
            {
                "pair": pair,
                "sleeve": sleeve,
                "stocks": int(len(rho)),
                "equal_stock_mean_spearman": float(rho.mean()) if len(rho) else math.nan,
                "equal_stock_mean_mi_nats": float(mi.mean()) if len(mi) else math.nan,
            }
        )
    return pd.DataFrame(rows)


def breadth_table(sep_sum: pd.DataFrame, path_all: pd.DataFrame,
                  coverage: pd.DataFrame) -> pd.DataFrame:
    total_bars = float(coverage["atlas_ready_rows"].sum())
    rows = []
    for dim in DIMS:
        sub = sep_sum[
            (sep_sum["dim"] == dim)
            & (sep_sum["scope"] == "ALL")
            & (sep_sum["property"] == "fwd_10")
        ]
        stocks = int(sub["stocks"].iloc[0]) if not sub.empty else 0
        pc = path_all[
            (path_all["test"] == f"path_{dim}_fwd") & (path_all["horizon"] == 10)
        ]
        bars = pc.groupby("state")["bars"].sum().to_dict() if not pc.empty else {}
        low_bars = float(bars.get("LOW", 0))
        high_bars = float(bars.get("HIGH", 0))
        low_share = low_bars / total_bars if total_bars else math.nan
        high_share = high_bars / total_bars if total_bars else math.nan
        rows.append(
            {
                "dim": dim,
                "stocks_with_both_bins": stocks,
                "low_bars": int(low_bars),
                "high_bars": int(high_bars),
                "atlas_ready_bars": int(total_bars),
                "low_bar_share": low_share,
                "high_bar_share": high_share,
                "adequate_stocks": bool(stocks >= MIN_AGG_STOCKS),
                "adequate_bar_share": bool(
                    np.isfinite(low_share)
                    and np.isfinite(high_share)
                    and low_share >= 0.05
                    and high_share >= 0.05
                ),
                "pass": bool(
                    stocks >= MIN_AGG_STOCKS
                    and np.isfinite(low_share)
                    and np.isfinite(high_share)
                    and low_share >= 0.05
                    and high_share >= 0.05
                ),
            }
        )
    return pd.DataFrame(rows)


def evaluate_dimension(dim: str, redun_sum: pd.DataFrame,
                       sep_sum: pd.DataFrame, cond_sum: pd.DataFrame,
                       breadth: pd.DataFrame) -> dict:
    rows = redun_sum[redun_sum["scope"] == "ALL"] if not redun_sum.empty else redun_sum
    pairs = PAIR_FOR_DIM[dim]
    g1 = True
    g1_detail = {}
    for pair in pairs:
        sub = rows[rows["pair"] == pair]
        if sub.empty:
            g1 = False
            g1_detail[pair] = "missing"
            continue
        rho = float(sub["equal_stock_mean_spearman"].iloc[0])
        mi = float(sub["equal_stock_mean_mi_nats"].iloc[0])
        ok = abs(rho) < NOVEL_SPEARMAN_MAX and mi < NOVEL_MI_MAX
        g1 = g1 and ok
        g1_detail[pair] = {
            "mean_spearman": rho,
            "mean_mi_nats": mi,
            "pass": bool(ok),
        }

    brow = breadth[breadth["dim"] == dim]
    g2 = bool(brow["pass"].iloc[0]) if not brow.empty else False
    g2_detail = brow.iloc[0].to_dict() if not brow.empty else {}

    sep_all = sep_sum[(sep_sum["dim"] == dim) & (sep_sum["scope_kind"] == "ALL")]
    g4_props = (
        sorted(set(sep_all[sep_all["separated"]]["property"].tolist()))
        if not sep_all.empty
        else []
    )

    def prop_scope(prop, kind):
        return sep_sum[
            (sep_sum["dim"] == dim)
            & (sep_sum["property"] == prop)
            & (sep_sum["scope_kind"] == kind)
        ]

    g3_props_ok = 0
    g3_detail = {}
    for prop in g4_props:
        blocks = prop_scope(prop, "block")
        sleeves = prop_scope(prop, "sleeve")
        adeq_blocks = blocks[blocks["stocks"] >= MIN_AGG_STOCKS]
        adeq_sleeves = sleeves[sleeves["stocks"] >= MIN_AGG_STOCKS]
        all_delta = sep_all[sep_all["property"] == prop]
        if all_delta.empty:
            continue
        sign0 = np.sign(float(all_delta["equal_stock_mean_delta"].iloc[0]))
        same_blocks = int(np.sum(np.sign(adeq_blocks["equal_stock_mean_delta"]) == sign0))
        same_sleeves = int(
            np.sum(np.sign(adeq_sleeves["equal_stock_mean_delta"]) == sign0)
        )
        b_ok = len(adeq_blocks) >= 4 and same_blocks >= len(adeq_blocks) - 1
        s_ok = len(adeq_sleeves) >= 1 and same_sleeves == len(adeq_sleeves)
        g3_detail[prop] = {
            "adequate_blocks": int(len(adeq_blocks)),
            "blocks_same_sign": same_blocks,
            "adequate_sleeves": int(len(adeq_sleeves)),
            "sleeves_same_sign": same_sleeves,
            "pass": bool(b_ok and s_ok),
        }
        if b_ok and s_ok:
            g3_props_ok += 1
    g3 = g3_props_ok >= 2

    g4 = len(g4_props) >= 2

    g5_detail = {}
    g5_props_ok = 0
    for prop in g4_props:
        sub = cond_sum[(cond_sum["dim"] == dim) & (cond_sum["property"] == prop)]
        if sub.empty:
            continue
        adeq = sub[sub["adequate"]]
        all_delta = sep_all[sep_all["property"] == prop]
        if all_delta.empty or len(adeq) < 2:
            continue
        sign0 = np.sign(float(all_delta["equal_stock_mean_delta"].iloc[0]))
        same = int(np.sum(np.sign(adeq["equal_stock_mean_delta"]) == sign0))
        need = math.ceil(2 / 3 * len(adeq))
        ok = same >= need
        g5_detail[prop] = {
            "adequate_cores": int(len(adeq)),
            "cores_same_sign": same,
            "need": int(need),
            "pass": bool(ok),
        }
        if ok:
            g5_props_ok += 1
    g5 = g5_props_ok >= 2

    if g2_detail.get("stocks_with_both_bins", 0) == 0 and sep_all.empty:
        classification = "INSUFFICIENT"
    elif not g1:
        classification = "REJECT_REDUNDANT"
    elif not g2 or not g3:
        classification = "REJECT_UNSTABLE"
    elif g4 and g5:
        classification = "KEEP_AS_ATLAS_DIMENSION"
    else:
        classification = "KEEP_AS_DESCRIPTIVE_ONLY"

    return {
        "dim": dim,
        "label": DIM_LABEL[dim],
        "G1_novelty": bool(g1),
        "G1_detail": g1_detail,
        "G2_breadth": bool(g2),
        "G2_detail": g2_detail,
        "G3_temporal_sleeve_stability": bool(g3),
        "G3_detail": g3_detail,
        "G4_path_separation": bool(g4),
        "G4_separated_properties": g4_props,
        "G5_core2_conditioning": bool(g5),
        "G5_detail": g5_detail,
        "separated_property_count": len(g4_props),
        "classification": classification,
    }


def hard_core_shares(dec: dict, K: int) -> list[dict]:
    raw = dec["raw_coords"]
    ev = dec["split"] == 1
    st = dec["state"].astype(int)
    struct, ext = raw[:, 0], raw[:, 1]
    cores = {
        "bull_low": (struct >= HARD_HIGH) & (ext <= HARD_LOW),
        "bull_high": (struct >= HARD_HIGH) & (ext >= HARD_HIGH),
        "bear_low": (struct <= HARD_LOW) & (ext <= HARD_LOW),
        "bear_high": (struct <= HARD_LOW) & (ext >= HARD_HIGH),
    }
    rows = []
    for k in range(K):
        mk = ev & (st == k)
        n = int(mk.sum())
        for name, cm in cores.items():
            rows.append(
                {
                    "state": k,
                    "core": name,
                    "bars": int((mk & cm).sum()),
                    "share_of_state": (
                        float((mk & cm).sum() / n) if n else math.nan
                    ),
                }
            )
    return rows


def hmm_state_summary(diag: dict) -> pd.DataFrame:
    K = diag["K"]
    rows = []
    for k in range(K):
        rows.append(
            {
                "state": k,
                "occupancy_train": diag["occupancy_train"][k],
                "occupancy_eval": diag["occupancy_eval"][k],
                "persistence_eval": diag["persistence_eval"][k],
                "centroid_drift": diag["centroid_drift"][k],
                "dominant_bin_train": diag["dominant_bin_train"][k],
                "dominant_bin_eval": diag["dominant_bin_eval"][k],
                "atlas_purity_eval": diag["atlas_purity_eval"][k],
                "reproducible": bool(diag["reproducible"][k]),
                "centroid_struct": diag["centroids_raw_eval"][k][0],
                "centroid_ext": diag["centroids_raw_eval"][k][1],
                "centroid_d3": diag["centroids_raw_eval"][k][2],
                "centroid_d4": diag["centroids_raw_eval"][k][3],
            }
        )
    return pd.DataFrame(rows)


def hmm_stability_table(diag: dict) -> pd.DataFrame:
    rows = []
    for block, occ in diag["block_occupancy"].items():
        for k, v in enumerate(occ):
            rows.append({"scope": block, "scope_kind": "block", "state": k, "occupancy": v})
    for sleeve, occ in diag["sleeve_occupancy"].items():
        for k, v in enumerate(occ):
            rows.append(
                {"scope": sleeve, "scope_kind": "sleeve", "state": k, "occupancy": v}
            )
    return pd.DataFrame(rows)


def hmm_transition_table(diag: dict) -> pd.DataFrame:
    rows = []
    K = diag["K"]
    for kind, mat in (
        ("model_train", diag["transition_model"]),
        ("eval_empirical", diag["transition_eval_empirical"]),
    ):
        for a in range(K):
            for b in range(K):
                rows.append(
                    {"matrix": kind, "from_state": a, "to_state": b, "prob": mat[a][b]}
                )
    return pd.DataFrame(rows)


def hmm_path_summary(diag: dict, entries: list[dict]) -> pd.DataFrame:
    counts = diag["counts"]
    sums = diag["sums"]
    K = diag["K"]
    rows = []
    for sp, split_name in ((0, "train"), (1, "eval")):
        for k in range(K):
            for j, prop in enumerate(GATE_PROPS):
                c = counts[:, sp, k]
                ok = c >= MIN_CELL_BARS
                per_stock = np.divide(
                    sums[ok, sp, k, j], c[ok], out=np.full(int(ok.sum()), np.nan),
                    where=c[ok] > 0,
                )
                rows.append(
                    {
                        "split": split_name,
                        "state": k,
                        "property": prop,
                        "stocks": int(ok.sum()),
                        "equal_stock_mean": (
                            float(per_stock.mean()) if ok.sum() else math.nan
                        ),
                    }
                )
    return pd.DataFrame(rows)


def hmm_pair_table(diag: dict) -> pd.DataFrame:
    rows = []
    for pair in diag["pair_tests"]:
        for item in pair["detail"]:
            rows.append(
                {
                    "state_a": pair["state_a"],
                    "state_b": pair["state_b"],
                    "dominant_bin": pair["dominant_bin"],
                    "property": item["property"],
                    "delta_train": item["delta_train"],
                    "delta_eval": item["delta_eval"],
                    "separated_both": item["separated_both"],
                    "pair_adds_structure": pair["adds_structure"],
                    "pair_separated_properties": pair["separated_properties"],
                }
            )
    return pd.DataFrame(rows)


# --------------------------------------------------------------------------
# main
# --------------------------------------------------------------------------

def run_discovery(universe_path: Path, manifest_path: Path, raw_dir: Path,
                  classifier_path: Path, out: Path, prereg_sha: str,
                  limit: int = 0, offset: int = 0) -> dict:
    cohort = collect_cohort(
        universe_path, manifest_path, raw_dir, classifier_path,
        EXPECTED_FIGI_SET_SHA, limit=limit, offset=offset,
    )
    out.mkdir(parents=True, exist_ok=True)
    pooled_sd = cohort["pooled_sd"]

    redun_stock = cohort["redundancy_per_stock"]
    redun_sum = redundancy_summary(redun_stock)
    redun_sleeve = redundancy_sleeve_summary(redun_stock)
    sep_stock = cohort["separation_per_stock"]
    sep_sum = separation_summary(sep_stock, pooled_sd)
    cond_stock = cohort["conditional_per_stock"]
    cond_sum = conditional_summary(cond_stock)
    path_all = cohort["path_all_per_stock"]
    path_all_sum = a1.aggregate_a1_cells(path_all, ["test", "state", "block", "horizon"])
    path_scope = cohort["path_scope_per_stock"]
    path_scope_sum = a1.aggregate_a1_cells(
        path_scope, ["test", "state", "block", "horizon"]
    )
    map_stock = cohort["map_per_stock"]
    map_sum = a1.aggregate_a1_cells(map_stock, ["test", "state", "block", "horizon"])
    breadth = breadth_table(sep_sum, path_all, cohort["coverage"])

    psd_rows = [
        {"property": k, "pooled_sd": pooled_sd.get(k, math.nan), "bars": v[0]}
        for k, v in sorted(cohort["pooled_acc"].items())
    ]

    classes = {
        dim: evaluate_dimension(dim, redun_sum, sep_sum, cond_sum, breadth)
        for dim in DIMS
    }
    d3_rule = resolve_d3(classes["d3"], classes["d3_rob"])
    classification = {
        "D3": d3_rule["headline"],
        "D4": classes["d4"]["classification"],
        "D3_primary_rv20": classes["d3"]["classification"],
        "D3_robustness_natr20": classes["d3_rob"]["classification"],
        "d3_rule": d3_rule,
    }

    # ---- HMM ----
    best, fits, mean, std, train_std = fit_hmm(cohort["hmm_entries"])
    model = best
    dec = decode_hmm(model, cohort["hmm_entries"], mean, std)
    diag = hmm_diagnostics(
        model, dec, cohort["hmm_entries"], mean, std,
        cohort["block_code"], cohort["sleeves"], pooled_sd,
    )
    verdict = hmm_verdict(diag)

    # ---- write artifacts ----
    paths = {}

    def emit(name: str, frame: pd.DataFrame) -> None:
        _write_csv(out / name, frame)
        paths[name] = str(out / name)

    emit("coverage.csv", cohort["coverage"])
    emit("redundancy_per_stock.csv", redun_stock)
    emit("redundancy_summary.csv", redun_sum)
    emit("redundancy_sleeve_summary.csv", redun_sleeve)
    emit("separation_per_stock.csv", sep_stock)
    emit("separation_summary.csv", sep_sum)
    emit("conditional_per_stock.csv", cond_stock)
    emit("conditional_summary.csv", cond_sum)
    emit("path_per_stock.csv", path_all)
    emit("path_summary.csv", path_all_sum)
    emit("path_scope_per_stock.csv", path_scope)
    emit("path_scope_summary.csv", path_scope_sum)
    emit("map_per_stock.csv", map_stock)
    emit("map_summary.csv", map_sum)
    emit("pooled_property_stats.csv", pd.DataFrame(psd_rows))
    emit("breadth.csv", breadth)
    emit("hmm_models.csv", pd.DataFrame(hmm_model_rows(fits)))
    emit("hmm_state_summary.csv", hmm_state_summary(diag))
    emit("hmm_transition.csv", hmm_transition_table(diag))
    emit("hmm_stability.csv", hmm_stability_table(diag))
    emit("hmm_path_summary.csv", hmm_path_summary(diag, cohort["hmm_entries"]))
    emit("hmm_pair_separation.csv", hmm_pair_table(diag))
    emit("hmm_atlas_overlap.csv", pd.DataFrame(hard_core_shares(dec, model["K"])))

    (out / "hmm_centroids.json").write_text(
        json.dumps(
            {
                "K": model["K"],
                "feature_order": [
                    "rank_c_struct", "rank_c_ext", "rank_c_d3", "rank_c_d4",
                ],
                "scaler_mean": [float(x) for x in mean],
                "scaler_std": [float(x) for x in std],
                "centroids_std_train": diag["centroids_std_train"],
                "centroids_std_eval": diag["centroids_std_eval"],
                "centroids_raw_train": diag["centroids_raw_train"],
                "centroids_raw_eval": diag["centroids_raw_eval"],
                "transition_model": diag["transition_model"],
                "initial_model": [float(x) for x in model["pi"]],
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    (out / "hmm_verdict.json").write_text(
        json.dumps(verdict, indent=2) + "\n", encoding="utf-8"
    )
    gate_eval = {
        "gates": classes,
        "classification": classification,
        "thresholds": {
            "novel_spearman_max": NOVEL_SPEARMAN_MAX,
            "novel_mi_max": NOVEL_MI_MAX,
            "path_sd_frac": PATH_SD_FRAC,
            "path_sign_frac": PATH_SIGN_FRAC,
            "trim_frac": TRIM_FRAC,
            "low_max": LOW_MAX,
            "high_min": HIGH_MIN,
            "min_agg_stocks": MIN_AGG_STOCKS,
            "min_cell_bars": MIN_CELL_BARS,
        },
    }
    (out / "gate_eval.json").write_text(
        json.dumps(gate_eval, indent=2, default=str) + "\n", encoding="utf-8"
    )

    summary = {
        "integrity": {
            "issue": 78,
            "child_issue": 181,
            "study": "Market Structure Dimension Audit A9",
            "role": "post-outcome architecture discovery; not fresh OOS validation",
            "prereg_commit": prereg_sha,
            "classifier_blob": cohort["blob"],
            "figi_set_sha256": cohort["figi_set_sha256"],
            "universe_sha256": sha256_file(universe_path),
            "manifest_sha256": sha256_file(manifest_path),
            "stocks": int(len(cohort["universe"])),
            "smoke_limit": int(cohort["limit"]),
            "raw_files": int(cohort["audit"]["completed"]),
            "raw_failures": int(cohort["audit"]["failures"]),
            "atlas_ready_bars": int(cohort["coverage"]["atlas_ready_rows"].sum()),
            "horizons": list(HORIZONS),
            "blocks": list(BLOCK_LABELS),
            "sleeves": list(cohort["sleeves"]),
            "oos4_touched": False,
            "oos5_touched": False,
        },
        "frozen": {
            "d1": "dir_structure (A1, reused)",
            "d2": "extension = |dir_velocity| (A1, reused)",
            "d3_primary": "rv20 = 20d realised log-return vol, causal 252-pct",
            "d3_robustness": "natr20 = gap-safe WilderATR20/close, causal 252-pct",
            "d4": "ER20, causal 252-pct",
            "bins": "LOW<=0.30, HIGH>=0.70 descriptive; Core-2 hard 80/20 for conditioning",
            "hmm": "pooled diagonal-Gaussian EM, K in {2,3,4,5} by train BIC, split 2015-01-01",
            "hmm_selected_K": int(model["K"]),
            "hmm_train_end": HMM_TRAIN_END,
        },
        "classification": classification,
        "hmm_verdict": verdict,
        "notes": [
            "OOS3 is deliberately reused discovery under the 2026-10-05 amendment.",
            "No result from this run is fresh OOS evidence.",
            "HMM is a benchmark; the Atlas stays primary.",
            "OOS4 replication is conditional on an OOS3 KEEP candidate.",
        ],
    }
    (out / "summary.json").write_text(
        json.dumps(summary, indent=2, default=str) + "\n", encoding="utf-8"
    )

    bundle_files = sorted(
        p.name for p in out.iterdir() if p.is_file() and p.name != "bundle_hashes.json"
    )
    bundle = {
        "prereg_commit": prereg_sha,
        "figi_set_sha256": cohort["figi_set_sha256"],
        "universe_sha256": sha256_file(universe_path),
        "manifest_sha256": sha256_file(manifest_path),
        "classifier_blob": cohort["blob"],
        "files": {name: sha256_file(out / name) for name in bundle_files},
    }
    (out / "bundle_hashes.json").write_text(
        json.dumps(bundle, indent=2, default=str) + "\n", encoding="utf-8"
    )
    print(json.dumps(summary, indent=2, default=str))
    return summary


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
    ap.add_argument("--prereg-sha", default="")
    ap.add_argument(
        "--limit",
        type=int,
        default=0,
        help="plumbing smoke test only; 0 = full frozen cohort",
    )
    ap.add_argument(
        "--offset",
        type=int,
        default=0,
        help="plumbing smoke test only; only used together with --limit",
    )
    args = ap.parse_args()
    for contact in (args.universe, args.manifest, args.raw_dir):
        assert "oos3" in str(contact).lower() or "snapshot" in str(contact).lower(), (
            "OOS3 discovery stage must not contact OOS4 paths"
        )
    run_discovery(
        args.universe, args.manifest, args.raw_dir, args.classifier,
        args.out, args.prereg_sha, limit=args.limit, offset=args.offset,
    )


if __name__ == "__main__":
    main()
