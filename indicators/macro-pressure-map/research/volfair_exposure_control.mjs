#!/usr/bin/env node
// VolFair-specific exposure control — execution per frozen prereg 802f674.
// Control: w_ctrl = min(1, k*w_vol), k = mean_714(w_vol+DH)/mean_714(w_vol).
// Descriptive hindsight counterfactual, NOT tradable. production_authorized=false.
import fs from "node:fs";
import path from "node:path";
import crypto from "node:crypto";
import { fileURLToPath } from "node:url";

const HERE = path.dirname(fileURLToPath(import.meta.url));
const RES = HERE;
const PANEL = path.join(RES, "generated/classic-equity-baselines/macro-incremental-monthly.csv");
const VOLM = path.join(RES, "generated/classic-equity-baselines/volatility-managed-monthly.csv");
const DAILY = path.join(RES, "generated/classic-equity-baselines/daily-market-total-returns.csv");
const EQ = path.join(RES, "generated/issue-166/equity-monthly-total-returns.csv");
const CASH = path.join(RES, "generated/issue-174/nine-sleeve-monthly-returns.csv");
const MATRIX = path.join(RES, "generated/issue-178/weight-matrix.csv");
const STRUCT = path.join(RES, "generated/issue-183/corrected-structural-monthly.csv");
const OUT = path.join(RES, "generated/classic-equity-baselines");
const FEE = 0.0002, FEE10 = 0.001;
const NEUTRAL = 0.45;

const assert = (ok, msg) => { if (!ok) throw new Error("BLOCKED: " + msg); };
const ym = (s) => { const [y, m] = s.slice(0, 7).split("-").map(Number); return y * 12 + m; };
const avg = (a) => a.reduce((x, y) => x + y, 0) / a.length;
const sd = (a) => { const m = avg(a); return Math.sqrt(a.reduce((x, y) => x + (y - m) ** 2, 0) / (a.length - 1)); };
const parse = (f) => {
  const lines = fs.readFileSync(f, "utf8").trim().split(/\r?\n/);
  const cols = lines.shift().split(",");
  return { cols, rows: lines.map((l) => Object.fromEntries(l.split(",").map((v, j) => [cols[j], v]))) };
};

// ---- 1. Frozen panel and returns ----
const pan = parse(PANEL);
assert(pan.rows.length === 714, "panel != 714");
pan.rows.forEach((r, i) => {
  if (i) assert(ym(r.date) - ym(pan.rows[i - 1].date) === 1, "panel gap at " + r.date);
});
assert(pan.rows[0].date === "1967-03" && pan.rows.at(-1).date === "2026-08", "panel bounds");
for (const r of pan.rows) {
  const e = Number(r.equity), c = Number(r.cash);
  assert(Number.isFinite(e) && e > -1 && Number.isFinite(c) && c > -1, "bad return " + r.date);
}
// Cross-check panel returns against the original frozen inputs.
const eqMap = new Map(parse(EQ).rows.map((r) => [r.date.slice(0, 7), Number(r.equity_tr)]));
const cashMap = new Map(parse(CASH).rows.map((r) => [r.date.slice(0, 7), Number(r.cash)]));
let maxEqDiff = 0, maxCashDiff = 0;
for (const r of pan.rows) {
  assert(eqMap.has(r.date) && cashMap.has(r.date), "source return missing " + r.date);
  maxEqDiff = Math.max(maxEqDiff, Math.abs(eqMap.get(r.date) - Number(r.equity)));
  maxCashDiff = Math.max(maxCashDiff, Math.abs(cashMap.get(r.date) - Number(r.cash)));
}
assert(maxEqDiff < 1e-12 && maxCashDiff < 1e-12, "panel returns differ from frozen sources");

// ---- 2. Matrix / structural timeline checks ----
const mx = parse(MATRIX);
assert(mx.rows.length === 9, "matrix rows != 9");
const E = {};
for (const r of mx.rows) {
  const sum = ["sp500","nasdaq","russell","treasury2y","treasury10y","longtreasury","gold","oil","cash"]
    .map((k) => Number(r[k])).reduce((a, b) => a + b, 0);
  assert(Math.abs(sum - 100) < 1e-9, "matrix row != 100 " + r.state);
  E[r.state] = (Number(r.sp500) + Number(r.nasdaq) + Number(r.russell)) / 100;
}
assert(Math.abs(E["G_Neutral/I_Neutral"] - NEUTRAL) < 1e-12, "neutral anchor != 0.45");
const st = parse(STRUCT);
const stMap = new Map(st.rows.map((r) => [r.date.slice(0, 7), r.alloc_state]));
assert(st.rows.length === 721, "struct rows != 721");

// ---- 3. Recompute VolFair from daily factors (integrity) ----
const byM = new Map();
for (const l of fs.readFileSync(DAILY, "utf8").trim().split("\n").slice(1)) {
  const c = l.split(",");
  const m = c[0].slice(0, 6), ex = parseFloat(c[2]);
  assert(Number.isFinite(ex), "daily excess " + c[0]);
  if (!byM.has(m)) byM.set(m, []);
  byM.get(m).push(ex);
}
const months = [...byM.keys()].sort();
const rv = new Map();
for (const m of months) {
  const d = byM.get(m), mu = avg(d);
  const v = d.reduce((a, x) => a + (x - mu) ** 2, 0) / 22;
  assert(v > 0, "RV<=0 " + m);
  rv.set(m, v);
}
const panelM = months.filter((m) => m >= "196703" && m <= "202608");
assert(panelM.length === 714, "daily panel months != 714");
const prevM = (m) => { const y = +m.slice(0, 4), mo = +m.slice(4, 6) - 1; return mo < 1 ? (y - 1) + "12" : y + String(mo).padStart(2, "0"); };
const seen = months.filter((m) => m < "196703").map((m) => rv.get(m));
const wFair = [];
for (const m of panelM) {
  const vbar = avg(seen);
  wFair.push(Math.min(1, Math.max(0, vbar / rv.get(prevM(m)))));
  seen.push(rv.get(m));
}
const volm = parse(VOLM);
assert(volm.rows.length === 714, "vol monthly != 714");
let maxFairDiff = 0;
volm.rows.forEach((r, i) => {
  assert(r.date.slice(0, 7).replace("-", "") === panelM[i], "vol date " + r.date);
  maxFairDiff = Math.max(maxFairDiff, Math.abs(Number(r.w_fair) - wFair[i]));
});
assert(maxFairDiff < 1e-4, "VolFair recompute mismatch " + maxFairDiff);

// ---- 4. Frozen weight series and rule reconstruction ----
const wVol = pan.rows.map((r) => Number(r.volfair));
const wVd = pan.rows.map((r) => Number(r.vol_dh));
const sMacro = pan.rows.map((r) => Number(r.s_macro));
const stale = pan.rows.map((r) => Number(r.stale));
const eDh = pan.rows.map((r) => Number(r.E_DH));
let maxVdDiff = 0, maxSDiff = 0, maxEDhDiff = 0;
pan.rows.forEach((r, i) => {
  maxVdDiff = Math.max(maxVdDiff, Math.abs(wVol[i] * sMacro[i] - wVd[i]));
  if (stMap.has(r.date)) {
    const e = E[stMap.get(r.date)];
    assert(e !== undefined, "unknown state " + r.date);
    maxEDhDiff = Math.max(maxEDhDiff, Math.abs(e - eDh[i]));
    maxSDiff = Math.max(maxSDiff, Math.abs(Math.min(1, e / NEUTRAL) - sMacro[i]));
  }
});
// Weight columns are stored at 6 decimals, so a product of two rounded columns
// can differ from the rounded product by up to ~1.5e-6; use a storage-aware tolerance.
assert(maxVdDiff < 2e-6, "w_vd != w_vol*s " + maxVdDiff);
assert(maxSDiff < 2e-6, "s_macro != min(1,E_DH/0.45) " + maxSDiff);
assert(maxEDhDiff < 5e-5, "E_DH != matrix equity " + maxEDhDiff);
const staleIdx = stale.map((v, i) => (v === 1 ? i : -1)).filter((i) => i >= 0);
assert(staleIdx.length === 3, "stale months != 3");
assert(staleIdx.map((i) => pan.rows[i].date).join(",") === "2025-10,2025-11,2026-01", "stale month identity");
for (const i of staleIdx) {
  assert(Math.abs(sMacro[i] - 1) < 1e-12, "stale s != 1 at " + pan.rows[i].date);
  assert(Math.abs(wVd[i] - wVol[i]) < 2e-6, "stale w_vd != w_vol at " + pan.rows[i].date);
}

// ---- 5. Control leg: one scalar, full-sample exposure match ----
const meanVol = avg(wVol), meanVd = avg(wVd);
const k = meanVd / meanVol;
assert(k > 0 && k < 1, "k outside (0,1): " + k);
const wCtrl = wVol.map((w) => Math.min(1, k * w));
const capBind = wCtrl.filter((w, i) => k * wVol[i] > 1).length;
assert(capBind === 0, "cap binds in " + capBind + " months");
const meanCtrl = avg(wCtrl);
assert(Math.abs(meanCtrl - meanVd) < 1e-9, "mean exposure mismatch " + (meanCtrl - meanVd));
for (let i = 0; i < wCtrl.length; i++) assert(wCtrl[i] <= wVol[i] + 1e-15, "w_ctrl > w_vol");

// ---- 6. Backtest ----
function run(w, fee) {
  return pan.rows.map((r, i) => {
    const to = i ? Math.abs(w[i] - w[i - 1]) : 0;
    const e = Number(r.equity), c = Number(r.cash);
    return { date: r.date, weight: w[i], equity: e, cash: c, turnover: to,
      net: e * w[i] + c * (1 - w[i]) - fee * to };
  });
}
function metrics(rs) {
  const n = rs.length, rets = rs.map((x) => x.net), mu = avg(rets), s = sd(rets);
  let W = 1, H = 1, dd = 0, worst = Infinity, to = 0, sw = 0;
  let upN = 0, dnN = 0, up = 0, dn = 0, miss = 0, avd = 0;
  for (const x of rs) {
    W *= 1 + x.net; H = Math.max(H, W); dd = Math.min(dd, W / H - 1);
    worst = Math.min(worst, x.net); to += x.turnover;
    if (x.turnover > 0) sw++;
    if (x.equity > 0) { upN++; up += x.weight; }
    if (x.equity < 0) { dnN++; dn += x.weight; }
    if (x.equity > 0 && x.equity > x.cash) miss += (1 - x.weight) * (x.equity - x.cash);
    if (x.equity < 0 && x.equity < x.cash) avd += (1 - x.weight) * (x.cash - x.equity);
  }
  return { n, first: rs[0].date, last: rs.at(-1).date,
    cagr: W ** (12 / n) - 1, vol: s * Math.sqrt(12),
    sharpe_like: s ? Math.sqrt(12) * avg(rs.map((x) => x.net - x.cash)) / s : null,
    max_dd: dd, worst_month: worst, avg_equity: avg(rs.map((x) => x.weight)),
    turnover_annual: to * 12 / n, switches: sw,
    part_up: upN ? up / upN : null, part_dn: dnN ? dn / dnN : null,
    missed_pp: miss * 100, avoided_pp: avd * 100, terminal: W };
}
const eras = { E1: ["1967-03", "1979-12"], E2: ["1980-01", "1999-12"], E3: ["2000-01", "2019-12"], E4: ["2020-01", "2026-08"] };
const crises = { "1973-74": ["1973-01", "1974-12"], "1987": ["1987-08", "1987-12"], "2000-02": ["2000-03", "2002-10"], "2007-09": ["2007-10", "2009-03"], "2020": ["2020-02", "2020-04"], "2022": ["2022-01", "2022-12"] };
const sel = (a, lo, hi) => a.filter((x) => ym(x.date) >= ym(lo) && ym(x.date) <= ym(hi));
const legs = { VolFair: wVol, VolCtrl: wCtrl, VolFairDH: wVd };
const sims = {}, sims10 = {}, results = {};
for (const [name, w] of Object.entries(legs)) {
  const r2 = run(w, FEE), r10 = run(w, FEE10);
  sims[name] = r2; sims10[name] = r10;
  const era = (rs) => Object.fromEntries(Object.entries(eras).map(([e, [lo, hi]]) => [e, metrics(sel(rs, lo, hi))]));
  const crisis = (rs) => Object.fromEntries(Object.entries(crises).map(([e, [lo, hi]]) => {
    const sub = sel(rs, lo, hi);
    let W = 1, H = 1, dd = 0;
    for (const x of sub) { W *= 1 + x.net; H = Math.max(H, W); dd = Math.min(dd, W / H - 1); }
    return [e, { ret: W - 1, max_dd: dd, avg_equity: avg(sub.map((x) => x.weight)), n: sub.length }];
  }));
  results[name] = { full: metrics(r2), fee10bp: { full: metrics(r10), eras: era(r10), crises: crisis(r10) },
    eras: era(r2), crises: crisis(r2) };
}

// ---- 7. Frozen comparison / verdict ----
function compare(a, b) {
  const A = results[a], B = results[b];
  const dS = A.full.sharpe_like - B.full.sharpe_like;
  const dD = (A.full.max_dd - B.full.max_dd) * 100;
  const dC = (A.full.cagr - B.full.cagr) * 100;
  return {
    sharpe_diff: dS, maxdd_diff_pp: dD, cagr_diff_pp: dC,
    sharpe_a: A.full.sharpe_like, sharpe_b: B.full.sharpe_like,
    maxdd_a: A.full.max_dd, maxdd_b: B.full.max_dd,
    cagr_a: A.full.cagr, cagr_b: B.full.cagr,
    gates: { sharpe: dS >= 0.02, maxdd: dD >= 1.0, cagr: dC >= -0.10 },
    gates_passed: [dS >= 0.02, dD >= 1.0, dC >= -0.10].filter(Boolean).length,
    gates_total: 3,
  };
}
const primary = compare("VolFairDH", "VolCtrl");
const contextExposure = compare("VolCtrl", "VolFair");
const contextTotal = compare("VolFairDH", "VolFair");
const eraConsistency = Object.keys(eras).filter((e) => results.VolFairDH.eras[e].sharpe_like > results.VolCtrl.eras[e].sharpe_like);
const crisisConsistency = Object.keys(crises).filter((e) => results.VolFairDH.crises[e].ret >= results.VolCtrl.crises[e].ret);
let verdict;
if (primary.gates_passed === 3) {
  verdict = eraConsistency.length >= 3 && crisisConsistency.length >= 4
    ? "volfair_timing_value_descriptively_supported"
    : "volfair_timing_value_mixed_by_era_or_crisis";
} else if (primary.gates_passed >= 1) {
  verdict = "volfair_timing_value_mixed";
} else {
  verdict = "volfair_timing_value_not_descriptively_supported";
}

// ---- 8. Supplementary context ----
const sVals = sMacro.filter((s) => s < 1 - 1e-12);
const sSorted = [...sMacro].sort((a, b) => a - b);
const sStats = {
  months_s_lt_1: sVals.length,
  min: sSorted[0], p25: sSorted[Math.floor(sSorted.length * 0.25)],
  median: sSorted[sSorted.length >> 1], mean: avg(sMacro),
  p75: sSorted[Math.floor(sSorted.length * 0.75)], max: sSorted.at(-1),
};
const maxWeightDiff = Math.max(...wVd.map((w, i) => Math.abs(w - wCtrl[i])));
const eraMeanExposure = Object.fromEntries(Object.keys(eras).map((e) => [e, {
  VolFair: results.VolFair.eras[e].avg_equity,
  VolCtrl: results.VolCtrl.eras[e].avg_equity,
  VolFairDH: results.VolFairDH.eras[e].avg_equity,
}]));

// ---- 9. Outputs ----
const sha = (f) => crypto.createHash("sha256").update(fs.readFileSync(f)).digest("hex");
const out = {
  study: "volfair_exposure_control",
  prereg_commit: "802f6749e30d6f10b871ff61200011ebf965ab3b",
  parent_201_commit: "2ee8fc99158f8a566d98168f757f6b3f1af5a931",
  review_comment: "6285267068",
  scope: "single descriptive hindsight exposure-controlled diagnostic; no causal/OOS/tradability claim",
  inputs: {
    panel_sha256: sha(PANEL), vol_monthly_sha256: sha(VOLM), daily_sha256: sha(DAILY),
    equity_sha256: sha(EQ), cash_sha256: sha(CASH), matrix_sha256: sha(MATRIX), struct_sha256: sha(STRUCT),
  },
  panel: { n: 714, first: "1967-03", last: "2026-08", stale_months: ["2025-10", "2025-11", "2026-01"] },
  control: { formula: "w_ctrl = min(1, k*w_vol); k = mean(w_vd)/mean(w_vol)",
    k, mean_vol: meanVol, mean_vd: meanVd, mean_ctrl: meanCtrl, cap_binding_months: capBind },
  integrity: { volfair_max_abs_diff_vs_recompute: maxFairDiff, w_vd_max_abs_diff: maxVdDiff,
    s_macro_max_abs_diff: maxSDiff, e_dh_max_abs_diff: maxEDhDiff,
    equity_panel_max_abs_diff: maxEqDiff, cash_panel_max_abs_diff: maxCashDiff,
    stale_months_verified: staleIdx.length, deterministic: "verified by test script (two runs byte-identical)" },
  results, comparisons: { primary_voldh_vs_volctrl: primary, context_volctrl_vs_volfair: contextExposure, context_voldh_vs_volfair: contextTotal },
  verdict: { ...primary, era_consistency_count: eraConsistency.length, era_consistent: eraConsistency,
    crisis_consistency_count: crisisConsistency.length, crisis_consistent: crisisConsistency,
    label: verdict, note: "precommitted descriptive heuristics; not statistical evidence, not causal, not tradable" },
  supplementary: { s_macro_stats: sStats, max_abs_weight_diff_vd_vs_ctrl: maxWeightDiff, era_mean_exposure: eraMeanExposure },
  era_metric_note: "Era rows are contiguous slices of the full-path net returns with wealth reset at era start (parent #201 convention); supplementary era turnover/switches therefore include the boundary step. Era consistency uses Sharpe only.",
  production_authorized: false,
};
fs.writeFileSync(path.join(OUT, "volfair-exposure-control-results.json"), JSON.stringify(out, null, 2) + "\n");
const cols = ["date", "volfair", "vol_dh", "vol_ctrl", "s_macro", "stale", "equity", "cash",
  "volfair_net_2bp", "volctrl_net_2bp", "voldh_net_2bp", "volfair_net_10bp", "volctrl_net_10bp", "voldh_net_10bp"];
const csv = [cols.join(",")];
for (let i = 0; i < pan.rows.length; i++) {
  csv.push([pan.rows[i].date, wVol[i].toFixed(6), wVd[i].toFixed(6), wCtrl[i].toFixed(6),
    sMacro[i].toFixed(6), stale[i], pan.rows[i].equity, pan.rows[i].cash,
    sims.VolFair[i].net.toFixed(6), sims.VolCtrl[i].net.toFixed(6), sims.VolFairDH[i].net.toFixed(6),
    sims10.VolFair[i].net.toFixed(6), sims10.VolCtrl[i].net.toFixed(6), sims10.VolFairDH[i].net.toFixed(6)].join(","));
}
fs.writeFileSync(path.join(OUT, "volfair-exposure-control-monthly.csv"), csv.join("\n") + "\n");
console.log(JSON.stringify({ k, meanVol, meanVd, meanCtrl, capBind, primary, verdict: verdict, eraConsistency, crisisConsistency }, null, 2));
