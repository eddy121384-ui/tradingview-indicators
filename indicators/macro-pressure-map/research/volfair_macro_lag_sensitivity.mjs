#!/usr/bin/env node
// VolFair+DH macro-factor lag sensitivity — execution per frozen prereg d215075 (PR #206).
// Research only. production_authorized=false. Draft PR stacked on #204; not merged.
//
// One experimental variable: an additional calendar-month delay L in {0,1,2,3} applied to the
// ALREADY-APPLIED defensive factor `s_macro` (not to `signal_month`, not to the raw B-2 state):
//     s_L[m] = A[m - L]        (calendar months, never row offsets)
//     w_L[m] = w_vol[m] * s_L[m]
// L=0 must reproduce PR #204 (head 6497c54) exactly before any L>0 is evaluated. Otherwise BLOCK.
//
// No tuning, no extra lag points, no alternative control, no best-lag selection.
import fs from "node:fs";
import path from "node:path";
import crypto from "node:crypto";
import { fileURLToPath } from "node:url";

const HERE = path.dirname(fileURLToPath(import.meta.url));
const RES = HERE;
const OUT = path.join(RES, "generated/classic-equity-baselines");
const PANEL = path.join(OUT, "macro-incremental-monthly.csv");
const VOLM = path.join(OUT, "volatility-managed-monthly.csv");
const DAILY = path.join(OUT, "daily-market-total-returns.csv");
const EQ = path.join(RES, "generated/issue-166/equity-monthly-total-returns.csv");
const CASH = path.join(RES, "generated/issue-174/nine-sleeve-monthly-returns.csv");
const MATRIX = path.join(RES, "generated/issue-178/weight-matrix.csv");
const STRUCT = path.join(RES, "generated/issue-183/corrected-structural-monthly.csv");
const CONTROL204 = path.join(OUT, "volfair-exposure-control-monthly.csv");
const RESULTS204 = path.join(OUT, "volfair-exposure-control-results.json");

const FEE = 0.0002, FEE10 = 0.001, NEUTRAL = 0.45;
const LAGS = [0, 1, 2, 3];
const STALE_KEYS = ["2025-10", "2025-11", "2026-01"];
const WARM_START = "1966-05", WARM_END = "1967-02";
const PREREG_COMMIT = "d215075820b6507df09f143b5e0ac59650f1bc7e";
const PARENT_204_COMMIT = "6497c5436c8e8fd84cca5f685b810092b4b9d2a8";
const REVIEW_COMMENT = "6307050459";
const K0_FROZEN = 0.9109091063518062;

const assert = (ok, msg) => { if (!ok) throw new Error("BLOCKED: " + msg); };
const avg = (a) => a.reduce((x, y) => x + y, 0) / a.length;
const sd = (a) => { const m = avg(a); return Math.sqrt(a.reduce((x, y) => x + (y - m) ** 2, 0) / (a.length - 1)); };
const ym = (s) => { const [y, m] = s.slice(0, 7).split("-").map(Number); return y * 12 + m; };
const monthKey = (s) => s.slice(0, 7);
const addMonths = (key, delta) => {
  const [y, m] = key.split("-").map(Number);
  const v = y * 12 + m + delta;
  const yy = Math.floor((v - 1) / 12), mm = v - yy * 12;
  return `${String(yy).padStart(4, "0")}-${String(mm).padStart(2, "0")}`;
};
const parse = (f) => {
  const lines = fs.readFileSync(f, "utf8").trim().split(/\r?\n/);
  const cols = lines.shift().split(",");
  return { cols, rows: lines.map((l) => Object.fromEntries(l.split(",").map((v, j) => [cols[j], v]))) };
};
const sha = (f) => crypto.createHash("sha256").update(fs.readFileSync(f)).digest("hex");

// Recursive leaf diff: numbers compared with tolerance, other primitives exactly.
function leafDiff(mine, target, tol, prefix = "", acc) {
  acc = acc || { max: 0, where: null, n: 0, missing: [], mismatched: [] };
  if (target === null || typeof target !== "object") {
    if (typeof target === "number") {
      if (typeof mine !== "number" || !Number.isFinite(mine)) { acc.missing.push(prefix); return acc; }
      acc.n++;
      const d = Math.abs(mine - target);
      if (d > acc.max) { acc.max = d; acc.where = prefix; }
      if (d > tol) acc.mismatched.push(`${prefix}: ${mine} vs ${target}`);
      return acc;
    }
    if (mine !== target) acc.mismatched.push(`${prefix}: ${JSON.stringify(mine)} vs ${JSON.stringify(target)}`);
    acc.n++;
    return acc;
  }
  for (const [k, v] of Object.entries(target)) {
    if (mine === null || mine === undefined || typeof mine !== "object" || !(k in mine)) {
      acc.missing.push(prefix ? `${prefix}.${k}` : k);
      continue;
    }
    leafDiff(mine[k], v, tol, prefix ? `${prefix}.${k}` : k, acc);
  }
  return acc;
}

export function compute() {
  // ---- 1. Frozen panel: 714 contiguous months 1967-03..2026-08 ----
  const pan = parse(PANEL);
  assert(pan.rows.length === 714, `panel rows ${pan.rows.length} != 714`);
  pan.rows.forEach((r, i) => {
    if (i) assert(ym(r.date) - ym(pan.rows[i - 1].date) === 1, "panel calendar gap at " + r.date);
  });
  assert(pan.rows[0].date === "1967-03" && pan.rows.at(-1).date === "2026-08", "panel bounds");
  for (const r of pan.rows) {
    const e = Number(r.equity), c = Number(r.cash);
    assert(Number.isFinite(e) && e > -1 && Number.isFinite(c) && c > -1, "bad frozen return " + r.date);
  }
  const eqMap = new Map(parse(EQ).rows.map((r) => [monthKey(r.date), Number(r.equity_tr)]));
  const cashMap = new Map(parse(CASH).rows.map((r) => [monthKey(r.date), Number(r.cash)]));
  let equityDiff = 0, cashDiff = 0;
  for (const r of pan.rows) {
    assert(eqMap.has(r.date) && cashMap.has(r.date), "source return missing " + r.date);
    equityDiff = Math.max(equityDiff, Math.abs(eqMap.get(r.date) - Number(r.equity)));
    cashDiff = Math.max(cashDiff, Math.abs(cashMap.get(r.date) - Number(r.cash)));
  }
  assert(equityDiff < 1e-12 && cashDiff < 1e-12, "panel returns differ from frozen sources");

  // ---- 2. Frozen 9-state equity matrix and #183 B-2 applied-state timeline (read-only) ----
  const mx = parse(MATRIX);
  assert(mx.rows.length === 9, "matrix rows != 9");
  const E = {};
  for (const r of mx.rows) {
    const sum = ["sp500", "nasdaq", "russell", "treasury2y", "treasury10y", "longtreasury", "gold", "oil", "cash"]
      .map((k) => Number(r[k])).reduce((a, b) => a + b, 0);
    assert(Math.abs(sum - 100) < 1e-9, "matrix row != 100 " + r.state);
    E[r.state] = (Number(r.sp500) + Number(r.nasdaq) + Number(r.russell)) / 100;
  }
  assert(Math.abs(E["G_Neutral/I_Neutral"] - NEUTRAL) < 1e-12, "neutral anchor != 0.45");
  const st = parse(STRUCT);
  assert(st.rows.length === 721, `struct rows ${st.rows.length} != 721`);
  const stateByMonth = new Map(st.rows.map((r) => [monthKey(r.date), r.alloc_state]));

  // ---- 3. VolFair recomputation (integrity only, no new data) ----
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
    assert(v > 0, "RV <= 0 " + m);
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
  let volfairRecomputeDiff = 0;
  volm.rows.forEach((r, i) => {
    assert(r.date.slice(0, 7).replace("-", "") === panelM[i], "vol date " + r.date);
    volfairRecomputeDiff = Math.max(volfairRecomputeDiff, Math.abs(Number(r.w_fair) - wFair[i]));
  });
  assert(volfairRecomputeDiff < 1e-4, "VolFair recompute mismatch " + volfairRecomputeDiff);

  // ---- 4. Frozen weight columns and identities ----
  const dates = pan.rows.map((r) => r.date);
  const wVol = pan.rows.map((r) => Number(r.volfair));
  const wVd = pan.rows.map((r) => Number(r.vol_dh));
  const sMacro = pan.rows.map((r) => Number(r.s_macro));
  const stale = pan.rows.map((r) => Number(r.stale));
  const eDh = pan.rows.map((r) => Number(r.E_DH));

  let wVdDiff = 0, sDiff = 0, eDhDiff = 0;
  for (let i = 0; i < pan.rows.length; i++) {
    wVdDiff = Math.max(wVdDiff, Math.abs(wVol[i] * sMacro[i] - wVd[i]));
    const stt = stateByMonth.get(dates[i]);
    if (stt !== undefined) {
      assert(E[stt] !== undefined, "unknown state " + dates[i]);
      eDhDiff = Math.max(eDhDiff, Math.abs(E[stt] - eDh[i]));
      sDiff = Math.max(sDiff, Math.abs(Math.min(1, E[stt] / NEUTRAL) - sMacro[i]));
    }
  }
  // 6-decimal storage: a product of two rounded columns can differ from the rounded product.
  assert(wVdDiff < 2e-6, "vol_dh != volfair*s_macro " + wVdDiff);
  assert(sDiff < 2e-6, "s_macro != min(1,E_DH/0.45) " + sDiff);
  assert(eDhDiff < 5e-5, "E_DH != matrix equity " + eDhDiff);

  const staleIdx = stale.map((v, i) => (v === 1 ? i : -1)).filter((i) => i >= 0);
  assert(staleIdx.length === 3, "stale months != 3");
  assert(staleIdx.map((i) => dates[i]).join(",") === STALE_KEYS.join(","), "stale month identity");
  for (const i of staleIdx) {
    assert(Math.abs(sMacro[i] - 1) < 1e-12, "stale s != 1 at " + dates[i]);
    assert(Math.abs(wVd[i] - wVol[i]) < 2e-6, "stale vol_dh != volfair at " + dates[i]);
  }
  // Frozen stale-carry rule: stored value must equal the last valid factor; no interpolation,
  // no later observation, no calendar compression.
  for (const i of staleIdx) {
    let j = i - 1;
    while (j >= 0 && stale[j] === 1) j--;
    assert(j >= 0, "no valid factor precedes stale month " + dates[i]);
    assert(Math.abs(sMacro[i] - sMacro[j]) < 1e-12, "stale carry broken at " + dates[i]);
    assert(sMacro[i] === Math.max(...sMacro.slice(j, i)), "stale carry is not the last valid factor at " + dates[i]);
    assert(!stateByMonth.has(dates[i]), "#183 unexpectedly has a state for stale month " + dates[i]);
  }

  // ---- 5. Applied-factor calendar map A: 1966-05..2026-08 (724 months) ----
  const A = new Map();
  for (let i = 0; i < dates.length; i++) A.set(dates[i], sMacro[i]);
  const warm = [];
  let cur = WARM_START;
  while (ym(cur) <= ym(WARM_END)) { warm.push(cur); cur = addMonths(cur, 1); }
  assert(warm.length === 10, "warm-up tail length != 10");
  for (const k of warm) {
    assert(stateByMonth.has(k), "warm-up month missing from #183 timeline: " + k);
    const stt = stateByMonth.get(k);
    assert(E[stt] !== undefined, "unknown warm-up state at " + k);
    A.set(k, Math.min(1, E[stt] / NEUTRAL));
  }
  assert(A.size === 724, `factor map size ${A.size} != 724`);
  // Warm-up reconstruction validated on every observed #183 month that is inside the panel.
  let warmOverlapN = 0, warmOverlapDiff = 0;
  for (const [k, stt] of stateByMonth) {
    if (!A.has(k) || ym(k) < ym("1967-03")) continue;
    warmOverlapN++;
    warmOverlapDiff = Math.max(warmOverlapDiff, Math.abs(Math.min(1, E[stt] / NEUTRAL) - A.get(k)));
  }
  assert(warmOverlapN === 711, `warm-up overlap ${warmOverlapN} != 711`);
  assert(warmOverlapDiff < 2e-6, "warm-up reconstruction mismatch " + warmOverlapDiff);

  // ---- 6. Factor shift, weights, and matched control (one lag at a time) ----
  // Fail-stop ordering. The engine materialises ONLY the L=0 replication point here, runs the L=0
  // replication gate in §9, and only then builds and prices L=1,2,3 in §9b. No L>0 weight or L>0
  // return exists before the gate passes. The realised order is recorded in `execOrder` and is
  // asserted, so the fail-stop claim is checkable rather than merely stated.
  const execOrder = [];
  const legs = { VolFair: wVol };
  const lagInfo = {};
  function buildLag(L) {
    const sL = [], wL = [];
    for (let i = 0; i < dates.length; i++) {
      const src = addMonths(dates[i], -L);
      assert(A.has(src), `L=${L} needs out-of-range factor month ${src} for payoff ${dates[i]}`);
      const s = A.get(src);
      assert(Number.isFinite(s) && s >= 0.5 && s <= 1, `L=${L} factor out of [0.5,1] at ${dates[i]}: ${s}`);
      sL.push(s);
      // L=0 uses the frozen stored product (exact #204 replication point); L>0 is the product.
      wL.push(L === 0 ? wVd[i] : wVol[i] * s);
    }
    const meanVol = avg(wVol), meanL = avg(wL);
    const kL = meanL / meanVol;
    const wCtrl = wVol.map((w) => Math.min(1, kL * w));
    assert(kL > 0 && kL < 1, `L=${L} k outside (0,1): ${kL}`);
    const capBind = wVol.filter((w) => kL * w > 1).length;
    assert(capBind === 0, `L=${L} cap binds in ${capBind} months`);
    assert(Math.abs(avg(wCtrl) - meanL) < 1e-9, `L=${L} mean exposure mismatch ${avg(wCtrl) - meanL}`);
    for (let i = 0; i < wL.length; i++) {
      assert(wL[i] >= 0 && wVol[i] >= 0, `L=${L} negative weight`);
      // L>0 products are exact in float; L=0 reads a 6-decimal stored column (storage tolerance).
      const tol = L === 0 ? 2e-6 : 0;
      assert(wL[i] <= wVol[i] + tol, `L=${L} weight ${wL[i]} > volfair ${wVol[i]}`);
      assert(wCtrl[i] <= wVol[i] + 1e-15, `L=${L} control > volfair`);
    }
    if (L === 0) {
      assert(Math.abs(kL - K0_FROZEN) <= 1e-12, `k_0 ${kL} != frozen ${K0_FROZEN}`);
      let prodDiff = 0;
      for (let i = 0; i < dates.length; i++) prodDiff = Math.max(prodDiff, Math.abs(wVol[i] * sL[i] - wL[i]));
      assert(prodDiff < 2e-6, "L=0 product vs stored vol_dh " + prodDiff);
    }
    lagInfo[L] = { sL, wL, wCtrl, k: kL, meanVol, meanL, meanCtrl: avg(wCtrl), capBind };
    legs[`L${L}`] = wL;
    legs[`C${L}`] = wCtrl;
    execOrder.push(`lag_${L}_weights_and_control_built`);
  }
  // Only the replication point exists at this stage. L>0 is deliberately not constructible yet.
  buildLag(0);

  // ---- 7. Backtest, metrics, eras, crises (identical conventions to #201/#204) ----
  function run(w, fee) {
    return pan.rows.map((r, i) => {
      const to = i ? Math.abs(w[i] - w[i - 1]) : 0;
      const e = Number(r.equity), c = Number(r.cash);
      return { date: r.date, weight: w[i], equity: e, cash: c, turnover: to, net: e * w[i] + c * (1 - w[i]) - fee * to };
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
  const eraFn = (rs) => Object.fromEntries(Object.entries(eras).map(([e, [lo, hi]]) => [e, metrics(sel(rs, lo, hi))]));
  const crisisFn = (rs) => Object.fromEntries(Object.entries(crises).map(([e, [lo, hi]]) => {
    const sub = sel(rs, lo, hi);
    let W = 1, H = 1, dd = 0;
    for (const x of sub) { W *= 1 + x.net; H = Math.max(H, W); dd = Math.min(dd, W / H - 1); }
    return [e, { ret: W - 1, max_dd: dd, avg_equity: avg(sub.map((x) => x.weight)), n: sub.length }];
  }));

  const sims = {}, sims10 = {}, results = {};
  function backtestLeg(name) {
    const w = legs[name];
    const r2 = run(w, FEE), r10 = run(w, FEE10);
    sims[name] = r2; sims10[name] = r10;
    results[name] = {
      full: metrics(r2), eras: eraFn(r2), crises: crisisFn(r2),
      fee10bp: { full: metrics(r10), eras: eraFn(r10), crises: crisisFn(r10) },
    };
    execOrder.push(`${name}_pnl_computed`);
  }
  // Fail-stop: before the gate, only VolFair and the L=0 replication point are priced.
  for (const name of ["VolFair", "L0", "C0"]) backtestLeg(name);

  // ---- 8. Comparison helper (frozen gate thresholds) ----
  function compare(a, b) {
    const A = results[a], B = results[b];
    const dS = A.full.sharpe_like - B.full.sharpe_like;
    const dD = (A.full.max_dd - B.full.max_dd) * 100;
    const dC = (A.full.cagr - B.full.cagr) * 100;
    return { sharpe_diff: dS, maxdd_diff_pp: dD, cagr_diff_pp: dC,
      sharpe_a: A.full.sharpe_like, sharpe_b: B.full.sharpe_like,
      maxdd_a: A.full.max_dd, maxdd_b: B.full.max_dd, cagr_a: A.full.cagr, cagr_b: B.full.cagr,
      gates: { sharpe: dS >= 0.02, maxdd: dD >= 1.0, cagr: dC >= -0.10 },
      gates_passed: [dS >= 0.02, dD >= 1.0, dC >= -0.10].filter(Boolean).length, gates_total: 3 };
  }

  // ---- 9. L=0 replication gate: must reproduce #204 exactly, else BLOCK ----
  const c204 = parse(CONTROL204);
  assert(c204.rows.length === 714, "204 monthly rows != 714");
  const j204 = JSON.parse(fs.readFileSync(RESULTS204, "utf8"));
  const t204 = (name) => new Map(c204.rows.map((r) => [r.date, Number(r[name])]));
  const maxAbs = (mine, map) => {
    let m = 0;
    c204.rows.forEach((r, i) => {
      assert(map.has(r.date), "204 target missing " + r.date);
      m = Math.max(m, Math.abs(mine[i] - map.get(r.date)));
    });
    return m;
  };
  const l0repl = {
    weights_volfair_max_abs_diff_vs_204: maxAbs(wVol, t204("volfair")),
    weights_lag0_max_abs_diff_vs_204: maxAbs(lagInfo[0].wL, t204("vol_dh")),
    weights_ctrl0_max_abs_diff_vs_204: maxAbs(lagInfo[0].wCtrl, t204("vol_ctrl")),
    net_2bp_volfair_max_abs_diff_vs_204: maxAbs(sims.VolFair.map((x) => x.net), t204("volfair_net_2bp")),
    net_2bp_lag0_max_abs_diff_vs_204: maxAbs(sims.L0.map((x) => x.net), t204("voldh_net_2bp")),
    net_2bp_ctrl0_max_abs_diff_vs_204: maxAbs(sims.C0.map((x) => x.net), t204("volctrl_net_2bp")),
    net_10bp_volfair_max_abs_diff_vs_204: maxAbs(sims10.VolFair.map((x) => x.net), t204("volfair_net_10bp")),
    net_10bp_lag0_max_abs_diff_vs_204: maxAbs(sims10.L0.map((x) => x.net), t204("voldh_net_10bp")),
    net_10bp_ctrl0_max_abs_diff_vs_204: maxAbs(sims10.C0.map((x) => x.net), t204("volctrl_net_10bp")),
  };
  assert(l0repl.weights_volfair_max_abs_diff_vs_204 <= 2e-6, "L=0 volfair weights vs #204");
  assert(l0repl.weights_lag0_max_abs_diff_vs_204 <= 2e-6, "L=0 leg weights vs #204");
  assert(l0repl.weights_ctrl0_max_abs_diff_vs_204 <= 2e-6, "L=0 control weights vs #204");
  for (const [k, v] of Object.entries(l0repl)) {
    if (k.startsWith("net_")) assert(v <= 1e-6, `${k} = ${v} > 1e-6`);
  }
  const metricDiffs = {
    volfair: leafDiff(results.VolFair, j204.results.VolFair, 1e-9),
    lag0_vs_204_voldh: leafDiff(results.L0, j204.results.VolFairDH, 1e-9),
    ctrl0_vs_204_volctrl: leafDiff(results.C0, j204.results.VolCtrl, 1e-9),
  };
  for (const [name, d] of Object.entries(metricDiffs)) {
    assert(d.missing.length === 0, `L=0 ${name} missing metric keys: ${d.missing.join(", ")}`);
    assert(d.mismatched.length === 0, `L=0 ${name} metric mismatch (max ${d.max} at ${d.where}): ${d.mismatched.slice(0, 5).join(" ; ")}`);
  }
  const primary0 = compare("L0", "C0");
  const context0vsfair = compare("L0", "VolFair");
  const contextC0vsfair = compare("C0", "VolFair");
  const cmpDiffs = {
    primary_vs_204: leafDiff(primary0, j204.comparisons.primary_voldh_vs_volctrl, 1e-9),
    context_lag0_vs_volfair_vs_204: leafDiff(context0vsfair, j204.comparisons.context_voldh_vs_volfair, 1e-9),
    context_ctrl0_vs_volfair_vs_204: leafDiff(contextC0vsfair, j204.comparisons.context_volctrl_vs_volfair, 1e-9),
  };
  for (const [name, d] of Object.entries(cmpDiffs)) {
    assert(d.missing.length === 0, `L=0 ${name} missing keys: ${d.missing.join(", ")}`);
    assert(d.mismatched.length === 0, `L=0 ${name} mismatch: ${d.mismatched.slice(0, 5).join(" ; ")}`);
  }
  const era0 = Object.keys(eras).filter((e) => results.L0.eras[e].sharpe_like > results.C0.eras[e].sharpe_like);
  const crisis0 = Object.keys(crises).filter((e) => results.L0.crises[e].ret >= results.C0.crises[e].ret);
  const verdict0 = primary0.gates_passed === 3
    ? (era0.length >= 3 && crisis0.length >= 4 ? "volfair_timing_value_descriptively_supported" : "volfair_timing_value_mixed_by_era_or_crisis")
    : (primary0.gates_passed >= 1 ? "volfair_timing_value_mixed" : "volfair_timing_value_not_descriptively_supported");
  assert(verdict0 === j204.verdict.label, `L=0 verdict ${verdict0} != #204 ${j204.verdict.label}`);
  assert(era0.length === j204.verdict.era_consistency_count, "L=0 era consistency count != #204");
  assert(crisis0.length === j204.verdict.crisis_consistency_count, "L=0 crisis consistency count != #204");
  leafDiff({ gates_passed: primary0.gates_passed, gates_total: primary0.gates_total, label: verdict0 },
    { gates_passed: j204.verdict.gates_passed, gates_total: j204.verdict.gates_total, label: j204.verdict.label }, 1e-9);
  l0repl.passed = true;
  l0repl.legacy_204_verdict = j204.verdict.label;
  l0repl.era_consistency_count = era0.length;
  l0repl.crisis_consistency_count = crisis0.length;

  // ---- 9b. L=0 gate PASSED — only now may L>0 be built and priced ----
  execOrder.push("l0_replication_gate_passed");
  for (const L of [1, 2, 3]) {
    buildLag(L);
    backtestLeg(`L${L}`);
    backtestLeg(`C${L}`);
  }
  // Fail-stop is structural (sequential code); assert it explicitly so the claim is falsifiable.
  {
    const gateAt = execOrder.indexOf("l0_replication_gate_passed");
    assert(gateAt >= 0, "execution order: gate event missing");
    assert(execOrder.indexOf("L0_pnl_computed") >= 0 && execOrder.indexOf("L0_pnl_computed") < gateAt,
      "execution order: L=0 P&L must be computed before the gate");
    for (const L of [1, 2, 3]) {
      const builtAt = execOrder.indexOf(`lag_${L}_weights_and_control_built`);
      const pricedAt = execOrder.indexOf(`L${L}_pnl_computed`);
      assert(builtAt > gateAt, `fail-stop violated: L=${L} weights built before the gate passed`);
      assert(pricedAt > gateAt, `fail-stop violated: L=${L} P&L computed before the gate passed`);
    }
    assert(execOrder.filter((e) => /^L[123]_pnl_computed$/.test(e)).length === 3, "execution order: expected exactly three L>0 P&L events");
  }
  const execOrderEnforced = "L=0 replication gate precedes all L>0 weight construction and all L>0 P&L";

  // ---- 10. Per-lag gates, consistency, verdicts ----
  const perLag = {};
  for (const L of LAGS) {
    const leg = `L${L}`, ctrl = `C${L}`;
    const primary = compare(leg, ctrl);
    const vsFair = compare(leg, "VolFair");
    const vsL0 = compare(leg, "L0");
    const eraPos = Object.keys(eras).filter((e) => results[leg].eras[e].sharpe_like > results[ctrl].eras[e].sharpe_like);
    const crisisNonNeg = Object.keys(crises).filter((e) => results[leg].crises[e].ret >= results[ctrl].crises[e].ret);
    const primary10 = (() => {
      const a = results[leg].fee10bp.full, b = results[ctrl].fee10bp.full;
      const dS = a.sharpe_like - b.sharpe_like, dD = (a.max_dd - b.max_dd) * 100, dC = (a.cagr - b.cagr) * 100;
      return { sharpe_diff: dS, maxdd_diff_pp: dD, cagr_diff_pp: dC,
        gates: { sharpe: dS >= 0.02, maxdd: dD >= 1.0, cagr: dC >= -0.10 },
        gates_passed: [dS >= 0.02, dD >= 1.0, dC >= -0.10].filter(Boolean).length, gates_total: 3 };
    })();
    const consistency = { era_positive_sharpe_count: eraPos.length, era_positive_sharpe: eraPos,
      crisis_non_negative_count: crisisNonNeg.length, crisis_non_negative: crisisNonNeg,
      era_pass: eraPos.length >= 3, crisis_pass: crisisNonNeg.length >= 4 };
    let label;
    if (primary.gates_passed === 3) label = consistency.era_pass && consistency.crisis_pass
      ? `lag_${L}_timing_value_descriptively_supported` : `lag_${L}_timing_value_mixed_by_era_or_crisis`;
    else if (primary.gates_passed >= 1) label = `lag_${L}_timing_value_mixed`;
    else label = `lag_${L}_timing_value_not_descriptively_supported`;
    perLag[L] = { k: lagInfo[L].k, mean_equity: lagInfo[L].meanL, mean_equity_ctrl: lagInfo[L].meanCtrl,
      cap_binding_months: lagInfo[L].capBind, primary_vs_own_control: primary, primary_vs_own_control_10bp: primary10,
      descriptive_vs_volfair: vsFair, decay_vs_lag0: vsL0, consistency, label,
      full_pass: primary.gates_passed === 3 && consistency.era_pass && consistency.crisis_pass };
  }
  const delayed = LAGS.filter((L) => L > 0);
  const fullPass = delayed.filter((L) => perLag[L].full_pass);
  const overallLabel = fullPass.length === delayed.length ? "lag_robust_descriptively_supported"
    : (fullPass.length > 0 ? "lag_partially_supported" : "lag_not_descriptively_supported");

  // ---- 11. Decay relative to the L=0 replication point ----
  const decay = {};
  for (const L of LAGS) {
    const dL = perLag[L].primary_vs_own_control, d0 = perLag[0].primary_vs_own_control;
    decay[L] = {
      delta_vs_control_sharpe: dL.sharpe_diff, delta_vs_control_sharpe_minus_lag0: dL.sharpe_diff - d0.sharpe_diff,
      delta_vs_control_maxdd_pp: dL.maxdd_diff_pp, delta_vs_control_maxdd_pp_minus_lag0: dL.maxdd_diff_pp - d0.maxdd_diff_pp,
      delta_vs_control_cagr_pp: dL.cagr_diff_pp, delta_vs_control_cagr_pp_minus_lag0: dL.cagr_diff_pp - d0.cagr_diff_pp,
      leg_sharpe_minus_lag0: results[`L${L}`].full.sharpe_like - results.L0.full.sharpe_like,
      leg_maxdd_minus_lag0: results[`L${L}`].full.max_dd - results.L0.full.max_dd,
      leg_cagr_minus_lag0: results[`L${L}`].full.cagr - results.L0.full.cagr,
    };
  }
  const sharpeSeq = LAGS.map((L) => perLag[L].primary_vs_own_control.sharpe_diff);
  const monotoneDecline = sharpeSeq.every((v, i) => i === 0 || v <= sharpeSeq[i - 1]);
  const monotoneRise = sharpeSeq.every((v, i) => i === 0 || v >= sharpeSeq[i - 1]);

  // ---- 12. Crisis defense matrix and disappearance ----
  const crisisDefense = {};
  const disappearance = {};
  for (const L of LAGS) {
    crisisDefense[L] = {};
    for (const c of Object.keys(crises)) {
      const d = results[`L${L}`].crises[c].ret - results[`C${L}`].crises[c].ret;
      crisisDefense[L][c] = {
        D_vs_own_control: d, present: d >= 0,
        secondary_vs_volfair: results[`L${L}`].crises[c].ret - results.VolFair.crises[c].ret,
      };
    }
  }
  for (const L of delayed) {
    const disappeared = [], weakened = [];
    for (const c of Object.keys(crises)) {
      const d0 = crisisDefense[0][c].D_vs_own_control, dL = crisisDefense[L][c].D_vs_own_control;
      if (d0 >= 0 && dL < 0) disappeared.push(c);
      else if (((d0 >= 0 && dL >= 0) || (d0 < 0 && dL < 0)) && dL < d0) weakened.push(c);
    }
    disappearance[L] = { disappeared, weakened,
      defense_lost_definition: "D_0,c >= 0 and D_L,c < 0" };
  }

  // ---- 13. Assembly ----
  const out = {
    study: "volfair_macro_lag_sensitivity",
    prereg_commit: PREREG_COMMIT,
    parent_204_commit: PARENT_204_COMMIT,
    review_comment: REVIEW_COMMENT,
    scope: "four predeclared calendar-month delays of the already-applied macro factor; descriptive delay stress test; not PIT, not causal, not tradable",
    panel: { n: 714, first: "1967-03", last: "2026-08", stale_months: STALE_KEYS, fee_primary_bp: 2, fee_sensitivity_bp: 10 },
    lag_definition: { formula: "s_L[m] = A[m-L]; w_L[m] = w_vol[m]*s_L[m]; A = frozen applied factor",
      applied_to: "already-applied s_macro, not signal_month and not raw B-2 state", lags: LAGS,
      calendar_map_months: A.size, warmup_tail: `${WARM_START}..${WARM_END}`,
      note: "L=0 uses the frozen vol_dh column for exact #204 replication; L>0 is the full-precision product" },
    inputs: { panel_sha256: sha(PANEL), vol_monthly_sha256: sha(VOLM), daily_sha256: sha(DAILY),
      equity_sha256: sha(EQ), cash_sha256: sha(CASH), matrix_sha256: sha(MATRIX), struct_sha256: sha(STRUCT),
      control204_monthly_sha256: sha(CONTROL204), results204_sha256: sha(RESULTS204) },
    integrity: { volfair_max_abs_diff_vs_recompute: volfairRecomputeDiff,
      w_vd_max_abs_diff: wVdDiff, s_macro_max_abs_diff: sDiff, e_dh_max_abs_diff: eDhDiff,
      equity_panel_max_abs_diff: equityDiff, cash_panel_max_abs_diff: cashDiff,
      stale_months_verified: staleIdx.length, stale_month_keys: STALE_KEYS,
      warmup_overlap_n: warmOverlapN, warmup_overlap_max_abs_diff: warmOverlapDiff,
      execution_order_enforced: execOrderEnforced, execution_order: execOrder,
      l0_replication: l0repl },
    results, comparisons: {
      l0_primary_vs_own_control: primary0,
      l0_vs_volfair: context0vsfair,
      ctrl0_vs_volfair: contextC0vsfair,
    },
    lags: perLag, decay, crisis_defense: crisisDefense, crisis_defense_disappearance: disappearance,
    decay_note: "monotonicity is descriptive only; not a gate and never used to select a lag",
    overall: { per_lag: Object.fromEntries(LAGS.map((L) => [L, { label: perLag[L].label,
      gates_passed: perLag[L].primary_vs_own_control.gates_passed,
      era_consistency_count: perLag[L].consistency.era_positive_sharpe_count,
      crisis_consistency_count: perLag[L].consistency.crisis_non_negative_count,
      full_pass: perLag[L].full_pass }])),
      label: overallLabel, all_delayed_full_pass: fullPass.length === delayed.length,
      any_delayed_full_pass: fullPass.length > 0,
      monotone_decline_in_sharpe: monotoneDecline, monotone_rise_in_sharpe: monotoneRise,
      sharpe_sequence_lag0_to_lag3: sharpeSeq,
      note: "precommitted descriptive label; no best-lag selection; not statistical evidence" },
    era_metric_note: "Era rows are contiguous slices of the full-path net returns with wealth reset at era start (parent #201 convention); supplementary era turnover/switches therefore include the boundary step. Era consistency uses Sharpe only.",
    limitations: [
      "revised-vintage, non-PIT; #189 PIT not identifiable; cannot repair data-revision bias",
      "delays only the already-applied factor; not a release-calendar replay and not a point-in-time backtest",
      "k_L uses full-sample information and is a descriptive hindsight counterfactual, not tradable",
      "no out-of-sample claim, no p-values, no multiplicity correction",
    ],
    production_authorized: false,
  };

  // Monthly audit CSV (6 decimals).
  const cols = ["date", "volfair", "vol_dh", "s_macro", "stale", "equity", "cash",
    "s_lag0", "s_lag1", "s_lag2", "s_lag3",
    "w_lag0", "w_lag1", "w_lag2", "w_lag3",
    "w_ctrl0", "w_ctrl1", "w_ctrl2", "w_ctrl3",
    "volfair_net_2bp", "lag0_net_2bp", "lag1_net_2bp", "lag2_net_2bp", "lag3_net_2bp",
    "ctrl0_net_2bp", "ctrl1_net_2bp", "ctrl2_net_2bp", "ctrl3_net_2bp",
    "volfair_net_10bp", "lag0_net_10bp", "lag1_net_10bp", "lag2_net_10bp", "lag3_net_10bp",
    "ctrl0_net_10bp", "ctrl1_net_10bp", "ctrl2_net_10bp", "ctrl3_net_10bp"];
  const csv = [cols.join(",")];
  for (let i = 0; i < dates.length; i++) {
    csv.push([dates[i], wVol[i].toFixed(6), wVd[i].toFixed(6), sMacro[i].toFixed(6), stale[i],
      pan.rows[i].equity, pan.rows[i].cash,
      lagInfo[0].sL[i].toFixed(6), lagInfo[1].sL[i].toFixed(6), lagInfo[2].sL[i].toFixed(6), lagInfo[3].sL[i].toFixed(6),
      lagInfo[0].wL[i].toFixed(6), lagInfo[1].wL[i].toFixed(6), lagInfo[2].wL[i].toFixed(6), lagInfo[3].wL[i].toFixed(6),
      lagInfo[0].wCtrl[i].toFixed(6), lagInfo[1].wCtrl[i].toFixed(6), lagInfo[2].wCtrl[i].toFixed(6), lagInfo[3].wCtrl[i].toFixed(6),
      sims.VolFair[i].net.toFixed(6), sims.L0[i].net.toFixed(6), sims.L1[i].net.toFixed(6), sims.L2[i].net.toFixed(6), sims.L3[i].net.toFixed(6),
      sims.C0[i].net.toFixed(6), sims.C1[i].net.toFixed(6), sims.C2[i].net.toFixed(6), sims.C3[i].net.toFixed(6),
      sims10.VolFair[i].net.toFixed(6), sims10.L0[i].net.toFixed(6), sims10.L1[i].net.toFixed(6), sims10.L2[i].net.toFixed(6), sims10.L3[i].net.toFixed(6),
      sims10.C0[i].net.toFixed(6), sims10.C1[i].net.toFixed(6), sims10.C2[i].net.toFixed(6), sims10.C3[i].net.toFixed(6),
    ].join(","));
  }
  return { out, csv: csv.join("\n") + "\n" };
}

export function main() {
  const a = compute();
  const b = compute(); // determinism: byte-identical outputs on a second run
  const jsonA = JSON.stringify(a.out, null, 2) + "\n";
  const jsonB = JSON.stringify(b.out, null, 2) + "\n";
  assert(jsonA === jsonB, "determinism: JSON differs between runs");
  assert(a.csv === b.csv, "determinism: CSV differs between runs");
  assert(a.out.integrity.l0_replication.passed === true, "L=0 replication gate did not pass");
  fs.writeFileSync(path.join(OUT, "volfair-macro-lag-sensitivity-results.json"), jsonA);
  fs.writeFileSync(path.join(OUT, "volfair-macro-lag-sensitivity-monthly.csv"), a.csv);
  console.log(JSON.stringify({
    study: a.out.study,
    l0_replication: a.out.integrity.l0_replication,
    per_lag: a.out.overall.per_lag,
    overall: a.out.overall.label,
    crisis_disappearance: a.out.crisis_defense_disappearance,
    production_authorized: a.out.production_authorized,
  }, null, 2));
}

if (process.argv[1] && path.resolve(process.argv[1]) === fileURLToPath(import.meta.url)) {
  main();
}
