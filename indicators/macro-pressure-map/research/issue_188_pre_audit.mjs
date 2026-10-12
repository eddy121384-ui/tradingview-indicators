#!/usr/bin/env node
// Issue #188 — PRE-PREREG baseline audit (allowed: baseline reproduction +
// weights-only feasibility; NO candidate control/ablation/placebo performance).
// Run once, record numbers into the prereg, then commit prereg BEFORE any
// new outcome work.
import fs from "node:fs";
import path from "node:path";

const ROOT = process.cwd();
const RES = path.join(ROOT, "indicators/macro-pressure-map/research");
const fin = (x) => typeof x === "number" && Number.isFinite(x);
const readLF = (rel) => fs.readFileSync(path.join(RES, rel), "utf8").replace(/\r/g, "");

const ORDER = ["sp500", "nasdaq", "russell", "treasury2y", "treasury10y", "longtreasury", "gold", "oil"];
const EQ = ["sp500", "nasdaq", "russell"];
const FAM = { sp500: "equity", nasdaq: "equity", russell: "equity", treasury2y: "rates", treasury10y: "rates", longtreasury: "rates", gold: "real", oil: "real" };
const SCAP = { sp500: 35, nasdaq: 20, russell: 15, treasury2y: 15, treasury10y: 25, longtreasury: 15, gold: 12, oil: 8 };
const FCAP = { equity: 60, rates: 50, real: 15 };
const CMIN_BIAS = { low: 5, neutral: 10, high: 20 };
const BASE = { sp500: 25, nasdaq: 12, russell: 8, treasury2y: 8, treasury10y: 14, longtreasury: 8, gold: 6, oil: 4 };
const MULT = { 0: 0, Low: 0.5, Neutral: 1.0, High: 1.75 };
const CASH_MIN = 2, CASH_MAX = 60, COST = 0.0002;
const G174 = "generated/issue-174", G176 = "generated/issue-176", G177 = "generated/issue-177";
const G178 = "generated/issue-178", G180 = "generated/issue-180", G183 = "generated/issue-183";

// matrix + tiers + fixed cbias (verbatim #183)
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
const TIERS = {};
for (const l of readLF(`${G177}/policy-matrix.csv`).trim().split("\n").slice(1)) {
  const c = l.split(",");
  if (c[1] === "cash") continue;
  TIERS[c[0] + "|" + c[1]] = c[2];
}
const CB = {};
for (const l of readLF(`${G177}/cash-bias.csv`).trim().split("\n").slice(1)) {
  const c = l.split(",");
  CB[c[0]] = c[2];
}
function weightsFromPolicy(state, avail) {
  const raw = {};
  for (const s of ORDER) {
    const m = MULT[TIERS[state + "|" + s]];
    if (m === undefined || m === 0) continue;
    if (avail !== null && !avail.has(s)) continue;
    raw[s] = BASE[s] * m;
  }
  for (const s of Object.keys(raw)) if (raw[s] > SCAP[s]) raw[s] = SCAP[s];
  for (const fam of Object.keys(FCAP)) {
    const mem = Object.keys(raw).filter((s) => FAM[s] === fam);
    const sum = mem.reduce((a, s) => a + raw[s], 0);
    if (sum > FCAP[fam]) { const k = FCAP[fam] / sum; for (const s of mem) raw[s] *= k; }
  }
  const S = Object.values(raw).reduce((a, x) => a + x, 0);
  const minC = CMIN_BIAS[CB[state]];
  let cash;
  if (100 - S < minC) { const k = S > 0 ? (100 - minC) / S : 0; for (const s of Object.keys(raw)) raw[s] *= k; cash = minC; }
  else if (100 - S > CASH_MAX) { const k = S > 0 ? (100 - CASH_MAX) / S : 0; for (const s of Object.keys(raw)) raw[s] *= k; cash = CASH_MAX; }
  else cash = 100 - S;
  if (cash < CASH_MIN) cash = CASH_MIN;
  for (const s of Object.keys(raw)) { if (raw[s] > SCAP[s]) { cash += raw[s] - SCAP[s]; raw[s] = SCAP[s]; } }
  const out = {};
  for (const s of ORDER) out[s] = raw[s] ?? 0;
  out.cash = cash;
  return out;
}
const matrixW = (state, avail) => (ORDER.every((s) => avail.has(s)) ? { ...SW.get(state) } : weightsFromPolicy(state, avail));

// B-2 (verbatim)
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
const tlB2 = (() => {
  const out = [];
  for (let i = 0; i < ALLMOS.length; i++) {
    const m = ALLMOS[i];
    if (m < "1966-05-01") continue;
    const a = dhByDate.get(ALLMOS[i - 1]), b = dhByDate.get(ALLMOS[i - 2]);
    if (a === undefined || b === undefined) continue;
    out.push({ date: m, dhState: a === b ? a : null });
  }
  let last = null;
  for (const r of out) { if (r.dhState === null) r.dhState = last; else last = r.dhState; }
  return out.filter((r) => r.dhState !== null);
})();

// returns (verbatim)
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
function downsideVol(rs) {
  const v = rs.filter(fin);
  return v.length ? Math.sqrt(v.reduce((a, x) => a + Math.min(x, 0) ** 2, 0) / v.length) * Math.sqrt(12) : NaN;
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
  return { n, cagr: comp ** (12 / n) - 1, vol_ann: sd * Math.sqrt(12), sharpe_like: esd > 0 ? (em * 12) / (esd * Math.sqrt(12)) : NaN, maxdd: dd };
}

// ---- panels
const fStruct = readLF(`${G183}/corrected-structural-monthly.csv`).trim().split("\n");
const fH = fStruct[0].split(",");
const pmaxMonths = fStruct.slice(1).map((l) => {
  const c = l.split(","); const o = {};
  fH.forEach((k, j) => o[k] = c[j]);
  return { date: o.date, ym: o.date.slice(0, 7), state: o.alloc_state, frozen: parseFloat(o.port_ret) };
});
const dhMap = new Map(tlB2.map((r) => [r.date, r.dhState]));
console.log("P-MAX months:", pmaxMonths.length, pmaxMonths[0].date, "->", pmaxMonths[pmaxMonths.length - 1].date);
// P-FULL: 2000-09..2023-06 subset of B-2 with ALL sleeves available
const pfullMonths = tlB2.filter((m) => m.date >= "2000-09-01" && m.date <= "2023-06-01" && ORDER.every((s) => fin(researchRet(s, m.date.slice(0, 7)))));
console.log("P-FULL months:", pfullMonths.length, pfullMonths[0]?.date, "->", pfullMonths[pfullMonths.length - 1]?.date);
// P-ETF: strict 2006-06+
const petfMonths = tlB2.filter((m) => m.date >= "2006-06-01");
console.log("P-ETF months:", petfMonths.length, petfMonths[0]?.date, "->", petfMonths[petfMonths.length - 1]?.date);

// ---- baseline A reproduction per panel (DH corrected)
function runA(months, retFn, availFn) {
  const R = [], C = [], W = [];
  for (const m of months) {
    const ym = m.date.slice(0, 7);
    const avail = new Set(ORDER.filter((s) => fin(retFn(s, ym)) && fin(retFn("cash", ym))));
    const w = availFn(m.dhState ?? m.state, avail);
    let p = 0, ok = true;
    for (const s of ORDER.concat(["cash"])) {
      if (w[s] === 0) continue;
      const r = retFn(s, ym);
      if (!fin(r)) { ok = false; break; }
      p += (w[s] / 100) * r;
    }
    if (!ok) continue;
    R.push(p); C.push(retFn("cash", ym)); W.push(w);
  }
  return { R, C, W };
}
{
  const { R } = runA(pmaxMonths, researchRet, matrixW);
  let mism = 0;
  const fr = pmaxMonths.map((m) => m.frozen);
  for (let i = 0; i < R.length; i++) if (Math.abs(R[i] - fr[i]) > 1e-12) mism++;
  console.log("A/P-MAX reproduce: n =", R.length, "mismatches =", mism);
  const m = metrics(R, pmaxMonths.map((x) => researchRet("cash", x.ym)));
  console.log("A/P-MAX: cagr", m.cagr.toFixed(6), "vol", m.vol_ann.toFixed(6), "maxdd", m.maxdd.toFixed(6), "(expect 0.087547/-0.170381)");
}
{
  const { R, C } = runA(pfullMonths, researchRet, (st) => ({ ...SW.get(st) }));
  const m = metrics(R, C);
  console.log("A/P-FULL: n =", R.length, "cagr", m.cagr.toFixed(6), "vol", m.vol_ann.toFixed(6), "maxdd", m.maxdd.toFixed(6), "(expect 0.059342/0.071194/-0.170381)");
}
{
  // P-ETF baseline: #180 rule (frozen row + missing-proxy->cash), compare vs #183 impl file months
  const fI = readLF(`${G183}/corrected-implementation-monthly.csv`).trim().split("\n");
  const ih = fI[0].split(",");
  const imp = new Map(fI.slice(1).map((l) => { const c = l.split(","); const o = {}; ih.forEach((k, j) => o[k] = c[j]); return [o.date, o]; }));
  let mism = 0, n = 0;
  const R = [], C = [];
  for (const m of petfMonths) {
    const ym = m.date.slice(0, 7);
    const w = { ...SW.get(m.dhState) };
    let moved = 0;
    for (const s of ORDER) if (w[s] > 0 && !fin(implRet(s, ym))) { moved += w[s]; w[s] = 0; }
    w.cash += moved;
    let p = 0, ok = true;
    for (const s of ORDER.concat(["cash"])) {
      if (w[s] === 0) continue;
      const r = implRet(s, ym);
      if (!fin(r)) { ok = false; break; }
      p += (w[s] / 100) * r;
    }
    if (!ok) { console.log("ETF drop", m.date); continue; }
    R.push(p); C.push(implRet("cash", ym)); n++;
    const f = imp.get(m.date);
    if (f && Math.abs(p - parseFloat(f.impl_pre)) > 1e-12) mism++;
  }
  const mm = metrics(R, C);
  console.log("A/P-ETF: n =", n, "mismatches vs frozen impl_pre =", mism, "cagr", mm.cagr.toFixed(6), "vol", mm.vol_ann.toFixed(6), "maxdd", mm.maxdd.toFixed(6));
}
// ---- baseline B reproduction (static neutral, orig redistribution) P-MAX
{
  const R = [], C = [];
  for (const m of pmaxMonths) {
    const ym = m.ym;
    const av = ORDER.filter((s) => fin(researchRet(s, ym)));
    const availTot = av.reduce((a, s) => a + BASE[s], 0) + 15;
    const w = {};
    for (const s of ORDER) w[s] = av.includes(s) ? (BASE[s] / availTot) * 100 : 0;
    w.cash = (15 / availTot) * 100;
    let p = 0, ok = true;
    for (const s of ORDER.concat(["cash"])) {
      if (w[s] === 0) continue;
      const r = researchRet(s, ym);
      if (!fin(r)) { ok = false; break; }
      p += (w[s] / 100) * r;
    }
    if (!ok) continue;
    R.push(p); C.push(researchRet("cash", ym));
  }
  const m = metrics(R, C);
  console.log("B/P-MAX neutral-orig: n =", R.length, "cagr", m.cagr.toFixed(6), "vol", m.vol_ann.toFixed(6), "maxdd", m.maxdd.toFixed(6), "(expect 0.083311/0.081298/-0.240486)");
}
// ---- weights-only D averages per panel (DH applied target rows)
function avgW(months, wfn) {
  const acc = {};
  for (const s of ORDER.concat(["cash"])) acc[s] = 0;
  for (const m of months) {
    const w = wfn(m.dhState ?? m.state);
    for (const s of ORDER.concat(["cash"])) acc[s] += w[s];
  }
  for (const s of ORDER.concat(["cash"])) acc[s] /= months.length;
  return acc;
}
console.log("D-targets P-MAX:", JSON.stringify(avgW(pmaxMonths, (st) => ({ ...SW.get(st) })), (k, v) => typeof v === "number" ? +v.toFixed(3) : v));
console.log("D-targets P-FULL:", JSON.stringify(avgW(pfullMonths, (st) => ({ ...SW.get(st) })), (k, v) => typeof v === "number" ? +v.toFixed(3) : v));
console.log("D-targets P-ETF:", JSON.stringify(avgW(petfMonths, (st) => ({ ...SW.get(st) })), (k, v) => typeof v === "number" ? +v.toFixed(3) : v));
// ---- E1 projection legality (weights-only): state frequencies + rows
{
  const cnt = {};
  for (const m of pmaxMonths) { const s = dhMap.get(m.date) ?? m.state; cnt[s] = (cnt[s] || 0) + 1; }
  const G3 = ["G_Low", "G_Neutral", "G_High"], I3 = ["I_Low", "I_Neutral", "I_High"];
  for (const g of G3) {
    const rows = I3.map((i) => `${g}/${i}`);
    const tot = rows.reduce((a, r) => a + (cnt[r] || 0), 0);
    console.log("freq", g, rows.map((r) => `${r}:${cnt[r] || 0}`).join(" "), "tot", tot);
  }
  // growth-only row = freq-weighted avg of 3 inflation rows
  for (const g of G3) {
    const rows = I3.map((i) => `${g}/${i}`);
    const tot = rows.reduce((a, r) => a + (cnt[r] || 0), 0);
    const agg = {};
    for (const s of ORDER.concat(["cash"])) agg[s] = rows.reduce((a, r) => a + (cnt[r] || 0) / tot * SW.get(r)[s], 0);
    const sum = ORDER.concat(["cash"]).reduce((a, s) => a + agg[s], 0);
    const famE = EQ.reduce((a, s) => a + agg[s], 0);
    console.log("G-row", g, "sum", sum.toFixed(4), "E", famE.toFixed(2), "cash", agg.cash.toFixed(2), "oil", agg.oil.toFixed(2), "caps-ok", ORDER.every((s) => agg[s] <= SCAP[s] + 1e-9));
  }
  // inflation-only median projection over growth rows
  for (const i of I3) {
    const rows = G3.map((g) => `${g}/${i}`);
    const agg = {};
    for (const s of ORDER.concat(["cash"])) agg[s] = rows.map((r) => SW.get(r)[s]).sort((a, b) => a - b)[1];
    const zeroViol = [["G_Low/I_Low", "oil"], ["G_Neutral/I_High", "russell"], ["G_High/I_Low", "gold"]].filter(([dh, s]) => rows.includes(dh) && Math.abs(agg[s]) > 1e-9).map(([dh, s]) => dh + "/" + s);
    console.log("I-proj", i, "E", EQ.reduce((a, s) => a + agg[s], 0).toFixed(2), "cash", agg.cash.toFixed(2), "zero-viol(nonpolicy if any):", JSON.stringify(zeroViol), "caps-ok", ORDER.every((s) => agg[s] <= SCAP[s] + 1e-9));
  }
}
// ---- E2 feasibility (weights-only)
{
  const dur = { sp500: 25, nasdaq: 12, russell: 8, treasury2y: 8, treasury10y: 14, longtreasury: 8, gold: 6, oil: 4, cash: 15 };
  const def = { sp500: 25, nasdaq: 12, russell: 8, treasury2y: 10, treasury10y: 0, longtreasury: 0, gold: 10, oil: 5, cash: 30 };
  for (const [nm, w] of [["duration", dur], ["defense", def]]) {
    const E = EQ.reduce((a, s) => a + w[s], 0);
    const rates = ["treasury2y", "treasury10y", "longtreasury"].reduce((a, s) => a + w[s], 0);
    const real = w.gold + w.oil;
    const tot = ORDER.reduce((a, s) => a + w[s], 0) + w.cash;
    console.log("E2", nm, "E", E, "rates", rates, "real", real, "tot", tot,
      "caps-ok", ORDER.every((s) => w[s] <= SCAP[s] + 1e-9) && E <= 60 && rates <= 50 && real <= 15 + 1e-9);
  }
}
