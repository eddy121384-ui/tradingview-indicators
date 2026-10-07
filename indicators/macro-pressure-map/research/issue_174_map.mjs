// Issue #174 — Phase B macro x asset outcome map (Node executor).
// Frozen methodology: issue-174-nine-sleeve-map-prereg.md
// Verifies frozen hashes, joins macro x backbone, computes month/episode/era/
// danger/classification/zero-candidate + core/full panels + summary.json.
// No weight optimization. No Pine change.
import fs from "node:fs";
import path from "node:path";
import crypto from "node:crypto";
import { execSync } from "node:child_process";

const ROOT = process.cwd();
const RES = path.join(ROOT, "indicators/macro-pressure-map/research");
const GEN174 = path.join(RES, "generated/issue-174");
const sha256 = (b) => crypto.createHash("sha256").update(b).digest("hex");
const gitBlob = (p) => execSync("git show HEAD:" + p, { maxBuffer: 100 * 1024 * 1024 });

// ---- Verify frozen inputs ----
const macroBlob = gitBlob("indicators/macro-pressure-map/research/generated/issue-160/deep-history-v01-monthly.csv");
const macroSha = sha256(macroBlob);
if (macroSha !== "42516418ec8d1ce981d1b4bc05e2ae86809d6acbf5de63dccbad515db507dcfc") {
  console.error("macro blob mismatch", macroSha);
  process.exit(1);
}
const eqBlobSha = sha256(gitBlob("indicators/macro-pressure-map/research/generated/issue-166/equity-monthly-total-returns.csv"));
const t10BlobSha = sha256(gitBlob("indicators/macro-pressure-map/research/generated/issue-166/treasury-monthly-total-returns.csv"));
console.log("verified macro", macroSha, "eq", eqBlobSha, "t10", t10BlobSha);

// ---- Load macro ----
function loadMacro() {
  const txt = fs.readFileSync(path.join(RES, "generated/issue-160/deep-history-v01-monthly.csv"), "utf8");
  const lines = txt.trim().split("\n");
  const idx = lines[0].split(",");
  const gi = idx.indexOf("growth_dh"), ii = idx.indexOf("inflation_dh");
  const out = new Map();
  for (let k = 1; k < lines.length; k++) {
    const c = lines[k].split(",");
    const d = c[0];
    const g = parseFloat(c[gi]), inf = parseFloat(c[ii]);
    if (!isFinite(g) || !isFinite(inf)) continue;
    out.set(d, { g, i: inf });
  }
  return out;
}
function band(s) {
  if (s < -10) return "Low";
  if (s > 10) return "High";
  return "Neutral";
}
function stateOf(g, i) {
  return "G_" + band(g) + "/I_" + band(i);
}
function eraOf(mo) {
  if (mo >= "1966-03-01" && mo <= "1979-12-01") return "E1_pre_volcker";
  if (mo >= "1980-01-01" && mo <= "2007-12-01") return "E2_great_moderation";
  if (mo >= "2008-01-01" && mo <= "2019-12-01") return "E3_post_gfc_qe";
  if (mo >= "2020-01-01" && mo <= "2026-08-01") return "E4_post_2020";
  return "OUT";
}

// ---- Load backbone ----
function loadBackbone() {
  const txt = fs.readFileSync(path.join(GEN174, "nine-sleeve-monthly-returns.csv"), "utf8");
  const lines = txt.trim().split("\n");
  const h = lines[0].split(",");
  const rows = [];
  for (let k = 1; k < lines.length; k++) {
    const c = lines[k].split(",");
    const r = { date: c[0] };
    for (let j = 1; j < h.length; j++) r[h[j]] = c[j] === "" ? NaN : parseFloat(c[j]);
    rows.push(r);
  }
  return { header: h, rows };
}

const SLEEVES = ["sp500", "nasdaq", "russell", "cash", "treasury2y", "treasury10y", "longtreasury", "gold", "oil"];
const STATES = [];
for (const g of ["Low", "Neutral", "High"]) for (const inf of ["Low", "Neutral", "High"]) STATES.push("G_" + g + "/I_" + inf);

// ---- Stats helpers (frozen) ----
const fin = (x) => typeof x === "number" && isFinite(x);
function mean(a) { const v = a.filter(fin); return v.length ? v.reduce((s, x) => s + x, 0) / v.length : NaN; }
function median(a) {
  const v = a.filter(fin).sort((x, y) => x - y);
  if (!v.length) return NaN;
  const n = v.length, m = Math.floor(n / 2);
  return n % 2 ? v[m] : (v[m - 1] + v[m]) / 2;
}
function bsd(a) {
  const v = a.filter(fin);
  if (!v.length) return NaN;
  const m = v.reduce((s, x) => s + x, 0) / v.length;
  return Math.sqrt(v.reduce((s, x) => s + (x - m) ** 2, 0) / v.length);
}
function downside(a) {
  const v = a.filter(fin);
  if (!v.length) return NaN;
  return Math.sqrt(v.reduce((s, x) => s + Math.min(x, 0) ** 2, 0) / v.length);
}
function pct(a, q) {
  const v = a.filter(fin).sort((x, y) => x - y);
  if (!v.length) return NaN;
  if (v.length === 1) return v[0];
  const pos = q * (v.length - 1), lo = Math.floor(pos), hi = Math.ceil(pos);
  if (lo === hi) return v[lo];
  return v[lo] * (hi - pos) + v[hi] * (pos - lo);
}
function compound(rs) {
  let p = 1;
  for (const r of rs) { if (!fin(r)) return NaN; p *= 1 + r; }
  return p - 1;
}
function calNext(mo) {
  let y = +mo.slice(0, 4), m = +mo.slice(5, 7) + 1;
  if (m > 12) { m = 1; y++; }
  return String(y).padStart(4, "0") + "-" + String(m).padStart(2, "0") + "-01";
}

const macro = loadMacro();
const { rows: bro } = loadBackbone();
// join: macro-valid months with backbone
const joined = [];
for (const r of bro) {
  const m = macro.get(r.date);
  if (!m) continue;
  joined.push({ date: r.date, g: m.g, i: m.i, state: stateOf(m.g, m.i), era: eraOf(r.date), ...r });
}
joined.sort((a, b) => (a.date < b.date ? -1 : 1));
console.log("joined months", joined.length);

// state episodes (macro-only, all macro-valid months 1966-03..2026-08 incl holes excluded)
const macroMonths = [...macro.keys()].filter((d) => d >= "1966-03-01" && d <= "2026-08-01").sort();
function buildStateEpisodes(months, states) {
  const eps = [];
  if (!months.length) return eps;
  let s = 0;
  for (let k = 1; k < months.length; k++) {
    if (states[k] === states[s] && calNext(months[k - 1]) === months[k]) continue;
    eps.push({ start: months[s], end: months[k - 1], state: states[s], sIdx: s, eIdx: k - 1 });
    s = k;
  }
  eps.push({ start: months[s], end: months[months.length - 1], state: states[s], sIdx: s, eIdx: months.length - 1 });
  return eps;
}
const macroStates = macroMonths.map((d) => stateOf(macro.get(d).g, macro.get(d).i));
const stateEpisodes = buildStateEpisodes(macroMonths, macroStates);

// state month counts
const stateCounts = STATES.map((st) => {
  const ms = macroMonths.filter((_, k) => macroStates[k] === st);
  const eps = stateEpisodes.filter((e) => e.state === st);
  const durs = eps.map((e) => e.eIdx - e.sIdx + 1);
  return {
    state: st, months: ms.length, episodes: eps.length,
    first: ms[0] || "", last: ms[ms.length - 1] || "",
    dur_min: durs.length ? Math.min(...durs) : 0,
    dur_median: durs.length ? median(durs) : 0,
    dur_max: durs.length ? Math.max(...durs) : 0,
  };
});
fs.writeFileSync(path.join(GEN174, "state-month-counts.csv"),
  "state,months,episodes,first,last,dur_min,dur_median,dur_max\n" +
  stateCounts.map((r) => [r.state, r.months, r.episodes, r.first, r.last, r.dur_min, r.dur_median, r.dur_max].join(",")).join("\n") + "\n");

// core outcome computer (frozen §6-10), filtered by date predicate
function computeOutcomes(filterFn) {
  const monthRows = [], episodeRows = [], eraRows = [], dangerRows = [], classRows = [];
  for (const st of STATES) {
    for (const sl of SLEEVES) {
      const obs = joined.filter((j) => j.state === st && filterFn(j.date) && fin(j[sl]) && fin(j.cash));
      // cash sleeve vs itself: excess 0
      const rs = obs.map((o) => o[sl]);
      const rc = obs.map((o) => o.cash);
      const ex = obs.map((o) => o[sl] - o.cash);
      const nM = rs.length;
      const comp = compound(rs), compC = compound(rc);
      const gex = fin(comp) && fin(compC) ? (1 + comp) / (1 + compC) - 1 : NaN;
      const ann = nM >= 12 && fin(comp) ? Math.pow(1 + comp, 12 / nM) - 1 : NaN;
      monthRows.push({
        state: st, sleeve: sl, n_months: nM,
        mean: mean(rs), median: median(rs), compounded: comp, annualized: ann,
        vol_ann: fin(bsd(rs)) ? bsd(rs) * Math.sqrt(12) : NaN,
        downside_ann: fin(downside(rs)) ? downside(rs) * Math.sqrt(12) : NaN,
        pos_frac: nM ? rs.filter((r) => r > 0).length / nM : NaN,
        cash_ex_mean: mean(ex), cash_ex_median: median(ex),
        cash_ex_comp: gex, cash_ex_pos_frac: nM ? ex.filter((e) => e > 0).length / nM : NaN,
        worst: nM ? Math.min(...rs.filter(fin)) : NaN, p10: pct(rs, 0.10), p10_ex: pct(ex, 0.10),
      });
      // episodes: slice stateEpisodes, keep months with sleeve+cash
      const eps = stateEpisodes.filter((e) => e.state === st);
      const epComps = [], epEx = [], epDurs = [];
      let worstEp = null, bestEp = null;
      for (const e of eps) {
        const em = [];
        let d = e.start;
        while (true) {
          const j = joined.find((x) => x.date === d);
          if (j && filterFn(d) && fin(j[sl]) && fin(j.cash)) em.push(j);
          if (d === e.end) break;
          d = calNext(d);
        }
        if (!em.length) continue;
        const Rs = compound(em.map((x) => x[sl])), Rc = compound(em.map((x) => x.cash));
        const Re = fin(Rs) && fin(Rc) ? (1 + Rs) / (1 + Rc) - 1 : NaN;
        epComps.push({ Rs, Re, dur: em.length, start: e.start, end: e.end });
        epDurs.push(em.length);
        if (!worstEp || Rs < worstEp.Rs) worstEp = { Rs, start: e.start, end: e.end, dur: em.length };
        if (!bestEp || Rs > bestEp.Rs) bestEp = { Rs, start: e.start, end: e.end, dur: em.length };
      }
      const RsAll = epComps.map((e) => e.Rs), ReAll = epComps.map((e) => e.Re);
      const posEp = RsAll.filter(fin);
      const sumPos = posEp.filter((r) => r > 0).reduce((s, x) => s + x, 0);
      const conc = sumPos > 0 && bestEp && fin(bestEp.Rs) && bestEp.Rs > 0 ? bestEp.Rs / sumPos : NaN;
      // max state-associated drawdown: min over episodes of min cumulative from start
      let maxDD = NaN;
      for (const e of eps) {
        let cum = 1, mn = 0;
        let d = e.start, any = false;
        while (true) {
          const j = joined.find((x) => x.date === d);
          if (j && filterFn(d) && fin(j[sl])) { cum *= 1 + j[sl]; mn = Math.min(mn, cum - 1); any = true; }
          if (d === e.end) break;
          d = calNext(d);
        }
        if (any && (!fin(maxDD) || mn < maxDD)) maxDD = mn;
      }
      episodeRows.push({
        state: st, sleeve: sl, n_episodes: epComps.length,
        ep_mean: mean(RsAll), ep_median: median(RsAll),
        ep_pos_frac: RsAll.length ? RsAll.filter((r) => r > 0).length / RsAll.length : NaN,
        ep_ex_mean: mean(ReAll), ep_ex_median: median(ReAll),
        ep_ex_pos_frac: ReAll.length ? ReAll.filter((r) => r > 0).length / ReAll.length : NaN,
        worst_ep: worstEp ? worstEp.Rs : NaN, worst_ep_start: worstEp ? worstEp.start : "",
        worst_ep_end: worstEp ? worstEp.end : "",
        best_ep: bestEp ? bestEp.Rs : NaN, best_ep_start: bestEp ? bestEp.start : "",
        best_ep_end: bestEp ? bestEp.end : "",
        dur_min: epDurs.length ? Math.min(...epDurs) : 0,
        dur_median: epDurs.length ? median(epDurs) : 0,
        dur_mean: epDurs.length ? mean(epDurs) : 0,
        dur_max: epDurs.length ? Math.max(...epDurs) : 0,
        concentration: conc, max_state_dd: maxDD,
      });
      // era stability: mean_ex per era with >=12 months
      const eraMeans = {};
      for (const er of ["E1_pre_volcker", "E2_great_moderation", "E3_post_gfc_qe", "E4_post_2020"]) {
        const eo = obs.filter((o) => o.era === er);
        eraMeans[er] = eo.length >= 12 ? mean(eo.map((o) => o[sl] - o.cash)) : NaN;
      }
      const evalEras = Object.values(eraMeans).filter(fin);
      const posE = Object.values(eraMeans).filter((v) => fin(v) && v > 0).length;
      const negE = Object.values(eraMeans).filter((v) => fin(v) && v < 0).length;
      const nEval = evalEras.length;
      let eraLabel = "insufficient_era";
      if (nEval >= 2) {
        if (posE === nEval) eraLabel = "persistent_positive";
        else if (negE === nEval) eraLabel = "persistent_negative";
        else if ((posE >= 3 || negE >= 3) && nEval >= 3) eraLabel = posE >= 3 ? "broadly_positive" : "broadly_negative";
        else eraLabel = "mixed";
      }
      // for classification need persistent flags with >=12m rule and >=3 eras
      const persPos = nEval >= 3 && negE === 0 && posE >= 3;
      const persNeg = nEval >= 3 && posE === 0 && negE >= 3;
      eraRows.push({ state: st, sleeve: sl, n_months: nM, n_episodes: epComps.length, ...Object.fromEntries(Object.entries(eraMeans).map(([k, v]) => ["era_" + k, v])), era_label: eraLabel, n_eval_eras: nEval });
      // danger
      const pUnder = nM ? ex.filter((e) => e < 0).length / nM : NaN;
      const pMat = nM ? ex.filter((e) => e < MATERIAL(e)).length / nM : NaN;
      function MATERIAL(e) { return -0.02; }
      const pEpMat = ReAll.length ? ReAll.filter((r) => fin(r) && r < -0.05).length / ReAll.length : NaN;
      dangerRows.push({
        state: st, sleeve: sl, n_months: nM, worst_monthly: nM ? Math.min(...rs.filter(fin)) : NaN,
        worst_episode: worstEp ? worstEp.Rs : NaN, max_state_dd: maxDD,
        p10: pct(rs, 0.10), p10_ex: pct(ex, 0.10),
        p_underperform: pUnder, p_material_monthly: pMat, p_material_episode: pEpMat,
      });
      // classification (frozen §9)
      const mr = monthRows[monthRows.length - 1], er2 = episodeRows[episodeRows.length - 1], dr = dangerRows[dangerRows.length - 1];
      let evidence = "mixed";
      if (nM < 24 || epComps.length < 4) evidence = "insufficient_sample";
      else if (fin(mr.cash_ex_mean) && mr.cash_ex_mean > 0.001 && fin(mr.cash_ex_pos_frac) && mr.cash_ex_pos_frac >= 0.55 && fin(er2.ep_ex_pos_frac) && er2.ep_ex_pos_frac >= 0.60 && fin(mr.p10_ex) && mr.p10_ex >= -0.04 && fin(mr.worst) && mr.worst > -0.20 && !persNeg) evidence = "historically_favored";
      else if (fin(mr.cash_ex_mean) && mr.cash_ex_mean < -0.0005 && ((fin(mr.cash_ex_pos_frac) && mr.cash_ex_pos_frac <= 0.45) || (fin(er2.ep_ex_pos_frac) && er2.ep_ex_pos_frac <= 0.40)) && ((fin(mr.p10_ex) && mr.p10_ex <= -0.03) || (fin(mr.worst) && mr.worst <= -0.10) || (fin(dr.p_underperform) && dr.p_underperform >= 0.60)) && !persPos) evidence = "historically_unfavorable";
      // zero candidate (frozen §10)
      const elig = { sp500: "eligible_primary", nasdaq: "eligible_with_limitation", russell: "eligible_with_limitation", cash: "eligible_primary", treasury2y: "eligible_primary", treasury10y: "eligible_primary", longtreasury: "eligible_primary", gold: "eligible_primary", oil: "eligible_with_limitation" }[sl];
      // ex-worst mean: drop worst episode months
      let exWorst = NaN;
      if (worstEp) {
        const keep = obs.filter((o) => !(o.date >= worstEp.start && o.date <= worstEp.end));
        exWorst = keep.length ? mean(keep.map((o) => o[sl] - o.cash)) : NaN;
      }
      const tailHit = (fin(mr.p10_ex) && mr.p10_ex <= -0.04) || (fin(er2.worst_ep) && er2.worst_ep <= -0.15) || (fin(dr.p_material_monthly) && dr.p_material_monthly >= 0.10);
      const zero = (elig === "eligible_primary" || elig === "eligible_with_limitation") && evidence === "historically_unfavorable" && nM >= 60 && epComps.length >= 6 && fin(er2.ep_ex_pos_frac) && er2.ep_ex_pos_frac <= 0.40 && fin(mr.cash_ex_mean) && mr.cash_ex_mean < 0 && tailHit && !persPos && fin(exWorst) && exWorst < 0;
      classRows.push({
        state: st, sleeve: sl, eligibility: elig, n_months: nM, n_episodes: epComps.length,
        mean_ex: mr.cash_ex_mean, pos_m_frac: mr.cash_ex_pos_frac, ep_hit: er2.ep_ex_pos_frac,
        p10_ex: mr.p10_ex, worst_m: mr.worst, p_under: dr.p_underperform,
        persistent_positive: persPos, persistent_negative: persNeg,
        era_label: eraLabel, evidence, future_zero_weight_candidate: zero,
        ex_worst_mean_ex: exWorst,
      });
    }
  }
  return { monthRows, episodeRows, eraRows, dangerRows, classRows };
}

const allF = () => true;
const coreF = (d) => d >= "1976-07-01";
const fullF = (d) => d >= "1987-10-01";
const R_all = computeOutcomes(allF);
const R_core = computeOutcomes(coreF);
const R_full = computeOutcomes(fullF);

function csv(rows, cols) {
  const f = (v) => (typeof v === "number" ? (isFinite(v) ? String(v) : "") : (v ?? ""));
  return cols.join(",") + "\n" + rows.map((r) => cols.map((c) => f(r[c])).join(",")).join("\n") + "\n";
}
const monthCols = ["state", "sleeve", "n_months", "mean", "median", "compounded", "annualized", "vol_ann", "downside_ann", "pos_frac", "cash_ex_mean", "cash_ex_median", "cash_ex_comp", "cash_ex_pos_frac", "worst", "p10", "p10_ex"];
const epCols = ["state", "sleeve", "n_episodes", "ep_mean", "ep_median", "ep_pos_frac", "ep_ex_mean", "ep_ex_median", "ep_ex_pos_frac", "worst_ep", "worst_ep_start", "worst_ep_end", "best_ep", "best_ep_start", "best_ep_end", "dur_min", "dur_median", "dur_mean", "dur_max", "concentration", "max_state_dd"];
const eraCols = ["state", "sleeve", "n_months", "n_episodes", "era_E1_pre_volcker", "era_E2_great_moderation", "era_E3_post_gfc_qe", "era_E4_post_2020", "era_label", "n_eval_eras"];
const dangerCols = ["state", "sleeve", "n_months", "worst_monthly", "worst_episode", "max_state_dd", "p10", "p10_ex", "p_underperform", "p_material_monthly", "p_material_episode"];
const classCols = ["state", "sleeve", "eligibility", "n_months", "n_episodes", "mean_ex", "pos_m_frac", "ep_hit", "p10_ex", "worst_m", "p_under", "persistent_positive", "persistent_negative", "era_label", "evidence", "future_zero_weight_candidate", "ex_worst_mean_ex"];

fs.writeFileSync(path.join(GEN174, "month-weighted-outcomes.csv"), csv(R_all.monthRows, monthCols));
fs.writeFileSync(path.join(GEN174, "episode-weighted-outcomes.csv"), csv(R_all.episodeRows, epCols));
fs.writeFileSync(path.join(GEN174, "era-stability.csv"), csv(R_all.eraRows, eraCols));
fs.writeFileSync(path.join(GEN174, "downside-danger.csv"), csv(R_all.dangerRows, dangerCols));
fs.writeFileSync(path.join(GEN174, "evidence-classification.csv"), csv(R_all.classRows, classCols));
fs.writeFileSync(path.join(GEN174, "future-zero-candidates.csv"),
  "state,sleeve,evidence,n_months,n_episodes,mean_ex,ep_hit,future_zero_weight_candidate\n" +
  R_all.classRows.map((r) => [r.state, r.sleeve, r.evidence, r.n_months, r.n_episodes, fin(r.mean_ex) ? r.mean_ex : "", fin(r.ep_hit) ? r.ep_hit : "", r.future_zero_weight_candidate].join(",")).join("\n") + "\n");

// panel comparison
const panel = {
  core: { start: "1976-07-01", end: "2026-08-01", n_months: joined.filter((j) => coreF(j.date)).length },
  full: { start: "1987-10-01", end: "2026-08-01", n_months: joined.filter((j) => fullF(j.date)).length },
  max_history_months: joined.length,
};
panel.core_month_means = {};
panel.full_month_means = {};
for (const sl of SLEEVES) {
  panel.core_month_means[sl] = mean(R_core.monthRows.filter((r) => r.sleeve === sl).flatMap(() => [])); // placeholder
}
// simpler: unconditional means per panel
for (const sl of SLEEVES) {
  const rc = joined.filter((j) => coreF(j.date) && fin(j[sl]));
  const rf = joined.filter((j) => fullF(j.date) && fin(j[sl]));
  panel.core_month_means[sl] = { n: rc.length, mean: mean(rc.map((x) => x[sl])) };
  panel.full_month_means[sl] = { n: rf.length, mean: mean(rf.map((x) => x[sl])) };
}
fs.writeFileSync(path.join(GEN174, "panel-comparison.json"), JSON.stringify({ panels: panel, note: "core=1976-07+ intersection of 6 long sleeves; full=1987-10+ all 9; max-history uses genuine starts" }, null, 2));

// summary.json
const bestWorst = STATES.map((st) => {
  const m = R_all.monthRows.filter((r) => r.state === st && r.sleeve !== "cash" && fin(r.mean));
  const sorted = [...m].sort((a, b) => b.mean - a.mean);
  return { state: st, best: sorted[0] ? { sleeve: sorted[0].sleeve, mean: sorted[0].mean } : null, worst: sorted[sorted.length - 1] ? { sleeve: sorted[sorted.length - 1].sleeve, mean: sorted[sorted.length - 1].mean } : null };
});
const summary = {
  issue: 174,
  branch: "research/issue-174-nine-sleeve-macro-asset-map",
  base_head: "f8eed2c5fa7086c0359a11360ce36cf33936afac",
  macro: { path: "generated/issue-160/deep-history-v01-monthly.csv", sha256: macroSha, months: macroMonths.length, first: "1966-03-01", last: "2026-08-01", thresholds: "±10", episodes: stateEpisodes.length },
  inputs: { equity_blob_sha256: eqBlobSha, treasury10y_blob_sha256: t10BlobSha },
  coverage: JSON.parse(fs.readFileSync(path.join(GEN174, "nine-sleeve-coverage.json"), "utf8")),
  state_counts: stateCounts,
  best_worst_by_state_monthly_mean: bestWorst,
  evidence_counts: {},
  zero_candidates: R_all.classRows.filter((r) => r.future_zero_weight_candidate).map((r) => ({ state: r.state, sleeve: r.sleeve })),
  panels: panel,
  production_authorized: false,
  outcome_data_loaded: true,
  files: fs.readdirSync(GEN174),
};
for (const r of R_all.classRows) summary.evidence_counts[r.evidence] = (summary.evidence_counts[r.evidence] || 0) + 1;
fs.writeFileSync(path.join(GEN174, "summary.json"), JSON.stringify(summary, null, 2));
console.log("wrote", GEN174, "zero candidates", summary.zero_candidates.length, "evidence", summary.evidence_counts);
console.log("DONE map");
