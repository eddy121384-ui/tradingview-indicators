#!/usr/bin/env node
// Issue #183 ??corrected lineage replay: Phase A (#178), Phase B (#180), Phase C (#182).
//
// Frozen contract: indicators/macro-pressure-map/research/issue-183-lineage-repair-spec.md
//
// Repair scope: the ONLY change vs the frozen parents is the #178 Cash-bias parser
// defect (issue_178_backtest.mjs loadTiers() read cash-bias.csv column 1
// `opportunity_score` instead of column 2 `cash_bias`). The corrected engine
// consumes the frozen 9x9 target weight matrix directly (matrix-as-truth) and
// reconstructs weights from frozen policy components using the CORRECT column
// only as a verification path.
//
// No policy parameter is changed. No optimizer. No grid search. No Pine changes.
// Parents are read-only. All writes go to research/generated/issue-183/.
//
// Reads are CRLF-normalised: the historical parents were produced on LF content
// and this Windows checkout converts text files to CRLF. Numeric parsing is
// CRLF-safe, but string fields (V6.6 `signal`) are not ??normalising to LF makes
// this replay byte-identical to the parent semantics.

import fs from "node:fs";
import path from "node:path";
import crypto from "node:crypto";
import zlib from "node:zlib";
import { execFileSync } from "node:child_process";

const ROOT = process.cwd();
const RES = path.join(ROOT, "indicators/macro-pressure-map/research");
const GEN183 = path.join(RES, "generated/issue-183");
const BIG = 1 << 28;

const sha256 = (b) => crypto.createHash("sha256").update(b).digest("hex");
const fin = (x) => typeof x === "number" && Number.isFinite(x);
const readLF = (rel) => fs.readFileSync(path.join(RES, rel), "utf8").replace(/\r/g, "");
const shaWt = (rel) => sha256(fs.readFileSync(path.join(RES, rel)));
const REPO_REL = "indicators/macro-pressure-map/research";
const shaBlob = (rev, rel) => sha256(execFileSync("git", ["show", `${rev}:${REPO_REL}/${rel}`], { maxBuffer: BIG, cwd: ROOT }));

// ---------------------------------------------------------------- frozen policy
const ORDER = ["sp500", "nasdaq", "russell", "treasury2y", "treasury10y", "longtreasury", "gold", "oil"];
const EQ = ["sp500", "nasdaq", "russell"];
const FAM = { sp500: "equity", nasdaq: "equity", russell: "equity", treasury2y: "rates", treasury10y: "rates", longtreasury: "rates", gold: "real", oil: "real" };
const SCAP = { sp500: 35, nasdaq: 20, russell: 15, treasury2y: 15, treasury10y: 25, longtreasury: 15, gold: 12, oil: 8 };
const FCAP = { equity: 60, rates: 50, real: 15 };
const ZEROS = [["G_Low/I_Low", "oil"], ["G_Neutral/I_High", "russell"], ["G_High/I_Low", "gold"]];
const CMIN_BIAS = { low: 5, neutral: 10, high: 20 };
const BASE = { sp500: 25, nasdaq: 12, russell: 8, treasury2y: 8, treasury10y: 14, longtreasury: 8, gold: 6, oil: 4 };
const BASE_S1 = { sp500: 30, nasdaq: 15, russell: 10, treasury2y: 6, treasury10y: 12, longtreasury: 7, gold: 5, oil: 3 };
const MULT = { 0: 0, Low: 0.5, Neutral: 1.0, High: 1.75 };
const MULT_S2 = { 0: 0, Low: 0.25, Neutral: 1.0, High: 2.0 };
const CASH_MIN = 2;
const CASH_MAX = 60;
const COST = 0.0002;
const COST_ALT = 0.0010;
const TOL = 1e-9;

const PARENTS = {
  "issue-177": "bc652bd615f2c5e9137050d01c666dbcd9528cd3",
  "issue-178": "10dcdce0ec86b0493d6df6b916b720eba46dcbe6",
  "issue-180": "ac251ad5149d9f550d82dfb34b3551fe01032367",
  "issue-182": "57852112ce95913d48297b35f803a1583cbab314",
};
const REQUIRED_HEAD = "57852112ce95913d48297b35f803a1583cbab314";

const G174 = "generated/issue-174";
const G176 = "generated/issue-176";
const G177 = "generated/issue-177";
const G178 = "generated/issue-178";
const G180 = "generated/issue-180";
const G182 = "generated/issue-182";

// ---------------------------------------------------------------- frozen matrix
function loadMatrix() {
  const t = readLF(`${G178}/weight-matrix.csv`).trim().split("\n");
  const header = t[0].split(",");
  const m = new Map();
  for (const l of t.slice(1)) {
    const c = l.split(",");
    const w = {};
    for (const s of ORDER) w[s] = +c[header.indexOf(s)];
    w.cash = +c[header.indexOf("cash")];
    w._total = +c[header.indexOf("total")];
    w._binds = c[header.indexOf("binds")];
    w._cash_bias = c[header.indexOf("cash_bias")];
    m.set(c[0], w);
  }
  return m;
}
const SW = loadMatrix();
const STATES = [...SW.keys()];

function matrixRowErrors(state, w) {
  const errs = [];
  const tot = ORDER.concat(["cash"]).reduce((a, s) => a + w[s], 0);
  if (Math.abs(tot - 100) > TOL) errs.push(`sum:${state}=${tot}`);
  if (tot > 100 + TOL) errs.push(`gross>100:${state}=${tot}`);
  for (const s of ORDER.concat(["cash"])) {
    if (w[s] < -TOL) errs.push(`negative:${state}:${s}`);
    if (SCAP[s] !== undefined && w[s] > SCAP[s] + TOL) errs.push(`sleeve-cap:${state}:${s}`);
  }
  for (const [dh, s] of ZEROS) if (state === dh && Math.abs(w[s]) > TOL) errs.push(`zero-cell:${state}:${s}`);
  for (const fam of Object.keys(FCAP)) {
    const f = ORDER.filter((s) => FAM[s] === fam).reduce((a, s) => a + w[s], 0);
    if (f > FCAP[fam] + TOL) errs.push(`family-cap:${state}:${fam}=${f}`);
  }
  if (w.cash < CASH_MIN - TOL) errs.push(`cash-min:${state}`);
  if (w.cash > CASH_MAX + TOL) errs.push(`cash-max:${state}`);
  return errs;
}
{
  const errs = STATES.flatMap((st) => matrixRowErrors(st, SW.get(st)));
  console.log("matrix integrity errors:", errs.length, errs.slice(0, 5));
  if (errs.length) { console.error("FAIL-STOP: frozen #178 matrix integrity"); process.exit(1); }
}

// ------------------------------------------------- frozen policy components
const TIERS = {};
for (const l of readLF(`${G177}/policy-matrix.csv`).trim().split("\n").slice(1)) {
  const c = l.split(",");
  if (c[1] === "cash") continue;
  TIERS[c[0] + "|" + c[1]] = c[2];
}
const CBIAS_BUGGY = {}; // column 1: opportunity_score  (the #178 defect)
const CBIAS_FIXED = {}; // column 2: cash_bias          (the repair)
for (const l of readLF(`${G177}/cash-bias.csv`).trim().split("\n").slice(1)) {
  const c = l.split(",");
  CBIAS_BUGGY[c[0]] = c[1];
  CBIAS_FIXED[c[0]] = c[2];
}

// Verbatim #178 normalization, parameterised by which Cash-bias map is consulted.
// `avail === null` means "every sleeve available" (the frozen matrix reference case).
function weightsFromPolicy(state, avail, base, mult, cbias) {
  const raw = {};
  for (const s of ORDER) {
    const m = mult[TIERS[state + "|" + s]];
    if (m === undefined || m === 0) continue;      // 0x tier / structurally-zero cell
    if (avail !== null && !avail.has(s)) continue; // missing history
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
  if (100 - S < minC) {                       // Cash-bias minimum scaling
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
const buggyWeights = (state, avail = null) => weightsFromPolicy(state, avail, BASE, MULT, CBIAS_BUGGY);
const fixedWeights = (state, avail = null) => weightsFromPolicy(state, avail, BASE, MULT, CBIAS_FIXED);
function fixedWeightsAvail(state, avail, base, mult) { return weightsFromPolicy(state, avail, base, mult, CBIAS_FIXED); }

// 2dp largest-remainder serialization, verbatim from issue_178_build.mjs (line 101).
// The frozen matrix is the largest-remainder rounding of the #178 engine output;
// "reproduce the frozen matrix exactly" therefore means: corrected component
// engine + frozen roundLR == frozen weight-matrix.csv, cell for cell.
function roundLR(w, zeros) {
  const fl = {};
  for (const s of Object.keys(w)) fl[s] = zeros.has(s) ? 0 : Math.floor(w[s] * 100 + 1e-9) / 100;
  const short = Math.round((100 - Object.values(fl).reduce((a, x) => a + x, 0)) * 100);
  if (short > 0) {
    const frac = Object.keys(w).filter((s) => !zeros.has(s)).map((s) => [w[s] * 100 - fl[s] * 100, s]).sort((a, b) => b[0] - a[0]);
    for (let i = 0; i < short; i++) fl[frac[i % frac.length][1]] += 0.01;
  }
  const r = {};
  for (const s of Object.keys(fl)) r[s] = Math.round(fl[s] * 100) / 100;
  return r;
}
const ZERO_SETS = Object.fromEntries(STATES.map((st) => [st, new Set(ORDER.filter((s) => TIERS[st + "|" + s] === "0"))]));
const MATRIX_REPRO = {};
{
  const check = (w) => {
    const rows = {};
    let n = 0;
    for (const st of STATES) {
      const r = roundLR(w(st, null), ZERO_SETS[st]);
      const m = SW.get(st);
      const mismatches = ORDER.concat(["cash"]).filter((s) => Math.abs(r[s] - m[s]) > 1e-12);
      rows[st] = { mismatches, n_mismatch: mismatches.length, max_abs_diff_pre_rounding: Math.max(...ORDER.concat(["cash"]).map((s) => Math.abs(w(st, null)[s] - m[s]))) };
      n += mismatches.length;
    }
    return { total_mismatches: n, rows };
  };
  MATRIX_REPRO.fixed_engine_reads_cash_bias = check(fixedWeights);
  MATRIX_REPRO.buggy_engine_reads_opportunity_score = check(buggyWeights);
  MATRIX_REPRO.conclusion = {
    fixed_reproduces_frozen_matrix_exactly: MATRIX_REPRO.fixed_engine_reads_cash_bias.total_mismatches === 0,
    buggy_reproduces_frozen_matrix_exactly: MATRIX_REPRO.buggy_engine_reads_opportunity_score.total_mismatches === 0,
  };
  console.log("matrix reproduction mismatches ??corrected engine:", MATRIX_REPRO.fixed_engine_reads_cash_bias.total_mismatches,
    "| buggy engine (#178 defect):", MATRIX_REPRO.buggy_engine_reads_opportunity_score.total_mismatches);
  if (!MATRIX_REPRO.conclusion.fixed_reproduces_frozen_matrix_exactly) { console.error("FAIL-STOP: corrected engine does not reproduce frozen matrix"); process.exit(1); }
}

// BUG PROOF: defective path fires bias-minimum scaling never; corrected path reproduces matrix.
const BUG_PROOF = {};
{
  for (const st of STATES) {
    const b = buggyWeights(st, null), c = fixedWeights(st, null), m = SW.get(st);
    const gross = (w) => ORDER.reduce((a, s) => a + w[s], 0) + w.cash;
    BUG_PROOF[st] = {
      buggy_noncash_sum: ORDER.reduce((a, s) => a + b[s], 0),
      buggy_cash: b.cash,
      buggy_gross_exposure: gross(b),
      corrected_gross_exposure: gross(c),
      matrix_gross_exposure: gross(m),
      margin_lookup_buggy: CMIN_BIAS[CBIAS_BUGGY[st]] ?? null,
      margin_lookup_corrected: CMIN_BIAS[CBIAS_FIXED[st]],
      matrix_max_abs_diff: Math.max(...ORDER.concat(["cash"]).map((s) => Math.abs(c[s] - m[s]))),
      leverage: gross(b) > 100 + TOL,
    };
  }
}
const LEVERAGED_STATES = STATES.filter((st) => BUG_PROOF[st].leverage);
console.log("states with accidental leverage:", JSON.stringify(LEVERAGED_STATES), LEVERAGED_STATES.map((s) => BUG_PROOF[s].buggy_gross_exposure));

// ---------------------------------------------------------------- macro states
function band(s) { return s < -10 ? "Low" : s > 10 ? "High" : "Neutral"; }
{
  const t = readLF("generated/issue-160/deep-history-v01-monthly.csv").trim().split("\n");
  const h = t[0].split(",");
  const gi = h.indexOf("growth_dh"), ii = h.indexOf("inflation_dh");
  var dhByDate = new Map();
  for (const l of t.slice(1)) {
    const c = l.split(",");
    const g = parseFloat(c[gi]), v = parseFloat(c[ii]);
    if (fin(g) && fin(v)) dhByDate.set(c[0], "G_" + band(g) + "/I_" + band(v));
  }
}
const ALLMOS = [...dhByDate.keys()].filter((d) => d >= "1966-03-01" && d <= "2026-08-01").sort();
// B-2 confirmation rule, byte-identical to #178 timeline()
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
    } else {
      st = dhByDate.get(ALLMOS[i - 1]);
      if (st === undefined) continue;
    }
    out.push({ date: m, dhState: st });
  }
  let last = null;
  for (const r of out) { if (r.dhState === null) r.dhState = last; else last = r.dhState; }
  return out.filter((r) => r.dhState !== null);
}
const tlB2 = timeline(true, "1966-05-01");
const tlImm = timeline(false, "1966-04-01");

// ---------------------------------------------------------------- returns
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
const oneqRet = new Map();
{
  const t = readLF(`${G180}/proxy-monthly-returns.csv`).trim().split("\n");
  const h = t[0].split(",");
  const k = h.indexOf("nasdaq_alt");
  for (const l of t.slice(1)) { const c = l.split(","); oneqRet.set(c[0].slice(0, 7), c[k] === "" ? NaN : parseFloat(c[k])); }
}
// #178 sleeveRet, verbatim (hardened S&P with flagged French fallback, investable oil, #174 others)
function researchRet(sl, ym) {
  if (sl === "sp500") { const h = r176.get(ym)?.sp500_tr_hardened; if (fin(h)) return h; const f = r174.get(ym)?.sp500; return fin(f) ? f : NaN; }
  if (sl === "oil") { const v = r176.get(ym)?.oil_investable_return; return fin(v) ? v : NaN; }
  const v = sl === "cash" ? r174.get(ym)?.cash : r174.get(ym)?.[sl];
  return fin(v) ? v : NaN;
}
// #180 proxy return (Cash identical by construction)
function implRet(sl, ym) {
  if (sl === "cash") return researchRet("cash", ym);
  const v = rPx.get(ym)?.[sl];
  return fin(v) ? v : NaN;
}
// Frozen #180 semantic mapping: each sleeve must have a declared proxy in
// generated/issue-180/proxy-map.csv AND its own return column in
// proxy-monthly-returns.csv. Issue #183 reuses that map unchanged, so #180's one
// open semantic question is resolved BY DATA rather than asserted by hand.
const PROXY_MAP = Object.fromEntries(readLF(`${G180}/proxy-map.csv`).trim().split("\n").slice(1).map((l) => { const c = l.split(","); return [c[0].replace(/"/g, ""), c[2].replace(/"/g, "")]; }));
const PX_COLUMNS = new Set(readLF(`${G180}/proxy-monthly-returns.csv`).split("\n")[0].split(","));
const semanticUnresolvedDerived = ORDER.some((s) => !PROXY_MAP[s] || !PX_COLUMNS.has(s));

// ---------------------------------------------------------------- metrics
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
const dOf = (x) => (fin(x) ? x : null);
function metricsJSON(m) { const o = {}; for (const k of Object.keys(m)) o[k] = fin(m[k]) || m[k] === null ? dOf(m[k]) : m[k]; if (!fin(m.sharpe_like)) o.sharpe_like = null; return o; }

// matrix weights with missing-history absorption (corrected structural engine)
function matrixW(state, avail) {
  const base = SW.get(state);
  // Issue #183 makes the frozen matrix the authoritative state allocation. When
  // every sleeve has history ??every #178 full-universe month and every #180 and
  // #182 month ??the frozen row is used VERBATIM.
  if (ORDER.every((s) => avail.has(s))) return { ...base };
  // Partial history (early max-history months only): #178's own documented
  // availability rule governs (issue_178_backtest.mjs computeWeights restricted
  // to available sleeves, with the correctly-read cash_bias). Absorbing the
  // missing-sleeve weight into Cash instead would breach the frozen CASH_MAX=60
  // and is NOT what the frozen parent does; spec section 2 asserts Cash in [2,60] in
  // every applied month, which this branch satisfies.
  return fixedWeights(state, avail);
}
// Frozen #180/#182 IMPLEMENTATION rule: the matrix row verbatim. The caller then
// applies #180's own documented treatment for sleeves whose tradable proxy has
// no history at that date ??`missing proxy weight -> Cash`
// (issue_180_backtest.mjs lines 97/111-120) ??with NO CASH_MAX re-derivation,
// because a proxy that does not exist yet cannot be bought. This is deliberately
// a DIFFERENT availability rule from #178's policy rule above; the two parents
// differ by design and Issue #183 must not silently unify them. Starting 2006-06
// (the #180 strict panel) every proxy has history, so this rule is inert there.
const frozenRow = (st) => ({ ...SW.get(st) });

// generic corrected structural runner (B-2 timeline; frozen #178 turnover semantics)
function runCorrected(wfn, months, retFn) {
  const rets = [], cashr = [], states = [], Ws = [];
  let prevW = null, switches = 0, stateChanges = 0, lastState = null, turnSum = 0, wchangeSum = 0;
  for (const m of months) {
    const ym = m.date.slice(0, 7);
    const avail = new Set(ORDER.filter((s) => fin(retFn(s, ym)) && fin(retFn("cash", ym))));
    const w = wfn(m.dhState, avail);
    Ws.push(w);
    if (lastState !== null && m.dhState !== lastState) stateChanges++;
    lastState = m.dhState;
    if (prevW !== null && JSON.stringify(w) !== JSON.stringify(prevW)) {
      switches++;
      const ch = ORDER.concat(["cash"]).reduce((a, s) => a + Math.abs(w[s] - prevW[s]), 0) / 2;
      turnSum += ch; wchangeSum += ch;
    }
    prevW = w;
    let pr = 0, ok = true;
    for (const s of ORDER.concat(["cash"])) {
      if (w[s] === 0) continue;
      const r = retFn(s, ym);
      if (!fin(r)) { ok = false; break; }
      pr += (w[s] / 100) * r;
    }
    if (!ok) { rets.push(NaN); cashr.push(NaN); states.push(m.dhState); continue; }
    rets.push(pr); cashr.push(retFn("cash", ym)); states.push(m.dhState);
  }
  return { rets, cashr, states, Ws, switches, stateChanges, turnSum, wchangeSum };
}
function rawChanges(months) {
  let n = 0;
  for (let i = 1; i < months.length; i++) {
    const a = dhByDate.get(months[i].date), b = dhByDate.get(months[i - 1].date);
    if (a !== undefined && b !== undefined && a !== b) n++;
  }
  return n;
}
function turnoverOf(R, months) {
  return {
    turnover_ann: R.turnSum / R.rets.length * 12,
    switches: R.switches,
    stateChanges: R.stateChanges,
    raw_state_changes: rawChanges(months),
    avg_months_between: R.rets.length / Math.max(1, R.switches),
    avg_wchange: R.switches ? R.wchangeSum / R.switches : 0,
  };
}
function avgFamily(R) {
  const acc = { equity: 0, rates: 0, real: 0, cash: 0 };
  const n = R.Ws.length;
  for (const w of R.Ws) {
    for (const s of ORDER) acc[FAM[s]] += w[s];
    acc.cash += w.cash;
  }
  for (const k of Object.keys(acc)) acc[k] /= n;
  return acc;
}

// =============================================================================
//  PHASE A ??corrected #178 structural replay
// =============================================================================
const FULL = { lo: "2000-09-01", hi: "2023-06-01" };
const inFull = (m) => m.date >= FULL.lo && m.date <= FULL.hi;
const ERAS = [["E1", "1966-03-01", "1979-12-01"], ["E2", "1980-01-01", "2007-12-01"], ["E3", "2008-01-01", "2019-12-01"], ["E4", "2020-01-01", "2026-08-01"]];

function benchNeutral(months) {
  const rets = [], cashr = [];
  for (const m of months) {
    const ym = m.date.slice(0, 7);
    const av = ORDER.filter((s) => fin(researchRet(s, ym)));
    const availTot = av.reduce((a, s) => a + BASE[s], 0) + 15;
    const w = {};
    for (const s of ORDER) w[s] = av.includes(s) ? (BASE[s] / availTot) * 100 : 0;
    w.cash = (15 / availTot) * 100;
    let pr = 0, ok = true;
    for (const s of ORDER.concat(["cash"])) {
      if (w[s] === 0) continue;
      const r = researchRet(s, ym);
      if (!fin(r)) { ok = false; break; }
      pr += (w[s] / 100) * r;
    }
    if (!ok) { rets.push(NaN); cashr.push(NaN); continue; }
    rets.push(pr); cashr.push(researchRet("cash", ym));
  }
  return { rets, cashr };
}
function runFrench(months, wEq) {
  const rets = [], cashr = [];
  for (const m of months) {
    const ym = m.date.slice(0, 7);
    const e = r174.get(ym)?.sp500, b = r174.get(ym)?.treasury10y, c = r174.get(ym)?.cash;
    if (!fin(e) || !fin(b) || !fin(c)) { rets.push(NaN); cashr.push(NaN); continue; }
    rets.push(wEq * e + (1 - wEq) * b); cashr.push(c);
  }
  return { rets, cashr };
}
function eraSplit(R, months) {
  const out = {};
  for (const [en, lo, hi] of ERAS) {
    const idx = months.map((m, i) => (m.date >= lo && m.date <= hi ? i : -1)).filter((i) => i >= 0);
    const RR = idx.map((i) => R.rets[i]), CC = idx.map((i) => R.cashr[i]);
    out[en] = { n: RR.filter(fin).length, ...metrics(RR, CC) };
  }
  return out;
}
function stateMeans(R, months) {
  const g = {};
  R.states.forEach((st, i) => { if (!fin(R.rets[i])) return; (g[st] = g[st] || []).push({ r: R.rets[i], c: R.cashr[i] }); });
  const out = {};
  for (const [st, rs] of Object.entries(g)) {
    const mean = rs.reduce((a, x) => a + x.r, 0) / rs.length;
    const sd = (a, f) => { const m = a.reduce((x, y) => x + f(y), 0) / a.length; return Math.sqrt(a.reduce((x, y) => x + (f(y) - m) ** 2, 0) / a.length) * Math.sqrt(12); };
    let peak = 1, dd = 0, cum = 1;
    for (const x of rs) { cum *= 1 + x.r; peak = Math.max(peak, cum); dd = Math.min(dd, cum / peak - 1); }
    out[st] = { n: rs.length, mean, cagr: rs.reduce((a, x) => a * (1 + x.r), 1) ** (12 / rs.length) - 1, vol: sd(rs, (x) => x.r), maxdd: dd };
  }
  return out;
}
function sensRun178(kind) {
  const wfn = kind === "S1"
    ? (st, av) => fixedWeightsAvail(st, av, BASE_S1, MULT)
    : kind === "S2"
      ? (st, av) => fixedWeightsAvail(st, av, BASE, MULT_S2)
      : null;
  const out = {};
  for (const [pn, months] of [["max_history", tlB2], ["full_universe", tlB2.filter(inFull)]]) {
    const t2 = kind === "S3" ? tlImm.filter((m) => (pn === "max_history" ? true : inFull(m))) : months;
    const r = runCorrected(wfn ?? matrixW, t2, researchRet);
    out[pn] = {
      met: metrics(r.rets, r.cashr), switches: r.switches,
      turnover_ann: r.turnSum / r.rets.length * 12, months: r.rets.length,
      avg_wchange: r.switches ? r.wchangeSum / r.switches : 0,
    };
  }
  return out;
}
// =============================================================================
//  PHASE B ??corrected #180 tradable implementation
// =============================================================================
function runImpl(retFn, months, costRate, lagMonths, wfn) {
  const A = [], B = [], C = [], turn = [], states = [], Ws = [];
  let prevW = null;
  const eff = months.map((m, i) => (i - lagMonths >= 0 ? months[i - lagMonths].dhState : null));
  for (let i = 0; i < months.length; i++) {
    const m = months[i], st = eff[i];
    if (st === null || st === undefined) { A.push(NaN); B.push(NaN); C.push(NaN); turn.push(0); states.push(null); Ws.push(null); continue; }
    const ym = m.date.slice(0, 7);
    const base = wfn(st, new Set(ORDER.filter((s) => fin(retFn(s, ym)))));
    const w = { ...base };
    let moved = 0;
    for (const s of ORDER) if (w[s] > 0 && !fin(retFn(s, ym))) { moved += w[s]; w[s] = 0; }
    w.cash += moved;
    let pb = 0, okb = true;
    for (const s of ORDER.concat(["cash"])) {
      if (w[s] === 0) continue;
      const r = retFn(s, ym);
      if (!fin(r)) { okb = false; break; }
      pb += (w[s] / 100) * r;
    }
    B.push(okb ? pb : NaN);
    const to = prevW ? ORDER.concat(["cash"]).reduce((a, s) => a + Math.abs(w[s] - prevW[s]), 0) / 2 / 100 : 0;
    turn.push(to);
    C.push(okb ? pb - to * costRate : NaN);
    // A leg: corrected structural research baseline on the same months
    const wb = matrixW(st, new Set(ORDER.filter((s) => fin(researchRet(s, ym)) && fin(researchRet("cash", ym)))));
    let pa = 0, oka = true;
    for (const s of ORDER.concat(["cash"])) {
      if (wb[s] === 0) continue;
      const ra = researchRet(s, ym);
      if (!fin(ra)) { oka = false; break; }
      pa += (wb[s] / 100) * ra;
    }
    A.push(oka ? pa : NaN);
    states.push(st);
    Ws.push({ ...w });
    prevW = { ...w };
  }
  return { A, B, C, turn, states, Ws };
}
const STRICT_LO = "2006-06-01";

// =============================================================================
//  PHASE C ??corrected #182 frozen V6.6 overlay
// =============================================================================
const V66 = new Map(), V66G = new Map();
{
  const t = readLF(`${G182}/tactical-timeline.csv`).trim().split("\n");
  const h = t[0].split(",");
  const si = h.indexOf("signal"), gidx = h.indexOf("v66_growth");
  for (const l of t.slice(1)) {
    const c = l.split(",");
    V66.set(c[0].slice(0, 7), c[si]);
    V66G.set(c[0].slice(0, 7), c[gidx]);
  }
}
function prevMonth(d) {
  let y = +d.slice(0, 4), m = +d.slice(5, 7) - 1;
  if (m < 1) { m = 12; y--; }
  return String(y).padStart(4, "0") + "-" + String(m).padStart(2, "0") + "-01";
}
// frozen #182 overlay mapping (verbatim)
function overlayW(base, signal, budget) {
  const w = { ...base };
  const eq = EQ.filter((s) => w[s] > 0);
  const E = eq.reduce((a, s) => a + w[s], 0);
  if (signal === "risk-on") {
    const head = eq.reduce((a, s) => a + (SCAP[s] - w[s]), 0);
    let add = Math.min(budget, Math.max(0, w.cash - CASH_MIN), CASH_MAX - E, head);
    add = Math.max(0, add);
    if (E > 0 && add > 0) {
      for (const s of eq) { const take = Math.min((add * w[s]) / E, SCAP[s] - w[s]); w[s] += take; w.cash -= take; }
    }
  } else if (signal === "risk-off") {
    const cut = Math.min(budget, E);
    if (E > 0 && cut > 0) { for (const s of eq) w[s] -= (cut * w[s]) / E; w.cash += cut; }
  }
  return w;
}
// Corrected A/B/C on one panel. A is the corrected structural baseline computed by
// the SAME code path as B/C (identical month set, identical 100%-gross base).
function runPanelC(retFn, budget, lagV66, costRate) {
  const rows = [];
  let prevWB = null;
  for (const m of tlB2) {
    if (m.date < "2007-02-01") continue;
    const ym = m.date.slice(0, 7);
    let sm = m.date;
    for (let k = 0; k < lagV66 + 1; k++) sm = prevMonth(sm);
    const sig = V66.get(sm.slice(0, 7));
    if (sig === undefined) continue;
    const base = SW.get(m.dhState);
    let pa = 0, oka = true;
    for (const s of ORDER.concat(["cash"])) {
      if (base[s] === 0) continue;
      const r = retFn(s, ym);
      if (!fin(r)) { oka = false; break; }
      pa += (base[s] / 100) * r;
    }
    const w = overlayW(base, sig, budget);
    let pb = 0, okb = true;
    for (const s of ORDER.concat(["cash"])) {
      if (w[s] === 0) continue;
      const r = retFn(s, ym);
      if (!fin(r)) { okb = false; break; }
      pb += (w[s] / 100) * r;
    }
    const toB = prevWB ? ORDER.concat(["cash"]).reduce((a, s) => a + Math.abs(w[s] - prevWB[s]), 0) / 2 / 100 : 0;
    const grossA = ORDER.reduce((a, s) => a + base[s], 0) + base.cash;
    const grossB = ORDER.reduce((a, s) => a + w[s], 0) + w.cash;
    rows.push({
      date: m.date, ym, dh: m.dhState, sig, vg: V66G.get(sm.slice(0, 7)) ?? null,
      A: oka ? pa : NaN, B: okb ? pb : NaN, C: okb ? pb - toB * costRate : NaN,
      turnB: toB, grossA, grossB, wA: base, wB: { ...w },
    });
    prevWB = { ...w };
  }
  return rows;
}
function incremental(rows, cash) {
  const idx = rows.map((_, i) => i).filter((i) => fin(rows[i].A) && fin(rows[i].B) && fin(rows[i].C) && fin(cash[i]));
  const cagrOf = (arr) => arr.reduce((a, x) => a * (1 + x), 1) ** (12 / arr.length) - 1;
  const dBC = idx.map((i) => rows[i].C - rows[i].A);
  const RA = idx.map((i) => rows[i].A), RC = idx.map((i) => rows[i].C);
  const eps = [];
  let cur = null;
  for (const i of idx) {
    const s = rows[i].sig;
    if (!cur || cur.sig !== s) { if (cur) eps.push(cur); cur = { sig: s, sum: 0, n: 0 }; }
    cur.sum += rows[i].C - rows[i].A; cur.n++;
  }
  if (cur) eps.push(cur);
  const pos = eps.filter((e) => e.sum > 0).sort((a, b) => b.sum - a.sum);
  const totPos = pos.reduce((a, e) => a + e.sum, 0);
  const ma = RA.reduce((a, x) => a + x, 0) / RA.length, mc = RC.reduce((a, x) => a + x, 0) / RC.length;
  let co = 0, va = 0, vc = 0;
  for (let k = 0; k < RA.length; k++) { co += (RA[k] - ma) * (RC[k] - mc); va += (RA[k] - ma) ** 2; vc += (RC[k] - mc) ** 2; }
  return {
    n: idx.length,
    cagr_BmA: cagrOf(idx.map((i) => rows[i].B)) - cagrOf(RA),
    cagr_CmA: cagrOf(RC) - cagrOf(RA),
    frac_gt_50bp: dBC.filter((d) => Math.abs(d) > 0.005).length / dBC.length,
    corr_AC: va > 0 && vc > 0 ? co / Math.sqrt(va * vc) : NaN,
    top1_share: totPos > 0 ? pos[0].sum / totPos : null,
    top3_share: totPos > 0 ? pos.slice(0, 3).reduce((a, e) => a + e.sum, 0) / totPos : null,
    n_episodes: eps.length,
  };
}
function stateDiag(rows, cash) {
  const acc = {};
  rows.forEach((r, i) => {
    acc[r.dh] = acc[r.dh] || { n: 0, A: [], C: [] };
    if (fin(r.A) && fin(r.C) && fin(cash[i])) { acc[r.dh].n++; acc[r.dh].A.push(r.A); acc[r.dh].C.push(r.C); }
  });
  const out = {};
  for (const [k, v] of Object.entries(acc)) {
    const mean = (a) => (a.length ? a.reduce((x, y) => x + y, 0) / a.length : NaN);
    const sd = (a) => { const m = mean(a); return a.length ? Math.sqrt(a.reduce((x, y) => x + (y - m) ** 2, 0) / a.length) * Math.sqrt(12) : NaN; };
    out[k] = {
      n: v.n, A_mean: mean(v.A), C_mean: mean(v.C), contrib: v.n ? mean(v.C) - mean(v.A) : NaN,
      C_ann: v.n ? v.C.reduce((x, y) => x * (1 + y), 1) ** (12 / v.n) - 1 : NaN,
      vol_diff: v.n ? sd(v.C) - sd(v.A) : NaN,
    };
  }
  return out;
}
function v66Diag(rows, cash) {
  const cls = { "risk-on": { d: [], n: 0 }, "risk-off": { d: [], n: 0 }, neutral: { d: [], n: 0 } };
  const cells = {}, ali = { aligned: [], divergent: [] };
  for (let i = 0; i < rows.length; i++) {
    const r = rows[i];
    if (!fin(r.A) || !fin(r.C) || !fin(cash[i])) continue;
    const d = r.C - r.A;
    cls[r.sig].d.push(d); cls[r.sig].n++;
    const ck = r.dh + "|" + r.sig;
    cells[ck] = (cells[ck] || 0) + 1;
    const dhg = r.dh.split("/")[0].slice(2);
    (dhg === r.vg ? ali.aligned : ali.divergent).push(d);
  }
  const mean = (a) => (a.length ? a.reduce((x, y) => x + y, 0) / a.length : NaN);
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
  const inside = [], outside = [], fq = { "risk-on": 0, "risk-off": 0, neutral: 0 };
  rows.forEach((r, i) => {
    if (!fin(r.A) || !fin(r.C) || !fin(cash[i])) return;
    (inWin.has(i) ? inside : outside).push(r.C - r.A);
    if (inWin.has(i)) fq[r.sig]++;
  });
  const mean = (a) => (a.length ? a.reduce((x, y) => x + y, 0) / a.length : NaN);
  return { n_transitions: chg.size, n_inside: inside.length, n_outside: outside.length, mean_inside: mean(inside), mean_outside: mean(outside), freq_inside: fq };
}
function eraSeg(rows, cash) {
  const segs = { pre2020: [], y2022: [], post2023: [] };
  rows.forEach((r, i) => {
    if (!fin(r.A) || !fin(r.C) || !fin(cash[i])) return;
    const rec = { A: r.A, C: r.C, B: r.B, cash: cash[i] };
    if (r.date < "2020-01-01") segs.pre2020.push(rec);
    else if (r.date <= "2022-12-01") segs.y2022.push(rec);
    else segs.post2023.push(rec);
  });
  const cagrOf = (a) => (a.length ? a.reduce((x, y) => x * (1 + y), 1) ** (12 / a.length) - 1 : NaN);
  const ddOf = (a) => { let peak = 1, dd = 0, cum = 1; for (const r of a) { cum *= 1 + r; peak = Math.max(peak, cum); dd = Math.min(dd, cum / peak - 1); } return a.length ? dd : NaN; };
  const out = {};
  for (const [k, v] of Object.entries(segs)) {
    const A = v.map((x) => x.A), B = v.map((x) => x.B), C = v.map((x) => x.C);
    out[k] = { n: v.length, cagr_A: cagrOf(A), cagr_B: cagrOf(B), cagr_C: cagrOf(C), contrib_C: cagrOf(C) - cagrOf(A), contrib_B: cagrOf(B) - cagrOf(A), maxdd_A: ddOf(A), maxdd_C: ddOf(C) };
  }
  return out;
}
function annTurnC(rows) { return rows.map((r) => r.turnB).filter(fin).reduce((a, x) => a + x, 0) / rows.length * 12; }
function structTurnC(rows) {
  let prev = null, sum = 0;
  for (const r of rows) {
    if (prev) sum += ORDER.concat(["cash"]).reduce((a, s) => a + Math.abs(r.wA[s] - prev[s]), 0) / 2 / 100;
    prev = { ...r.wA };
  }
  return sum / rows.length * 12;
}
function sigFreq(rows) {
  const c = { "risk-on": 0, "risk-off": 0, neutral: 0 };
  for (const r of rows) c[r.sig]++;
  return { n: rows.length, ...Object.fromEntries(Object.entries(c).map(([k, v]) => [k, v / rows.length])) };
}
function avgW(rows) {
  let se = 0, sc = 0;
  for (const r of rows) { se += EQ.reduce((a, s) => a + r.wB[s], 0); sc += r.wB.cash; }
  return { equity: se / rows.length, cash: sc / rows.length };
}
function dragAnn(rows) {
  const d = rows.map((r) => (fin(r.B) && fin(r.C) ? r.B - r.C : NaN)).filter(fin);
  return d.reduce((a, x) => a + x, 0) / rows.length * 12;
}
// ORIGINAL #182 frozen seven gates (thresholds verbatim; unchanged)
function gates182(perf, incr, to, erSeg, stDiag) {
  const cagrGap = incr.cagr_CmA * 100;
  const sharpeGap = perf.C.sharpe_like - perf.A.sharpe_like;
  const maxddGap = (perf.C.maxdd - perf.A.maxdd) * 100;
  const incrTo = to.incr_ann * 100;
  const benefitPos = incr.cagr_CmA > 0;
  const conc = benefitPos ? (incr.top1_share ?? 1) : null;
  const segGaps = Object.values(erSeg).map((s) => s.contrib_C * 100).filter(fin);
  const worstSeg = segGaps.length ? Math.min(...segGaps) : NaN;
  const stGaps = Object.values(stDiag).filter((s) => s.n >= 12).map((s) => s.contrib * 12 * 100).filter(fin);
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
  return {
    values: {
      cagr_gap_pp: cagrGap, sharpe_gap: sharpeGap, maxdd_gap_pp: maxddGap, incr_turnover_pp: incrTo,
      top1_share: conc, benefit_positive: benefitPos, worst_seg_pp: worstSeg, worst_state_pp: worstState,
    }, gates: g, fails, verdict,
  };
}

// =============================================================================
//  COMPUTE EVERYTHING
// =============================================================================
function compute() {
  const out = {};      // machine-readable payload
  const files = {};    // filename -> content
  const num = (x) => (fin(x) ? x : "");

  // ---------------- Phase A ----------------
  const rAmax = runCorrected(matrixW, tlB2, researchRet);
  const rAfull = runCorrected(matrixW, tlB2.filter(inFull), researchRet);
  {
    const grossMax = Math.max(...rAmax.Ws.map((w) => ORDER.reduce((a, s) => a + w[s], 0) + w.cash));
    if (grossMax > 100 + TOL) { throw new Error("corrected #178 gross exposure >100: " + grossMax); }
  }
  const oldMax = new Map(), oldFull = new Map();
  for (const l of readLF(`${G178}/backtest-monthly.csv`).trim().split("\n").slice(1)) {
    const c = l.split(",");
    oldMax.set(c[0], c[2] === "" ? NaN : parseFloat(c[2]));
  }
  const oldPerf = JSON.parse(readLF(`${G178}/performance.json`));
  const oldBench = JSON.parse(readLF(`${G178}/benchmarks.json`));
  const oldTurn = JSON.parse(readLF(`${G178}/turnover.json`));
  const oldEra = JSON.parse(readLF(`${G178}/era-report.json`));
  const oldSens = JSON.parse(readLF(`${G178}/sensitivity.json`));
  const oldSummary = JSON.parse(readLF(`${G178}/summary.json`));

  const newPerfA = {
    max_history: { policy: metrics(rAmax.rets, rAmax.cashr), months: rAmax.rets.filter(fin).length },
    full_universe: { policy: metrics(rAfull.rets, rAfull.cashr), months: rAfull.rets.filter(fin).length },
  };
  const bMax = benchNeutral(tlB2), bFull = benchNeutral(tlB2.filter(inFull));
  const fEqMax = runFrench(tlB2, 1), fEqFull = runFrench(tlB2.filter(inFull), 1);
  const f6040Max = runFrench(tlB2, 0.6), f6040Full = runFrench(tlB2.filter(inFull), 0.6);
  const cashBench = (months) => { const R = months.map((m) => researchRet("cash", m.date.slice(0, 7))); const v = R.filter(fin); return metrics(v, v); };
  const newBenchA = {
    max_history: { neutral: metrics(bMax.rets, bMax.cashr), cash: cashBench(tlB2), equity100: metrics(fEqMax.rets, fEqMax.cashr), balanced6040: metrics(f6040Max.rets, f6040Max.cashr) },
    full_universe: { neutral: metrics(bFull.rets, bFull.cashr), cash: cashBench(tlB2.filter(inFull)), equity100: metrics(fEqFull.rets, fEqFull.cashr), balanced6040: metrics(f6040Full.rets, f6040Full.cashr) },
  };
  // benchmark identity proof: corrected engine must reproduce frozen #178 benchmarks exactly
  {
    const eq = (x, y) => ((!fin(x) && !fin(y)) || (fin(x) && fin(y) && Math.abs(x - y) < 1e-12));
    const errs = [];
    for (const pn of ["max_history", "full_universe"]) {
      for (const bn of ["neutral", "cash", "equity100", "balanced6040"]) {
        const o = oldBench[pn][bn].met ?? oldBench[pn][bn];
        for (const k of ["n", "cagr", "vol_ann", "cash_excess_ann", "sharpe_like", "maxdd", "worst_month", "pos_frac"]) {
          if (!eq(o[k], newBenchA[pn][bn][k])) errs.push(`${pn}.${bn}.${k}`);
        }
      }
    }
    out.benchmark_identity_178 = { errors: errs, pass: errs.length === 0 };
    console.log("Phase A benchmark identity errors:", errs.length, errs.slice(0, 4));
    if (errs.length) throw new Error("Phase A benchmark identity failed");
  }
  const newTurnA = {
    max_history: turnoverOf(rAmax, tlB2),
    full_universe: turnoverOf(rAfull, tlB2.filter(inFull)),
  };
  const newEraA = { max_history: eraSplit(rAmax, tlB2), full_universe: eraSplit(rAfull, tlB2.filter(inFull)) };
  const newSensA = { S1_alt_baseline: sensRun178("S1"), S2_alt_multipliers: sensRun178("S2"), S3_immediate: sensRun178("S3") };
  const newStateA = { max_history: stateMeans(rAmax, tlB2) };
  const avgFamA = avgFamily(rAmax);

  // old-vs-corrected series + leverage isolation
  // Full-precision corrected engine (reads cash_bias) ??separates the Cash-bias
  // repair effect from the frozen 2dp largest-remainder matrix serialization.
  const rAfixed = runCorrected((st, av) => fixedWeights(st, av), tlB2, researchRet);
  const perfFixed = metrics(rAfixed.rets, rAfixed.cashr);
  // Defective engine, recomputed over the same panel: must reproduce the frozen
  // #178 `backtest-monthly.csv` return series exactly, otherwise the old-vs-new
  // comparison is not a like-for-like counterfactual.
  const rAbuggy = runCorrected((st, av) => buggyWeights(st, av), tlB2, researchRet);
  const rowsA = tlB2.map((m, i) => {
    const st = m.dhState;
    const buggy = buggyWeights(st, new Set(ORDER.filter((s) => fin(researchRet(s, m.date.slice(0, 7))) && fin(researchRet("cash", m.date.slice(0, 7))))));
    const corr = rAmax.Ws[i];
    const gross = (w) => ORDER.reduce((a, s) => a + w[s], 0) + w.cash;
    return {
      i, date: m.date, state: st, buggy, corr,
      gross_buggy: gross(buggy), gross_corr: gross(corr),
      old_ret: oldMax.get(m.date) ?? NaN, new_ret: rAmax.rets[i], fixed_ret: rAfixed.rets[i],
    };
  });
  const N = rowsA.length;
  // fail-stop: the defective engine must reproduce the frozen #178 return series
  const oldBuggyIdentity = {
    source: "generated/issue-178/backtest-monthly.csv column port_ret",
    months: N,
    mismatch_months: rowsA.filter((r, i) => !fin(r.old_ret) || !fin(rAbuggy.rets[i]) || Math.abs(r.old_ret - rAbuggy.rets[i]) > 1e-12).length,
  };
  oldBuggyIdentity.max_abs_diff = Math.max(...rowsA.map((r, i) => (fin(r.old_ret) && fin(rAbuggy.rets[i]) ? Math.abs(r.old_ret - rAbuggy.rets[i]) : 0)));
  oldBuggyIdentity.pass = oldBuggyIdentity.mismatch_months === 0;
  console.log("old-buggy engine identity vs frozen #178 stream:", JSON.stringify(oldBuggyIdentity));
  if (!oldBuggyIdentity.pass) { console.error("FAIL-STOP: defective engine does not reproduce frozen #178 returns"); process.exit(1); }
  const leverageIso = {};
  {
    const totalDiff = rowsA.reduce((a, r) => a + (fin(r.old_ret) && fin(r.new_ret) ? r.old_ret - r.new_ret : 0), 0);
    const fixedDiff = rowsA.reduce((a, r, i) => a + (fin(r.old_ret) && fin(rAfixed.rets[i]) ? r.old_ret - rAfixed.rets[i] : 0), 0);
    const roundDiff = rowsA.reduce((a, r, i) => a + (fin(rAfixed.rets[i]) && fin(r.new_ret) ? rAfixed.rets[i] - r.new_ret : 0), 0);
    // weights are byte-identical for all non-affected states -> decomposition is exact
    const weightIdentical = STATES.filter((st) => !LEVERAGED_STATES.includes(st)).every((st) =>
      JSON.stringify(buggyWeights(st, null)) === JSON.stringify(fixedWeights(st, null)));
    leverageIso.panel_wide = {
      n_months: N,
      cagr_old_buggy: oldPerf.max_history.policy.met.cagr,
      cagr_corrected_fixed_engine: perfFixed.cagr,
      cagr_corrected_frozen_matrix: newPerfA.max_history.policy.cagr,
      cagr_delta_pp: (oldPerf.max_history.policy.met.cagr - newPerfA.max_history.policy.cagr) * 100,
      arithmetic_mean_diff_ann_pp: (totalDiff / N) * 12 * 100,
      leverage_component_ann_pp: (fixedDiff / N) * 12 * 100,
      matrix_serialization_component_ann_pp: (roundDiff / N) * 12 * 100,
      leverage_share_of_old_cagr: (fixedDiff / N) * 12 / oldPerf.max_history.policy.met.cagr,
      leverage_share_of_total_repair: Math.abs(totalDiff) > 0 ? fixedDiff / totalDiff : null,
      non_affected_states_weights_identical: weightIdentical,
    };
    for (const st of LEVERAGED_STATES) {
      const sub = rowsA.filter((r) => r.state === st);
      const o = sub.map((r) => r.old_ret).filter(fin), c = sub.map((r) => r.new_ret).filter(fin);
      const mean = (a) => a.reduce((x, y) => x + y, 0) / a.length;
      const sd = (a) => { const m = mean(a); return Math.sqrt(a.reduce((x, y) => x + (y - m) ** 2, 0) / a.length) * Math.sqrt(12); };
      const dd = (a) => { let peak = 1, d = 0, cum = 1; for (const r of a) { cum *= 1 + r; peak = Math.max(peak, cum); d = Math.min(d, cum / peak - 1); } return d; };
      const d = sub.map((r) => r.old_ret - r.new_ret).filter(fin);
      const dfix = sub.map((r) => r.old_ret - r.fixed_ret).filter(fin);
      const cfix = sub.map((r) => r.fixed_ret).filter(fin);
      leverageIso[st] = {
        n_months: sub.length,
        buggy_gross_exposure: BUG_PROOF[st].buggy_gross_exposure,
        corrected_gross_exposure: BUG_PROOF[st].corrected_gross_exposure,
        buggy_cash: BUG_PROOF[st].buggy_cash,
        corrected_cash: SW.get(st).cash,
        buggy_mean_ret_ann_pp: mean(o) * 12 * 100,
        corrected_mean_ret_ann_pp: mean(c) * 12 * 100,
        corrected_fixed_engine_mean_ret_ann_pp: mean(cfix) * 12 * 100,
        return_diff_ann_pp: mean(d) * 12 * 100,
        leverage_only_return_diff_ann_pp: mean(dfix) * 12 * 100,
        buggy_vol_ann: sd(o), corrected_vol_ann: sd(c), vol_diff_pp: (sd(o) - sd(c)) * 100,
        buggy_maxdd: dd(o), corrected_maxdd: dd(c), maxdd_diff_pp: (dd(o) - dd(c)) * 100,
        contribution_to_overall_cagr_diff_pp: (mean(d) * sub.length / N) * 12 * 100,
        leverage_only_contribution_pp: (mean(dfix) * sub.length / N) * 12 * 100,
      };
    }
    leverageIso.leveraged_states_total = {
      contribution_pp: LEVERAGED_STATES.reduce((a, st) => a + leverageIso[st].contribution_to_overall_cagr_diff_pp, 0),
      leverage_only_contribution_pp: LEVERAGED_STATES.reduce((a, st) => a + leverageIso[st].leverage_only_contribution_pp, 0),
      share_of_total_diff: (() => {
        const tot = LEVERAGED_STATES.reduce((a, st) => a + leverageIso[st].contribution_to_overall_cagr_diff_pp, 0);
        return Math.abs(leverageIso.panel_wide.arithmetic_mean_diff_ann_pp) > 0 ? tot / leverageIso.panel_wide.arithmetic_mean_diff_ann_pp : null;
      })(),
    };
  }
  const cmpMetA = (o, n) => {
    const d = {};
    for (const k of ["n", "cagr", "vol_ann", "cash_excess_ann", "sharpe_like", "maxdd", "worst_month", "pos_frac"]) {
      d[k] = { old: dOf(o[k]), new: dOf(n[k]), delta: fin(o[k]) && fin(n[k]) ? n[k] - o[k] : null };
    }
    return d;
  };
  const cmpA = {
    policy: { max_history: cmpMetA(oldPerf.max_history.policy.met, newPerfA.max_history.policy), full_universe: cmpMetA(oldPerf.full_universe.policy.met, newPerfA.full_universe.policy) },
    benchmarks: {}, turnover: {}, eras: {}, sensitivity: {},
  };
  for (const pn of ["max_history", "full_universe"]) {
    cmpA.benchmarks[pn] = {};
    for (const bn of ["neutral", "cash", "equity100", "balanced6040"]) cmpA.benchmarks[pn][bn] = cmpMetA(oldBench[pn][bn].met ?? oldBench[pn][bn], newBenchA[pn][bn]);
  }
  for (const k of ["turnover_ann", "switches", "stateChanges", "raw_state_changes", "avg_months_between", "avg_wchange"]) {
    cmpA.turnover[k] = { old_max: oldTurn.max_history[k], new_max: newTurnA.max_history[k], old_full: oldTurn.full_universe[k] ?? null, new_full: newTurnA.full_universe[k] ?? null };
  }
  for (const en of ["E1", "E2", "E3", "E4"]) cmpA.eras[en] = { old_cagr: oldEra.max_history[en].policy.cagr, new_cagr: newEraA.max_history[en].cagr, old_maxdd: oldEra.max_history[en].policy.maxdd, new_maxdd: newEraA.max_history[en].maxdd, old_vol: oldEra.max_history[en].policy.vol_ann, new_vol: newEraA.max_history[en].vol_ann };
  for (const sk of ["S1_alt_baseline", "S2_alt_multipliers", "S3_immediate"]) {
    cmpA.sensitivity[sk] = {};
    for (const pn of ["max_history", "full_universe"]) cmpA.sensitivity[sk][pn] = cmpMetA(oldSens[sk][pn].met, newSensA[sk][pn].met);
  }

  // corrected #178 verdict (spec section 4 comparative-revalidation framing)
  const oldGap178 = oldPerf.max_history.policy.met.cagr - oldBench.max_history.neutral.met.cagr;
  const newGap178 = newPerfA.max_history.policy.cagr - newBenchA.max_history.neutral.cagr;
  const relCagrGap = newGap178 - oldGap178;
  const sameSign178 = Math.sign(newGap178) === Math.sign(oldGap178);
  const maxddGap178 = newPerfA.max_history.policy.maxdd - oldPerf.max_history.policy.met.maxdd;
  const turnGap178 = newTurnA.max_history.turnover_ann - oldTurn.max_history.turnover_ann;
  const appliedCashA = rowsA.map((r) => r.corr.cash);
  const appliedGrossA = rowsA.map((r) => r.gross_corr);
  const outOfBand = (rt, w) => rt.cash < CASH_MIN - 1e-9 || rt.cash > CASH_MAX + 1e-9 || w > 100 + 1e-9;
  const capsOk178 = rowsA.every((r) => !outOfBand(r.corr, r.gross_corr));
  const newViolations178 = rowsA.filter((r) => outOfBand(r.corr, r.gross_corr) && !outOfBand(r.buggy, r.gross_buggy)).map((r) => r.date);
  const noNewViolation178 = newViolations178.length === 0;
  const sensitivitiesStable178 = Object.values(cmpA.sensitivity).every((s) => Math.abs(s.max_history.cagr.delta) <= 0.01);
  // spec section 4 basis, implemented literally and in the frozen order.
  let verdict178;
  if (maxddGap178 < -0.10) verdict178 = "state_weight_policy_candidate_invalidated_by_repair";
  else if (Math.abs(relCagrGap) <= 0.01 && sameSign178 && maxddGap178 >= -0.03 && Math.abs(turnGap178) <= 5 && noNewViolation178 && sensitivitiesStable178) verdict178 = "state_weight_policy_candidate_revalidated";
  else verdict178 = "state_weight_policy_candidate_revalidated_with_limitations";
  const verdictBasis178 = {
    basis: "spec section 4 comparative revalidation",
    old_policy_minus_neutral_gap_pp: oldGap178 * 100,
    new_policy_minus_neutral_gap_pp: newGap178 * 100,
    rel_cagr_gap_pp: relCagrGap * 100,
    same_sign_as_buggy_run: sameSign178,
    maxdd_gap_pp: maxddGap178 * 100,
    turnover_gap_pp: turnGap178,
    applied_cash_range: [Math.min(...appliedCashA), Math.max(...appliedCashA)],
    applied_gross_max_pct: Math.max(...appliedGrossA),
    buggy_applied_cash_range: [Math.min(...rowsA.map((r) => r.buggy.cash)), Math.max(...rowsA.map((r) => r.buggy.cash))],
    buggy_applied_gross_max_pct: Math.max(...rowsA.map((r) => r.gross_buggy)),
    no_cap_or_cash_violation: capsOk178,
    new_cap_or_cash_violations_vs_buggy_run: newViolations178.length,
    no_new_cap_or_cash_violation: noNewViolation178,
    availability_rule: "frozen matrix row when all sleeves have history; otherwise #178 computeWeights(state, available) with cash_bias read correctly (never missing-weight-to-Cash)",
    sensitivities_stable_within_1pp: sensitivitiesStable178,
    verdict: verdict178,
  };

  // Panel provenance: the frozen parents SKIP months whose inputs are non-finite,
  // so the headline CAGR annualises on 12/applied_months rather than the calendar
  // span. Recorded here so the (inherited) inflation of absolute CAGR levels is
  // stated, and so the repair delta can be shown to survive re-annualisation.
  const appliedKeys = new Set(rowsA.map((r) => r.date.slice(0, 7)));
  const spanKeys = [];
  {
    let y = Number(rowsA[0].date.slice(0, 4)), mo = Number(rowsA[0].date.slice(5, 7));
    const ey = Number(rowsA[N - 1].date.slice(0, 4)), emo = Number(rowsA[N - 1].date.slice(5, 7));
    while (y < ey || (y === ey && mo <= emo)) { spanKeys.push(`${y}-${String(mo).padStart(2, "0")}`); mo++; if (mo === 13) { mo = 1; y++; } }
  }
  const calCagr = (c) => (1 + c) ** (N / spanKeys.length) - 1;
  const panelProvenance = {
    first_applied_month: rowsA[0].date,
    last_applied_month: rowsA[N - 1].date,
    applied_months: N,
    calendar_span_months: spanKeys.length,
    dropped_months: spanKeys.filter((k) => !appliedKeys.has(k)),
    dropped_reason: "inherited frozen-parent behaviour (issue_178_backtest.mjs skips months with non-finite macro/market inputs); not introduced by Issue #183",
    annualization: `CAGR uses 12/${N} applied months, not the ${spanKeys.length}-month calendar span`,
    cagr_old_calendar_time: calCagr(oldPerf.max_history.policy.met.cagr),
    cagr_corrected_calendar_time: calCagr(newPerfA.max_history.policy.cagr),
    cagr_delta_pp_applied_basis: (oldPerf.max_history.policy.met.cagr - newPerfA.max_history.policy.cagr) * 100,
    cagr_delta_pp_calendar_basis: (calCagr(oldPerf.max_history.policy.met.cagr) - calCagr(newPerfA.max_history.policy.cagr)) * 100,
    delta_robust_to_annualization: Math.abs((calCagr(oldPerf.max_history.policy.met.cagr) - calCagr(newPerfA.max_history.policy.cagr)) - (oldPerf.max_history.policy.met.cagr - newPerfA.max_history.policy.cagr)) * 100 < 0.01,
  };
  out.phase_a = {
    old_performance: { max_history: oldPerf.max_history.policy.met, full_universe: oldPerf.full_universe.policy.met },
    corrected_performance: newPerfA,
    turnover_old: oldTurn, turnover_corrected: newTurnA,
    eras_old: { max_history: oldEra.max_history, full_universe: oldEra.full_universe }, eras_corrected: newEraA,
    state_means_corrected: newStateA, avg_family_weights_corrected: avgFamA,
    leverage_isolation: leverageIso,
    matrix_reproduction: MATRIX_REPRO,
    panel_provenance: panelProvenance,
    old_buggy_identity: oldBuggyIdentity,
    corrected_full_precision_fixed_engine: { max_history: perfFixed },
    verdict_relative_gap: { rel_cagr_gap_vs_neutral: relCagrGap, maxdd_gap: maxddGap178, turnover_gap: turnGap178 },
    verdict_basis: verdictBasis178,
    verdict: verdict178,
    old_buggy_source: { file: "generated/issue-178/backtest-monthly.csv", sha256_worktree: shaWt(`${G178}/backtest-monthly.csv`), read_only: true, used_verbatim: true },
  };
  files["corrected-structural-monthly.csv"] =
    "date,alloc_state,cash_bias,gross_exposure,applied_cash,port_ret\n" +
    rowsA.map((r) => [r.date, r.state, CBIAS_FIXED[r.state], r.gross_corr.toFixed(6), r.corr.cash.toFixed(6), num(r.new_ret)].join(",")).join("\n") + "\n";
  files["old-vs-corrected-178.csv"] =
    "date,alloc_state,gross_exposure_buggy,gross_exposure_corrected,old_buggy_ret,corrected_ret,delta\n" +
    rowsA.map((r) => [r.date, r.state, r.gross_buggy.toFixed(6), r.gross_corr.toFixed(6), num(r.old_ret), num(r.new_ret), fin(r.old_ret) && fin(r.new_ret) ? (r.old_ret - r.new_ret) : ""].join(",")).join("\n") + "\n";
  files["performance-178.json"] = JSON.stringify({ issue: 183, phase: "A", old: { max_history: oldPerf.max_history, full_universe: oldPerf.full_universe }, corrected: newPerfA, benchmarks_old: oldBench, benchmarks_corrected: newBenchA, benchmark_identity_errors: out.benchmark_identity_178.errors, panel_provenance: panelProvenance }, null, 2);
  files["comparison-178.json"] = JSON.stringify({ issue: 183, phase: "A", comparison: cmpA }, null, 2);
  files["era-178.json"] = JSON.stringify({ issue: 183, phase: "A", old: { max_history: oldEra.max_history, full_universe: oldEra.full_universe }, corrected: newEraA, comparison: cmpA.eras }, null, 2);
  files["state-level-178.csv"] = "state,n_months,buggy_gross,corrected_gross,old_mean,corrected_mean,delta_mean,contrib_to_cagr_diff_pp_yr,avg_equity,avg_rates,avg_real,avg_cash,mean_equity_buggy,mean_cash_buggy\n" +
    STATES.map((st) => {
      const sub = rowsA.filter((r) => r.state === st);
      const of_ = sub.map((r) => r.old_ret).filter(fin), nf = sub.map((r) => r.new_ret).filter(fin);
      const mean = (a) => (a.length ? a.reduce((x, y) => x + y, 0) / a.length : NaN);
      const famOf = (Ws) => {
        const acc = { equity: 0, rates: 0, real: 0, cash: 0 };
        for (const w of Ws) { for (const s of ORDER) acc[FAM[s]] += w[s]; acc.cash += w.cash; }
        for (const k of Object.keys(acc)) acc[k] /= Ws.length;
        return acc;
      };
      const fc = sub.length ? famOf(sub.map((r) => r.corr)) : { equity: NaN, rates: NaN, real: NaN, cash: NaN };
      const fb = sub.length ? famOf(sub.map((r) => r.buggy)) : { equity: NaN, rates: NaN, real: NaN, cash: NaN };
      return [st, sub.length, BUG_PROOF[st].buggy_gross_exposure.toFixed(4), BUG_PROOF[st].corrected_gross_exposure.toFixed(4),
        num(mean(of_)), num(mean(nf)), num(mean(of_) - mean(nf)),
        num(sub.length ? (mean(of_) - mean(nf)) * sub.length / N * 12 * 100 : NaN),
        num(fc.equity), num(fc.rates), num(fc.real), num(fc.cash), num(fb.equity), num(fb.cash)].join(",");
    }).join("\n") + "\n";
  files["leverage-isolation-178.json"] = JSON.stringify({ issue: 183, phase: "A", bug_proof: BUG_PROOF, leveraged_states: LEVERAGED_STATES, matrix_reproduction: MATRIX_REPRO, isolation: leverageIso }, null, 2);
  files["turnover-178.json"] = JSON.stringify({ issue: 183, phase: "A", old: oldTurn, corrected: newTurnA, comparison: cmpA.turnover }, null, 2);
  files["sensitivity-178.json"] = JSON.stringify({ issue: 183, phase: "A", corrected: newSensA, old: oldSens, comparison: cmpA.sensitivity }, null, 2);

  // ---------------- Phase B ----------------
  const sIdx = tlB2.map((m, i) => (m.date >= STRICT_LO ? i : -1)).filter((i) => i >= 0);
  const RB = runImpl(implRet, tlB2, COST, 0, frozenRow);
  const cashB = tlB2.map((m) => researchRet("cash", m.date.slice(0, 7)));
  const sub = (arr) => sIdx.map((i) => arr[i]);
  const cIdx = sIdx.filter((i) => fin(RB.A[i]) && fin(RB.B[i]) && fin(RB.C[i]) && fin(cashB[i]));
  if (cIdx.length !== sIdx.length) throw new Error(`Phase B strict panel drops: ${sIdx.length - cIdx.length}`);
  const RA = cIdx.map((i) => RB.A[i]), RBv = cIdx.map((i) => RB.B[i]), RC = cIdx.map((i) => RB.C[i]), CC = cIdx.map((i) => cashB[i]);
  const mAB = metrics(RA, CC), mBB = metrics(RBv, CC), mCB = metrics(RC, CC);
  const diffsBA = RBv.map((r, k) => r - RA[k]);
  const mdBA = diffsBA.reduce((a, x) => a + x, 0) / diffsBA.length;
  const te = Math.sqrt(diffsBA.reduce((a, x) => a + (x - mdBA) ** 2, 0) / diffsBA.length) * Math.sqrt(12);
  const dragMonths = cIdx.map((i) => RB.turn[i] * COST);
  const dragAnnB = dragMonths.reduce((a, x) => a + x, 0) / cIdx.length * 12;
  function byStateImpl(Rs) {
    const g = {};
    cIdx.forEach((i, k) => { const st = RB.states[i]; (g[st] = g[st] || []).push(Rs[k]); });
    return Object.fromEntries(Object.entries(g).map(([st, rs]) => {
      const m = rs.reduce((a, x) => a + x, 0) / rs.length;
      return [st, { n: rs.length, mean: m, vol: Math.sqrt(rs.reduce((a, x) => a + (x - m) ** 2, 0) / rs.length) * Math.sqrt(12), worst: Math.min(...rs) }];
    }));
  }
  const sA = byStateImpl(RA), sB = byStateImpl(RBv), sC = byStateImpl(RC);
  const rank = (g) => Object.entries(g).sort((a, b) => b[1].mean - a[1].mean).map(([st]) => st);
  const rA180 = rank(sA), rB180 = rank(sB);
  const rankKept = rA180[0] === rB180[0] && rA180[rA180.length - 1] === rB180[rB180.length - 1];
  const DEF = ["G_Low/I_High", "G_Neutral/I_High"];
  let defWorse = 0;
  for (const st of DEF) if (sB[st] && sA[st]) defWorse = Math.max(defWorse, (sB[st].vol - sA[st].vol) * 100);
  const gauges180 = {
    g1_cagr_gap_pp: { value: (mCB.cagr - mAB.cagr) * 100, threshold: "abs<=1.0", pass: Math.abs((mCB.cagr - mAB.cagr) * 100) <= 1.0 },
    g2_te_pct: { value: te * 100, threshold: "<=2.5", pass: te * 100 <= 2.5 },
    g3_maxdd_gap_pp: { value: (mCB.maxdd - mAB.maxdd) * 100, threshold: ">=-5.0", pass: (mCB.maxdd - mAB.maxdd) * 100 >= -5.0 },
    g4_cost_drag_pct: { value: dragAnnB * 100, threshold: "<=0.4", pass: dragAnnB * 100 <= 0.4 },
    g5_state_rank_kept: { value: rankKept, threshold: "best+worst unchanged", pass: rankKept, rank_A: rA180, rank_B: rB180 },
    g6_defensive_vol_worse_pp: { value: defWorse, threshold: "<=2.0", pass: defWorse <= 2.0 },
  };
  const fails180 = Object.values(gauges180).filter((g) => !g.pass).length;
  const semanticUnresolved = semanticUnresolvedDerived; // derived from the frozen #180 proxy map + return columns
  let verdict180;
  if (fails180 === 0) verdict180 = "tradable_implementation_revalidated";
  else if (fails180 <= 2 && !semanticUnresolved && te * 100 <= 4) verdict180 = "tradable_implementation_revalidated_with_limitations";
  else verdict180 = "tradable_implementation_invalidated_by_repair";
  // Phase B benchmarks identity
  const bench180 = (weightsFn) => {
    const R = [], C = [];
    for (const m of tlB2) {
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
  };
  const NEU180 = { sp500: 25, nasdaq: 12, russell: 8, treasury2y: 8, treasury10y: 14, longtreasury: 8, gold: 6, oil: 4, cash: 15 };
  const zeroW = () => ({ ...Object.fromEntries(ORDER.map((s) => [s, 0])), cash: 100 });
  const benchNew180 = {
    neutral_etf: bench180(() => NEU180),
    cash: bench180(zeroW),
    equity_spy: bench180(() => ({ ...Object.fromEntries(ORDER.map((s) => [s, 0])), sp500: 100, cash: 0 })),
    balanced_6040: bench180(() => ({ ...Object.fromEntries(ORDER.map((s) => [s, 0])), sp500: 60, treasury10y: 40, cash: 0 })),
  };
  {
    const old180 = JSON.parse(readLF(`${G180}/benchmarks.json`));
    const errs = [];
    for (const k of ["neutral_etf", "cash", "equity_spy", "balanced_6040"]) {
      for (const m of ["n", "cagr", "vol_ann", "maxdd"]) if (Math.abs(old180[k][m] - benchNew180[k][m]) > 1e-12) errs.push(`${k}.${m}`);
    }
    out.benchmark_identity_180 = { errors: errs, pass: errs.length === 0 };
    console.log("Phase B benchmark identity errors:", errs.length, errs.slice(0, 4));
    if (errs.length) throw new Error("Phase B benchmark identity failed");
  }
  // Phase B sensitivities (original #180: ONEQ / 10bp / 1-mo lag)
  const sensB = {};
  {
    const R1 = [], C1 = [];
    for (const i of cIdx) {
      const m = tlB2[i], ym = m.date.slice(0, 7), st = RB.states[i];
      const px = (s) => (s === "nasdaq" ? oneqRet.get(ym) : implRet(s, ym));
      const base = frozenRow(st); // frozen #180 implementation rule (see frozenRow)
      const w = { ...base };
      let moved = 0;
      for (const s of ORDER) if (w[s] > 0 && !fin(px(s))) { moved += w[s]; w[s] = 0; }
      w.cash += moved;
      let pr = 0, ok = true;
      for (const s of ORDER.concat(["cash"])) { if (w[s] === 0) continue; const v = px(s); if (!fin(v)) { ok = false; break; } pr += (w[s] / 100) * v; }
      if (!ok) continue;
      R1.push(pr - RB.turn[i] * COST); C1.push(cashB[i]);
    }
    sensB.ONEQ_nasdaq = metrics(R1, C1);
    const r3 = runImpl(implRet, tlB2, COST_ALT, 0, frozenRow);
    const R3 = cIdx.map((i) => r3.C[i]), C3 = cIdx.map((i) => cashB[i]);
    sensB.cost_10bp = metrics(R3, C3);
    const r4 = runImpl(implRet, tlB2, COST, 1, frozenRow);
    const R4 = cIdx.map((i) => r4.C[i]), C4 = cIdx.map((i) => cashB[i]);
    sensB.lag_1mo = metrics(R4, C4);
  }
  out.phase_b = {
    strict_panel: [tlB2[sIdx[0]].date, tlB2[sIdx[sIdx.length - 1]].date],
    strict_months: sIdx.length, strict_common_months: cIdx.length, drops: 0,
    A: mAB, B: mBB, C: mCB,
    gauges: gauges180, fails: fails180, verdict: verdict180,
    state_table: { A: sA, B: sB, C: sC },
    drag_ann: dragAnnB, drag_cum: dragMonths.reduce((a, x) => a + x, 0),
    te_ann: te,
    benchmarks: benchNew180, benchmark_identity_errors: out.benchmark_identity_180.errors,
    sensitivities: sensB,
  };
  files["corrected-implementation-monthly.csv"] =
    "date,alloc_state,research_ret,impl_pre,impl_post,turnover\n" +
    tlB2.map((m, i) => [m.date, RB.states[i] ?? "", num(RB.A[i]), num(RB.B[i]), num(RB.C[i]), RB.turn[i]].join(",")).join("\n") + "\n";
  files["performance-180.json"] = JSON.stringify({ issue: 183, phase: "B", strict: { A: mAB, B: mBB, C: mCB }, benchmarks: benchNew180, benchmark_identity_errors: out.benchmark_identity_180.errors, sensitivities: sensB }, null, 2);
  files["state-implementation-183.csv"] = "state,n,research_mean,pre_mean,post_mean,drag,vol_pre,worst_pre\n" +
    Object.keys(sA).sort().map((st) => [st, sA[st].n, sA[st].mean, sB[st]?.mean ?? "", sC[st]?.mean ?? "", (sB[st]?.mean ?? NaN) - sA[st].mean, sB[st]?.vol ?? "", sB[st]?.worst ?? ""].join(",")).join("\n") + "\n";
  files["sensitivity-180.json"] = JSON.stringify({ issue: 183, phase: "B", describe: "original #180 sensitivities (descriptive only; primary never replaced)", sensitivities: sensB }, null, 2);

  // FAIL-STOP lineage identity: the corrected #180 implementation stream must be
  // byte-identical to the frozen #180 `implementation-monthly.csv` in every
  // column the frozen parent produced from the matrix + proxy availability
  // (alloc_state, impl_pre, impl_post, turnover) across all 721 max-history
  // months. Only the A/research leg may differ (that is the repaired quantity).
  {
    const par = readLF(`${G180}/implementation-monthly.csv`).trim().split("\n");
    const hdr = par[0].split(",");
    const ci = Object.fromEntries(hdr.map((k, j) => [k, j]));
    const rows180 = par.slice(1).map((l) => { const c = l.replace(/"/g, "").split(","); return c; });
    const eq = (a, b) => (a === "" || b === "" ? a === b : Math.abs(parseFloat(a) - parseFloat(b)) <= 1e-12);
    const diffs = { alloc_state: 0, impl_pre: 0, impl_post: 0, turnover: 0, rows: 0 };
    for (let i = 0; i < tlB2.length; i++) {
      const f = rows180[i];
      if (!f || f[ci.date] !== tlB2[i].date) { diffs.rows++; continue; }
      if ((RB.states[i] ?? "") !== f[ci.alloc_state]) diffs.alloc_state++;
      const mine = [num(RB.B[i]), num(RB.C[i]), String(RB.turn[i])];
      const theirs = [f[ci.impl_pre], f[ci.impl_post], f[ci.turnover]];
      ["impl_pre", "impl_post", "turnover"].forEach((k, j) => { if (!eq(mine[j], theirs[j])) diffs[k]++; });
    }
    diffs.rows += Math.max(0, rows180.length - tlB2.length) + Math.max(0, tlB2.length - rows180.length);
    const implIdOk = Object.values(diffs).every((v) => v === 0);
    const implCash = RB.Ws.filter(Boolean).map((w) => w.cash);
    const implCashStrict = sIdx.map((i) => RB.Ws[i]?.cash).filter((x) => x !== undefined);
    out.phase_b.implementation_identity_180 = { source: "generated/issue-180/implementation-monthly.csv", compared_months: rows180.length, diffs, pass: implIdOk, note: "frozen #180 length/cols, only research_ret differs (repaired)" };
    out.phase_b.implementation_cash = {
      all_months_range: [Math.min(...implCash), Math.max(...implCash)],
      strict_panel_range: [Math.min(...implCashStrict), Math.max(...implCashStrict)],
      gross_exposure: "exactly 100% in every row (missing-proxy weight is carried as Cash)",
      note: "Inherited frozen #180 behaviour: before a tradable proxy exists its weight is held in Cash with no CASH_MAX re-derivation (issue_180_backtest.mjs lines 97/111-120). The spec section 2 Cash-in-[2,60] assert therefore applies to the #178 POLICY stream (Phase A), whose applied cash is [5,60]; on the #180 strict panel (2006-06+) no proxy is missing, so the implementation cash band is inside [2,60] as well.",
    };
    console.log("Phase B frozen-#180 implementation identity:", JSON.stringify(diffs), implIdOk ? "PASS" : "FAIL");
    console.log("Phase B applied cash:", JSON.stringify(out.phase_b.implementation_cash.all_months_range), "strict", JSON.stringify(out.phase_b.implementation_cash.strict_panel_range));
    if (!implIdOk) { console.error("FAIL-STOP: corrected implementation stream does not reproduce frozen #180 (matrix+availability columns)"); process.exit(1); }
  }

  files["preservation-180.json"] = JSON.stringify({ issue: 183, phase: "B", gauges: gauges180, fails: fails180, semantic_unresolved: semanticUnresolved, verdict: verdict180, strict_panel: out.phase_b.strict_panel, strict_months: sIdx.length, te_ann: te, drag_ann: dragAnnB, rank_A: rA180, rank_B: rB180, defensive_vol_worse_pp: defWorse, implementation_identity_180: out.phase_b.implementation_identity_180, implementation_cash: out.phase_b.implementation_cash }, null, 2);

  // ---------------- Phase C ----------------
  const PR = runPanelC(researchRet, 5, 0, COST);
  const PT = runPanelC(implRet, 5, 0, COST);
  // A-leg consistency proof: Phase C A == corrected structural baseline from A/B
  {
    const idxByDate = new Map(tlB2.map((m, i) => [m.date, i]));
    let mismR = 0, mismT = 0, nR = 0, nT = 0;
    const grossErr = [];
    for (const r of PR) {
      const i = idxByDate.get(r.date);
      if (fin(r.A) && fin(rAmax.rets[i])) { nR++; if (Math.abs(r.A - rAmax.rets[i]) > 1e-12) mismR++; }
      if (Math.abs(r.grossA - 100) > TOL) grossErr.push(`A_R:${r.date}`);
      if (r.grossB > 100 + TOL) grossErr.push(`B_R:${r.date}`);
    }
    for (const r of PT) {
      const i = idxByDate.get(r.date);
      if (fin(r.A) && fin(RB.B[i])) { nT++; if (Math.abs(r.A - RB.B[i]) > 1e-12) mismT++; }
      if (Math.abs(r.grossA - 100) > TOL) grossErr.push(`A_T:${r.date}`);
      if (r.grossB > 100 + TOL) grossErr.push(`B_T:${r.date}`);
    }
    out.phase_c_baseline_proof = { research_matched: nR, research_mismatches: mismR, tradable_matched: nT, tradable_mismatches: mismT, gross_violations: grossErr, pass: mismR === 0 && mismT === 0 && grossErr.length === 0 };
    console.log("Phase C baseline proof:", JSON.stringify(out.phase_c_baseline_proof).slice(0, 300));
    if (!out.phase_c_baseline_proof.pass) throw new Error("Phase C baseline proof failed");
  }

  function packPanelC(rows, cash) {
    const perf = { A: metrics(rows.map((r) => r.A), cash), B: metrics(rows.map((r) => r.B), cash), C: metrics(rows.map((r) => r.C), cash) };
    const incr = incremental(rows, cash);
    const stD = stateDiag(rows, cash);
    const vD = v66Diag(rows, cash);
    const tD = transDiag(rows, cash);
    const eD = eraSeg(rows, cash);
    const to = {
      B_ann: annTurnC(rows), struct_ann: structTurnC(rows),
      tactical_active_months: rows.filter((r) => r.sig !== "neutral").length,
      tactical_switches: rows.slice(1).filter((r, i) => r.sig !== rows[i].sig).length,
      freq: sigFreq(rows), avgW: avgW(rows),
    };
    to.incr_ann = to.B_ann - to.struct_ann;
    return { perf, incr, state: stD, v66: vD, transition: tD, era: eD, turnover: to, drag_ann: dragAnn(rows), n: rows.length };
  }
  const cashCR = PR.map((r) => researchRet("cash", r.ym));
  const cashCT = PT.map((r) => implRet("cash", r.ym));
  const pcR = packPanelC(PR, cashCR);
  const pcT = packPanelC(PT, cashCT);
  const G = gates182(pcT.perf, pcT.incr, pcT.turnover, pcT.era, pcT.state);
  const GR = gates182(pcR.perf, pcR.incr, pcR.turnover, pcR.era, pcR.state);
  // sensitivities S1/S2/S3 on the PRIMARY tradable panel (original #182 set)
  const sensC = {};
  for (const [name, b, l, c] of [["S1_budget10", 10, 0, COST], ["S2_lag2", 5, 1, COST], ["S3_cost10bp", 5, 0, COST_ALT]]) {
    const rows = runPanelC(implRet, b, l, c);
    const cc = rows.map((r) => implRet("cash", r.ym));
    const m = metrics(rows.map((r) => r.C), cc);
    sensC[name] = { params: { budget_pp: b, lag_months: l + 1, cost_rate: c }, C: m, incr_vs_primary_C_cagr_pp: (m.cagr - pcT.perf.C.cagr) * 100 };
  }
  out.phase_c = {
    panels: { research: "2007-02+ B-2 backbone", tradable: "2007-02+ ETF proxies" },
    months_research: PR.length, months_tradable: PT.length,
    research: pcR, tradable: pcT,
    gates_primary_tradable: G, gates_research_reference: GR,
    sensitivities: sensC,
    true_pure_tactical_C_minus_A_tradable_pp: G.values.cagr_gap_pp,
    true_pure_tactical_C_minus_A_research_pp: GR.values.cagr_gap_pp,
    verdict: G.verdict,
    old_182_reference: (() => { const s = JSON.parse(readLF(`${G182}/summary.json`)); return { verdict: s.verdict, gates: s.gates, gate_values: s.gate_values, months_tradable: s.months_tradable }; })(),
  };
  files["corrected-overlay-monthly.csv"] = "panel,date,dh_state,v66_signal,A,B,C,turnover,gross_A,gross_B\n" +
    PR.map((r) => ["research", r.date, r.dh, r.sig, num(r.A), num(r.B), num(r.C), r.turnB, r.grossA, r.grossB].join(","))
      .concat(PT.map((r) => ["tradable", r.date, r.dh, r.sig, num(r.A), num(r.B), num(r.C), r.turnB, r.grossA, r.grossB].join(","))).join("\n") + "\n";
  files["performance-183-controlled-182.json"] = JSON.stringify({ issue: 183, phase: "C", research: { A: pcR.perf.A, B: pcR.perf.B, C: pcR.perf.C }, tradable: { A: pcT.perf.A, B: pcT.perf.B, C: pcT.perf.C }, incremental: { research: pcR.incr, tradable: pcT.incr }, turnover: { research: pcR.turnover, tradable: pcT.turnover } }, null, 2);
  files["gates-182.json"] = JSON.stringify({ issue: 183, phase: "C", framework: "ORIGINAL #182 seven gates, thresholds unchanged", primary_panel: "tradable", values: G.values, gates: G.gates, fails: G.fails, verdict: G.verdict, research_reference: { values: GR.values, gates: GR.gates, fails: GR.fails, verdict: GR.verdict } }, null, 2);
  files["v66-diagnostics-183.json"] = JSON.stringify({ issue: 183, phase: "C", research: pcR.v66, tradable: pcT.v66 }, null, 2);
  files["state-diagnostics-183.csv"] = "panel,state,n,A_mean,C_mean,contrib,C_ann,vol_diff,contrib_ann_pp\n" +
    Object.entries({ research: pcR.state, tradable: pcT.state }).flatMap(([p, t]) =>
      Object.entries(t).map(([st, v]) => [p, st, v.n, v.A_mean, v.C_mean, v.contrib, v.C_ann, v.vol_diff, v.contrib * 12 * 100].join(","))).join("\n") + "\n";
  files["transition-183.json"] = JSON.stringify({ issue: 183, phase: "C", research: pcR.transition, tradable: pcT.transition }, null, 2);
  files["alignment-183.json"] = JSON.stringify({ issue: 183, phase: "C", research: { aligned: pcR.v66.aligned, divergent: pcR.v66.divergent, cell_counts: pcR.v66.cell_counts }, tradable: { aligned: pcT.v66.aligned, divergent: pcT.v66.divergent, cell_counts: pcT.v66.cell_counts } }, null, 2);
  files["era-182-183.json"] = JSON.stringify({ issue: 183, phase: "C", research: pcR.era, tradable: pcT.era, old_182_reference: JSON.parse(readLF(`${G182}/era-stability.json`)) }, null, 2);
  files["sensitivity-183.json"] = JSON.stringify({ issue: 183, phase: "C", describe: "original #182 S1/S2/S3 exactly; descriptive, never promoted", sensitivities: sensC }, null, 2);
  // spec section 6 deliverable names (aliases of the split artifacts above; identical content)
  files["state-diagnostics.csv"] = files["state-diagnostics-183.csv"];
  files["era-report.json"] = JSON.stringify({ issue: 183, deliverable: "research/generated/issue-183/era-report.json", phase_a: JSON.parse(files["era-178.json"]), phase_c: JSON.parse(files["era-182-183.json"]) }, null, 2);
  files["transition-alignment.json"] = JSON.stringify({ issue: 183, deliverable: "research/generated/issue-183/transition-alignment.json", transition: JSON.parse(files["transition-183.json"]), alignment: JSON.parse(files["alignment-183.json"]) }, null, 2);

  // ---------------- manifest / lineage ----------------
  const PARENT_FILES = {
    "issue-177": [`${G177}/policy-matrix.csv`, `${G177}/cash-bias.csv`],
    "issue-178": [`${G178}/weight-matrix.csv`, `${G178}/policy.json`, `${G178}/backtest-monthly.csv`, `${G178}/benchmarks.json`, `${G178}/performance.json`, `${G178}/turnover.json`, `${G178}/era-report.json`, `${G178}/sensitivity.json`, `${G178}/summary.json`, `${G178}/state-cards.md`],
    "issue-180": [`${G180}/implementation-monthly.csv`, `${G180}/proxy-monthly-returns.csv`, `${G180}/proxy-map.csv`, `${G180}/benchmarks.json`, `${G180}/performance.json`, `${G180}/tracking.csv`, `${G180}/policy.json`, `${G180}/summary.json`, `${G180}/state-implementation.csv`, `${G180}/era-live.json`, `${G180}/sensitivity.json`],
    "issue-182": [`${G182}/tactical-timeline.csv`, `${G182}/overlay-weights.csv`, `${G182}/overlay-policy.json`, `${G182}/v66-input-manifest.json`, `${G182}/v66-exact-monthly.csv.gz.b64`, `${G182}/performance.json`, `${G182}/summary.json`, `${G182}/alignment.json`, `${G182}/transition.json`, `${G182}/era-stability.json`, `${G182}/state-diagnostics.csv`, `${G182}/sensitivity.json`, `${G182}/incremental.json`, `${G182}/benchmarks.json`],
  };
  const manifest = { issue: 183, branch: "research/issue-183-allocation-lineage-repair", required_start_head: REQUIRED_HEAD, parent_final_commits: PARENTS, sha_convention: "sha256 of the working-tree bytes as read by the engine (CRLF on Windows checkouts); git_blob_sha256 = sha256 of the committed LF blob; pinned historical parent SHAs in #178/#180/#182 were recorded from scan-time bytes and are compared against worktree_sha256", artifacts: {}, parents_unmodified: {}, v66_payload: {}, policy_constants: {} };
  for (const [issue, filesList] of Object.entries(PARENT_FILES)) {
    for (const rel of filesList) {
      let blobParent = null, blobHead = null;
      try { blobParent = shaBlob(PARENTS[issue], rel); } catch { blobParent = null; }
      try { blobHead = shaBlob("HEAD", rel); } catch { blobHead = null; }
      manifest.artifacts[rel] = { worktree_sha256: shaWt(rel), git_blob_sha256_parent_commit: blobParent, git_blob_sha256_head: blobHead, unmodified_since_parent: blobParent !== null && blobParent === blobHead };
    }
  }
  manifest.parents_unmodified.all = Object.values(manifest.artifacts).every((a) => a.unmodified_since_parent);
  manifest.matrix_reproduction = {
    method: "corrected component engine (reads cash-bias.csv column 2 `cash_bias`) + frozen issue_178_build.mjs roundLR 2dp largest-remainder == frozen weight-matrix.csv",
    corrected_engine_reproduces_frozen_matrix_exactly: MATRIX_REPRO.conclusion.fixed_reproduces_frozen_matrix_exactly,
    buggy_engine_reproduces_frozen_matrix_exactly: MATRIX_REPRO.conclusion.buggy_reproduces_frozen_matrix_exactly,
    corrected_mismatch_cells: MATRIX_REPRO.fixed_engine_reads_cash_bias.total_mismatches,
    buggy_mismatch_cells: MATRIX_REPRO.buggy_engine_reads_opportunity_score.total_mismatches,
    buggy_mismatch_detail: Object.entries(MATRIX_REPRO.buggy_engine_reads_opportunity_score.rows).filter(([, v]) => v.n_mismatch > 0).map(([k, v]) => [k, v.mismatches]),
  };
  {
    const b64 = fs.readFileSync(path.join(RES, `${G182}/v66-exact-monthly.csv.gz.b64`));
    const gz = Buffer.from(b64.toString("utf8").trim(), "base64");
    const csv = zlib.gunzipSync(gz);
    const frozen = JSON.parse(readLF(`${G182}/v66-input-manifest.json`));
    manifest.v66_payload = {
      source: "generated/issue-182/v66-exact-monthly.csv.gz.b64",
      gzip_sha256: sha256(gz), gzip_sha256_frozen: frozen.gzip_sha256,
      csv_sha256: sha256(csv), csv_sha256_frozen: frozen.csv_sha256,
      rows: csv.toString("utf8").trim().split("\n").length - 1, rows_frozen: frozen.rows,
      unchanged: sha256(gz) === frozen.gzip_sha256 && sha256(csv) === frozen.csv_sha256,
      classification_worktree_sha256: shaWt(`${G182}/tactical-timeline.csv`),
      classification_git_blob_sha256: shaBlob("HEAD", "generated/issue-182/tactical-timeline.csv"),
      classification_pinned_in_182_summary: JSON.parse(readLF(`${G182}/summary.json`)).inputs_sha256["issue-182/tactical-timeline.csv"],
      classification_matches_pin: shaBlob("HEAD", "generated/issue-182/tactical-timeline.csv") === JSON.parse(readLF(`${G182}/summary.json`)).inputs_sha256["issue-182/tactical-timeline.csv"],
    };
    if (!manifest.v66_payload.unchanged) throw new Error("V6.6 payload SHA mismatch");
  }
  manifest.policy_constants = {    issue_177_zero_cells: ZEROS, issue_178_baseline: BASE, issue_178_tier_multipliers: MULT,
    issue_178_sleeve_caps: SCAP, issue_178_family_caps: FCAP, issue_178_cash_min: CASH_MIN, issue_178_cash_max: CASH_MAX,
    issue_178_cash_bias_minimums: CMIN_BIAS, issue_178_rebalance: "B-2 confirmation",
    issue_180_proxy_map: PROXY_MAP,
    issue_180_cost_primary: COST, issue_180_cost_alt: COST_ALT,
    issue_182_v66_budget_pp: 5, issue_182_v66_bands: "+-10", issue_182_tactical_timing: "V6.6 state(m-1) -> month m",
    issue_182_gate_thresholds: { g1_cagr_pp: -0.50, g2_sharpe: -0.05, g3_maxdd_pp: -3.0, g4_incr_turnover_pp: 40.0, g5_top1_share: 0.60, g6_worst_seg_pp: -1.0, g7_worst_state_pp: -3.0 },
    issue_183_sensitivities: { S1: "budget 10pp", S2: "V6.6 state(m-2)", S3: "cost 10bp" },
  };
  files["manifest.json"] = JSON.stringify(manifest, null, 2);
  out.manifest = manifest;

  const lineage = {
    issue: 183,
    defect: {
      file: "indicators/macro-pressure-map/research/issue_178_backtest.mjs",
      function: "loadTiers()",
      line: 40,
      defective_read: "cb[c[0]] = c[1]   // column 1 = opportunity_score",
      correct_read: "cb[c[0]] = c[2]   // column 2 = cash_bias",
      effect: "CMIN_BIAS[cash-bias] lookup undefined -> bias-minimum scaling never fires",
      affected_states: LEVERAGED_STATES,
      buggy_gross_exposure: Object.fromEntries(LEVERAGED_STATES.map((st) => [st, BUG_PROOF[st].buggy_gross_exposure])),
      corrected_gross_exposure: Object.fromEntries(LEVERAGED_STATES.map((st) => [st, BUG_PROOF[st].corrected_gross_exposure])),
      other_states_identical: STATES.filter((st) => !LEVERAGED_STATES.includes(st)).every((st) => BUG_PROOF[st].buggy_gross_exposure === BUG_PROOF[st].corrected_gross_exposure),
      matrix_reproduction: {
        corrected_engine_reads_cash_bias_reproduces_frozen_matrix_exactly: MATRIX_REPRO.conclusion.fixed_reproduces_frozen_matrix_exactly,
        buggy_engine_reads_opportunity_score_reproduces_frozen_matrix_exactly: MATRIX_REPRO.conclusion.buggy_reproduces_frozen_matrix_exactly,
        corrected_mismatches: MATRIX_REPRO.fixed_engine_reads_cash_bias.total_mismatches,
        buggy_mismatches: MATRIX_REPRO.buggy_engine_reads_opportunity_score.total_mismatches,
        buggy_mismatch_cells: Object.entries(MATRIX_REPRO.buggy_engine_reads_opportunity_score.rows).filter(([, v]) => v.n_mismatch > 0).map(([k, v]) => [k, v.mismatches]),
      },
    },
    parent_artifacts_modified: false,
    parents_unmodified_all: manifest.parents_unmodified.all,
    issue_178: {
      old_cagr: oldPerf.max_history.policy.met.cagr, corrected_cagr: newPerfA.max_history.policy.cagr,
      delta_pp: (newPerfA.max_history.policy.cagr - oldPerf.max_history.policy.met.cagr) * 100,
      old_vol: oldPerf.max_history.policy.met.vol_ann, corrected_vol: newPerfA.max_history.policy.vol_ann,
      old_maxdd: oldPerf.max_history.policy.met.maxdd, corrected_maxdd: newPerfA.max_history.policy.maxdd,
      old_sharpe: oldPerf.max_history.policy.met.sharpe_like, corrected_sharpe: newPerfA.max_history.policy.sharpe_like,
      turnover_old_ann: oldTurn.max_history.turnover_ann, turnover_corrected_ann: newTurnA.max_history.turnover_ann,
      verdict: verdict178,
    },
    issue_180: { verdict: verdict180, fails: fails180, gauges: gauges180 },
    issue_182: {
      old_verdict: JSON.parse(readLF(`${G182}/summary.json`)).verdict,
      old_gate_values: JSON.parse(readLF(`${G182}/summary.json`)).gate_values,
      corrected_verdict: G.verdict, corrected_gate_values: G.values, corrected_gates: G.gates, fails: G.fails,
      true_pure_tactical_C_minus_A_pp: G.values.cagr_gap_pp,
      baseline_alignment_proof: out.phase_c_baseline_proof,
    },
    overall_verdict: null,
  };
  // overall verdict (spec section 4)
  const anyInvalid = [verdict178, verdict180, G.verdict].some((v) => /invalidated|not_supported/.test(v));
  const anyMaterial = !["state_weight_policy_candidate_revalidated", "tradable_implementation_revalidated", "v66_tactical_overlay_candidate_supported"].includes(verdict178) ||
    verdict180 !== "tradable_implementation_revalidated" || G.verdict !== "v66_tactical_overlay_candidate_supported" ||
    Math.abs((newPerfA.max_history.policy.cagr - oldPerf.max_history.policy.met.cagr) * 100) > 1.0;
  lineage.overall_verdict = anyInvalid ? "allocation_lineage_repair_failed" : anyMaterial ? "allocation_lineage_repair_complete_with_material_changes" : "allocation_lineage_repair_complete";
  out.overall_verdict = lineage.overall_verdict;
  files["lineage-diff.json"] = JSON.stringify(lineage, null, 2);

  files["summary.json"] = JSON.stringify({
    issue: 183,
    branch: "research/issue-183-allocation-lineage-repair",
    required_start_head: REQUIRED_HEAD,
    defect: "issue_178_backtest.mjs loadTiers() read cash-bias.csv column 1 (opportunity_score) instead of column 2 (cash_bias)",
    affected_states: LEVERAGED_STATES,
    buggy_gross_exposure: Object.fromEntries(LEVERAGED_STATES.map((st) => [st, BUG_PROOF[st].buggy_gross_exposure])),
    corrected_gross_exposure: Object.fromEntries(LEVERAGED_STATES.map((st) => [st, BUG_PROOF[st].corrected_gross_exposure])),
    verdict_178: verdict178,
    verdict_basis_178: verdictBasis178,
    verdict_180: verdict180,
    verdict_182: G.verdict,
    overall_verdict: lineage.overall_verdict,
    key_corrected_178: { cagr: newPerfA.max_history.policy.cagr, vol_ann: newPerfA.max_history.policy.vol_ann, sharpe_like: newPerfA.max_history.policy.sharpe_like, maxdd: newPerfA.max_history.policy.maxdd, worst_month: newPerfA.max_history.policy.worst_month, turnover_ann: newTurnA.max_history.turnover_ann, avg_family_weights: avgFamA },
    key_corrected_182: { cagr_gap_pp: G.values.cagr_gap_pp, sharpe_gap: G.values.sharpe_gap, maxdd_gap_pp: G.values.maxdd_gap_pp, incr_turnover_pp: G.values.incr_turnover_pp, worst_seg_pp: G.values.worst_seg_pp, worst_state_pp: G.values.worst_state_pp, benefit_positive: G.values.benefit_positive, top1_share: G.values.top1_share },
    gates_182: G.gates,
    gates_180: Object.fromEntries(Object.entries(gauges180).map(([k, v]) => [k, v.pass])),
    leverage_contribution_pp_per_yr: leverageIso.panel_wide.leverage_component_ann_pp,
    matrix_serialization_contribution_pp_per_yr: leverageIso.panel_wide.matrix_serialization_component_ann_pp,
    total_repair_effect_pp_per_yr: leverageIso.panel_wide.arithmetic_mean_diff_ann_pp,
    matrix_reproduction: {
      corrected_engine_reproduces_frozen_matrix_exactly: MATRIX_REPRO.conclusion.fixed_reproduces_frozen_matrix_exactly,
      buggy_engine_reproduces_frozen_matrix_exactly: MATRIX_REPRO.conclusion.buggy_reproduces_frozen_matrix_exactly,
      corrected_mismatches: MATRIX_REPRO.fixed_engine_reads_cash_bias.total_mismatches,
      buggy_mismatches: MATRIX_REPRO.buggy_engine_reads_opportunity_score.total_mismatches,
    },
    inputs_sha256: { "generated/issue-178/weight-matrix.csv": shaWt(`${G178}/weight-matrix.csv`), "generated/issue-178/backtest-monthly.csv": shaWt(`${G178}/backtest-monthly.csv`), "generated/issue-180/proxy-monthly-returns.csv": shaWt(`${G180}/proxy-monthly-returns.csv`), "generated/issue-180/proxy-map.csv": shaWt(`${G180}/proxy-map.csv`), "generated/issue-182/tactical-timeline.csv": shaWt(`${G182}/tactical-timeline.csv`), "generated/issue-182/overlay-weights.csv": shaWt(`${G182}/overlay-weights.csv`), "generated/issue-183/corrected-structural-monthly.csv": sha256(Buffer.from(files["corrected-structural-monthly.csv"])), "generated/issue-183/corrected-implementation-monthly.csv": sha256(Buffer.from(files["corrected-implementation-monthly.csv"])), "generated/issue-183/corrected-overlay-monthly.csv": sha256(Buffer.from(files["corrected-overlay-monthly.csv"])) },
    parents_unmodified: manifest.parents_unmodified.all,
    v66_payload_unchanged: manifest.v66_payload.unchanged,
    production_authorized: false,
  }, null, 2);
  return { files, out };
}

// =============================================================================
//  DETERMINISM + WRITE
// =============================================================================
const run1 = compute();
const run2 = compute();
const detErrs = [];
for (const k of Object.keys(run1.files)) {
  if (!(k in run2.files)) detErrs.push(`missing:${k}`);
  else if (run1.files[k] !== run2.files[k]) detErrs.push(`differs:${k}`);
}
const determinism = {
  issue: 183,
  runs: 2,
  artifacts_compared: Object.keys(run1.files).length,
  byte_identical: detErrs.length === 0,
  errors: detErrs,
  method: "in-process recompute of the full Phase A/B/C pipeline; every generated artifact compared byte-for-byte",
};
if (detErrs.length) { console.error("NONDETERMINISTIC:", detErrs); process.exit(1); }

fs.mkdirSync(GEN183, { recursive: true });
const written = [];
for (const [name, content] of Object.entries(run1.files)) {
  fs.writeFileSync(path.join(GEN183, name), content);
  written.push(name);
}
fs.writeFileSync(path.join(GEN183, "determinism.json"), JSON.stringify(determinism, null, 2));
written.push("determinism.json");

const o = run1.out;
console.log("\n=== ISSUE #183 CORRECTED REPLAY ===");
console.log("buggy gross:", JSON.stringify(Object.fromEntries(LEVERAGED_STATES.map((s) => [s, BUG_PROOF[s].buggy_gross_exposure]))));
console.log("corrected gross:", JSON.stringify(Object.fromEntries(LEVERAGED_STATES.map((s) => [s, BUG_PROOF[s].corrected_gross_exposure]))));
console.log("#178 old CAGR", o.phase_a.old_performance.max_history.cagr, "-> corrected", o.phase_a.corrected_performance.max_history.policy.cagr, "verdict", o.phase_a.verdict);
console.log("#178 old MaxDD", o.phase_a.old_performance.max_history.maxdd, "-> corrected", o.phase_a.corrected_performance.max_history.policy.maxdd);
console.log("total repair effect pp/yr:", o.phase_a.leverage_isolation.panel_wide.arithmetic_mean_diff_ann_pp,
  "| leverage component:", o.phase_a.leverage_isolation.panel_wide.leverage_component_ann_pp,
  "| 2dp-matrix serialization component:", o.phase_a.leverage_isolation.panel_wide.matrix_serialization_component_ann_pp);
console.log("#180 gauges:", JSON.stringify(Object.fromEntries(Object.entries(o.phase_b.gauges).map(([k, v]) => [k, [v.value, v.pass]]))));
console.log("#180 verdict:", o.phase_b.verdict, "fails", o.phase_b.fails);
console.log("#182 corrected gate values:", JSON.stringify(o.phase_c.gates_primary_tradable.values));
console.log("#182 corrected gates:", JSON.stringify(o.phase_c.gates_primary_tradable.gates), "verdict", o.phase_c.gates_primary_tradable.verdict);
console.log("#182 research gates:", JSON.stringify(o.phase_c.gates_research_reference.gates), o.phase_c.gates_research_reference.verdict);
console.log("true pure tactical C-A (tradable) pp:", o.phase_c.true_pure_tactical_C_minus_A_tradable_pp, "| research pp:", o.phase_c.true_pure_tactical_C_minus_A_research_pp);
console.log("overall verdict:", o.overall_verdict);
console.log("determinism:", determinism.byte_identical, "artifacts:", written.length);
console.log("DONE issue-183 replay");
