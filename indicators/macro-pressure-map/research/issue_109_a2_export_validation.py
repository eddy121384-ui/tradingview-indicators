#!/usr/bin/env python3
"""Validate a user-exported Issue #109 A2 TradingView trajectory CSV.

This gate must pass before any A2 asset-payoff model is allowed to run.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
DATA = HERE / "data"

AUDIT = DATA / "issue-64-frozen-axis-audit.csv"
TRANSITIONS = DATA / "issue-64-frozen-regime-transitions.csv"

EXPECTED_AUDIT_SHA = "9021844c7ed0b927ce95ca3de117ac3749eb3c5541e5d6c46557aa5624fa08c1"
EXPECTED_TRANSITION_SHA = "80446bbcb91be8b18eb0b95e62466edf892e4c04087696a04532f0fe214698af"
SIGNAL_CUTOFF = pd.Timestamp("2026-08-14")
AXIS_TOL = 5e-6
FEATURE_TOL = 5e-8


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def norm(s: str) -> str:
    return re.sub(r"[^a-z0-9]+", " ", str(s).lower()).strip()


def find_column(columns: list[str], required_tokens: tuple[str, ...], *, exact_any: tuple[str, ...] = ()) -> str:
    normalized = {c: norm(c) for c in columns}
    for c, n in normalized.items():
        if n in exact_any:
            return c
    matches = [c for c, n in normalized.items() if all(tok in n for tok in required_tokens)]
    if len(matches) != 1:
        raise ValueError(f"expected exactly one column containing tokens {required_tokens}, got {matches}")
    return matches[0]


def find_date_column(columns: list[str]) -> str:
    preferred = {"time", "date", "datetime", "timestamp"}
    for c in columns:
        if norm(c) in preferred:
            return c
    for c in columns:
        n = norm(c)
        if "time" in n or "date" in n:
            return c
    raise ValueError("could not identify TradingView date/time column")


def parse_export(path: Path) -> tuple[pd.DataFrame, dict]:
    raw = pd.read_csv(path)
    cols = list(raw.columns)
    date_col = find_date_column(cols)

    mapping = {
        "raw_gpi": find_column(cols, ("a2", "raw", "gpi")),
        "raw_ipi": find_column(cols, ("a2", "raw", "ipi")),
        "gpi_fast": find_column(cols, ("a2", "gpi", "fast", "slope", "20")),
        "gpi_mid": find_column(cols, ("a2", "gpi", "mid", "slope", "63")),
        "gpi_acc": find_column(cols, ("a2", "gpi", "acceleration")),
        "ipi_fast": find_column(cols, ("a2", "ipi", "fast", "slope", "20")),
        "ipi_mid": find_column(cols, ("a2", "ipi", "mid", "slope", "63")),
        "ipi_acc": find_column(cols, ("a2", "ipi", "acceleration")),
        "regime_id": find_column(cols, ("a2", "reconstructed", "regime", "id")),
    }

    out = pd.DataFrame()
    # TradingView may export exchange timestamps or ISO date strings.
    out["date"] = pd.to_datetime(raw[date_col], errors="raise", utc=True).dt.tz_convert(None).dt.normalize()
    for key, col in mapping.items():
        out[key] = pd.to_numeric(raw[col], errors="coerce")

    out = out.dropna(subset=["date"]).sort_values("date").reset_index(drop=True)
    if out["date"].duplicated().any():
        dup = out.loc[out["date"].duplicated(), "date"].dt.strftime("%Y-%m-%d").tolist()[:10]
        raise ValueError(f"duplicate export dates: {dup}")
    if not out["date"].is_monotonic_increasing:
        raise ValueError("export dates are not increasing")

    meta = {
        "raw_columns": cols,
        "date_column": date_col,
        "mapped_columns": mapping,
    }
    return out, meta


def regime_from_axes(gpi: pd.Series, ipi: pd.Series) -> pd.Series:
    result = pd.Series(np.nan, index=gpi.index, dtype=float)
    finite = gpi.notna() & ipi.notna()

    gp = gpi > 10.0
    gn = gpi < -10.0
    gz = ~(gp | gn)
    ip = ipi > 10.0
    inn = ipi < -10.0
    iz = ~(ip | inn)

    result.loc[finite & gp & inn] = 1
    result.loc[finite & gp & iz] = 2
    result.loc[finite & gp & ip] = 3
    result.loc[finite & gz & inn] = 4
    result.loc[finite & gz & iz] = 5
    result.loc[finite & gz & ip] = 6
    result.loc[finite & gn & inn] = 7
    result.loc[finite & gn & iz] = 8
    result.loc[finite & gn & ip] = 9
    return result


def expected_regime_for_dates(dates: pd.Series) -> np.ndarray:
    t = pd.read_csv(TRANSITIONS)
    t["start_date"] = pd.to_datetime(t["start_date"], errors="raise")
    t = t.sort_values("start_date")
    starts = t["start_date"].to_numpy(dtype="datetime64[ns]")
    ids = t["regime_id"].to_numpy(int)

    result = np.full(len(dates), np.nan)
    for i, d in enumerate(dates):
        if d > SIGNAL_CUTOFF:
            continue
        pos = int(np.searchsorted(starts, np.datetime64(d), side="right") - 1)
        if pos >= 0:
            result[i] = ids[pos]
    return result


def max_abs(a: pd.Series, b: pd.Series) -> float:
    mask = a.notna() & b.notna()
    if not mask.any():
        return float("nan")
    return float(np.max(np.abs(a.loc[mask].to_numpy(float) - b.loc[mask].to_numpy(float))))


def validate_features(df: pd.DataFrame) -> dict:
    calc_gpi_fast = (df["raw_gpi"] - df["raw_gpi"].shift(20)) / 20.0
    calc_gpi_mid = (df["raw_gpi"] - df["raw_gpi"].shift(63)) / 63.0
    calc_gpi_acc = calc_gpi_fast - calc_gpi_mid

    calc_ipi_fast = (df["raw_ipi"] - df["raw_ipi"].shift(20)) / 20.0
    calc_ipi_mid = (df["raw_ipi"] - df["raw_ipi"].shift(63)) / 63.0
    calc_ipi_acc = calc_ipi_fast - calc_ipi_mid

    diffs = {
        "gpi_fast": max_abs(df["gpi_fast"], calc_gpi_fast),
        "gpi_mid": max_abs(df["gpi_mid"], calc_gpi_mid),
        "gpi_acc": max_abs(df["gpi_acc"], calc_gpi_acc),
        "ipi_fast": max_abs(df["ipi_fast"], calc_ipi_fast),
        "ipi_mid": max_abs(df["ipi_mid"], calc_ipi_mid),
        "ipi_acc": max_abs(df["ipi_acc"], calc_ipi_acc),
    }
    for name, value in diffs.items():
        if not np.isfinite(value) or value > FEATURE_TOL:
            raise ValueError(f"trajectory feature mismatch {name}: {value} > {FEATURE_TOL}")
    return diffs


def validate_axis_audit(df: pd.DataFrame) -> dict:
    audit = pd.read_csv(AUDIT)
    audit["date"] = pd.to_datetime(audit["date"], errors="raise")
    joined = audit.merge(df[["date", "raw_gpi", "raw_ipi", "regime_id"]], on="date", how="left")

    missing = joined.loc[joined["raw_gpi"].isna() | joined["raw_ipi"].isna(), "date"]
    if len(missing):
        raise ValueError(f"export misses {len(missing)} frozen axis audit dates; first={missing.iloc[0].date()}")

    gpi_err = float(np.max(np.abs(joined["raw_gpi"] - joined["GPI"])))
    ipi_err = float(np.max(np.abs(joined["raw_ipi"] - joined["IPI"])))
    regime_match = int((joined["regime_id"].round().astype(int) == joined["regime_id_x"].round().astype(int)).sum()) if "regime_id_x" in joined.columns else None

    # pandas suffix names depend on duplicate column names.
    expected_regime_col = "regime_id_x" if "regime_id_x" in joined.columns else "regime_id"
    export_regime_col = "regime_id_y" if "regime_id_y" in joined.columns else "regime_id"
    regime_matches = joined[expected_regime_col].round().astype(int).eq(joined[export_regime_col].round().astype(int))
    if not regime_matches.all():
        bad = joined.loc[~regime_matches, ["date", expected_regime_col, export_regime_col]].head(10)
        raise ValueError(f"axis-audit regime mismatch:\n{bad.to_string(index=False)}")

    if gpi_err > AXIS_TOL or ipi_err > AXIS_TOL:
        raise ValueError(f"axis checkpoint mismatch: GPI={gpi_err}, IPI={ipi_err}, tol={AXIS_TOL}")

    return {
        "checkpoints": int(len(joined)),
        "max_abs_gpi_error": gpi_err,
        "max_abs_ipi_error": ipi_err,
        "regime_matches": int(regime_matches.sum()),
    }


def validate_transition_history(df: pd.DataFrame) -> dict:
    subset = df.loc[df["date"] <= SIGNAL_CUTOFF].copy()
    expected = expected_regime_for_dates(subset["date"])
    observed = subset["regime_id"].to_numpy(float)
    mask = np.isfinite(expected) & np.isfinite(observed)
    if not mask.any():
        raise ValueError("no common finite regime history for transition validation")
    mismatch = np.flatnonzero(expected[mask].astype(int) != np.rint(observed[mask]).astype(int))
    if len(mismatch):
        idx = np.flatnonzero(mask)[mismatch[:10]]
        bad = subset.iloc[idx][["date", "regime_id"]].copy()
        bad["expected_regime_id"] = expected[idx]
        raise ValueError(f"frozen transition mismatch count={len(mismatch)}:\n{bad.to_string(index=False)}")
    return {
        "compared_rows": int(mask.sum()),
        "mismatch_rows": 0,
        "first_compared_date": subset.loc[mask, "date"].min().date().isoformat(),
        "last_compared_date": subset.loc[mask, "date"].max().date().isoformat(),
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("csv", type=Path)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()

    if sha256_file(AUDIT) != EXPECTED_AUDIT_SHA:
        raise RuntimeError("Issue #64 axis audit hash mismatch")
    if sha256_file(TRANSITIONS) != EXPECTED_TRANSITION_SHA:
        raise RuntimeError("Issue #64 transition hash mismatch")

    df, mapping = parse_export(args.csv)

    finite_axes = df.loc[df["raw_gpi"].notna() & df["raw_ipi"].notna()]
    if finite_axes.empty:
        raise ValueError("export contains no finite reconstructed raw axes")
    if finite_axes["date"].min() > pd.Timestamp("2007-01-04"):
        raise ValueError(f"history starts too late: {finite_axes['date'].min().date()}")

    recomputed_regime = regime_from_axes(df["raw_gpi"], df["raw_ipi"])
    regime_err = max_abs(df["regime_id"], recomputed_regime)
    if not np.isfinite(regime_err) or regime_err > 0:
        raise ValueError(f"exported regime id disagrees with raw-axis reconstruction: {regime_err}")

    feature_check = validate_features(df)
    audit_check = validate_axis_audit(df)
    transition_check = validate_transition_history(df)

    result = {
        "schema_version": 1,
        "issue": 109,
        "phase": "A2-exact-axis-acceptance",
        "accepted": True,
        "export_sha256": sha256_file(args.csv),
        "rows": int(len(df)),
        "finite_axis_rows": int(len(finite_axes)),
        "first_date": df["date"].min().date().isoformat(),
        "last_date": df["date"].max().date().isoformat(),
        "first_finite_axis_date": finite_axes["date"].min().date().isoformat(),
        "last_finite_axis_date": finite_axes["date"].max().date().isoformat(),
        "column_mapping": mapping,
        "axis_audit": audit_check,
        "transition_history": transition_check,
        "feature_recompute_max_abs_error": feature_check,
        "a2_payoff_authorized": True,
        "production_authorized": False,
    }

    text = json.dumps(result, indent=2, ensure_ascii=False) + "\n"
    if args.output:
        args.output.write_text(text, encoding="utf-8")
    print(text)


if __name__ == "__main__":
    main()
