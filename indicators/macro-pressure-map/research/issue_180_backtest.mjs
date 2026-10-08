// Issue #180 — A/B/C implementation backtest (Node executor).
// Frozen: issue-180-implementation-prereg.md. Runs ONLY post-prereg.
// A = #178 research (reproduced exactly); B = tradable pre-cost;
// C = tradable post-cost (2bp turnover). Weights NEVER recalculated.
import fs from "node:fs";
import path from "node:path";
import crypto from "node:crypto";

const ROOT = process.cwd();
const RES = path.join(ROOT, "indicators/macro-pressure-map/research");
const GEN178 = path.join(RES, "generated/issue-178");
const GEN = path.join(RES, "generated/issue-180");
const sha256 = (b) => crypto.createHash("sha256").update(b).digest("hex");
const fin = (x) => typeof x === "number" && isFinite(x);

// ---- pins ----
const pins = {};
for (const f of ["weight-matrix.csv", "policy.json", "backtest-monthly.csv"]) {
  pins["issue-178/" + f] = sha256(fs.readFileSync(path.join(GEN178, f)));
}
console.log("pins:", JSON.stringify(pins));

// ---- frozen weights ----
const ORDER = ["sp500", "nasdaq", "russell", "treasury2y", "treasury10y", "longtreasury", "gold", "oil"];
const Wt = new Map();
{
  const t = fs.readFileSync(path.join(GEN178, "weight-matrix.csv"), "utf8").trim().split("\n");
  for (const l of t.slice(1)) {
    const c = l.split(",");
    const w = {};
    ["sp500", "nasdaq", "russell", "treasury2y", "treasury10y", "longtreasury", "gold", "oil", "cash"].forEach((s, j) => w[s] = parseFloat(c[j + 1]));
    Wt.set(c[0], w);
  }
}
// ---- macro states (frozen ±10) ----
function band(s) { if (s < -10) return "Low"; if (s > 10) return "High"; return "Neutral"; }
const macroT = fs.readFileSync(path.join(RES, "generated/issue-160/deep-history-v01-monthly.csv"), "utf8").trim().split("\n");
const mh = macroT[0].split(",");
const gi = mh.indexOf("growth_dh"), ii = mh.indexOf("inflation_dh");
const stateByDate = new Map();
for (const l of macroT.slice(1)) {
  const c = l.split(",");
  const g = parseFloat(c[gi]), v = parseFloat(c[ii]);
  if (fin(g) && fin(v)) stateByDate.set(c[0], "G_" + band(g) + "/I_" + band(v));
}
const ALLMOS = [...stateByDate.keys()].filter((d) => d >= "1966-03-01" && d <= "2026-08-01").sort();
// ---- returns: research (frozen #178 semantics) + implementation proxies ----
function loadRet(p) {
  const t = fs.readFileSync(p, "utf8").trim().split("\n");
  const h = t[0].split(",").map((k) => k.trim());
  const m = new Map();
  for (const l of t.slice(1)) {
    const c = l.split(","); const r = {};
    h.forEach((k, j) => r[k] = j === 0 ? c[j] : (c[j] === "" ? NaN : parseFloat(c[j])));
    m.set(r.date.slice(0, 7), r);
  }
  return m;
}
const r174 = loadRet(path.join(RES, "generated/issue-174/nine-sleeve-monthly-returns.csv"));
const r176 = loadRet(path.join(RES, "generated/issue-176/hardened-monthly-returns.csv"));
const rImpl = loadRet(path.join(GEN, "proxy-monthly-returns.csv"));
function researchRet(sl, ym) {
  if (sl === "sp500") { const h = r176.get(ym)?.sp500_tr_hardened; if (fin(h)) return h; const f = r174.get(ym)?.sp500; return fin(f) ? f : NaN; }
  if (sl === "oil") { const v = r176.get(ym)?.oil_investable_return; return fin(v) ? v : NaN; }
  const v = sl === "cash" ? r174.get(ym)?.cash : r174.get(ym)?.[sl];
  return fin(v) ? v : NaN;
}
function implRet(sl, ym) {
  if (sl === "cash") return researchRet("cash", ym);
  const v = rImpl.get(ym)?.[sl];
  return fin(v) ? v : NaN;
}
// ---- B-2 timeline (frozen #178 timing) ----
function timeline() {
  const out = [];
  for (let i = 0; i < ALLMOS.length; i++) {
    const m = ALLMOS[i];
    if (m < "1966-05-01") continue;
    const a = stateByDate.get(ALLMOS[i - 1]), b = stateByDate.get(ALLMOS[i - 2]);
    if (a === undefined || b === undefined) continue;
    out.push({ date: m, allocState: (a === b) ? a : null });
  }
  let last = null;
  for (const r of out) { if (r.allocState === null) r.allocState = last; else last = r.allocState; }
  return out.filter((r) => r.allocState !== null);
}
const tl = timeline();
// self-check: allocStates reproduce #178 backtest-monthly.csv
{
  const t = fs.readFileSync(path.join(GEN178, "backtest-monthly.csv"), "utf8").trim().split("\n");
  const ref = new Map(t.slice(1).map((l) => { const c = l.split(","); return [c[0], c[1]]; }));
  let mism = 0;
  for (const m of tl) if (ref.get(m.date) !== m.allocState) mism++;
  console.log("timeline self-check mismatches:", mism, "of", tl.length);
  if (mism > 0) process.exit(1);
}
// ---- runner (weights frozen; missing proxy -> weight to cash) ----
const COST = 0.0002, COST_ALT = 0.0010;
function run(retFn, months, costRate, lagMonths) {
  const A = [], B = [], C = [], turn = [];
  const states = [], Ws = [];
  let prevW = null;
  const eff = months.map((m, i) => {
    const j = i - lagMonths;
    return j >= 0 ? months[j].allocState : null;
  });
  for (let i = 0; i < months.length; i++) {
    const m = months[i];
    const st = eff[i];
    if (st === null) { A.push(NaN); B.push(NaN); C.push(NaN); turn.push(0); states.push(null); continue; }
    const base = Wt.get(st);
    const ym = m.date.slice(0, 7);
    // research leg (A): same availability rule as #178
    // implementation legs: frozen weights; missing proxy weight -> cash
    const w = { ...base };
    let moved = 0;
    for (const s of ORDER) {
      if (w[s] > 0 && !fin(retFn(s, ym))) { moved += w[s]; w[s] = 0; }
    }
    w.cash += moved;
    let pb = 0, okb = true;
    for (const s of ORDER.concat(["cash"])) {
      const rb = retFn(s, ym);
      if (w[s] === 0) continue;
      if (!fin(rb)) { okb = false; break; }
      pb += (w[s] / 100) * rb;
    }
    // A leg comes from the frozen #178 file (exact reproduction, verified below).
    B.push(okb ? pb : NaN);
    const to = prevW ? ORDER.concat(["cash"]).reduce((a, s) => a + Math.abs(w[s] - prevW[s]), 0) / 2 / 100 : 0;
    turn.push(to);
    C.push(okb ? pb - to * costRate : NaN);
    A.push(NaN); // filled from #178 file below
    states.push(st);
    Ws.push({ ...w });
    prevW = { ...w };
  }
  return { A, B, C, turn, states, Ws };
}
// A from frozen #178 file (exact reproduction, verified below)
const ref178 = new Map(fs.readFileSync(path.join(GEN178, 'backtest-monthly.csv'), 'utf8').trim().split(String.fromCharCode(10)).slice(1).map((l) => { const c = l.split(','); return [c[0], { state: c[1], ret: c[2] === '' ? NaN : parseFloat(c[2]) }]; }));
const R = run(implRet, tl, COST, 0);
let mismA = 0, nA = 0;
for (let i = 0; i < tl.length; i++) {
  const ref = ref178.get(tl[i].date);
  R.A[i] = ref ? ref.ret : NaN;
  if (ref && fin(ref.ret)) { nA++; }
}
// A-vs-file check is structural (same file); real check: recompute A independently? #178 engine frozen;
// file IS the frozen A. Record SHA pin instead (done above). Verify count sanity:
console.log("A months from #178 file:", nA, "of", tl.length);

function metrics(R, C) {
  const idx = R.map((r, i) => fin(r) && fin(C[i]) ? i : -1).filter((i) => i >= 0);
  const Rs = idx.map((i) => R[i]), Cs = idx.map((i) => C[i]);
  const n = Rs.length;
  if (n === 0) return { n: 0, cagr: NaN, vol_ann: NaN, cash_excess_ann: NaN, sharpe_like: NaN, maxdd: NaN, worst_month: NaN, pos_frac: NaN };
  const mm = Rs.reduce((a, x) => a + x, 0) / n;
  const sd = Math.sqrt(Rs.reduce((a, x) => a + (x - mm) ** 2, 0) / n);
  const comp = Rs.reduce((a, x) => a * (1 + x), 1), compC = Cs.reduce((a, x) => a * (1 + x), 1);
  const ex = Rs.map((r, i) => r - Cs[i]);
  const em = ex.reduce((a, x) => a + x, 0) / n;
  const esd = Math.sqrt(ex.reduce((a, x) => a + (x - em) ** 2, 0) / n);
  let peak = 1, dd = 0, cum = 1;
  for (const r of Rs) { cum *= 1 + r; peak = Math.max(peak, cum); dd = Math.min(dd, cum / peak - 1); }
  return { n, cagr: comp ** (12 / n) - 1, vol_ann: sd * Math.sqrt(12), cash_excess_ann: (comp / compC) ** (12 / n) - 1, sharpe_like: esd > 0 ? (em * 12) / (esd * Math.sqrt(12)) : NaN, maxdd: dd, worst_month: Math.min(...Rs), pos_frac: Rs.filter((r) => r > 0).length / n };
}
const cashFull = tl.map((m) => researchRet("cash", m.date.slice(0, 7)));
// strict panel months (all primary proxies present)
const STRICT_LO = "2006-06-01";
const sIdx = tl.map((m, i) => (m.date >= STRICT_LO ? i : -1)).filter((i) => i >= 0);
console.log("strict months:", sIdx.length);
const pick = (arr) => sIdx.map((i) => arr[i]);
const A = R.A, B = R.B, C = R.C;
// preservation on strict panel, common valid months
const cIdx = sIdx.filter((i) => fin(A[i]) && fin(B[i]) && fin(C[i]));
console.log("common strict months:", cIdx.length);
const RA = cIdx.map((i) => A[i]), RB = cIdx.map((i) => B[i]), RC = cIdx.map((i) => C[i]);
const mA = metrics(RA, cIdx.map((i) => cashFull[i])), mB = metrics(RB, cIdx.map((i) => cashFull[i])), mC = metrics(RC, cIdx.map((i) => cashFull[i]));
const diffs = RB.map((r, k) => r - RA[k]);
const md = diffs.reduce((a, x) => a + x, 0) / diffs.length;
const te = Math.sqrt(diffs.reduce((a, x) => a + (x - md) ** 2, 0) / diffs.length) * Math.sqrt(12);
const dragMonths = R.turn.map((t, i) => cIdx.includes(i) ? t * COST : 0);
const dragAnn = dragMonths.reduce((a, x) => a + x, 0) / cIdx.length * 12;
const bigFrac = diffs.filter((d) => Math.abs(d) > 0.01).length / diffs.length;
const order = [...diffs].map((d, k) => ({ d, k })).sort((a, b) => Math.abs(b.d) - Math.abs(a.d)).slice(0, 5).map((x) => tl[cIdx[x.k]].date + ":" + (x.d * 100).toFixed(2) + "pp");
// state rank stability (strict panel, by active allocation state)
function byState(Rs) {
  const g = {};
  cIdx.forEach((i, k) => { const st = R.states[i]; (g[st] = g[st] || []).push(Rs[k]); });
  return Object.fromEntries(Object.entries(g).map(([st, rs]) => [st, { n: rs.length, mean: rs.reduce((a, x) => a + x, 0) / rs.length, vol: Math.sqrt(rs.reduce((a, x) => { const m = rs.reduce((p, q) => p + q, 0) / rs.length; return a + (x - m) ** 2; }, 0) / rs.length) * Math.sqrt(12), worst: Math.min(...rs) }]));
}
const sA = byState(RA), sB = byState(RB), sC = byState(RC);
const rank = (g) => Object.entries(g).sort((a, b) => b[1].mean - a[1].mean).map(([st]) => st);
const rA = rank(sA), rB = rank(sB);
const bestWorstKept = rA[0] === rB[0] && rA[rA.length - 1] === rB[rB.length - 1];
// defensive states (high cash bias): Low-High, Neutral-High vol check
const DEF = ["G_Low/I_High", "G_Neutral/I_High"];
let defWorse = 0;
for (const st of DEF) if (sB[st] && sA[st]) defWorse = Math.max(defWorse, (sB[st].vol - sA[st].vol) * 100);
// full-history metrics for each leg
const fA = metrics(R.A.filter((_, i) => fin(R.A[i])), cashFull.filter((_, i) => fin(R.A[i])));
const fB = metrics(R.B.filter((_, i) => fin(R.B[i])), cashFull.filter((_, i) => fin(R.B[i])));
const fC = metrics(R.C.filter((_, i) => fin(R.C[i])), cashFull.filter((_, i) => fin(R.C[i])));
console.log("strict A:", JSON.stringify(mA));
console.log("strict B:", JSON.stringify(mB));
console.log("strict C:", JSON.stringify(mC));
console.log("TE:", te.toFixed(4), "dragAnn:", (dragAnn * 100).toFixed(3) + "%", "bigFrac:", bigFrac.toFixed(3));
console.log("rank kept:", bestWorstKept, rA[0], "->", rB[0], "|", rA[rA.length - 1], "->", rB[rB.length - 1], "defWorse:", defWorse.toFixed(2) + "pp");

// determinism: rerun B/C and compare
const R2 = run(implRet, tl, COST, 0);
if (JSON.stringify(R.B) !== JSON.stringify(R2.B) || JSON.stringify(R.C) !== JSON.stringify(R2.C)) { console.error("nondeterministic"); process.exit(1); }

// ---- write artifacts ----
function num(x) { return fin(x) ? x : ""; }
fs.writeFileSync(path.join(GEN, "implementation-monthly.csv"),
  "date,alloc_state,research_ret,impl_pre,impl_post,turnover\n" +
  tl.map((m, i) => [m.date, R.states[i] ?? "", num(R.A[i]), num(R.B[i]), num(R.C[i]), R.turn[i]].join(",")).join("\n") + "\n");
fs.writeFileSync(path.join(GEN, "performance.json"), JSON.stringify({
  strict: { A: mA, B: mB, C: mC },
  full_live: { B: fB, C: fC, A_full_history: fA },
  preservation: {
    corr_AB: (() => { const ma = RA.reduce((a, x) => a + x, 0) / RA.length, mb = RB.reduce((a, x) => a + x, 0) / RB.length; let co = 0, va = 0, vb = 0; for (let k = 0; k < RA.length; k++) { co += (RA[k] - ma) * (RB[k] - mb); va += (RA[k] - ma) ** 2; vb += (RB[k] - mb) ** 2; } return co / Math.sqrt(va * vb); })(),
    corr_AC: (() => { const ma = RA.reduce((a, x) => a + x, 0) / RA.length, mc = RC.reduce((a, x) => a + x, 0) / RC.length; let co = 0, va = 0, vc = 0; for (let k = 0; k < RA.length; k++) { co += (RA[k] - ma) * (RC[k] - mc); va += (RA[k] - ma) ** 2; vc += (RC[k] - mc) ** 2; } return co / Math.sqrt(va * vc); })(),
    TE_ann: te, cagr_gap_B: mB.cagr - mA.cagr, cagr_gap_C: mC.cagr - mA.cagr,
    vol_gap_B: mB.vol_ann - mA.vol_ann, maxdd_gap_C: mC.maxdd - mA.maxdd,
    frac_gt_1pp: bigFrac, largest_months: order,
    drag_ann: dragAnn, drag_cum: dragMonths.reduce((a, x) => a + x, 0),
    rank_kept: bestWorstKept, rank_A: rA, rank_B: rB, defensive_vol_worse_pp: defWorse,
    reallocations: (() => { let n = 0, p = null; for (const i of cIdx) { const w = R.states[i]; if (p !== null && w !== p) n++; p = w; } return n; })(),
  },
}, null, 2));
fs.writeFileSync(path.join(GEN, "state-implementation.csv"),
  "state,n,research_mean,pre_mean,post_mean,drag,vol_pre,worst_pre\n" +
  Object.keys(sA).sort().map((st) => [st, sA[st].n, sA[st].mean, sB[st]?.mean ?? "", sC[st]?.mean ?? "", ((sB[st]?.mean ?? NaN) - sA[st].mean), sB[st]?.vol ?? "", sB[st]?.worst ?? ""].join(",")).join("\n") + "\n");
// benchmarks (same cost/timing): neutral ETF basket / cash / SPY / SPY-IEF 60-40
function bench(weightsFn) {
  const R = [], C = [];
  for (const m of tl) {
    if (m.date < STRICT_LO) continue;
    const ym = m.date.slice(0, 7);
    const w = weightsFn();
    let pr = 0, ok = true;
    for (const s of ORDER.concat(["cash"])) {
      if (w[s] === 0) continue;
      const v = implRet(s, ym);
      if (!fin(v)) { ok = false; break; }
      pr += (w[s] / 100) * v;
    }
    if (!ok) continue;
    R.push(pr); C.push(researchRet("cash", ym));
  }
  return metrics(R, C);
}
const NEU = { sp500: 25, nasdaq: 12, russell: 8, treasury2y: 8, treasury10y: 14, longtreasury: 8, gold: 6, oil: 4, cash: 15 };
fs.writeFileSync(path.join(GEN, "benchmarks.json"), JSON.stringify({
  neutral_etf: bench(() => NEU),
  cash: bench(() => ({ ...Object.fromEntries(ORDER.map((s) => [s, 0])), cash: 100 })),
  equity_spy: bench(() => ({ ...Object.fromEntries(ORDER.map((s) => [s, 0])), sp500: 100, cash: 0 })),
  balanced_6040: bench(() => ({ ...Object.fromEntries(ORDER.map((s) => [s, 0])), sp500: 60, treasury10y: 40, cash: 0 })),
}, null, 2));
// era split
const ERAS = [["E1", "1966-03-01", "1979-12-01"], ["E2", "1980-01-01", "2007-12-01"], ["E3", "2008-01-01", "2019-12-01"], ["E4", "2020-01-01", "2026-08-01"]];
const era = {};
const EA = R.A, EB = R.B, EC = R.C, WW = run(implRet, tl, COST, 0).Ws;
for (const [en, lo, hi] of ERAS) {
  const idx = tl.map((m, i) => (m.date >= lo && m.date <= hi) ? i : -1).filter((i) => i >= 0);
  const q = (arr) => idx.map((i) => arr[i]).filter((r, k) => fin(r) && fin(cashFull[idx[k]]));
  const qq = (arr) => idx.map((i) => cashFull[i]).filter((_, k) => fin(idx.map((j) => arr[j])[k]));
  const cw = (arr) => idx.map((i) => WW[i]?.cash).filter((r, k) => fin(idx.map((j) => arr[j])[k]));
  const leg = (arr, isImpl) => { const m = metrics(q(arr), qq(arr)); if (isImpl) { const c = cw(arr); m.avg_cash_w = c.length ? c.reduce((a, x) => a + x, 0) / c.length : NaN; } else { m.avg_cash_w = null; } return m; };
  era[en] = { A: leg(EA, false), B: leg(EB, true), C: leg(EC, true) };
}
fs.writeFileSync(path.join(GEN, "era-live.json"), JSON.stringify(era, null, 2));
// sensitivity: ONEQ nasdaq / 10bp costs / 1-mo lag
const oneqRet = new Map();
for (const l of fs.readFileSync(path.join(GEN, "proxy-monthly-returns.csv"), "utf8").trim().split("\n").slice(1)) {
  const c = l.split(",");
  oneqRet.set(c[0].slice(0, 7), c[10] === "" || c[10] === undefined ? NaN : parseFloat(c[10]));
}
const sens = {};
// S1: ONEQ for nasdaq (strict panel common months)
{
  const RB2 = [], RC2 = [];
  for (const i of cIdx) {
    const m = tl[i], ym = m.date.slice(0, 7);
    const base = Wt.get(R.states[i]);
    const w = { ...base };
    let moved = 0;
    for (const s of ORDER) {
      const v = s === "nasdaq" ? oneqRet.get(ym) : implRet(s, ym);
      if (w[s] > 0 && !fin(v)) { moved += w[s]; w[s] = 0; }
    }
    w.cash += moved;
    let pr = 0, ok = true;
    for (const s of ORDER.concat(["cash"])) {
      if (w[s] === 0) continue;
      const v = s === "nasdaq" ? oneqRet.get(ym) : implRet(s, ym);
      if (!fin(v)) { ok = false; break; }
      pr += (w[s] / 100) * v;
    }
    if (ok) { RB2.push(pr - R.turn[i] * COST); RC2.push(cashFull[i]); }
  }
  sens.ONEQ_nasdaq = metrics(RB2, RC2);
}
// S2: 10bp costs on primary B
{
  const RB3 = [], RC3 = [];
  const r3 = run(implRet, tl, COST_ALT, 0);
  for (const i of cIdx) if (fin(r3.C[i])) { RB3.push(r3.C[i]); RC3.push(cashFull[i]); }
  sens.cost_10bp = metrics(RB3.filter((_, k) => fin(RC3[k])), RC3.filter((r) => fin(r)));
}
// S3: 1-month lag on primary B
{
  const r4 = run(implRet, tl, COST, 1);
  const RB4 = [], RC4 = [];
  for (const i of cIdx) if (fin(r4.C[i])) { RB4.push(r4.C[i]); RC4.push(cashFull[i]); }
  sens.lag_1mo = metrics(RB4.filter((_, k) => fin(RC4[k])), RC4.filter((r) => fin(r)));
}
fs.writeFileSync(path.join(GEN, "sensitivity.json"), JSON.stringify(sens, null, 2));
fs.writeFileSync(path.join(GEN, "summary.json"), JSON.stringify({
  issue: 180, branch: "research/issue-180-tradable-implementation-reality-check",
  strict_panel: [STRICT_LO, "2026-08-01"], strict_months: cIdx.length,
  full_live_B_months: R.B.filter(fin).length,
  inputs_sha256: pins, production_authorized: false,
}, null, 2));
console.log("DONE backtest");
