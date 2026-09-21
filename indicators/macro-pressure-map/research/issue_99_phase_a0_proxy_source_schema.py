#!/usr/bin/env python3
"""Issue #99 A0: official SF Fed Proxy Funds Rate workbook schema audit only."""
from __future__ import annotations

import argparse
import hashlib
import io
import json
import re
import urllib.parse
import urllib.request
from pathlib import Path

import pandas as pd

HERE=Path(__file__).resolve().parent
PLAN=HERE/"decisions"/"issue-99-phase-a0-proxy-source-plan.json"
PAGE_URL="https://www.frbsf.org/research-and-insights/data-and-indicators/proxy-funds-rate/"
USER_AGENT="tradingview-indicators-issue-99/1.0"


def fetch(url:str,timeout:int=45)->tuple[bytes,str,str]:
    req=urllib.request.Request(url,headers={"User-Agent":USER_AGENT})
    with urllib.request.urlopen(req,timeout=timeout) as r:  # nosec B310 - frozen official HTTPS source
        payload=r.read()
        final=r.geturl()
        ctype=r.headers.get("Content-Type","")
    if not payload:
        raise RuntimeError(f"empty response: {url}")
    return payload,final,ctype


def sha256_bytes(b:bytes)->str:
    return hashlib.sha256(b).hexdigest()


def resolve_workbook_url(page_html:bytes,page_final_url:str)->str:
    text=page_html.decode("utf-8",errors="ignore")
    hrefs=re.findall(r'href=["\']([^"\']*proxy-funds-rate-data\.xlsx[^"\']*)["\']',text,re.I)
    if not hrefs:
        raise RuntimeError("official Proxy Funds Rate workbook link not found")
    unique=[]
    for h in hrefs:
        u=urllib.parse.urljoin(page_final_url,h.replace("&amp;","&"))
        if u not in unique:
            unique.append(u)
    if len(unique)!=1:
        raise RuntimeError(f"ambiguous Proxy Funds Rate workbook links: {unique}")
    return unique[0]


def cell_to_json(v):
    if pd.isna(v):
        return None
    if isinstance(v,pd.Timestamp):
        return v.isoformat()
    if hasattr(v,"item"):
        try: v=v.item()
        except Exception: pass
    if isinstance(v,(str,int,float,bool)) or v is None:
        return v
    return str(v)


def parse_monthly_proxy(payload:bytes,end_month:str="2025-12")->pd.DataFrame:
    raw=pd.read_excel(io.BytesIO(payload),sheet_name="Monthly",header=None,engine="openpyxl")
    if raw.shape[1] < 3:
        raise RuntimeError("Monthly sheet has fewer than 3 columns")
    header=[str(x).strip() for x in raw.iloc[0,:3].tolist()]
    expected=["Date","Effective funds rate","Proxy funds rate"]
    if header != expected:
        raise RuntimeError(f"unexpected Monthly header: {header}")
    out=raw.iloc[1:,:3].copy()
    out.columns=["date","workbook_effr","proxy_rate"]
    out["date"]=pd.to_datetime(out["date"],errors="coerce")
    out["workbook_effr"]=pd.to_numeric(out["workbook_effr"],errors="coerce")
    out["proxy_rate"]=pd.to_numeric(out["proxy_rate"],errors="coerce")
    out=out.dropna(subset=["date"]).sort_values("date").reset_index(drop=True)
    cutoff=pd.Period(end_month,freq="M").end_time.normalize()
    used=out.loc[out["date"].le(cutoff)].copy()
    if used.empty or used[["workbook_effr","proxy_rate"]].isna().any().any():
        raise RuntimeError("missing monthly proxy/effr values in canonical window")
    if used["date"].duplicated().any():
        raise RuntimeError("duplicate proxy monthly date")
    expected_dates=pd.period_range(used["date"].min().to_period("M"),pd.Period(end_month,"M"),freq="M")
    actual=pd.PeriodIndex(used["date"].dt.to_period("M"))
    missing=[str(x) for x in expected_dates.difference(actual)]
    if missing:
        raise RuntimeError(f"missing monthly proxy observations: {missing}")
    return used


def canonical_proxy_payload(frame:pd.DataFrame)->bytes:
    records=[
        {
            "month":row.date.strftime("%Y-%m"),
            "workbook_effr":round(float(row.workbook_effr),10),
            "proxy_rate":round(float(row.proxy_rate),10),
        }
        for row in frame.itertuples(index=False)
    ]
    return json.dumps(records,sort_keys=True,separators=(",",":")).encode("utf-8")


def audit_workbook(payload:bytes)->dict:
    book=pd.ExcelFile(io.BytesIO(payload),engine="openpyxl")
    sheets=[]
    for sheet in book.sheet_names:
        frame=pd.read_excel(book,sheet_name=sheet,header=None,engine="openpyxl")
        preview=[]
        for row in frame.head(8).itertuples(index=False,name=None):
            preview.append([cell_to_json(x) for x in row[:12]])
        sheets.append({
            "sheet":str(sheet),
            "rows":int(frame.shape[0]),
            "columns":int(frame.shape[1]),
            "preview_first_8_rows_first_12_columns":preview
        })
    return {"sheet_names":[str(x) for x in book.sheet_names],"sheets":sheets}


def run(output_dir:Path)->dict:
    plan=json.loads(PLAN.read_text(encoding="utf-8"))
    assert plan["created_before_policy_model_outcomes"] is True
    assert plan["created_before_treasury_outcomes"] is True

    page,page_final,page_ctype=fetch(PAGE_URL)
    workbook_url=resolve_workbook_url(page,page_final)
    workbook,workbook_final,workbook_ctype=fetch(workbook_url)
    if "spreadsheet" not in workbook_ctype.lower() and not workbook_final.lower().split("?")[0].endswith(".xlsx"):
        raise RuntimeError(f"unexpected workbook content type: {workbook_ctype}")

    monthly=parse_monthly_proxy(workbook,"2025-12")
    canonical=canonical_proxy_payload(monthly)
    result={
      "schema_version":1,
      "issue":99,
      "phase":"A0-proxy-policy-stance-source-schema-audit",
      "policy_model_outcomes_computed":False,
      "treasury_outcomes_loaded":False,
      "portfolio_results_computed":False,
      "page":{
        "requested_url":PAGE_URL,
        "final_url":page_final,
        "content_type":page_ctype,
        "sha256":sha256_bytes(page),
        "bytes":len(page)
      },
      "workbook":{
        "resolved_url":workbook_url,
        "final_url":workbook_final,
        "content_type":workbook_ctype,
        "raw_sha256":sha256_bytes(workbook),
        "raw_bytes":len(workbook),
        **audit_workbook(workbook),
        "canonical_monthly_through_2025_12":{
          "first_month":monthly["date"].min().strftime("%Y-%m"),
          "last_month":monthly["date"].max().strftime("%Y-%m"),
          "observations":int(len(monthly)),
          "canonical_sha256":sha256_bytes(canonical),
          "canonical_bytes":len(canonical),
          "proxy_min":float(monthly["proxy_rate"].min()),
          "proxy_max":float(monthly["proxy_rate"].max())
        }
      }
    }
    output_dir.mkdir(parents=True,exist_ok=True)
    (output_dir/"issue-99-phase-a0-proxy-source-schema.json").write_text(
        json.dumps(result,indent=2,ensure_ascii=False)+"\n",encoding="utf-8")
    return result


def main()->int:
    ap=argparse.ArgumentParser()
    ap.add_argument("--output-dir",type=Path,required=True)
    args=ap.parse_args()
    print(json.dumps(run(args.output_dir),indent=2,ensure_ascii=False))
    return 0


if __name__=="__main__":
    raise SystemExit(main())
