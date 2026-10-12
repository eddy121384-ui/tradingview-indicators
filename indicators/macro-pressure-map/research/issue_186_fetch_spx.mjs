#!/usr/bin/env node
// Issue #186 — S&P 500 price fetcher (input provenance, pre-prereg).
// Primary: Yahoo ^GSPC daily 1966+ -> month-end last closes (method matches
// repo NASDAQCOM precedent: daily -> month-end last close -> price return).
// Secondary: Shiller/datahub monthly averages for cross-validation only.
// Writes raw bytes + derived CSVs + provenance under generated/issue-186/.
// No event extraction, no allocation join, no lag computation here.
import fs from "node:fs";
import path from "node:path";
import crypto from "node:crypto";

const ROOT = process.cwd();
const OUT = path.join(ROOT, "indicators/macro-pressure-map/research/generated/issue-186");
fs.mkdirSync(OUT, { recursive: true });
const sha256 = (b) => crypto.createHash("sha256").update(b).digest("hex");
const sleep = (ms) => new Promise((r) => setTimeout(r, ms));

async function get(url) {
  const r = await fetch(url, { headers: { "User-Agent": "Mozilla/5.0" } });
  if (!r.ok) throw new Error(`HTTP ${r.status} ${url}`);
  return Buffer.from(await r.arrayBuffer());
}

// 1. Yahoo ^GSPC daily 1966-01-01 -> 2026-09-15 (complete months through 2026-08)
const p1 = Math.floor(Date.UTC(1966, 0, 1) / 1000);
const p2 = Math.floor(Date.UTC(2026, 8, 15) / 1000);
const yurl = `https://query1.finance.yahoo.com/v8/finance/chart/%5EGSPC?interval=1d&period1=${p1}&period2=${p2}&events=div%7Csplit`;
const yraw = await get(yurl);
fs.writeFileSync(path.join(OUT, "spx-yahoo-daily-raw.json"), yraw);
const yj = JSON.parse(yraw.toString("utf8"));
const res = yj.chart.result[0];
const ts = res.timestamp, cl = res.indicators.quote[0].close,
  op = res.indicators.quote[0].open, hi = res.indicators.quote[0].high,
  lo = res.indicators.quote[0].low, vo = res.indicators.quote[0].volume;
const adj = res.indicators.adjclose ? res.indicators.adjclose[0].adjclose : null;
const rows = [];
for (let i = 0; i < ts.length; i++) {
  const d = new Date(ts[i] * 1000).toISOString().slice(0, 10);
  rows.push({ date: d, close: cl[i], open: op[i], high: hi[i], low: lo[i], volume: vo[i], adj: adj ? adj[i] : "" });
}
rows.sort((a, b) => (a.date < b.date ? -1 : 1));
// NOTE: unadjusted closes used (price index; splits/dividends of the index itself
// are index-level by construction; ^GSPC has no splits; dividends excluded = price).
const dl = ["date,close,open,high,low,volume", ...rows.map((r) => [r.date, r.close, r.open, r.high, r.low, r.volume ?? ""].join(","))].join("\n") + "\n";
fs.writeFileSync(path.join(OUT, "spx-daily.csv"), dl);

// 2. Month-end last closes (complete calendar months only; drop incomplete 2026-09)
const byMon = new Map();
for (const r of rows) {
  if (!Number.isFinite(r.close)) continue;
  const m = r.date.slice(0, 7);
  if (!byMon.has(m) || r.date > byMon.get(m).date) byMon.set(m, r);
}
const mons = [...byMon.keys()].sort();
const mrows = mons.filter((m) => m >= "1966-01" && m <= "2026-08").map((m) => {
  const r = byMon.get(m);
  return { month: m, date: m + "-01", close_date: r.date, close: r.close };
});
fs.writeFileSync(path.join(OUT, "spx-monthly.csv"),
  "date,month,close_date,close\n" + mrows.map((r) => [r.date, r.month, r.close_date, r.close].join(",")).join("\n") + "\n");

// 3. Shiller secondary (monthly averages; validation only)
await sleep(1000);
const sraw = await get("https://datahub.io/core/s-and-p-500/r/0.csv");
fs.writeFileSync(path.join(OUT, "spx-shiller-monthly-raw.csv"), sraw);

// 4. Provenance
const prov = {
  issue: 186,
  primary: {
    provider: "Yahoo Finance (^GSPC daily, Chicago Options/GIDS)",
    url: yurl,
    method: "daily closes -> month-end last available daily close (repo NASDAQCOM precedent); unadjusted close = price index",
    raw_bytes: yraw.length,
    raw_sha256: sha256(yraw),
    daily_rows: rows.length,
    daily_first: rows[0].date,
    daily_last: rows[rows.length - 1].date,
    monthly_months: mrows.length,
    monthly_first: mrows[0].month,
    monthly_last: mrows[mrows.length - 1].month,
    firstTradeDate: res.meta.firstTradeDate,
    currency: res.meta.currency,
    exchangeName: res.meta.exchangeName,
  },
  secondary: {
    provider: "Robert Shiller / datahub.io core s-and-p-500 (monthly AVERAGES; validation only)",
    url: "https://datahub.io/core/s-and-p-500/r/0.csv",
    raw_bytes: sraw.length,
    raw_sha256: sha256(sraw),
    semantic: "monthly average of daily closes (Shiller P), NOT month-end; level/scale differs pre-1957 (Composite); used only for turning-point cross-check ±1mo",
  },
  fetched_at: new Date().toISOString(),
};
fs.writeFileSync(path.join(OUT, "spx-provenance.json"), JSON.stringify(prov, null, 2) + "\n");
console.log("daily", rows.length, rows[0].date, "->", rows[rows.length - 1].date);
console.log("monthly", mrows.length, mrows[0].month, "->", mrows[mrows.length - 1].month);
// continuity: every calendar month 1966-01..2026-08 present?
const exp = [];
for (let y = 1966; y <= 2026; y++) for (let m = 1; m <= 12; m++) {
  const k = String(y).padStart(4, "0") + "-" + String(m).padStart(2, "0");
  if (k > "2026-08") break;
  exp.push(k);
}
const have = new Set(mrows.map((r) => r.month));
console.log("expected", exp.length, "missing", exp.filter((m) => !have.has(m)).length, exp.filter((m) => !have.has(m)).slice(0, 10));
