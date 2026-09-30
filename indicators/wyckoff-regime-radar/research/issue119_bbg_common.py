#!/usr/bin/env python3
"""Shared data-contract helpers for Issue #119 Bloomberg OOS2 pipeline.

No strategy economics live in this module.
"""
from __future__ import annotations

from hashlib import sha256
from pathlib import Path
import re
from typing import Iterable

import numpy as np
import pandas as pd

RAW_START = "1998-01-01"
EVENT_START = "2000-01-03"
EVENT_END = "2026-08-31"

CALIBRATION_TICKERS = {"AAPL", "JPM", "XOM"}
SOURCE_INDICES = {
    "large": "SPX Index",
    "mid": "MID Index",
    "small": "SML Index",
}
TARGET_BY_SLEEVE = {"large": 100, "mid": 100, "small": 100}
UNIVERSE_SEED = "issue119-bbg-oos2-v1"

HISTORICAL_FIELDS = ("PX_OPEN", "PX_HIGH", "PX_LOW", "PX_LAST", "PX_VOLUME")
METADATA_FIELDS = (
    "ID_BB_GLOBAL",
    "TICKER",
    "GICS_SECTOR_NAME",
    "CUR_MKT_CAP",
    "MARKET_SECTOR_DES",
    "SECURITY_TYP",
    "EQY_PRIM_EXCH_SHRT",
)

DISALLOWED_SECURITY_TOKENS = (
    "ETF",
    "ETN",
    "PREFERRED",
    "PREFERENCE",
    "ADR",
    "DEPOSITARY",
    "WARRANT",
    "RIGHT",
    "UNIT",
    "CLOSED-END",
    "CLOSED END",
)
ALLOWED_SECURITY_TYPES = {"COMMON STOCK", "REIT"}


def file_sha256(path: Path) -> str:
    h = sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def text_sha256(value: str) -> str:
    return sha256(value.encode("utf-8")).hexdigest()


def stable_key(*parts: object, seed: str = UNIVERSE_SEED) -> str:
    return text_sha256("|".join([seed, *(str(x) for x in parts)]))


def canonical_ticker(value: object) -> str:
    text = str(value or "").strip().upper()
    if not text:
        return ""
    return re.split(r"\s+", text)[0].replace("/", ".")


def normalize_member_security(value: object) -> str:
    """Normalize INDX_MEMBERS first-column output to a Bloomberg Equity id."""
    text = str(value or "").strip()
    if not text:
        return ""
    if text.upper().endswith(" EQUITY"):
        return text
    return f"{text} Equity"


def eligible_metadata(row: pd.Series) -> tuple[bool, str]:
    ticker = canonical_ticker(row.get("ticker", ""))
    if not ticker:
        return False, "missing_ticker"
    if ticker in CALIBRATION_TICKERS:
        return False, "calibration_fixture"

    figi = str(row.get("figi", "") or "").strip()
    sector = str(row.get("sector", "") or "").strip()
    market_sector = str(row.get("market_sector", "") or "").strip().upper()
    security_type = str(row.get("security_type", "") or "").strip().upper()

    if not figi:
        return False, "missing_figi"
    if not sector:
        return False, "missing_sector"
    if market_sector != "EQUITY":
        return False, "not_equity_market_sector"
    if not security_type:
        return False, "missing_security_type"
    if any(token in security_type for token in DISALLOWED_SECURITY_TOKENS):
        return False, "disallowed_security_type"
    if security_type not in ALLOWED_SECURITY_TYPES:
        return False, f"unsupported_security_type:{security_type}"

    market_cap = pd.to_numeric(pd.Series([row.get("market_cap")]), errors="coerce").iloc[0]
    if not np.isfinite(market_cap) or market_cap <= 0:
        return False, "missing_market_cap"

    return True, "eligible"


def _allocate_equal_sector_quota(
    sector_counts: dict[str, int],
    target: int,
    *,
    seed: str,
    sleeve: str,
) -> dict[str, int]:
    """Equal-sector allocation with deterministic capacity-aware redistribution."""
    sectors = sorted(sector_counts)
    if not sectors:
        raise ValueError(f"{sleeve}: no sectors available")
    if sum(sector_counts.values()) < target:
        raise ValueError(
            f"{sleeve}: only {sum(sector_counts.values())} eligible candidates for target {target}"
        )

    order = sorted(sectors, key=lambda s: (stable_key("sector", sleeve, s, seed=seed), s))
    base, remainder = divmod(target, len(sectors))
    quota = {
        s: min(base + (1 if s in order[:remainder] else 0), sector_counts[s])
        for s in sectors
    }

    assigned = sum(quota.values())
    while assigned < target:
        growable = [s for s in sectors if quota[s] < sector_counts[s]]
        if not growable:
            raise ValueError(f"{sleeve}: unable to redistribute sector quota to {target}")
        growable = sorted(
            growable,
            key=lambda s: (
                quota[s] / sector_counts[s],
                stable_key("redistribute", sleeve, s, quota[s], seed=seed),
                s,
            ),
        )
        quota[growable[0]] += 1
        assigned += 1
    return quota


def deterministic_stratified_sample(
    candidates: pd.DataFrame,
    *,
    targets: dict[str, int] | None = None,
    seed: str = UNIVERSE_SEED,
) -> pd.DataFrame:
    """Select a fixed equal-sector sample inside large/mid/small sleeves."""
    targets = dict(targets or TARGET_BY_SLEEVE)
    required = {"sleeve", "security", "figi", "ticker", "sector", "market_cap"}
    missing = required.difference(candidates.columns)
    if missing:
        raise ValueError(f"candidates missing columns: {sorted(missing)}")

    frame = candidates.copy()
    frame["ticker"] = frame["ticker"].map(canonical_ticker)
    eligibility = frame.apply(eligible_metadata, axis=1, result_type="expand")
    frame["eligible"] = eligibility[0].astype(bool)
    frame["eligibility_reason"] = eligibility[1].astype(str)
    frame = frame[frame["eligible"]].copy()

    sleeve_order = {"large": 0, "mid": 1, "small": 2}
    frame["_sleeve_order"] = frame["sleeve"].map(sleeve_order).fillna(99)
    frame = (
        frame.sort_values(["_sleeve_order", "figi", "security"])
        .drop_duplicates("figi", keep="first")
        .drop(columns="_sleeve_order")
    )

    selected: list[pd.DataFrame] = []
    for sleeve, target in targets.items():
        pool = frame[frame["sleeve"] == sleeve].copy()
        if len(pool) < target:
            raise ValueError(f"{sleeve}: {len(pool)} eligible candidates < target {target}")
        counts = pool["sector"].value_counts().sort_index().to_dict()
        quota = _allocate_equal_sector_quota(counts, target, seed=seed, sleeve=sleeve)
        for sector, n in sorted(quota.items()):
            part = pool[pool["sector"] == sector].copy()
            part["sample_hash"] = part["figi"].map(
                lambda figi: stable_key("security", sleeve, sector, figi, seed=seed)
            )
            part = part.sort_values(["sample_hash", "figi", "security"]).head(n)
            selected.append(part)

    out = pd.concat(selected, ignore_index=True)
    out["sample_rank"] = (
        out.sort_values(["sleeve", "sector", "sample_hash", "figi"])
        .groupby(["sleeve", "sector"])
        .cumcount()
        + 1
    )
    out = out.sort_values(
        ["sleeve", "sector", "sample_hash", "figi"]
    ).reset_index(drop=True)

    if out["figi"].duplicated().any():
        raise AssertionError("sample contains duplicate FIGI")
    if set(out["ticker"]) & CALIBRATION_TICKERS:
        raise AssertionError("sample contains calibration fixture")
    expected = sum(targets.values())
    if len(out) != expected:
        raise AssertionError(f"sample size {len(out)} != {expected}")
    return out


def normalize_ohlcv(frame: pd.DataFrame) -> tuple[pd.DataFrame, dict[str, object]]:
    """Normalize one Bloomberg history response to classifier-ready OHLCV."""
    source = frame.copy()
    source.columns = [str(c).strip().upper() for c in source.columns]
    required = {"DATE", *HISTORICAL_FIELDS}
    missing = required.difference(source.columns)
    if missing:
        raise ValueError(f"history missing required fields: {sorted(missing)}")

    out = pd.DataFrame(
        {
            "date": pd.to_datetime(source["DATE"], errors="coerce"),
            "open": pd.to_numeric(source["PX_OPEN"], errors="coerce"),
            "high": pd.to_numeric(source["PX_HIGH"], errors="coerce"),
            "low": pd.to_numeric(source["PX_LOW"], errors="coerce"),
            "close": pd.to_numeric(source["PX_LAST"], errors="coerce"),
            "volume": pd.to_numeric(source["PX_VOLUME"], errors="coerce"),
        }
    )
    if out["date"].isna().any():
        raise ValueError("history contains invalid dates")
    if out["date"].duplicated().any():
        raise ValueError("history contains duplicate dates")

    out = out.sort_values("date").reset_index(drop=True)

    finite_ohlc = out[["open", "high", "low", "close"]].notna().all(axis=1)
    positive = (out[["open", "high", "low", "close"]] > 0).all(axis=1)
    volume_ok = out["volume"].isna() | out["volume"].ge(0)

    nonpositive = finite_ohlc & ~positive
    if nonpositive.any():
        bad_dates = [
            str(x.date())
            for x in out.loc[nonpositive, "date"].head(5)
        ]
        raise ValueError(
            f"history contains nonpositive OHLC on {bad_dates}"
        )
    if (~volume_ok).any():
        raise ValueError("history contains negative volume")

    high_ok = out["high"] >= out[["open", "close"]].max(axis=1)
    low_ok = out["low"] <= out[["open", "close"]].min(axis=1)
    range_bad = finite_ohlc & positive & (~high_ok | ~low_ok)

    repairs: list[dict[str, object]] = []
    if range_bad.any():
        before = out.loc[
            range_bad,
            ["date", "open", "high", "low", "close"],
        ].copy()

        repaired_high = out.loc[
            range_bad, ["open", "high", "close"]
        ].max(axis=1)
        repaired_low = out.loc[
            range_bad, ["open", "low", "close"]
        ].min(axis=1)

        out.loc[range_bad, "high"] = repaired_high
        out.loc[range_bad, "low"] = repaired_low

        after = out.loc[
            range_bad,
            ["date", "open", "high", "low", "close"],
        ]
        for idx in before.index:
            repairs.append(
                {
                    "date": str(before.at[idx, "date"].date()),
                    "open": float(before.at[idx, "open"]),
                    "high_before": float(before.at[idx, "high"]),
                    "high_after": float(after.at[idx, "high"]),
                    "low_before": float(before.at[idx, "low"]),
                    "low_after": float(after.at[idx, "low"]),
                    "close": float(before.at[idx, "close"]),
                }
            )

    high_ok = out["high"] >= out[["open", "close"]].max(axis=1)
    low_ok = out["low"] <= out[["open", "close"]].min(axis=1)
    usable = finite_ohlc & positive & high_ok & low_ok
    if usable.sum() == 0:
        raise ValueError("history contains zero usable OHLC rows")

    diagnostics = {
        "normalization_contract_version": 2,
        "rows": int(len(out)),
        "usable_ohlc_rows": int(usable.sum()),
        "ohlc_range_repairs": int(range_bad.sum()),
        "ohlc_range_repair_records": repairs,
        "min_date": str(out["date"].min().date()) if len(out) else None,
        "max_date": str(out["date"].max().date()) if len(out) else None,
        "missing": {
            col: int(out[col].isna().sum())
            for col in ("open", "high", "low", "close", "volume")
        },
    }
    return out, diagnostics


def chunked(items: Iterable[str], size: int) -> list[list[str]]:
    items = list(items)
    if size <= 0:
        raise ValueError("chunk size must be positive")
    return [items[i : i + size] for i in range(0, len(items), size)]
