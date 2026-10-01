#!/usr/bin/env python3
"""Issue #141 — preregistered monthly structural-analogue signal bridge.

This evaluator is intentionally signal-only. It never loads asset-return
outcomes. It compares a frozen monthly structural analogue of V6.6 GPI/IPI
against the frozen exact V6.6 monthly signal snapshot.
"""
from __future__ import annotations

import argparse
import base64
import gzip
import hashlib
import io
import json
import math
import sys
from pathlib import Path

import numpy as np
import pandas as pd

import issue_141_source_acquisition as src

EXPECTED_EXACT_SHA = "1d03923503e7fe82a69b033897484c48aa646279ecf70164d090ed62a5a70719"
EXPECTED_SOURCE_SHA = {
    "french_factors": "593f4fbef03181bc0b22ff6292f217689dd1fb79355049ca905d95b262040a66",
    "french_12_industry": "309eb6b2bdbb5bc45f039b9814753b079cd40bd4038ffda9afb6c5e0563fd120",
    "world_bank_monthly": "9fdcfa8a2aed9a1bb545a10c1a5ce036c6a0acd4766f450424ca800b4b5a0225",
    "cleveland_inflation_expectations": "20701ccf394d280fe1db38fa9def5628f2385dd0aef148ff989e33ff15caba95",
}
DEV_START = pd.Period("2007-01", freq="M")
DEV_END = pd.Period("2016-12", freq="M")
HOLD_START = pd.Period("2017-01", freq="M")
HIST_START = pd.Period("1984-01", freq="M")
HIST_END = pd.Period("2006-12", freq="M")


def sha256(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def zscore_rolling(s: pd.Series, n: int) -> pd.Series:
    mean = s.rolling(n, min_periods=n).mean()
    sd = s.rolling(n, min_periods=n).std(ddof=1)
    out = (s - mean) / sd
    return out.where(sd.ne(0))


def component_score(level: pd.Series) -> pd.Series:
    x = pd.to_numeric(level, errors="coerce").astype(float)
    x = x.where(x.gt(0))
    lvl = zscore_rolling(x, 12)
    roc_fast = (x / x.shift(1) - 1.0) * 100.0
    roc_mid = (x / x.shift(3) - 1.0) * 100.0
    mom_raw = 0.6 * roc_fast + 0.4 * roc_mid
    mom = zscore_rolling(mom_raw, 12)
    sd = x.rolling(12, min_periods=12).std(ddof=1)
    sma1 = x
    sma3 = x.rolling(3, min_periods=3).mean()
    dir_raw = (sma1 - sma3) / sd
    direction = np.tanh(dir_raw)
    raw = 0.5 * lvl + 0.3 * mom + 0.2 * direction
    score = 100.0 * np.tanh(raw / 2.0)
    return score.where(lvl.notna() & mom.notna() & direction.notna())


def wealth_from_pct_return(ret_pct: pd.Series) -> pd.Series:
    r = pd.to_numeric(ret_pct, errors="coerce") / 100.0
    mult = 1.0 + r
    if (mult.dropna() <= 0).any():
        raise RuntimeError("wealth construction encountered return <= -100%")
    # French monthly series are complete in the frozen source. Fail closed on gaps.
    if r.isna().any():
        raise RuntimeError("wealth construction encountered missing monthly return")
    return mult.cumprod()


def load_frozen_sources() -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame, dict]:
    raw_factors = src.fetch(src.FRENCH_FACTORS)
    raw_ind = src.fetch(src.FRENCH_12IND)
    wb_url, _ = src.locate_world_bank_monthly_url()
    raw_wb = src.fetch(wb_url)
    cleveland_url, _ = src.locate_cleveland_xlsx()
    raw_cleveland = src.fetch(cleveland_url)

    observed = {
        "french_factors": sha256(raw_factors),
        "french_12_industry": sha256(raw_ind),
        "world_bank_monthly": sha256(raw_wb),
        "cleveland_inflation_expectations": sha256(raw_cleveland),
    }
    drift = {
        k: {"expected": EXPECTED_SOURCE_SHA[k], "observed": observed[k]}
        for k in EXPECTED_SOURCE_SHA
        if observed[k] != EXPECTED_SOURCE_SHA[k]
    }
    if drift:
        raise RuntimeError(f"Issue #141 frozen source hash drift: {json.dumps(drift, sort_keys=True)}")

    factors = src.parse_french_block(
        src.first_member_text(raw_factors), {"Mkt-RF", "SMB", "RF"}
    )
    industries = src.parse_french_block(
        src.first_member_text(raw_ind), {"NoDur", "Durbl", "Manuf", "Utils", "Shops"}
    )
    wb_prices = src.wb_sheet(raw_wb, "Monthly Prices")
    wb = src.selected_world_bank_panel(wb_prices)
    cleveland = src.selected_cleveland_panel(raw_cleveland)
    meta = {
        "raw_sha256": observed,
        "world_bank_url": wb_url,
        "cleveland_url": cleveland_url,
    }
    return factors, industries, wb, cleveland, meta


def with_period(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    out["period"] = pd.to_datetime(out["date"]).dt.to_period("M")
    if out["period"].duplicated().any():
        dup = out.loc[out["period"].duplicated(keep=False), "period"].astype(str).tolist()
        raise RuntimeError(f"duplicate monthly period: {dup[:10]}")
    return out.sort_values("period").reset_index(drop=True)


def build_analogue(
    factors: pd.DataFrame,
    industries: pd.DataFrame,
    wb: pd.DataFrame,
    cleveland: pd.DataFrame,
) -> pd.DataFrame:
    f = with_period(factors)
    ind = with_period(industries)
    w = with_period(wb)
    c = with_period(cleveland)

    fcols = ["period", "Mkt-RF", "SMB", "RF"]
    industry_cols = [x for x in ind.columns if x not in {"date", "period"}]
    required_ind = {"NoDur", "Durbl", "Manuf", "Utils", "Shops"}
    if not required_ind.issubset(set(industry_cols)):
        raise RuntimeError("required industry columns missing")
    if len(industry_cols) != 12:
        raise RuntimeError(f"expected 12 French industry portfolios, got {industry_cols}")

    x = f[fcols].merge(
        ind[["period"] + industry_cols],
        on="period",
        how="inner",
        validate="one_to_one",
    )
    x = x.merge(
        w.drop(columns=["date"]),
        on="period",
        how="outer",
        validate="one_to_one",
    )
    x = x.merge(
        c.drop(columns=["date"]),
        on="period",
        how="outer",
        validate="one_to_one",
    ).sort_values("period").reset_index(drop=True)

    # Wealth-based equity-growth proxy levels.
    # Build these only on the complete French history, then merge by month.
    fr = f[fcols].merge(
        ind[["period"] + industry_cols],
        on="period",
        how="inner",
        validate="one_to_one",
    ).sort_values("period").reset_index(drop=True)

    fr["small_relative_level"] = wealth_from_pct_return(fr["SMB"])
    ind_ew_ret = fr[industry_cols].astype(float).mean(axis=1)
    market_ret = fr["Mkt-RF"].astype(float) + fr["RF"].astype(float)
    fr["industry_ew_wealth"] = wealth_from_pct_return(ind_ew_ret)
    fr["market_wealth"] = wealth_from_pct_return(market_ret)
    fr["breadth_level"] = fr["industry_ew_wealth"] / fr["market_wealth"]

    cyc_ret = fr[["Durbl", "Shops"]].astype(float).mean(axis=1)
    def_ret = fr["NoDur"].astype(float)
    fr["cyc_wealth"] = wealth_from_pct_return(cyc_ret)
    fr["def_wealth"] = wealth_from_pct_return(def_ret)
    fr["cyc_def_level"] = fr["cyc_wealth"] / fr["def_wealth"]

    fr["manuf_wealth"] = wealth_from_pct_return(fr["Manuf"].astype(float))
    fr["utils_wealth"] = wealth_from_pct_return(fr["Utils"].astype(float))
    fr["manuf_utils_level"] = fr["manuf_wealth"] / fr["utils_wealth"]

    levels = fr[
        ["period", "small_relative_level", "breadth_level", "cyc_def_level", "manuf_utils_level"]
    ].copy()
    x = x.drop(
        columns=[
            "small_relative_level", "breadth_level", "cyc_def_level", "manuf_utils_level"
        ],
        errors="ignore",
    ).merge(levels, on="period", how="left", validate="one_to_one")

    x["copper_gold_level"] = x["Copper"] / x["Gold"]

    commodity_cols = [
        "Crude oil, WTI",
        "Natural gas, US",
        "Aluminum",
        "Copper",
        "Wheat, US HRW",
        "Maize",
        "Coffee, Arabica",
        "Sugar, world",
    ]
    positive_complete = x[commodity_cols].notna().all(axis=1) & x[commodity_cols].gt(0).all(axis=1)
    x["commodity_basket_level"] = np.nan
    x.loc[positive_complete, "commodity_basket_level"] = np.exp(
        np.log(x.loc[positive_complete, commodity_cols].astype(float)).mean(axis=1)
    )

    # Frozen monthly component-score formula.
    gpi_map = {
        "gpi_small": "small_relative_level",
        "gpi_breadth": "breadth_level",
        "gpi_cyc_def": "cyc_def_level",
        "gpi_manuf_utils": "manuf_utils_level",
        "gpi_copper_gold": "copper_gold_level",
    }
    for score_col, level_col in gpi_map.items():
        x[score_col] = component_score(x[level_col])

    x["ipi_expected"] = component_score(x["expected_inflation_10y"])
    x["ipi_commodity"] = component_score(x["commodity_basket_level"])
    x["ipi_wti"] = component_score(x["Crude oil, WTI"])
    x["ipi_natgas"] = component_score(x["Natural gas, US"])
    x["ipi_energy"] = x[["ipi_wti", "ipi_natgas"]].mean(axis=1, skipna=False)

    gpi_cols = list(gpi_map)
    x["gpi_a"] = x[gpi_cols].mean(axis=1, skipna=False)
    x["ipi_a"] = (
        0.35 * x["ipi_expected"]
        + 0.40 * x["ipi_commodity"]
        + 0.25 * x["ipi_energy"]
    )
    x["analogue_eligible"] = x[gpi_cols + ["ipi_expected", "ipi_commodity", "ipi_wti", "ipi_natgas"]].notna().all(axis=1)
    x.loc[~x["analogue_eligible"], ["gpi_a", "ipi_a"]] = np.nan
    x["regime_a"] = [
        regime_id(g, i) if np.isfinite(g) and np.isfinite(i) else np.nan
        for g, i in zip(x["gpi_a"].to_numpy(float), x["ipi_a"].to_numpy(float))
    ]
    x["date"] = x["period"].dt.to_timestamp("M")
    return x


def regime_id(gpi: float, ipi: float) -> int:
    g = 1 if gpi > 10.0 else (-1 if gpi < -10.0 else 0)
    i = 1 if ipi > 10.0 else (-1 if ipi < -10.0 else 0)
    mapping = {
        (1, -1): 1,
        (1, 0): 2,
        (1, 1): 3,
        (0, -1): 4,
        (0, 0): 5,
        (0, 1): 6,
        (-1, -1): 7,
        (-1, 0): 8,
        (-1, 1): 9,
    }
    return mapping[(g, i)]


def load_exact(issue133_root: Path) -> tuple[pd.DataFrame, dict]:
    data = issue133_root / "data"
    manifest = json.loads(
        (data / "issue-133-exact-monthly-manifest.json").read_text(encoding="utf-8")
    )
    if manifest["normalized_csv_sha256"] != EXPECTED_EXACT_SHA:
        raise RuntimeError("Issue #141 exact source manifest SHA drift")
    gz = base64.b64decode(
        (data / "issue-133-exact-monthly.csv.gz.b64").read_text().strip(),
        validate=True,
    )
    if hashlib.sha256(gz).hexdigest() != manifest["deterministic_gzip_sha256"]:
        raise RuntimeError("Issue #141 exact source gzip SHA drift")
    csv_bytes = gzip.decompress(gz)
    if hashlib.sha256(csv_bytes).hexdigest() != EXPECTED_EXACT_SHA:
        raise RuntimeError("Issue #141 exact normalized CSV SHA drift")
    x = pd.read_csv(io.BytesIO(csv_bytes))
    if list(x.columns) != ["date", "gpi", "ipi", "regime"]:
        raise RuntimeError(f"unexpected exact columns: {list(x.columns)}")
    x["date"] = pd.to_datetime(x["date"], errors="raise")
    x["period"] = x["date"].dt.to_period("M")
    x["gpi"] = pd.to_numeric(x["gpi"], errors="raise")
    x["ipi"] = pd.to_numeric(x["ipi"], errors="raise")
    x["regime"] = pd.to_numeric(x["regime"], errors="raise").astype(int)
    if x["period"].duplicated().any():
        raise RuntimeError("duplicate exact monthly period")
    return x.sort_values("period").reset_index(drop=True), manifest


def assign_episode_id(regime: pd.Series, periods: pd.Series) -> pd.Series:
    ids = []
    eid = 0
    prev_r7 = False
    prev_ord = None
    for r, p in zip(regime, periods):
        is_r7 = pd.notna(r) and int(r) == 7
        ord_ = p.ordinal
        consecutive = prev_ord is not None and ord_ == prev_ord + 1
        if is_r7 and (not prev_r7 or not consecutive):
            eid += 1
        ids.append(eid if is_r7 else 0)
        prev_r7 = is_r7
        prev_ord = ord_
    return pd.Series(ids, index=regime.index, dtype=int)


def add_turning(frame: pd.DataFrame, gcol: str, icol: str, rcol: str, prefix: str) -> pd.DataFrame:
    x = frame.copy().sort_values("period").reset_index(drop=True)
    dg = x[gcol].diff()
    di = x[icol].diff()
    gturn = (dg > 0) & (dg.shift(1) <= 0)
    iturn = (di > 0) & (di.shift(1) <= 0)
    grecent = gturn.rolling(3, min_periods=3).max().fillna(0).astype(bool)
    irecent = iturn.rolling(3, min_periods=3).max().fillna(0).astype(bool)
    x[f"{prefix}_episode_id"] = assign_episode_id(x[rcol], x["period"])
    candidate = x[rcol].eq(7) & grecent & irecent & x[gcol].notna() & x[icol].notna()
    trigger = pd.Series(False, index=x.index, dtype=bool)
    for _, group in x.loc[x[f"{prefix}_episode_id"].gt(0)].groupby(
        f"{prefix}_episode_id", sort=True
    ):
        hits = group.index[candidate.loc[group.index]]
        if len(hits):
            trigger.loc[hits[0]] = True
    x[f"{prefix}_trigger"] = trigger
    return x


def pearson(a: pd.Series, b: pd.Series) -> float | None:
    ok = a.notna() & b.notna()
    if int(ok.sum()) < 12:
        return None
    aa = a.loc[ok].astype(float)
    bb = b.loc[ok].astype(float)
    if aa.std(ddof=1) == 0 or bb.std(ddof=1) == 0:
        return None
    return float(aa.corr(bb))


def sign_agreement(frame: pd.DataFrame, exact_col: str, analogue_col: str) -> dict:
    e = frame[exact_col].astype(float)
    a = frame[analogue_col].astype(float)
    de = e.diff()
    da = a.diff()
    periods = frame["period"]
    consecutive = periods.map(lambda p: p.ordinal).diff().eq(1)
    ok = de.notna() & da.notna() & consecutive
    n = int(ok.sum())
    if n < 12:
        return {"n": n, "agreement": None}
    es = np.sign(de.loc[ok].to_numpy())
    aas = np.sign(da.loc[ok].to_numpy())
    return {"n": n, "agreement": float(np.mean(es == aas))}


def r7_precision_recall(frame: pd.DataFrame) -> dict:
    e = frame["regime"].eq(7)
    a = frame["regime_a"].eq(7)
    tp = int((e & a).sum())
    ap = int(a.sum())
    ep = int(e.sum())
    precision = float(tp / ap) if ap else None
    recall = float(tp / ep) if ep else None
    return {
        "true_positive_months": tp,
        "analogue_r7_months": ap,
        "exact_r7_months": ep,
        "precision": precision,
        "recall": recall,
    }


def trigger_match(exact_periods: list[pd.Period], analogue_periods: list[pd.Period]) -> dict:
    if not exact_periods and not analogue_periods:
        return {
            "exact_n": 0, "analogue_n": 0, "matched": 0,
            "precision": None, "recall": None, "f1": None, "count_ratio": None,
            "pairs": [],
        }
    candidates = []
    for e in exact_periods:
        for a in analogue_periods:
            dist = abs(e.ordinal - a.ordinal)
            if dist <= 1:
                candidates.append((dist, e.ordinal, a.ordinal, e, a))
    candidates.sort(key=lambda z: (z[0], z[1], z[2]))
    used_e: set[int] = set()
    used_a: set[int] = set()
    pairs = []
    for dist, eo, ao, ep, ap in candidates:
        if eo in used_e or ao in used_a:
            continue
        used_e.add(eo)
        used_a.add(ao)
        pairs.append({
            "exact": str(ep),
            "analogue": str(ap),
            "month_distance": int(dist),
        })
    matched = len(pairs)
    en = len(exact_periods)
    an = len(analogue_periods)
    if en > 0 and an == 0:
        precision = recall = f1 = 0.0
    else:
        precision = float(matched / an) if an else None
        recall = float(matched / en) if en else None
        if precision is None or recall is None or precision + recall == 0:
            f1 = 0.0 if precision is not None and recall is not None else None
        else:
            f1 = float(2 * precision * recall / (precision + recall))
    ratio = float(an / en) if en else None
    return {
        "exact_n": en,
        "analogue_n": an,
        "matched": matched,
        "precision": precision,
        "recall": recall,
        "f1": f1,
        "count_ratio": ratio,
        "pairs": pairs,
    }


def period_metrics(
    merged: pd.DataFrame,
    exact_turn: pd.DataFrame,
    analogue_turn: pd.DataFrame,
    start: pd.Period,
    end: pd.Period,
) -> dict:
    f = merged.loc[merged["period"].between(start, end)].copy()
    eligible = (
        f["gpi"].notna()
        & f["ipi"].notna()
        & f["regime"].notna()
        & f["gpi_a"].notna()
        & f["ipi_a"].notna()
        & f["regime_a"].notna()
    )
    f = f.loc[eligible].sort_values("period").reset_index(drop=True)

    slope_g = sign_agreement(f, "gpi", "gpi_a")
    slope_i = sign_agreement(f, "ipi", "ipi_a")
    regime_agreement = (
        float((f["regime"].astype(int) == f["regime_a"].astype(int)).mean())
        if len(f) else None
    )
    r7 = r7_precision_recall(f) if len(f) else {
        "true_positive_months": 0,
        "analogue_r7_months": 0,
        "exact_r7_months": 0,
        "precision": None,
        "recall": None,
    }
    eligible_periods = set(f["period"])
    et = [
        p for p in exact_turn.loc[
            exact_turn["exact_trigger"] & exact_turn["period"].between(start, end),
            "period",
        ].tolist()
        if p in eligible_periods
    ]
    at = [
        p for p in analogue_turn.loc[
            analogue_turn["analogue_trigger"] & analogue_turn["period"].between(start, end),
            "period",
        ].tolist()
        if p in eligible_periods
    ]
    triggers = trigger_match(et, at)
    return {
        "start": str(start),
        "end": str(end),
        "common_eligible_months": int(len(f)),
        "gpi_correlation": pearson(f["gpi"], f["gpi_a"]) if len(f) else None,
        "ipi_correlation": pearson(f["ipi"], f["ipi_a"]) if len(f) else None,
        "gpi_slope_sign": slope_g,
        "ipi_slope_sign": slope_i,
        "regime_agreement": regime_agreement,
        "r7": r7,
        "triggers": triggers,
    }


def subsegment_regime(merged: pd.DataFrame, start: str, end: str) -> dict:
    ps = pd.Period(start, freq="M")
    pe = pd.Period(end, freq="M")
    f = merged.loc[merged["period"].between(ps, pe)].copy()
    ok = (
        f["gpi"].notna()
        & f["ipi"].notna()
        & f["regime"].notna()
        & f["gpi_a"].notna()
        & f["ipi_a"].notna()
        & f["regime_a"].notna()
    )
    f = f.loc[ok]
    n = int(len(f))
    evaluable = n >= 12
    agreement = (
        float((f["regime"].astype(int) == f["regime_a"].astype(int)).mean())
        if evaluable else None
    )
    return {
        "segment": f"{start[:4]}-{end[:4]}",
        "start": start,
        "end": end,
        "common_eligible_months": n,
        "evaluable": evaluable,
        "regime_agreement": agreement,
    }


def evaluate_bridge(exact: pd.DataFrame, analogue: pd.DataFrame) -> tuple[dict, pd.DataFrame, pd.DataFrame]:
    exact_use = exact.loc[exact["period"].ge(pd.Period("2007-01", freq="M"))].copy()
    ana_use = analogue.loc[analogue["period"].ge(pd.Period("2007-01", freq="M"))].copy()
    exact_turn = add_turning(exact_use, "gpi", "ipi", "regime", "exact")
    analogue_turn = add_turning(ana_use, "gpi_a", "ipi_a", "regime_a", "analogue")

    merged = exact_turn[
        ["period", "date", "gpi", "ipi", "regime", "exact_trigger", "exact_episode_id"]
    ].merge(
        analogue_turn[
            ["period", "gpi_a", "ipi_a", "regime_a", "analogue_trigger", "analogue_episode_id"]
        ],
        on="period",
        how="inner",
        validate="one_to_one",
    )

    latest = min(
        exact_use["period"].max(),
        ana_use.loc[ana_use["gpi_a"].notna() & ana_use["ipi_a"].notna(), "period"].max(),
    )
    development = period_metrics(
        merged, exact_turn, analogue_turn, DEV_START, min(DEV_END, latest)
    )
    holdout = period_metrics(
        merged, exact_turn, analogue_turn, HOLD_START, latest
    )
    segments = [
        subsegment_regime(merged, "2017-01", "2019-12"),
        subsegment_regime(merged, "2020-01", "2022-12"),
        subsegment_regime(merged, "2023-01", str(latest)),
    ]
    eval_segments = [x for x in segments if x["evaluable"]]

    h = holdout
    gates = {
        "1_common_eligible_months_ge_60": h["common_eligible_months"] >= 60,
        "2_exact_triggers_ge_4": h["triggers"]["exact_n"] >= 4,
        "3_gpi_correlation_ge_0_70": bool(h["gpi_correlation"] is not None and h["gpi_correlation"] >= 0.70),
        "4_ipi_correlation_ge_0_70": bool(h["ipi_correlation"] is not None and h["ipi_correlation"] >= 0.70),
        "5_gpi_slope_agreement_ge_0_70": bool(h["gpi_slope_sign"]["agreement"] is not None and h["gpi_slope_sign"]["agreement"] >= 0.70),
        "6_ipi_slope_agreement_ge_0_70": bool(h["ipi_slope_sign"]["agreement"] is not None and h["ipi_slope_sign"]["agreement"] >= 0.70),
        "7_regime_agreement_ge_0_60": bool(h["regime_agreement"] is not None and h["regime_agreement"] >= 0.60),
        "8_r7_precision_ge_0_60": bool(h["r7"]["precision"] is not None and h["r7"]["precision"] >= 0.60),
        "9_r7_recall_ge_0_60": bool(h["r7"]["recall"] is not None and h["r7"]["recall"] >= 0.60),
        "10_trigger_f1_ge_0_60": bool(h["triggers"]["f1"] is not None and h["triggers"]["f1"] >= 0.60),
        "11_trigger_count_ratio_0_50_to_2_00": bool(h["triggers"]["count_ratio"] is not None and 0.50 <= h["triggers"]["count_ratio"] <= 2.00),
        "12_each_evaluable_segment_regime_agreement_ge_0_45": bool(
            len(eval_segments) > 0
            and all(x["regime_agreement"] is not None and x["regime_agreement"] >= 0.45 for x in eval_segments)
        ),
    }
    if not gates["1_common_eligible_months_ge_60"] or not gates["2_exact_triggers_ge_4"]:
        verdict = "signal_bridge_inconclusive_sample"
    elif all(gates.values()):
        verdict = "signal_bridge_passed"
    else:
        verdict = "signal_bridge_failed"

    result = {
        "development": development,
        "holdout": holdout,
        "holdout_subsegments": segments,
        "gates": gates,
        "verdict": verdict,
        "validated_for_outcome_testing": verdict == "signal_bridge_passed",
        "latest_common_month": str(latest),
    }
    return result, merged, analogue_turn


def run(issue133_root: Path, outdir: Path) -> dict:
    outdir.mkdir(parents=True, exist_ok=True)
    factors, industries, wb, cleveland, source_meta = load_frozen_sources()
    exact, exact_manifest = load_exact(issue133_root)
    analogue = build_analogue(factors, industries, wb, cleveland)

    bridge, merged, analogue_turn = evaluate_bridge(exact, analogue)
    historical = analogue_turn.loc[
        analogue_turn["period"].between(HIST_START, HIST_END),
        [
            "date", "period", "gpi_a", "ipi_a", "regime_a",
            "analogue_episode_id", "analogue_trigger", "analogue_eligible",
        ],
    ].copy()
    historical["validated_for_outcome_testing"] = bridge["validated_for_outcome_testing"]

    merged.to_csv(outdir / "issue-141-modern-bridge-evidence.csv", index=False, float_format="%.12g")
    historical.to_csv(outdir / "issue-141-historical-signals-1984-2006.csv", index=False, float_format="%.12g")

    result = {
        "schema_version": 1,
        "issue": 141,
        "phase": "monthly-structural-analogue-signal-bridge",
        "source_meta": source_meta,
        "exact_signal_sha256": exact_manifest["normalized_csv_sha256"],
        "bridge": bridge,
        "historical_signal_sample": {
            "rows": int(len(historical)),
            "eligible_rows": int(historical["analogue_eligible"].sum()),
            "first_eligible_month": (
                str(historical.loc[historical["analogue_eligible"], "period"].min())
                if historical["analogue_eligible"].any() else None
            ),
            "last_eligible_month": (
                str(historical.loc[historical["analogue_eligible"], "period"].max())
                if historical["analogue_eligible"].any() else None
            ),
            "r7_months": int(historical["regime_a"].eq(7).sum()),
            "async_turn_triggers": int(historical["analogue_trigger"].sum()),
            "trigger_months": [
                str(p) for p in historical.loc[historical["analogue_trigger"], "period"].tolist()
            ],
        },
        "outcome_data_loaded": False,
        "production_authorized": False,
    }
    (outdir / "issue-141-result.json").write_text(
        json.dumps(result, indent=2, ensure_ascii=False, allow_nan=False) + "\n",
        encoding="utf-8",
    )

    finding = [
        "# Issue #141 — monthly structural analogue signal bridge",
        "",
        f"Formal bridge verdict: **{bridge['verdict']}**",
        "",
        f"Holdout: 2017-01 through {bridge['latest_common_month']}.",
        f"Common eligible months: {bridge['holdout']['common_eligible_months']}.",
        f"Exact holdout async triggers: {bridge['holdout']['triggers']['exact_n']}.",
        f"Analogue holdout async triggers: {bridge['holdout']['triggers']['analogue_n']}.",
        "",
        f"GPI correlation: {bridge['holdout']['gpi_correlation']}.",
        f"IPI correlation: {bridge['holdout']['ipi_correlation']}.",
        f"Regime agreement: {bridge['holdout']['regime_agreement']}.",
        f"R7 precision: {bridge['holdout']['r7']['precision']}.",
        f"R7 recall: {bridge['holdout']['r7']['recall']}.",
        f"Trigger F1: {bridge['holdout']['triggers']['f1']}.",
        "",
        f"Validated for historical outcome testing: **{bridge['validated_for_outcome_testing']}**.",
        "",
        "No asset-return outcome was loaded by this study.",
        "No production rule is authorized.",
    ]
    (outdir / "issue-141-finding.md").write_text("\n".join(finding) + "\n", encoding="utf-8")
    return result


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--issue133-root", type=Path, required=True)
    ap.add_argument("--output-dir", type=Path, required=True)
    args = ap.parse_args()
    r = run(args.issue133_root, args.output_dir)
    print(json.dumps({
        "verdict": r["bridge"]["verdict"],
        "validated_for_outcome_testing": r["bridge"]["validated_for_outcome_testing"],
        "holdout": r["bridge"]["holdout"],
        "gates": r["bridge"]["gates"],
        "historical_signal_sample": r["historical_signal_sample"],
        "outcome_data_loaded": r["outcome_data_loaded"],
    }, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
