// Issue #176 — Phase C conditional rerun (Node executor).
// Allowed ONLY post-prereg (7a48b62) + post-build. Reuses #174 frozen stack
// EXACTLY: same macro file, ±10 bands, episodes, eras, Cash, p10, materiality,
// classification + zero rules VERBATIM (self-check old cells reproduce #174).
// Affected cells ONLY: sp500_tr_hardened (9 states), oil_investable_return
// (9 states, NEW). Nasdaq/russell/others: reproduction self-check.
import fs from "node:fs";
import path from "node:path";
import crypto from "node:crypto";
import { execSync } from "node:child_process";

const ROOT = process.cwd();
const RES = path.join(ROOT, "indicators/macro-pressure-map/research");
const GEN174 = path.join(RES, "generated/issue-174");
const GEN = path.join(RES, "generated/issue-176");
const sha256 = (b) => crypto.createHash("sha256").update(b).digest("hex");
function gitBlob(p) { return execSync("git show HEAD:" + p, { maxBuffer: 100 * 1024 * 1024 }); }

// ---- verify frozen inputs ----
const macroSha = sha256(gitBlob("indicators/macro-pressure-map/research/generated/issue-160/deep-history-v01-monthly.csv"));
if (macroSha !== "42516418ec8d1ce981d1b4bc05e2ae86809d6acbf5de63dccbad515db507dcfc") { console.error("macro mismatch"); process.exit(1); }

// ---- frozen helpers (VERBATIM from #174 map) ----
function band(s) { if (s < -10) return "Low"; if (s > 10) return "High"; return "Neutral"; }
function stateOf(g, i) { return "G_" + band(g) + "/I_" + band(i); }
function eraOf(mo) {
  if (mo >= "1966-03-01" && mo <= "1979-12-01") return "E1_pre_volcker";
  if (mo >= "1980-01-01" && mo <= "2007-12-01") return "E2_great_moderation";
  if (mo >= "2008-01-01" && mo <= "2019-12-01") return "E3_post_gfc_qe";
  if (mo >= "2020-01-01" && mo <= "2026-08-01") return "E4_post_2020";
  return "OUT";
}
const fin = (x) => typeof x === "number" && isFinite(x);
function mean(a) { const v = a.filter(fin); return v.length ? v.reduce((s, x) => s + x, 0) / v.length : NaN; }
function median(a) { const v = a.filter(fin).sort((x, y) => x - y); if (!v.length) return NaN; const m = Math.floor(v.length / 2); return v.length % 2 ? v[m] : (v[m - 1] + v[m]) / 2; }
function bsd(a) { const v = a.filter(fin); if (!v.length) return NaN; const m = v.reduce((s, x) => s + x, 0) / v.length; return Math.sqrt(v.reduce((s, x) => s + (x - m) ** 2, 0) / v.length); }
function pct(a, q) { const v = a.filter(fin).sort((x, y) => x - y); if (!v.length) return NaN; if (v.length === 1) return v[0]; const p = q * (v.length - 1), lo = Math.floor(p), hi = Math.ceil(p); return lo === hi ? v[lo] : v[lo] * (hi - p) + v[hi] * (p - lo); }
function compound(rs) { let p = 1; for (const r of rs) { if (!fin(r)) return NaN; p *= 1 + r; } return p - 1; }
function calNext(mo) { let y = +mo.slice(0, 4), m = +mo.slice(5, 7) + 1; if (m > 12) { m = 1; y++; } return String(y).padStart(4, "0") + "-" + String(m).padStart(2, "0") + "-01"; }

// ---- load macro + episodes (frozen) ----
function loadMacro() {
  const t = fs.readFileSync(path.join(RES, "generated/issue-160/deep-history-v01-monthly.csv"), "utf8").trim().split("\n");
  const h = t[0].split(","); const gi = h.indexOf("growth_dh"), ii = h.indexOf("inflation_dh");
  const m = new Map();
  for (const l of t.slice(1)) { const c = l.split(","); const g = parseFloat(c[gi]), v = parseFloat(c[ii]); if (fin(g) && fin(v)) m.set(c[0], { g, i: v }); }
  return m;
}
const macro = loadMacro();
const macroMonths = [...macro.keys()].filter((d) => d >= "1966-03-01" && d <= "2026-08-01").sort();
const macroStates = macroMonths.map((d) => stateOf(macro.get(d).g, macro.get(d).i));
function buildEps(months, states) {
  const eps = []; let s = 0;
  for (let k = 1; k < months.length; k++) {
    if (states[k] === states[s] && calNext(months[k - 1]) === months[k]) continue;
    eps.push({ start: months[s], end: months[k - 1], state: states[s] }); s = k;
  }
  eps.push({ start: months[s], end: months[months.length - 1], state: states[s] });
  return eps;
}
const stateEpisodes = buildEps(macroMonths, macroStates);

// ---- load #174 backbone + #176 hardened ----
function loadCsv(p) {
  const t = fs.readFileSync(p, "utf8").trim().split("\n");
  const h = t[0].split(",").map((k) => k.trim());
  const m = new Map();
  for (const l of t.slice(1)) { const c = l.split(","); const r = {}; h.forEach((k, j) => r[k] = j === 0 ? c[j] : (c[j] === "" ? NaN : parseFloat(c[j]))); m.set(r.date.slice(0, 7), r); }
  return { header: h, map: m };
}
const old174 = loadCsv(path.join(GEN174, "nine-sleeve-monthly-returns.csv")).map;
const hard176 = loadCsv(path.join(GEN, "hardened-monthly-returns.csv")).map;
const joined = [];
for (const d of macroMonths) {
  const ym = d.slice(0, 7);
  const o = old174.get(ym), n = hard176.get(ym);
  if (!o) continue;
  joined.push({ date: d, state: stateOf(macro.get(d).g, macro.get(d).i), era: eraOf(d), cash: o.cash, sp_old: o.sp500, sp_new: n?.sp500_tr_hardened, oil_old: o.oil, oil_new: n?.oil_investable_return, nas: o.nasdaq, rus: o.russell });
}

// ---- frozen cell computer (VERBATIM #174 logic) ----
const ELIG = { sp: "eligible_primary", oil: "eligible_with_limitation" };
function cell(state, getR) {
  const obs = joined.filter((j) => j.state === state && fin(getR(j)) && fin(j.cash));
  const rs = obs.map(getR), ex = obs.map((o) => getR(o) - o.cash);
  const nM = rs.length;
  const comp = compound(rs), compC = compound(obs.map((o) => o.cash));
  const gex = fin(comp) && fin(compC) ? (1 + comp) / (1 + compC) - 1 : NaN;
  // episodes
  const eps = stateEpisodes.filter((e) => e.state === state);
  const ReAll = [];
  let worstEp = NaN;
  for (const e of eps) {
    const em = []; let d = e.start;
    while (true) { const j = joined.find((x) => x.date === d); if (j && fin(getR(j)) && fin(j.cash)) em.push(j); if (d === e.end) break; d = calNext(d); }
    if (!em.length) continue;
    const Rs = compound(em.map((x) => getR(x))), Rc = compound(em.map((x) => x.cash));
    const Re = fin(Rs) && fin(Rc) ? (1 + Rs) / (1 + Rc) - 1 : NaN;
    ReAll.push(Re);
    const w = em.length ? Rs : NaN;
    if (fin(w) && (!fin(worstEp) || w < worstEp)) worstEp = w;
  }
  const epHit = ReAll.length ? ReAll.filter((r) => r > 0).length / ReAll.length : NaN;
  // eras
  const eraMeans = {};
  for (const er of ["E1_pre_volcker", "E2_great_moderation", "E3_post_gfc_qe", "E4_post_2020"]) {
    const eo = obs.filter((o) => o.era === er);
    eraMeans[er] = eo.length >= 12 ? mean(eo.map((o) => getR(o) - o.cash)) : NaN;
  }
  const vals = Object.values(eraMeans).filter(fin);
  const posE = vals.filter((v) => v > 0).length, negE = vals.filter((v) => v < 0).length;
  const persPos = vals.length >= 3 && negE === 0 && posE >= 3;
  const persNeg = vals.length >= 3 && posE === 0 && negE >= 3;
  // classification VERBATIM
  const meanEx = mean(ex), posM = nM ? ex.filter((e) => e > 0).length / nM : NaN;
  const p10ex = pct(ex, 0.10), worst = nM ? Math.min(...rs.filter(fin)) : NaN;
  const pUnder = nM ? ex.filter((e) => e < 0).length / nM : NaN;
  let evidence = "mixed";
  if (nM < 24 || ReAll.length < 4) evidence = "insufficient_sample";
  else if (fin(meanEx) && meanEx > 0.001 && fin(posM) && posM >= 0.55 && fin(epHit) && epHit >= 0.60 && fin(p10ex) && p10ex >= -0.04 && fin(worst) && worst > -0.20 && !persNeg) evidence = "historically_favored";
  else if (fin(meanEx) && meanEx < -0.0005 && ((fin(posM) && posM <= 0.45) || (fin(epHit) && epHit <= 0.40)) && ((fin(p10ex) && p10ex <= -0.03) || (fin(worst) && worst <= -0.10) || (fin(pUnder) && pUnder >= 0.60)) && !persPos) evidence = "historically_unfavorable";
  // zero VERBATIM
  const pMat = nM ? ex.filter((e) => e < -0.02).length / nM : NaN;
  const tailHit = (fin(p10ex) && p10ex <= -0.04) || (fin(worstEp) && worstEp <= -0.15) || (fin(pMat) && pMat >= 0.10);
  const zero = (nM >= 60 && ReAll.length >= 6 && fin(epHit) && epHit <= 0.40 && fin(meanEx) && meanEx < 0 && tailHit && !persPos);
  // (ex-worst check folded: full VERBATIM needs ex-worst mean; compute)
  return { nM, nE: ReAll.length, mean: mean(rs), vol: fin(bsd(rs)) ? bsd(rs) * Math.sqrt(12) : NaN, p10: pct(rs, 0.10), meanEx, epHit, evidence, pUnder, worstEp, zeroPrelim: zero, obs, ReAll };
}

const STATES = [];
for (const g of ["Low", "Neutral", "High"]) for (const i of ["Low", "Neutral", "High"]) STATES.push("G_" + g + "/I_" + i);

// self-check vs #174 CSVs
function load174out(f, key) {
  const t = fs.readFileSync(path.join(GEN174, f), "utf8").trim().split("\n");
  const h = t[0].split(",");
  const m = new Map();
  for (const l of t.slice(1)) { const c = l.split(","); m.set(c[0] + "|" + c[1], Object.fromEntries(h.map((k, j) => [k, c[j]]))); }
  return m;
}
const mMonth = load174out("month-weighted-outcomes.csv");
const mClass = load174out("evidence-classification.csv");
let mism = 0;
for (const st of STATES) {
  for (const [sl, get] of [["sp500", (j) => j.sp_old], ["oil", (j) => j.oil_old], ["nasdaq", (j) => j.nas], ["russell", (j) => j.rus]]) {
    const c = cell(st, get);
    const ref = mMonth.get(st + "|" + (sl === "sp500" ? "sp500" : sl === "oil" ? "oil" : sl));
    const rMean = parseFloat(ref.mean);
    if (Math.abs(c.mean - rMean) > 1e-12) { mism++; console.log("MISMATCH", st, sl, c.mean, rMean); }
    const rc = mClass.get(st + "|" + (sl === "sp500" ? "sp500" : sl === "oil" ? "oil" : sl));
    if (rc.evidence !== c.evidence) { mism++; console.log("LABEL MISMATCH", st, sl, c.evidence, rc.evidence); }
  }
}
console.log("self-check mismatches:", mism);
if (mism > 0) process.exit(1);

// affected cells
const sens = [], changed = [];
function verdict(oldE, newE, oldZ, newZ, oldX, newX, oldH, newH) {
  if (oldE !== newE) {
    if ((oldE === "historically_favored" && newE === "historically_unfavorable") || (oldE === "historically_unfavorable" && newE === "historically_favored")) return "reversed";
    if (newE === "historically_favored" || (oldE === "historically_unfavorable" && newE === "mixed")) return "strengthened";
    return "weakened";
  }
  if (oldZ !== newZ) return newZ === "true" ? "strengthened" : "weakened";
  if (Math.sign(oldX) !== Math.sign(newX) && oldX !== 0) return newX > oldX ? "strengthened" : "weakened";
  return "unchanged";
}
for (const st of STATES) {
  // sp500 old vs new
  const co = cell(st, (j) => j.sp_old), cn = cell(st, (j) => j.sp_new);
  const zo = mClass.get(st + "|sp500").future_zero_weight_candidate;
  // recompute zero fully (VERBATIM incl ex-worst): approximate via cell zeroPrelim + ex-worst
  const zn = co.zeroPrelim; // placeholder, computed properly below
  const row = { state: st, sleeve: "sp500", n_old: co.nM, n_new: cn.nM, mean_old: co.mean, mean_new: cn.mean, ex_old: co.meanEx, ex_new: cn.meanEx, vol_old: co.vol, vol_new: cn.vol, p10_old: co.p10, p10_new: cn.p10, hit_old: co.epHit, hit_new: cn.epHit, ev_old: co.evidence, ev_new: cn.evidence, zero_old: zo, zero_new: null, conclusion: null };
  sens.push(row);
}
// oil investable NEW cells (no old counterpart; spot reproduced above in self-check)
const oilNew = [];
for (const st of STATES) {
  const cn = cell(st, (j) => j.oil_new);
  // full VERBATIM zero flag incl ex-worst (eligibility hardened_with_limitation)
  const obsN = joined.filter((j) => j.state === st && fin(j.oil_new) && fin(j.cash));
  const epsN = stateEpisodes.filter((e) => e.state === st);
  let wS = null, wE = null, wRs = NaN;
  for (const e of epsN) {
    const em = []; let d = e.start;
    while (true) { const j = joined.find((x) => x.date === d); if (j && fin(j.oil_new) && fin(j.cash)) em.push(j); if (d === e.end) break; d = calNext(d); }
    if (!em.length) continue;
    const Rs = compound(em.map((x) => x.oil_new));
    if (fin(Rs) && (!fin(wRs) || Rs < wRs)) { wRs = Rs; wS = e.start; wE = e.end; }
  }
  const keepN = obsN.filter((o) => !(wS && o.date >= wS && o.date <= wE));
  const exWorstN = keepN.length ? mean(keepN.map((o) => o.oil_new - o.cash)) : NaN;
  const exN = obsN.map((o) => o.oil_new - o.cash);
  const p10exN = pct(exN, 0.10), pMatN = exN.length ? exN.filter((e) => e < -0.02).length / exN.length : NaN;
  const eraM = {};
  for (const er of ["E1_pre_volcker", "E2_great_moderation", "E3_post_gfc_qe", "E4_post_2020"]) {
    const eo = obsN.filter((o) => o.era === er);
    eraM[er] = eo.length >= 12 ? mean(eo.map((o) => o.oil_new - o.cash)) : NaN;
  }
  const vv = Object.values(eraM).filter(fin);
  const pp = vv.length >= 3 && vv.filter((v) => v < 0).length === 0 && vv.filter((v) => v > 0).length >= 3;
  const tN = (fin(p10exN) && p10exN <= -0.04) || (fin(wRs) && wRs <= -0.15) || (fin(pMatN) && pMatN >= 0.10);
  const zeroN = cn.evidence === "historically_unfavorable" && cn.nM >= 60 && cn.nE >= 6 && fin(cn.epHit) && cn.epHit <= 0.40 && fin(cn.meanEx) && cn.meanEx < 0 && tN && !pp && fin(exWorstN) && exWorstN < 0;
  oilNew.push({ state: st, sleeve: "oil_investable_return", n: cn.nM, nE: cn.nE, mean: cn.mean, meanEx: cn.meanEx, vol: cn.vol, p10: cn.p10, epHit: cn.epHit, evidence: cn.evidence, zero: String(zeroN) });
}
// finalize sp500 zero flags with ex-worst VERBATIM + verdicts
for (const r of sens) {
  const st = r.state;
  const obsNew = joined.filter((j) => j.state === st && fin(j.sp_new) && fin(j.cash));
  // worst episode months for new
  const eps = stateEpisodes.filter((e) => e.state === st);
  let wStart = null, wEnd = null, wRs = NaN;
  for (const e of eps) {
    const em = []; let d = e.start;
    while (true) { const j = joined.find((x) => x.date === d); if (j && fin(j.sp_new) && fin(j.cash)) em.push(j); if (d === e.end) break; d = calNext(d); }
    if (!em.length) continue;
    const Rs = compound(em.map((x) => x.sp_new));
    if (fin(Rs) && (!fin(wRs) || Rs < wRs)) { wRs = Rs; wStart = e.start; wEnd = e.end; }
  }
  const keep = obsNew.filter((o) => !(wStart && o.date >= wStart && o.date <= wEnd));
  const exWorst = keep.length ? mean(keep.map((o) => o.sp_new - o.cash)) : NaN;
  const cn = cell(st, (j) => j.sp_new);
  const tailHit = (fin(cn.p10) && false) || false; // recompute properly:
  const ex = obsNew.map((o) => o.sp_new - o.cash);
  const p10ex = pct(ex, 0.10);
  const pMat = ex.length ? ex.filter((e) => e < -0.02).length / ex.length : NaN;
  const t2 = (fin(p10ex) && p10ex <= -0.04) || (fin(wRs) && wRs <= -0.15) || (fin(pMat) && pMat >= 0.10);
  // era persPos for new
  const eraMeans = {};
  for (const er of ["E1_pre_volcker", "E2_great_moderation", "E3_post_gfc_qe", "E4_post_2020"]) {
    const eo = obsNew.filter((o) => o.era === er);
    eraMeans[er] = eo.length >= 12 ? mean(eo.map((o) => o.sp_new - o.cash)) : NaN;
  }
  const vals = Object.values(eraMeans).filter(fin);
  const persPos = vals.length >= 3 && vals.filter((v) => v < 0).length === 0 && vals.filter((v) => v > 0).length >= 3;
  const zeroNew = cn.evidence === "historically_unfavorable" && cn.nM >= 60 && cn.nE >= 6 && fin(cn.epHit) && cn.epHit <= 0.40 && fin(cn.meanEx) && cn.meanEx < 0 && t2 && !persPos && fin(exWorst) && exWorst < 0;
  r.zero_new = String(zeroNew);
  r.conclusion = verdict(r.ev_old, r.ev_new, r.zero_old, r.zero_new, r.ex_old, r.ex_new);
  if (r.ev_old !== r.ev_new || r.zero_old !== r.zero_new) changed.push({ state: st, sleeve: "sp500", ev_old: r.ev_old, ev_new: r.ev_new, zero_old: r.zero_old, zero_new: r.zero_new, conclusion: r.conclusion });
}
fs.writeFileSync(path.join(GEN, "affected-state-sensitivity.csv"),
  "state,sleeve,n_old,n_new,mean_old,mean_new,ex_old,ex_new,vol_old,vol_new,p10_old,p10_new,hit_old,hit_new,ev_old,ev_new,zero_old,zero_new,conclusion\n" +
  sens.map((r) => [r.state, r.sleeve, r.n_old, r.n_new, r.mean_old, r.mean_new, r.ex_old, r.ex_new, r.vol_old, r.vol_new, r.p10_old, r.p10_new, r.hit_old, r.hit_new, r.ev_old, r.ev_new, r.zero_old, r.zero_new, r.conclusion].join(",")).join("\n") + "\n");
fs.writeFileSync(path.join(GEN, "changed-classification.csv"),
  "state,sleeve,ev_old,ev_new,zero_old,zero_new,conclusion\n" +
  (changed.length ? changed.map((r) => [r.state, r.sleeve, r.ev_old, r.ev_new, r.zero_old, r.zero_new, r.conclusion].join(",")).join("\n") : "") + "\n");
fs.writeFileSync(path.join(GEN, "oil-investable-state-cells.csv"),
  "state,n,episodes,mean,meanEx,vol,p10,epHit,evidence,zero_candidate\n" +
  oilNew.map((r) => [r.state, r.n, r.nE, r.mean, r.meanEx, r.vol, r.p10, r.epHit, r.evidence, r.zero].join(",")).join("\n") + "\n");
const summary = {
  issue: 176, branch: "research/issue-176-allocation-backbone-hardening", base_head: "f1fdda31fc355ac857796fe10ca3b7bcd38964b8",
  prereg_commit: "7a48b62ade201127b5ce1ae27633730dfcb30fba",
  self_check_mismatches: mism,
  sp500_changed: changed, oil_investable_cells: oilNew,
  production_authorized: false, outcome_data_loaded: true,
};
fs.writeFileSync(path.join(GEN, "summary.json"), JSON.stringify(summary, null, 2));
console.log("sens conclusions:", sens.map((r) => r.state + ":" + r.conclusion).join(" "));
console.log("DONE rerun");
