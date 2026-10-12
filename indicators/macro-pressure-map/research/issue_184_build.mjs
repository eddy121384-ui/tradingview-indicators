#!/usr/bin/env node
// Issue #184 — specificity builder: A/B reproduction + C/D controls + placebo null.
// Frozen contract: indicators/macro-pressure-map/research/issue-184-v66-specificity-prereg.md
// Post-prereg commit ONLY (prereg 6da9a3611c3b16b8e602711bd9f1e3f3678ceb6a).
// No policy parameter changed. No optimizer. No Pine. Parents read-only.
// All writes go to research/generated/issue-184/.

import fs from "node:fs";
import path from "node:path";
import crypto from "node:crypto";

const ROOT = process.cwd();
const RES = path.join(ROOT, "indicators/macro-pressure-map/research");
const GEN184 = path.join(RES, "generated/issue-184");
const BIG = 1 << 28;

const sha256 = (b) => crypto.createHash("sha256").update(b).digest("hex");
const fin = (x) => typeof x === "number" && Number.isFinite(x);
const readLF = (rel) => fs.readFileSync(path.join(RES, rel), "utf8").replace(/\r/g, "");
const shaWt = (rel) => sha256(fs.readFileSync(path.join(RES, rel)));

// ---------------------------------------------------------------- frozen policy (verbatim #183)
const ORDER = ["sp500", "nasdaq", "russell", "treasury2y", "treasury10y", "longtreasury", "gold", "oil"];
const EQ = ["sp500", "nasdaq", "russell"];
const SCAP = { sp500: 35, nasdaq: 20, russell: 15, treasury2y: 15, treasury10y: 25, longtreasury: 15, gold: 12, oil: 8 };
const FCAP = { equity: 60, rates: 50, real: 15 };
const ZEROS = [["G_Low/I_Low", "oil"], ["G_Neutral/I_High", "russell"], ["G_High/I_Low", "gold"]];
const CASH_MIN = 2, CASH_MAX = 60, COST = 0.0002, TOL = 1e-9;
const BUDGET = 5;
const D_PP = 3.051724137931045; // prereg section 4
const REQUIRED_BASE = "411835cc9e3a00d0f5d998df9fb2058d8a917e96";
const PARENTS = {
  "issue-177": "bc652bd615f2c5e9137050d01c666dbcd9528cd3",
  "issue-178": "10dcdce0ec86b0493d6df6b916b720eba46dcbe6",
  "issue-180": "ac251ad5149d9f550d82dfb34b3551fe01032367",
  "issue-182": "57852112ce95913d48297b35f803a1583cbab314",
  "issue-183": "411835cc9e3a00d0f5d998df9fb2058d8a917e96",
};
const G174 = "generated/issue-174", G176 = "generated/issue-176";
const G177 = "generated/issue-177", G178 = "generated/issue-178";
const G180 = "generated/issue-180", G182 = "generated/issue-182", G183 = "generated/issue-183";

// ---------------------------------------------------------------- frozen matrix
function loadMatrix() {
  const t = readLF(`${G178}/weight-matrix.csv`).trim().split("\n");
  const h = t[0].split(",");
  const m = new Map();
  for (const l of t.slice(1)) {
    const c = l.split(",");
    const w = {};
    for (const s of ORDER) w[s] = +c[h.indexOf(s)];
    w.cash = +c[h.indexOf("cash")];
    m.set(c[0], w);
  }
  return m;
}
const SW = loadMatrix();
for (const [st, w] of SW) {
  const tot = ORDER.concat(["cash"]).reduce((a, s) => a + w[s], 0);
  if (Math.abs(tot - 100) > TOL) { console.error("FAIL matrix sum " + st); process.exit(1); }
  if (w.cash < CASH_MIN - TOL || w.cash > CASH_MAX + TOL) { console.error("FAIL matrix cash " + st); process.exit(1); }
  for (const [dh, s] of ZEROS) if (st === dh && Math.abs(w[s]) > TOL) { console.error("FAIL zero " + st); process.exit(1); }
}

// ---------------------------------------------------------------- B-2 timeline (verbatim #183)
function band(s) { return s < -10 ? "Low" : s > 10 ? "High" : "Neutral"; }
const dhByDate = new Map();
{
  const t = readLF("generated/issue-160/deep-history-v01-monthly.csv").trim().split("\n");
  const h = t[0].split(",");
  const gi = h.indexOf("growth_dh"), ii = h.indexOf("inflation_dh");
  for (const l of t.slice(1)) {
    const c = l.split(",");
    const g = parseFloat(c[gi]), v = parseFloat(c[ii]);
    if (fin(g) && fin(v)) dhByDate.set(c[0], "G_" + band(g) + "/I_" + band(v));
  }
}
const ALLMOS = [...dhByDate.keys()].filter((d) => d >= "1966-03-01" && d <= "2026-08-01").sort();
function timeline(confirm, lo) {
  const out = [];
  for (let i = 0; i < ALLMOS.length; i++) {
    const m = ALLMOS[i];
    if (m < lo) continue;
    let st;
    if (confirm) {
      const a = dhByDate.get(ALLMOS[i - 1]), b = dhByDate.get(ALLMOS[i - 2]);
      if (a === undefined || b === undefined) continue;
      st = a === b ? a : null;
    } else { st = dhByDate.get(ALLMOS[i - 1]); if (st === undefined) continue; }
    out.push({ date: m, dhState: st });
  }
  let last = null;
  for (const r of out) { if (r.dhState === null) r.dhState = last; else last = r.dhState; }
  return out.filter((r) => r.dhState !== null);
}
const tlB2 = timeline(true, "1966-05-01");

// ---------------------------------------------------------------- V6.6 timeline (verbatim)
const V66 = new Map();
{
  const t = readLF(`${G182}/tactical-timeline.csv`).trim().split("\n");
  const h = t[0].split(",");
  const si = h.indexOf("signal");
  for (const l of t.slice(1)) { const c = l.split(","); V66.set(c[0].slice(0, 7), c[si]); }
}
function prevMonth(d) {
  let y = +d.slice(0, 4), m = +d.slice(5, 7) - 1;
  if (m < 1) { m = 12; y--; }
  return String(y).padStart(4, "0") + "-" + String(m).padStart(2, "0") + "-01";
}

// ---------------------------------------------------------------- returns (verbatim #183)
function loadRet(rel) {
  const t = readLF(rel).trim().split("\n");
  const h = t[0].split(",").map((k) => k.trim());
  const m = new Map();
  for (const l of t.slice(1)) {
    const c = l.split(",");
    const r = {};
    h.forEach((k, j) => { r[k] = j === 0 ? c[j] : (c[j] === "" ? NaN : parseFloat(c[j])); });
    m.set(r.date.slice(0, 7), r);
  }
  return m;
}
const r174 = loadRet(`${G174}/nine-sleeve-monthly-returns.csv`);
const r176 = loadRet(`${G176}/hardened-monthly-returns.csv`);
const rPx = loadRet(`${G180}/proxy-monthly-returns.csv`);
function researchRet(sl, ym) {
  if (sl === "sp500") { const h = r176.get(ym)?.sp500_tr_hardened; if (fin(h)) return h; const f = r174.get(ym)?.sp500; return fin(f) ? f : NaN; }
  if (sl === "oil") { const v = r176.get(ym)?.oil_investable_return; return fin(v) ? v : NaN; }
  const v = sl === "cash" ? r174.get(ym)?.cash : r174.get(ym)?.[sl];
  return fin(v) ? v : NaN;
}
function implRet(sl, ym) {
  if (sl === "cash") return researchRet("cash", ym);
  const v = rPx.get(ym)?.[sl];
  return fin(v) ? v : NaN;
}

// ---------------------------------------------------------------- frozen overlay + control math (verbatim prereg)
function overlayW(base, signal, budget = BUDGET) {
  const w = { ...base };
  const eq = EQ.filter((s) => w[s] > 0);
  const E = eq.reduce((a, s) => a + w[s], 0);
  if (signal === "risk-on") {
    const head = eq.reduce((a, s) => a + (SCAP[s] - w[s]), 0);
    let add = Math.min(budget, Math.max(0, w.cash - CASH_MIN), CASH_MAX - E, head);
    add = Math.max(0, add);
    if (E > 0 && add > 0) for (const s of eq) { const take = Math.min((add * w[s]) / E, SCAP[s] - w[s]); w[s] += take; w.cash -= take; }
  } else if (signal === "risk-off") {
    const cut = Math.min(budget, E);
    if (E > 0 && cut > 0) { for (const s of eq) w[s] -= (cut * w[s]) / E; w.cash += cut; }
  }
  return w;
}
// C builder reads NO V6.6 signal (prereg section 5 code-path assert: no V66 ref here).
function constantW(base, d = D_PP) {
  const w = { ...base };
  const eq = EQ.filter((s) => w[s] > 0);
  const E = eq.reduce((a, s) => a + w[s], 0);
  const cut = Math.min(d, E);
  if (E > 0 && cut > 0) { for (const s of eq) w[s] -= (cut * w[s]) / E; w.cash += cut; }
  return w;
}

// ---------------------------------------------------------------- metrics (verbatim #183)
function downsideVol(rs) {
  const v = rs.filter(fin);
  if (!v.length) return NaN;
  return Math.sqrt(v.reduce((a, x) => a + Math.min(x, 0) ** 2, 0) / v.length) * Math.sqrt(12);
}
function metrics(R, C) {
  const idx = R.map((r, i) => (fin(r) && fin(C[i]) ? i : -1)).filter((i) => i >= 0);
  const Rs = idx.map((i) => R[i]), Cs = idx.map((i) => C[i]);
  const n = Rs.length;
  if (!n) return { n: 0 };
  const mm = Rs.reduce((a, x) => a + x, 0) / n;
  const sd = Math.sqrt(Rs.reduce((a, x) => a + (x - mm) ** 2, 0) / n);
  const comp = Rs.reduce((a, x) => a * (1 + x), 1), compC = Cs.reduce((a, x) => a * (1 + x), 1);
  const ex = Rs.map((r, i) => r - Cs[i]);
  const em = ex.reduce((a, x) => a + x, 0) / n;
  const esd = Math.sqrt(ex.reduce((a, x) => a + (x - em) ** 2, 0) / n);
  let peak = 1, dd = 0, cum = 1;
  for (const r of Rs) { cum *= 1 + r; peak = Math.max(peak, cum); dd = Math.min(dd, cum / peak - 1); }
  return {
    n, cagr: comp ** (12 / n) - 1, vol_ann: sd * Math.sqrt(12),
    cash_excess_ann: (comp / compC) ** (12 / n) - 1,
    sharpe_like: esd > 0 ? (em * 12) / (esd * Math.sqrt(12)) : NaN,
    maxdd: dd, worst_month: Math.min(...Rs),
    pos_frac: Rs.filter((r) => r > 0).length / n, downside_vol: downsideVol(Rs),
  };
}

// ---------------------------------------------------------------- frozen panel + A/B reproduction
const frozen = readLF(`${G183}/corrected-overlay-monthly.csv`).trim().split("\n");
const fH = frozen[0].split(",");
const fRows = frozen.slice(1).map((l) => { const c = l.split(","); const o = {}; fH.forEach((k, j) => o[k] = c[j]); return o; });
const panelTrad = fRows.filter((r) => r.panel === "tradable");
const panelRes = fRows.filter((r) => r.panel === "research");
if (panelTrad.length !== 232 || panelRes.length !== 232) { console.error("FAIL panel N"); process.exit(1); }
const panelDates = panelTrad.map((r) => r.date);
if (JSON.stringify(panelDates) !== JSON.stringify(panelRes.map((r) => r.date))) { console.error("FAIL panel dates differ"); process.exit(1); }
if (panelDates[0] !== "2007-02-01" || panelDates[231] !== "2026-08-01") { console.error("FAIL panel bounds"); process.exit(1); }
const dhMap = new Map(tlB2.map((r) => [r.date, r.dhState]));

// Recompute A_pre/B_pre/B_post weights-only + returns (tradable implRet), compare to frozen.
const rec = [];
{
  let prevWB = null;
  for (const d of panelDates) {
    const st = dhMap.get(d);
    const sig = V66.get(prevMonth(d).slice(0, 7));
    const base = SW.get(st);
    const ym = d.slice(0, 7);
    let pa = 0, oka = true;
    for (const s of ORDER.concat(["cash"])) {
      if (base[s] === 0) continue;
      const r = implRet(s, ym);
      if (!fin(r)) { oka = false; break; }
      pa += (base[s] / 100) * r;
    }
    const wB = overlayW(base, sig, BUDGET);
    let pb = 0, okb = true;
    for (const s of ORDER.concat(["cash"])) {
      if (wB[s] === 0) continue;
      const r = implRet(s, ym);
      if (!fin(r)) { okb = false; break; }
      pb += (wB[s] / 100) * r;
    }
    const toB = prevWB ? ORDER.concat(["cash"]).reduce((a, s) => a + Math.abs(wB[s] - prevWB[s]), 0) / 2 / 100 : 0;
    rec.push({ date: d, dh: st, sig, Apre: oka ? pa : NaN, Bpre: okb ? pb : NaN, Bpost: okb ? pb - toB * COST : NaN, toB, wA: base, wB });
    prevWB = { ...wB };
  }
}
{
  let mism = 0;
  for (let i = 0; i < 232; i++) {
    const f = panelTrad[i], r = rec[i];
    if (f.date !== r.date || f.dh_state !== r.dh || f.v66_signal !== r.sig) { console.error("FAIL panel identity " + r.date); process.exit(1); }
    for (const [fk, rv] of [["A", r.Apre], ["B", r.Bpre], ["C", r.Bpost]]) {
      const fv = parseFloat(f[fk]);
      if (!fin(fv) || !fin(rv) || Math.abs(fv - rv) > 1e-12) mism++;
    }
  }
  console.log("A/B reproduction mismatches (tol 1e-12):", mism);
  if (mism !== 0) { console.error("FAIL A/B reproduction"); process.exit(1); }
}

// ---------------------------------------------------------------- weights-only exposure freeze check (prereg section 4)
{
  let sA = 0, sB = 0, sAc = 0, sBc = 0;
  for (const r of rec) {
    sA += EQ.reduce((a, s) => a + r.wA[s], 0);
    sB += EQ.reduce((a, s) => a + r.wB[s], 0);
    sAc += r.wA.cash; sBc += r.wB.cash;
  }
  const Aeq = sA / 232, Beq = sB / 232;
  console.log("exposure Aeq", Aeq, "Beq", Beq, "d", Aeq - Beq);
  if (Math.abs(Aeq - 45.67784482758621) > 1e-9 || Math.abs(Beq - 42.62612068965516) > 1e-9) { console.error("FAIL exposure freeze"); process.exit(1); }
  if (Math.abs((Aeq - Beq) - D_PP) > 1e-12) { console.error("FAIL d freeze"); process.exit(1); }
}

// ---------------------------------------------------------------- build C control (no V66 read in weight path)
const ctrl = [];
{
  let prevWC = null;
  for (const r of rec) {
    const wC = constantW(r.wA);
    const ym = r.date.slice(0, 7);
    let pc = 0, okc = true;
    for (const s of ORDER.concat(["cash"])) {
      if (wC[s] === 0) continue;
      const v = implRet(s, ym);
      if (!fin(v)) { okc = false; break; }
      pc += (wC[s] / 100) * v;
    }
    const toC = prevWC ? ORDER.concat(["cash"]).reduce((a, s) => a + Math.abs(wC[s] - prevWC[s]), 0) / 2 / 100 : 0;
    ctrl.push({ ...r, wC, Cpre: okc ? pc : NaN, Cpost: okc ? pc - toC * COST : NaN, toC });
    prevWC = { ...wC };
  }
}
{
  const avgC = ctrl.reduce((a, r) => a + EQ.reduce((x, s) => x + r.wC[s], 0), 0) / 232;
  const avgB = rec.reduce((a, r) => a + EQ.reduce((x, s) => x + r.wB[s], 0), 0) / 232;
  console.log("exposure match |C-B| pp:", Math.abs(avgC - avgB));
  if (Math.abs(avgC - avgB) > 0.01) { console.error("FAIL exposure match"); process.exit(1); }
}

// ---------------------------------------------------------------- structural turnover + A_post
const toA = [];
{
  let prev = null;
  for (const r of rec) {
    const to = prev ? ORDER.concat(["cash"]).reduce((a, s) => a + Math.abs(r.wA[s] - prev[s]), 0) / 2 / 100 : 0;
    toA.push(to);
    prev = { ...r.wA };
  }
}
const Apre = rec.map((r) => r.Apre), Bpre = rec.map((r) => r.Bpre), Bpost = rec.map((r) => r.Bpost);
const Cpre = ctrl.map((r) => r.Cpre), Cpost = ctrl.map((r) => r.Cpost);
const Apost = Apre.map((v, i) => fin(v) ? v - toA[i] * COST : NaN);
const cash = rec.map((r) => implRet("cash", r.date.slice(0, 7)));

// ---------------------------------------------------------------- build D placebos (231 shifts)
const sigSeq = rec.map((r) => r.sig);
const dResults = [];
for (let k = 1; k <= 231; k++) {
  const sh = sigSeq.map((_, i) => sigSeq[(((i - k) % 232) + 232) % 232]);
  let prevW = null, pre = [], to = [];
  for (let i = 0; i < 232; i++) {
    const w = overlayW(rec[i].wA, sh[i], BUDGET);
    const ym = rec[i].date.slice(0, 7);
    let p = 0, ok = true;
    for (const s of ORDER.concat(["cash"])) {
      if (w[s] === 0) continue;
      const v = implRet(s, ym);
      if (!fin(v)) { ok = false; break; }
      p += (w[s] / 100) * v;
    }
    const t = prevW ? ORDER.concat(["cash"]).reduce((a, s) => a + Math.abs(w[s] - prevW[s]), 0) / 2 / 100 : 0;
    pre.push(ok ? p : NaN); to.push(t);
    prevW = { ...w };
  }
  const post = pre.map((v, i) => fin(v) ? v - to[i] * COST : NaN);
  const m = metrics(post, cash);
  dResults.push({ k, ...m, turnover_ann: to.filter(fin).reduce((a, x) => a + x, 0) / 232 * 12 });
}

// ---------------------------------------------------------------- ABC comparison (post-cost primary)
const mA = metrics(Apost, cash), mB = metrics(Bpost, cash), mC = metrics(Cpost, cash);
function avgWsum(rows, key) {
  return rows.reduce((a, r) => a + EQ.reduce((x, s) => x + r[key][s], 0), 0) / rows.length;
}
const avgEq = { A: avgWsum(rec.map((r) => ({ A: r.wA })), "A"), B: avgWsum(rec, "wB"), C: ctrl.reduce((a, r) => a + EQ.reduce((x, s) => x + r.wC[s], 0), 0) / 232 };
const avgCash = {
  A: rec.reduce((a, r) => a + r.wA.cash, 0) / 232,
  B: rec.reduce((a, r) => a + r.wB.cash, 0) / 232,
  C: ctrl.reduce((a, r) => a + r.wC.cash, 0) / 232,
};
const turnA = toA.filter(fin).reduce((a, x) => a + x, 0) / 232 * 12;
const turnB = rec.map((r) => r.toB).filter(fin).reduce((a, x) => a + x, 0) / 232 * 12;
const turnC = ctrl.map((r) => r.toC).filter(fin).reduce((a, x) => a + x, 0) / 232 * 12;
function corr(X, Y) {
  const idx = X.map((_, i) => (fin(X[i]) && fin(Y[i]) ? i : -1)).filter((i) => i >= 0);
  const xs = idx.map((i) => X[i]), ys = idx.map((i) => Y[i]);
  const mx = xs.reduce((a, x) => a + x, 0) / xs.length, my = ys.reduce((a, x) => a + x, 0) / ys.length;
  let co = 0, vx = 0, vy = 0;
  for (let i = 0; i < xs.length; i++) { co += (xs[i] - mx) * (ys[i] - my); vx += (xs[i] - mx) ** 2; vy += (ys[i] - my) ** 2; }
  return vx > 0 && vy > 0 ? co / Math.sqrt(vx * vy) : NaN;
}
const comparison = {
  A: { ...mA, turnover_ann: turnA, avg_equity: avgEq.A, avg_cash: avgCash.A },
  B: { ...mB, turnover_ann: turnB, avg_equity: avgEq.B, avg_cash: avgCash.B },
  C: { ...mC, turnover_ann: turnC, avg_equity: avgEq.C, avg_cash: avgCash.C },
  BmC: {
    cagr_pp: (mB.cagr - mC.cagr) * 100, vol_pp: (mB.vol_ann - mC.vol_ann) * 100,
    maxdd_pp: (mB.maxdd - mC.maxdd) * 100, worst_pp: (mB.worst_month - mC.worst_month) * 100,
    downside_pp: (mB.downside_vol - mC.downside_vol) * 100, sharpe: mB.sharpe_like - mC.sharpe_like,
    turnover_pp: (turnB - turnC) * 100, corr: corr(Bpost, Cpost),
  },
  BmA: {
    cagr_pp: (mB.cagr - mA.cagr) * 100, vol_pp: (mB.vol_ann - mA.vol_ann) * 100,
    maxdd_pp: (mB.maxdd - mA.maxdd) * 100, sharpe: mB.sharpe_like - mA.sharpe_like,
  },
};

// ---------------------------------------------------------------- ranks + percentiles
function pct(arr, q) {
  const a = arr.filter(fin).sort((x, y) => x - y);
  if (!a.length) return NaN;
  const pos = (q / 100) * (a.length - 1);
  const lo = Math.floor(pos), hi = Math.ceil(pos);
  return a[lo] + (a[hi] - a[lo]) * (pos - lo);
}
const rankOf = (v, arr, higherBetter) => higherBetter
  ? 100 * arr.filter((d) => d <= v).length / arr.length
  : 100 * arr.filter((d) => d >= v).length / arr.length;
const ranks = {
  cagr: rankOf(mB.cagr, dResults.map((d) => d.cagr), true),
  sharpe_like: rankOf(mB.sharpe_like, dResults.map((d) => d.sharpe_like), true),
  maxdd: rankOf(mB.maxdd, dResults.map((d) => d.maxdd), true),
  downside_vol: rankOf(mB.downside_vol, dResults.map((d) => d.downside_vol), false),
  worst_month: rankOf(mB.worst_month, dResults.map((d) => d.worst_month), true),
};
const dist = {};
for (const [k, hb] of [["cagr", 1], ["sharpe_like", 1], ["maxdd", 1], ["downside_vol", 0], ["worst_month", 1]]) {
  const arr = dResults.map((d) => d[k]);
  dist[k] = { median: pct(arr, 50), p10: pct(arr, 10), p25: pct(arr, 25), p75: pct(arr, 75), p90: pct(arr, 90), frac_B_beats: (hb ? rankOf(mB[k], arr, true) : rankOf(mB[k], arr, false)) };
}

// ---------------------------------------------------------------- segments / transitions / states (B vs C post-cost)
function cagrOf(a) { const v = a.filter(fin); return v.length ? v.reduce((x, y) => x * (1 + y), 1) ** (12 / v.length) - 1 : NaN; }
function ddOf(a) { const v = a.filter(fin); let peak = 1, dd = 0, cum = 1; for (const r of v) { cum *= 1 + r; peak = Math.max(peak, cum); dd = Math.min(dd, cum / peak - 1); } return v.length ? dd : NaN; }
const segBounds = [["pre2020", "2007-02-01", "2019-12-01"], ["y2020_2022", "2020-01-01", "2022-12-01"], ["post2023", "2023-01-01", "2026-08-01"]];
const segments = {};
for (const [name, lo, hi] of segBounds) {
  const idx = rec.map((r, i) => (r.date >= lo && r.date <= hi ? i : -1)).filter((i) => i >= 0);
  segments[name] = {
    n: idx.length,
    cagr_A: cagrOf(idx.map((i) => Apost[i])), cagr_B: cagrOf(idx.map((i) => Bpost[i])), cagr_C: cagrOf(idx.map((i) => Cpost[i])),
    contrib_BmC_pp: (cagrOf(idx.map((i) => Bpost[i])) - cagrOf(idx.map((i) => Cpost[i]))) * 100,
    contrib_BmA_pp: (cagrOf(idx.map((i) => Bpost[i])) - cagrOf(idx.map((i) => Apost[i]))) * 100,
  };
}
const chg = new Set();
for (let i = 1; i < 232; i++) if (rec[i].dh !== rec[i - 1].dh) chg.add(i);
const inWin = new Set();
for (const i of chg) for (let k = -3; k <= 3; k++) if (rec[i + k]) inWin.add(i + k);
{
  const inside = [], outside = [];
  rec.forEach((r, i) => { if (fin(Bpost[i]) && fin(Cpost[i])) (inWin.has(i) ? inside : outside).push(Bpost[i] - Cpost[i]); });
  var trans = { n_transitions: chg.size, n_inside: inside.length, n_outside: outside.length, mean_inside: inside.reduce((a, x) => a + x, 0) / inside.length, mean_outside: outside.reduce((a, x) => a + x, 0) / outside.length };
}
const states = {};
rec.forEach((r, i) => {
  states[r.dh] = states[r.dh] || { n: 0, A: [], B: [], C: [] };
  if (fin(Apost[i]) && fin(Bpost[i]) && fin(Cpost[i])) { states[r.dh].n++; states[r.dh].A.push(Apost[i]); states[r.dh].B.push(Bpost[i]); states[r.dh].C.push(Cpost[i]); }
});
const stateDiag = {};
for (const [k, v] of Object.entries(states)) {
  const mean = (a) => a.reduce((x, y) => x + y, 0) / a.length;
  const sd = (a) => { const m = mean(a); return Math.sqrt(a.reduce((x, y) => x + (y - m) ** 2, 0) / a.length) * Math.sqrt(12); };
  stateDiag[k] = {
    n: v.n, A_mean: mean(v.A), B_mean: mean(v.B), C_mean: mean(v.C),
    BmC_ann_pp: (cagrOf(v.B) - cagrOf(v.C)) * 100,
    B_vol: sd(v.B), C_vol: sd(v.C), B_down: downsideVol(v.B), C_down: downsideVol(v.C),
  };
}

// ---------------------------------------------------------------- gates S1-S5 + verdict (verbatim prereg section 8)
const S1 = mB.vol_ann < mA.vol_ann && mB.maxdd > mA.maxdd && mB.downside_vol < mA.downside_vol;
const S2 = (mB.sharpe_like - mC.sharpe_like) >= -0.02 && (mB.maxdd - mC.maxdd) * 100 >= -1.0;
const s3count = ["sharpe_like", "maxdd", "downside_vol", "worst_month"].filter((k) => ranks[k] >= 90).length;
const S3 = s3count >= 2;
const S3partial = ["sharpe_like", "maxdd", "downside_vol", "worst_month"].some((k) => ranks[k] >= 75);
const S4 = (turnB - turnC) * 100 <= 40.0;
const worstSeg = Math.min(...Object.values(segments).map((s) => s.contrib_BmC_pp).filter(fin));
const worstState = Math.min(...Object.values(stateDiag).filter((s) => s.n >= 12).map((s) => s.BmC_ann_pp).filter(fin));
const S5 = worstSeg >= -1.0 && worstState >= -3.0;
let verdict;
if (S1 && S2 && S3 && S4 && S5) verdict = "v66_overlay_specific_information_supported";
else if (!S1 || !S4 || !S5) verdict = "v66_overlay_not_supported_after_controls";
else if (S1 && S2 && S4 && S5 && !S3) verdict = "v66_overlay_risk_control_supported_but_timing_not_specific";
else if (S1 && S4 && S5 && (S2 || S3partial)) verdict = "v66_overlay_specificity_suggestive";
else verdict = "v66_overlay_not_supported_after_controls";

// ---------------------------------------------------------------- write outputs
fs.mkdirSync(GEN184, { recursive: true });
const W = (name, content) => fs.writeFileSync(path.join(GEN184, name), content);
const J = (o) => JSON.stringify(o, null, 2) + "\n";
W("manifest.json", J({
  issue: 184, branch: "research/issue-184-v66-overlay-specificity",
  required_base: REQUIRED_BASE, prereg: "6da9a3611c3b16b8e602711bd9f1e3f3678ceb6a",
  parents: PARENTS, panel: { first: "2007-02-01", last: "2026-08-01", n: 232, risk_on: 35, risk_off: 163, neutral: 34 },
  cost_primary: COST, budget_pp: BUDGET, d_pp: D_PP, n_placebos: 231,
  production_authorized: false,
}));
W("exposure.json", J({
  method: "weights-only (matrix + overlayW + B-2 states + V6.6 signals; no returns)",
  A_avg_equity: avgEq.A, B_avg_equity: avgEq.B, C_avg_equity: avgEq.C,
  A_avg_cash: avgCash.A, B_avg_cash: avgCash.B, C_avg_cash: avgCash.C,
  d_pp: (avgEq.A - avgEq.B), match_CmB_pp: (avgEq.C - avgEq.B),
}));
W("control-monthly.csv", "date,dh_state,v66_signal,A_pre,A_post,B_pre,B_post,C_pre,C_post,turnover_A,turnover_B,turnover_C\n" +
  rec.map((r, i) => [r.date, r.dh, r.sig, Apre[i], Apost[i], Bpre[i], Bpost[i], Cpre[i], Cpost[i], toA[i], r.toB, ctrl[i].toC].join(",")).join("\n") + "\n");
W("placebo-distribution.csv", "shift,cagr,vol_ann,sharpe_like,maxdd,worst_month,downside_vol,turnover_ann\n" +
  dResults.map((d) => [d.k, d.cagr, d.vol_ann, d.sharpe_like, d.maxdd, d.worst_month, d.downside_vol, d.turnover_ann].join(",")).join("\n") + "\n");
W("percentile-ranks.json", J({ B_post: { cagr: mB.cagr, sharpe_like: mB.sharpe_like, maxdd: mB.maxdd, downside_vol: mB.downside_vol, worst_month: mB.worst_month }, ranks, distribution: dist }));
W("comparison-ABC.json", J(comparison));
W("segment-diagnostics.json", J(segments));
W("transition-diagnostics.json", J(trans));
W("state-diagnostics.csv", "state,n,A_mean,B_mean,C_mean,BmC_ann_pp,B_vol,C_vol,B_down,C_down\n" +
  Object.entries(stateDiag).map(([k, v]) => [k, v.n, v.A_mean, v.B_mean, v.C_mean, v.BmC_ann_pp, v.B_vol, v.C_vol, v.B_down, v.C_down].join(",")).join("\n") + "\n");
W("summary.json", J({
  issue: 184, verdict, gates: { S1, S2, S3, s3count90: s3count, S3partial, S4, S5, worst_seg_BmC_pp: worstSeg, worst_state_BmC_pp: worstState },
  comparison, ranks, distribution: dist, segments, transition: trans,
  panel: { n: 232, first: "2007-02-01", last: "2026-08-01" },
  production_authorized: false,
}));
console.log("verdict:", verdict);
console.log("S1", S1, "S2", S2, "S3", S3, s3count, "S4", S4, "S5", S5, worstSeg, worstState);
console.log("ABC Sharpe:", mA.sharpe_like, mB.sharpe_like, mC.sharpe_like);
console.log("ABC MaxDD:", mA.maxdd, mB.maxdd, mC.maxdd);
console.log("ranks:", JSON.stringify(ranks));
