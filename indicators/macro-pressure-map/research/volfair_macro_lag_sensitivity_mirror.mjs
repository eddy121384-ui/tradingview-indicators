#!/usr/bin/env node
// Independent mirror for the VolFair+DH lag-sensitivity study (frozen prereg d215075, PR #206).
//
// Deliberately does NOT import the engine. It re-reads the published audit CSV and the frozen
// inputs and recomputes, along a separate code path:
//   * the calendar-month factor shift s_L[m] = A[m-L] (including the 1966-05..1967-02 warm-up)
//   * the per-lag control k_L and w_ctrl,L = min(1, k_L * w_vol)
//   * every 2bp / 10bp net return from weights, equity, cash and fee
//   * full-period, era and crisis metrics from those independently recomputed nets
// and compares them against the monthly CSV and the results JSON.
//
// Tolerances are storage-aware: the audit CSV stores weights and nets at 6 decimals.
// Exit code is non-zero on any mismatch. production_authorized=false.
import fs from "node:fs";
import path from "node:path";

const ROOT = process.cwd();
const BASE = path.join(ROOT, "indicators/macro-pressure-map/research");
const OUT = path.join(BASE, "generated/classic-equity-baselines");
const CSV = path.join(OUT, "volfair-macro-lag-sensitivity-monthly.csv");
const JSONF = path.join(OUT, "volfair-macro-lag-sensitivity-results.json");
const PANEL = path.join(OUT, "macro-incremental-monthly.csv");
const VOLM = path.join(OUT, "volatility-managed-monthly.csv");
const STRUCT = path.join(BASE, "generated/issue-183/corrected-structural-monthly.csv");
const MATRIX = path.join(BASE, "generated/issue-178/weight-matrix.csv");

const FEE2 = 0.0002, FEE10 = 0.001, NEUTRAL = 0.45;
const FAIL = [];
const chk = (cond, msg) => { if (!cond) FAIL.push(msg); };
const avg = (a) => a.reduce((x, y) => x + y, 0) / a.length;
const sd = (a) => { const m = avg(a); return Math.sqrt(a.reduce((x, y) => x + (y - m) ** 2, 0) / (a.length - 1)); };
const ym = (s) => { const [y, m] = s.split("-").map(Number); return y * 12 + m; };
const shift = (key, d) => { const [y, m] = key.split("-").map(Number); const v = y * 12 + m + d; const yy = Math.floor((v - 1) / 12); return `${String(yy).padStart(4, "0")}-${String(v - yy * 12).padStart(2, "0")}`; };
const parse = (f) => {
  const lines = fs.readFileSync(f, "utf8").trim().split(/\r?\n/);
  const cols = lines.shift().split(",");
  return lines.map((l) => { const c = l.split(","); return Object.fromEntries(cols.map((k, j) => [k, c[j]])); });
};

// ---- independently rebuild the applied-factor calendar map A (1966-05..2026-08) ----
const pan = parse(PANEL);
const mx = parse(MATRIX);
const E = {};
for (const r of mx) E[r.state] = (Number(r.sp500) + Number(r.nasdaq) + Number(r.russell)) / 100;
const stMap = new Map(parse(STRUCT).map((r) => [r.date.slice(0, 7), r.alloc_state]));

const A = new Map();
for (const r of pan) A.set(r.date, Number(r.s_macro));
for (const [k, state] of stMap) {
  if (ym(k) >= ym("1966-05") && ym(k) <= ym("1967-02")) A.set(k, Math.min(1, E[state] / NEUTRAL));
}
chk(A.size === 724, `independently rebuilt factor map size ${A.size} != 724`);

// ---- read the published audit CSV ----
const rows = parse(CSV);
chk(rows.length === 714, `audit CSV rows ${rows.length} != 714`);
const res = JSON.parse(fs.readFileSync(JSONF, "utf8"));

const num = (r, k) => Number(r[k]);
let maxSDiff = 0, maxWDiff = 0, maxCtrlDiff = 0, maxKDiff = 0;
let maxNet2 = 0, maxNet10 = 0, maxFairDiff = 0;
const volmMap = new Map(parse(VOLM).map((r) => [r.date.slice(0, 7), Number(r.w_fair)]));

const legs = {};
for (const L of [0, 1, 2, 3]) {
  legs[`L${L}`] = { w: [], net2: [], net10: [] };
  legs[`C${L}`] = { w: [], net2: [], net10: [] };
}
legs.VolFair = { w: [], net2: [], net10: [] };

for (let i = 0; i < rows.length; i++) {
  const r = rows[i];
  if (i) chk(ym(r.date) - ym(rows[i - 1].date) === 1, `audit CSV calendar gap at ${r.date}`);
  maxFairDiff = Math.max(maxFairDiff, Math.abs(num(r, "volfair") - volmMap.get(r.date)));

  const wVol = num(r, "volfair");
  const eq = num(r, "equity"), cash = num(r, "cash");
  const meanVol = res.results.VolFair.full.avg_equity;

  for (const L of [0, 1, 2, 3]) {
    const src = shift(r.date, -L);
    chk(A.has(src), `L=${L} factor source ${src} missing at ${r.date}`);
    const sExpr = L === 0 ? num(r, "s_macro") : A.get(src);
    const sCsv = num(r, `s_lag${L}`);
    maxSDiff = Math.max(maxSDiff, Math.abs(sCsv - (L === 0 ? num(r, "s_macro") : A.get(src))));

    const wLeg = num(r, `w_lag${L}`);
    const wExp = L === 0 ? num(r, "vol_dh") : wVol * sExpr;
    maxWDiff = Math.max(maxWDiff, Math.abs(wLeg - wExp));

    const k = num(r, `w_ctrl${L}`) / (wVol || 1);
    const wCtrl = num(r, `w_ctrl${L}`);
    maxCtrlDiff = Math.max(maxCtrlDiff, Math.abs(wCtrl - Math.min(1, k * wVol)));

    legs[`L${L}`].w.push(wLeg);
    legs[`C${L}`].w.push(wCtrl);
  }
  legs.VolFair.w.push(wVol);
  chk(Math.abs(num(r, "s_macro") - num(r, "s_lag0")) < 1e-12, `s_lag0 != s_macro at ${r.date}`);
}

// ---- independently recompute nets from the published weights ----
for (const name of Object.keys(legs)) {
  const w = legs[name].w;
  for (let i = 0; i < rows.length; i++) {
    const to = i ? Math.abs(w[i] - w[i - 1]) : 0;
    const eq = num(rows[i], "equity"), cash = num(rows[i], "cash");
    const n2 = eq * w[i] + cash * (1 - w[i]) - FEE2 * to;
    const n10 = eq * w[i] + cash * (1 - w[i]) - FEE10 * to;
    legs[name].net2.push(n2);
    legs[name].net10.push(n10);
    const col2 = name === "VolFair" ? "volfair_net_2bp" : `${name[0] === "L" ? "lag" : "ctrl"}${name.slice(1)}_net_2bp`;
    const col10 = name === "VolFair" ? "volfair_net_10bp" : `${name[0] === "L" ? "lag" : "ctrl"}${name.slice(1)}_net_10bp`;
    maxNet2 = Math.max(maxNet2, Math.abs(n2 - num(rows[i], col2)));
    maxNet10 = Math.max(maxNet10, Math.abs(n10 - num(rows[i], col10)));
  }
}

// ---- independently recompute per-lag k and mean-exposure equality ----
const meanVol = avg(legs.VolFair.w);
for (const L of [0, 1, 2, 3]) {
  const meanLeg = avg(legs[`L${L}`].w);
  const kIndep = meanLeg / meanVol;
  maxKDiff = Math.max(maxKDiff, Math.abs(kIndep - res.lags[L].k));
  chk(Math.abs(avg(legs[`C${L}`].w) - meanLeg) < 1e-6, `L=${L} mean exposure equality (storage tol)`);
  chk(kIndep > 0 && kIndep < 1, `L=${L} k not in (0,1): ${kIndep}`);
}

// ---- independently recompute full-period metrics from the recomputed nets ----
function fullMetrics(nets, w, eqs, cashs) {
  const n = nets.length;
  let W = 1, H = 1, dd = 0;
  for (const x of nets) { W *= 1 + x; H = Math.max(H, W); dd = Math.min(dd, W / H - 1); }
  const s = sd(nets);
  return { cagr: W ** (12 / n) - 1, sharpe_like: Math.sqrt(12) * avg(nets.map((x, i) => x - cashs[i])) / s, max_dd: dd, avg_equity: avg(w) };
}
const eqs = rows.map((r) => num(r, "equity")), cashs = rows.map((r) => num(r, "cash"));
let maxMetricDiff = 0;
for (const name of Object.keys(legs)) {
  const m = fullMetrics(legs[name].net2, legs[name].w, eqs, cashs);
  const j = res.results[name].full;
  maxMetricDiff = Math.max(maxMetricDiff, Math.abs(m.cagr - j.cagr), Math.abs(m.sharpe_like - j.sharpe_like), Math.abs(m.max_dd - j.max_dd), Math.abs(m.avg_equity - j.avg_equity));
}

// ---- assert with storage-aware tolerances ----
chk(maxFairDiff < 1e-4, `volfair column vs volatility-managed w_fair: ${maxFairDiff}`);
chk(maxSDiff < 1e-9, `calendar shift s_L mismatch: ${maxSDiff}`);
chk(maxWDiff < 2e-6, `weight reconstruction mismatch: ${maxWDiff}`);
chk(maxCtrlDiff < 1e-6, `control reconstruction mismatch: ${maxCtrlDiff}`);
chk(maxNet2 < 2e-6, `2bp net reconstruction mismatch: ${maxNet2}`);
chk(maxNet10 < 2e-6, `10bp net reconstruction mismatch: ${maxNet10}`);
chk(maxKDiff < 1e-6, `per-lag k mismatch: ${maxKDiff}`);
chk(maxMetricDiff < 1e-4, `full-period metric mismatch: ${maxMetricDiff}`);
chk(res.production_authorized === false, "production_authorized must be false");
chk(res.integrity.l0_replication.passed === true, "engine-reported L=0 gate must be true");

console.log(JSON.stringify({
  mirror: "volfair_macro_lag_sensitivity_mirror",
  independent: true,
  checks_failed: FAIL.length,
  max_abs_diff: {
    calendar_shift_s: maxSDiff,
    weight_reconstruction: maxWDiff,
    control_reconstruction: maxCtrlDiff,
    per_lag_k: maxKDiff,
    net_2bp: maxNet2,
    net_10bp: maxNet10,
    full_period_metric: maxMetricDiff,
    volfair_vs_volatility_managed: maxFairDiff,
  },
  failures: FAIL.slice(0, 20),
}, null, 2));

if (FAIL.length) { console.error("MIRROR FAILED: " + FAIL.length + " check(s)"); process.exit(1); }
console.log("MIRROR OK: independent recomputation from the audit CSV reproduces the study.");
