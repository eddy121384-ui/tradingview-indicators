#!/usr/bin/env node
// Independent mirror: recompute control weights and headline metrics from the
// exported monthly CSV using fresh code, and cross-check the results JSON.
import fs from "node:fs";

const CSV = "indicators/macro-pressure-map/research/generated/classic-equity-baselines/volfair-exposure-control-monthly.csv";
const JSONF = "indicators/macro-pressure-map/research/generated/classic-equity-baselines/volfair-exposure-control-results.json";
const lines = fs.readFileSync(CSV, "utf8").trim().split(/\r?\n/);
const h = lines[0].split(",");
const col = (n) => h.indexOf(n);
const rows = lines.slice(1).map((l) => {
  const c = l.split(",");
  return Object.fromEntries(h.map((k, i) => [k, c[i]]));
});
const res = JSON.parse(fs.readFileSync(JSONF, "utf8"));

let fails = 0;
const check = (ok, msg) => { if (!ok) { console.log("MISMATCH: " + msg); fails++; } };

check(rows.length === 714, "row count " + rows.length);
for (let i = 1; i < rows.length; i++) {
  const [y, m] = rows[i].date.split("-").map(Number);
  const [py, pm] = rows[i - 1].date.split("-").map(Number);
  check(y * 12 + m - (py * 12 + pm) === 1, "date gap at " + rows[i].date);
}
check(rows.at(-1).date === "2026-08" && rows[0].date === "1967-03", "panel bounds");

const wVol = rows.map((r) => Number(r.volfair));
const wVd = rows.map((r) => Number(r.vol_dh));
const wCtrl = rows.map((r) => Number(r.vol_ctrl));
const k = res.control.k;
for (let i = 0; i < rows.length; i++) {
  check(Math.abs(Math.min(1, k * wVol[i]) - wCtrl[i]) < 1e-6, "w_ctrl formula at " + rows[i].date);
  check(Math.abs(wVol[i] * Number(rows[i].s_macro) - wVd[i]) < 2e-6, "w_vd formula at " + rows[i].date);
}
const mean = (a) => a.reduce((x, y) => x + y, 0) / a.length;
check(Math.abs(mean(wCtrl) - mean(wVd)) < 1e-6, "mean exposure equality " + (mean(wCtrl) - mean(wVd)));

function metrics(weights, equity, cash, net) {
  const n = net.length;
  let W = 1, P = 1, dd = 0;
  for (const r of net) { W *= 1 + r; P = Math.max(P, W); dd = Math.min(dd, W / P - 1); }
  const mu = mean(net);
  const sd = Math.sqrt(net.reduce((a, r) => a + (r - mu) ** 2, 0) / (n - 1));
  return { cagr: W ** (12 / n) - 1, sharpe: Math.sqrt(12) * mean(net.map((r, i) => r - cash[i])) / sd, max_dd: dd, avg_equity: mean(weights) };
}
const legs = {
  VolFair: { w: wVol, net: rows.map((r) => Number(r.volfair_net_2bp)) },
  VolCtrl: { w: wCtrl, net: rows.map((r) => Number(r.volctrl_net_2bp)) },
  VolFairDH: { w: wVd, net: rows.map((r) => Number(r.voldh_net_2bp)) },
};
const equity = rows.map((r) => Number(r.equity));
const cash = rows.map((r) => Number(r.cash));
for (const [name, leg] of Object.entries(legs)) {
  const m = metrics(leg.w, equity, cash, leg.net);
  const ref = res.results[name].full;
  check(Math.abs(m.cagr - ref.cagr) < 3e-6, name + " cagr " + m.cagr + " vs " + ref.cagr);
  check(Math.abs(m.sharpe - ref.sharpe_like) < 3e-6, name + " sharpe " + m.sharpe + " vs " + ref.sharpe_like);
  check(Math.abs(m.max_dd - ref.max_dd) < 3e-6, name + " maxdd " + m.max_dd + " vs " + ref.max_dd);
  check(Math.abs(m.avg_equity - ref.avg_equity) < 1e-6, name + " avg equity");
  // Recompute net returns from weights/returns and compare to exported nets.
  let maxNetDiff = 0;
  for (let i = 0; i < rows.length; i++) {
    const to = i ? Math.abs(leg.w[i] - leg.w[i - 1]) : 0;
    const net = equity[i] * leg.w[i] + cash[i] * (1 - leg.w[i]) - 0.0002 * to;
    maxNetDiff = Math.max(maxNetDiff, Math.abs(net - leg.net[i]));
  }
  check(maxNetDiff < 2e-6, name + " exported net diff " + maxNetDiff);
}
// 10bp headline cross-check
for (const [name, leg] of Object.entries(legs)) {
  const net10 = rows.map((r) => Number(r[name === "VolFair" ? "volfair_net_10bp" : name === "VolCtrl" ? "volctrl_net_10bp" : "voldh_net_10bp"]));
  const m = metrics(leg.w, equity, cash, net10);
  const ref = res.results[name].fee10bp.full;
  check(Math.abs(m.cagr - ref.cagr) < 3e-6, name + " 10bp cagr");
  check(Math.abs(m.sharpe - ref.sharpe_like) < 3e-6, name + " 10bp sharpe");
  check(Math.abs(m.max_dd - ref.max_dd) < 3e-6, name + " 10bp maxdd");
}
console.log(fails === 0 ? "MIRROR ALL OK" : "MIRROR FAILURES: " + fails);
process.exit(fails === 0 ? 0 : 1);
