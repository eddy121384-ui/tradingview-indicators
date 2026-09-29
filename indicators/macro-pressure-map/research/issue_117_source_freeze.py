#!/usr/bin/env python3
"""Issue #117 Phase 0 source freeze and monthly HMRA state build.

No conditioned Gold-vs-Cash payoff is computed in this module.
"""
from __future__ import annotations

import argparse
import hashlib
import io
import json
import math
import re
import urllib.request
import zipfile
from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent

FED_IP_URL = "https://www.federalreserve.gov/releases/g17/Current/ipdisk/ip_sa.txt"
BLS_URL = "https://api.bls.gov/publicAPI/v1/timeseries/data/"
FED_IP_CODE = "B50001"
BLS_CPI_CODE = "CUUR0000SA0"
GOLD_MIRROR_COMMIT = "95bfea9197222dcda13d8c4d9928fb631fe745aa"
GOLD_URL = f"https://raw.githubusercontent.com/datasets/gold-prices/{GOLD_MIRROR_COMMIT}/data/monthly.csv"
GOLD_README_URL = f"https://raw.githubusercontent.com/datasets/gold-prices/{GOLD_MIRROR_COMMIT}/README.md"
FF_URL = "https://mba.tuck.dartmouth.edu/pages/faculty/ken.french/ftp/F-F_Research_Data_Factors_CSV.zip"
USER_AGENT = "tradingview-indicators-issue-117/1.0"


def sha256_bytes(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def fetch_bytes(url: str, *, data: bytes | None = None, headers: dict | None = None) -> tuple[bytes, str]:
    h = {"User-Agent": USER_AGENT}
    if headers:
        h.update(headers)
    req = urllib.request.Request(url, data=data, headers=h, method="POST" if data is not None else "GET")
    with urllib.request.urlopen(req, timeout=60) as resp:  # nosec B310 official/frozen HTTPS sources
        payload = resp.read()
        final = resp.geturl()
    if not payload:
        raise RuntimeError(f"empty response from {url}")
    return payload, final


def parse_fed_ip(payload: bytes) -> pd.DataFrame:
    text = payload.decode("utf-8")
    rows = []
    pat = re.compile(r'^"(?P<code>[^"]+)"\s+(?P<year>\d{4})\s+(?P<values>.+)$')
    for line in text.splitlines():
        m = pat.match(line.strip())
        if not m or m.group("code") != FED_IP_CODE:
            continue
        vals = [float(x) for x in m.group("values").split()]
        y = int(m.group("year"))
        for month, value in enumerate(vals, start=1):
            rows.append((pd.Timestamp(y, month, 1), value))
    if not rows:
        raise RuntimeError("Fed IP series not found")
    out = pd.DataFrame(rows, columns=["date", "ip"]).drop_duplicates("date").sort_values("date")
    return out.reset_index(drop=True)


def fetch_bls_cpi(start_year: int = 1913, end_year: int = 2026) -> tuple[pd.DataFrame, bytes, int]:
    obs = []
    requests = 0
    for start in range(start_year, end_year + 1, 10):
        end = min(start + 9, end_year)
        body = json.dumps({"seriesid":[BLS_CPI_CODE],"startyear":str(start),"endyear":str(end)}).encode()
        payload, _ = fetch_bytes(BLS_URL, data=body, headers={"Content-Type":"application/json"})
        j = json.loads(payload.decode())
        requests += 1
        if j.get("status") != "REQUEST_SUCCEEDED":
            raise RuntimeError(f"BLS failed {start}-{end}: {j.get('message')}")
        series = j.get("Results",{}).get("series",[])
        if len(series) != 1 or series[0].get("seriesID") != BLS_CPI_CODE:
            raise RuntimeError("unexpected BLS response")
        for item in series[0].get("data",[]):
            p = str(item.get("period",""))
            if not re.fullmatch(r"M(?:0[1-9]|1[0-2])", p):
                continue
            try:
                v = float(item["value"])
            except (TypeError, ValueError):
                continue
            obs.append((pd.Timestamp(int(item["year"]), int(p[1:]), 1), v))
    out = pd.DataFrame(obs, columns=["date","cpi"]).drop_duplicates("date", keep="last").sort_values("date")
    canonical = json.dumps(
        [{"date":d.strftime("%Y-%m-%d"),"cpi":float(v)} for d,v in out.itertuples(index=False)],
        separators=(",",":"), sort_keys=True
    ).encode()
    return out.reset_index(drop=True), canonical, requests


def parse_gold(payload: bytes) -> pd.DataFrame:
    raw = pd.read_csv(io.BytesIO(payload))
    if list(raw.columns) != ["Date","Price"]:
        raise RuntimeError(f"unexpected gold columns {list(raw.columns)}")
    raw["date"] = pd.to_datetime(raw["Date"].astype(str) + "-01", errors="raise")
    raw["gold_usd"] = pd.to_numeric(raw["Price"], errors="raise").astype(float)
    out = raw[["date","gold_usd"]].drop_duplicates("date", keep="last").sort_values("date")
    if (out["gold_usd"] <= 0).any():
        raise RuntimeError("invalid gold price")
    return out.reset_index(drop=True)


def parse_french_rf(zip_payload: bytes) -> pd.DataFrame:
    with zipfile.ZipFile(io.BytesIO(zip_payload)) as zf:
        names = zf.namelist()
        csv_names = [n for n in names if n.lower().endswith(".csv")]
        if len(csv_names) != 1:
            raise RuntimeError(f"unexpected French zip members: {names}")
        text = zf.read(csv_names[0]).decode("utf-8-sig", errors="strict")

    rows = []
    started = False
    for line in text.splitlines():
        fields = [x.strip() for x in line.split(",")]
        if not fields:
            continue
        key = fields[0]
        if re.fullmatch(r"\d{6}", key):
            started = True
            if len(fields) < 5:
                raise RuntimeError("French monthly row has too few columns")
            y, m = int(key[:4]), int(key[4:])
            rf_pct = float(fields[4])
            rows.append((pd.Timestamp(y,m,1), rf_pct / 100.0))
        elif started:
            break
    if not rows:
        raise RuntimeError("no monthly RF rows parsed")
    out = pd.DataFrame(rows, columns=["date","rf_return"]).drop_duplicates("date").sort_values("date")
    return out.reset_index(drop=True)


def prior_z(s: pd.Series, window: int = 60) -> pd.Series:
    prior = s.shift(1)
    mean = prior.rolling(window, min_periods=window).mean()
    sd = prior.rolling(window, min_periods=window).std(ddof=0)
    return ((s - mean) / sd).where(sd.notna() & sd.ne(0))


def scaled_axis(rate: pd.Series) -> pd.Series:
    accel = rate - rate.shift(12)
    raw = 0.70 * prior_z(rate, 60) + 0.30 * prior_z(accel, 60)
    return 100.0 * np.tanh(raw / 2.0)


def tri_state(x: float) -> str:
    if pd.isna(x):
        return "n/a"
    if x < -10:
        return "low"
    if x > 10:
        return "high"
    return "neutral"


REGIMES = {
    ("high","low"):"Goldilocks / Disinflationary Expansion",
    ("high","neutral"):"Benign Expansion / Stable Inflation",
    ("high","high"):"Reflation / Inflation Rising",
    ("neutral","low"):"Disinflationary Drift",
    ("neutral","neutral"):"Neutral / Range-bound Macro",
    ("neutral","high"):"Inflation Pressure without Growth Confirmation",
    ("low","low"):"Slowdown / Disinflation",
    ("low","neutral"):"Growth Slowdown / Stable Inflation",
    ("low","high"):"Stagflation Pressure",
}
DEFENSIVE = {
    "Slowdown / Disinflation",
    "Growth Slowdown / Stable Inflation",
    "Stagflation Pressure",
}


def build_monthly_hmra(ip: pd.DataFrame, cpi: pd.DataFrame) -> pd.DataFrame:
    x = ip.merge(cpi, on="date", how="inner", validate="one_to_one").sort_values("date").reset_index(drop=True)
    x["growth_rate"] = 100.0 * np.log(x["ip"] / x["ip"].shift(12))
    x["inflation_rate"] = 100.0 * np.log(x["cpi"] / x["cpi"].shift(12))
    x["growth_accel"] = x["growth_rate"] - x["growth_rate"].shift(12)
    x["inflation_accel"] = x["inflation_rate"] - x["inflation_rate"].shift(12)
    x["growth_score"] = scaled_axis(x["growth_rate"])
    x["inflation_score"] = scaled_axis(x["inflation_rate"])
    x["growth_state"] = x["growth_score"].map(tri_state)
    x["inflation_state"] = x["inflation_score"].map(tri_state)
    x["regime"] = [REGIMES.get((g,i),"n/a") for g,i in zip(x["growth_state"],x["inflation_state"])]
    x["defensive_gold_state"] = x["regime"].isin(DEFENSIVE)
    return x


def write_csv(frame: pd.DataFrame, path: Path) -> dict:
    serial = frame.copy()
    if "date" in serial.columns:
        serial["date"] = pd.to_datetime(serial["date"]).dt.strftime("%Y-%m-%d")
    serial.to_csv(path, index=False, float_format="%.12g")
    return {"file":path.name,"rows":int(len(frame)),"sha256":sha256_file(path)}


def run(out_dir: Path) -> dict:
    out_dir.mkdir(parents=True, exist_ok=True)

    fed_raw, fed_final = fetch_bytes(FED_IP_URL)
    ip = parse_fed_ip(fed_raw)
    cpi, cpi_canon, bls_requests = fetch_bls_cpi()

    gold_raw, gold_final = fetch_bytes(GOLD_URL)
    gold_readme, _ = fetch_bytes(GOLD_README_URL)
    if b"World Bank Commodity Markets" not in gold_readme or b"1960" not in gold_readme:
        raise RuntimeError("gold mirror README provenance guard failed")
    gold = parse_gold(gold_raw)

    ff_raw, ff_final = fetch_bytes(FF_URL)
    rf = parse_french_rf(ff_raw)

    hmra = build_monthly_hmra(ip, cpi)

    files = {
        "macro": write_csv(hmra, out_dir/"issue-117-monthly-hmra.csv"),
        "gold": write_csv(gold, out_dir/"issue-117-gold-monthly.csv"),
        "cash": write_csv(rf, out_dir/"issue-117-cash-rf-monthly.csv"),
    }

    common = (
        hmra.loc[hmra["date"] >= pd.Timestamp("1975-01-01"), ["date"]]
        .merge(gold[["date"]], on="date")
        .merge(rf[["date"]], on="date")
        .sort_values("date")
    )
    valid_states = hmra.loc[
        (hmra["date"] >= pd.Timestamp("1975-01-01"))
        & hmra["regime"].ne("n/a")
    ]
    span_years = (common["date"].max() - common["date"].min()).days / 365.2425 if len(common) else 0.0

    manifest = {
        "schema_version":1,
        "issue":117,
        "phase":"source-freeze-before-payoff",
        "conditioned_gold_cash_payoff_computed":False,
        "source_hashes":{
            "fed_ip_raw":sha256_bytes(fed_raw),
            "bls_cpi_canonical":sha256_bytes(cpi_canon),
            "gold_mirror_raw":sha256_bytes(gold_raw),
            "gold_mirror_readme":sha256_bytes(gold_readme),
            "fama_french_zip":sha256_bytes(ff_raw),
        },
        "sources":{
            "fed_ip":{"url":FED_IP_URL,"final_url":fed_final,"series":FED_IP_CODE,"first":ip["date"].min().date().isoformat(),"last":ip["date"].max().date().isoformat()},
            "bls_cpi":{"url":BLS_URL,"series":BLS_CPI_CODE,"requests":bls_requests,"first":cpi["date"].min().date().isoformat(),"last":cpi["date"].max().date().isoformat()},
            "gold":{"url":GOLD_URL,"final_url":gold_final,"mirror_commit":GOLD_MIRROR_COMMIT,"upstream":"World Bank Commodity Markets Pink Sheet per mirror README","first":gold["date"].min().date().isoformat(),"last":gold["date"].max().date().isoformat()},
            "cash_rf":{"url":FF_URL,"final_url":ff_final,"series":"RF","first":rf["date"].min().date().isoformat(),"last":rf["date"].max().date().isoformat()},
        },
        "files":files,
        "common_source_coverage":{
            "first":common["date"].min().date().isoformat(),
            "last":common["date"].max().date().isoformat(),
            "months":int(len(common)),
            "span_years":float(span_years),
        },
        "monthly_hmra":{
            "valid_state_first":valid_states["date"].min().date().isoformat(),
            "valid_state_last":valid_states["date"].max().date().isoformat(),
            "valid_state_months":int(len(valid_states)),
            "defensive_months":int(valid_states["defensive_gold_state"].sum()),
            "regime_counts":valid_states["regime"].value_counts().sort_index().to_dict(),
        },
        "gate":{
            "span_ge_45_years":bool(span_years >= 45.0),
            "gold_starts_by_1975":bool(gold["date"].min() <= pd.Timestamp("1975-01-01")),
            "cash_starts_by_1975":bool(rf["date"].min() <= pd.Timestamp("1975-01-01")),
            "hmra_valid_by_1975":bool(valid_states["date"].min() <= pd.Timestamp("1975-01-01")),
        },
    }
    (out_dir/"issue-117-source-freeze-manifest.json").write_text(
        json.dumps(manifest,indent=2,ensure_ascii=False)+"\n", encoding="utf-8"
    )
    print(json.dumps(manifest,indent=2,ensure_ascii=False))
    return manifest


def main() -> None:
    ap=argparse.ArgumentParser()
    ap.add_argument("--output-dir",type=Path,required=True)
    args=ap.parse_args()
    m=run(args.output_dir)
    if not all(m["gate"].values()):
        raise SystemExit("Issue #117 source gate failed closed")


if __name__=="__main__":
    main()
