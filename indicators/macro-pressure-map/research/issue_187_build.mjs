#!/usr/bin/env node
// Issue #187 — early-recovery overlay builder: signals, episodes, ABCD legs,
// cases, false-starts, stress. Frozen contract: issue-187-early-recovery-prereg.md
// Post-prereg ONLY (prereg e2a141f). No model change. No V6.6. No optimizer.
// Parents read-only. All writes go to research/generated/issue-187/.
import fs from "node:fs";
import path from "node:path";
import crypto from "node:crypto";

const ROOT = process.cwd();
const RES = path.join(ROOT, "indicators/macro-pressure-map/research");
const GEN187 = path.join(RES, "generated/issue-187");
const sha256 = (b) => crypto.createHash("sha256").update(b).digest("hex");
const fin = (x) => typeof x === "number" && Number.isFinite(x);
const readLF = (rel) => fs.readFileSync(path.join(RES, rel), "utf8").replace(/\r/g, "");

// ---------------------------------------------------------------- frozen policy (verbatim #178/#183)
const ORDER = ["sp500", "nasdaq", "russell", "treasury2y", "treasury10y", "longtreasury", "gold", "oil"];
const EQ = ["sp500", "nasdaq", "russell"];
const FAM = { sp500: "equity", nasdaq: "equity", russell: "equity", treasury2y: "rates", treasury10y: "rates", longtreasury: "rates", gold: "real", oil: "real" };
const SCAP = { sp500: 35, nasdaq: 20, russell: 15, treasury2y: 15, treasury10y: 25, longtreasury: 15, gold: 12, oil: 8 };
const FCAP = { equity: 60, rates: 50, real: 15 };
const ZEROS = [["G_Low/I_Low", "oil"], ["G_Neutral/I_High", "russell"], ["G_High/I_Low", "gold"]];
const CMIN_BIAS = { low: 5, neutral: 10, high: 20 };
const BASE = { sp500: 25, nasdaq: 12, russell: 8, treasury2y: 8, treasury10y: 14, longtreasury: 8, gold: 6, oil: 4 };
const MULT = { 0: 0, Low: 0.5, Neutral: 1.0, High: 1.75 };
const CASH_MIN = 2, CASH_MAX = 60, COST = 0.0002, TOL = 1e-9, BUDGET = 5;
const PARENTS = {
  "issue-177": "bc652bd615f2c5e9137050d01c666dbcd9528cd3",
  "issue-178": "10dcdce0ec86b0493d6df6b916b720eba46dcbe6",
  "issue-180": "ac251ad5149d9f550d82dfb34b3551fe01032367",
  "issue-183": "411835cc9e3a00d0f5d998df9fb2058d8a917e96",
  "issue-184": "a3c6dbbdbcdbaf25129caf9bd5008b08947605e3",
  "issue-186": "a83836ce0453d890c4d00667d50c36767aa9278b",
};
const G174 = "generated/issue-174", G176 = "generated/issue-176", G177 = "generated/issue-177";
const G178 = "generated/issue-178", G180 = "generated/issue-180", G183 = "generated/issue-183", G186 = "generated/issue-186";
const ERAS = [["E1", "1966-03-01", "1979-12-01"], ["E2", "1980-01-01", "2007-12-01"], ["E3", "2008-01-01", "2019-12-01"], ["E4", "2020-01-01", "2026-08-01"]];

// ---------------------------------------------------------------- matrix + policy components (verbatim #183)
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
const STATES = [...SW.keys()];
const TIERS = {};
for (const l of readLF(`${G177}/policy-matrix.csv`).trim().split("\n").slice(1)) {
  const c = l.split(",");
  if (c[1] === "cash") continue;
  TIERS[c[0] + "|" + c[1]] = c[2];
}
const CBIAS_FIXED = {};
for (const l of readLF(`${G177}/cash-bias.csv`).trim().split("\n").slice(1)) {
  const c = l.split(",");
  CBIAS_FIXED[c[0]] = c[2];
}
function weightsFromPolicy(state, avail, base, mult, cbias) {
  const raw = {};
  for (const s of ORDER) {
    const m = mult[TIERS[state + "|" + s]];
    if (m === undefined || m === 0) continue;
    if (avail !== null && !avail.has(s)) continue;
    raw[s] = base[s] * m;
  }
  for (const s of Object.keys(raw)) if (raw[s] > SCAP[s]) raw[s] = SCAP[s];
  for (const fam of Object.keys(FCAP)) {
    const mem = Object.keys(raw).filter((s) => FAM[s] === fam);
    const sum = mem.reduce((a, s) => a + raw[s], 0);
    if (sum > FCAP[fam]) { const k = FCAP[fam] / sum; for (const s of mem) raw[s] *= k; }
  }
  const S = Object.values(raw).reduce((a, x) => a + x, 0);
  const minC = CMIN_BIAS[cbias[state]];
  let cash;
  if (100 - S < minC) {
    const k = S > 0 ? (100 - minC) / S : 0;
    for (const s of Object.keys(raw)) raw[s] *= k;
    cash = minC;
  } else if (100 - S > CASH_MAX) {
    const k = S > 0 ? (100 - CASH_MAX) / S : 0;
    for (const s of Object.keys(raw)) raw[s] *= k;
    cash = CASH_MAX;
  } else cash = 100 - S;
  if (cash < CASH_MIN) cash = CASH_MIN;
  for (const s of Object.keys(raw)) {
    if (raw[s] > SCAP[s]) { cash += raw[s] - SCAP[s]; raw[s] = SCAP[s]; }
  }
  const out = {};
  for (const s of ORDER) out[s] = raw[s] ?? 0;
  out.cash = cash;
  return out;
}
const fixedWeights = (state, avail = null) => weightsFromPolicy(state, avail, BASE, MULT, CBIAS_FIXED);
function matrixW(state, avail) {
  const base = SW.get(state);
  if (ORDER.every((s) => avail.has(s))) return { ...base };
  return fixedWeights(state, avail);
}
const frozenRow = (st) => ({ ...SW.get(st) });

// ---------------------------------------------------------------- DH + B-2 (verbatim #183)
function band(s) { return s < -10 ? "Low" : s > 10 ? "High" : "Neutral"; }
let dhByDate = new Map(), gDH = new Map(), iDH = new Map();
function loadDH() {
  dhByDate = new Map(); gDH = new Map(); iDH = new Map();
  const t = readLF("generated/issue-160/deep-history-v01-monthly.csv").trim().split("\n");
  const h = t[0].split(",");
  const gi = h.indexOf("growth_dh"), ii = h.indexOf("inflation_dh");
  for (const l of t.slice(1)) {
    const c = l.split(",");
    const g = parseFloat(c[gi]), v = parseFloat(c[ii]);
    if (fin(g) && fin(v)) { dhByDate.set(c[0], "G_" + band(g) + "/I_" + band(v)); gDH.set(c[0].slice(0, 7), g); iDH.set(c[0].slice(0, 7), v); }
  }
}
loadDH();
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

// ---------------------------------------------------------------- overlay sizing (frozen §4; D reuses with requested=d)
function sizeOverlay(base, requested) {
  const w = { ...base };
  const eq = EQ.filter((s) => w[s] > 0);
  const E = eq.reduce((a, s) => a + w[s], 0);
  const head = eq.reduce((a, s) => a + (SCAP[s] - w[s]), 0);
  let add = Math.min(requested, Math.max(0, w.cash - CASH_MIN), FCAP.equity - E, head);
  add = Math.max(0, add);
  const reason = Math.abs(add - requested) < 1e-9 ? "full"
    : (Math.abs(add - Math.max(0, w.cash - CASH_MIN)) < 1e-9 ? "cash_floor" : "cap_headroom");
  if (E > 0 && add > 0) for (const s of eq) { const take = Math.min((add * w[s]) / E, SCAP[s] - w[s]); w[s] += take; w.cash -= take; }
  return { w, add, blocked: requested - add, reason };
}

// ---------------------------------------------------------------- month arithmetic + DH access (shiftable for stress)
const addM = (ym, k) => {
  let y = +ym.slice(0, 4), m = +ym.slice(5, 7) + k;
  while (m > 12) { m -= 12; y++; }
  while (m < 1) { m += 12; y--; }
  return String(y).padStart(4, "0") + "-" + String(m).padStart(2, "0");
};
let G = gDH, I = iDH; // shifted under stress
const sigAt = (ym) => {
  const g0 = G.get(ym), g1 = G.get(addM(ym, -1)), g2 = G.get(addM(ym, -2));
  const i0 = I.get(ym), i1 = I.get(addM(ym, -1));
  if (![g0, g1, g2, i0, i1].every(fin)) return false;
  return g0 < -10 && g0 > g1 && g1 > g2 && i0 <= 10 && (i0 - i1) <= 5;
};
// Low episodes on (possibly shifted) Growth series over timeline months
function lowEpisodes(ymList) {
  const eps = [];
  let s = null;
  for (let i = 0; i < ymList.length; i++) {
    const g = G.get(ymList[i]);
    if (!fin(g)) { if (s !== null) { eps.push([s, i - 1]); s = null; } continue; }
    if (g < -10) { if (s === null) s = i; }
    else if (s !== null) { eps.push([s, i - 1]); s = null; }
  }
  if (s !== null) eps.push([s, ymList.length - 1]);
  return eps;
}

// ---------------------------------------------------------------- structural E targets per panel month
// FULL panel: frozen month list from #183 corrected-structural-monthly
const fStruct = readLF(`${G183}/corrected-structural-monthly.csv`).trim().split("\n");
const fH = fStruct[0].split(",");
const fullMonths = fStruct.slice(1).map((l) => {
  const c = l.split(",");
  const o = {};
  fH.forEach((k, j) => o[k] = c[j]);
  return { date: o.date, ym: o.date.slice(0, 7), state: o.alloc_state, frozenRet: parseFloat(o.port_ret) };
});
const dhMap = new Map(tlB2.map((r) => [r.date, r.dhState]));
// base weights FULL (matrixW availability rule) + A_pre + assert vs frozen
const fullBase = [];
{
  let mism = 0;
  for (const m of fullMonths) {
    const st = dhMap.get(m.date) ?? m.state;
    const avail = new Set(ORDER.filter((s) => fin(researchRet(s, m.ym)) && fin(researchRet("cash", m.ym))));
    const w = matrixW(st, avail);
    let pr = 0, ok = true;
    for (const s of ORDER.concat(["cash"])) {
      if (w[s] === 0) continue;
      const r = researchRet(s, m.ym);
      if (!fin(r)) { ok = false; break; }
      pr += (w[s] / 100) * r;
    }
    fullBase.push({ ...m, wA: w, Apre: ok ? pr : NaN });
    if (ok && fin(m.frozenRet) && Math.abs(pr - m.frozenRet) > 1e-12) mism++;
  }
  console.log("FULL A reproduction mismatches (tol 1e-12):", mism);
  if (mism !== 0) { console.error("FAIL A/FULL reproduction"); process.exit(1); }
}
const EYM = new Map(fullBase.map((r) => [r.ym, EQ.reduce((a, s) => a + r.wA[s], 0)]));
// ETF STRICT panel
const STRICT_LO = "2006-06-01";
const etfMonths = tlB2.filter((m) => m.date >= STRICT_LO);
const fImpl = readLF(`${G183}/corrected-implementation-monthly.csv`).trim().split("\n");
const iH = fImpl[0].split(",");
const implFrozen = new Map(fImpl.slice(1).map((l) => {
  const c = l.split(","); const o = {};
  iH.forEach((k, j) => o[k] = c[j]);
  return [o.date, parseFloat(o.impl_pre)];
}));
const etfBase = [];
{
  let mism = 0, drops = 0;
  for (const m of etfMonths) {
    const ym = m.date.slice(0, 7);
    const base = frozenRow(m.dhState);
    const w = { ...base };
    let moved = 0;
    for (const s of ORDER) if (w[s] > 0 && !fin(implRet(s, ym))) { moved += w[s]; w[s] = 0; }
    w.cash += moved;
    let pb = 0, okb = true;
    for (const s of ORDER.concat(["cash"])) {
      if (w[s] === 0) continue;
      const r = implRet(s, ym);
      if (!fin(r)) { okb = false; break; }
      pb += (w[s] / 100) * r;
    }
    etfBase.push({ date: m.date, ym, state: m.dhState, wA: w, Apre: okb ? pb : NaN });
    if (!okb) drops++;
    else if (implFrozen.has(m.date) && Math.abs(pb - implFrozen.get(m.date)) > 1e-12) mism++;
  }
  console.log("ETF A reproduction mismatches:", mism, "drops:", drops, "n:", etfMonths.length);
  if (mism !== 0) { console.error("FAIL A/ETF reproduction"); process.exit(1); }
  if (drops !== 0) console.log("WARN ETF drops nonzero (reported, not filled)");
}

// ---------------------------------------------------------------- signal scan + activations (weights/levels only; DH + E targets)
function buildActivations(months, eym, firstSignalYM) {
  const yms = months.map((m) => m.ym !== undefined ? m.ym : m.date.slice(0, 7));
  const eps = lowEpisodes(yms);
  const consumed = new Set();
  const acts = [], suppressed = [];
  for (const [s, e] of eps) {
    for (let i = s; i <= e; i++) {
      const ym = yms[i];
      if (ym < firstSignalYM) continue;
      if (!sigAt(ym)) continue;
      const epKey = s + "-" + e;
      if (consumed.has(epKey)) { suppressed.push({ ym, ep: epKey }); continue; }
      consumed.add(epKey);
      // activation: m0 = next timeline month present in months
      const m0i = i + 1;
      if (m0i >= months.length) { acts.push({ signal: ym, m0: null, ep: epKey, censored: true }); continue; }
      const m0 = months[m0i].ym !== undefined ? months[m0i].ym : months[m0i].date.slice(0, 7);
      const m0date = months[m0i].date;
      // reference structural E at m0
      const eRef = eym.get(m0);
      // size on m0 base
      const base = months[m0i].wA;
      const sized = sizeOverlay(base, BUDGET);
      acts.push({ signal: ym, m0, m0date, ep: epKey, eRef, X: sized.add, blocked: sized.blocked, reason: sized.reason, censored: false });
      break; // one per episode (further signals suppressed by consumed flag anyway)
    }
  }
  return { acts, suppressed, eps };
}
function runExits(acts, months, eym) {
  const ymIdx = new Map(months.map((m, i) => [(m.ym !== undefined ? m.ym : m.date.slice(0, 7)), i]));
  return acts.map((a) => {
    if (a.censored || a.m0 === null) return { ...a, exit: null, exitReason: "censored_no_m0", activeMonths: [] };
    const start = ymIdx.get(a.m0);
    const active = [];
    let exit = null, reasons = [];
    for (let t = start; t < months.length; t++) {
      const ym = months[t].ym !== undefined ? months[t].ym : months[t].date.slice(0, 7);
      // evaluate at close ym (needs ym, ym-1, ym-2 in DH + E targets)
      const eNow = eym.get(ym), ePrev = eym.get(addM(ym, -1));
      const g0 = G.get(ym), g1 = G.get(addM(ym, -1)), g2 = G.get(addM(ym, -2));
      const i0 = I.get(ym), i1 = I.get(addM(ym, -1));
      const fires = [];
      if (fin(eNow) && eNow >= a.eRef + BUDGET - 1e-9) fires.push("A");
      if ((fin(i0) && i0 > 10) || (fin(i0) && fin(i1) && i0 - i1 > 5)) fires.push("B");
      if ([g0, g1, g2].every(fin) && (g0 - g1) <= 0 && (g1 - g2) <= 0) fires.push("C");
      if (fin(eNow) && fin(ePrev) && eNow - ePrev <= -BUDGET + 1e-9) fires.push("D");
      const completed = active.length + 1; // active months completed incl. current
      if (completed >= 6) fires.push("E");
      active.push(ym); // month t itself ran WITH the overlay (exit takes effect t+1)
      if (fires.length) { exit = { month: addM(ym, 1), reason: fires[0], all: fires, atClose: ym }; reasons = fires; break; }
    }
    if (!exit) return { ...a, exit: null, exitReason: "censored_open", activeMonths: active };
    return { ...a, exit: exit.month, exitReason: exit.reason, exitAll: exit.all, activeMonths: active };
  });
}

// FULL activations (primary)
const fullActs = buildActivations(fullBase, EYM, "1966-05");
const fullRuns = runExits(fullActs.acts, fullBase, EYM);
console.log("FULL episodes:", fullActs.eps.length, "activations:", fullActs.acts.length, "suppressed:", fullActs.suppressed.length);
// overlay weight timeline FULL (weights-only) + d freeze
const overW = new Map(); // ym -> {wB, add}
{
  const actByM0 = new Map();
  for (const a of fullRuns) {
    if (!a.exit && a.exitReason === "censored_no_m0") continue;
    for (const m of a.activeMonths) actByM0.set(m, a);
  }
  for (const m of fullBase) {
    const a = actByM0.get(m.ym);
    if (!a) { overW.set(m.ym, { wB: { ...m.wA }, add: 0 }); continue; }
    const { w, add } = sizeOverlay(m.wA, a.X);
    overW.set(m.ym, { wB: w, add });
  }
}
let dFULL = 0;
{
  let s = 0, n = 0;
  for (const m of fullBase) {
    const o = overW.get(m.ym);
    s += EQ.reduce((x, st) => x + o.wB[st], 0) - EQ.reduce((x, st) => x + m.wA[st], 0);
    n++;
  }
  dFULL = s / n;
}
console.log("FROZEN dFULL (weights-only) =", dFULL.toFixed(10), "pp over", fullBase.length, "months");
// NOTE: d is now frozen; D control performance is computed AFTER this line.

// ---------------------------------------------------------------- legs FULL (returns; identical month set A&B&D ok)
const legs = [];
{
  let prevA = null, prevB = null, prevD = null, drops = 0;
  // D weights need dFULL (frozen above)
  for (const m of fullBase) {
    const o = overW.get(m.ym);
    const wD = sizeOverlay(m.wA, dFULL).w;
    const calc = (w) => {
      let p = 0;
      for (const s of ORDER.concat(["cash"])) {
        if (w[s] === 0) continue;
        const r = researchRet(s, m.ym);
        if (!fin(r)) return NaN;
        p += (w[s] / 100) * r;
      }
      return p;
    };
    const b = calc(o.wB), d = calc(wD);
    if (!fin(m.Apre) || !fin(b) || !fin(d)) { drops++; continue; }
    const toA = prevA ? ORDER.concat(["cash"]).reduce((x, s) => x + Math.abs(m.wA[s] - prevA[s]), 0) / 2 / 100 : 0;
    const toB = prevB ? ORDER.concat(["cash"]).reduce((x, s) => x + Math.abs(o.wB[s] - prevB[s]), 0) / 2 / 100 : 0;
    const toD = prevD ? ORDER.concat(["cash"]).reduce((x, s) => x + Math.abs(wD[s] - prevD[s]), 0) / 2 / 100 : 0;
    legs.push({ date: m.date, ym: m.ym, state: m.state, A: m.Apre, Bp: b, Cp: b - toB * COST, Dp: d - toD * COST, Ap: m.Apre - toA * COST, toA, toB, toD, add: o.add, wA: m.wA, wB: o.wB, wD });
    prevA = { ...m.wA }; prevB = { ...o.wB }; prevD = { ...wD };
  }
  console.log("FULL legs n:", legs.length, "drops:", drops);
}
{
  const avgB = legs.reduce((a, r) => a + EQ.reduce((x, s) => x + r.wB[s], 0), 0) / legs.length;
  const avgD = legs.reduce((a, r) => a + EQ.reduce((x, s) => x + r.wD[s], 0), 0) / legs.length;
  console.log("exposure |D-B| pp:", Math.abs(avgD - avgB).toFixed(6), avgD >= avgB ? "(D over)" : "(D UNDER)");
  // Prereg §7 acceptance is REPORTED, never silently fixed (see finding).
  var exposureAccept = Math.abs(avgD - avgB) <= 0.01;
  var dShortMonths = legs.filter((r) => (EQ.reduce((x, s) => x + r.wD[s], 0) - EQ.reduce((x, s) => x + r.wA[s], 0)) < dFULL - 1e-9).length;
  var dBiasBound_pp_per_yr = Math.abs(avgD - avgB) * 0.06; // 0.017pp equity x ~6% ERP upper bound
  if (!exposureAccept) console.log("WARN exposure-match acceptance MISS (>0.01pp) — disclosed, not fixed;", dShortMonths, "D-short months");
  var avgEqB = avgB, avgEqD = avgD;
  var avgEqA = legs.reduce((a, r) => a + EQ.reduce((x, s) => x + r.wA[s], 0), 0) / legs.length;
}

// ---------------------------------------------------------------- legs ETF (same overlay state machine on ETF months)
const etfEYM = new Map(etfBase.map((r) => [r.ym, EQ.reduce((a, s) => a + r.wA[s], 0)]));
const etfActs = buildActivations(etfBase, etfEYM, "2006-06");
const etfRuns = runExits(etfActs.acts, etfBase, etfEYM);
console.log("ETF episodes:", etfActs.eps.length, "activations:", etfActs.acts.length);
const legsE = [];
{
  const actByM0 = new Map();
  for (const a of etfRuns) {
    if (!a.exit && a.exitReason === "censored_no_m0") continue;
    for (const m of a.activeMonths) actByM0.set(m, a);
  }
  let prevA = null, prevB = null, prevD = null, drops = 0;
  for (const m of etfBase) {
    const a = actByM0.get(m.ym);
    const o = a ? sizeOverlay(m.wA, a.X) : { w: { ...m.wA }, add: 0 };
    const wB = o.w, wD = sizeOverlay(m.wA, dFULL).w;
    const calc = (w) => {
      let p = 0;
      for (const s of ORDER.concat(["cash"])) {
        if (w[s] === 0) continue;
        const r = implRet(s, m.ym);
        if (!fin(r)) return NaN;
        p += (w[s] / 100) * r;
      }
      return p;
    };
    const b = calc(wB), d = calc(wD);
    if (!fin(m.Apre) || !fin(b) || !fin(d)) { drops++; continue; }
    const toA = prevA ? ORDER.concat(["cash"]).reduce((x, s) => x + Math.abs(m.wA[s] - prevA[s]), 0) / 2 / 100 : 0;
    const toB = prevB ? ORDER.concat(["cash"]).reduce((x, s) => x + Math.abs(wB[s] - prevB[s]), 0) / 2 / 100 : 0;
    const toD = prevD ? ORDER.concat(["cash"]).reduce((x, s) => x + Math.abs(wD[s] - prevD[s]), 0) / 2 / 100 : 0;
    legsE.push({ date: m.date, ym: m.ym, state: m.state, A: m.Apre, Bp: b, Cp: b - toB * COST, Dp: d - toD * COST, Ap: m.Apre - toA * COST, toA, toB, toD, add: o.add ?? 0, wA: m.wA, wB, wD });
    prevA = { ...m.wA }; prevB = { ...wB }; prevD = { ...wD };
  }
  console.log("ETF legs n:", legsE.length, "drops:", drops);
}

// ---------------------------------------------------------------- performance helper
function perf(L) {
  const A = L.map((r) => r.A), Bp = L.map((r) => r.Bp), Cp = L.map((r) => r.Cp),
    Dp = L.map((r) => r.Dp), Ap = L.map((r) => r.Ap);
  const cash = L.map((r) => researchRet("cash", r.ym));
  const mA = metrics(A, cash), mB = metrics(Bp, cash), mC = metrics(Cp, cash),
    mD = metrics(Dp, cash), mAp = metrics(Ap, cash);
  const tA = L.map((r) => r.toA).reduce((a, x) => a + x, 0) / L.length * 12;
  const tB = L.map((r) => r.toB).reduce((a, x) => a + x, 0) / L.length * 12;
  const corr = (X, Y) => {
    const idx = X.map((_, i) => (fin(X[i]) && fin(Y[i]) ? i : -1)).filter((i) => i >= 0);
    const xs = idx.map((i) => X[i]), ys = idx.map((i) => Y[i]);
    const mx = xs.reduce((a, x) => a + x, 0) / xs.length, my = ys.reduce((a, x) => a + x, 0) / ys.length;
    let co = 0, vx = 0, vy = 0;
    for (let i = 0; i < xs.length; i++) { co += (xs[i] - mx) * (ys[i] - my); vx += (xs[i] - mx) ** 2; vy += (ys[i] - my) ** 2; }
    return vx > 0 && vy > 0 ? co / Math.sqrt(vx * vy) : NaN;
  };
  return {
    A: mA, B_pre: mB, C: mC, D: mD, A_post: mAp,
    turnA: tA, turnB: tB, turnC: tB, turnD: L.map((r) => r.toD).reduce((a, x) => a + x, 0) / L.length * 12,
    incrCA: { cagr_pp: (mC.cagr - mA.cagr) * 100, maxdd_pp: (mC.maxdd - mA.maxdd) * 100, sharpe: mC.sharpe_like - mA.sharpe_like },
    incrCD: { cagr_pp: (mC.cagr - mD.cagr) * 100, sharpe: mC.sharpe_like - mD.sharpe_like },
    corrBC: corr(Bp, Cp), corrCD: corr(Cp, Dp),
  };
}
const pFull = perf(legs), pEtf = perf(legsE);
// activations stats FULL
function actStats(runs, L) {
  const idx = new Map(L.map((r, i) => [r.ym, i]));
  return runs.map((a) => {
    if (!a.activeMonths.length) return { ...a, pnl: null, horizons: {}, exitLoss: null };
    const ii = a.activeMonths.map((m) => idx.get(m)).filter((i) => i !== undefined);
    const diffs = ii.map((i) => L[i].Bp - L[i].A);
    const cum = diffs.reduce((x, y) => x + y, 0);
    const H = {};
    for (const h of [1, 3, 6, 12]) H[h] = ii.length >= h ? diffs.slice(0, h).reduce((x, y) => x + y, 0) : null;
    return { ...a, pnl: cum, horizons: H, exitLoss: cum < 0, adds: a.activeMonths.map((m) => legs.find((r) => r.ym === m)?.add ?? null) };
  });
}
const fullStats = actStats(fullRuns, legs);

// ---------------------------------------------------------------- bear cases (reuse #186 troughs)
const s186 = JSON.parse(readLF(`${G186}/summary.json`));
const spxM = new Map(readLF(`${G186}/spx-monthly.csv`).trim().split("\n").slice(1).map((l) => {
  const c = l.split(","); return [c[1], parseFloat(c[3])];
}));
const spxCloses = [...spxM.keys()].sort().map((k) => spxM.get(k));
const spxKeys = [...spxM.keys()].sort();
function r20frac(troughYM) {
  const ti = spxKeys.indexOf(troughYM);
  const pt = spxM.get(troughYM);
  for (let k = ti + 1; k < spxKeys.length; k++)
    if (spxM.get(spxKeys[k]) >= 1.2 * pt) return { ref: spxKeys[k], frac: null };
  return { ref: null, frac: null };
}
function structAddAfter(T) {
  const ti = EYM.has(T) ? [...EYM.keys()].indexOf(T) : -1;
  const keys = [...EYM.keys()];
  if (ti < 0) return null;
  for (let k = ti + 1; k <= Math.min(keys.length - 1, ti + 12); k++)
    if (EYM.get(keys[k]) - EYM.get(T) >= 5 - 1e-9) return keys[k];
  return null;
}
const cases = s186.troughs20.map((t) => {
  const T = t.trough;
  const overlapping = fullStats.filter((a) => a.activeMonths.some((m) => {
    const dd = (ym1, ym2) => (+ym2.slice(0, 4) - +ym1.slice(0, 4)) * 12 + (+ym2.slice(5, 7) - +ym1.slice(5, 7));
    return Math.abs(dd(T, m)) <= 12;
  }));
  const sa = structAddAfter(T);
  const first = overlapping.length ? overlapping.map((a) => a.activeMonths[0]).sort()[0] : null;
  const r20 = r20frac(T);
  let reb = null;
  if (first && r20.ref) reb = (spxM.get(first) - spxM.get(T)) / (spxM.get(r20.ref) - spxM.get(T));
  const pnl = overlapping.length ? overlapping.map((a) => a.pnl).reduce((x, y) => x + (y ?? 0), 0) : null;
  return {
    trough: T, trough_px: spxM.get(T), growth_up: s186.slope.find((s) => s.trough === T)?.g_up ?? null,
    signal: overlapping.length ? overlapping[0].signal : null,
    early_add: first, structural_add: sa,
    months_early: first && sa ? ((+sa.slice(0, 4) - +first.slice(0, 4)) * 12 + (+sa.slice(5, 7) - +first.slice(5, 7))) : null,
    rebound_frac_at_early: reb, deployed_X: overlapping.length ? overlapping[0].X : null,
    incr_pnl_active: pnl, lower_low_after_entry: first ? spxKeys.filter((k) => k > first && k <= addM(first, 12)).some((k) => spxM.get(k) < spxM.get(overlapping[0].signal)) : null,
    n_overlapping: overlapping.length,
  };
});

// ---------------------------------------------------------------- false-recovery table (ALL FULL activations)
const falseRows = fullStats.map((a) => {
  if (!a.activeMonths.length) return { signal: a.signal, m0: a.m0, status: a.exitReason, pnl: null };
  const ref = spxM.get(a.signal);
  const fwd = spxKeys.filter((k) => k > a.signal && k <= addM(a.signal, 12)).map((k) => spxM.get(k) / ref - 1);
  return {
    signal: a.signal, m0: a.m0, exit: a.exit, exitReason: a.exitReason,
    X: a.X, blocked: a.blocked, active_n: a.activeMonths.length,
    pnl_active: a.pnl, h1: a.horizons[1], h3: a.horizons[3], h6: a.horizons[6], h12: a.horizons[12],
    exitLoss: a.exitLoss, max_dd_after_entry: fwd.length ? Math.min(...fwd) : null,
    lower_low: fwd.some((v) => v < 0), dd10: fwd.some((v) => v <= -0.10),
  };
});

// ---------------------------------------------------------------- gates + verdict (prereg §12; FULL post-cost primary)
const g = {
  G1: pFull.incrCA.cagr_pp >= -0.15,
  G2: pFull.incrCA.maxdd_pp >= -1.5,
  G3: pFull.incrCA.sharpe >= -0.03,
  G4: Math.min(...falseRows.filter((r) => r.pnl_active !== null).map((r) => r.pnl_active)) * 100 >= -3.0,
  G5: (() => {
    const v = cases.map((c) => c.months_early).filter((x) => x !== null && Number.isFinite(x));
    return v.length ? v.sort((a, b) => a - b)[Math.floor(v.length / 2)] >= 1 : false;
  })(),
  G6: pFull.incrCD.cagr_pp >= -0.05 && pFull.incrCD.sharpe >= -0.02,
  G7: (pFull.turnC - pFull.turnA) * 100 <= 20,
  G8: true, // filled by stress rerun below
  n_act: fullStats.filter((a) => a.activeMonths.length).length,
  overlap_y: legs.length / 12,
};
// ---------------------------------------------------------------- +1/+2/+3 stress (shift DH maps; frozen logic rerun)
function stressShift(k) {
  const G2 = new Map(), I2 = new Map();
  for (const [ym, v] of gDH) G2.set(addM(ym, k), v);
  for (const [ym, v] of iDH) I2.set(addM(ym, k), v);
  const Gs = G, Is = I;
  G = G2; I = I2;
  const acts = buildActivations(fullBase, EYM, "1966-05");
  const runs = runExits(acts.acts, fullBase, EYM);
  G = Gs; I = Is;
  // rebuild B/C legs aligned to the frozen `legs` month grid (same drops)
  const actByM0 = new Map();
  for (const a of runs) {
    if (!a.exit && a.exitReason === "censored_no_m0") continue;
    for (const m of a.activeMonths) actByM0.set(m, a);
  }
  const Bp = [], Cp = [], To = [];
  let prev = null;
  for (const L of legs) {
    const a = actByM0.get(L.ym);
    const wB = a ? sizeOverlay(L.wA, a.X).w : { ...L.wA };
    let p = 0, ok = true;
    for (const s of ORDER.concat(["cash"])) {
      if (wB[s] === 0) continue;
      const r = researchRet(s, L.ym);
      if (!fin(r)) { ok = false; break; }
      p += (wB[s] / 100) * r;
    }
    const to = prev ? ORDER.concat(["cash"]).reduce((x, s) => x + Math.abs(wB[s] - prev[s]), 0) / 2 / 100 : 0;
    Bp.push(ok ? p : NaN); To.push(to); Cp.push(ok ? p - to * COST : NaN);
    prev = { ...wB };
  }
  const A = legs.map((r) => r.A), cash = legs.map((r) => researchRet("cash", r.ym));
  const mC = metrics(Cp, cash), mA = metrics(A, cash);
  return { k, activations: runs.filter((a) => a.activeMonths.length).length, incr_cagr_pp: (mC.cagr - mA.cagr) * 100, maxdd_pp: (mC.maxdd - mA.maxdd) * 100 };
}
const stress = [stressShift(1), stressShift(2), stressShift(3)];
g.G8 = stress.find((s) => s.k === 2).incr_cagr_pp >= -0.25;
let verdict;
if (g.n_act < 3 || g.overlap_y < 10) verdict = "early_recovery_equity_overlay_not_assessable";
else if ([1, 2, 3, 4, 5, 6, 7, 8].every((i) => g["G" + i])) verdict = "early_recovery_equity_overlay_supported";
else if (g.G1 && [1, 2, 3, 4, 5, 6, 7, 8].filter((i) => !g["G" + i]).length <= 2 && g.G2 && g.G4) verdict = "early_recovery_equity_overlay_suggestive_with_limitations";
else verdict = "early_recovery_equity_overlay_not_supported";

// ---------------------------------------------------------------- era splits (frozen ERAS) + robustness
function eraPerf(L) {
  const o = {};
  for (const [en, lo, hi] of ERAS) {
    const sub = L.filter((r) => r.date >= lo && r.date <= hi);
    o[en] = { n: sub.length, ...(sub.length ? perf(sub).incrCA : {}) };
  }
  return o;
}
const robust = {
  exit_reasons: fullStats.reduce((a, r) => { a[r.exitReason] = (a[r.exitReason] || 0) + 1; return a; }, {}),
  blocked_total_pp: fullStats.reduce((a, r) => a + (r.blocked || 0), 0),
  partial_activations: fullStats.filter((r) => (r.blocked || 0) > 1e-9).length,
  episodes: fullActs.eps.length, suppressed_repeats: fullActs.suppressed.length,
  etf_episodes: etfActs.eps.length, etf_suppressed: etfActs.suppressed.length,
  eras_full: eraPerf(legs),
};

// ---------------------------------------------------------------- write outputs
fs.mkdirSync(GEN187, { recursive: true });
const W = (n, c) => fs.writeFileSync(path.join(GEN187, n), c);
const J = (o) => JSON.stringify(o, null, 2) + "\n";
W("manifest.json", J({ issue: 187, parents: PARENTS, cost: COST, budget_pp: BUDGET, panels: { full_n: legs.length, etf_n: legsE.length }, production_authorized: false }));
W("policy.json", J({ entry: "G(t)<-10 & G(t)>G(t-1)>G(t-2) & I(t)<=10 & I(t)-I(t-1)<=5", exits: "A:struct+5pp B:I-High|>+5 C:G 2x non-positive D:struct -5pp E:6 active months", once_per_low_episode: true, cash_floor: 2, caps: "sleeve+family frozen", timing: "signal@t -> effective t+1" }));
W("exposure.json", J({ dFULL_pp: dFULL, avgEqA: avgEqA, avgEqB: avgEqB, avgEqD: avgEqD, match_DmB_pp: avgEqD - avgEqB, match_tol_pp: 0.01, exposure_accept: exposureAccept, d_short_months: dShortMonths, bias_bound_pp_per_yr: dBiasBound_pp_per_yr, note: exposureAccept ? "control exposure-matched" : "ACCEPTANCE MISS disclosed: D structurally under-deploys in cap/cash-bound months; G6 evaluated on actuals, bias bounded above; see finding", cost: COST }));
W("trigger-timeline.csv", "signal,m0,exit,exitReason,X,blocked\n" + fullStats.map((a) => [a.signal, a.m0 ?? "", a.exit ?? "", a.exitReason, (a.X ?? "").toString(), (a.blocked ?? "").toString()].join(",")).join("\n") + "\n");
W("monthly-full.csv", "date,state,E_base,add,A,Bp,Cp,Dp,Ap,toA,toB,toD\n" + legs.map((r) => [r.date, r.state, EQ.reduce((a, s) => a + r.wA[s], 0).toFixed(2), r.add.toFixed(2), r.A, r.Bp, r.Cp, r.Dp, r.Ap, r.toA, r.toB, r.toD].join(",")).join("\n") + "\n");
W("monthly-etf.csv", "date,state,E_base,add,A,Bp,Cp,Dp,Ap\n" + legsE.map((r) => [r.date, r.state, EQ.reduce((a, s) => a + r.wA[s], 0).toFixed(2), r.add.toFixed(2), r.A, r.Bp, r.Cp, r.Dp, r.Ap].join(",")).join("\n") + "\n");
W("performance-full.json", J(pFull));
W("performance-etf.json", J(pEtf));
W("case-cards.json", J(cases));
W("false-recovery.json", J(falseRows));
W("stress.json", J(stress));
W("sensitivity.json", J(robust));
const worstEp = [...falseRows.filter((r) => r.pnl_active !== null)].sort((a, b) => a.pnl_active - b.pnl_active).slice(0, 5);
W("summary.json", J({
  issue: 187, verdict, gates: g,
  full: { n: legs.length, A: pFull.A, C: pFull.C, D: pFull.D, incrCA: pFull.incrCA, incrCD: pFull.incrCD, turnA: pFull.turnA, turnC: pFull.turnC },
  etf: { n: legsE.length, incrCA: pEtf.incrCA, incrCD: pEtf.incrCD },
  activations_full: fullStats.length, active_with_months: g.n_act, activations_etf: etfRuns.filter((a) => a.activeMonths.length).length,
  worst_episodes: worstEp, stress, robust,
  dFULL_pp: dFULL, cost: COST, production_authorized: false,
}));
console.log("dFULL =", dFULL.toFixed(6), "| FULL n:", legs.length, "acts:", fullStats.length, "active:", g.n_act);
console.log("ETF n:", legsE.length, "acts:", etfRuns.filter((a) => a.activeMonths.length).length);
console.log("FULL incrCA:", JSON.stringify(pFull.incrCA), "incrCD:", JSON.stringify(pFull.incrCD));
console.log("ETF incrCA:", JSON.stringify(pEtf.incrCA), "incrCD:", JSON.stringify(pEtf.incrCD));
console.log("gates:", JSON.stringify({ G1: g.G1, G2: g.G2, G3: g.G3, G4: g.G4, G5: g.G5, G6: g.G6, G7: g.G7, G8: g.G8 }));
console.log("verdict:", verdict);
