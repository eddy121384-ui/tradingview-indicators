// Issue #178 — historical backtest (Node executor).
// Frozen: issue-178-weight-policy-prereg.md §§5-10. Runs ONLY post-matrix.
// No optimizer. No grid search. Zero costs. No Pine.
import fs from "node:fs";
import path from "node:path";
import crypto from "node:crypto";

const ROOT = process.cwd();
const RES = path.join(ROOT, "indicators/macro-pressure-map/research");
const GEN174 = path.join(RES, "generated/issue-174");
const GEN176 = path.join(RES, "generated/issue-176");
const GEN177 = path.join(RES, "generated/issue-177");
const GEN = path.join(RES, "generated/issue-178");
const sha256 = (b) => crypto.createHash("sha256").update(b).digest("hex");
const fin = (x) => typeof x === "number" && isFinite(x);

// ---- frozen policy (VERBATIM prereg) ----
const BASE = { sp500: 25, nasdaq: 12, russell: 8, treasury2y: 8, treasury10y: 14, longtreasury: 8, gold: 6, oil: 4 };
const BASE_S1 = { sp500: 30, nasdaq: 15, russell: 10, treasury2y: 6, treasury10y: 12, longtreasury: 7, gold: 5, oil: 3 };
const FAM = { sp500: "equity", nasdaq: "equity", russell: "equity", treasury2y: "rates", treasury10y: "rates", longtreasury: "rates", gold: "real", oil: "real" };
const MULT = { "0": 0, Low: 0.5, Neutral: 1.0, High: 1.75 };
const MULT_S2 = { "0": 0, Low: 0.25, Neutral: 1.0, High: 2.0 };
const SCAP = { sp500: 35, nasdaq: 20, russell: 15, treasury2y: 15, treasury10y: 25, longtreasury: 15, gold: 12, oil: 8 };
const FCAP = { equity: 60, rates: 50, real: 15 };
const CMIN_BIAS = { low: 5, neutral: 10, high: 20 };
const CASH_MAX = 60, CASH_MIN = 2;
const ORDER = ["sp500", "nasdaq", "russell", "treasury2y", "treasury10y", "longtreasury", "gold", "oil"];

function loadTiers() {
  const t = fs.readFileSync(path.join(GEN177, "policy-matrix.csv"), "utf8").trim().split("\n");
  const m = {};
  for (const l of t.slice(1)) {
    const c = l.split(",");
    if (c[1] === "cash") continue;
    m[c[0] + "|" + c[1]] = c[2];
  }
  const cb = {};
  for (const l of fs.readFileSync(path.join(GEN177, "cash-bias.csv"), "utf8").trim().split("\n").slice(1)) {
    const c = l.split(",");
    cb[c[0]] = c[1];
  }
  return { tiers: m, cbias: cb };
}
const { tiers, cbias } = loadTiers();

function computeWeights(state, available, base, mult) {
  const raw = {};
  for (const s of ORDER) {
    const m = mult[tiers[state + "|" + s]];
    if (!available.has(s) || m === 0) continue;
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

// ---- load macro states + returns ----
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
function loadRet(p, cols) {
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
const r174 = loadRet(path.join(GEN174, "nine-sleeve-monthly-returns.csv"));
const r176 = loadRet(path.join(GEN176, "hardened-monthly-returns.csv"));
// sleeve return(stock): hardened S&P w/ French fallback (flagged), investable oil, #174 others
const frenchFallbackMonths = [];
function sleeveRet(sl, ym) {
  if (sl === "sp500") {
    const h = r176.get(ym)?.sp500_tr_hardened;
    if (fin(h)) return { r: h, fb: false };
    const f = r174.get(ym)?.sp500;
    if (fin(f)) { frenchFallbackMonths.push(ym); return { r: f, fb: true }; }
    return { r: NaN, fb: false };
  }
  if (sl === "oil") {
    const v = r176.get(ym)?.oil_investable_return;
    return { r: fin(v) ? v : NaN, fb: false };
  }
  const v = r174.get(ym)?.[sl];
  return { r: fin(v) ? v : NaN, fb: false };
}
const ALLMOS = [...stateByDate.keys()].filter((d) => d >= "1966-03-01" && d <= "2026-08-01").sort();

// ---- allocation timeline ----
function timeline(confirm) {
  // returns [{date, allocState, weights}] for months with full info; B-2 starts 1966-05, immediate starts 1966-04
  const out = [];
  for (let i = 0; i < ALLMOS.length; i++) {
    const m = ALLMOS[i];
    if (m < "1966-05-01" && confirm) continue;
    if (m < "1966-04-01" && !confirm) continue;
    let allocState;
    if (confirm) {
      const a = stateByDate.get(ALLMOS[i - 1]), b = stateByDate.get(ALLMOS[i - 2]);
      if (a === undefined || b === undefined) continue;
      allocState = (a === b) ? a : null; // null = hold previous
    } else {
      allocState = stateByDate.get(ALLMOS[i - 1]);
      if (allocState === undefined) continue;
    }
    out.push({ date: m, allocState });
  }
  // forward-fill holds
  let last = null;
  for (const r of out) {
    if (r.allocState === null) r.allocState = last;
    else last = r.allocState;
  }
  return out.filter((r) => r.allocState !== null);
}

// ---- portfolio runner ----
function run(weightsFn, months, availFn) {
  const rets = [], cashr = [], states = [], Ws = [];
  const fams = { equity: [], rates: [], real: [], cash: [] };
  let prevW = null, switches = 0, stateChanges = 0, lastState = null, turnSum = 0, wchangeSum = 0;
  for (const m of months) {
    const ym = m.date.slice(0, 7);
    const avail = new Set(ORDER.filter((s) => fin(sleeveRet(s, ym).r) && fin(sleeveRet("cash", ym).r)));
    const w = weightsFn(m.allocState, avail);
    Ws.push(w);
    if (lastState !== null && m.allocState !== lastState) stateChanges++;
    lastState = m.allocState;
    if (prevW !== null && JSON.stringify(w) !== JSON.stringify(prevW)) {
      switches++;
      const ch = ORDER.concat(["cash"]).reduce((a, s) => a + Math.abs(w[s] - prevW[s]), 0) / 2;
      turnSum += ch; wchangeSum += ch;
    }
    prevW = w;
    let pr = 0, ok = true;
    for (const s of ORDER.concat(["cash"])) {
      if (w[s] === 0) continue; // §7: excluded sleeves need no return
      const { r } = sleeveRet(s, ym);
      if (!fin(r)) { ok = false; break; }
      pr += (w[s] / 100) * r;
    }
    if (!ok) { rets.push(NaN); cashr.push(NaN); states.push(m.allocState); continue; }
    rets.push(pr);
    cashr.push(sleeveRet("cash", ym).r);
    states.push(m.allocState);
    fams.equity.push(ORDER.filter((s) => FAM[s] === "equity").reduce((a, s) => a + w[s], 0));
    fams.rates.push(ORDER.filter((s) => FAM[s] === "rates").reduce((a, s) => a + w[s], 0));
    fams.real.push(ORDER.filter((s) => FAM[s] === "real").reduce((a, s) => a + w[s], 0));
    fams.cash.push(w.cash);
  }
  return { rets, cashr, states, Ws, fams, switches, stateChanges, turnSum, wchangeSum };
}
function metrics(rets, cashr) {
  const idx = rets.map((r, i) => fin(r) && fin(cashr[i]) ? i : -1).filter((i) => i >= 0);
  const R = idx.map((i) => rets[i]), C = idx.map((i) => cashr[i]);
  const n = R.length;
  const meanM = R.reduce((a, x) => a + x, 0) / n;
  const sdM = Math.sqrt(R.reduce((a, x) => a + (x - meanM) ** 2, 0) / n);
  const comp = R.reduce((a, x) => a * (1 + x), 1);
  const compC = C.reduce((a, x) => a * (1 + x), 1);
  const ex = R.map((r, i) => r - C[i]);
  const exM = ex.reduce((a, x) => a + x, 0) / n;
  const exSd = Math.sqrt(ex.reduce((a, x) => a + (x - exM) ** 2, 0) / n);
  let peak = 1, maxdd = 0, cum = 1;
  for (const r of R) { cum *= 1 + r; peak = Math.max(peak, cum); maxdd = Math.min(maxdd, cum / peak - 1); }
  return {
    n, cagr: Math.pow(comp, 12 / n) - 1, vol_ann: sdM * Math.sqrt(12),
    cash_excess_ann: (comp / compC) ** (12 / n) - 1,
    sharpe_like: exSd > 0 ? (exM * 12) / (exSd * Math.sqrt(12)) : NaN,
    maxdd, worst_month: Math.min(...R), pos_frac: R.filter((r) => r > 0).length / n,
  };
}

// ---- panels ----
const tlB2 = timeline(true);
const tlImm = timeline(false);
const FULL = { lo: "2000-09-01", hi: "2023-06-01" };
function inFull(m) { return m.date >= FULL.lo && m.date <= FULL.hi; }
// full-panel availability assertion: every month has all sleeves
const fullDrops = tlB2.filter(inFull).filter((m) => {
  const ym = m.date.slice(0, 7);
  return !ORDER.concat(["cash"]).every((s) => fin(sleeveRet(s, ym).r));
});
console.log("full-panel months:", tlB2.filter(inFull).length, "drops:", fullDrops.length);

const primaryW = (st, av) => {
  const w = computeWeights(st, av, BASE, MULT);
  const out = {}; for (const s of ORDER) out[s] = w[s] ?? 0; out.cash = w.cash; return out;
};
const benchW = {
  neutral: (st, av) => {
    const tot = ORDER.filter((s) => av.has(s)).reduce((a, s) => a + BASE[s] + (s === "cash" ? 0 : 0), 0);
    const baseAll = { ...BASE, cash: 15 };
    const availTot = ORDER.filter((s) => av.has(s)).reduce((a, s) => a + BASE[s], 0) + 15;
    const out = {};
    for (const s of ORDER) out[s] = av.has(s) ? BASE[s] / availTot * 100 : 0;
    out.cash = 15 / availTot * 100;
    return out;
  },
  cash100: () => ({ ...Object.fromEntries(ORDER.map((s) => [s, 0])), cash: 100 }),
  equity100: (st, av) => {
    const out = Object.fromEntries(ORDER.map((s) => [s, 0]));
    out.cash = 100; // French equity unavailable? never missing; kept for shape
    // 100% French market TR expressed via sp500 sleeve slot? No: use French directly below.
    return out;
  },
};

function runAll(label, wfn, tl, months) {
  const r = run(wfn, months, null);
  const met = metrics(r.rets, r.cashr);
  const to = r.turnSum / r.rets.length * 12 * 100; // annualized one-way % (weights in %)
  return { label, met, turnover_ann_pct: to / 100, switches: r.switches, stateChanges: r.stateChanges, avgWchange: r.switches ? r.wchangeSum / r.switches : 0, avgFam: Object.fromEntries(Object.entries(r.fams).map(([k, v]) => [k, v.reduce((a, x) => a + x, 0) / v.length])), months: r.rets.length };
}
// French equity + 60/40 need custom runners (benchmarks bypass sleeve slots)
function runFrench(months, wEq) {
  const rets = [], cashr = [];
  for (const m of months) {
    const ym = m.date.slice(0, 7);
    const e = r174.get(ym)?.sp500, b = r174.get(ym)?.treasury10y, c = r174.get(ym)?.cash;
    if (!fin(e) || !fin(b) || !fin(c)) { rets.push(NaN); cashr.push(NaN); continue; }
    rets.push(wEq * e + (1 - wEq) * (wEq === 1 ? 0 : b) + (wEq === 1 ? 0 : 0));
    cashr.push(c);
  }
  return { rets, cashr };
}

const results = {};
function panel(label, months) {
  const out = {};
  out.policy = runAll("policy", primaryW, null, months);
  const rb = run(benchW.neutral, months, null);
  out.neutral = { met: metrics(rb.rets, rb.cashr), months: rb.rets.length };
  const rc = run(benchW.cash100, months, null);
  out.cash = { met: metrics(rc.rets, rc.cashr), months: rc.rets.length };
  for (const [bn, wEq] of [["equity100", 1], ["balanced6040", 0.6]]) {
    const { rets, cashr } = runFrench(months, wEq);
    const R = rets.filter((r, i) => fin(r) && fin(cashr[i])), C = cashr.filter((_, i) => fin(rets[i]) && fin(cashr[i]));
    out[bn] = { met: metrics(R, C), months: R.length };
  }
  // per-state + era
  out.by_state = {};
  const fullR = run(primaryW, months, null);
  const states9 = [...new Set(fullR.states)];
  for (const st of states9) {
    const idx = fullR.states.map((s, i) => s === st ? i : -1).filter((i) => i >= 0);
    const R = idx.map((i) => fullR.rets[i]), C = idx.map((i) => fullR.cashr[i]);
    out.by_state[st] = { n: idx.length, ...metrics(R, C) };
  }
  const ERAS = [["E1", "1966-03-01", "1979-12-01"], ["E2", "1980-01-01", "2007-12-01"], ["E3", "2008-01-01", "2019-12-01"], ["E4", "2020-01-01", "2026-08-01"]];
  out.by_era = {};
  for (const [en, lo, hi] of ERAS) {
    const idx = months.map((m, i) => (m.date >= lo && m.date <= hi) ? i : -1).filter((i) => i >= 0);
    const R = idx.map((i) => fullR.rets[i]).filter((r, k) => fin(r) && fin(idx.map((i) => fullR.cashr[i])[k]));
    const C = idx.map((i) => fullR.cashr[i]).filter((_, k) => fin(idx.map((i) => fullR.rets[i])[k]));
    const Rb = idx.map((i) => rb.rets[i]).filter((r, k) => fin(r) && fin(idx.map((i) => rb.cashr[i])[k]));
    out.by_era[en] = { n: R.length, policy: metrics(R, C), neutral_n: Rb.length, neutral_cagr: Rb.length ? Math.pow(Rb.reduce((a, x) => a * (1 + x), 1), 12 / Rb.length) - 1 : NaN };
  }
  // time per state + avg cash
  out.time_state = {};
  for (const st of states9) out.time_state[st] = fullR.states.filter((s) => s === st).length;
  out.avg_cash = fullR.fams.cash.reduce((a, x) => a + x, 0) / fullR.fams.cash.length;
  out.avg_fam = Object.fromEntries(Object.entries(fullR.fams).map(([k, v]) => [k, v.reduce((a, x) => a + x, 0) / v.length]));
  out.switches = fullR.switches; out.stateChanges = fullR.stateChanges;
  out.turnover_ann = fullR.turnSum / fullR.rets.length * 12;
  out.avg_months_between = fullR.rets.length / Math.max(1, fullR.switches);
  out.monthly = months.map((m, i) => ({ date: m.date, state: fullR.states[i], ret: fullR.rets[i] }));
  return out;
}

results.max_history = panel("max", tlB2);
results.full_universe = panel("full", tlB2.filter(inFull));
// raw macro state changes (incl. 1-month flickers) vs allocation-affecting ones
function rawChanges(months) {
  let n = 0;
  for (let i = 1; i < months.length; i++) {
    const a = stateByDate.get(months[i].date), b = stateByDate.get(months[i - 1].date);
    if (a !== undefined && b !== undefined && a !== b) n++;
  }
  return n;
}
const RAW_MAX = rawChanges(tlB2);
const RAW_FULL = rawChanges(tlB2.filter(inFull));

// ---- sensitivity (frozen set, max-history + full) ----
function sensRun(kind) {
  const wfn = kind === "S1" ? ((st, av) => { const w = computeWeights(st, av, BASE_S1, MULT); const o = {}; for (const s of ORDER) o[s] = w[s] ?? 0; o.cash = w.cash; return o; })
    : kind === "S2" ? ((st, av) => { const w = computeWeights(st, av, BASE, MULT_S2); const o = {}; for (const s of ORDER) o[s] = w[s] ?? 0; o.cash = w.cash; return o; })
    : null;
  const out = {};
  for (const [pn, months] of [["max_history", tlB2], ["full_universe", tlB2.filter(inFull)]]) {
    const tl = kind === "S3" ? tlImm.filter((m) => pn === "max_history" ? true : inFull(m)) : months;
    const r = run(wfn ?? primaryW, tl, null);
    out[pn] = { met: metrics(r.rets, r.cashr), switches: r.switches, turnover_ann: r.turnSum / r.rets.length * 12, months: r.rets.length, avg_wchange: r.switches ? r.wchangeSum / r.switches : 0 };
  }
  return out;
}
results.sensitivity = { S1_alt_baseline: sensRun("S1"), S2_alt_multipliers: sensRun("S2"), S3_immediate: sensRun("S3") };

// determinism: rerun primary max-history metrics twice
const det1 = JSON.stringify(results.max_history.policy.met);
const rr = run(primaryW, tlB2, null);
const det2 = JSON.stringify(metrics(rr.rets, rr.cashr));
if (det1 !== det2) { console.error("nondeterministic backtest"); process.exit(1); }

fs.writeFileSync(path.join(GEN, "backtest-monthly.csv"),
  "date,alloc_state,port_ret\n" + results.max_history.monthly.map((r) => [r.date, r.state, fin(r.ret) ? r.ret : ""].join(",")).join("\n") + "\n");
const slim = (o) => o;
fs.writeFileSync(path.join(GEN, "performance.json"), JSON.stringify({ max_history: { policy: results.max_history.policy, by_state: results.max_history.by_state, time_state: results.max_history.time_state, avg_cash: results.max_history.avg_cash, avg_fam: results.max_history.avg_fam, switches: results.max_history.switches, stateChanges: results.max_history.stateChanges, turnover_ann: results.max_history.turnover_ann, avg_months_between: results.max_history.avg_months_between }, full_universe: { policy: results.full_universe.policy, by_state: results.full_universe.by_state, avg_cash: results.full_universe.avg_cash, switches: results.full_universe.switches, turnover_ann: results.full_universe.turnover_ann } }, null, 2));
fs.writeFileSync(path.join(GEN, "benchmarks.json"), JSON.stringify({ max_history: { neutral: results.max_history.neutral, cash: results.max_history.cash, equity100: results.max_history.equity100, balanced6040: results.max_history.balanced6040 }, full_universe: { neutral: results.full_universe.neutral, cash: results.full_universe.cash, equity100: results.full_universe.equity100, balanced6040: results.full_universe.balanced6040 } }, null, 2));
fs.writeFileSync(path.join(GEN, "turnover.json"), JSON.stringify({
  max_history: { turnover_ann: results.max_history.turnover_ann, switches: results.max_history.switches, stateChanges: results.max_history.stateChanges, raw_state_changes: RAW_MAX, avg_months_between: results.max_history.avg_months_between, avg_wchange: (() => { const r = run(primaryW, tlB2, null); return r.switches ? r.wchangeSum / r.switches : 0; })() },
  full_universe: { turnover_ann: results.full_universe.turnover_ann, switches: results.full_universe.switches, raw_state_changes: RAW_FULL },
}, null, 2));
fs.writeFileSync(path.join(GEN, "era-report.json"), JSON.stringify({ max_history: results.max_history.by_era, full_universe: results.full_universe.by_era }, null, 2));
fs.writeFileSync(path.join(GEN, "sensitivity.json"), JSON.stringify(results.sensitivity, null, 2));
fs.writeFileSync(path.join(GEN, "summary.json"), JSON.stringify({
  issue: 178, branch: "research/issue-178-state-weight-policy",
  french_fallback_months: [...new Set(frenchFallbackMonths)].sort(),
  full_drops: fullDrops.map((m) => m.date),
  policy_months_max: results.max_history.policy.months,
  policy_months_full: results.full_universe.policy.months,
  production_authorized: false,
}, null, 2));
console.log("policy max:", JSON.stringify(results.max_history.policy.met));
console.log("policy full:", JSON.stringify(results.full_universe.policy.met));
console.log("neutral max:", JSON.stringify(results.max_history.neutral.met));
console.log("french fallback months:", frenchFallbackMonths.length);
console.log("DONE backtest");
