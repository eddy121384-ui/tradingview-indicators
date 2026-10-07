// Issue #177 — deterministic policy builder (Node executor).
// Frozen methodology: issue-177-state-allocation-policy-prereg.md
//
// Pipeline (frozen order):
//   1. pin the canonical HEAD blob SHA-256 of every frozen input and assert the
//      worktree copy is byte-equivalent after CRLF normalisation (STOP on drift);
//   2. recompute the #174 month/episode/era/danger/classification tables from the
//      frozen #174 returns and the #176 hardened S&P / investable-oil tables from
//      the frozen #176 returns, exactly with the frozen #174 formulas, and require
//      0 mismatches BEFORE any exposure tier is emitted (self-check gate);
//   3. assert frozen full-common-sample window coverage (panel-comparison.json);
//   4. derive the primary 9x9 matrix, cash bias, zero audit, confidence table,
//      full-common-sample policy sensitivity, consistency checks, state cards and
//      machine-readable summary.
//
// No percentages. No optimizer. No Pine. No trajectory. No V6.6. No manual overrides.
import fs from "node:fs";
import path from "node:path";
import crypto from "node:crypto";
import { execSync } from "node:child_process";
import { fileURLToPath } from "node:url";

// ROOT is resolved from this file's own location: <repo>/indicators/macro-pressure-map/research
const RES = path.dirname(fileURLToPath(import.meta.url));
const ROOT = path.resolve(RES, "../../..");
const GEN174 = path.join(RES, "generated/issue-174");
const GEN176 = path.join(RES, "generated/issue-176");
const GEN = path.join(RES, "generated/issue-177");
fs.mkdirSync(GEN, { recursive: true });

const sha256 = (b) => crypto.createHash("sha256").update(b).digest("hex");
function gitBlob(p) { return execSync("git show HEAD:" + p, { cwd: ROOT, maxBuffer: 100 * 1024 * 1024 }); }
const normText = (s) => s.replace(/\r\n/g, "\n");

// ---- 1. frozen input pinning (canonical blob SHAs captured at #176 final) ----
const R = "indicators/macro-pressure-map/research/generated";
const FROZEN = {
  [`${R}/issue-160/deep-history-v01-monthly.csv`]: "42516418ec8d1ce981d1b4bc05e2ae86809d6acbf5de63dccbad515db507dcfc",
  [`${R}/issue-174/evidence-classification.csv`]: "87ea365e1ffe4e6c0ab1d38e7e213fd98802abb5c873fe24f1e850606d9c87e9",
  [`${R}/issue-174/month-weighted-outcomes.csv`]: "f59909fdcb52612b71375fba8c2d8c25be7d6ce65035a50fe6f779d30fffaf31",
  [`${R}/issue-174/episode-weighted-outcomes.csv`]: "fd057b84a1fbbe312de122f03ea17b126900085015fdde080e4757ed7eba5fdb",
  [`${R}/issue-174/era-stability.csv`]: "5e3abcc02354733d0ae86d4844312df49b0497fa10e052eff739a65b1e08eb7b",
  [`${R}/issue-174/downside-danger.csv`]: "4ff60a9c5fccc190f6a37e5d76dbca3c164c336a9483d245369126816d063fd6",
  [`${R}/issue-174/future-zero-candidates.csv`]: "4cf82f3a1625c5f4ac92dc2c781af32ef6cd0a95012506c88b3895798aacd139",
  [`${R}/issue-174/nine-sleeve-monthly-returns.csv`]: "cbee7f210a55c25e73f890fc1743a6c0cc08b84bd0700820ba486ce38acb1b0a",
  [`${R}/issue-174/panel-comparison.json`]: "59747ce9ddd0458f32e283f7b092deccd6339d3bb90874f116215933cda0e5a7",
  [`${R}/issue-176/affected-state-sensitivity.csv`]: "1c3d42a7cd7857be423e06aa171751975ca20433d53ea6085e2c821a639dd6ff",
  [`${R}/issue-176/oil-investable-state-cells.csv`]: "5d50e0c32c86c62565603a9f46611fa7ad118bd609b7c4d66728e5cdaf6038ce",
  [`${R}/issue-176/hardened-monthly-returns.csv`]: "7588023e1e242f78c9de43f6d0c4bbfd49ea33a4b05ec578353559a364a3434a",
};
const INPUT_SHAS = {};
let frozenFail = 0;
for (const [rel, wantBlob] of Object.entries(FROZEN)) {
  const worktree = normText(fs.readFileSync(path.join(ROOT, rel), "utf8"));
  const wtSha = sha256(Buffer.from(worktree, "utf8"));
  const headSha = sha256(gitBlob(rel));
  INPUT_SHAS[rel.replace(R + "/", "")] = { head_blob_sha256: headSha, worktree_normalised_sha256: wtSha };
  if (headSha !== wantBlob) { console.error("FROZEN HEAD BLOB MISMATCH", rel, headSha); frozenFail++; }
  if (wtSha !== headSha) { console.error("FROZEN WORKTREE DRIFT", rel, wtSha); frozenFail++; }
}
if (frozenFail) { console.error("frozen input verification FAILED:", frozenFail); process.exit(1); }
console.log("frozen inputs verified:", Object.keys(FROZEN).length, "files (canonical blob SHA-256 + worktree equivalence)");

// ---- 2. frozen helpers (VERBATIM #174 engine) ----
const fin = (x) => typeof x === "number" && isFinite(x);
function mean(a) { const v = a.filter(fin); return v.length ? v.reduce((s, x) => s + x, 0) / v.length : NaN; }
function median(a) { const v = a.filter(fin).sort((x, y) => x - y); if (!v.length) return NaN; const n = v.length, m = Math.floor(n / 2); return n % 2 ? v[m] : (v[m - 1] + v[m]) / 2; }
function pct(a, q) { const v = a.filter(fin).sort((x, y) => x - y); if (!v.length) return NaN; if (v.length === 1) return v[0]; const p = q * (v.length - 1), lo = Math.floor(p), hi = Math.ceil(p); return lo === hi ? v[lo] : v[lo] * (hi - p) + v[hi] * (p - lo); }
function compound(rs) { let p = 1; for (const r of rs) { if (!fin(r)) return NaN; p *= 1 + r; } return p - 1; }
function bsd(a) { const v = a.filter(fin); if (!v.length) return NaN; const m = v.reduce((s, x) => s + x, 0) / v.length; return Math.sqrt(v.reduce((s, x) => s + (x - m) ** 2, 0) / v.length); }
function band(s) { if (s < -10) return "Low"; if (s > 10) return "High"; return "Neutral"; }
function stateOf(g, i) { return "G_" + band(g) + "/I_" + band(i); }
function eraOf(mo) {
  if (mo >= "1966-03-01" && mo <= "1979-12-01") return "E1_pre_volcker";
  if (mo >= "1980-01-01" && mo <= "2007-12-01") return "E2_great_moderation";
  if (mo >= "2008-01-01" && mo <= "2019-12-01") return "E3_post_gfc_qe";
  if (mo >= "2020-01-01" && mo <= "2026-08-01") return "E4_post_2020";
  return "OUT";
}
function calNext(mo) { let y = +mo.slice(0, 4), m = +mo.slice(5, 7) + 1; if (m > 12) { m = 1; y++; } return String(y).padStart(4, "0") + "-" + String(m).padStart(2, "0") + "-01"; }
const ERAS = ["E1_pre_volcker", "E2_great_moderation", "E3_post_gfc_qe", "E4_post_2020"];
const STATES = [];
for (const g of ["Low", "Neutral", "High"]) for (const i of ["Low", "Neutral", "High"]) STATES.push("G_" + g + "/I_" + i);
const SLEEVES174 = ["sp500", "nasdaq", "russell", "cash", "treasury2y", "treasury10y", "longtreasury", "gold", "oil"];
const NONCASH = ["sp500", "nasdaq", "russell", "treasury2y", "treasury10y", "longtreasury", "gold", "oil"];

// Robust CSV reader: CRLF-safe, every field trimmed (frozen files are CRLF).
function parseCsv(text) {
  const lines = normText(text).trim().split("\n");
  const header = lines[0].split(",").map((k) => k.trim());
  const rows = lines.slice(1).filter((l) => l.trim() !== "").map((l) => {
    const c = l.split(",");
    const r = {};
    header.forEach((k, j) => { r[k] = c[j] === undefined ? "" : c[j].trim(); });
    return r;
  });
  return { header, rows };
}
function cellVal(c) {
  if (c === "" || c === undefined) return NaN;
  if (c === "true") return true;
  if (c === "false") return false;
  const n = parseFloat(c);
  return isFinite(n) ? n : c;
}
const RAW_COLS = new Set(["state", "sleeve", "date"]);
function loadCsvMap(p, keyFn) {
  const { header, rows } = parseCsv(fs.readFileSync(p, "utf8"));
  const typed = rows.map((r) => {
    const o = {};
    for (const k of header) o[k] = RAW_COLS.has(k) ? r[k] : cellVal(r[k]);
    return o;
  });
  return { header, rows: typed, map: new Map(typed.map((r) => [keyFn(r), r])) };
}

// ---- 3. load macro + episodes + returns ----
function loadMacro() {
  const { rows } = parseCsv(fs.readFileSync(path.join(RES, "generated/issue-160/deep-history-v01-monthly.csv"), "utf8"));
  const m = new Map();
  for (const r of rows) {
    const g = parseFloat(r.growth_dh), v = parseFloat(r.inflation_dh);
    if (fin(g) && fin(v)) m.set(r.date, { g, i: v });
  }
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
const ret174 = loadCsvMap(path.join(GEN174, "nine-sleeve-monthly-returns.csv"), (r) => r.date.slice(0, 7));
const ret176 = loadCsvMap(path.join(GEN176, "hardened-monthly-returns.csv"), (r) => r.date.slice(0, 7));
const joined = [];
for (const d of macroMonths) {
  const ym = d.slice(0, 7);
  const o = ret174.map.get(ym), n = ret176.map.get(ym);
  if (!o) continue;
  const j = { date: d, state: stateOf(macro.get(d).g, macro.get(d).i), era: eraOf(d), cash: o.cash };
  for (const sl of SLEEVES174) j[sl] = o[sl];
  j.sp_hard = n ? n.sp500_tr_hardened : NaN;
  j.oil_inv = n ? n.oil_investable_return : NaN;
  joined.push(j);
}

// ---- 4. frozen cell-stats engine (VERBATIM #174 + strict zero flag) ----
function cellStats(state, getR, filterFn) {
  const obs = joined.filter((j) => j.state === state && filterFn(j.date) && fin(getR(j)) && fin(j.cash));
  const rs = obs.map(getR), ex = obs.map((o) => getR(o) - o.cash);
  const nM = rs.length;
  const meanEx = mean(ex), posM = nM ? ex.filter((e) => e > 0).length / nM : NaN;
  const p10ex = pct(ex, 0.10), worstM = nM ? Math.min(...rs.filter(fin)) : NaN;
  const pUnder = nM ? ex.filter((e) => e < 0).length / nM : NaN;
  const pMat = nM ? ex.filter((e) => e < -0.02).length / nM : NaN;
  const eps = stateEpisodes.filter((e) => e.state === state);
  const ReAll = []; let worstEp = NaN, wStart = "", wEnd = "";
  for (const e of eps) {
    const em = []; let d = e.start;
    while (true) { const j = joined.find((x) => x.date === d); if (j && filterFn(d) && fin(getR(j)) && fin(j.cash)) em.push(j); if (d === e.end) break; d = calNext(d); }
    if (!em.length) continue;
    const Rs = compound(em.map((x) => getR(x))), Rc = compound(em.map((x) => x.cash));
    const Re = fin(Rs) && fin(Rc) ? (1 + Rs) / (1 + Rc) - 1 : NaN;
    ReAll.push(Re);
    if (fin(Rs) && (!fin(worstEp) || Rs < worstEp)) { worstEp = Rs; wStart = e.start; wEnd = e.end; }
  }
  const epHit = ReAll.length ? ReAll.filter((r) => r > 0).length / ReAll.length : NaN;
  const keep = (wStart) ? obs.filter((o) => !(o.date >= wStart && o.date <= wEnd)) : obs;
  const exWorst = keep.length ? mean(keep.map((o) => getR(o) - o.cash)) : NaN;
  const eraMeans = {};
  for (const er of ERAS) {
    const eo = obs.filter((o) => o.era === er);
    eraMeans[er] = eo.length >= 12 ? mean(eo.map((o) => getR(o) - o.cash)) : NaN;
  }
  const vals = Object.values(eraMeans).filter(fin);
  const posE = vals.filter((v) => v > 0).length, negE = vals.filter((v) => v < 0).length;
  const persPos = vals.length >= 3 && negE === 0 && posE >= 3;
  const persNeg = vals.length >= 3 && posE === 0 && negE >= 3;
  let eraLabel = "insufficient_era";
  if (vals.length >= 2) {
    if (posE === vals.length) eraLabel = "persistent_positive";
    else if (negE === vals.length) eraLabel = "persistent_negative";
    else if ((posE >= 3 || negE >= 3) && vals.length >= 3) eraLabel = posE >= 3 ? "broadly_positive" : "broadly_negative";
    else eraLabel = "mixed";
  }
  let evidence = "mixed";
  if (nM < 24 || ReAll.length < 4) evidence = "insufficient_sample";
  else if (fin(meanEx) && meanEx > 0.001 && fin(posM) && posM >= 0.55 && fin(epHit) && epHit >= 0.60 && fin(p10ex) && p10ex >= -0.04 && fin(worstM) && worstM > -0.20 && !persNeg) evidence = "historically_favored";
  else if (fin(meanEx) && meanEx < -0.0005 && ((fin(posM) && posM <= 0.45) || (fin(epHit) && epHit <= 0.40)) && ((fin(p10ex) && p10ex <= -0.03) || (fin(worstM) && worstM <= -0.10) || (fin(pUnder) && pUnder >= 0.60)) && !persPos) evidence = "historically_unfavorable";
  // strict frozen danger flag (#174 §10 / #176 rerun): eligibility is primary-or-limitation for all 9 sleeves
  const tailHit = (fin(p10ex) && p10ex <= -0.04) || (fin(worstEp) && worstEp <= -0.15) || (fin(pMat) && pMat >= 0.10);
  const strictZero = evidence === "historically_unfavorable" && nM >= 60 && ReAll.length >= 6 && fin(epHit) && epHit <= 0.40
    && fin(meanEx) && meanEx < 0 && tailHit && !persPos && fin(exWorst) && exWorst < 0;
  return { nM, nE: ReAll.length, mean: mean(rs), median: median(rs), vol: fin(bsd(rs)) ? bsd(rs) * Math.sqrt(12) : NaN, p10: pct(rs, 0.10), meanEx, posM, epHit, p10ex, worstM, pUnder, pMat, worstEp, exWorst, persPos, persNeg, nEval: vals.length, eraLabel, evidence, tailHit, strictZero };
}

// ---- 5. SELF-CHECK GATE (0 mismatches required before any tier) ----
const ev174 = loadCsvMap(path.join(GEN174, "evidence-classification.csv"), (r) => r.state + "|" + r.sleeve);
const mo174 = loadCsvMap(path.join(GEN174, "month-weighted-outcomes.csv"), (r) => r.state + "|" + r.sleeve);
const ep174 = loadCsvMap(path.join(GEN174, "episode-weighted-outcomes.csv"), (r) => r.state + "|" + r.sleeve);
const era174 = loadCsvMap(path.join(GEN174, "era-stability.csv"), (r) => r.state + "|" + r.sleeve);
const dg174 = loadCsvMap(path.join(GEN174, "downside-danger.csv"), (r) => r.state + "|" + r.sleeve);
const sens176 = loadCsvMap(path.join(GEN176, "affected-state-sensitivity.csv"), (r) => r.state + "|" + r.sleeve);
const inv176 = loadCsvMap(path.join(GEN176, "oil-investable-state-cells.csv"), (r) => r.state);
const panel174 = JSON.parse(normText(fs.readFileSync(path.join(GEN174, "panel-comparison.json"), "utf8")));

let mism = 0; const mislog = []; const chkByTable = {};
function chk(cond, msg, table) {
  chkByTable[table] = chkByTable[table] || { compared: 0, mismatches: 0 };
  chkByTable[table].compared++;
  if (!cond) { chkByTable[table].mismatches++; mism++; if (mislog.length < 40) mislog.push(msg); }
}
const near = (a, b) => (fin(a) && fin(b)) ? Math.abs(a - b) < 1e-12 : (!fin(a) && !fin(b));
const allF = () => true;
for (const st of STATES) {
  for (const sl of SLEEVES174) {
    const key = st + "|" + sl;
    const c = cellStats(st, (j) => j[sl], allF);
    const m = mo174.map.get(key), e = ep174.map.get(key), g = era174.map.get(key), d = dg174.map.get(key), v = ev174.map.get(key);
    // #174 month-weighted table
    chk(near(c.nM, m.n_months), `mo.n ${key}`, "issue-174/month-weighted");
    chk(near(c.mean, m.mean), `mo.mean ${key}`, "issue-174/month-weighted");
    chk(near(c.median, m.median), `mo.median ${key}`, "issue-174/month-weighted");
    chk(near(c.vol, m.vol_ann), `mo.vol ${key}`, "issue-174/month-weighted");
    chk(near(c.p10, m.p10), `mo.p10 ${key}`, "issue-174/month-weighted");
    chk(near(c.meanEx, m.cash_ex_mean), `mo.meanEx ${key}`, "issue-174/month-weighted");
    chk(near(c.posM, m.cash_ex_pos_frac), `mo.posM ${key}`, "issue-174/month-weighted");
    chk(near(c.p10ex, m.p10_ex), `mo.p10ex ${key}`, "issue-174/month-weighted");
    // #174 episode table
    chk(near(c.nE, e.n_episodes), `ep.n ${key}`, "issue-174/episode-weighted");
    chk(near(c.epHit, e.ep_ex_pos_frac), `ep.hit ${key}`, "issue-174/episode-weighted");
    chk(near(c.worstEp, e.worst_ep), `ep.worst ${key}`, "issue-174/episode-weighted");
    // #174 era table
    chk(c.eraLabel === g.era_label, `era.label ${key}: ${c.eraLabel} vs ${g.era_label}`, "issue-174/era-stability");
    chk(near(c.nEval, g.n_eval_eras), `era.nEval ${key}`, "issue-174/era-stability");
    // #174 danger table
    chk(near(c.worstM, d.worst_monthly), `dg.worst_m ${key}`, "issue-174/downside-danger");
    chk(near(c.worstEp, d.worst_episode), `dg.worst_ep ${key}`, "issue-174/downside-danger");
    chk(near(c.p10ex, d.p10_ex), `dg.p10ex ${key}`, "issue-174/downside-danger");
    chk(near(c.pUnder, d.p_underperform), `dg.pUnder ${key}`, "issue-174/downside-danger");
    chk(near(c.pMat, d.p_material_monthly), `dg.pMat ${key}`, "issue-174/downside-danger");
    // #174 classification table
    chk(c.evidence === v.evidence, `cl.evidence ${key}: ${c.evidence} vs ${v.evidence}`, "issue-174/evidence-classification");
    chk(near(c.nM, v.n_months), `cl.nM ${key}`, "issue-174/evidence-classification");
    chk(near(c.nE, v.n_episodes), `cl.nE ${key}`, "issue-174/evidence-classification");
    chk(near(c.meanEx, v.mean_ex), `cl.meanEx ${key}`, "issue-174/evidence-classification");
    chk(near(c.posM, v.pos_m_frac), `cl.posM ${key}`, "issue-174/evidence-classification");
    chk(near(c.epHit, v.ep_hit), `cl.epHit ${key}`, "issue-174/evidence-classification");
    chk(near(c.p10ex, v.p10_ex), `cl.p10ex ${key}`, "issue-174/evidence-classification");
    chk(near(c.worstM, v.worst_m), `cl.worstM ${key}`, "issue-174/evidence-classification");
    chk(near(c.pUnder, v.p_under), `cl.pUnder ${key}`, "issue-174/evidence-classification");
    chk(c.persPos === v.persistent_positive, `cl.persPos ${key}`, "issue-174/evidence-classification");
    chk(c.persNeg === v.persistent_negative, `cl.persNeg ${key}`, "issue-174/evidence-classification");
    chk(c.eraLabel === v.era_label, `cl.eraLabel ${key}`, "issue-174/evidence-classification");
    chk(c.strictZero === v.future_zero_weight_candidate, `cl.zeroFlag ${key}: ${c.strictZero} vs ${v.future_zero_weight_candidate}`, "issue-174/evidence-classification");
    chk(near(c.exWorst, v.ex_worst_mean_ex), `cl.exWorst ${key}`, "issue-174/evidence-classification");
  }
  // #176 hardened S&P 500 table
  {
    const c = cellStats(st, (j) => j.sp_hard, allF);
    const r = sens176.map.get(st + "|sp500");
    const T = "issue-176/affected-state-sensitivity";
    chk(near(c.nM, r.n_new), `sp.n ${st}`, T);
    chk(near(c.mean, r.mean_new), `sp.mean ${st}`, T);
    chk(near(c.meanEx, r.ex_new), `sp.meanEx ${st}`, T);
    chk(near(c.vol, r.vol_new), `sp.vol ${st}`, T);
    chk(near(c.p10, r.p10_new), `sp.p10 ${st}`, T);
    chk(near(c.epHit, r.hit_new), `sp.hit ${st}`, T);
    chk(c.evidence === r.ev_new, `sp.evidence ${st}: ${c.evidence} vs ${r.ev_new}`, T);
    chk(c.strictZero === (r.zero_new === true || r.zero_new === "true"), `sp.zeroFlag ${st}`, T);
  }
  // #176 investable oil table
  {
    const c = cellStats(st, (j) => j.oil_inv, allF);
    const r = inv176.map.get(st);
    const T = "issue-176/oil-investable";
    chk(near(c.nM, r.n), `oil.n ${st}`, T);
    chk(near(c.nE, r.episodes), `oil.nE ${st}`, T);
    chk(near(c.mean, r.mean), `oil.mean ${st}`, T);
    chk(near(c.meanEx, r.meanEx), `oil.meanEx ${st}`, T);
    chk(near(c.vol, r.vol), `oil.vol ${st}`, T);
    chk(near(c.p10, r.p10), `oil.p10 ${st}`, T);
    chk(near(c.epHit, r.epHit), `oil.hit ${st}`, T);
    chk(c.evidence === r.evidence, `oil.evidence ${st}: ${c.evidence} vs ${r.evidence}`, T);
    chk(c.strictZero === (r.zero_candidate === true || r.zero_candidate === "true"), `oil.zeroFlag ${st}`, T);
  }
}
console.log("self-check gate:");
for (const [t, s] of Object.entries(chkByTable)) console.log("  " + t.padEnd(42), "compared", String(s.compared).padStart(4), "mismatches", s.mismatches);
if (mism > 0) { console.error("SELF-CHECK MISMATCHES", mism, mislog.slice(0, 20)); process.exit(1); }

// ---- 5b. frozen full-common-sample window coverage assertion (prereg §10) ----
const FULL_START = "1987-10-01", FULL_END = "2026-08-01";
const fullF = (d) => d >= FULL_START && d <= FULL_END;
const winMonths = macroMonths.filter(fullF);
const panelOut = { window: [FULL_START, FULL_END], months_in_window: winMonths.length, per_sleeve: {}, longtreasury_gap: null };
let panelFail = 0;
if (winMonths.length !== panel174.panels.full.n_months) { console.error("panel month count mismatch", winMonths.length); panelFail++; }
for (const sl of SLEEVES174) {
  const miss = winMonths.filter((d) => { const j = joined.find((x) => x.date === d); return !j || !fin(j[sl]); });
  const have = winMonths.length - miss.length;
  const ref = panel174.panels.full_month_means[sl];
  const meanEx = mean(joined.filter((j) => fullF(j.date) && fin(j[sl])).map((j) => j[sl]));
  panelOut.per_sleeve[sl] = { n: have, n_missing: miss.length, mean: meanEx, ref_n: ref.n, ref_mean: ref.mean, ok: have === ref.n && Math.abs(meanEx - ref.mean) < 1e-12 };
  if (!panelOut.per_sleeve[sl].ok) { console.error("panel sleeve mismatch", sl, have, ref.n, meanEx, ref.mean); panelFail++; }
  if (sl === "longtreasury") panelOut.longtreasury_gap = { n_missing: miss.length, first: miss[0] || "", last: miss[miss.length - 1] || "" };
  else if (miss.length !== 0) { console.error("unexpected missing months outside disclosed long-treasury gap", sl, miss.length); panelFail++; }
}
const ltg = panelOut.longtreasury_gap;
const ltContiguous = ltg && ltg.n_missing === 73 && ltg.first === "1987-10-01" && ltg.last === "1993-10-01";
if (!ltContiguous) { console.error("long-treasury gap does not match the disclosed contiguous 1987-10..1993-10 window", JSON.stringify(ltg)); panelFail++; }
panelOut.pass = panelFail === 0;
if (panelFail) { console.error("PANEL COVERAGE ASSERTION FAILED"); process.exit(1); }
console.log("panel coverage assertion: PASS (", winMonths.length, "months; LT gap", ltg.n_missing, ltg.first, "..", ltg.last, ")");

// ---- 6. frozen policy inputs per cell ----
const ELIG174 = {};
for (const r of ev174.rows) ELIG174[r.sleeve] = r.eligibility;
const HARD_VERDICT = { sp500: "hardened_with_limitation", nasdaq: "unresolved_keep_issue174_semantics", russell: "unresolved_keep_issue174_semantics", oil: "hardened_with_limitation" };
const LIMIT_NOTE = {
  sp500: "S&P TR reconstruction (^GSPC month-ends + Shiller dividends); ends 2023-06",
  nasdaq: "price-only; dividends excluded (~0.96%/yr wedge); official TR only 2003+",
  russell: "price-only; dividends excluded (~1.34%/yr wedge); official TR only 1995+",
  oil: "investable = CL=F excess + TB3MS collateral from 2000-09; spot kept separately",
  cash: "residual; direct T-bill accrual",
  treasury2y: "synthetic 2Y CMT TR",
  treasury10y: "frozen #166 synthetic 10Y TR",
  longtreasury: "synthetic 20Y CMT TR; 73-mo 1987-10..1993-10 gap",
  gold: "Pink Sheet monthly-avg price; pre-1971 fixed parity",
};
function confidence(sl) {
  if (ELIG174[sl] === "eligible_with_limitation") return "limited";
  if (HARD_VERDICT[sl] === "hardened_with_limitation" || HARD_VERDICT[sl] === "unresolved_keep_issue174_semantics") return "limited";
  return "full";
}
function cellInput(state, sleeve) {
  if (sleeve === "sp500") {
    const c = cellStats(state, (j) => j.sp_hard, allF);
    const r = sens176.map.get(state + "|sp500");
    return { ...c, flagA: r.zero_new === true || r.zero_new === "true", flagSource: "#176 affected-state-sensitivity.zero_new", source: "#176 hardened S&P TR" };
  }
  if (sleeve === "oil") {
    const c = cellStats(state, (j) => j.oil_inv, allF);
    const r = inv176.map.get(state);
    return { ...c, flagA: r.zero_candidate === true || r.zero_candidate === "true", flagSource: "#176 oil-investable-state-cells.zero_candidate", source: "#176 investable oil" };
  }
  const ref = ev174.map.get(state + "|" + sleeve);
  const c = cellStats(state, (j) => j[sleeve], allF);
  return { ...c, evidence: ref.evidence, flagA: ref.future_zero_weight_candidate === true || ref.future_zero_weight_candidate === "true", flagSource: "#174 evidence-classification.future_zero_weight_candidate", source: "#174" };
}

// ---- 7. frozen tier / zero / cash mapping ----
const POINTS = { High: 2, Neutral: 1, Low: 0, "0": -1 };
const TIERS = ["0", "Low", "Neutral", "High"];
function baseline(ev, mx) {
  if (ev === "historically_favored") return "High";
  if (ev === "historically_unfavorable") return "Low";
  if (ev === "mixed") return (fin(mx) && mx >= 0) ? "Neutral" : "Low";
  if (ev === "insufficient_sample") return "Neutral";
  throw new Error("unknown evidence " + ev);
}
function ruleB(inp) {
  if (inp.evidence !== "historically_unfavorable") return false;
  if (!(fin(inp.meanEx) && inp.meanEx < 0)) return false;
  if (!(fin(inp.epHit) && inp.epHit <= 0.40)) return false;
  if (!inp.tailHit) return false;
  return fin(inp.exWorst) && inp.exWorst < 0;
}
function tailList(inp) {
  const t = [];
  if (fin(inp.p10ex) && inp.p10ex <= -0.04) t.push("p10_ex<=-0.04");
  if (fin(inp.worstEp) && inp.worstEp <= -0.15) t.push("worst_ep<=-0.15");
  if (fin(inp.pMat) && inp.pMat >= 0.10) t.push("p_material_monthly>=0.10");
  return t;
}
function zeroReason(path, inp) {
  if (path === "A") return "A:frozen_zero_candidate[" + inp.flagSource + "]=true";
  if (path === "B") return "B:evidence=historically_unfavorable;meanEx<0;epHit<=0.40;severe_tail[" + tailList(inp).join("|") + "];exWorstMeanEx<0";
  return "";
}
function deriveCell(state, sleeve) {
  const inp = cellInput(state, sleeve);
  const base = baseline(inp.evidence, inp.meanEx);
  const rb = ruleB(inp);
  let tier = base, zeroPath = "";
  if (base === "Low" && (inp.flagA || rb)) { tier = "0"; zeroPath = inp.flagA ? "A" : "B"; }
  return { inp, base, ruleB: rb, tier, zeroPath, reason: zeroReason(zeroPath, inp) };
}

const matrix = [];
const tierIndex = {};
for (const st of STATES) {
  const tiers = {};
  for (const sl of NONCASH) {
    const d = deriveCell(st, sl);
    const inp = d.inp;
    tierIndex[st + "|" + sl] = d.tier;
    matrix.push({
      state: st, sleeve: sl, exposure: d.tier, confidence: confidence(sl),
      evidence: inp.evidence, mean_ex: inp.meanEx, ep_hit: inp.epHit, era_label: inp.eraLabel,
      severe_tail: inp.tailHit, p10_ex: inp.p10ex, worst_ep: inp.worstEp, p_material: inp.pMat,
      p_under: inp.pUnder, worst_monthly: inp.worstM, ex_worst_mean_ex: inp.exWorst,
      future_zero_candidate: inp.flagA, zero_rule_path: d.zeroPath, zero_rule_reason: d.reason,
      low_confidence: inp.evidence === "insufficient_sample",
      source: inp.source, limitation: LIMIT_NOTE[sl], n_months: inp.nM, n_episodes: inp.nE,
      mean: inp.mean, vol: inp.vol, p10: inp.p10, policy_sensitive: false,
    });
    tiers[sl] = d.tier;
  }
  const score = NONCASH.reduce((s, sl) => s + POINTS[tiers[sl]], 0);
  const bias = score <= 3 ? "high" : score <= 8 ? "neutral" : "low";
  matrix.push({ state: st, sleeve: "cash", exposure: "residual", confidence: "full", evidence: "NA", mean_ex: "", ep_hit: "", era_label: "NA", severe_tail: false, p10_ex: "", worst_ep: "", p_material: "", p_under: "", worst_monthly: "", ex_worst_mean_ex: "", future_zero_candidate: false, zero_rule_path: "", zero_rule_reason: "", low_confidence: false, source: "#174 Cash residual", limitation: LIMIT_NOTE.cash, n_months: "", n_episodes: "", mean: "", vol: "", p10: "", policy_sensitive: false, opportunity_score: score, cash_bias: bias, cash_role: "residual" });
}

// ---- 8. consistency checks (machine-readable) ----
const checks = [];
function check(id, description, pass, detail) {
  checks.push({ id, description, pass: !!pass, detail: detail === undefined ? "" : detail });
  return !!pass;
}
const tierRows = matrix.filter((r) => r.sleeve !== "cash");
check(1, "no historically_unfavorable cell receives High", tierRows.every((r) => !(r.evidence === "historically_unfavorable" && r.exposure === "High")), "9x8 cells scanned");
check(2, "every 0 exposure satisfies the frozen zero rule (A or B)", tierRows.filter((r) => r.exposure === "0").every((r) => { const d = deriveCell(r.state, r.sleeve); return (d.inp.flagA || d.ruleB) && r.zero_rule_path !== ""; }), "3 zero cells re-derived");
check(3, "insufficient_sample cells are never High", tierRows.every((r) => !(r.evidence === "insufficient_sample" && r.exposure === "High")), "low-confidence cells scanned");
check(4, "insufficient_sample cells are never 0", tierRows.every((r) => !(r.evidence === "insufficient_sample" && r.exposure === "0")), "low-confidence cells scanned");
check(5, "every macro state contains all 9 sleeves", STATES.every((st) => matrix.filter((r) => r.state === st).length === 9));
check(6, "every non-cash sleeve carries exactly one valid tier per state", tierRows.every((r) => TIERS.includes(r.exposure)) && STATES.every((st) => NONCASH.every((sl) => tierRows.filter((r) => r.state === st && r.sleeve === sl).length === 1)));
check(7, "Cash is residual only and never classified against itself", matrix.filter((r) => r.sleeve === "cash").every((r) => r.exposure === "residual" && r.cash_role === "residual" && r.evidence === "NA"));
check(8, "#176 hardened S&P 500 evidence supersedes the #174 broad-market proxy", tierRows.filter((r) => r.sleeve === "sp500").every((r) => r.source === "#176 hardened S&P TR" && r.evidence === sens176.map.get(r.state + "|sp500").ev_new), "all 9 states");
check(9, "#176 investable-oil evidence supersedes WTI spot for allocation logic", tierRows.filter((r) => r.sleeve === "oil").every((r) => r.source === "#176 investable oil" && r.evidence === inv176.map.get(r.state).evidence), "all 9 states");
check(10, "Nasdaq price-only source limitation remains explicit", tierRows.filter((r) => r.sleeve === "nasdaq").every((r) => r.confidence === "limited" && /price-only/.test(r.limitation)), "all 9 states");
check(11, "Russell price-only source limitation remains explicit", tierRows.filter((r) => r.sleeve === "russell").every((r) => r.confidence === "limited" && /price-only/.test(r.limitation)), "all 9 states");
const matrixKeys = Object.keys(tierRows[0] || {});
const inputPaths = Object.keys(FROZEN);
check(12, "no trajectory input enters the baseline", !matrixKeys.some((k) => /traj/i.test(k)) && !inputPaths.some((p) => /traj/i.test(p)) && tierRows.every((r) => !/traj/i.test(r.source)), "matrix keys + frozen input paths + sources scanned");
check(13, "no V6.6 input enters the baseline", !matrixKeys.some((k) => /v6/i.test(k)) && !inputPaths.some((p) => /v6/i.test(p)) && tierRows.every((r) => !/v6/i.test(r.source)), "matrix keys + frozen input paths + sources scanned");
check(14, "no manual overrides: every cell re-derives from the frozen rules", tierRows.every((r) => { const d = deriveCell(r.state, r.sleeve); return d.tier === r.exposure && d.base === baseline(r.evidence, r.mean_ex); }));
check(15, "no percentages / weights / optimiser output is produced", tierRows.every((r) => TIERS.includes(r.exposure)) && !Object.keys(matrix[0]).some((k) => /weight|percent|pct_weight|alloc/i.test(k)));
const errs = checks.filter((c) => !c.pass);
console.log("consistency checks:", checks.length, "failures:", errs.length, errs.map((c) => c.id + ":" + c.description));
if (errs.length) process.exit(1);

// ---- 9. policy sensitivity: full-common-sample recompute (frozen formulas) ----
const sensRows = [];
for (const st of STATES) {
  for (const sl of NONCASH) {
    const get = sl === "sp500" ? ((j) => j.sp_hard) : sl === "oil" ? ((j) => j.oil_inv) : ((j) => j[sl]);
    const c = cellStats(st, get, fullF);
    const src = sl === "sp500" ? sens176.map.get(st + "|sp500") : sl === "oil" ? inv176.map.get(st) : ev174.map.get(st + "|" + sl);
    const flagA = sl === "sp500" ? (src.zero_new === true || src.zero_new === "true") : sl === "oil" ? (src.zero_candidate === true || src.zero_candidate === "true") : (src.future_zero_weight_candidate === true || src.future_zero_weight_candidate === "true");
    const base = baseline(c.evidence, c.meanEx);
    let tier = base, path = "";
    if (base === "Low" && (flagA || ruleB(c))) { tier = "0"; path = flagA ? "A" : "B"; }
    if (c.evidence === "insufficient_sample") tier = "Neutral";
    const prim = tierIndex[st + "|" + sl];
    const changed = prim !== tier;
    if (changed) { const row = matrix.find((x) => x.state === st && x.sleeve === sl); row.policy_sensitive = true; }
    sensRows.push({ state: st, sleeve: sl, primary: prim, implied: tier, evidence_full: c.evidence, n_full: c.nM, zero_rule_path_full: path, changed, policy_sensitive: changed });
  }
}
const nChanged = sensRows.filter((r) => r.changed).length;
const changedCells = sensRows.filter((r) => r.changed).map((r) => r.state + "|" + r.sleeve + ":" + r.primary + "->" + r.implied);
console.log("sensitivity changed cells:", nChanged, "of", sensRows.length);
console.log("  ", changedCells.join(" "));

// ---- 10. write artifacts ----
function csv(rows, cols) {
  const f = (v) => (typeof v === "number" ? (isFinite(v) ? String(v) : "") : (v ?? ""));
  return cols.join(",") + "\n" + rows.map((r) => cols.map((c) => f(r[c])).join(",")).join("\n") + "\n";
}
const mcols = ["state", "sleeve", "exposure", "confidence", "evidence", "mean_ex", "ep_hit", "era_label", "severe_tail", "p10_ex", "worst_ep", "p_material", "p_under", "worst_monthly", "ex_worst_mean_ex", "future_zero_candidate", "zero_rule_path", "zero_rule_reason", "low_confidence", "policy_sensitive", "source", "limitation", "n_months", "n_episodes"];
fs.writeFileSync(path.join(GEN, "policy-matrix.csv"), csv(tierRows, mcols));
fs.writeFileSync(path.join(GEN, "cash-bias.csv"),
  "state,opportunity_score,cash_bias,cash_role\n" + STATES.map((st) => { const r = matrix.find((x) => x.state === st && x.sleeve === "cash"); return [st, r.opportunity_score, r.cash_bias, "residual"].join(","); }).join("\n") + "\n");
const zeroRows = tierRows.filter((r) => r.exposure === "0");
fs.writeFileSync(path.join(GEN, "zero-audit.csv"),
  "state,sleeve,exposure,evidence,mean_ex,ep_hit,p10_ex,worst_ep,p_material,ex_worst_mean_ex,severe_tail,flag_a,zero_rule_path,zero_rule_reason\n" +
  zeroRows.map((r) => [r.state, r.sleeve, r.exposure, r.evidence, r.mean_ex, r.ep_hit, r.p10_ex, r.worst_ep, r.p_material, r.ex_worst_mean_ex, r.severe_tail, r.future_zero_candidate, r.zero_rule_path, r.zero_rule_reason].join(",")).join("\n") + "\n");
fs.writeFileSync(path.join(GEN, "confidence.csv"),
  "state,sleeve,exposure,confidence,eligibility,hardening_verdict,limitation,low_confidence,policy_sensitive\n" +
  tierRows.map((r) => [r.state, r.sleeve, r.exposure, r.confidence, ELIG174[r.sleeve], HARD_VERDICT[r.sleeve] || "", '"' + r.limitation + '"', r.low_confidence, r.policy_sensitive].join(",")).join("\n") + "\n");
fs.writeFileSync(path.join(GEN, "sensitivity-common-sample.csv"),
  "state,sleeve,primary,implied,evidence_full,n_full,zero_rule_path_full,changed,policy_sensitive\n" +
  sensRows.map((r) => [r.state, r.sleeve, r.primary, r.implied, r.evidence_full, r.n_full, r.zero_rule_path_full, r.changed, r.policy_sensitive].join(",")).join("\n") + "\n");

// state cards
const DESC = {
  "G_Low/I_Low": "Deflationary bust — contracting activity with falling prices.",
  "G_Low/I_Neutral": "Disinflationary slowdown — weak growth, stable prices.",
  "G_Low/I_High": "Stagflationary slump — weak growth with high inflation.",
  "G_Neutral/I_Low": "Healthy disinflation — steady growth, low inflation.",
  "G_Neutral/I_Neutral": "Balanced expansion — steady growth, neutral inflation.",
  "G_Neutral/I_High": "Late-cycle heat — steady growth with elevated inflation.",
  "G_High/I_Low": "Productivity boom — strong growth, low inflation.",
  "G_High/I_Neutral": "Broad boom — strong growth, neutral inflation.",
  "G_High/I_High": "Overheating — strong growth with high inflation.",
};
let cards = "# Issue #177 — State allocation cards (deterministic; see policy-matrix.csv)\n\n";
cards += "Tiers are qualitative exposure tiers (0 / Low / Neutral / High), never portfolio weights.\n";
cards += "`(limited)` = documented source limitation; `(policy-sensitive)` = tier changes under the full-common-sample panel.\n\n";
for (const st of STATES) {
  const rows = tierRows.filter((x) => x.state === st);
  const cash = matrix.find((x) => x.state === st && x.sleeve === "cash");
  const tag = (x) => x.sleeve + (x.confidence === "limited" ? " (limited)" : "") + (x.policy_sensitive ? " (policy-sensitive)" : "");
  const grp = (t) => rows.filter((x) => x.exposure === t).map(tag).join(", ") || "—";
  const caveats = rows.filter((x) => x.confidence === "limited" || x.low_confidence).map((x) => x.sleeve + ": " + x.limitation + (x.low_confidence ? " [low confidence: insufficient sample]" : "")).join("; ");
  const sensitive = rows.filter((x) => x.policy_sensitive).map((x) => x.sleeve).join(", ");
  cards += "## " + st + " — " + DESC[st] + "\n\n"
    + "- High: " + grp("High") + "\n- Neutral: " + grp("Neutral") + "\n- Low: " + grp("Low") + "\n- Zero: " + grp("0") + "\n"
    + "- Cash: residual, bias " + cash.cash_bias + " (opportunity score " + cash.opportunity_score + ")\n"
    + "- Policy-sensitive sleeves: " + (sensitive || "none") + "\n"
    + "- Caveats: " + (caveats || "none") + "\n\n";
}
fs.writeFileSync(path.join(GEN, "state-cards.md"), cards);

// summary
const counts = {};
for (const r of tierRows) counts[r.exposure] = (counts[r.exposure] || 0) + 1;
const anyLimited = tierRows.some((r) => r.confidence === "limited");
const anyLowConf = tierRows.some((r) => r.low_confidence);
const verdict = (anyLimited || anyLowConf)
  ? "state_allocation_policy_candidate_complete_with_limitations"
  : "state_allocation_policy_candidate_complete";
const artifactHashes = {};
for (const f of ["policy-matrix.csv", "cash-bias.csv", "zero-audit.csv", "confidence.csv", "sensitivity-common-sample.csv", "state-cards.md"]) {
  artifactHashes[f] = sha256(fs.readFileSync(path.join(GEN, f)));
}
const summary = {
  issue: 177,
  branch: "research/issue-177-state-allocation-policy",
  base_head: "5d596047e1da5531f43190bad761a79a8b3ac342",
  prereg_commit: "8fb864ef1a7925235153679f2a2e83220f4f6d18",
  verdict,
  verdict_basis: { any_limited_confidence: anyLimited, any_low_confidence: anyLowConf },
  self_check_gate: { mismatches: mism, tables: chkByTable },
  panel_coverage_assertion: panelOut,
  tier_counts: counts,
  total_non_cash_cells: tierRows.length,
  zero_cells: zeroRows.map((r) => ({ state: r.state, sleeve: r.sleeve, path: r.zero_rule_path, reason: r.zero_rule_reason })),
  cash_bias: STATES.map((st) => { const r = matrix.find((x) => x.state === st && x.sleeve === "cash"); return { state: st, score: r.opportunity_score, bias: r.cash_bias }; }),
  confidence_counts: tierRows.reduce((o, r) => { o[r.confidence] = (o[r.confidence] || 0) + 1; return o; }, {}),
  limited_confidence_cells: tierRows.filter((r) => r.confidence === "limited").map((r) => r.state + "|" + r.sleeve),
  low_confidence_cells: tierRows.filter((r) => r.low_confidence).map((r) => r.state + "|" + r.sleeve),
  policy_sensitive_cells: sensRows.filter((r) => r.changed).map((r) => ({ state: r.state, sleeve: r.sleeve, primary: r.primary, common_sample: r.implied, evidence_full: r.evidence_full })),
  sensitivity: { compared_cells: sensRows.length, changed_cells: nChanged, unchanged_cells: sensRows.length - nChanged },
  checks,
  artifact_hashes: artifactHashes,
  inputs: INPUT_SHAS,
  optimizer_used: false,
  percentages_assigned: false,
  trajectory_used: false,
  v6_6_used: false,
  manual_overrides: false,
  outcome_data_loaded: true,
  production_authorized: false,
};
fs.writeFileSync(path.join(GEN, "summary.json"), JSON.stringify(summary, null, 2));
console.log("tier counts:", JSON.stringify(counts));
console.log("verdict:", verdict);
console.log("DONE build");
