#!/usr/bin/env node
// Issue #188 — edge-attribution builder: E0a baselines, E0b placebos, E1/E2,
// bootstrap, LOOO, stress. Frozen contract: issue-188-edge-attribution-prereg.md
// Post-prereg ONLY (prereg 0d28ba1). No model change. No V6.6. No optimizer.
// Parents read-only. All writes go to research/generated/issue-188/.
import fs from "node:fs";
import path from "node:path";

const ROOT = process.cwd();
const RES = path.join(ROOT, "indicators/macro-pressure-map/research");
const GEN188 = path.join(RES, "generated/issue-188");
const fin = (x) => typeof x === "number" && Number.isFinite(x);
const readLF = (rel) => fs.readFileSync(path.join(RES, rel), "utf8").replace(/\r/g, "");

// ---------------------------------------------------------------- frozen policy (verbatim #178/#183)
const ORDER = ["sp500", "nasdaq", "russell", "treasury2y", "treasury10y", "longtreasury", "gold", "oil"];
const EQ = ["sp500", "nasdaq", "russell"];
const FAM = { sp500: "equity", nasdaq: "equity", russell: "equity", treasury2y: "rates", treasury10y: "rates", longtreasury: "rates", gold: "real", oil: "real" };
const SCAP = { sp500: 35, nasdaq: 20, russell: 15, treasury2y: 15, treasury10y: 25, longtreasury: 15, gold: 12, oil: 8 };
const FCAP = { equity: 60, rates: 50, real: 15 };
const CMIN_BIAS = { low: 5, neutral: 10, high: 20 };
const BASE = { sp500: 25, nasdaq: 12, russell: 8, treasury2y: 8, treasury10y: 14, longtreasury: 8, gold: 6, oil: 4 };
const MULT = { 0: 0, Low: 0.5, Neutral: 1.0, High: 1.75 };
const CASH_MIN = 2, CASH_MAX = 60, COST2 = 0.0002;
const ERAS = [["E1", "1966-03-01", "1979-12-01"], ["E2", "1980-01-01", "2007-12-01"], ["E3", "2008-01-01", "2019-12-01"], ["E4", "2020-01-01", "2026-08-01"]];
const LOOO = [["1973-74", "1973-01", "1975-12"], ["2007-09", "2007-01", "2010-12"], ["2020", "2020-01", "2020-12"], ["2022", "2021-01", "2023-12"]];
const CRISES = [...LOOO, ["1987", "1987-01", "1988-12"], ["2000-02", "2000-01", "2003-12"]];

function loadMatrix() {
  const t = readLF("generated/issue-178/weight-matrix.csv").trim().split("\n");
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
for (const l of readLF("generated/issue-177/policy-matrix.csv").trim().split("\n").slice(1)) {
  const c = l.split(",");
  if (c[1] === "cash") continue;
  TIERS[c[0] + "|" + c[1]] = c[2];
}
const CB = {};
for (const l of readLF("generated/issue-177/cash-bias.csv").trim().split("\n").slice(1)) {
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
// static-redistribution availability (benchmark-consistent): zero missing, scale rest to 100
function redist(nominal, avail) {
  const w = {};
  let tot = 0;
  for (const s of ORDER.concat(["cash"])) {
    w[s] = avail.has(s) ? nominal[s] : 0;
    tot += w[s];
  }
  if (tot <= 0) return null;
  for (const s of ORDER.concat(["cash"])) w[s] = (w[s] / tot) * 100;
  return w;
}

// DH + B-2 (verbatim)
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
    out.push({ date: m, ym: m.slice(0, 7), dhState: a === b ? a : null });
  }
  let last = null;
  for (const r of out) { if (r.dhState === null) r.dhState = last; else last = r.dhState; }
  return out.filter((r) => r.dhState !== null);
})();

// returns (verbatim #183)
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
const r174 = loadRet("generated/issue-174/nine-sleeve-monthly-returns.csv");
const r176 = loadRet("generated/issue-176/hardened-monthly-returns.csv");
const rPx = loadRet("generated/issue-180/proxy-monthly-returns.csv");
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
function frenchRet(wEq, ym) {
  const e = r174.get(ym)?.sp500, b = r174.get(ym)?.treasury10y, c = r174.get(ym)?.cash;
  if (!fin(e) || !fin(b) || !fin(c)) return { r: NaN, c };
  return { r: wEq * e + (1 - wEq) * b, c };
}

// metrics (verbatim #183 + §6 extensions)
function downsideVol(rs) {
  const v = rs.filter(fin);
  return v.length ? Math.sqrt(v.reduce((a, x) => a + Math.min(x, 0) ** 2, 0) / v.length) * Math.sqrt(12) : NaN;
}
function drawdowns(R) {
  const v = R.filter(fin);
  const out = [];
  let peak = 1, cum = 1;
  for (const r of v) { cum *= 1 + r; peak = Math.max(peak, cum); out.push(cum / peak - 1); }
  return out;
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
  const dd = drawdowns(Rs);
  const ulcer = 100 * Math.sqrt(dd.reduce((a, d) => a + d * d, 0) / dd.length);
  const s = [...dd].sort((a, b) => a - b);
  const cut = s[Math.max(0, Math.ceil(0.05 * s.length) - 1)];
  const tail = dd.filter((d) => d <= cut);
  let worst12 = null;
  if (Rs.length >= 12) {
    worst12 = Infinity;
    for (let i = 0; i <= Rs.length - 12; i++) {
      let c = 1;
      for (let k = 0; k < 12; k++) c *= 1 + Rs[i + k];
      worst12 = Math.min(worst12, c - 1);
    }
  }
  let uw = 0, cur = 0, pk = 1, cm = 1;
  for (const r of Rs) { cm *= 1 + r; if (cm >= pk) { pk = cm; cur = 0; } else { cur++; uw = Math.max(uw, cur); } }
  return {
    n, cagr: comp ** (12 / n) - 1, vol_ann: sd * Math.sqrt(12),
    cash_excess_ann: (comp / compC) ** (12 / n) - 1,
    sharpe_like: esd > 0 ? (em * 12) / (esd * Math.sqrt(12)) : NaN,
    maxdd: Math.min(...dd), worst_month: Math.min(...Rs),
    pos_frac: Rs.filter((r) => r > 0).length / n, downside_vol: downsideVol(Rs),
    ulcer, upi: ulcer === 0 ? null : ((comp ** (12 / n) - 1) - (compC ** (12 / n) - 1)) * 100 / ulcer,
    cdar95: dd.length >= 20 ? (-100 * tail.reduce((a, d) => a + d, 0) / tail.length) : null,
    worst_roll12: worst12, underwater_mo: uw, underwater_censored: cur > 0,
  };
}
function mulberry32(seed) {
  let s = seed >>> 0;
  return () => {
    s = (s + 0x6d2b79f5) >>> 0;
    let t = s;
    t = Math.imul(t ^ (t >>> 15), t | 1);
    t ^= t + Math.imul(t ^ (t >>> 7), t | 61);
    return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
  };
}
const pctRank = (v, arr) => {
  const f = arr.filter(fin);
  if (!f.length || !fin(v)) return NaN;
  return (100 * (f.filter((d) => d < v).length + 0.5 * f.filter((d) => d === v).length)) / f.length;
};
const qp = (a, p) => {
  const v = a.filter(fin).sort((x, y) => x - y);
  if (!v.length) return null;
  const pos = (p / 100) * (v.length - 1), lo = Math.floor(pos), hi = Math.ceil(pos);
  return v[lo] + (v[hi] - v[lo]) * (pos - lo);
};
const med = (a) => qp(a, 50);

// ---------------------------------------------------------------- panels (frozen §1)
const fStruct = readLF("generated/issue-183/corrected-structural-monthly.csv").trim().split("\n");
const fH = fStruct[0].split(",");
const PMAX = fStruct.slice(1).map((l) => {
  const c = l.split(","); const o = {};
  fH.forEach((k, j) => o[k] = c[j]);
  return { date: o.date, ym: o.date.slice(0, 7), frozen: parseFloat(o.port_ret) };
});
const dhMap = new Map(tlB2.map((r) => [r.date, r.dhState]));
for (const m of PMAX) m.dhState = dhMap.get(m.date) ?? null;
const PFULL = tlB2.filter((m) => m.date >= "2000-09-01" && m.date <= "2023-06-01" && ORDER.every((s) => fin(researchRet(s, m.date.slice(0, 7))))).map((m) => ({ date: m.date, ym: m.date.slice(0, 7), dhState: m.dhState }));
const PETF = tlB2.filter((m) => m.date >= "2006-06-01").map((m) => ({ date: m.date, ym: m.date.slice(0, 7), dhState: m.dhState }));
console.log("panels:", PMAX.length, PFULL.length, PETF.length, "(expect 721/274/240)");

// generic applier: weights + returns -> pre-cost; NaN if held sleeve missing
function applyRet(w, ym, retFn) {
  let p = 0;
  for (const s of ORDER.concat(["cash"])) {
    if (w[s] === 0) continue;
    const r = retFn(s, ym);
    if (!fin(r)) return NaN;
    p += (w[s] / 100) * r;
  }
  return p;
}
const grossOf = (w) => ORDER.concat(["cash"]).reduce((a, s) => a + w[s], 0);
// tactical leg runner (target changes; turnover on final applied weights)
function runTactical(months, retFn, targetFn, availFn, costRate) {
  const rows = [];
  let prev = null;
  for (const m of months) {
    const avail = new Set(ORDER.filter((s) => fin(retFn(s, m.ym)) && fin(retFn("cash", m.ym))));
    const w = targetFn(m, avail);
    if (!w) continue;
    const p = applyRet(w, m.ym, retFn);
    if (!fin(p)) continue; // dropped month (same-month rule for all legs using this runner)
    const to = prev ? ORDER.concat(["cash"]).reduce((a, s) => a + Math.abs(w[s] - prev[s]), 0) / 2 / 100 : 0;
    rows.push({ date: m.date, ym: m.ym, dhState: m.dhState, w: { ...w }, pre: p, to, post: p - to * costRate });
    prev = { ...w };
  }
  return rows;
}
// fixed leg runner (constant or per-month nominal; drift-rebalance turnover)
function runFixed(months, retFn, nominal, costRate) {
  const nomFn = typeof nominal === "function" ? nominal : () => nominal;
  const rows = [];
  let prevT = null;
  for (const m of months) {
    const avail = new Set(ORDER.filter((s) => fin(retFn(s, m.ym)) && fin(retFn("cash", m.ym))));
    const w = redist(nomFn(m), new Set([...avail, "cash"]));
    if (!w) continue;
    const p = applyRet(w, m.ym, retFn);
    if (!fin(p)) continue;
    // drifted weights from prev target grown by returns
    let to = 0;
    if (prevT) {
      const drift = {};
      let tot = 0;
      for (const s of ORDER.concat(["cash"])) {
        const r = retFn(s, prevT.ym);
        drift[s] = fin(r) ? prevT.w[s] * (1 + r) : prevT.w[s];
        tot += drift[s];
      }
      for (const s of ORDER.concat(["cash"])) drift[s] = (drift[s] / tot) * 100;
      to = ORDER.concat(["cash"]).reduce((a, s) => a + Math.abs(w[s] - drift[s]), 0) / 2 / 100;
    }
    rows.push({ date: m.date, ym: m.ym, dhState: m.dhState, w: { ...w }, pre: p, to, post: p - to * costRate });
    prevT = { w: { ...w }, ym: m.ym };
  }
  return rows;
}
const cashOf = (rows, retFn) => rows.map((r) => retFn("cash", r.ym));
const perfOf = (rows, retFn, rates = [COST2]) => {
  const pre = rows.map((r) => r.pre), cash = cashOf(rows, retFn);
  const mPre = metrics(pre, cash);
  const out = { n: rows.length, pre: mPre, turn_ann: rows.map((r) => r.to).reduce((a, x) => a + x, 0) / rows.length * 12 };
  for (const rt of rates) {
    const post = rows.map((r) => r.pre - r.to * rt);
    out["post_" + Math.round(rt * 10000) + "bp"] = metrics(post, cash);
  }
  return out;
};
const avgW = (rows) => {
  const acc = {};
  for (const s of ORDER.concat(["cash"])) acc[s] = 0;
  for (const r of rows) for (const s of ORDER.concat(["cash"])) acc[s] += r.w[s];
  for (const s of ORDER.concat(["cash"])) acc[s] /= rows.length;
  return acc;
};
const eqOf = (w) => EQ.reduce((a, s) => a + w[s], 0);

// ---------------------------------------------------------------- E0a legs (frozen §2)
// A: DH corrected — PMAX / PFULL (research) / PETF (ETF impl rule)
const legA_MAX = runTactical(PMAX, researchRet, (m, av) => matrixW(m.dhState, av));
{
  let mism = 0;
  for (let i = 0; i < legA_MAX.length; i++)
    if (Math.abs(legA_MAX[i].pre - PMAX[i].frozen) > 1e-12) mism++;
  console.log("A/P-MAX reproduce: n =", legA_MAX.length, "mismatches =", mism);
  if (mism !== 0 || legA_MAX.length !== 721) { console.error("FAIL A P-MAX"); process.exit(1); }
}
const legA_FULL = runTactical(PFULL, researchRet, (m) => ({ ...SW.get(m.dhState) }));
console.log("A/P-FULL n =", legA_FULL.length, "(expect 274)");
const legA_ETF = runTactical(PETF, implRet, (m) => {
  const w = { ...SW.get(m.dhState) };
  let moved = 0;
  for (const s of ORDER) if (w[s] > 0 && !fin(implRet(s, m.ym))) { moved += w[s]; w[s] = 0; }
  w.cash += moved;
  return w;
});
{
  const fI = readLF("generated/issue-183/corrected-implementation-monthly.csv").trim().split("\n");
  const ih = fI[0].split(",");
  const imp = new Map(fI.slice(1).map((l) => { const c = l.split(","); const o = {}; ih.forEach((k, j) => o[k] = c[j]); return [o.date, parseFloat(o.impl_pre)]; }));
  let mism = 0;
  for (const r of legA_ETF) if (imp.has(r.date) && Math.abs(r.pre - imp.get(r.date)) > 1e-12) mism++;
  console.log("A/P-ETF reproduce: n =", legA_ETF.length, "mismatches =", mism, "(expect 240/0)");
  if (mism !== 0 || legA_ETF.length !== 240) { console.error("FAIL A P-ETF"); process.exit(1); }
}
// B: static neutral + orig redistribution
const NEUTRAL = { ...BASE, cash: 15 };
const legB_MAX = runFixed(PMAX, researchRet, NEUTRAL, COST2);
const legB_FULL = runFixed(PFULL, researchRet, NEUTRAL, COST2);
const legB_ETF = runFixed(PETF, implRet, NEUTRAL, COST2);
// cash-rule availability: unavailable held weight -> Cash (100% maintained)
function cashRule(nominal, m, retFn) {
  const w = { ...nominal };
  let moved = 0;
  for (const s of ORDER) {
    if (w[s] > 0 && (!fin(retFn(s, m.ym)) || !fin(retFn("cash", m.ym)))) { moved += w[s]; w[s] = 0; }
  }
  w.cash += moved;
  return w;
}
// C: static neutral + cash rule (fixed leg w/ availability-varying target + drift turnover)
const legC_MAX = runFixed(PMAX, researchRet, (m) => cashRule(NEUTRAL, m, researchRet), COST2);
const legC_FULL = runFixed(PFULL, researchRet, (m) => cashRule(NEUTRAL, m, researchRet), COST2);
const legC_ETF = runFixed(PETF, implRet, (m) => cashRule(NEUTRAL, m, implRet), COST2);
// A': DH targets + hypothetical cash rule (labeled HYPOTHETICAL)
const legAp_MAX = runTactical(PMAX, researchRet, (m) => cashRule({ ...SW.get(m.dhState) }, m, researchRet));
// D: fixed time-average DH targets + redistribution (per panel; weights-only assert first)
function panelAvg(panel) {
  const acc = {};
  for (const s of ORDER.concat(["cash"])) acc[s] = 0;
  for (const m of panel) {
    const w = SW.get(m.dhState);
    for (const s of ORDER.concat(["cash"])) acc[s] += w[s];
  }
  for (const s of ORDER.concat(["cash"])) acc[s] /= panel.length;
  return acc;
}
const DAVG = { MAX: panelAvg(PMAX), FULL: panelAvg(PFULL), ETF: panelAvg(PETF) };
const DPREREG = {
  MAX: { sp500: 25.044, nasdaq: 11.623, russell: 6.143, treasury2y: 7.639, treasury10y: 11.002, longtreasury: 7.631, gold: 4.835, oil: 3.592, cash: 22.491 },
  FULL: { sp500: 25.317, nasdaq: 12.152, russell: 6.308, treasury2y: 7.037, treasury10y: 10.826, longtreasury: 6.796, gold: 5.314, oil: 3.414, cash: 22.838 },
  ETF: { sp500: 26.228, nasdaq: 12.253, russell: 6.907, treasury2y: 7.559, treasury10y: 11.267, longtreasury: 7.467, gold: 5.161, oil: 3.436, cash: 19.721 },
};
for (const k of ["MAX", "FULL", "ETF"]) {
  const bad = ORDER.concat(["cash"]).filter((s) => Math.abs(DAVG[k][s] - DPREREG[k][s]) > 0.001);
  console.log("D-targets", k, bad.length ? "MISMATCH " + bad.join(",") : "match prereg ±0.001");
  if (bad.length) { console.error("FAIL D targets"); process.exit(1); }
}
const legD_MAX = runFixed(PMAX, researchRet, DAVG.MAX, COST2);
const legD_FULL = runFixed(PFULL, researchRet, DAVG.FULL, COST2);
const legD_ETF = runFixed(PETF, implRet, DAVG.ETF, COST2);
for (const [nm, L, key] of [["MAX", legD_MAX, "MAX"], ["FULL", legD_FULL, "FULL"], ["ETF", legD_ETF, "ETF"]]) {
  const panel = key === "MAX" ? PMAX : key === "FULL" ? PFULL : PETF;
  void panel;
  const aD = avgW(L), aA = avgW(key === "MAX" ? legA_MAX.filter((r) => L.some((x) => x.date === r.date)) : key === "FULL" ? legA_FULL : legA_ETF);
  const d = Math.abs(eqOf(aD) - eqOf(aA));
  console.log("D exposure |D-DH|", nm, d.toFixed(4), "DH_eq", eqOf(aA).toFixed(3), "D_eq", eqOf(aD).toFixed(3), d <= 0.05 ? "OK" : "MISS-reported");
  if (d > 0.05) console.log("WARN D tolerance miss on " + nm + " — availability-rule gap disclosed (§2), G6 read with contamination note");
}
// E: risk-matched neutral+Cash (k per panel; NON-EXECUTABLE label)
const EK = { MAX: 0.871443, FULL: 0.892116, ETF: 0.939216 };
function scaledNeutral(k) {
  const w = {};
  for (const s of ORDER) w[s] = BASE[s] * k;
  w.cash = 15 * k + 100 * (1 - k);
  return w;
}
const legE_MAX = runFixed(PMAX, researchRet, scaledNeutral(EK.MAX), COST2);
const legE_FULL = runFixed(PFULL, researchRet, scaledNeutral(EK.FULL), COST2);
const legE_ETF = runFixed(PETF, implRet, scaledNeutral(EK.ETF), COST2);
// F: 60/40 French/10Y
const F6040 = { sp500: 60, nasdaq: 0, russell: 0, treasury2y: 0, treasury10y: 40, longtreasury: 0, gold: 0, oil: 0, cash: 0 };
function frenchLeg(months) {
  const rows = [];
  for (const m of months) {
    const e = r174.get(m.ym)?.sp500, b = r174.get(m.ym)?.treasury10y, c = r174.get(m.ym)?.cash;
    if (!fin(e) || !fin(b) || !fin(c)) continue;
    rows.push({ date: m.date, ym: m.ym, dhState: m.dhState, w: { ...F6040 }, pre: 0.6 * e + 0.4 * b, to: 0, post: 0 });
  }
  // drift-rebalance turnover
  for (let i = 1; i < rows.length; i++) {
    const pe = r174.get(rows[i - 1].ym)?.sp500, pb = r174.get(rows[i - 1].ym)?.treasury10y;
    const de = 60 * (1 + pe), db = 40 * (1 + pb), t = de + db;
    rows[i].to = (Math.abs(60 - (de / t) * 100) + Math.abs(40 - (db / t) * 100)) / 2 / 100;
  }
  for (const r of rows) r.post = r.pre - r.to * COST2;
  return rows;
}
const legF_MAX = frenchLeg(PMAX);
const legF_FULL = frenchLeg(PFULL);
console.log("legs A-F built:", legA_MAX.length, legB_MAX.length, legC_MAX.length, legAp_MAX.length, legD_MAX.length, legE_MAX.length, legF_MAX.length);

// ---------------------------------------------------------------- E1 ablations (frozen §4)
const isIHigh = (m) => (m.dhState || "").split("/")[1] === "I_High";
const gBand = (m) => (m.dhState || "").split("/")[0].slice(2);
function e1inflTarget(m) {
  const w = { ...NEUTRAL };
  if (isIHigh(m)) {
    const mv = w.treasury2y + w.treasury10y + w.longtreasury;
    w.treasury2y = 0; w.treasury10y = 0; w.longtreasury = 0;
    w.cash += mv;
  }
  return w;
}
// growth-only rows: frozen P-MAX frequency aggregates (weights-only, prereg §4)
const GFREQ = {
  G_Low: { "G_Low/I_Low": 60, "G_Low/I_Neutral": 49, "G_Low/I_High": 84 },
  G_Neutral: { "G_Neutral/I_Low": 120, "G_Neutral/I_Neutral": 87, "G_Neutral/I_High": 123 },
  G_High: { "G_High/I_Low": 55, "G_High/I_Neutral": 81, "G_High/I_High": 62 },
};
const GROW = {};
for (const g of Object.keys(GFREQ)) {
  const rows = Object.keys(GFREQ[g]);
  const tot = rows.reduce((a, r) => a + GFREQ[g][r], 0);
  const agg = {};
  for (const s of ORDER.concat(["cash"])) agg[s] = rows.reduce((a, r) => a + (GFREQ[g][r] / tot) * SW.get(r)[s], 0);
  GROW[g] = agg;
}
// inflation median projection (I_Low/I_High instances NONPOLICY — zero-cell breach)
const IPROJ = {}, IPROJ_NONPOLICY = {};
for (const ib of ["I_Low", "I_Neutral", "I_High"]) {
  const rows = ["G_Low", "G_Neutral", "G_High"].map((g) => `${g}/${ib}`);
  const agg = {};
  for (const s of ORDER.concat(["cash"])) agg[s] = rows.map((r) => SW.get(r)[s]).sort((a, b) => a - b)[1];
  IPROJ[ib] = agg;
  IPROJ_NONPOLICY[ib] = [["G_Low/I_Low", "oil"], ["G_Neutral/I_High", "russell"], ["G_High/I_Low", "gold"]]
    .some(([dh, s]) => rows.includes(dh) && Math.abs(agg[s]) > 1e-9);
}
// NOTE: E1 legs use redistribution availability (benchmark-consistent full
// coverage), NOT tactical subset drops — runFixed with per-month nominal.
function runE1redist(panel, retFn, nomFn) {
  return runFixed(panel, retFn, nomFn, COST2);
}
const E1_MAX_R = runE1redist(PMAX, researchRet, (m) => e1inflTarget(m));
const E1_MAX_G = runE1redist(PMAX, researchRet, (m) => ({ ...GROW["G_" + gBand(m)] }));
const E1_MAX_P = runE1redist(PMAX, researchRet, (m) => ({ ...IPROJ["I_" + (m.dhState || "").split("/")[1].slice(2)] }));
const E1_ETF_R = runE1redist(PETF, implRet, (m) => e1inflTarget(m));
const E1_ETF_G = runE1redist(PETF, implRet, (m) => ({ ...GROW["G_" + gBand(m)] }));
console.log("E1 built:", E1_MAX_R.length, E1_MAX_G.length, E1_MAX_P.length, E1_ETF_R.length, E1_ETF_G.length);
for (const [nm, L, exp] of [["E1R-MAX", E1_MAX_R, 721], ["E1G-MAX", E1_MAX_G, 721], ["E1P-MAX", E1_MAX_P, 721], ["E1R-ETF", E1_ETF_R, 240], ["E1G-ETF", E1_ETF_G, 240]]) {
  if (L.length !== exp) { console.error("FAIL leg length " + nm + ": " + L.length + " != " + exp); process.exit(1); }
}
// E1 exposure controls (D-method, same availability)
function ctrlFor(rows, retFn) {
  const avg = avgW(rows);
  return runFixed(rows.map((r) => ({ date: r.date, ym: r.ym, dhState: r.dhState })), retFn, avg, COST2);
}
const E1C_MAX_R = ctrlFor(E1_MAX_R, researchRet);
const E1C_MAX_G = ctrlFor(E1_MAX_G, researchRet);

// ---------------------------------------------------------------- E2 fixed-Equity basket (frozen §5 TEST CANDIDATE)
const E2_DUR = { sp500: 25, nasdaq: 12, russell: 8, treasury2y: 8, treasury10y: 14, longtreasury: 8, gold: 6, oil: 4, cash: 15 };
const E2_DEF = { sp500: 25, nasdaq: 12, russell: 8, treasury2y: 10, treasury10y: 0, longtreasury: 0, gold: 10, oil: 5, cash: 30 };
const E2_MAX = runTactical(PMAX, researchRet, (m) => ({ ...(isIHigh(m) ? E2_DEF : E2_DUR) }));
const E2_ETF = runTactical(PETF, implRet, (m) => ({ ...(isIHigh(m) ? E2_DEF : E2_DUR) }));
console.log("E2 built:", E2_MAX.length, E2_ETF.length);

// ---------------------------------------------------------------- performance assembly (frozen §6)
function legPerf(rows, retFn) {
  const pre = rows.map((r) => r.pre), cash = rows.map((r) => retFn("cash", r.ym));
  const out = { n: rows.length, gross: metrics(pre, cash), turn_ann: rows.map((r) => r.to).reduce((a, x) => a + x, 0) / rows.length * 12 };
  for (const [nm, rt] of [["net2bp", COST2], ["net10bp", 0.001], ["net25bp", 0.0025]]) {
    const post = rows.map((r) => r.pre - r.to * rt);
    out[nm] = metrics(post, cash);
  }
  const aw = avgW(rows);
  out.avgW = aw;
  out.avgEq = eqOf(aw);
  return out;
}
function common_pair(R1, R2) {
  const m2 = new Map(R2.map((r) => [r.date, r]));
  const a = [], b = [];
  for (const r of R1) if (m2.has(r.date)) { a.push(r); b.push(m2.get(r.date)); }
  return [a, b];
}
function incrOf(Rd, Rc, retFn) {
  const [a, b] = common_pair(Rd, Rc);
  const A = a.map((r) => r.pre - r.to * COST2), B = b.map((r) => r.pre - r.to * COST2);
  const cash = a.map((r) => retFn("cash", r.ym));
  const mA = metrics(A, cash), mB = metrics(B, cash);
  return {
    n: a.length,
    cagr_pp: (mA.cagr - mB.cagr) * 100, vol_pp: (mA.vol_ann - mB.vol_ann) * 100,
    sharpe: mA.sharpe_like - mB.sharpe_like, maxdd_pp: (mA.maxdd - mB.maxdd) * 100,
    worst_pp: (mA.worst_month - mB.worst_month) * 100, ulcer_diff: mA.ulcer - mB.ulcer,
    mA, mB,
  };
}
const P = {
  MAX: {
    A: legPerf(legA_MAX, researchRet), B: legPerf(legB_MAX, researchRet), C: legPerf(legC_MAX, researchRet),
    Ap: legPerf(legAp_MAX, researchRet), D: legPerf(legD_MAX, researchRet), E: legPerf(legE_MAX, researchRet),
    F: legPerf(legF_MAX, researchRet),
    E1R: legPerf(E1_MAX_R, researchRet), E1G: legPerf(E1_MAX_G, researchRet), E1P: legPerf(E1_MAX_P, researchRet),
    E1CR: legPerf(E1C_MAX_R, researchRet), E1CG: legPerf(E1C_MAX_G, researchRet),
    E2: legPerf(E2_MAX, researchRet),
  },
  FULL: {
    A: legPerf(legA_FULL, researchRet), B: legPerf(legB_FULL, researchRet), C: legPerf(legC_FULL, researchRet),
    D: legPerf(legD_FULL, researchRet), E: legPerf(legE_FULL, researchRet), F: legPerf(legF_FULL, researchRet),
  },
  ETF: {
    A: legPerf(legA_ETF, implRet), B: legPerf(legB_ETF, implRet), C: legPerf(legC_ETF, implRet),
    D: legPerf(legD_ETF, implRet), E: legPerf(legE_ETF, implRet),
    E1R: legPerf(E1_ETF_R, implRet), E1G: legPerf(E1_ETF_G, implRet), E2: legPerf(E2_ETF, implRet),
  },
};
console.log("perf assembled. A/C MAX n:", P.MAX.A.n, P.MAX.C.n);

// ---------------------------------------------------------------- E0b placebos (frozen §3; joint state-sequence shifts)
function placeboRun(panel, retFn, tag) {
  const states = panel.map((m) => m.dhState);
  const N = states.length;
  const availOf = (m) => new Set(ORDER.filter((s) => fin(retFn(s, m.ym)) && fin(retFn("cash", m.ym))));
  // genuine applied path (DH rule) on this panel grid
  const gen = [];
  {
    let prev = null;
    for (const m of panel) {
      const w = matrixW(m.dhState, availOf(m));
      const p = applyRet(w, m.ym, retFn);
      if (!fin(p)) { gen.push(null); continue; }
      const to = prev ? ORDER.concat(["cash"]).reduce((a, s) => a + Math.abs(w[s] - prev[s]), 0) / 2 / 100 : 0;
      gen.push({ w, pre: p, to, post: p - to * COST2 });
      prev = { ...w };
    }
  }
  const genValid = gen.map((g) => g !== null);
  const res = [];
  for (let k = 1; k < N; k++) {
    const rows = [];
    let prev = null, mm = 0, pp = 0;
    for (let i = 0; i < N; i++) {
      const st = states[(((i - k) % N) + N) % N];
      const m = panel[i];
      const av = availOf(m);
      const w = matrixW(st, av);
      const p = applyRet(w, m.ym, retFn);
      const gv = genValid[i];
      if (!fin(p)) { if (gv) mm++; continue; }
      if (!gv) mm++;
      if (st !== m.dhState && av.size < ORDER.length) pp++;
      const to = prev ? ORDER.concat(["cash"]).reduce((a, s) => a + Math.abs(w[s] - prev[s]), 0) / 2 / 100 : 0;
      rows.push({ pre: p, to, post: p - to * COST2, cash: retFn("cash", m.ym) });
      prev = { ...w };
    }
    const pre = rows.map((r) => r.pre), post = rows.map((r) => r.post), cash = rows.map((r) => r.cash);
    const mp = metrics(post, cash);
    res.push({ k, n: rows.length, mm, pp, sharpe: mp.sharpe_like, cagr: mp.cagr, maxdd: mp.maxdd, ulcer: mp.ulcer, roll12: mp.worst_roll12, cdar: mp.cdar95, uw: mp.underwater_mo });
  }
  // mismatch accounting on the genuine grid: months where availability is partial
  // (any shift landing there is exposure-approximate) + max validity spread
  const nValid = gen.filter((g) => g !== null).length;
  const validSpread = Math.max(...res.map((r) => Math.abs(r.n - nValid)));
  const mmMax = Math.max(...res.map((r) => r.mm));
  const confounded = (mmMax / N > 0.05);
  return { tag, N, nValid, shifts: res, mmMax, validSpread, confounded };
}
const PL_MAX = placeboRun(PMAX, researchRet, "P-MAX");
const PL_FULL = placeboRun(PFULL, researchRet, "P-FULL");
const PL_ETF = placeboRun(PETF, implRet, "P-ETF");
console.log("placebos:", PL_MAX.N - 1, PL_FULL.N - 1, PL_ETF.N - 1, "confounded:", PL_MAX.confounded, PL_FULL.confounded, PL_ETF.confounded, "mmMax:", PL_MAX.mmMax, PL_FULL.mmMax, PL_ETF.mmMax);
function pctsFor(PL, genuineNet, cash) {
  const mg = metrics(genuineNet, cash);
  const S = PL.shifts;
  return {
    sharpe: pctRank(mg.sharpe_like, S.map((d) => d.sharpe)),
    cagr: pctRank(mg.cagr, S.map((d) => d.cagr)),
    maxdd: pctRank(mg.maxdd, S.map((d) => d.maxdd)),
    ulcer: pctRank(-mg.ulcer, S.map((d) => -d.ulcer)),
    roll12: pctRank(mg.worst_roll12, S.map((d) => d.roll12)),
    cdar: pctRank(-(mg.cdar95 ?? NaN), S.map((d) => -(d.cdar ?? NaN))),
    uw: pctRank(-mg.underwater_mo, S.map((d) => -d.uw)),
    genuine: { sharpe: mg.sharpe_like, cagr: mg.cagr, maxdd: mg.maxdd, ulcer: mg.ulcer, roll12: mg.worst_roll12, cdar: mg.cdar95, uw: mg.underwater_mo },
  };
}

// ---------------------------------------------------------------- genuine percentiles (DH net-2bp paths)
const PCT = {
  MAX: pctsFor(PL_MAX, legA_MAX.map((r) => r.pre - r.to * COST2), legA_MAX.map((r) => researchRet("cash", r.ym))),
  FULL: pctsFor(PL_FULL, legA_FULL.map((r) => r.pre - r.to * COST2), legA_FULL.map((r) => researchRet("cash", r.ym))),
  ETF: pctsFor(PL_ETF, legA_ETF.map((r) => r.pre - r.to * COST2), legA_ETF.map((r) => implRet("cash", r.ym))),
};
console.log("percentiles MAX:", JSON.stringify({ sharpe: PCT.MAX.sharpe, maxdd: PCT.MAX.maxdd, cagr: PCT.MAX.cagr }));
console.log("percentiles ETF:", JSON.stringify({ sharpe: PCT.ETF.sharpe, maxdd: PCT.ETF.maxdd }));

// ---------------------------------------------------------------- Shapley 2x2 (frozen §2; CAGR pp, P-MAX net-2bp)
function cagrOf(rows) {
  const v = rows.map((r) => r.pre - r.to * COST2).filter(fin);
  return v.reduce((a, x) => a * (1 + x), 1) ** (12 / v.length) - 1;
}
const SHAP = (() => {
  const A = cagrOf(legA_MAX) * 100, B = cagrOf(legB_MAX) * 100, C = cagrOf(legC_MAX) * 100, Ap = cagrOf(legAp_MAX) * 100;
  const PE = 0.5 * ((A - C) + (Ap - B)), AE = 0.5 * ((A - Ap) + (C - B)), INT = (A - Ap) - (C - B);
  return { A, B, C, Aprime: Ap, PE, AE, INT, PE_share: Math.abs(PE) / (Math.abs(PE) + Math.abs(AE)) };
})();
console.log("shapley:", JSON.stringify(SHAP));

// ---------------------------------------------------------------- attribution DH vs C by family (P-MAX common months, pre-cost + cost split)
function attribution(Rd, Rc, retFn) {
  const m2 = new Map(Rc.map((r) => [r.date, r]));
  const fam = { equity: 0, rates: 0, real: 0, cash: 0 };
  let totPre = 0, costD = 0, n = 0;
  for (const r of Rd) {
    const c = m2.get(r.date);
    if (!c) continue;
    n++;
    for (const s of ORDER.concat(["cash"])) {
      const rv = retFn(s, r.ym);
      if (!fin(rv)) continue;
      fam[FAM[s] ?? "cash"] += ((r.w[s] - c.w[s]) / 100) * rv;
    }
    totPre += r.pre - c.pre;
    costD += (r.to - c.to) * COST2;
  }
  const famSum = fam.equity + fam.rates + fam.real + fam.cash;
  return { n, fam, famSum, totPre, costDrag: costD, remainder: totPre - famSum };
}
const ATTR_MAX = attribution(legA_MAX, legC_MAX, researchRet);
// era + crisis splits of (DH-C) net diffs
function splitDiff(Rd, Rc, retFn, windows) {
  const m2 = new Map(Rc.map((r) => [r.date, r]));
  const out = {};
  for (const [nm, lo, hi] of windows) {
    let s = 0, n = 0;
    for (const r of Rd) {
      if (r.date < lo || r.date > hi) continue;
      const c = m2.get(r.date);
      if (!c) continue;
      s += (r.pre - r.to * COST2) - (c.pre - c.to * COST2);
      n++;
    }
    out[nm] = { n, cum_pp: s * 100 };
  }
  return out;
}
const ERA_DIFF = splitDiff(legA_MAX, legC_MAX, researchRet, [...ERAS.map(([e, lo, hi]) => [e, lo.slice(0, 7), hi.slice(0, 7)]), ...CRISES.map(([e, lo, hi]) => ["crisis_" + e, lo, hi])]);
// top-3 #186 spans
const s186 = JSON.parse(readLF("generated/issue-186/summary.json"));
const spans186 = s186.peaks20.map((p) => [p.peak, p.rec]);
{
  const m2 = new Map(legC_MAX.map((r) => [r.date, r]));
  var top3 = spans186.map(([pk, rc]) => {
    let s = 0;
    for (const r of legA_MAX) {
      if (r.ym < pk || (rc && r.ym >= rc)) continue;
      const c = m2.get(r.date);
      if (!c) continue;
      s += (r.pre - r.to * COST2) - (c.pre - c.to * COST2);
    }
    return { span: pk + "->" + (rc ?? "cens"), cum_pp: s * 100 };
  });
  const pos = top3.filter((t) => t.cum_pp > 0).sort((a, b) => b.cum_pp - a.cum_pp);
  var top3share = pos.length ? pos.slice(0, 3).reduce((a, t) => a + t.cum_pp, 0) / pos.reduce((a, t) => a + t.cum_pp, 0) : null;
}
// 2008 mechanism audit: applied weights 2007-01..2010-12
const audit08 = legA_MAX.filter((r) => r.date >= "2007-01-01" && r.date <= "2010-12-01").map((r) => ({
  date: r.date, state: r.dhState, E: +eqOf(r.w).toFixed(2), cash: +r.w.cash.toFixed(2),
  rates: +(r.w.treasury2y + r.w.treasury10y + r.w.longtreasury).toFixed(2), real: +(r.w.gold + r.w.oil).toFixed(2),
}));

// ---------------------------------------------------------------- bootstrap + LOOO (frozen §7; DH-C paired net diffs, P-MAX)
function pairedDiffs(Rd, Rc) {
  const m2 = new Map(Rc.map((r) => [r.date, r]));
  const d = [];
  for (const r of Rd) {
    const c = m2.get(r.date);
    if (!c) continue;
    d.push([(r.pre - r.to * COST2), (c.pre - c.to * COST2)]);
  }
  return d;
}
function bootstrapCI(pairs, block, reps, seed) {
  const n = pairs.length;
  const rnd = mulberry32(seed);
  const diffs = [];
  const nb = Math.ceil(n / block);
  for (let b = 0; b < reps; b++) {
    const idx = [];
    for (let k = 0; k < nb; k++) {
      const s = Math.floor(rnd() * n);
      for (let j = 0; j < block; j++) idx.push((s + j) % n);
    }
    const use = idx.slice(0, n);
    let cd = 1, cc = 1;
    for (const i of use) { cd *= 1 + pairs[i][0]; cc *= 1 + pairs[i][1]; }
    diffs.push((cd ** (12 / n) - 1 - (cc ** (12 / n) - 1)) * 100);
  }
  diffs.sort((a, b) => a - b);
  return { lo5: diffs[Math.floor(0.05 * reps)], hi95: diffs[Math.floor(0.95 * reps)] };
}
function cagrDiffPairs(pairs) {
  let cd = 1, cc = 1;
  for (const [a, b] of pairs) { cd *= 1 + a; cc *= 1 + b; }
  const n = pairs.length;
  return (cd ** (12 / n) - 1 - (cc ** (12 / n) - 1)) * 100;
}
const pairsMAX = pairedDiffs(legA_MAX, legC_MAX);
const pairsETF = pairedDiffs(legA_ETF, legC_ETF);
const BS_MAX = bootstrapCI(pairsMAX, 24, 5000, 188);
const BS_ETF = bootstrapCI(pairsETF, 24, 5000, 188);
// LOOO with dates (drop episode months, recompute DH-C CAGR diff)
{
  const m2 = new Map(legC_MAX.map((r) => [r.date, r]));
  var dated = legA_MAX.filter((r) => m2.has(r.date)).map((r) => ({ date: r.date, ym: r.ym, a: r.pre - r.to * COST2, c: m2.get(r.date).pre - m2.get(r.date).to * COST2 }));
}
const LOOO_OUT = LOOO.map(([nm, lo, hi]) => {
  const sub = dated.filter((r) => r.ym < lo || r.ym > hi).map((r) => [r.a, r.c]);
  return { episode: nm, n: sub.length, cagr_diff_pp: +cagrDiffPairs(sub).toFixed(4) };
});
console.log("bootstrap MAX CI:", JSON.stringify(BS_MAX), "ETF CI:", JSON.stringify(BS_ETF));
console.log("LOOO:", JSON.stringify(LOOO_OUT));

// ---------------------------------------------------------------- +1/+2/+3 DH-availability stress (frozen §7; shift band maps, rerun A)
function stressShift(k) {
  const addM = (ym, d) => {
    let y = +ym.slice(0, 4), m = +ym.slice(5, 7) + d;
    while (m > 12) { m -= 12; y++; }
    while (m < 1) { m += 12; y--; }
    return String(y).padStart(4, "0") + "-" + String(m).padStart(2, "0");
  };
  // shifted B-2 timeline: confirmation on shifted bands
  const shifted = new Map();
  for (const d of ALLMOS) {
    const i = ALLMOS.indexOf(d);
    const src = i - k >= 0 ? ALLMOS[i - k] : null;
    if (src) shifted.set(d, dhByDate.get(src));
  }
  const tl = [];
  for (let i = 0; i < ALLMOS.length; i++) {
    const m = ALLMOS[i];
    if (m < "1966-05-01") continue;
    const a = shifted.get(ALLMOS[i - 1]), b = shifted.get(ALLMOS[i - 2]);
    if (a === undefined || b === undefined) continue;
    tl.push({ date: m, ym: m.slice(0, 7), dhState: a === b ? a : null });
  }
  let last = null;
  for (const r of tl) { if (r.dhState === null) r.dhState = last; else last = r.dhState; }
  const months = tl.filter((r) => r.dhState !== null).filter((r) => PMAX.some((p) => p.date === r.date));
  const R = [], C = [];
  for (const m of months) {
    const avail = new Set(ORDER.filter((s) => fin(researchRet(s, m.ym)) && fin(researchRet("cash", m.ym))));
    const w = matrixW(m.dhState, avail);
    const p = applyRet(w, m.ym, researchRet);
    if (!fin(p)) continue;
    R.push(p); C.push(researchRet("cash", m.ym));
  }
  const mm = metrics(R, C);
  // incr vs C-leg on same months
  const mC = new Map(legC_MAX.map((r) => [r.date, r.pre - r.to * COST2]));
  const pairs = months.map((m, i) => [R[i], mC.get(m.date)]).filter(([a, b]) => fin(a) && fin(b));
  return { k, n: R.length, cagr: +mm.cagr.toFixed(6), maxdd: +mm.maxdd.toFixed(6), sharpe: fin(mm.sharpe_like) ? +mm.sharpe_like.toFixed(4) : null, incr_cagr_pp: +cagrDiffPairs(pairs).toFixed(4) };
}
const STRESS = [stressShift(1), stressShift(2), stressShift(3)];
console.log("stress:", JSON.stringify(STRESS));

// ---------------------------------------------------------------- gates + verdict (frozen §8; P-MAX net-2bp primary)
function netPerf(rows, retFn) {
  const post = rows.map((r) => r.pre - r.to * COST2);
  return metrics(post, rows.map((r) => retFn("cash", r.ym)));
}
const nA = netPerf(legA_MAX, researchRet), nC = netPerf(legC_MAX, researchRet),
  nD = netPerf(legD_MAX, researchRet), nE2 = netPerf(E2_MAX, researchRet),
  nR = netPerf(E1_MAX_R, researchRet), nG = netPerf(E1_MAX_G, researchRet);
const nAetf = netPerf(legA_ETF, implRet), nCetf = netPerf(legC_ETF, implRet);
// G5 on COMMON valid months (prereg §6 same-calendar rule; E2 n=309 subset)
const e2dates = new Set(E2_MAX.map((r) => r.date));
const nAcommon = netPerf(legA_MAX.filter((r) => e2dates.has(r.date)), researchRet);
const G5common = {
  dh: { cagr: nAcommon.cagr, sharpe: nAcommon.sharpe_like, maxdd: nAcommon.maxdd, n: nAcommon.n },
  e2: { cagr: nE2.cagr, sharpe: nE2.sharpe_like, maxdd: nE2.maxdd, n: nE2.n },
};
const g = {
  G1: (nA.cagr - nC.cagr) * 100 >= 0.10 && (nAetf.cagr - nCetf.cagr) * 100 >= 0,
  G2: (nA.sharpe_like - nC.sharpe_like) >= 0.02 && (nA.maxdd - nC.maxdd) * 100 >= 1.0,
  G3: !PL_MAX.confounded && PCT.MAX.sharpe >= 75 && PCT.MAX.maxdd >= 75 && PCT.ETF.sharpe >= 50,
  G4: (nA.sharpe_like - Math.max(nR.sharpe_like, nG.sharpe_like)) >= 0.01,
  G5: ((G5common.e2.maxdd - G5common.dh.maxdd) * 100 <= -1.0) || (G5common.e2.sharpe <= G5common.dh.sharpe - 0.01),
  G6: (nA.cagr - nD.cagr) * 100 >= 0.05 && (nA.sharpe_like - nD.sharpe_like) >= 0,
  G7: SHAP.PE_share >= 0.50 && SHAP.PE > 0,
  G8: BS_MAX.lo5 > 0 && LOOO_OUT.every((o) => o.cagr_diff_pp > -0.05),
};
const assessable = legA_MAX.length >= 600 && !PL_MAX.confounded;
let verdict;
if (!assessable) verdict = "deep_history_evidence_mixed_or_inconclusive";
else if ([1, 2, 3, 4, 5, 6, 7, 8].every((i) => g["G" + i])) verdict = "deep_history_macro_information_supported";
else if (g.G1 && !g.G4) verdict = "deep_history_reducible_to_simpler_defense";
else if (!g.G6 || !g.G7) verdict = "deep_history_exposure_or_availability_explained";
else verdict = "deep_history_evidence_mixed_or_inconclusive";
console.log("gates:", JSON.stringify(g));
console.log("verdict:", verdict);

// ---------------------------------------------------------------- outputs (frozen §9)
fs.mkdirSync(GEN188, { recursive: true });
const W = (n, c) => fs.writeFileSync(path.join(GEN188, n), c);
const J = (o) => JSON.stringify(o, null, 2) + "\n";
const ser = (rows) => rows.map((r) => [r.date, r.pre, r.to, r.pre - r.to * COST2].join(",")).join("\n");
W("manifest.json", J({
  issue: 188, parents: { "#177": "bc652bd615f2c5e9137050d01c666dbcd9528cd3", "#178": "10dcdce0ec86b0493d6df6b916b720eba46dcbe6", "#180": "ac251ad5149d9f550d82dfb34b3551fe01032367", "#183": "411835cc9e3a00d0f5d998df9fb2058d8a917e96", "#184": "a3c6dbbdbcdbaf25129caf9bd5008b08947605e3", "#186": "a83836ce0453d890c4d00667d50c36767aa9278b", "#187": "e61b9a31feb08ab757d34d77cc841fda70c77bcc" },
  panels: { PMAX: PMAX.length, PFULL: PFULL.length, PETF: PETF.length, missing_cal: ["2025-10-01", "2025-11-01", "2026-01-01"] },
  costs: { primary_bp: 2, hypo_bp: [10, 25] }, bootstrap: { block: 24, reps: 5000, seed: 188 },
  production_authorized: false,
}));
W("reproduction.json", J({
  A_MAX: { n: legA_MAX.length, mismatches: 0 }, A_FULL: { n: legA_FULL.length }, A_ETF: { n: legA_ETF.length, mismatches: 0 },
  B_MAX_neutral: P.MAX.B.pre, F_MAX: P.MAX.F.pre,
}));
W("monthly-PMAX-A.csv", "date,pre,turnover,post2bp\n" + ser(legA_MAX) + "\n");
W("monthly-PMAX-C.csv", "date,pre,turnover,post2bp\n" + ser(legC_MAX) + "\n");
W("monthly-PMAX-D.csv", "date,pre,turnover,post2bp\n" + ser(legD_MAX) + "\n");
W("monthly-PETF-A.csv", "date,pre,turnover,post2bp\n" + ser(legA_ETF) + "\n");
W("monthly-PETF-C.csv", "date,pre,turnover,post2bp\n" + ser(legC_ETF) + "\n");
W("monthly-PMAX-E2.csv", "date,pre,turnover,post2bp\n" + ser(E2_MAX) + "\n");
W("performance.json", J({
  MAX: { A: P.MAX.A, B: P.MAX.B, C: P.MAX.C, Ap: P.MAX.Ap, D: P.MAX.D, E: P.MAX.E, F: P.MAX.F, E1R: P.MAX.E1R, E1G: P.MAX.E1G, E1P: P.MAX.E1P, E1CR: P.MAX.E1CR, E1CG: P.MAX.E1CG, E2: P.MAX.E2 },
  FULL: P.FULL, ETF: P.ETF,
}));
W("placebo.json", J({
  MAX: { N: PL_MAX.N, nValid: PL_MAX.nValid, mmMax: PL_MAX.mmMax, confounded: PL_MAX.confounded, pct: PCT.MAX },
  FULL: { N: PL_FULL.N, nValid: PL_FULL.nValid, mmMax: PL_FULL.mmMax, confounded: PL_FULL.confounded, pct: PCT.FULL },
  ETF: { N: PL_ETF.N, nValid: PL_ETF.nValid, mmMax: PL_ETF.mmMax, confounded: PL_ETF.confounded, pct: PCT.ETF },
}));
W("placebo-PMAX.csv", "shift,n,sharpe,cagr,maxdd,ulcer,roll12,cdar,uw\n" + PL_MAX.shifts.map((d) => [d.k, d.n, d.sharpe, d.cagr, d.maxdd, d.ulcer, d.roll12, d.cdar, d.uw].join(",")).join("\n") + "\n");
W("attribution.json", J({ MAX_vs_C: ATTR_MAX, era_crisis: ERA_DIFF, top3_spans: top3, top3_share_pos: top3share }));
W("audit-2008.csv", "date,state,E,cash,rates,real\n" + audit08.map((r) => [r.date, r.state, r.E, r.cash, r.rates, r.real].join(",")).join("\n") + "\n");
W("bootstrap.json", J({ MAX_CI90: BS_MAX, ETF_CI90: BS_ETF, LOOO: LOOO_OUT }));
W("stress.json", J(STRESS));
W("summary.json", J({
  issue: 188, verdict, gates: g, assessable,
  g5_common_months: G5common,
  shapley: SHAP, incrAC_MAX_pp: (nA.cagr - nC.cagr) * 100, incrAC_ETF_pp: (nAetf.cagr - nCetf.cagr) * 100,
  bootstrap_MAX: BS_MAX, looo: LOOO_OUT, stress: STRESS,
  panels: { PMAX: legA_MAX.length, PFULL: legA_FULL.length, PETF: legA_ETF.length },
  production_authorized: false,
}));
console.log("wrote", fs.readdirSync(GEN188).length, "files");
