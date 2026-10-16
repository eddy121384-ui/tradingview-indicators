"""Fetch official Ken French daily broad-US total returns for a later volatility study.
Run: python research/fetch_french_daily_market.py
No third-party dependencies. Not part of classic_equity_baselines.mjs P&L.
"""
from __future__ import annotations

import csv
import hashlib
import io
import json
from pathlib import Path
from urllib.request import Request, urlopen
from zipfile import ZipFile

ROOT = Path(__file__).resolve().parent
URL = (
    "https://mba.tuck.dartmouth.edu/pages/faculty/Ken.French/ftp/"
    "F-F_Research_Data_Factors_daily_CSV.zip"
)
OUT = ROOT / "generated" / "classic-equity-baselines"


def main() -> None:
    req = Request(URL, headers={"User-Agent": "macro-pressure-map-research/1.0"})
    with urlopen(req, timeout=60) as response:
        payload = response.read()
    sha = hashlib.sha256(payload).hexdigest()

    with ZipFile(io.BytesIO(payload)) as zf:
        filenames = [n for n in zf.namelist() if n.lower().endswith(".csv")]
        if len(filenames) != 1:
            raise ValueError(f"Expected exactly one CSV in official ZIP: {filenames}")
        lines = zf.read(filenames[0]).decode("utf-8-sig", errors="replace").splitlines()

    dates_seen: set[str] = set()
    daily: list[tuple[str, float, float, float]] = []
    for line in lines:
        columns = next(csv.reader([line]), [])
        if len(columns) < 5:
            continue
        date = columns[0].strip()
        if len(date) != 8 or not date.isascii() or not date.isdigit():
            continue
        try:
            market_excess = float(columns[1]) / 100
            rf = float(columns[4]) / 100
        except ValueError:
            raise ValueError(f"Malformed daily factor row for {date}")
        if not (0 <= rf < .05 and -1 < market_excess + rf < 1):
            raise ValueError(f"Unexpected daily factor value on {date}")
        if date in dates_seen:
            raise ValueError(f"Duplicated official daily factor date: {date}")
        dates_seen.add(date)
        daily.append((date, market_excess + rf, market_excess, rf))
    if len(daily) < 10000 or sorted(r[0] for r in daily) != [r[0] for r in daily]:
        raise ValueError("Official daily dataset missing rows or incorrectly ordered")

    bymonth: dict[str, float] = {}
    for date, market, _, _ in daily:
        month = date[:6]
        bymonth[month] = bymonth.get(month, 1.) * (1 + market)
    input_file = ROOT / "generated" / "issue-166" / "equity-monthly-total-returns.csv"
    with input_file.open(newline="", encoding="utf-8") as f:
        monthly = {r["date"][:7].replace("-", ""): float(r["equity_tr"]) for r in csv.DictReader(f)}
    overlap = [
        (m, bymonth[m] - 1 - monthly[m])
        for m in bymonth.keys() & monthly.keys()
    ]
    if len(overlap) < 600:
        raise ValueError("Insufficient daily-monthly source overlap")
    worst = max(overlap, key=lambda r: abs(r[1]))
    mean_absolute = sum(abs(d) for _, d in overlap) / len(overlap)

    OUT.mkdir(parents=True, exist_ok=True)
    with (OUT / "daily-market-total-returns.csv").open("w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["date", "market_tr", "market_excess", "rf"])
        w.writerows(daily)
    manifest = {
        "source": URL,
        "zip_sha256": sha,
        "daily_rows": len(daily),
        "first": daily[0][0],
        "last": daily[-1][0],
        "overlap_months": len(overlap),
        "monthly_comparison_mae_pp": mean_absolute * 100,
        "monthly_comparison_max_abs_pp": abs(worst[1]) * 100,
        "worst_month": worst[0],
        "can_claim_pit": False,
        "volatility_strategy_authorized": False,
        "note": "Check daily-vs-monthly source vintages before constructing inverse-variance policy.",
    }
    (OUT / "daily-provenance.json").write_text(
        json.dumps(manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    print(json.dumps(manifest, indent=2))


if __name__ == "__main__":
    main()
