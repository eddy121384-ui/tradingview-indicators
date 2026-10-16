#!/usr/bin/env node
// Independent mirror: recompute headline metrics from macro-incremental-monthly.csv
// using fresh code (no shared functions with the backtest engine).
import fs from "node:fs";
const monthly = fs.readFileSync("indicators/macro-pressure-map/research/generated/classic-equity-baselines/macro-incremental-monthly.csv", "utf8").trim().split("\n");
const res = JSON.parse(fs.readFileSync("indicators/macro-pressure-map/research/generated/classic-equity-baselines/macro-incremental-results.json", "utf8"));
const head = monthly[0].split(",");
const idx = (c) => head.indexOf(c);
const cols = { sma_dh_net: "sma_dh_net", mom_dh_net: "mom_dh_net", vol_dh_net: "vol_dh_net", sma_net: "sma_net", vol_net: "vol_net", dh_net: "dh_net" };
let fails = 0;
for (const [key, col] of Object.entries(cols)) {
  const rets = monthly.slice(1).map((l) => parseFloat(l.split(",")[idx(col)]));
  const n = rets.length;
  let W = 1, P = 1, dd = 0;
  for (const r of rets) { W *= 1 + r; if (W > P) P = W; const d = W / P - 1; if (d < dd) dd = d; }
  const cagr = Math.pow(W, 12 / n) - 1;
  const mean = rets.reduce((a, b) => a + b, 0) / n;
  const sd = Math.sqrt(rets.reduce((a, b) => a + (b - mean) ** 2, 0) / (n - 1));
  const legMap = { sma_dh_net: "SMA_DH", mom_dh_net: "MOM_DH", vol_dh_net: "VOL_DH", sma_net: "SMA", vol_net: "VOL", dh_net: "DH" };
  const ref = res.results[legMap[key]].full;
  const dc = Math.abs(cagr - ref.cagr), ddif = Math.abs(dd - ref.max_dd);
  const okC = dc < 2e-6, okD = ddif < 2e-6; // CSV stores nets at 6 decimals; allow rounding accumulation
  console.log(key, "n=" + n, "cagr " + cagr.toFixed(6) + " ref " + ref.cagr.toFixed(6), okC ? "OK" : "MISMATCH", "| dd " + dd.toFixed(6) + " ref " + ref.max_dd.toFixed(6), okD ? "OK" : "MISMATCH");
  if (!okC || !okD) fails++;
}
// timing/ordering checks from CSV
const dIdx = idx("date"), sIdx = idx("signal_month"), stIdx = idx("stale");
let nStale = 0; const staleMonths = [];
for (let i = 1; i < monthly.length; i++) {
  const c = monthly[i].split(",");
  if (c[stIdx] === "1") { nStale++; staleMonths.push(c[dIdx]); }
  const wAug = parseFloat(c[idx("sma_dh")]), wBase = parseFloat(c[idx("sma10")]);
  if (!(wAug <= wBase + 1e-9)) { console.log("W_AUG>W_BASE at " + c[dIdx]); fails++; break; }
}
console.log("stale months:", nStale, staleMonths.join(","));
if (nStale !== 3) { console.log("STALE COUNT MISMATCH"); fails++; }
console.log(fails === 0 ? "MIRROR ALL OK" : "MIRROR FAILURES: " + fails);
process.exit(fails === 0 ? 0 : 1);
