#!/usr/bin/env python3
"""Issue #151 Phase A — SPF 10Y CPI source freeze only.

No exact V6.6 signal and no asset-return outcome is loaded.

The quarterly SPF forecast becomes available only after the Philadelphia Fed's
official public release date. The normalized monthly series is a causal
last-observation-carried-forward step function at completed month end.
"""
from __future__ import annotations

import argparse
import hashlib
import io
import json
import re
import time
from pathlib import Path

import pandas as pd
import requests

INFLATION_URL = (
    "https://www.philadelphiafed.org/-/media/FRBP/Assets/Surveys-And-Data/"
    "survey-of-professional-forecasters/historical-data/Inflation.xlsx"
)
RELEASE_DATES_URL = (
    "https://www.philadelphiafed.org/-/media/frbp/assets/surveys-and-data/"
    "survey-of-professional-forecasters/spf-release-dates.txt"
)

UA = "tradingview-indicators-research/issue-151"


def sha256_bytes(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def fetch(url: str, attempts: int = 4) -> bytes:
    last: Exception | None = None
    for i in range(attempts):
        try:
            r = requests.get(url, headers={"User-Agent": UA}, timeout=(15, 60))
            r.raise_for_status()
            return r.content
        except Exception as exc:
            last = exc
            if i + 1 < attempts:
                time.sleep(2 ** i)
    raise RuntimeError(f"failed to fetch {url}: {last}")


def norm(x: object) -> str:
    return re.sub(r"\s+", "", str(x)).upper()


def parse_inflation_xlsx(raw: bytes) -> tuple[pd.DataFrame, dict]:
    xls = pd.ExcelFile(io.BytesIO(raw))
    matches = []
    inventory = {}
    for sheet in xls.sheet_names:
        df = pd.read_excel(io.BytesIO(raw), sheet_name=sheet)
        inventory[sheet] = [str(c) for c in df.columns]
        cmap = {norm(c): c for c in df.columns}
        targets = [k for k in cmap if k in {"INFCPI10YR", "CPI10"}]
        if targets:
            matches.append((sheet, df, cmap, targets))

    if len(matches) != 1:
        raise RuntimeError(
            f"expected one SPF inflation sheet with INFCPI10YR/CPI10; "
            f"matches={[(m[0],m[3]) for m in matches]}, inventory={inventory}"
        )

    sheet, df, cmap, targets = matches[0]
    target_key = "INFCPI10YR" if "INFCPI10YR" in cmap else "CPI10"
    target_col = cmap[target_key]

    year_keys = [k for k in cmap if k in {"YEAR", "YR"}]
    q_keys = [k for k in cmap if k in {"QUARTER", "QTR", "QUART"}]
    if len(year_keys) != 1 or len(q_keys) != 1:
        raise RuntimeError(
            f"cannot identify YEAR/QUARTER columns on {sheet}; columns={list(df.columns)}"
        )
    year_col = cmap[year_keys[0]]
    q_col = cmap[q_keys[0]]

    out = df[[year_col, q_col, target_col]].copy()
    out.columns = ["year", "quarter", "spf10"]
    out["year"] = pd.to_numeric(out["year"], errors="coerce")
    out["quarter"] = (
        out["quarter"].astype(str)
        .str.upper()
        .str.replace("Q", "", regex=False)
        .str.strip()
    )
    out["quarter"] = pd.to_numeric(out["quarter"], errors="coerce")
    out["spf10"] = pd.to_numeric(out["spf10"], errors="coerce")
    out = out.loc[
        out["year"].notna()
        & out["quarter"].isin([1, 2, 3, 4])
        & out["spf10"].notna()
    ].copy()
    out["year"] = out["year"].astype(int)
    out["quarter"] = out["quarter"].astype(int)
    out["survey"] = out["year"].astype(str) + ":Q" + out["quarter"].astype(str)
    if out["survey"].duplicated().any():
        raise RuntimeError("duplicate SPF survey observation")
    out = out.sort_values(["year", "quarter"]).reset_index(drop=True)

    meta = {
        "sheet": sheet,
        "year_column": str(year_col),
        "quarter_column": str(q_col),
        "target_column": str(target_col),
        "rows": int(len(out)),
        "first_survey": out["survey"].iloc[0] if len(out) else None,
        "last_survey": out["survey"].iloc[-1] if len(out) else None,
        "column_inventory": inventory,
    }
    return out, meta


DATE_RE = re.compile(r"\b\d{1,2}/\d{1,2}/(?:\d{2}|\d{4})\b")
SURVEY_RE = re.compile(r"\b(19\d{2}|20\d{2})\s*[:\-]?\s*Q?([1-4])\b", re.I)


def parse_date_token(s: str) -> pd.Timestamp:
    # pandas interprets 2-digit years with dateutil conventions; explicitly
    # normalize the SPF range to 1900/2000 for deterministic behavior.
    m = re.fullmatch(r"(\d{1,2})/(\d{1,2})/(\d{2}|\d{4})", s)
    if not m:
        raise ValueError(s)
    mm, dd, yy = m.groups()
    y = int(yy)
    if len(yy) == 2:
        y = 2000 + y if y <= 69 else 1900 + y
    return pd.Timestamp(year=y, month=int(mm), day=int(dd))


def parse_release_dates(raw: bytes) -> tuple[pd.DataFrame, dict]:
    text = raw.decode("utf-8", errors="replace")
    rows = []
    for line in text.splitlines():
        sm = SURVEY_RE.search(line)
        if not sm:
            continue
        year = int(sm.group(1))
        quarter = int(sm.group(2))
        date_tokens = DATE_RE.findall(line)
        if not date_tokens:
            continue
        # Official file contains deadline/publication timing. The last date on
        # the survey line is the public release date.
        dates = [parse_date_token(x) for x in date_tokens]
        rows.append({
            "year": year,
            "quarter": quarter,
            "survey": f"{year}:Q{quarter}",
            "release_date": dates[-1],
            "date_tokens": "|".join(date_tokens),
            "source_line": line.strip(),
        })

    df = pd.DataFrame(rows)
    if df.empty:
        raise RuntimeError(
            "release-date parser produced zero rows; "
            f"head={text.splitlines()[:40]}"
        )
    df = df.sort_values(["year", "quarter"]).drop_duplicates(
        "survey", keep="last"
    ).reset_index(drop=True)

    # Historical release-date coverage should begin by 1990:Q3.
    if not (df["survey"] == "1990:Q3").any():
        raise RuntimeError(
            "official release-date file did not yield 1990:Q3; "
            f"first={df['survey'].head(10).tolist()}"
        )
    if (df["release_date"].dt.year < df["year"]).any():
        raise RuntimeError("release-date year precedes survey year")

    meta = {
        "rows": int(len(df)),
        "first_survey": df["survey"].iloc[0],
        "last_survey": df["survey"].iloc[-1],
        "first_release_date": df["release_date"].min().date().isoformat(),
        "last_release_date": df["release_date"].max().date().isoformat(),
        "text_head": text.splitlines()[:25],
    }
    return df, meta


def build_causal_monthly(
    surveys: pd.DataFrame, releases: pd.DataFrame
) -> tuple[pd.DataFrame, dict]:
    merged = surveys.merge(
        releases[["survey", "release_date"]],
        on="survey",
        how="left",
        validate="one_to_one",
    )

    usable = merged.loc[
        merged["spf10"].notna() & merged["release_date"].notna()
    ].copy()
    if usable.empty:
        raise RuntimeError("no SPF observations have both value and release date")
    usable = usable.sort_values("release_date").reset_index(drop=True)

    # Fail closed if a survey with a target value in the intended modern bridge
    # range has no public release date.
    modern_missing = merged.loc[
        merged["year"].ge(1991)
        & merged["spf10"].notna()
        & merged["release_date"].isna(),
        "survey",
    ].tolist()
    if modern_missing:
        raise RuntimeError(
            f"SPF target surveys missing official release dates: {modern_missing[:20]}"
        )

    start = usable["release_date"].min().to_period("M")
    end = usable["release_date"].max().to_period("M")
    months = pd.period_range(start, end, freq="M")
    month_end = months.to_timestamp("M")

    release_view = usable[["release_date", "spf10", "survey"]].sort_values(
        "release_date"
    )
    monthly = pd.DataFrame({"period": months, "month_end": month_end})
    monthly = pd.merge_asof(
        monthly.sort_values("month_end"),
        release_view,
        left_on="month_end",
        right_on="release_date",
        direction="backward",
        allow_exact_matches=True,
    )
    monthly = monthly.loc[monthly["spf10"].notna()].copy()
    monthly["date"] = monthly["period"].dt.to_timestamp("M")

    # Availability sanity: the carried survey must already have been public.
    if (monthly["release_date"] > monthly["month_end"]).any():
        raise RuntimeError("causal SPF monthly series used a future release")

    meta = {
        "first_month": str(monthly["period"].min()),
        "last_month": str(monthly["period"].max()),
        "rows": int(len(monthly)),
        "source_surveys_used": int(monthly["survey"].nunique()),
        "first_source_survey": monthly["survey"].iloc[0],
        "last_source_survey": monthly["survey"].iloc[-1],
    }
    return monthly.reset_index(drop=True), meta


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--output-dir", type=Path, required=True)
    args = ap.parse_args()
    outdir = args.output_dir
    outdir.mkdir(parents=True, exist_ok=True)

    inflation_raw = fetch(INFLATION_URL)
    release_raw = fetch(RELEASE_DATES_URL)

    surveys, inflation_meta = parse_inflation_xlsx(inflation_raw)
    releases, release_meta = parse_release_dates(release_raw)
    monthly, monthly_meta = build_causal_monthly(surveys, releases)

    survey_path = outdir / "issue-151-spf10-surveys.csv"
    release_path = outdir / "issue-151-spf-release-dates.csv"
    monthly_path = outdir / "issue-151-spf10-causal-monthly.csv"

    surveys.to_csv(survey_path, index=False, float_format="%.12g")
    releases.to_csv(release_path, index=False, date_format="%Y-%m-%d")
    monthly[["date", "spf10", "survey", "release_date"]].to_csv(
        monthly_path, index=False, date_format="%Y-%m-%d", float_format="%.12g"
    )

    manifest = {
        "schema_version": 1,
        "issue": 151,
        "phase": "A-source-only",
        "exact_v66_signal_loaded": False,
        "outcome_data_loaded": False,
        "inflation_workbook": {
            "url": INFLATION_URL,
            "raw_sha256": sha256_bytes(inflation_raw),
            **inflation_meta,
        },
        "release_dates": {
            "url": RELEASE_DATES_URL,
            "raw_sha256": sha256_bytes(release_raw),
            **release_meta,
        },
        "monthly_rule": (
            "At each completed calendar month end, use the latest SPF 10Y CPI "
            "median forecast whose official public release_date is <= month_end; "
            "carry forward until the next release; no interpolation."
        ),
        "causal_monthly": {
            **monthly_meta,
            "normalized_csv_sha256": sha256_bytes(monthly_path.read_bytes()),
        },
        "files": {
            "survey_csv_sha256": sha256_bytes(survey_path.read_bytes()),
            "release_csv_sha256": sha256_bytes(release_path.read_bytes()),
        },
        "guardrail": (
            "SPF source freeze only. No exact V6.6 signal and no asset-return "
            "outcome loaded."
        ),
    }
    (outdir / "issue-151-source-manifest.json").write_text(
        json.dumps(manifest, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(manifest, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
