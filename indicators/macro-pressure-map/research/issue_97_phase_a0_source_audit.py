#!/usr/bin/env python3
"""Issue #97 Phase A0: official source audit only."""
from __future__ import annotations
import argparse, csv, hashlib, io, json
from pathlib import Path
import pandas as pd

from issue_91_phase1_hmra_v01 import (
    FED_IP_URL, FED_IP_CODE, BLS_CPI_URL, BLS_CPI_CODE,
    fetch_bytes, fetch_bls_cpi_api, parse_fed_ip,
)

HERE=Path(__file__).resolve().parent
PLAN=HERE/"decisions"/"issue-97-phase-a0-source-plan.json"
EFFR_URL="https://www.federalreserve.gov/datadownload/Output.aspx?rel=H15&series=d7e27b7b09a3a7feae95b9c61781fcd8&lastobs=&from=07/01/1954&to=12/31/2025&filetype=csv&label=omit&layout=seriescolumn"
EFFR_CODE="H15/H15/RIFSPFF_N.M"

def sha256_bytes(b:bytes)->str:
    return hashlib.sha256(b).hexdigest()

def parse_h15_effr(payload:bytes)->pd.DataFrame:
    text=payload.decode("utf-8-sig",errors="strict")
    lines=text.splitlines()
    header_idx=None
    for i,line in enumerate(lines):
        if "Time Period" in line and "RIFSPFF_N.M" in line:
            header_idx=i
            break
    if header_idx is None:
        raise RuntimeError("H15 monthly EFFR header not found")
    frame=pd.read_csv(io.StringIO("\n".join(lines[header_idx:])))
    frame.columns=[str(c).strip().strip('"') for c in frame.columns]
    if "Time Period" not in frame.columns or "RIFSPFF_N.M" not in frame.columns:
        raise RuntimeError(f"unexpected H15 columns: {list(frame.columns)}")
    out=pd.DataFrame({
        "month":pd.to_datetime(frame["Time Period"],format="%Y-%m",errors="coerce"),
        "effr":pd.to_numeric(frame["RIFSPFF_N.M"].replace("ND",pd.NA),errors="coerce"),
    }).dropna(subset=["month"]).sort_values("month").reset_index(drop=True)
    out=out.loc[out["month"].le(pd.Timestamp("2025-12-01"))].copy()
    if out.empty or out["effr"].isna().any():
        raise RuntimeError("H15 EFFR has missing values in frozen window")
    if out["month"].duplicated().any():
        raise RuntimeError("duplicate H15 monthly observation")
    return out

def monthize(frame:pd.DataFrame,value_col:str)->pd.DataFrame:
    out=frame.copy()
    out["month_date"]=pd.to_datetime(dict(year=out["year"],month=out["month"],day=1))
    return out[["month_date",value_col]].rename(columns={value_col:"value"})

def run(output_dir:Path)->dict:
    plan=json.loads(PLAN.read_text(encoding="utf-8"))
    assert plan["created_before_policy_model_outcomes"] is True
    assert plan["created_before_treasury_outcomes"] is True

    ip_raw,ip_final=fetch_bytes(FED_IP_URL)
    ip=parse_fed_ip(ip_raw)
    cpi,cpi_canonical,cpi_requests=fetch_bls_cpi_api(start_year=1913,end_year=2025)
    effr_raw,effr_final=fetch_bytes(EFFR_URL)
    effr=parse_h15_effr(effr_raw)

    ipm=monthize(ip,"ip")
    cpim=monthize(cpi,"cpi")
    overlap=ipm.rename(columns={"value":"ip"}).merge(
        cpim.rename(columns={"value":"cpi"}),on="month_date",how="inner"
    ).merge(effr.rename(columns={"month":"month_date"}),on="month_date",how="inner")
    overlap=overlap.loc[overlap["month_date"].between("1954-07-01","2025-12-01")].copy()
    if overlap.empty:
        raise RuntimeError("no IP/CPI/EFFR overlap")

    result={
      "schema_version":1,"issue":97,"phase":"A0-policy-reaction-source-audit",
      "policy_model_outcomes_computed":False,"treasury_outcomes_loaded":False,"portfolio_results_computed":False,
      "sources":{
        "ip":{"series_code":FED_IP_CODE,"requested_url":FED_IP_URL,"final_url":ip_final,
              "raw_sha256":sha256_bytes(ip_raw),"raw_bytes":len(ip_raw),
              "first_month":f"{int(ip.year.min()):04d}-{int(ip.loc[ip.year.eq(ip.year.min()),'month'].min()):02d}",
              "last_month":f"{int(ip.year.max()):04d}-{int(ip.loc[ip.year.eq(ip.year.max()),'month'].max()):02d}"},
        "cpi":{"series_code":BLS_CPI_CODE,"requested_url":BLS_CPI_URL,
               "canonical_observations_sha256":sha256_bytes(cpi_canonical),
               "canonical_observations_bytes":len(cpi_canonical),"request_count":cpi_requests,
               "first_month":f"{int(cpi.year.min()):04d}-{int(cpi.loc[cpi.year.eq(cpi.year.min()),'month'].min()):02d}",
               "last_month":f"{int(cpi.year.max()):04d}-{int(cpi.loc[cpi.year.eq(cpi.year.max()),'month'].max()):02d}"},
        "effr":{"series_code":EFFR_CODE,"requested_url":EFFR_URL,"final_url":effr_final,
                "raw_sha256":sha256_bytes(effr_raw),"raw_bytes":len(effr_raw),
                "first_month":effr["month"].min().strftime("%Y-%m"),
                "last_month":effr["month"].max().strftime("%Y-%m"),"observations":int(len(effr))}
      },
      "monthly_overlap":{
        "first_month":overlap["month_date"].min().strftime("%Y-%m"),
        "last_month":overlap["month_date"].max().strftime("%Y-%m"),
        "observations":int(len(overlap)),
        "missing_ip":int(overlap["ip"].isna().sum()),
        "missing_cpi":int(overlap["cpi"].isna().sum()),
        "missing_effr":int(overlap["effr"].isna().sum())
      }
    }
    output_dir.mkdir(parents=True,exist_ok=True)
    (output_dir/"issue-97-phase-a0-source-audit.json").write_text(json.dumps(result,indent=2,ensure_ascii=False)+"\n",encoding="utf-8")
    return result

def main()->int:
    ap=argparse.ArgumentParser(); ap.add_argument("--output-dir",type=Path,required=True)
    args=ap.parse_args(); print(json.dumps(run(args.output_dir),indent=2)); return 0

if __name__=="__main__":
    raise SystemExit(main())
