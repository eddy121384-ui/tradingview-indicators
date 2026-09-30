#!/usr/bin/env python3
"""CRSP CIZ data contract for Issue #78 Cross-Sectional OOS2.

This module contains *no strategy economics*. It only validates and normalizes
the frozen CRSP inputs needed before formal OOS2 can begin.
"""
from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
from pathlib import Path

import numpy as np
import pandas as pd

RAW_START = pd.Timestamp("1998-01-01")
EVENT_START = pd.Timestamp("2000-01-03")
EVENT_END = pd.Timestamp("2026-08-31")

ELIGIBLE_PRIMARY_EXCH = {"N", "A", "Q"}
ELIGIBLE_SECURITY_TYPE = "EQTY"
ELIGIBLE_SECURITY_SUBTYPE = "COM"
INELIGIBLE_SHARE_TYPES = {"ADR", "SBI"}

DAILY_REQUIRED = {
    "permno",
    "dlycaldt",
    "dlyopen",
    "dlyhigh",
    "dlylow",
    "dlyclose",
    "dlyprc",
    "dlyvol",
    "dlyretx",
    "dlydelflg",
}
FACTOR_REQUIRED = {"permno", "dlycaldt", "dlycumfacpr", "dlycumfacshr"}
INFO_REQUIRED = {
    "permno",
    "secinfostartdt",
    "secinfoenddt",
    "primaryexch",
    "securitytype",
    "securitysubtype",
    "sharetype",
    "issuertype",
    "usincflg",
    "ticker",
    "tradingsymbol",
    "siccd",
}


def _canon(frame: pd.DataFrame) -> pd.DataFrame:
    out = frame.copy()
    out.columns = [str(c).strip().lower() for c in out.columns]
    return out


def require_columns(frame: pd.DataFrame, required: set[str], label: str) -> None:
    missing = sorted(required.difference(frame.columns))
    if missing:
        raise ValueError(f"{label} missing required columns: {missing}")


def file_sha256(path: Path) -> str:
    h = sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def normalize_crsp(
    daily: pd.DataFrame,
    factors: pd.DataFrame,
    info_hist: pd.DataFrame,
) -> pd.DataFrame:
    """Return one split-consistent, point-in-time classified CRSP daily panel."""
    d = _canon(daily)
    f = _canon(factors)
    i = _canon(info_hist)
    require_columns(d, DAILY_REQUIRED, "daily")
    require_columns(f, FACTOR_REQUIRED, "factors")
    require_columns(i, INFO_REQUIRED, "info_hist")

    for frame, date_cols in (
        (d, ["dlycaldt"]),
        (f, ["dlycaldt"]),
        (i, ["secinfostartdt", "secinfoenddt"]),
    ):
        for col in date_cols:
            frame[col] = pd.to_datetime(frame[col], errors="coerce")

    d = d[(d["dlycaldt"] >= RAW_START) & (d["dlycaldt"] <= EVENT_END)].copy()
    f = f[(f["dlycaldt"] >= RAW_START) & (f["dlycaldt"] <= EVENT_END)].copy()

    panel = d.merge(
        f[["permno", "dlycaldt", "dlycumfacpr", "dlycumfacshr"]],
        on=["permno", "dlycaldt"],
        how="left",
        validate="one_to_one",
    )

    # Point-in-time interval join via merge_asof by PERMNO and start date.
    panel = panel.sort_values(["permno", "dlycaldt"]).reset_index(drop=True)
    info = i.sort_values(["permno", "secinfostartdt"]).reset_index(drop=True)
    chunks: list[pd.DataFrame] = []
    for permno, bars in panel.groupby("permno", sort=False):
        hist = info[info["permno"] == permno]
        if hist.empty:
            tmp = bars.copy()
            for col in INFO_REQUIRED.difference({"permno"}):
                tmp[col] = pd.NA
            chunks.append(tmp)
            continue
        tmp = pd.merge_asof(
            bars.sort_values("dlycaldt"),
            hist.drop(columns=["permno"]).sort_values("secinfostartdt"),
            left_on="dlycaldt",
            right_on="secinfostartdt",
            direction="backward",
            allow_exact_matches=True,
        )
        valid_interval = (
            tmp["secinfostartdt"].notna()
            & (
                tmp["secinfoenddt"].isna()
                | (tmp["dlycaldt"] <= tmp["secinfoenddt"])
            )
        )
        for col in INFO_REQUIRED.difference({"permno"}):
            tmp.loc[~valid_interval, col] = pd.NA
        chunks.append(tmp)
    panel = pd.concat(chunks, ignore_index=True) if chunks else panel.iloc[0:0].copy()

    facpr = pd.to_numeric(panel["dlycumfacpr"], errors="coerce")
    facshr = pd.to_numeric(panel["dlycumfacshr"], errors="coerce")
    factor_ok = facpr.gt(0) & facshr.gt(0)

    for src, dst in (
        ("dlyopen", "open"),
        ("dlyhigh", "high"),
        ("dlylow", "low"),
        ("dlyclose", "close"),
    ):
        raw = pd.to_numeric(panel[src], errors="coerce")
        panel[dst] = np.where(factor_ok, raw / facpr, np.nan)

    raw_volume = pd.to_numeric(panel["dlyvol"], errors="coerce")
    panel["volume"] = np.where(factor_ok, raw_volume * facshr, np.nan)
    panel["dollar_volume"] = panel["close"] * panel["volume"]

    share = panel["sharetype"].astype("string").str.upper()
    panel["eligible_security_type"] = (
        panel["primaryexch"].astype("string").str.upper().isin(ELIGIBLE_PRIMARY_EXCH)
        & panel["securitytype"].astype("string").str.upper().eq(ELIGIBLE_SECURITY_TYPE)
        & panel["securitysubtype"].astype("string").str.upper().eq(ELIGIBLE_SECURITY_SUBTYPE)
        & ~share.isin(INELIGIBLE_SHARE_TYPES)
    )

    ohlc_ok = (
        panel[["open", "high", "low", "close"]].notna().all(axis=1)
        & (panel[["open", "high", "low", "close"]] > 0).all(axis=1)
        & (panel["high"] >= panel[["open", "close", "low"]].max(axis=1))
        & (panel["low"] <= panel[["open", "close", "high"]].min(axis=1))
    )
    panel["valid_classifier_bar"] = factor_ok & ohlc_ok & panel["volume"].ge(0)

    panel = panel.rename(columns={"dlycaldt": "date"})
    return panel.sort_values(["permno", "date"]).reset_index(drop=True)


def add_entry_eligibility(panel: pd.DataFrame) -> pd.DataFrame:
    """Add causal 252-bar history and 60-session liquidity eligibility fields."""
    out = panel.copy().sort_values(["permno", "date"]).reset_index(drop=True)
    out["prior_valid_bars"] = 0
    out["median_dollar_volume_60"] = np.nan

    for _, idx in out.groupby("permno", sort=False).groups.items():
        loc = np.asarray(list(idx), dtype=int)
        valid = out.loc[loc, "valid_classifier_bar"].astype(bool).to_numpy()
        dollar = pd.to_numeric(out.loc[loc, "dollar_volume"], errors="coerce")

        prior = np.zeros(len(loc), dtype=int)
        if len(loc) > 1:
            prior[1:] = np.cumsum(valid[:-1])
        med60 = dollar.rolling(60, min_periods=60).median().to_numpy()

        out.loc[loc, "prior_valid_bars"] = prior
        out.loc[loc, "median_dollar_volume_60"] = med60

    out["entry_eligible"] = (
        out["eligible_security_type"].astype(bool)
        & out["valid_classifier_bar"].astype(bool)
        & out["date"].between(EVENT_START, EVENT_END)
        & out["prior_valid_bars"].ge(252)
        & out["close"].ge(5.0)
        & out["median_dollar_volume_60"].ge(5_000_000.0)
    )
    return out


@dataclass(frozen=True)
class SnapshotStats:
    rows: int
    securities: int
    min_date: str | None
    max_date: str | None
    valid_bars: int
    point_in_time_eligible_bars: int


def snapshot_stats(panel: pd.DataFrame) -> SnapshotStats:
    dates = pd.to_datetime(panel["date"], errors="coerce")
    return SnapshotStats(
        rows=int(len(panel)),
        securities=int(panel["permno"].nunique(dropna=True)),
        min_date=None if dates.dropna().empty else str(dates.min().date()),
        max_date=None if dates.dropna().empty else str(dates.max().date()),
        valid_bars=int(panel["valid_classifier_bar"].sum()),
        point_in_time_eligible_bars=int(panel["eligible_security_type"].sum()),
    )
