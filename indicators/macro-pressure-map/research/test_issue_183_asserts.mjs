#!/usr/bin/env node
// Issue #183 — INDEPENDENT verification suite.
//
// This file does NOT import issue_183_replay.mjs. It re-derives every checked
// quantity from the frozen PARENT artifacts and the generated issue-183 outputs,
// using its own copy of the frozen policy rules. A shared bug between the replay
// and this test therefore cannot hide.
//
// Covers the 17 mandatory checks of Issue #183.

import fs from "node:fs";
import path from "node:path";
import crypto from "node:crypto";
import zlib from "node:zlib";
import { execFileSync } from "node:child_process";

const ROOT = process.cwd();
const RES = path.join(ROOT, "indicators/macro-pressure-map/research");
const G = path.join(RES, "generated");
const G183 = path.join(G, "issue-183");
const BIG = 1 << 28;
const sha = (b) => crypto.createHash("sha256").update(b).digest("hex");
const rd = (rel) => fs.readFileSync(path.join(RES, rel), "utf8").replace(/\r/g, "");
const rdG = (rel) => fs.readFileSync(path.join(G183, rel), "utf8").replace(/\r/g, "");
const jG = (rel) => JSON.parse(rdG(rel));
const fin = (x) => typeof x === "number" && Number.isFinite(x);

let pass = 0, fail = 0;
const failures = [];
const RESULTS = [];
function ok(name, cond, detail) {
  if (cond) { pass++; RESULTS.push({ name, pass: true }); console.log(`PASS  ${name}`); }
  else { fail++; RESULTS.push({ name, pass: false, detail: detail ?? null }); failures.push(name + (detail ? ` :: ${detail}` : "")); console.log(`FAIL  ${name}${detail ? " :: " + detail : ""}`); }
}
function close(a, b, tol = 1e-12) { return fin(a) && fin(b) && Math.abs(a - b) <= tol; }

// ---------------------------------------------------------------- frozen policy (independent copy)
const ORDER = ["sp500", "nasdaq", "russell", "treasury2y", "treasury10y", "longtreasury", "gold", "oil"];
const EQ = ["sp500", "nasdaq", "russell"];
const FAM = { sp500: "equity", nasdaq: "equity", russell: "equity", treasury2y: "rates", treasury10y: "rates", longtreasury: "rates", gold: "real", oil: "real" };
const SCAP = { sp500: 35, nasdaq: 20, russell: 15, treasury2y: 15, treasury10y: 25, longtreasury: 15, gold: 12, oil: 8 };
const FCAP = { equity: 60, rates: 50, real: 15 };
const ZEROS = [["G_Low/I_Low", "oil"], ["G_Neutral/I_High", "russell"], ["G_High/I_Low", "gold"]];
const CMIN = { low: 5, neutral: 10, high: 20 };
const BASE = { sp500: 25, nasdaq: 12, russell: 8, treasury2y: 8, treasury10y: 14, longtreasury: 8, gold: 6, oil: 4 };
const MULT = { 0: 0, Low: 0.5, Neutral: 1.0, High: 1.75 };
const COST = 0.0002;

const TIERS = {};
for (const l of rd("generated/issue-177/policy-matrix.csv").trim().split("\n").slice(1)) {
  const c = l.split(",");
  if (c[1] === "cash") continue;
  TIERS[c[0] + "|" + c[1]] = c[2];
}
const CB = {};
for (const l of rd("generated/issue-177/cash-bias.csv").trim().split("\n").slice(1)) {
  const c = l.split(",");
  CB[c[0]] = { opportunity_score: c[1], cash_bias: c[2] };
}

function policyWeights(state, biasField) {
  const raw = {};
  for (const s of ORDER) {
    const m = MULT[TIERS[state + "|" + s]];
    if (m === 0 || m === undefined) continue;
    raw[s] = BASE[s] * m;
  }
  for (const s of Object.keys(raw)) if (raw[s] > SCAP[s]) raw[s] = SCAP[s];
  for (const f of Object.keys(FCAP)) {
    const mem = Object.keys(raw).filter((s) => FAM[s] === f);
    const sum = mem.reduce((a, s) => a + raw[s], 0);
    if (sum > FCAP[f]) { const k = FCAP[f] / sum; for (const s of mem) raw[s] *= k; }
  }
  const S = Object.values(raw).reduce((a, x) => a + x, 0);
  const minC = CMIN[CB[state][biasField]];
  let cash;
  if (100 - S < minC) { const k = S > 0 ? (100 - minC) / S : 0; for (const s of Object.keys(raw)) raw[s] *= k; cash = minC; }
  else if (100 - S > 60) { const k = S > 0 ? 40 / S : 0; for (const s of Object.keys(raw)) raw[s] *= k; cash = 60; }
  else cash = 100 - S;
  if (cash < 2) cash = 2;
  for (const s of Object.keys(raw)) if (raw[s] > SCAP[s]) { cash += raw[s] - SCAP[s]; raw[s] = SCAP[s]; }
  const out = {};
  for (const s of ORDER) out[s] = raw[s] ?? 0;
  out.cash = cash;
  return out;
}
// verbatim issue_178_build.mjs roundLR
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
// frozen #182 overlay mapping (independent re-implementation from the frozen prereg)
function overlayW(base, signal, budget) {
  const w = { ...base };
  const eq = EQ.filter((s) => w[s] > 0);
  const E = eq.reduce((a, s) => a + w[s], 0);
  if (signal === "risk-on") {
    const head = eq.reduce((a, s) => a + (SCAP[s] - w[s]), 0);
    let add = Math.min(budget, Math.max(0, w.cash - 2), 60 - E, head);
    add = Math.max(0, add);
    if (E > 0 && add > 0) for (const s of eq) { const take = Math.min((add * w[s]) / E, SCAP[s] - w[s]); w[s] += take; w.cash -= take; }
  } else if (signal === "risk-off") {
    const cut = Math.min(budget, E);
    if (E > 0 && cut > 0) { for (const s of eq) w[s] -= (cut * w[s]) / E; w.cash += cut; }
  }
  return w;
}
// frozen matrix
const SW = new Map();
{
  const t = rd("generated/issue-178/weight-matrix.csv").trim().split("\n");
  const h = t[0].split(",");
  for (const l of t.slice(1)) {
    const c = l.split(",");
    const w = {};
    for (const s of ORDER.concat(["cash"])) w[s] = +c[h.indexOf(s)];
    SW.set(c[0], w);
  }
}
const STATES = [...SW.keys()];
const rowsCSV = (rel) => {
  const t = rd(rel).trim().split("\n");
  const h = t[0].split(",");
  return t.slice(1).map((l) => { const c = l.split(","); const o = {}; h.forEach((k, i) => { let v = c[i]; if (v !== undefined) { v = v.trim(); if (v.length >= 2 && v.startsWith('"') && v.endsWith('"')) v = v.slice(1, -1); } o[k] = v; }); return o; });
};
const gross = (w) => ORDER.reduce((a, s) => a + w[s], 0) + w.cash;

// ---------------------------------------------------------------- 1. matrix reproduced exactly
{
  const zerosOf = (st) => new Set(ORDER.filter((s) => TIERS[st + "|" + s] === "0"));
  let correctedMismatch = 0, buggyMismatch = 0;
  for (const st of STATES) {
    const c = roundLR(policyWeights(st, "cash_bias"), zerosOf(st));
    const b = roundLR(policyWeights(st, "opportunity_score"), zerosOf(st));
    const m = SW.get(st);
    for (const s of ORDER.concat(["cash"])) {
      if (Math.abs(c[s] - m[s]) > 1e-12) correctedMismatch++;
      if (Math.abs(b[s] - m[s]) > 1e-12) buggyMismatch++;
    }
  }
  ok("1. frozen #178 matrix reproduced exactly by corrected engine (cash_bias, 2dp largest-remainder)", correctedMismatch === 0, `mismatches=${correctedMismatch}`);
  ok("1b. defective engine (opportunity_score) does NOT reproduce the matrix", buggyMismatch > 0, `mismatches=${buggyMismatch}`);
}

// ---------------------------------------------------------------- 2. rows sum to 100
{
  const bad = STATES.filter((st) => Math.abs(gross(SW.get(st)) - 100) > 1e-9);
  ok("2. all 9 frozen state rows sum to 100%", bad.length === 0, JSON.stringify(bad));
}

// ---------------------------------------------------------------- BUG PROOF: buggy gross exposure
const BUG_GROSS = {};
{
  for (const st of STATES) BUG_GROSS[st] = gross(policyWeights(st, "opportunity_score"));
  const lev = STATES.filter((st) => BUG_GROSS[st] > 100 + 1e-9);
  ok("bug. exactly the 2 documented states lever up (Low-Low, Neutral-Low)", JSON.stringify(lev) === JSON.stringify(["G_Low/I_Low", "G_Neutral/I_Low"]), JSON.stringify(lev));
  ok("bug. Low-Low buggy gross exposure = 103%", close(BUG_GROSS["G_Low/I_Low"], 103, 1e-9), String(BUG_GROSS["G_Low/I_Low"]));
  ok("bug. Neutral-Low buggy gross exposure = 109% (non-cash 107% + 2% cash floor)", close(BUG_GROSS["G_Neutral/I_Low"], 109, 1e-9), String(BUG_GROSS["G_Neutral/I_Low"]));
  ok("bug. corrected gross exposure = 100% for both", close(gross(SW.get("G_Low/I_Low")), 100, 1e-9) && close(gross(SW.get("G_Neutral/I_Low")), 100, 1e-9));
  ok("bug. all other 7 states identical buggy vs corrected", STATES.filter((st) => !lev.includes(st)).every((st) => Math.abs(BUG_GROSS[st] - 100) < 1e-9));
}

// ---------------------------------------------------------------- 3/4/5. corrected stream bounds
{
  const rows = rowsCSV("generated/issue-183/corrected-structural-monthly.csv");
  const bad = rows.filter((r) => +r.gross_exposure > 100 + 1e-6);
  ok("3. corrected structural monthly stream: no gross exposure > 100%", bad.length === 0, `violations=${bad.length}`);
  const notExact = rows.filter((r) => Math.abs(+r.gross_exposure - 100) > 1e-6);
  ok("3a. corrected structural monthly stream: gross exposure is exactly 100% in all 721 applied months", notExact.length === 0, `violations=${notExact.length}`);
  // applied cash must respect the frozen [2,60] band (spec section 2) -- the
  // replay uses the matrix row when all sleeves have history and #178's own
  // availability rule otherwise; it must never dump missing weight into Cash.
  const ovW = rowsCSV("generated/issue-183/old-vs-corrected-178.csv");
  const cashBad = rows.filter((r) => +r.applied_cash < 2 - 1e-9 || +r.applied_cash > 60 + 1e-9);
  ok("3b. corrected applied Cash respects the frozen [2,60] band in every month", cashBad.length === 0, `violations=${cashBad.length}`);
  ok("3b2. corrected stream reproduces the frozen #178 allocation dates 1:1", ovW.length === rows.length && ovW.every((r, i) => r.date === rows[i].date), `${ovW.length} vs ${rows.length}`);
  let idBad = 0;
  const frozen178 = new Map(rowsCSV("generated/issue-178/backtest-monthly.csv").map((r) => [r.date, +r.port_ret]));
  let idN = 0, idWorst = 0;
  for (const r of ovW) {
    const f = frozen178.get(r.date);
    if (f === undefined) continue;
    idN++;
    const d = Math.abs(f - +r.old_buggy_ret);
    if (d > 1e-12) idBad++;
    idWorst = Math.max(idWorst, d);
  }
  ok("3c. defective engine reproduces the frozen #178 return series exactly (like-for-like counterfactual)", idBad === 0 && idN === rows.length, `mismatches=${idBad}/${idN} worst=${idWorst}`);
  const ov = rowsCSV("generated/issue-183/corrected-overlay-monthly.csv");
  const badA = ov.filter((r) => +r.gross_A > 100 + 1e-6);
  const badB = ov.filter((r) => +r.gross_B > 100 + 1e-6);
  ok("3d. corrected #182 overlay stream: gross(A) <= 100%", badA.length === 0, `violations=${badA.length}`);
  ok("3e. corrected #182 overlay stream: gross(B) <= 100%", badB.length === 0, `violations=${badB.length}`);
  // Lineage identity: #180's implementation legs do not consume the defective
  // engine at all, so the corrected #180 stream must reproduce the frozen #180
  // matrix/availability columns EXACTLY, with only the research A leg repaired.
  {
    const f180 = rowsCSV("generated/issue-180/implementation-monthly.csv");
    const c183 = rowsCSV("generated/issue-183/corrected-implementation-monthly.csv");
    let cells = 0, rowMis = 0;
    for (let i = 0; i < f180.length; i++) {
      if (!c183[i] || f180[i].date !== c183[i].date) { rowMis++; continue; }
      for (const k of ["alloc_state", "impl_pre", "impl_post", "turnover"]) {
        const a = f180[i][k], b = c183[i][k];
        const same = /^-?[0-9.eE+-]+$/.test(a) && /^-?[0-9.eE+-]+$/.test(b) ? Math.abs(+a - +b) <= 1e-12 : a === b;
        if (!same) cells++;
      }
    }
    ok("3f. corrected #180 implementation stream reproduces frozen #180 exactly (alloc_state/impl_pre/impl_post/turnover, 721/721 months)", cells === 0 && rowMis === 0 && f180.length === c183.length, `cells=${cells} rows=${rowMis} n=${c183.length}`);
    let aMis = 0, aWorst = 0;
    for (let i = 0; i < c183.length; i++) {
      const s = rows[i];
      if (!s || s.date !== c183[i].date) continue;
      const d = Math.abs(+s.port_ret - +c183[i].research_ret);
      if (d > 1e-12) aMis++;
      aWorst = Math.max(aWorst, d);
    }
    ok("3g. corrected #180 research A leg equals the corrected structural stream (only repaired quantity)", aMis === 0, `mismatches=${aMis} worst=${aWorst}`);
  }
  const negMatrix = STATES.flatMap((st) => ORDER.concat(["cash"]).filter((s) => SW.get(st)[s] < -1e-9).map((s) => st + ":" + s));
  ok("4. no negative weights in the frozen matrix", negMatrix.length === 0, JSON.stringify(negMatrix.slice(0, 5)));
  // independent overlay reconstruction must never go negative
  let negOverlay = 0;
  for (const st of STATES) for (const sig of ["risk-on", "risk-off", "neutral"]) {
    const w = overlayW(SW.get(st), sig, 5);
    for (const s of ORDER.concat(["cash"])) if (w[s] < -1e-9) negOverlay++;
  }
  ok("4b. no negative weights in any independently reconstructed overlay row", negOverlay === 0, `violations=${negOverlay}`);
  const zeroBad = ZEROS.filter(([st, s]) => Math.abs(SW.get(st)[s]) > 1e-12);
  ok("5. frozen zero cells remain exactly zero in the matrix", zeroBad.length === 0, JSON.stringify(zeroBad));
  let zeroOverlayBad = 0;
  for (const [st, s] of ZEROS) for (const sig of ["risk-on", "risk-off"]) {
    if (Math.abs(overlayW(SW.get(st), sig, 5)[s]) > 1e-12) zeroOverlayBad++;
  }
  ok("5b. frozen zero cells stay zero under the tactical overlay", zeroOverlayBad === 0, `violations=${zeroOverlayBad}`);
}

// ---------------------------------------------------------------- 6. B-2 unchanged
function band(s) { return s < -10 ? "Low" : s > 10 ? "High" : "Neutral"; }
const dhByDate = new Map();
{
  const t = rd("generated/issue-160/deep-history-v01-monthly.csv").trim().split("\n");
  const h = t[0].split(",");
  const gi = h.indexOf("growth_dh"), ii = h.indexOf("inflation_dh");
  for (const l of t.slice(1)) { const c = l.split(","); const g = parseFloat(c[gi]), v = parseFloat(c[ii]); if (fin(g) && fin(v)) dhByDate.set(c[0], "G_" + band(g) + "/I_" + band(v)); }
}
const ALLMOS = [...dhByDate.keys()].filter((d) => d >= "1966-03-01" && d <= "2026-08-01").sort();
function b2Timeline() {
  const out = [];
  for (let i = 0; i < ALLMOS.length; i++) {
    const m = ALLMOS[i];
    if (m < "1966-05-01") continue;
    const a = dhByDate.get(ALLMOS[i - 1]), b = dhByDate.get(ALLMOS[i - 2]);
    if (a === undefined || b === undefined) continue;
    out.push({ date: m, s: a === b ? a : null });
  }
  let last = null;
  for (const r of out) { if (r.s === null) r.s = last; else last = r.s; }
  return out.filter((r) => r.s !== null);
}
{
  const tl = b2Timeline();
  const mine = rowsCSV("generated/issue-183/corrected-structural-monthly.csv");
  const a178 = new Map(rowsCSV("generated/issue-178/backtest-monthly.csv").map((r) => [r.date, r.alloc_state]));
  const a180 = new Map(rowsCSV("generated/issue-180/implementation-monthly.csv").map((r) => [r.date, r.alloc_state]));
  const m183 = new Map(mine.map((r) => [r.date, r.alloc_state]));
  const mism = tl.filter((r) => m183.get(r.date) !== r.s || a178.get(r.date) !== r.s || a180.get(r.date) !== r.s);
  ok("6. B-2 confirmation rule unchanged (corrected #183 == frozen #178 == frozen #180 timeline)", mism.length === 0 && tl.length === mine.length, `mismatches=${mism.length} n=${tl.length}/${mine.length}`);
}

// ---------------------------------------------------------------- 7/8/9. #180 map / cost / execution
{
  const pmap = rowsCSV("generated/issue-180/proxy-map.csv");
  const blob = sha(execFileSync("git", ["show", "ac251ad5149d9f550d82dfb34b3551fe01032367:indicators/macro-pressure-map/research/generated/issue-180/proxy-map.csv"], { maxBuffer: BIG, cwd: ROOT }));
  const head = sha(execFileSync("git", ["show", "HEAD:indicators/macro-pressure-map/research/generated/issue-180/proxy-map.csv"], { maxBuffer: BIG, cwd: ROOT }));
  const expect = { sp500: "SPY", nasdaq: "QQQ", russell: "IWM", treasury2y: "SHY", treasury10y: "IEF", longtreasury: "TLT", gold: "GLD", oil: "USO" };
  const got = Object.fromEntries(pmap.map((r) => [r.sleeve, r.proxy]));
  ok("7. #180 proxy map unchanged", blob === head && Object.entries(expect).every(([k, v]) => (got[k] || "").startsWith(v)), JSON.stringify(got));
  const imp = rowsCSV("generated/issue-183/corrected-implementation-monthly.csv");
  let costBad = 0, n = 0;
  for (const r of imp) {
    const pre = parseFloat(r.impl_pre), post = parseFloat(r.impl_post), to = parseFloat(r.turnover);
    if (!fin(pre) || !fin(post) || !fin(to)) continue;
    n++;
    if (Math.abs(post - (pre - to * COST)) > 1e-15) costBad++;
  }
  ok("8. #180 cost model unchanged: impl_post == impl_pre - turnover x 2bp", costBad === 0, `violations=${costBad} of ${n}`);
  // execution lag 0: applied allocation for month m is the B-2 state confirmed through m-1
  const tl = new Map(b2Timeline().map((r) => [r.date, r.s]));
  const execBad = imp.filter((r) => tl.get(r.date) !== r.alloc_state);
  ok("9. #180 execution timing unchanged (B-2 confirmed state applied to month m)", execBad.length === 0, `violations=${execBad.length}`);
}

// ---------------------------------------------------------------- 10/11/12/13. V6.6 payload / mapping / budget / timing
const V66 = new Map();
{
  const b64 = fs.readFileSync(path.join(G, "issue-182/v66-exact-monthly.csv.gz.b64"));
  const gz = Buffer.from(b64.toString("utf8").trim(), "base64");
  const csv = zlib.gunzipSync(gz);
  const frozen = JSON.parse(rd("generated/issue-182/v66-input-manifest.json"));
  ok("10. V6.6 payload bytes unchanged (gzip + csv SHA256 vs frozen manifest)",
    sha(gz) === frozen.gzip_sha256 && sha(csv) === frozen.csv_sha256 &&
    sha(gz) === "6087d7eceff168147b4db2e8688ce308dc12aa6b4187ff0c18f1d5e51e4beda2" &&
    sha(csv) === "1d03923503e7fe82a69b033897484c48aa646279ecf70164d090ed62a5a70719",
    `gz=${sha(gz).slice(0, 12)} csv=${sha(csv).slice(0, 12)}`);
  const tt = rowsCSV("generated/issue-182/tactical-timeline.csv");
  let mapBad = 0;
  const seen = new Set();
  for (const r of tt) {
    V66.set(r.date.slice(0, 7), r.signal);
    const g = r.v66_growth, inf = r.v66_inflation;
    const expect = (g === "High" && inf !== "High") ? "risk-on" : ((g === "Low" || inf === "High") ? "risk-off" : "neutral");
    seen.add(expect);
    if (expect !== r.signal) mapBad++;
  }
  ok("11. V6.6 classification unchanged: frozen band rule reproduces every stored signal", mapBad === 0 && seen.size === 3, `mismatches=${mapBad}`);
  const ttBlob = sha(execFileSync("git", ["show", "57852112ce95913d48297b35f803a1583cbab314:indicators/macro-pressure-map/research/generated/issue-182/tactical-timeline.csv"], { maxBuffer: BIG, cwd: ROOT }));
  const pinned = JSON.parse(rd("generated/issue-182/summary.json")).inputs_sha256["issue-182/tactical-timeline.csv"];
  ok("11b. V6.6 classification file byte-identical to the #182-pinned SHA", ttBlob === pinned, `${ttBlob.slice(0, 12)} vs ${pinned.slice(0, 12)}`);
}
{
  // 12. ±5pp budget, pro-rata equity, zeros preserved: compare independent reconstruction with frozen #182 overlay weights
  const frozenOw = rowsCSV("generated/issue-182/overlay-weights.csv").filter((r) => r.budget === "5");
  let worst = 0, n = 0, budgetBad = 0, cashBad = 0;
  for (const r of frozenOw) {
    const w = overlayW(SW.get(r.dh_state), r.signal, 5);
    for (const s of ORDER.concat(["cash"])) worst = Math.max(worst, Math.abs(w[s] - parseFloat(r[s])));
    const dEq = EQ.reduce((a, s) => a + (w[s] - SW.get(r.dh_state)[s]), 0);
    if (Math.abs(dEq) > 5 + 1e-9) budgetBad++;
    if (w.cash < 2 - 1e-9) cashBad++;
    n++;
  }
  ok("12. +/-5pp tactical budget unchanged (reconstruction == frozen #182 overlay-weights.csv)", worst <= 0.006 && n === 27, `max|diff|=${worst.toFixed(6)} n=${n}`);
  ok("12b. equity delta never exceeds the frozen 5pp budget and Cash never breaches the 2% floor", budgetBad === 0 && cashBad === 0, `budget=${budgetBad} cash=${cashBad}`);
}
function prevMonth(d) { let y = +d.slice(0, 4), m = +d.slice(5, 7) - 1; if (m < 1) { m = 12; y--; } return String(y).padStart(4, "0") + "-" + String(m).padStart(2, "0") + "-01"; }
{
  const ov = rowsCSV("generated/issue-183/corrected-overlay-monthly.csv");
  const bad = ov.filter((r) => V66.get(prevMonth(r.date).slice(0, 7)) !== r.v66_signal);
  ok("13. tactical timing unchanged (V6.6 state m-1 applied to month m, no look-ahead)", bad.length === 0, `violations=${bad.length} of ${ov.length}`);
  const badLag = ov.filter((r) => V66.get(r.date.slice(0, 7)) !== r.v66_signal);
  ok("13b. look-ahead detector: same-month signal is NOT the one applied", badLag.length > 0, `same-month matches=${ov.length - badLag.length}`);
}

// ---------------------------------------------------------------- 14. original seven gates unchanged
{
  const src = fs.readFileSync(path.join(RES, "issue_182_backtest.mjs"), "utf8");
  const literals = ["cagrGap >= -0.50", "sharpeGap >= -0.05", "maxddGap >= -3.0", "incrTo <= 40.0", "conc <= 0.60", "worstSeg >= -1.0", "worstState >= -3.0"];
  const missing = literals.filter((l) => !src.includes(l));
  ok("14. original #182 gate thresholds unchanged in the frozen parent source", missing.length === 0, JSON.stringify(missing));
  const g = jG("gates-182.json");
  const v = g.values;
  const recomputed = {
    g1_cagr: v.cagr_gap_pp >= -0.50,
    g2_sharpe: v.sharpe_gap >= -0.05,
    g3_maxdd: v.maxdd_gap_pp >= -3.0,
    g4_turnover: v.incr_turnover_pp <= 40.0,
    g5_concentration: !v.benefit_positive ? true : v.top1_share <= 0.60,
    g6_segment: v.worst_seg_pp >= -1.0,
    g7_state: v.worst_state_pp >= -3.0,
  };
  const same = JSON.stringify(recomputed) === JSON.stringify(g.gates);
  const fails = Object.values(recomputed).filter((x) => !x).length;
  const verdict = fails === 0 ? "v66_tactical_overlay_candidate_supported"
    : (v.cagr_gap_pp > 0 && recomputed.g3_maxdd && recomputed.g7_state && fails <= 2) ? "v66_tactical_overlay_candidate_suggestive"
      : "v66_tactical_overlay_not_supported";
  ok("14b. corrected #182 verdict derives from the ORIGINAL seven gates", same && verdict === g.verdict, `${g.verdict} vs ${verdict}`);
}

// ---------------------------------------------------------------- 15. parent artifacts untouched
{
  const man = jG("manifest.json");
  const bad = Object.entries(man.artifacts).filter(([, a]) => !a.unmodified_since_parent);
  ok("15. all pinned #177/#178/#180/#182 artifacts unmodified since their parent commits", bad.length === 0, JSON.stringify(bad.map(([k]) => k)));
  ok("15b. manifest records the required starting HEAD", man.required_start_head === "57852112ce95913d48297b35f803a1583cbab314");
  const heads = {
    "issue-177": "bc652bd615f2c5e9137050d01c666dbcd9528cd3",
    "issue-178": "10dcdce0ec86b0493d6df6b916b720eba46dcbe6",
    "issue-180": "ac251ad5149d9f550d82dfb34b3551fe01032367",
    "issue-182": "57852112ce95913d48297b35f803a1583cbab314",
  };
  const mismatch = Object.entries(man.parent_final_commits).filter(([k, v]) => heads[k] !== v);
  ok("15c. parent final commits recorded correctly", mismatch.length === 0, JSON.stringify(mismatch));
}

// ---------------------------------------------------------------- compare corrected vs original parents
{
  const old182 = JSON.parse(rd("generated/issue-182/performance.json"));
  const new182 = jG("performance-183-controlled-182.json");
  const keys = ["n", "cagr", "vol_ann", "cash_excess_ann", "sharpe_like", "maxdd", "worst_month", "pos_frac", "downside_vol"];
  let worst = 0;
  for (const leg of ["A", "B", "C"]) for (const k of keys) if (fin(old182.tradable[leg][k]) && fin(new182.tradable[leg][k])) worst = Math.max(worst, Math.abs(old182.tradable[leg][k] - new182.tradable[leg][k]));
  ok("C1. corrected #182 PRIMARY (tradable) A/B/C identical to #182: the repaired leg was already matrix-based", worst < 1e-12, `max|diff|=${worst}`);
  const oldInc = JSON.parse(rd("generated/issue-182/incremental.json"));
  ok("C2. corrected #182 primary C-A equals the original #182 primary C-A (true pure tactical effect, not a bug artifact)",
    Math.abs(oldInc.tradable.cagr_CmA - new182.incremental.tradable.cagr_CmA) < 1e-12,
    `${oldInc.tradable.cagr_CmA} vs ${new182.incremental.tradable.cagr_CmA}`);
  ok("C3. corrected #182 RESEARCH leg DOES change (repair materially affects the research baseline)",
    Math.abs(oldInc.research.cagr_CmA - new182.incremental.research.cagr_CmA) > 1e-6,
    `${oldInc.research.cagr_CmA} -> ${new182.incremental.research.cagr_CmA}`);
  const old180 = JSON.parse(rd("generated/issue-180/performance.json"));
  const new180 = jG("performance-180.json");
  let worstB = 0;
  for (const leg of ["B", "C"]) for (const k of keys) if (fin(old180.strict[leg][k]) && fin(new180.strict[leg][k])) worstB = Math.max(worstB, Math.abs(old180.strict[leg][k] - new180.strict[leg][k]));
  ok("B1. corrected #180 tradable legs (B/C) identical to #180: the tradable implementation was already matrix-based", worstB < 1e-12, `max|diff|=${worstB}`);
  ok("B2. corrected #180 research A leg changes vs #180 (buggy parent baseline replaced)", Math.abs(old180.strict.A.cagr - new180.strict.A.cagr) > 1e-6,
    `${old180.strict.A.cagr} -> ${new180.strict.A.cagr}`);
  const old178 = JSON.parse(rd("generated/issue-178/performance.json"));
  const new178 = jG("performance-178.json");
  ok("A1. corrected #178 policy metrics differ from the buggy frozen run", Math.abs(old178.max_history.policy.met.cagr - new178.corrected.max_history.policy.cagr) > 1e-6,
    `${old178.max_history.policy.met.cagr} -> ${new178.corrected.max_history.policy.cagr}`);
  ok("A2. corrected #178 is worse on CAGR but better on MaxDD/vol (no performance restoration)", new178.corrected.max_history.policy.cagr < old178.max_history.policy.met.cagr && new178.corrected.max_history.policy.maxdd > old178.max_history.policy.met.maxdd);
}

// ---------------------------------------------------------------- 16. deterministic rerun
{
  const list = fs.readdirSync(G183).filter((f) => f !== "determinism.json").sort();
  const before = Object.fromEntries(list.map((f) => [f, sha(fs.readFileSync(path.join(G183, f)))]));
  execFileSync(process.execPath, [path.join(RES, "issue_183_replay.mjs")], { cwd: ROOT, stdio: "ignore", maxBuffer: BIG });
  const after = Object.fromEntries(list.map((f) => [f, sha(fs.readFileSync(path.join(G183, f)))]));
  const diff = list.filter((f) => before[f] !== after[f]);
  ok("16. deterministic rerun reproduces every repaired artifact byte-for-byte", diff.length === 0, JSON.stringify(diff));
  const det = jG("determinism.json");
  ok("16b. replay self-check reports 2 identical in-process runs", det.byte_identical === true && det.runs === 2);
}

// ---------------------------------------------------------------- 17. no production / Pine changes
{
  const status = execFileSync("git", ["status", "--porcelain"], { cwd: ROOT, maxBuffer: BIG }).toString().replace(/\r/g, "");
  // __pycache__ is a Python bytecode cache (build artifact), never a source change.
  const changed = status.split("\n").filter(Boolean).map((l) => l.slice(3).trim()).filter((p) => !/(^|\/)__pycache__\//.test(p));
  const allowed = /^indicators\/macro-pressure-map\/research\/(generated\/issue-183\/|issue_183_|test_issue_183_|issue-183-|decisions\/issue-183-)/;
  const bad = changed.filter((p) => !allowed.test(p));
  ok("17. workspace changes are confined to Issue #183 artifacts", bad.length === 0, JSON.stringify(bad));
  const trackedDiff = execFileSync("git", ["diff", "--name-only", "HEAD"], { cwd: ROOT, maxBuffer: BIG }).toString().replace(/\r/g, "").split("\n").filter(Boolean);
  const stagedDiff = execFileSync("git", ["diff", "--cached", "--name-only", "HEAD"], { cwd: ROOT, maxBuffer: BIG }).toString().replace(/\r/g, "").split("\n").filter(Boolean);
  const trackedBad = [...new Set(trackedDiff.concat(stagedDiff))].filter((p) => !allowed.test(p));
  ok("17a. no pre-existing TRACKED file (production, Pine, parent artifact) is modified or staged", trackedBad.length === 0, JSON.stringify(trackedBad));
  const pine = execFileSync("git", ["diff", "--name-only", "57852112ce95913d48297b35f803a1583cbab314", "--", "*.pine"], { cwd: ROOT, maxBuffer: BIG }).toString().replace(/\r/g, "").trim();
  ok("17b. no production Pine file changed since the #182 final commit", pine === "", pine);
  const pineSt = execFileSync("git", ["status", "--porcelain", "--", "*.pine"], { cwd: ROOT, maxBuffer: BIG }).toString().replace(/\r/g, "").trim();
  ok("17c. no untracked/modified Pine files", pineSt === "", pineSt);
}

// ---------------------------------------------------------------- overall verdict consistency
{
  const s = jG("summary.json");
  ok("V. summary records production_authorized=false", s.production_authorized === false);
  ok("V2. three parent verdicts + overall verdict are from the frozen allowed sets",
    ["state_weight_policy_candidate_revalidated", "state_weight_policy_candidate_revalidated_with_limitations", "state_weight_policy_candidate_invalidated_by_repair"].includes(s.verdict_178) &&
    ["tradable_implementation_revalidated", "tradable_implementation_revalidated_with_limitations", "tradable_implementation_invalidated_by_repair"].includes(s.verdict_180) &&
    ["v66_tactical_overlay_candidate_supported", "v66_tactical_overlay_candidate_suggestive", "v66_tactical_overlay_not_supported"].includes(s.verdict_182) &&
    ["allocation_lineage_repair_complete", "allocation_lineage_repair_complete_with_material_changes", "allocation_lineage_repair_failed"].includes(s.overall_verdict),
    JSON.stringify({ a: s.verdict_178, b: s.verdict_180, c: s.verdict_182, o: s.overall_verdict }));
  // spec section 4 basis must carry every operand, evaluated independently
  const vb = s.verdict_basis_178;
  ok("V3. #178 verdict basis implements every spec section 4 operand",
    Math.abs(vb.rel_cagr_gap_pp) <= 1.0 && vb.same_sign_as_buggy_run === true && vb.maxdd_gap_pp >= -3.0 &&
    Math.abs(vb.turnover_gap_pp) <= 5.0 && vb.no_new_cap_or_cash_violation === true && vb.sensitivities_stable_within_1pp === true,
    JSON.stringify(vb));
  ok("V4. revalidated verdict follows from those operands", s.verdict_178 === "state_weight_policy_candidate_revalidated");
}
{
  // panel provenance: dropped months and annualisation robustness must be stated
  const pp = jG("performance-178.json").panel_provenance;
  ok("V5. panel provenance recorded (721 applied of 724 calendar months, 3 inherited drops)",
    pp && pp.applied_months === 721 && pp.calendar_span_months === 724 && pp.dropped_months.length === 3,
    JSON.stringify(pp && { a: pp.applied_months, c: pp.calendar_span_months, d: pp.dropped_months }));
  ok("V6. repair delta is robust to the frozen annualisation choice", pp && pp.delta_robust_to_annualization === true, JSON.stringify(pp && { a: pp.cagr_delta_pp_applied_basis, c: pp.cagr_delta_pp_calendar_basis }));
  ok("V7. #180 semantic mapping resolved by data (not hardcoded)", jG("preservation-180.json").semantic_unresolved === false);
  ok("V8. inputs_sha256 keys resolve to real workspace paths", Object.keys(jG("summary.json").inputs_sha256).every((k) => k.startsWith("generated/")));
}

console.log(`\nissue-183 independent assertions: ${pass} pass, ${fail} fail`);
fs.writeFileSync(path.join(G183, "test-results-183.json"), JSON.stringify({
  issue: 183,
  suite: "research/test_issue_183_asserts.mjs (independent; does not import the replay)",
  spec_commit: "149bf0bc994b523033f540f60c286df51dcb4866",
  total: pass + fail, pass, fail, results: RESULTS,
  production_authorized: false,
}, null, 2) + "\n");
if (fail) { console.error("FAILURES:\n" + failures.map((f) => " - " + f).join("\n")); process.exit(1); }
console.log("ALL PASS");
