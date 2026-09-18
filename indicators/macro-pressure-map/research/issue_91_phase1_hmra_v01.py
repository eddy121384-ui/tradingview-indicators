#!/usr/bin/env python3
"""Issue #91 Phase 1: Historical Macro Regime Analogue v0.1.

This module fetches only official macro series and creates annual macro states.
It intentionally never loads asset returns.
"""
from __future__ import annotations

import argparse
import hashlib
import io
import json
import math
from pathlib import Path
import re
import urllib.request

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
PREREG = HERE / "decisions" / "issue-91-phase1-hmra-v0.1-preregistered.json"

FED_IP_URL = "https://www.federalreserve.gov/releases/g17/Current/ipdisk/ip_sa.txt"
BLS_CPI_URL = "https://download.bls.gov/pub/time.series/cu/cu.data.1.AllItems"
FED_IP_CODE = "B50001"
BLS_CPI_CODE = "CUUR0000SA0"
USER_AGENT = "tradingview-indicators-issue-91/1.0"


def fetch_bytes(url: str, timeout: int = 30) -> tuple[bytes, str]:
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(request, timeout=timeout) as response:  # nosec B310 - frozen HTTPS sources
        payload = response.read()
        final_url = response.geturl()
    if not payload:
        raise RuntimeError(f"empty response from {url}")
    return payload, final_url


def sha256_bytes(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def parse_fed_ip(payload: bytes, series_code: str = FED_IP_CODE) -> pd.DataFrame:
    text = payload.decode("utf-8", errors="strict")
    rows = []
    pattern = re.compile(r'^"(?P<code>[^"]+)"\s+(?P<year>\d{4})\s+(?P<values>.+)$')
    for line in text.splitlines():
        m = pattern.match(line.strip())
        if not m or m.group("code") != series_code:
            continue
        values = m.group("values").split()
        if len(values) < 12:
            raise RuntimeError(f"Fed IP row has fewer than 12 months: {line}")
        nums = [float(x) for x in values[:12]]
        year = int(m.group("year"))
        for month, value in enumerate(nums, start=1):
            rows.append((year, month, value))
    if not rows:
        raise RuntimeError(f"Fed IP series {series_code} not found")
    frame = pd.DataFrame(rows, columns=["year", "month", "ip"])
    if frame.duplicated(["year", "month"]).any():
        raise RuntimeError("duplicate Fed IP year-month")
    return frame.sort_values(["year", "month"]).reset_index(drop=True)


def parse_bls_cpi(payload: bytes, series_code: str = BLS_CPI_CODE) -> pd.DataFrame:
    frame = pd.read_csv(io.BytesIO(payload), sep="\t", dtype=str)
    frame.columns = [str(c).strip() for c in frame.columns]
    needed = {"series_id", "year", "period", "value"}
    if not needed.issubset(frame.columns):
        raise RuntimeError(f"BLS CPI unexpected columns: {list(frame.columns)}")
    for col in ("series_id", "year", "period", "value"):
        frame[col] = frame[col].astype(str).str.strip()
    frame = frame.loc[frame["series_id"].eq(series_code)].copy()
    frame = frame.loc[frame["period"].str.fullmatch(r"M(?:0[1-9]|1[0-2])", na=False)].copy()
    if frame.empty:
        raise RuntimeError(f"BLS CPI series {series_code} not found")
    frame["month"] = frame["period"].str[1:].astype(int)
    frame["year"] = pd.to_numeric(frame["year"], errors="raise").astype(int)
    frame["cpi"] = pd.to_numeric(frame["value"], errors="raise").astype(float)
    if frame.duplicated(["year", "month"]).any():
        raise RuntimeError("duplicate BLS CPI year-month")
    return frame[["year", "month", "cpi"]].sort_values(["year", "month"]).reset_index(drop=True)


def annual_december(ip: pd.DataFrame, cpi: pd.DataFrame, end_year: int = 2025) -> pd.DataFrame:
    ip_dec = ip.loc[ip["month"].eq(12), ["year", "ip"]].copy()
    cpi_dec = cpi.loc[cpi["month"].eq(12), ["year", "cpi"]].copy()
    annual = ip_dec.merge(cpi_dec, on="year", how="inner", validate="one_to_one")
    annual = annual.loc[annual["year"].le(end_year)].sort_values("year").reset_index(drop=True)
    if annual.empty:
        raise RuntimeError("no annual December overlap")
    if annual[["ip", "cpi"]].isna().any().any():
        raise RuntimeError("missing December level in annual overlap")
    return annual


def prior_window_z(series: pd.Series, window: int) -> pd.Series:
    prior = series.shift(1)
    mean = prior.rolling(window, min_periods=window).mean()
    sd = prior.rolling(window, min_periods=window).std(ddof=0)
    return ((series - mean) / sd).where(sd.notna() & (sd != 0.0))


def scaled_axis(rate: pd.Series, window: int) -> pd.DataFrame:
    accel = rate.diff()
    level_z = prior_window_z(rate, window)
    accel_z = prior_window_z(accel, window)
    raw = 0.70 * level_z + 0.30 * accel_z
    score = 100.0 * np.tanh(raw / 2.0)
    return pd.DataFrame({
        "rate": rate,
        "acceleration": accel,
        "level_z": level_z,
        "acceleration_z": accel_z,
        "raw": raw,
        "score": score,
    })


def tri_state(value: float) -> str:
    if pd.isna(value):
        return "n/a"
    if value > 10.0:
        return "high"
    if value < -10.0:
        return "low"
    return "neutral"


REGIMES = {
    ("high", "low"): "Goldilocks / Disinflationary Expansion",
    ("high", "neutral"): "Benign Expansion / Stable Inflation",
    ("high", "high"): "Reflation / Inflation Rising",
    ("neutral", "low"): "Disinflationary Drift",
    ("neutral", "neutral"): "Neutral / Range-bound Macro",
    ("neutral", "high"): "Inflation Pressure without Growth Confirmation",
    ("low", "low"): "Slowdown / Disinflation",
    ("low", "neutral"): "Growth Slowdown / Stable Inflation",
    ("low", "high"): "Stagflation Pressure",
}


def core_regime(growth_state: str, inflation_state: str) -> str:
    return REGIMES.get((growth_state, inflation_state), "n/a")


def inflation_bucket(pi: float) -> str:
    if pd.isna(pi):
        return "n/a"
    if pi < 0.0:
        return "deflation"
    if pi < 2.0:
        return "low"
    if pi < 4.0:
        return "moderate"
    if pi < 6.0:
        return "high"
    return "very_high"


def era_label(year: int) -> str:
    eras = [
        (1928, 1945, "Depression_WWII"),
        (1946, 1970, "Postwar_Bretton_Woods"),
        (1971, 1979, "Great_Inflation_pre_Volcker"),
        (1980, 1984, "Volcker_disinflation"),
        (1985, 1999, "Post_Volcker_disinflation"),
        (2000, 2007, "Pre_GFC_2000s"),
        (2008, 2019, "GFC_QE_low_inflation"),
        (2020, 2020, "COVID_shock"),
        (2021, 2022, "Inflation_surge"),
        (2023, 2025, "Higher_rate_disinflation"),
    ]
    for start, end, label in eras:
        if start <= year <= end:
            return label
    return "outside_primary_era"


def build_hmra(annual: pd.DataFrame, primary_window: int = 5, sensitivity_window: int = 10) -> pd.DataFrame:
    out = annual.copy()
    out["growth_rate"] = 100.0 * np.log(out["ip"] / out["ip"].shift(1))
    out["inflation_rate"] = 100.0 * np.log(out["cpi"] / out["cpi"].shift(1))

    g = scaled_axis(out["growth_rate"], primary_window).add_prefix("growth_")
    i = scaled_axis(out["inflation_rate"], primary_window).add_prefix("inflation_")
    gs = scaled_axis(out["growth_rate"], sensitivity_window).add_prefix("growth_sens10_")
    is_ = scaled_axis(out["inflation_rate"], sensitivity_window).add_prefix("inflation_sens10_")
    out = pd.concat([out, g, i, gs, is_], axis=1)

    out["growth_state"] = out["growth_score"].map(tri_state)
    out["inflation_state"] = out["inflation_score"].map(tri_state)
    out["core_regime"] = [
        core_regime(gv, iv) for gv, iv in zip(out["growth_state"], out["inflation_state"])
    ]
    out["growth_state_sens10"] = out["growth_sens10_score"].map(tri_state)
    out["inflation_state_sens10"] = out["inflation_sens10_score"].map(tri_state)
    out["core_regime_sens10"] = [
        core_regime(gv, iv)
        for gv, iv in zip(out["growth_state_sens10"], out["inflation_state_sens10"])
    ]
    out["absolute_inflation_bucket"] = out["inflation_rate"].map(inflation_bucket)
    out["era"] = out["year"].map(era_label)
    out["strict_causal_return_year"] = out["year"] + 2
    out["same_year_structural_only"] = True
    return out


def validate_prereg() -> dict:
    p = json.loads(PREREG.read_text(encoding="utf-8"))
    if p["issue"] != 91 or p["phase"] != "1-hmra-v0.1-preregistration":
        raise RuntimeError("bad Phase 1 prereg identity")
    if p["created_before_asset_conditioned_results"] is not True:
        raise RuntimeError("prereg timing guard failed")
    forbidden = " ".join(p["phase1_forbidden_outputs"]).lower()
    for token in ("equity returns", "treasury returns", "t-bill returns", "gold returns", "portfolio performance"):
        if token not in forbidden:
            raise RuntimeError(f"missing forbidden output guard: {token}")
    return p


def run(output_dir: Path) -> dict:
    p = validate_prereg()
    fed_raw, fed_final = fetch_bytes(FED_IP_URL)
    bls_raw, bls_final = fetch_bytes(BLS_CPI_URL)
    ip = parse_fed_ip(fed_raw)
    cpi = parse_bls_cpi(bls_raw)
    annual = annual_december(ip, cpi, end_year=p["primary_analysis_window"]["completed_macro_year_end"])
    states = build_hmra(
        annual,
        primary_window=p["score_rule"]["primary_reference_window_years"],
        sensitivity_window=p["score_rule"]["sensitivity_reference_window_years"],
    )

    output_dir.mkdir(parents=True, exist_ok=True)
    state_path = output_dir / "issue-91-hmra-v0.1-macro-states.csv"
    states.to_csv(state_path, index=False)

    valid = states.loc[
        states["year"].ge(p["primary_analysis_window"]["asset_history_target_start_year"])
        & states["growth_score"].notna()
        & states["inflation_score"].notna()
    ].copy()
    if valid.empty:
        raise RuntimeError("no valid HMRA states in primary analysis window")

    occupancy = (
        valid.groupby(["growth_state", "inflation_state", "core_regime"], dropna=False)
        .size()
        .rename("years")
        .reset_index()
        .sort_values(["growth_state", "inflation_state"])
    )
    occupancy.to_csv(output_dir / "issue-91-hmra-v0.1-occupancy.csv", index=False)

    sensitivity_comparable = valid["core_regime_sens10"].ne("n/a")
    agreement = (
        valid.loc[sensitivity_comparable, "core_regime"]
        .eq(valid.loc[sensitivity_comparable, "core_regime_sens10"])
        .mean()
        if sensitivity_comparable.any()
        else np.nan
    )

    manifest = {
        "schema_version":1,
        "issue":91,
        "phase":"1-hmra-v0.1",
        "asset_returns_loaded":False,
        "asset_conditioned_results_computed":False,
        "portfolio_results_computed":False,
        "sources":{
            "fed_ip":{
                "requested_url":FED_IP_URL,
                "final_url":fed_final,
                "series_code":FED_IP_CODE,
                "sha256":sha256_bytes(fed_raw),
                "bytes":len(fed_raw),
                "first_year":int(ip["year"].min()),
                "last_year":int(ip["year"].max()),
            },
            "bls_cpi":{
                "requested_url":BLS_CPI_URL,
                "final_url":bls_final,
                "series_code":BLS_CPI_CODE,
                "sha256":sha256_bytes(bls_raw),
                "bytes":len(bls_raw),
                "first_year":int(cpi["year"].min()),
                "last_year":int(cpi["year"].max()),
            },
        },
        "annual_overlap":{
            "first_year":int(annual["year"].min()),
            "last_year":int(annual["year"].max()),
            "rows":int(len(annual)),
        },
        "primary_valid_states":{
            "first_year":int(valid["year"].min()),
            "last_year":int(valid["year"].max()),
            "years":int(len(valid)),
            "regime_occupancy":occupancy.to_dict(orient="records"),
        },
        "sensitivity_10y":{
            "comparable_years":int(sensitivity_comparable.sum()),
            "exact_regime_agreement_rate":float(agreement) if not pd.isna(agreement) else None,
            "diagnostic_only":True,
        },
        "timing":{
            "same_year_state_return_role":"structural descriptive only; not causal",
            "strict_causal_return_year_offset":2,
        },
    }
    (output_dir / "issue-91-hmra-v0.1-manifest.json").write_text(
        json.dumps(manifest, indent=2, ensure_ascii=False, allow_nan=False)+"\n",
        encoding="utf-8",
    )
    return manifest


def main() -> int:
    parser=argparse.ArgumentParser(description="Build Issue #91 HMRA-v0.1 macro states only")
    parser.add_argument("--output-dir", type=Path, required=True)
    args=parser.parse_args()
    manifest=run(args.output_dir)
    print(json.dumps(manifest, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
