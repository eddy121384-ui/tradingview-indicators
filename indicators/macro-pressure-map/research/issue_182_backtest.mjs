// Issue #182 — A/B/C overlay backtest (Node executor).
// Frozen: issue-182-v66-tactical-prereg.md. Runs ONLY post-prereg.
// A legs read VERBATIM from frozen parent files (byte-exact by construction).
// B/C build on frozen MATRIX weights (sums 100, no leverage) + overlay.
// Panel R minus Panel T separation kept throughout. No optimizer. No Pine.
import fs from "node:fs";
import path from "node:path";
import crypto from "node:crypto";

const ROOT = process.cwd();
const RES = path.join(ROOT, "indicators/macro-pressure-map/research");
const GEN178 = path.join(RES, "generated/issue-178");
const GEN180 = path.join(RES, "generated/issue-180");
const GEN = path.join(RES, "generated/issue-182");
const sha256 = (b) => crypto.createHash("sha256").update(b).digest("hex");
const fin = (x) => typeof x === "number" && isFinite(x);
const ORDER = ["sp500", "nasdaq", "russell", "treasury2y", "treasury10y", "longtreasury", "gold", "oil"];
const EQ = ["sp500", "nasdaq", "russell"];
const SCAP = { sp500: 35, nasdaq: 20, russell: 15 };

// ---- pins ----
const pins = {};
for (const f of ["weight-matrix.csv", "policy.json", "backtest-monthly.csv"]) pins["issue-178/" + f] = sha256(fs.readFileSync(path.join(GEN178, f)));
for (const f of ["implementation-monthly.csv", "proxy-monthly-returns.csv"]) pins["issue-180/" + f] = sha256(fs.readFileSync(path.join(GEN180, f)));
pins["issue-182/tactical-timeline.csv"] = sha256(fs.readFileSync(path.join(GEN, "tactical-timeline.csv")));
pins["issue-182/overlay-weights.csv"] = sha256(fs.readFileSync(path.join(GEN, "overlay-weights.csv")));
console.log("pins recorded");

// ---- frozen matrix weights ----
const SW = new Map();
{
  const t = fs.readFileSync(path.join(GEN178, "weight-matrix.csv"), "utf8").trim().split("\n");
  for (const l of t.slice(1)) {
    const c = l.split(",");
    SW.set(c[0], { sp500: +c[1], nasdaq: +c[2], russell: +c[3], treasury2y: +c[4], treasury10y: +c[5], longtreasury: +c[6], gold: +c[7], oil: +c[8], cash: +c[9] });
  }
}
// ---- DH states ----
function band(s) { if (s < -10) return "Low"; if (s > 10) return "High"; return "Neutral"; }
const macroT = fs.readFileSync(path.join(RES, "generated/issue-160/deep-history-v01-monthly.csv"), "utf8").trim().split("\n");
const mh = macroT[0].split(",");
const gi = mh.indexOf("growth_dh"), ii = mh.indexOf("inflation_dh");
const dhByDate = new Map(), dhG = new Map();
for (const l of macroT.slice(1)) {
  const c = l.split(",");
  const g = parseFloat(c[gi]), v = parseFloat(c[ii]);
  if (fin(g) && fin(v)) { dhByDate.set(c[0], "G_" + band(g) + "/I_" + band(v)); dhG.set(c[0], band(g)); }
}
const ALLMOS = [...dhByDate.keys()].filter((d) => d >= "1966-03-01" && d <= "2026-08-01").sort();
// ---- V6.6 signal ----
const v66sig = new Map(), v66growth = new Map();
for (const l of fs.readFileSync(path.join(GEN, "tactical-timeline.csv"), "utf8").trim().split("\n").slice(1)) {
  const c = l.split(",");
  v66sig.set(c[0].slice(0, 7), c[7]);
  v66growth.set(c[0].slice(0, 7), c[4]);
}
// ---- returns ----
function loadRet(p) {
  const t = fs.readFileSync(p, "utf8").trim().split("\n");
  const h = t[0].split(",").map((k) => k.trim());
  const m = new Map();
  for (const l of t.slice(1)) {
    const c = l.split(",");
    const r = {};
    h.forEach((k, j) => r[k] = j === 0 ? c[j] : (c[j] === "" ? NaN : parseFloat(c[j])));
    m.set(r.date.slice(0, 7), r);
  }
  return m;
}
const r174 = loadRet(path.join(RES, "generated/issue-174/nine-sleeve-monthly-returns.csv"));
const r176 = loadRet(path.join(RES, "generated/issue-176/hardened-monthly-returns.csv"));
const rPx = loadRet(path.join(GEN180, "proxy-monthly-returns.csv"));
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
// ---- structural B-2 timeline (frozen #178) ----
function structuralTL() {
  const out = [];
  for (let i = 0; i < ALLMOS.length; i++) {
    const m = ALLMOS[i];
    if (m < "1966-05-01") continue;
    const a = dhByDate.get(ALLMOS[i - 1]), b = dhByDate.get(ALLMOS[i - 2]);
    if (a === undefined || b === undefined) continue;
    out.push({ date: m, dhState: (a === b) ? a : null });
  }
  let last = null;
  for (const r of out) { if (r.dhState === null) r.dhState = last; else last = r.dhState; }
  return out.filter((r) => r.dhState !== null);
}
const tl = structuralTL();
// ---- A legs VERBATIM from frozen files + alignment proof ----
function loadFileLeg(p, col) {
  const m = new Map();
  for (const l of fs.readFileSync(p, "utf8").trim().split("\n").slice(1)) {
    const c = l.split(",");
    m.set(c[0], c[col] === "" || c[col] === undefined ? NaN : parseFloat(c[col]));
  }
  return m;
}
const fileAR = loadFileLeg(path.join(GEN178, "backtest-monthly.csv"), 2);
const fileAT = loadFileLeg(path.join(GEN180, "implementation-monthly.csv"), 3);
const fileATstate = new Map();
for (const l of fs.readFileSync(path.join(GEN180, "implementation-monthly.csv"), "utf8").trim().split("\n").slice(1)) {
  const c = l.split(",");
  fileATstate.set(c[0], c[1]);
}
// matrix-base recompute (policy-correct base for B/C + base_effect)
function matrixBaseRet(retFn, state, ym) {
  const w = SW.get(state);
  let p = 0;
  for (const s of ORDER.concat(["cash"])) {
    if (w[s] === 0) continue;
    const r = retFn(s, ym);
    if (!fin(r)) return NaN;
    p += w[s] / 100 * r;
  }
  return p;
}
// cross-check: matrix-based tradable recompute MUST match #180 file (proves #180 has no analogous bug)
{
  let mism = 0, n = 0;
  for (const m of tl) {
    if (m.date < "2007-02-01") continue;
    const ym = m.date.slice(0, 7);
    const ref = fileAT.get(m.date);
    if (ref === undefined) continue;
    // #180 impl_pre used matrix weights; recompute identically
    const w = SW.get(m.dhState);
    let p = 0, ok = true;
    for (const s of ORDER.concat(["cash"])) {
      if (w[s] === 0) continue;
      const r = implRet(s, ym);
      if (!fin(r)) { ok = false; break; }
      p += w[s] / 100 * r;
    }
    // #180 availability: missing proxy -> excluded? #180 run: weight->cash? mirror by NaN rule:
    if (fin(ref)) {
      n++;
      // note: #180 excluded missing sleeves (weight to cash) — replicate exactly:
      const w2 = { ...w };
      let moved = 0;
      for (const s of ORDER) if (w2[s] > 0 && !fin(implRet(s, ym))) { moved += w2[s]; w2[s] = 0; }
      w2.cash += moved;
      let p2 = 0, ok2 = true;
      for (const s of ORDER.concat(["cash"])) {
        if (w2[s] === 0) continue;
        const r = implRet(s, ym);
        if (!fin(r)) { ok2 = false; break; }
        p2 += w2[s] / 100 * r;
      }
      const mine = ok2 ? p2 : NaN;
      if ((fin(mine) !== fin(ref)) || (fin(mine) && Math.abs(mine - ref) > 1e-12)) mism++;
    }
  }
  console.log("tradable-A cross-check: n=" + n + " mism=" + mism);
  if (mism > 0) process.exit(1);
}
// ---- overlay application (frozen §3) ----
const COST = 0.0002, COST_ALT = 0.0010;
function overlayW(base, signal, budget) {
  const w = { ...base };
  const eq = EQ.filter((s) => w[s] > 0);
  const E = eq.reduce((a, s) => a + w[s], 0);
  if (signal === "risk-on") {
    const head = eq.reduce((a, s) => a + (SCAP[s] - w[s]), 0);
    let add = Math.min(budget, Math.max(0, w.cash - 2), 60 - E, head);
    add = Math.max(0, add);
    if (E > 0 && add > 0) {
      for (const s of eq) {
        const share = add * w[s] / E;
        const take = Math.min(share, SCAP[s] - w[s]);
        w[s] += take;
        w.cash -= take;
      }
    }
  } else if (signal === "risk-off") {
    const cut = Math.min(budget, E);
    if (E > 0 && cut > 0) {
      for (const s of eq) w[s] -= cut * w[s] / E;
      w.cash += cut;
    }
  }
  return w;
}
function prevMonth(d) { let y = +d.slice(0, 4), m = +d.slice(5, 7) - 1; if (m < 1) { m = 12; y--; } return String(y).padStart(4, "0") + "-" + String(m).padStart(2, "0") + "-01"; }
// ---- main runner: B/C on a return basis; A from files ----
function runPanel(retFn, budget, lagV66, costRate) {
  const rows = [];
  let prevWB = null;
  for (const m of tl) {
    if (m.date < "2007-02-01") continue;
    const ym = m.date.slice(0, 7);
    let sm = m.date;
    for (let k = 0; k < lagV66 + 1; k++) sm = prevMonth(sm);
    const sig = v66sig.get(sm.slice(0, 7));
    if (sig === undefined) continue; // no proxy-fill, ever
    const base = SW.get(m.dhState);
    const w = overlayW(base, sig, budget);
    let pb = 0, okb = true;
    for (const s of ORDER.concat(["cash"])) {
      if (w[s] === 0) continue;
      const r = retFn(s, ym);
      if (!fin(r)) { okb = false; break; }
      pb += w[s] / 100 * r;
    }
    const toB = prevWB ? ORDER.concat(["cash"]).reduce((a, s) => a + Math.abs(w[s] - prevWB[s]), 0) / 2 / 100 : 0;
    rows.push({ date: m.date, dh: m.dhState, sig, vg: v66growth.get(sm.slice(0, 7)) ?? null, B: okb ? pb : NaN, C: okb ? pb - toB * costRate : NaN, turnB: toB, wB: { ...w } });
    prevWB = { ...w };
  }
  return rows;
}
const PR = runPanel(researchRet, 5, 0, COST);
const PT = runPanel(implRet, 5, 0, COST);
// attach file-verbatim A legs + alignment proof
{
  let mismR = 0, nR = 0, mismT = 0, nT = 0;
  for (const r of PR) {
    const f = fileAR.get(r.date);
    if (f === undefined) { console.error("A_R missing month", r.date); process.exit(1); }
    r.A = f; nR++;
  }
  for (const r of PT) {
    const f = fileAT.get(r.date);
    if (f === undefined) { console.error("A_T missing month", r.date); process.exit(1); }
    r.A = f; nT++;
    if (fileATstate.get(r.date) !== r.dh) { console.error("timeline drift", r.date); process.exit(1); }
  }
  console.log("A legs attached verbatim: R n=" + nR + " T n=" + nT + " (0 recompute mismatches by construction; parents byte-frozen)");
}
// determinism: rerun B/C and compare
const PR2 = runPanel(researchRet, 5, 0, COST);
if (JSON.stringify(PR.map((r) => [r.B, r.C])) !== JSON.stringify(PR2.map((r) => [r.B, r.C]))) { console.error("nondeterministic"); process.exit(1); }
// ---- metrics ----
function downside(rs) {
  const v = rs.filter(fin);
  if (!v.length) return NaN;
  return Math.sqrt(v.reduce((a, x) => a + Math.min(x, 0) ** 2, 0) / v.length) * Math.sqrt(12);
}
function metrics(R, C) {
  const idx = R.map((r, i) => fin(r) && fin(C[i]) ? i : -1).filter((i) => i >= 0);
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
  return { n, cagr: comp ** (12 / n) - 1, vol_ann: sd * Math.sqrt(12), cash_excess_ann: (comp / compC) ** (12 / n) - 1, sharpe_like: esd > 0 ? (em * 12) / (esd * Math.sqrt(12)) : NaN, maxdd: dd, worst_month: Math.min(...Rs), pos_frac: Rs.filter((r) => r > 0).length / n, downside_vol: downside(Rs) };
}
function structTurn(rows) {
  let prev = null, sum = 0, n = 0;
  for (const r of rows) {
    const w = SW.get(r.dh);
    if (prev) sum += ORDER.concat(["cash"]).reduce((a, s) => a + Math.abs(w[s] - prev[s]), 0) / 2 / 100;
    prev = { ...w };
    n++;
  }
  return sum / n * 12;
}
function annTurn(rows) {
  const t = rows.map((r) => r.turnB).filter(fin);
  return t.reduce((a, x) => a + x, 0) / rows.length * 12;
}
function sigFreq(rows) {
  const c = { "risk-on": 0, "risk-off": 0, neutral: 0 };
  for (const r of rows) c[r.sig]++;
  const n = rows.length;
  return { n, ...Object.fromEntries(Object.entries(c).map(([k, v]) => [k, v / n])) };
}
function avgW(rows, key) {
  // average Equity / Cash weight from stored wB
  let se = 0, sc = 0, n = 0;
  for (const r of rows) {
    if (!r.wB) continue;
    se += EQ.reduce((a, s) => a + r.wB[s], 0);
    sc += r.wB.cash;
    n++;
  }
  return { equity: se / n, cash: sc / n };
}
// ---- incremental + concentration ----
function incremental(rows, cash) {
  const B = rows.map((r) => r.B), C = rows.map((r) => r.C), A = rows.map((r) => r.A);
  const idx = rows.map((_, i) => i).filter((i) => fin(A[i]) && fin(B[i]) && fin(C[i]) && fin(cash[i]));
  const dBC = idx.map((i) => C[i] - A[i]);
  const comp = (arr) => arr.reduce((a, x) => a * (1 + x), 1);
  const cagrOf = (arr) => comp(arr) ** (12 / arr.length) - 1;
  const RA = idx.map((i) => A[i]), RC = idx.map((i) => C[i]);
  // contribution episodes: maximal runs of identical tactical class
  const eps = [];
  let cur = null;
  for (const i of idx) {
    const s = rows[i].sig;
    if (!cur || cur.sig !== s) { if (cur) eps.push(cur); cur = { sig: s, sum: 0, n: 0 }; }
    cur.sum += RC[idx.indexOf(i)] - RA[idx.indexOf(i)];
    cur.n++;
  }
  if (cur) eps.push(cur);
  const pos = eps.filter((e) => e.sum > 0).sort((a, b) => b.sum - a.sum);
  const totPos = pos.reduce((a, e) => a + e.sum, 0);
  // A-vs-C correlation
  const ma = RA.reduce((a, x) => a + x, 0) / RA.length, mc = RC.reduce((a, x) => a + x, 0) / RC.length;
  let co = 0, va = 0, vc = 0;
  for (let k = 0; k < RA.length; k++) { co += (RA[k] - ma) * (RC[k] - mc); va += (RA[k] - ma) ** 2; vc += (RC[k] - mc) ** 2; }
  return {
    n: idx.length,
    cagr_BmA: cagrOf(idx.map((i) => rows[i].B)) - cagrOf(RA),
    cagr_CmA: cagrOf(RC) - cagrOf(RA),
    frac_gt_50bp: dBC.filter((d) => Math.abs(d) > 0.005).length / dBC.length,
    corr_AC: co / Math.sqrt(va * vc),
    top1_share: totPos > 0 ? pos[0].sum / totPos : null,
    top3_share: totPos > 0 ? pos.slice(0, 3).reduce((a, e) => a + e.sum, 0) / totPos : null,
    n_episodes: eps.length,
  };
}
// ---- state diagnostics ----
function stateDiag(rows, cash) {
  const out = {};
  for (const r of rows) {
    const k = r.dh;
    out[k] = out[k] || { n: 0, A: [], C: [] };
    const i = rows.indexOf(r);
    if (fin(r.A) && fin(r.C) && fin(cash[rows.indexOf(r)])) { out[k].n++; out[k].A.push(r.A); out[k].C.push(r.C); }
  }
  for (const k of Object.keys(out)) {
    const { A, C, n } = out[k];
    const mean = (a) => a.reduce((x, y) => x + y, 0) / a.length;
    const sd = (a) => { const m = mean(a); return Math.sqrt(a.reduce((x, y) => x + (y - m) ** 2, 0) / a.length) * Math.sqrt(12); };
    out[k] = { n, A_mean: n ? mean(A) : NaN, C_mean: n ? mean(C) : NaN, contrib: n ? mean(C) - mean(A) : NaN, C_ann: n ? (C.reduce((x, y) => x * (1 + y), 1)) ** (12 / n) - 1 : NaN, vol_diff: n ? sd(C) - sd(A) : NaN };
  }
  return out;
}
// ---- V6.6 + alignment + transition diagnostics ----
function v66Diag(rows, cash) {
  const cls = { "risk-on": { d: [], n: 0 }, "risk-off": { d: [], n: 0 }, neutral: { d: [], n: 0 } };
  const cells = {};
  const ali = { aligned: [], divergent: [] };
  for (let i = 0; i < rows.length; i++) {
    const r = rows[i];
    if (!fin(r.A) || !fin(r.C) || !fin(cash[i])) continue;
    const d = r.C - r.A;
    cls[r.sig].d.push(d); cls[r.sig].n++;
    const ck = r.dh + "|" + r.sig;
    cells[ck] = (cells[ck] || 0) + 1;
    const dhg = r.dh.split("/")[0].slice(2);
    ((dhg === r.vg) ? ali.aligned : ali.divergent).push(d);
  }
  const mean = (a) => a.length ? a.reduce((x, y) => x + y, 0) / a.length : NaN;
  return {
    by_class: Object.fromEntries(Object.entries(cls).map(([k, v]) => [k, { n: v.n, mean_contrib: mean(v.d) }])),
    cell_counts: cells,
    aligned: { n: ali.aligned.length, mean_contrib: mean(ali.aligned) },
    divergent: { n: ali.divergent.length, mean_contrib: mean(ali.divergent) },
  };
}
function transDiag(rows, cash) {
  const chg = new Set();
  for (let i = 1; i < rows.length; i++) if (rows[i].dh !== rows[i - 1].dh) chg.add(i);
  const inWin = new Set();
  for (const i of chg) for (let k = -3; k <= 3; k++) if (rows[i + k]) inWin.add(i + k);
  const inside = [], outside = [];
  const fq = { "risk-on": 0, "risk-off": 0, neutral: 0 };
  rows.forEach((r, i) => {
    if (!fin(r.A) || !fin(r.C) || !fin(cash[i])) return;
    (inWin.has(i) ? inside : outside).push(r.C - r.A);
    if (inWin.has(i)) fq[r.sig]++;
  });
  const mean = (a) => a.length ? a.reduce((x, y) => x + y, 0) / a.length : NaN;
  return { n_transitions: chg.size, n_inside: inside.length, n_outside: outside.length, mean_inside: mean(inside), mean_outside: mean(outside), freq_inside: fq };
}
function eraSeg(rows, cash) {
  const segs = { pre2020: [], y2022: [], post2023: [] };
  rows.forEach((r, i) => {
    if (!fin(r.A) || !fin(r.C) || !fin(cash[i])) return;
    const rec = { A: r.A, C: r.C, cash: cash[i] };
    if (r.date < "2020-01-01") segs.pre2020.push(rec);
    else if (r.date <= "2022-12-01") segs.y2022.push(rec);
    else segs.post2023.push(rec);
  });
  const out = {};
  for (const [k, v] of Object.entries(segs)) {
    const cagrOf = (arr) => arr.length ? arr.reduce((a, x) => a * (1 + x), 1) ** (12 / arr.length) - 1 : NaN;
    const ddOf = (arr) => { let peak = 1, dd = 0, cum = 1; for (const r of arr) { cum *= 1 + r; peak = Math.max(peak, cum); dd = Math.min(dd, cum / peak - 1); } return arr.length ? dd : NaN; };
    const A = v.map((x) => x.A), C = v.map((x) => x.C);
    out[k] = { n: v.length, cagr_A: cagrOf(A), cagr_C: cagrOf(C), contrib: cagrOf(C) - cagrOf(A), maxdd_A: ddOf(A), maxdd_C: ddOf(C) };
  }
  return out;
}
// ---- assemble outputs ----
function cashOf(rows, retFn) {
  return rows.map((r) => retFn("cash", r.date.slice(0, 7)));
}
const cashR = cashOf(PR, researchRet), cashT = cashOf(PT, implRet);
function legs(rows, cash) {
  return {
    A: metrics(rows.map((r) => r.A), cash),
    B: metrics(rows.map((r) => r.B), cash),
    C: metrics(rows.map((r) => r.C), cash),
  };
}
const perfR = legs(PR, cashR), perfT = legs(PT, cashT);
const incrR = incremental(PR, cashR), incrT = incremental(PT, cashT);
const stR = stateDiag(PR, cashR), stT = stateDiag(PT, cashT);
const vR = v66Diag(PR, cashR), vT = v66Diag(PT, cashT);
const trR = transDiag(PR, cashR), trT = transDiag(PT, cashT);
const erR = eraSeg(PR, cashR), erT = eraSeg(PT, cashT);
function sigSwitches(rows) {
  let n = 0;
  for (let i = 1; i < rows.length; i++) if (rows[i].sig !== rows[i - 1].sig) n++;
  return n;
}
const toR = { B_ann: annTurn(PR), struct_ann: structTurn(PR), tactical_active_months: PR.filter((r) => r.sig !== "neutral").length, tactical_switches: sigSwitches(PR), freq: sigFreq(PR), avgW: avgW(PR) };
const toT = { B_ann: annTurn(PT), struct_ann: structTurn(PT), tactical_active_months: PT.filter((r) => r.sig !== "neutral").length, tactical_switches: sigSwitches(PT), freq: sigFreq(PT), avgW: avgW(PT) };
toR.incr_ann = toR.B_ann - toR.struct_ann;
toT.incr_ann = toT.B_ann - toT.struct_ann;
// cost drag (C vs B, annualized)
function dragAnn(rows) {
  const d = rows.map((r) => (fin(r.B) && fin(r.C)) ? r.B - r.C : NaN).filter(fin);
  return d.reduce((a, x) => a + x, 0) / rows.length * 12;
}
// ---- gates (frozen §8, PRIMARY tradable panel) ----
function gates(perf, incr, to, erSeg, stDiag) {
  const cagrGap = incr.cagr_CmA * 100;
  const sharpeGap = perf.C.sharpe_like - perf.A.sharpe_like;
  const maxddGap = (perf.C.maxdd - perf.A.maxdd) * 100;
  const incrTo = to.incr_ann * 100;
  const benefitPos = incr.cagr_CmA > 0;
  const conc = benefitPos ? (incr.top1_share ?? 1) : null;
  const segGaps = Object.values(erSeg).map((s) => (s.contrib ?? NaN) * 100).filter(fin);
  const worstSeg = segGaps.length ? Math.min(...segGaps) : NaN;
  const stGaps = Object.values(stDiag).filter((s) => s.n >= 12).map((s) => (s.contrib ?? NaN) * 12 * 100).filter(fin);
  const worstState = stGaps.length ? Math.min(...stGaps) : NaN;
  const g = {
    g1_cagr: cagrGap >= -0.50,
    g2_sharpe: sharpeGap >= -0.05,
    g3_maxdd: maxddGap >= -3.0,
    g4_turnover: incrTo <= 40.0,
    g5_concentration: !benefitPos ? true : conc <= 0.60,
    g6_segment: worstSeg >= -1.0,
    g7_state: worstState >= -3.0,
  };
  const fails = Object.values(g).filter((v) => !v).length;
  let verdict;
  if (fails === 0) verdict = "v66_tactical_overlay_candidate_supported";
  else if (incr.cagr_CmA > 0 && g.g3_maxdd && g.g7_state && fails <= 2) verdict = "v66_tactical_overlay_candidate_suggestive";
  else verdict = "v66_tactical_overlay_not_supported";
  return { values: { cagr_gap_pp: cagrGap, sharpe_gap: sharpeGap, maxdd_gap_pp: maxddGap, incr_turnover_pp: incrTo, top1_share: conc, benefit_positive: benefitPos, worst_seg_pp: worstSeg, worst_state_pp: worstState }, gates: g, fails, verdict };
}
const G = gates(perfT, incrT, toT, erT, stT);
// ---- sensitivities S1/S2/S3 (primary panel) ----
function sensRun(budget, lagV66, costRate) {
  const rows = [];
  let prevWB = null;
  for (const m of tl) {
    if (m.date < "2007-02-01") continue;
    const ym = m.date.slice(0, 7);
    let sm = m.date;
    for (let k = 0; k < lagV66 + 1; k++) sm = prevMonth(sm);
    const sig = v66sig.get(sm.slice(0, 7));
    if (sig === undefined) continue;
    const base = SW.get(m.dhState);
    const w = overlayW(base, sig, budget);
    let pb = 0, okb = true;
    for (const s of ORDER.concat(["cash"])) {
      if (w[s] === 0) continue;
      const r = implRet(s, ym);
      if (!fin(r)) { okb = false; break; }
      pb += (w[s] / 100) * r;
    }
    const toB = prevWB ? ORDER.concat(["cash"]).reduce((a, s) => a + Math.abs(w[s] - prevWB[s]), 0) / 2 / 100 : 0;
    rows.push({ date: m.date, dh: m.dhState, sig, B: okb ? pb : NaN, C: okb ? pb - toB * costRate : NaN });
    prevWB = { ...w };
  }
  return rows;
}
const sens = {};
for (const [name, b, l, c] of [["S1_budget10", 10, 0, COST], ["S2_lag2", 5, 1, COST], ["S3_cost10bp", 5, 0, COST_ALT]]) {
  const rows = sensRun(b, l, c);
  const cc = rows.map((r) => implRet("cash", r.date.slice(0, 7)));
  sens[name] = { C: metrics(rows.map((r) => r.C), cc), incr_vs_primary_C_cagr_pp: (metrics(rows.map((r) => r.C), cc).cagr - perfT.C.cagr) * 100 };
}
// ---- benchmarks on V6.6 panel (frozen #180 definitions, proxy returns) ----
function bench(weightsFn) {
  const R = [], C = [];
  for (const m of tl) {
    if (m.date < "2007-02-01") continue;
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
    R.push(pr); C.push(implRet("cash", ym));
  }
  return metrics(R, C);
}
const NEU = { sp500: 25, nasdaq: 12, russell: 8, treasury2y: 8, treasury10y: 14, longtreasury: 8, gold: 6, oil: 4, cash: 15 };
const benchmarks = {
  neutral_etf: bench(() => NEU),
  cash: bench(() => ({ ...Object.fromEntries(ORDER.map((s) => [s, 0])), cash: 100 })),
  equity_spy: bench(() => ({ ...Object.fromEntries(ORDER.map((s) => [s, 0])), sp500: 100, cash: 0 })),
  balanced_6040: bench(() => ({ ...Object.fromEntries(ORDER.map((s) => [s, 0])), sp500: 60, treasury10y: 40, cash: 0 })),
};
// ---- write artifacts ----
function num(x) { return fin(x) ? x : ""; }
fs.writeFileSync(path.join(GEN, "performance.json"), JSON.stringify({ research: { A: perfR.A, B: perfR.B, C: perfR.C }, tradable: { A: perfT.A, B: perfT.B, C: perfT.C } }, null, 2));
fs.writeFileSync(path.join(GEN, "incremental.json"), JSON.stringify({ research: incrR, tradable: incrT, turnover_R: toR, turnover_T: toT, drag_R_ann_pp: dragAnn(PR) * 100, drag_T_ann_pp: dragAnn(PT) * 100 }, null, 2));
fs.writeFileSync(path.join(GEN, "state-diagnostics.csv"),
  "panel,state,n,A_mean,C_mean,contrib,C_ann,vol_diff\n" +
  Object.entries({ research: stR, tradable: stT }).flatMap(([p, t]) => Object.entries(t).map(([st, v]) => [p, st, v.n, v.A_mean, v.C_mean, v.contrib, v.C_ann, v.vol_diff].join(","))).join("\n") + "\n");
fs.writeFileSync(path.join(GEN, "v66-diagnostics.json"), JSON.stringify({ research: vR, tradable: vT }, null, 2));
fs.writeFileSync(path.join(GEN, "alignment.json"), JSON.stringify({ research: { aligned: vR.aligned, divergent: vR.divergent }, tradable: { aligned: vT.aligned, divergent: vT.divergent } }, null, 2));
fs.writeFileSync(path.join(GEN, "transition.json"), JSON.stringify({ research: trR, tradable: trT }, null, 2));
fs.writeFileSync(path.join(GEN, "era-stability.json"), JSON.stringify({ research: erR, tradable: erT }, null, 2));
fs.writeFileSync(path.join(GEN, "sensitivity.json"), JSON.stringify(sens, null, 2));
fs.writeFileSync(path.join(GEN, "benchmarks.json"), JSON.stringify(benchmarks, null, 2));
fs.writeFileSync(path.join(GEN, "overlay-policy.json"), JSON.stringify({
  issue: 182, budget_pp: 5, scope: "total Equity <-> Cash only", pro_rata: "frozen structural equity weights",
  caps: { sleeve: SCAP, family: 60, cash_floor: 2 }, timing: "V6.6 state(m-1) -> month m; alternate lag state(m-2)",
  costs: { primary_rate: COST, alternate_rate: COST_ALT }, panels: { research: "2007-01+ backbone", tradable: "2007-01+ ETF" },
  verdict: G.verdict, gates: G.gates, gate_values: G.values, production_authorized: false,
}, null, 2));
fs.writeFileSync(path.join(GEN, "summary.json"), JSON.stringify({
  issue: 182, branch: "research/issue-182-v66-tactical-overlay",
  verdict: G.verdict, gates: G.gates, gate_values: G.values,
  months_research: perfR.C.n, months_tradable: perfT.C.n,
  inputs_sha256: pins, production_authorized: false,
}, null, 2));
fs.writeFileSync(path.join(GEN, "structural-vs-overlay.csv"),
  "panel,date,dh_state,v66_signal,A,B,C\n" +
  PR.map((r) => ["research", r.date, r.dh, r.sig, num(r.A), num(r.B), num(r.C)].join(",")).concat(
    PT.map((r) => ["tradable", r.date, r.dh, r.sig, num(r.A), num(r.B), num(r.C)].join(","))).join("\n") + "\n");
console.log("research A/B/C:", JSON.stringify({ A: perfR.A.cagr, B: perfR.B.cagr, C: perfR.C.cagr }));
console.log("tradable A/B/C:", JSON.stringify({ A: perfT.A.cagr, B: perfT.B.cagr, C: perfT.C.cagr }));
console.log("gates:", JSON.stringify(G.gates), "verdict:", G.verdict);
console.log("DONE backtest");
