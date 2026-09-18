#!/usr/bin/env python3
"""Issue #91 Phase 2: preregistered long-history state -> asset payoff validation.

This module may load asset outcomes because the Phase 2 preregistration was
committed and CI-validated beforehand. It must not modify HMRA-v0.1 rules or
run the #89 portfolio policy.
"""
from __future__ import annotations

import argparse
import hashlib
import io
import json
import math
from pathlib import Path
import tempfile
import urllib.request

import numpy as np
import pandas as pd

from issue_91_phase0_data_audit import flatten_columns
from issue_91_phase1_hmra_v01 import run as run_hmra
from issue_91_phase1_completion_validation import validate as validate_hmra_freeze

HERE = Path(__file__).resolve().parent
PREREG = HERE / "decisions" / "issue-91-phase2-asset-validation-preregistered.json"

DAMODARAN_URL = "https://pages.stern.nyu.edu/adamodar/New_Home_Page/datafile/histretSP.html"
JST_URL = "https://www.macrohistory.net/app/download/9834512569/JSTdatasetR6.xlsx"
USER_AGENT = "tradingview-indicators-issue-91-phase2/1.0"

PRIMARY_ASSETS = ["equity", "treasury", "cash"]
ALL_ASSETS = ["equity", "treasury", "cash", "gold"]
SPREADS = [
    "equity_minus_treasury",
    "treasury_minus_cash",
    "equity_minus_gold",
    "treasury_minus_gold",
]
GOLD_SPREADS = {"equity_minus_gold", "treasury_minus_gold"}


def sha256_bytes(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def fetch_bytes(url: str, timeout: int = 60) -> tuple[bytes, str]:
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(request, timeout=timeout) as response:  # nosec B310 - frozen HTTPS source
        payload = response.read()
        final_url = response.geturl()
    if not payload:
        raise RuntimeError(f"empty response from {url}")
    return payload, final_url


def validate_prereg() -> dict:
    p = json.loads(PREREG.read_text(encoding="utf-8"))
    if p["issue"] != 91 or p["phase"] != "2-structural-and-causal-asset-validation-preregistration":
        raise RuntimeError("bad Phase 2 prereg identity")
    if p["created_before_phase2_asset_outcomes"] is not True:
        raise RuntimeError("Phase 2 prereg timing guard failed")
    if p["portfolio_policy_test_in_this_phase"] is not False:
        raise RuntimeError("portfolio policy unexpectedly allowed in Phase 2")
    if p["pairings"]["strict_causal_primary"]["return_year"] != "t+2":
        raise RuntimeError("strict causal timing drift")
    return p


def _promote_embedded_header(table: pd.DataFrame, exact_columns: dict[str, str]) -> pd.DataFrame | None:
    raw = table.copy()
    wanted = {"Year", *exact_columns.values()}
    for pos in range(min(len(raw), 15)):
        row = [str(x).strip() for x in raw.iloc[pos].tolist()]
        if not wanted.issubset(set(row)):
            continue
        headers = []
        seen: dict[str, int] = {}
        for i, value in enumerate(row):
            base = value if value and value.lower() != "nan" else f"column_{i}"
            count = seen.get(base, 0)
            seen[base] = count + 1
            headers.append(base if count == 0 else f"{base}__{count+1}")
        out = raw.iloc[pos + 1 :].copy()
        out.columns = headers
        return out
    return None


def _parse_percent_decimal(value: object) -> float:
    if pd.isna(value):
        raise ValueError("missing annual return")
    text = str(value).strip().replace(",", "")
    if not text:
        raise ValueError("blank annual return")
    negative = text.startswith("(") and text.endswith(")")
    if negative:
        text = text[1:-1].strip()
    if text.endswith("%"):
        text = text[:-1].strip()
        number = float(text) / 100.0
    else:
        number = float(text)
        # Damodaran annual return table is normally percent-formatted. If pandas
        # has already converted an Excel-style percentage to a decimal, preserve it.
        if abs(number) > 2.0:
            number = number / 100.0
    return -number if negative else number


def parse_damodaran_returns(payload: bytes, prereg: dict) -> pd.DataFrame:
    exact = prereg["primary_asset_source"]["exact_columns"]
    tables = pd.read_html(io.BytesIO(payload), header=None)
    candidates = []
    for table in tables:
        frame = flatten_columns(table)
        promoted = _promote_embedded_header(frame, exact)
        if promoted is not None:
            candidates.append(promoted)
    if not candidates:
        raise RuntimeError("Damodaran annual return table not found")
    frame = max(candidates, key=len)

    missing = [name for name in exact.values() if name not in frame.columns]
    if missing:
        raise RuntimeError(f"Damodaran exact primary columns missing: {missing}")

    selected = frame[[
        exact["year"],
        exact["equity"],
        exact["cash"],
        exact["treasury"],
        exact["gold"],
    ]].copy()
    selected.columns = ["year", "equity", "cash", "treasury", "gold"]
    selected["year"] = pd.to_numeric(selected["year"], errors="coerce")
    selected = selected.loc[selected["year"].between(1928, 2025, inclusive="both")].copy()
    selected["year"] = selected["year"].astype(int)
    if selected["year"].duplicated().any():
        raise RuntimeError("duplicate Damodaran year")
    for col in ALL_ASSETS:
        selected[col] = selected[col].map(_parse_percent_decimal)
        if not np.isfinite(selected[col]).all():
            raise RuntimeError(f"nonnumeric Damodaran {col} return")
    selected = selected.sort_values("year").reset_index(drop=True)
    expected = list(range(1928, 2026))
    if selected["year"].tolist() != expected:
        raise RuntimeError("Damodaran primary years are not exactly 1928-2025")
    return selected


def parse_jst_returns(payload: bytes, prereg: dict) -> pd.DataFrame:
    book = pd.ExcelFile(io.BytesIO(payload), engine="openpyxl")
    selected = None
    for sheet in book.sheet_names:
        frame = pd.read_excel(book, sheet_name=sheet, engine="openpyxl")
        cols = {str(c).strip().lower(): c for c in frame.columns}
        if not {"year", "iso", "eq_tr", "bond_tr"}.issubset(cols):
            continue
        us = frame.loc[frame[cols["iso"]].astype(str).str.upper().eq("USA")].copy()
        if us.empty:
            continue
        selected = pd.DataFrame({
            "year": pd.to_numeric(us[cols["year"]], errors="coerce"),
            "jst_equity": pd.to_numeric(us[cols["eq_tr"]], errors="coerce"),
            "jst_treasury": pd.to_numeric(us[cols["bond_tr"]], errors="coerce"),
        })
        break
    if selected is None:
        raise RuntimeError("JST USA return rows not found")
    selected = selected.dropna(subset=["year"]).copy()
    selected["year"] = selected["year"].astype(int)
    selected = selected.loc[selected["year"].between(1928, 2020, inclusive="both")].copy()
    if selected["year"].duplicated().any():
        raise RuntimeError("duplicate JST USA year")
    # Official R6 documentation defines eq_tr and bond_tr directly as decimal r[t].
    for col in ("jst_equity", "jst_treasury"):
        values = selected[col].dropna()
        if not values.empty and (values.abs() > 5.0).any():
            raise RuntimeError(f"JST {col} violates frozen decimal-return scale")
    return selected.sort_values("year").reset_index(drop=True)


def add_spreads(frame: pd.DataFrame) -> pd.DataFrame:
    out = frame.copy()
    out["equity_minus_treasury"] = out["equity"] - out["treasury"]
    out["treasury_minus_cash"] = out["treasury"] - out["cash"]
    out["equity_minus_gold"] = out["equity"] - out["gold"]
    out["treasury_minus_gold"] = out["treasury"] - out["gold"]
    return out


def sample_label(n: int) -> str:
    if n < 3:
        return "insufficient"
    if n <= 4:
        return "very_sparse"
    if n <= 9:
        return "sparse"
    return "regular"


def _seed_for(base_seed: int, key: str) -> int:
    digest = hashlib.sha256(key.encode("utf-8")).hexdigest()
    return (base_seed + int(digest[:8], 16)) % (2**32 - 1)


def bootstrap_mean_ci(values: np.ndarray, repetitions: int, seed: int) -> tuple[float | None, float | None]:
    arr = np.asarray(values, dtype=float)
    arr = arr[np.isfinite(arr)]
    if len(arr) < 3:
        return None, None
    rng = np.random.default_rng(seed)
    draws = rng.choice(arr, size=(repetitions, len(arr)), replace=True)
    means = draws.mean(axis=1)
    q = np.quantile(means, [0.025, 0.975])
    return float(q[0]), float(q[1])


def metric_summary(values: pd.Series, metric: str, prereg: dict, key: str) -> dict:
    arr = pd.to_numeric(values, errors="coerce").dropna().to_numpy(dtype=float)
    n = int(len(arr))
    result = {
        "metric": metric,
        "n": n,
        "sample_label": sample_label(n),
        "arithmetic_mean": float(np.mean(arr)) if n else None,
        "median": float(np.median(arr)) if n else None,
        "sample_standard_deviation": float(np.std(arr, ddof=1)) if n >= 2 else None,
        "positive_fraction": float(np.mean(arr > 0.0)) if n else None,
        "bootstrap_mean_ci_low": None,
        "bootstrap_mean_ci_high": None,
        "geometric_mean": None,
    }
    if n >= prereg["descriptive_metrics"]["bootstrap"]["minimum_n"]:
        low, high = bootstrap_mean_ci(
            arr,
            prereg["descriptive_metrics"]["bootstrap"]["repetitions"],
            _seed_for(prereg["descriptive_metrics"]["bootstrap"]["seed"], key),
        )
        result["bootstrap_mean_ci_low"] = low
        result["bootstrap_mean_ci_high"] = high
    if metric in ALL_ASSETS and n and np.all(arr > -1.0):
        result["geometric_mean"] = float(np.exp(np.mean(np.log1p(arr))) - 1.0)
    return result


def summarize_by_cell(frame: pd.DataFrame, pairing: str, prereg: dict) -> pd.DataFrame:
    metrics = ALL_ASSETS + SPREADS
    rows = []
    for (g, i, regime), group in frame.groupby(["growth_state", "inflation_state", "core_regime"], sort=True):
        for metric in metrics:
            summary = metric_summary(group[metric], metric, prereg, f"{pairing}|{g}|{i}|{metric}")
            rows.append({
                "pairing": pairing,
                "growth_state": g,
                "inflation_state": i,
                "core_regime": regime,
                **summary,
            })
    return pd.DataFrame(rows)


def summarize_by_cell_era(frame: pd.DataFrame, pairing: str, prereg: dict) -> pd.DataFrame:
    metrics = ALL_ASSETS + SPREADS
    rows = []
    for (g, i, regime, era), group in frame.groupby(["growth_state", "inflation_state", "core_regime", "era"], sort=True):
        for metric in metrics:
            summary = metric_summary(group[metric], metric, prereg, f"era|{pairing}|{g}|{i}|{era}|{metric}")
            rows.append({
                "pairing": pairing,
                "growth_state": g,
                "inflation_state": i,
                "core_regime": regime,
                "era": era,
                **summary,
            })
    return pd.DataFrame(rows)


def sign_of(value: float | None) -> int:
    if value is None or pd.isna(value):
        return 0
    if value > 0:
        return 1
    if value < 0:
        return -1
    return 0


def era_sign_consistency(full_summary: pd.DataFrame, era_summary: pd.DataFrame) -> pd.DataFrame:
    full = full_summary.loc[full_summary["metric"].isin(SPREADS)].copy()
    rows = []
    keys = ["pairing", "growth_state", "inflation_state", "core_regime", "metric"]
    for key_vals, full_group in full.groupby(keys, sort=True):
        if len(full_group) != 1:
            raise RuntimeError("duplicate full cell summary")
        full_mean = full_group.iloc[0]["arithmetic_mean"]
        full_sign = sign_of(full_mean)
        mask = pd.Series(True, index=era_summary.index)
        for k, v in zip(keys, key_vals):
            mask &= era_summary[k].eq(v)
        eras = era_summary.loc[mask & era_summary["n"].ge(3)].copy()
        era_signs = eras["arithmetic_mean"].map(sign_of)
        eligible = int(len(eras))
        same = int((era_signs.eq(full_sign) & era_signs.ne(0)).sum()) if full_sign != 0 else 0
        rows.append({
            **dict(zip(keys, key_vals)),
            "full_mean": full_mean,
            "full_sign": full_sign,
            "eligible_eras_n_ge_3": eligible,
            "same_nonzero_sign_eras": same,
            "sign_consistency": float(same / eligible) if eligible else None,
        })
    return pd.DataFrame(rows)


def leader_for_group(group: pd.DataFrame, assets: list[str]) -> str | None:
    means = group[assets].mean(numeric_only=True)
    if means.isna().all():
        return None
    return str(means.idxmax())


def leader_consistency(frame: pd.DataFrame, pairing: str) -> pd.DataFrame:
    rows = []
    asset_sets = [
        ("three_asset", ["equity", "treasury", "cash"], None),
        ("four_asset_gold_valid", ["equity", "treasury", "cash", "gold"], 1975),
    ]
    for set_name, assets, start_year in asset_sets:
        base = frame if start_year is None else frame.loc[frame["return_year"].ge(start_year)]
        for (g, i, regime), cell in base.groupby(["growth_state", "inflation_state", "core_regime"], sort=True):
            full_leader = leader_for_group(cell, assets)
            eligible = 0
            same = 0
            details = []
            for era, egroup in cell.groupby("era", sort=True):
                if len(egroup) < 3:
                    continue
                leader = leader_for_group(egroup, assets)
                eligible += 1
                same += int(leader == full_leader and leader is not None)
                details.append(f"{era}:{leader}:{len(egroup)}")
            rows.append({
                "pairing": pairing,
                "asset_set": set_name,
                "growth_state": g,
                "inflation_state": i,
                "core_regime": regime,
                "full_sample_leader": full_leader,
                "eligible_eras_n_ge_3": eligible,
                "same_leader_eras": same,
                "leader_consistency": float(same / eligible) if eligible else None,
                "era_leaders": "|".join(details),
            })
    return pd.DataFrame(rows)


def bootstrap_difference_ci(a: np.ndarray, b: np.ndarray, prereg: dict, key: str) -> tuple[float, float]:
    reps = prereg["absolute_inflation_regime_test"]["bootstrap"]["repetitions"]
    base = prereg["absolute_inflation_regime_test"]["bootstrap"]["seed"]
    rng = np.random.default_rng(_seed_for(base, key))
    da = rng.choice(a, size=(reps, len(a)), replace=True).mean(axis=1)
    db = rng.choice(b, size=(reps, len(b)), replace=True).mean(axis=1)
    q = np.quantile(db - da, [0.025, 0.975])
    return float(q[0]), float(q[1])


def absolute_inflation_comparison(structural: pd.DataFrame, prereg: dict) -> pd.DataFrame:
    rows = []
    for metric in SPREADS:
        base = structural
        window = "1928-2025"
        if metric in GOLD_SPREADS:
            base = base.loc[base["return_year"].ge(prereg["gold_boundary"]["primary_investable_gold_start_year"])]
            window = "1975-2025_gold_valid"
        for (g, i, regime), cell in base.groupby(["growth_state", "inflation_state", "core_regime"], sort=True):
            low = cell.loc[cell["inflation_rate"].lt(4.0), metric].dropna().to_numpy(dtype=float)
            high = cell.loc[cell["inflation_rate"].ge(4.0), metric].dropna().to_numpy(dtype=float)
            eligible = len(low) >= 5 and len(high) >= 5
            row = {
                "metric": metric,
                "analysis_window": window,
                "growth_state": g,
                "inflation_state": i,
                "core_regime": regime,
                "below_4pct_n": int(len(low)),
                "at_or_above_4pct_n": int(len(high)),
                "below_4pct_mean": float(np.mean(low)) if len(low) else None,
                "at_or_above_4pct_mean": float(np.mean(high)) if len(high) else None,
                "mean_difference_high_minus_low": None,
                "bootstrap_difference_ci_low": None,
                "bootstrap_difference_ci_high": None,
                "sign_reversal_between_groups": None,
                "eligible_both_n_ge_5": bool(eligible),
            }
            if eligible:
                diff = float(np.mean(high) - np.mean(low))
                lo, hi = bootstrap_difference_ci(
                    low,
                    high,
                    prereg,
                    f"absinf|{metric}|{g}|{i}|{regime}",
                )
                row["mean_difference_high_minus_low"] = diff
                row["bootstrap_difference_ci_low"] = lo
                row["bootstrap_difference_ci_high"] = hi
                row["sign_reversal_between_groups"] = sign_of(np.mean(low)) != sign_of(np.mean(high))
            rows.append(row)
    return pd.DataFrame(rows)


def leave_one_era_out(structural: pd.DataFrame, prereg: dict) -> pd.DataFrame:
    rows = []
    for metric in SPREADS:
        base = structural
        window = "1928-2025"
        if metric in GOLD_SPREADS:
            base = base.loc[base["return_year"].ge(prereg["gold_boundary"]["primary_investable_gold_start_year"])]
            window = "1975-2025_gold_valid"
        for (g, i, regime), cell in base.groupby(["growth_state", "inflation_state", "core_regime"], sort=True):
            full = cell[metric].dropna()
            if len(full) < 5:
                continue
            full_mean = float(full.mean())
            full_sign = sign_of(full_mean)
            for era in [x["label"] for x in prereg["era_definitions"]]:
                removed_n = int(cell["era"].eq(era).sum())
                if removed_n == 0:
                    continue
                left = cell.loc[~cell["era"].eq(era), metric].dropna()
                if len(left) < prereg["leave_one_era_out"]["minimum_remaining_n"]:
                    continue
                leave_mean = float(left.mean())
                leave_sign = sign_of(leave_mean)
                ratio = abs(leave_mean) / abs(full_mean) if abs(full_mean) > 1e-12 else None
                rows.append({
                    "metric": metric,
                    "analysis_window": window,
                    "growth_state": g,
                    "inflation_state": i,
                    "core_regime": regime,
                    "omitted_era": era,
                    "removed_observations": removed_n,
                    "remaining_n": int(len(left)),
                    "full_mean": full_mean,
                    "leaveout_mean": leave_mean,
                    "full_sign": full_sign,
                    "leaveout_sign": leave_sign,
                    "sign_flip": bool(full_sign != 0 and leave_sign != 0 and full_sign != leave_sign),
                    "absolute_mean_retention_ratio": ratio,
                    "era_concentrated": bool(
                        (full_sign != 0 and leave_sign != 0 and full_sign != leave_sign)
                        or (ratio is not None and ratio < 0.5)
                    ),
                })
    return pd.DataFrame(rows)


def build_pairings(states: pd.DataFrame, assets: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    states = states.loc[
        states["year"].between(1928, 2025, inclusive="both")
        & states["core_regime"].ne("n/a")
    ].copy()
    structural = states.merge(assets, on="year", how="inner", validate="one_to_one")
    structural["state_year"] = structural["year"]
    structural["return_year"] = structural["year"]
    structural["pairing"] = "structural_same_year"
    structural = add_spreads(structural)

    causal_states = states.loc[states["year"].le(2023)].copy()
    causal_states["return_year"] = causal_states["year"] + 2
    causal_states = causal_states.rename(columns={"year": "state_year"})
    returns = assets.rename(columns={"year": "return_year"})
    causal = causal_states.merge(returns, on="return_year", how="inner", validate="one_to_one")
    causal["year"] = causal["state_year"]
    causal["pairing"] = "strict_causal_t_plus_2"
    causal = add_spreads(causal)
    return structural, causal


def cross_source_validation(
    states: pd.DataFrame,
    assets: pd.DataFrame,
    jst: pd.DataFrame,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    overlap = assets.merge(jst, on="year", how="inner")
    overlap = overlap.loc[overlap["year"].between(1928, 2020, inclusive="both")].copy()
    overlap["primary_spread"] = overlap["equity"] - overlap["treasury"]
    overlap["jst_spread"] = overlap["jst_equity"] - overlap["jst_treasury"]

    valid = overlap.dropna(subset=["equity", "treasury", "jst_equity", "jst_treasury"])
    overall = pd.DataFrame([{
        "overlap_first_year": int(valid["year"].min()),
        "overlap_last_year": int(valid["year"].max()),
        "overlap_years": int(len(valid)),
        "equity_return_correlation": float(valid["equity"].corr(valid["jst_equity"])),
        "treasury_return_correlation": float(valid["treasury"].corr(valid["jst_treasury"])),
        "equity_minus_treasury_correlation": float(valid["primary_spread"].corr(valid["jst_spread"])),
    }])

    s = states[["year", "growth_state", "inflation_state", "core_regime"]].copy()
    cell = s.merge(overlap, on="year", how="inner")
    rows = []
    for (g, i, regime), group in cell.groupby(["growth_state", "inflation_state", "core_regime"], sort=True):
        primary = group["primary_spread"].dropna()
        jst_spread = group["jst_spread"].dropna()
        common = group.dropna(subset=["primary_spread", "jst_spread"])
        eligible = len(common) >= 5
        pm = float(common["primary_spread"].mean()) if len(common) else None
        jm = float(common["jst_spread"].mean()) if len(common) else None
        rows.append({
            "growth_state": g,
            "inflation_state": i,
            "core_regime": regime,
            "common_n": int(len(common)),
            "primary_mean_equity_minus_treasury": pm,
            "jst_mean_equity_minus_treasury": jm,
            "eligible_n_ge_5": bool(eligible),
            "mean_sign_agreement": bool(sign_of(pm) == sign_of(jm) and sign_of(pm) != 0) if eligible else None,
            "within_cell_annual_spread_correlation": float(common["primary_spread"].corr(common["jst_spread"])) if len(common) >= 3 else None,
        })
    return overall, pd.DataFrame(rows)


def output_hash_manifest(output_dir: Path, exclude: set[str] | None = None) -> dict:
    exclude = exclude or set()
    result = {}
    for path in sorted(output_dir.glob("*")):
        if not path.is_file() or path.name in exclude:
            continue
        result[path.name] = {
            "sha256": sha256_file(path),
            "bytes": path.stat().st_size,
        }
    return result


def run(output_dir: Path) -> dict:
    prereg = validate_prereg()
    output_dir.mkdir(parents=True, exist_ok=True)

    # Regenerate the Phase 1 macro-only evidence and enforce its durable freeze
    # before any asset outcomes are joined.
    with tempfile.TemporaryDirectory(prefix="issue91-phase1-") as tmp:
        hmra_dir = Path(tmp)
        run_hmra(hmra_dir)
        hmra_validation = validate_hmra_freeze(hmra_dir)
        states = pd.read_csv(hmra_dir / "issue-91-hmra-v0.1-macro-states.csv")

    dam_raw, dam_final = fetch_bytes(DAMODARAN_URL)
    expected_dam_sha = prereg["primary_asset_source"]["frozen_raw_sha256_from_phase0"]
    if sha256_bytes(dam_raw) != expected_dam_sha:
        raise RuntimeError("Damodaran raw source SHA changed from Phase 0 freeze")
    assets = parse_damodaran_returns(dam_raw, prereg)

    jst_raw, jst_final = fetch_bytes(JST_URL)
    expected_jst_sha = prereg["independent_cross_check"]["frozen_raw_sha256_from_phase0"]
    if sha256_bytes(jst_raw) != expected_jst_sha:
        raise RuntimeError("JST raw source SHA changed from Phase 0 freeze")
    jst = parse_jst_returns(jst_raw, prereg)

    structural, causal = build_pairings(states, assets)

    structural_summary = summarize_by_cell(structural, "structural_same_year", prereg)
    causal_summary = summarize_by_cell(causal, "strict_causal_t_plus_2", prereg)
    era_structural = summarize_by_cell_era(structural, "structural_same_year", prereg)
    era_causal = summarize_by_cell_era(causal, "strict_causal_t_plus_2", prereg)
    era_all = pd.concat([era_structural, era_causal], ignore_index=True)

    full_all = pd.concat([structural_summary, causal_summary], ignore_index=True)
    sign_consistency = era_sign_consistency(full_all, era_all)
    leaders = pd.concat([
        leader_consistency(structural, "structural_same_year"),
        leader_consistency(causal, "strict_causal_t_plus_2"),
    ], ignore_index=True)

    abs_inf = absolute_inflation_comparison(structural, prereg)
    loeo = leave_one_era_out(structural, prereg)
    cross_overall, cross_cells = cross_source_validation(states, assets, jst)

    # Primary joined evidence is persisted for auditability. JST row-level data is
    # intentionally not persisted; only aggregate cross-check diagnostics are.
    join_cols = [
        "state_year", "return_year", "growth_state", "inflation_state", "core_regime",
        "growth_score", "inflation_score", "growth_rate", "inflation_rate",
        "absolute_inflation_bucket", "era", "equity", "treasury", "cash", "gold",
        *SPREADS,
    ]
    structural[join_cols].to_csv(output_dir / "issue-91-phase2-structural-joined.csv", index=False)
    causal[join_cols].to_csv(output_dir / "issue-91-phase2-causal-joined.csv", index=False)
    structural_summary.to_csv(output_dir / "issue-91-phase2-structural-cell-summary.csv", index=False)
    causal_summary.to_csv(output_dir / "issue-91-phase2-causal-cell-summary.csv", index=False)
    era_all.to_csv(output_dir / "issue-91-phase2-era-summary.csv", index=False)
    sign_consistency.to_csv(output_dir / "issue-91-phase2-era-sign-consistency.csv", index=False)
    leaders.to_csv(output_dir / "issue-91-phase2-leader-consistency.csv", index=False)
    abs_inf.to_csv(output_dir / "issue-91-phase2-absolute-inflation-comparison.csv", index=False)
    loeo.to_csv(output_dir / "issue-91-phase2-leave-one-era-out.csv", index=False)
    cross_overall.to_csv(output_dir / "issue-91-phase2-cross-source-overall.csv", index=False)
    cross_cells.to_csv(output_dir / "issue-91-phase2-cross-source-cells.csv", index=False)

    eligible_abs = abs_inf.loc[abs_inf["eligible_both_n_ge_5"]].copy()
    abs_sign_reversals = int(eligible_abs["sign_reversal_between_groups"].fillna(False).sum())
    abs_ci_excludes_zero = int(
        (
            (eligible_abs["bootstrap_difference_ci_low"].gt(0.0) & eligible_abs["bootstrap_difference_ci_high"].gt(0.0))
            | (eligible_abs["bootstrap_difference_ci_low"].lt(0.0) & eligible_abs["bootstrap_difference_ci_high"].lt(0.0))
        ).sum()
    )
    loeo_eligible = loeo.loc[loeo["remaining_n"].ge(5)]
    loeo_concentrated = int(loeo_eligible["era_concentrated"].sum())
    cross_eligible = cross_cells.loc[cross_cells["eligible_n_ge_5"]]
    cross_sign_agreement_rate = (
        float(cross_eligible["mean_sign_agreement"].mean()) if len(cross_eligible) else None
    )

    manifest = {
        "schema_version":1,
        "issue":91,
        "phase":"2-structural-and-causal-asset-validation",
        "preregistration_file":"decisions/issue-91-phase2-asset-validation-preregistered.json",
        "preregistration_preceded_asset_implementation":True,
        "hmra_freeze_validated_before_asset_join":bool(hmra_validation["validated"]),
        "production_v66_modified":False,
        "etfs_used":False,
        "portfolio_policy_evaluated":False,
        "sources":{
            "damodaran":{
                "requested_url":DAMODARAN_URL,
                "final_url":dam_final,
                "raw_sha256":sha256_bytes(dam_raw),
                "rows":int(len(assets)),
                "first_year":int(assets["year"].min()),
                "last_year":int(assets["year"].max()),
            },
            "jst":{
                "requested_url":JST_URL,
                "final_url":jst_final,
                "raw_sha256":sha256_bytes(jst_raw),
                "row_level_data_persisted":False,
                "license":"CC BY-NC-SA 4.0",
                "returns_citation":"Jorda, Knoll, Kuvshinov, Schularick, Taylor (2019), The Rate of Return on Everything",
            },
        },
        "pairings":{
            "structural":{"rows":int(len(structural)),"first_state_year":int(structural["state_year"].min()),"last_state_year":int(structural["state_year"].max())},
            "strict_causal_t_plus_2":{"rows":int(len(causal)),"first_state_year":int(causal["state_year"].min()),"last_state_year":int(causal["state_year"].max()),"first_return_year":int(causal["return_year"].min()),"last_return_year":int(causal["return_year"].max())},
        },
        "diagnostic_counts":{
            "absolute_inflation_eligible_cell_spread_comparisons":int(len(eligible_abs)),
            "absolute_inflation_sign_reversals":abs_sign_reversals,
            "absolute_inflation_bootstrap_difference_ci_excludes_zero":abs_ci_excludes_zero,
            "leave_one_era_out_rows":int(len(loeo_eligible)),
            "leave_one_era_out_era_concentrated_rows":loeo_concentrated,
            "cross_source_eligible_cells":int(len(cross_eligible)),
            "cross_source_cell_sign_agreement_rate":cross_sign_agreement_rate,
        },
        "cross_source_overall":cross_overall.iloc[0].to_dict(),
        "structural_verdict_committed":False,
        "output_files":{},
    }
    manifest_path = output_dir / "issue-91-phase2-manifest.json"
    manifest_path.write_text(json.dumps(manifest, indent=2, ensure_ascii=False, allow_nan=False)+"\n", encoding="utf-8")
    manifest["output_files"] = output_hash_manifest(output_dir, exclude={manifest_path.name})
    manifest_path.write_text(json.dumps(manifest, indent=2, ensure_ascii=False, allow_nan=False)+"\n", encoding="utf-8")
    return manifest


def main() -> int:
    parser=argparse.ArgumentParser(description="Issue #91 Phase 2 long-history structural asset validation")
    parser.add_argument("--output-dir",type=Path,required=True)
    args=parser.parse_args()
    print(json.dumps(run(args.output_dir),indent=2,ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
