#!/usr/bin/env node
// Issue #186 — turning-lag builder: E_t timeline, bear extraction, matching,
// diagnostics, stress. Frozen contract: issue-186-turning-lag-prereg.md.
// Post-prereg ONLY (prereg a9a2cbc). No model change. No V6.6 in primary.
// Parents read-only. All writes go to research/generated/issue-186/.
import fs from "node:fs";
import path from "node:path";
import crypto from "node:crypto";

const ROOT = process.cwd();
const RES = path.join(ROOT, "indicators/macro-pressure-map/research");
const GEN186 = path.join(RES, "generated/issue-186");
const sha256 = (b) => crypto.createHash("sha256").update(b).digest("hex");
const fin = (x) => typeof x === "number" && Number.isFinite(x);
const readLF = (rel) => fs.readFileSync(path.join(RES, rel), "utf8").replace(/\r/g, "");

// ---------------------------------------------------------------- frozen policy (verbatim #178/#183)
const ORDER = ["sp500", "nasdaq", "russell", "treasury2y", "treasury10y", "longtreasury", "gold", "oil"];
const EQ = ["sp500", "nasdaq", "russell"];
const ZEROS = [["G_Low/I_Low", "oil"], ["G_Neutral/I_High", "russell"], ["G_High/I_Low", "gold"]];
const TOL = 1e-9, COST_UNUSED = 0;
const MOVE = 5, MOVE10 = 10, WIN = 12, DEF = 27.5, EXP = 52.5;
const ERAS = [["E1", "1966-03-01", "1979-12-01"], ["E2", "1980-01-01", "2007-12-01"], ["E3", "2008-01-01", "2019-12-01"], ["E4", "2020-01-01", "2026-08-01"]];
const eraOf = (d) => (ERAS.find(([, lo, hi]) => d >= lo && d <= hi) || ["EX"])[0];

// ---------------------------------------------------------------- 1. parent pins + matrix integrity
const PARENTS = {
  "issue-177": "bc652bd615f2c5e9137050d01c666dbcd9528cd3",
  "issue-178": "10dcdce0ec86b0493d6df6b916b720eba46dcbe6",
  "issue-180": "ac251ad5149d9f550d82dfb34b3551fe01032367",
  "issue-183": "411835cc9e3a00d0f5d998df9fb2058d8a917e96",
  "issue-184": "a3c6dbbdbcdbaf25129caf9bd5008b08947605e3",
};
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
for (const [st, w] of SW) {
  const tot = ORDER.concat(["cash"]).reduce((a, s) => a + w[s], 0);
  if (Math.abs(tot - 100) > TOL) { console.error("FAIL matrix " + st); process.exit(1); }
  for (const [dh, s] of ZEROS) if (st === dh && Math.abs(w[s]) > TOL) { console.error("FAIL zero " + st); process.exit(1); }
}
const EQW = new Map([...SW].map(([k, w]) => [k, EQ.reduce((a, s) => a + w[s], 0)]));
console.log("matrix states", SW.size, "E range", Math.min(...EQW.values()).toFixed(2), Math.max(...EQW.values()).toFixed(2));

// ---------------------------------------------------------------- B-2 timeline (verbatim #183) + E_t
function band(s) { return s < -10 ? "Low" : s > 10 ? "High" : "Neutral"; }
const dhByDate = new Map(), gDH = new Map(), iDH = new Map();
{
  const t = readLF("generated/issue-160/deep-history-v01-monthly.csv").trim().split("\n");
  const h = t[0].split(",");
  const gi = h.indexOf("growth_dh"), ii = h.indexOf("inflation_dh");
  for (const l of t.slice(1)) {
    const c = l.split(",");
    const g = parseFloat(c[gi]), v = parseFloat(c[ii]);
    if (fin(g) && fin(v)) { dhByDate.set(c[0], "G_" + band(g) + "/I_" + band(v)); gDH.set(c[0].slice(0, 7), g); iDH.set(c[0].slice(0, 7), v); }
  }
}
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
const ETL = tlB2.map((r) => ({ date: r.date, ym: r.date.slice(0, 7), state: r.dhState, E: EQW.get(r.dhState) }));
{
  const gross = ETL.every((r) => fin(r.E) && r.E >= 22.5 - TOL && r.E <= 60 + TOL);
  if (ETL.length !== 721 || !gross) { console.error("FAIL E_t integrity " + ETL.length); process.exit(1); }
}
console.log("E_t months", ETL.length, ETL[0].date, "->", ETL[ETL.length - 1].date);
const dE = ETL.map((r, i) => (i ? r.E - ETL[i - 1].E : 0));
const nSig = dE.filter((v) => Math.abs(v) >= MOVE - 1e-9).length;
console.log("months with |dE|>=5pp:", nSig);

// ---------------------------------------------------------------- prices
const mpx = readLF("generated/issue-186/spx-monthly.csv").trim().split("\n").slice(1).map((l) => {
  const c = l.split(","); return { date: c[0], ym: c[1], px: parseFloat(c[3]) };
});
if (mpx.length !== 728 || mpx[0].ym !== "1966-01" || mpx[727].ym !== "2026-08") { console.error("FAIL price panel"); process.exit(1); }
const PM = new Map(mpx.map((r) => [r.ym, r.px]));
const dpx = readLF("generated/issue-186/spx-daily.csv").trim().split("\n").slice(1).map((l) => {
  const c = l.split(","); return { date: c[0], px: parseFloat(c[1]) };
}).filter((r) => fin(r.px));

// ---------------------------------------------------------------- extractor (verbatim prereg section 4)
function extractBears(labels, closes, thresh) {
  const n = labels.length, events = [];
  let i = 0;
  while (i < n) {
    let peakI = i, peakP = closes[i], j = i + 1, rec = null;
    while (j < n) {
      if (closes[j] > peakP) { peakP = closes[j]; peakI = j; }
      else if (closes[j] <= (1 - thresh) * peakP) {
        for (let k = j + 1; k < n; k++) if (closes[k] >= peakP) { rec = k; break; }
        break;
      }
      j++;
    }
    if (rec === null) {
      if (j < n) {
        const seg = closes.slice(peakI);
        let ti = 0; for (let t = 1; t < seg.length; t++) if (seg[t] < seg[ti]) ti = t;
        events.push({ peakI, troughI: peakI + ti, recI: null, severity: seg[ti] / peakP - 1, censored: true });
      }
      break;
    }
    const pre = closes.slice(i, rec);
    const pmax = Math.max(...pre);
    const peakI2 = i + pre.findIndex((v) => v === pmax);
    const seg2 = closes.slice(peakI2, rec);
    let ti = 0; for (let t = 1; t < seg2.length; t++) if (seg2[t] < seg2[ti]) ti = t;
    events.push({ peakI: peakI2, troughI: peakI2 + ti, recI: rec, severity: seg2[ti] / closes[peakI2] - 1, censored: false });
    i = rec + 1;
  }
  return events;
}
const mons = mpx.map((r) => r.ym), mcl = mpx.map((r) => r.px);
const ev20 = extractBears(mons, mcl, 0.20);
const ev10 = extractBears(mons, mcl, 0.10);
console.log("monthly 20% events:", ev20.length, ev20.map((e) => mons[e.peakI] + "->" + mons[e.troughI] + (e.censored ? "(c)" : "")).join(" "));
console.log("monthly 10% events:", ev10.length);
// daily COVID + 1987
function dailyWin(lo, hi) { return dpx.filter((r) => r.date >= lo && r.date <= hi); }
const cov = dailyWin("2020-01-01", "2020-06-30");
const evCov = extractBears(cov.map((r) => r.date), cov.map((r) => r.px), 0.20);
const y87 = dailyWin("1987-09-01", "1987-12-31");
const ev87 = extractBears(y87.map((r) => r.date), y87.map((r) => r.px), 0.20);
console.log("daily covid events:", evCov.length, evCov.map((e) => cov[e.peakI].date + "->" + cov[e.troughI].date).join(" "));
console.log("daily 1987 events:", ev87.length, ev87.map((e) => y87[e.peakI].date + "->" + y87[e.troughI].date + " sev" + (e.severity * 100).toFixed(1)).join(" "));

// ---------------------------------------------------------------- matching (verbatim prereg section 6)
const EIDX = new Map(ETL.map((r, i) => [r.ym, i]));
const moDiff = (a, b) => (+b.slice(0, 4) - +a.slice(0, 4)) * 12 + (+b.slice(5, 7) - +a.slice(5, 7));
function matchPeak(T, th) {
  const ti = EIDX.get(T);
  if (ti === undefined) return { label: "censored_edge", lag: null, act: null };
  let best = null;
  for (let m = Math.max(1, ti - WIN); m <= ti; m++)
    if (dE[m] <= -th && ETL[ti].E <= ETL[m - 1].E - th) best = m;
  if (best !== null) return { label: "early_protection", lag: moDiff(T, ETL[best].ym), act: ETL[best].date };
  for (let m = ti + 1; m < Math.min(ETL.length, ti + 1 + WIN); m++)
    if (dE[m] <= -th) return { label: "late_protection", lag: moDiff(T, ETL[m].ym), act: ETL[m].date };
  if (ETL[ti].E <= DEF) return { label: "already_defensive", lag: null, act: null };
  if (ti < WIN || ti + WIN >= ETL.length) return { label: "censored_edge", lag: null, act: null };
  return { label: "no_action", lag: null, act: null };
}
function matchTrough(T, th) {
  const ti = EIDX.get(T);
  if (ti === undefined) return { label: "censored_edge", lag: null, act: null };
  let best = null;
  for (let m = Math.max(1, ti - WIN); m <= ti; m++)
    if (dE[m] >= th && ETL[ti].E >= ETL[m - 1].E + th) best = m;
  if (best !== null) return { label: "early_re-risk", lag: moDiff(T, ETL[best].ym), act: ETL[best].date };
  for (let m = ti + 1; m < Math.min(ETL.length, ti + 1 + WIN); m++)
    if (dE[m] >= th) return { label: "late_re-risk", lag: moDiff(T, ETL[m].ym), act: ETL[m].date };
  if (ETL[ti].E >= EXP) return { label: "already_exposed", lag: null, act: null };
  if (ti < WIN || ti + WIN >= ETL.length) return { label: "censored_edge", lag: null, act: null };
  return { label: "no_action", lag: null, act: null };
}
const Eat = (ym, off) => {
  const i = EIDX.get(ym);
  if (i === undefined || i + off < 0 || i + off >= ETL.length) return null;
  return ETL[i + off].E;
};

// ---------------------------------------------------------------- per-event measures (prereg section 7)
function r20from(troughI, closes) {
  const base = closes[troughI];
  for (let k = troughI + 1; k < closes.length; k++)
    if (closes[k] >= 1.2 * base) return k;
  return null;
}
function peakRow(e, th) {
  const P = mons[e.peakI], T = mons[e.troughI];
  const m = matchPeak(P, th);
  const pxP = mcl[e.peakI], pxT = mcl[e.troughI];
  let ddBefore = null, retToAct = null;
  if (m.act) {
    const pa = PM.get(m.act.slice(0, 7));
    retToAct = pa / pxP - 1;
    ddBefore = (pxP - pa) / (pxP - pxT);
  }
  const win = [];
  for (let k = -WIN; k <= WIN; k++) {
    const ti = EIDX.get(P);
    if (ti !== undefined && ti + k >= 1 && ti + k < ETL.length) win.push(dE[ti + k]);
  }
  // first post-event unconditional reallocation (robustness column)
  let firstPost = null;
  {
    const ti = EIDX.get(P);
    for (let k = 1; k <= WIN && ti + k < ETL.length; k++)
      if (Math.abs(dE[ti + k]) > 1e-9) { firstPost = { month: ETL[ti + k].date, dE: dE[ti + k] }; break; }
  }
  // whipsaws: pre-window >=th cuts failing remains-in-effect
  let whip = 0;
  {
    const ti = EIDX.get(P);
    for (let k = Math.max(1, ti - WIN); k <= ti; k++)
      if (dE[k] <= -th && !(ETL[ti].E <= ETL[k - 1].E - th)) whip++;
  }
  let churn = 0;
  {
    const ti = EIDX.get(P);
    for (let k = Math.max(1, ti - WIN); k <= Math.min(ETL.length - 1, ti + WIN); k++)
      if (ETL[k].state !== ETL[k - 1].state) churn++;
  }
  return {
    peak: P, peak_px: pxP, trough: T, trough_px: pxT, severity: e.severity, rec: e.recI === null ? null : mons[e.recI], censored: e.censored,
    match: m.label, lag: m.lag, act: m.act, E_peak: ETL[EIDX.get(P)]?.E ?? null, E_trough: ETL[EIDX.get(T)]?.E ?? null,
    E_m6: Eat(P, -6), E_m3: Eat(P, -3), E_m1: Eat(P, -1), E_p1: Eat(P, 1), E_p3: Eat(P, 3), E_p6: Eat(P, 6),
    ret_peak_to_act: retToAct, dd_frac_before_action: ddBefore,
    n_win_actions: win.filter((v) => Math.abs(v) >= th).length, win_down: win.filter((v) => v <= -th).length, win_up: win.filter((v) => v >= th).length,
    first_post: firstPost, whipsaws: whip, churn, era: eraOf(P + "-01"),
  };
}
function troughRow(e, th) {
  const T = mons[e.troughI];
  const m = matchTrough(T, th);
  const pxT = mcl[e.troughI];
  const r20 = r20from(e.troughI, mcl);
  let frac = null, retToAct = null;
  if (m.act && r20 !== null) {
    const pa = PM.get(m.act.slice(0, 7));
    frac = (pa - pxT) / (mcl[r20] - pxT);
    retToAct = pa / pxT - 1;
  }
  const win = [];
  for (let k = -WIN; k <= WIN; k++) {
    const ti = EIDX.get(T);
    if (ti !== undefined && ti + k >= 1 && ti + k < ETL.length) win.push(dE[ti + k]);
  }
  let firstPost = null;
  {
    const ti = EIDX.get(T);
    for (let k = 1; k <= WIN && ti + k < ETL.length; k++)
      if (Math.abs(dE[ti + k]) > 1e-9) { firstPost = { month: ETL[ti + k].date, dE: dE[ti + k] }; break; }
  }
  let whip = 0;
  {
    const ti = EIDX.get(T);
    for (let k = Math.max(1, ti - WIN); k <= ti; k++)
      if (dE[k] >= th && !(ETL[ti].E >= ETL[k - 1].E + th)) whip++;
  }
  let churn = 0;
  {
    const ti = EIDX.get(T);
    for (let k = Math.max(1, ti - WIN); k <= Math.min(ETL.length - 1, ti + WIN); k++)
      if (ETL[k].state !== ETL[k - 1].state) churn++;
  }
  return {
    trough: T, trough_px: pxT, peak: mons[e.peakI], peak_px: mcl[e.peakI], severity: e.severity,
    rec20: r20 === null ? null : mons[r20], rec20_px: r20 === null ? null : mcl[r20],
    recfull: e.recI === null ? null : mons[e.recI], censored: e.censored,
    match: m.label, lag: m.lag, act: m.act, E_trough: ETL[EIDX.get(T)]?.E ?? null,
    E_m6: Eat(T, -6), E_m3: Eat(T, -3), E_m1: Eat(T, -1), E_p1: Eat(T, 1), E_p3: Eat(T, 3), E_p6: Eat(T, 6),
    ret_trough_to_act: retToAct, rebound_frac_before_action: frac,
    n_win_actions: win.filter((v) => Math.abs(v) >= th).length, win_down: win.filter((v) => v <= -th).length, win_up: win.filter((v) => v >= th).length,
    first_post: firstPost, whipsaws: whip, churn, era: eraOf(T + "-01"),
  };
}
const peaks20 = ev20.map((e) => peakRow(e, MOVE));
const troughs20 = ev20.map((e) => troughRow(e, MOVE));
const peaks10 = ev10.map((e) => peakRow(e, MOVE));
const troughs10 = ev10.map((e) => troughRow(e, MOVE));

// ---------------------------------------------------------------- summaries (prereg section 8)
const q = (a, p) => {
  const v = a.filter(fin).sort((x, y) => x - y);
  if (!v.length) return null;
  const pos = (p / 100) * (v.length - 1), lo = Math.floor(pos), hi = Math.ceil(pos);
  return v[lo] + (v[hi] - v[lo]) * (pos - lo);
};
const med = (a) => q(a, 50);
function lagSummary(rows, earlyRe, lateRe) {
  const matched = rows.filter((r) => r.lag !== null && fin(r.lag));
  const lags = matched.map((r) => r.lag);
  const lab = rows.map((r) => r.match);
  const hit = (x) => rows.filter((r) => r.match === lateRe && r.lag !== null && r.lag <= x).length / rows.length;
  return {
    n: rows.length,
    matched: matched.length, coverage: rows.length ? matched.length / rows.length : null,
    lag_median: med(lags), lag_p25: q(lags, 25), lag_p75: q(lags, 75),
    lag_min: lags.length ? Math.min(...lags) : null, lag_max: lags.length ? Math.max(...lags) : null,
    share_early: rows.filter((r) => r.match === earlyRe).length / rows.length,
    share_late: rows.filter((r) => r.match === lateRe).length / rows.length,
    share_never: rows.filter((r) => r.match === "no_action").length / rows.length,
    share_def: rows.filter((r) => ["already_defensive", "already_exposed"].includes(r.match)).length / rows.length,
    share_cens: rows.filter((r) => r.match === "censored_edge").length / rows.length,
    hit3: hit(3), hit6: hit(6), hit12: hit(12),
  };
}
const sumPeak10 = { ...lagSummary(peaks10, "early_protection", "late_protection"), dd_before_median: med(peaks10.filter((r) => r.dd_frac_before_action !== null).map((r) => r.dd_frac_before_action)) };
const sumTrough10 = { ...lagSummary(troughs10, "early_re-risk", "late_re-risk"), rebound_frac_median: med(troughs10.filter((r) => r.rebound_frac_before_action !== null).map((r) => r.rebound_frac_before_action)) };
const sumPeak20 = { ...lagSummary(peaks20, "early_protection", "late_protection"), dd_before_median: med(peaks20.filter((r) => r.dd_frac_before_action !== null).map((r) => r.dd_frac_before_action)) };
const sumTrough20 = { ...lagSummary(troughs20, "early_re-risk", "late_re-risk"), rebound_frac_median: med(troughs20.filter((r) => r.rebound_frac_before_action !== null).map((r) => r.rebound_frac_before_action)) };
// era splits
function eraSplit(rows, key) {
  const o = {};
  for (const r of rows) { (o[r.era] = o[r.era] || []).push(r.lag); }
  return Object.fromEntries(Object.entries(o).map(([k, v]) => [k, { n: v.length, matched: v.filter((x) => x !== null && fin(x)).length, median: med(v.filter((x) => x !== null && fin(x))) }]));
}

// ---------------------------------------------------------------- slope diagnostic (prereg section 9, descriptive only)
function slopeDiag() {
  return ev20.map((e) => {
    const T = mons[e.troughI];
    const ti = mpx.findIndex((r) => r.ym === T);
    let g1 = null, i1 = null, x1 = null, b1 = null;
    const st0 = ETL[EIDX.get(T)]?.state ?? null;
    // walk months T..T+12 using month arithmetic on ym strings
    const addM = (ym, k) => {
      let y = +ym.slice(0, 4), m = +ym.slice(5, 7) + k;
      while (m > 12) { m -= 12; y++; }
      return String(y).padStart(4, "0") + "-" + String(m).padStart(2, "0");
    };
    for (let k = 0; k <= WIN; k++) {
      const ym = addM(T, k);
      if (g1 === null && gDH.has(ym) && gDH.has(addM(ym, -1)) && k > 0 && gDH.get(ym) - gDH.get(addM(ym, -1)) > 0) g1 = ym;
      if (i1 === null && iDH.has(ym) && iDH.has(addM(ym, -1)) && k > 0 && iDH.get(ym) - iDH.get(addM(ym, -1)) >= 0) i1 = ym;
      if (x1 === null && k > 0) {
        const sNow = ETL[EIDX.get(ym)]?.state, sPrev = ETL[EIDX.get(addM(T, 0))]?.state;
        if (sNow && sPrev && sNow !== st0) x1 = ym;
      }
      if (b1 === null && k > 0 && ETL[EIDX.get(ym)] && ETL[EIDX.get(T)] && ETL[EIDX.get(ym)].state !== ETL[EIDX.get(T)].state) b1 = ym;
    }
    const tr = troughs20.find((r) => r.trough === T);
    const e1 = tr && tr.match.includes("re-risk") ? tr.act : (tr && tr.match === "early_re-risk" ? tr.act : null);
    const pxT = mcl[e.troughI];
    const falseG = g1 !== null && mpx.slice(e.troughI + 1, e.troughI + 7).some((r) => r.px < pxT);
    const falseI = i1 !== null && mpx.slice(e.troughI + 1, e.troughI + 7).some((r) => r.px < pxT);
    let eRev = false;
    if (tr && tr.act) {
      const ai = EIDX.get(tr.act.slice(0, 7));
      for (let k = ai + 1; k <= Math.min(ETL.length - 1, ai + 6); k++)
        if (ETL[k].E - ETL[k - 1].E <= -MOVE) eRev = true;
    }
    return {
      trough: T, trough_px: pxT, g_up: g1, i_flat: i1,
      i_level_band: i1 ? band(iDH.get(i1)) : null, regime_cross: x1, b2: b1,
      equity_add: tr?.act ?? null, equity_add_lag: tr?.lag ?? null,
      false_start_growth: falseG, false_start_inflation: falseI, equity_reversal_6mo: eRev,
    };
  });
}
const slope = slopeDiag();

// ---------------------------------------------------------------- +1/+2/+3 stress (prereg section 10: shift E_t, rerun matching)
function stressRun(k) {
  const Esh = ETL.map((r, i) => (i - k >= 0 ? ETL[i - k].E : ETL[0].E));
  const dEsh = Esh.map((v, i) => (i ? v - Esh[i - 1] : 0));
  const mP = (T) => {
    const ti = EIDX.get(T);
    if (ti === undefined) return null;
    let best = null;
    for (let m = Math.max(1, ti - WIN); m <= ti; m++)
      if (dEsh[m] <= -MOVE && Esh[ti] <= Esh[m - 1] - MOVE) best = m;
    if (best !== null) return moDiff(T, ETL[best].ym);
    for (let m = ti + 1; m < Math.min(Esh.length, ti + 1 + WIN); m++)
      if (dEsh[m] <= -MOVE) return moDiff(T, ETL[m].ym);
    return null;
  };
  const mT = (T) => {
    const ti = EIDX.get(T);
    if (ti === undefined) return null;
    let best = null;
    for (let m = Math.max(1, ti - WIN); m <= ti; m++)
      if (dEsh[m] >= MOVE && Esh[ti] >= Esh[m - 1] + MOVE) best = m;
    if (best !== null) return moDiff(T, ETL[best].ym);
    for (let m = ti + 1; m < Math.min(Esh.length, ti + 1 + WIN); m++)
      if (dEsh[m] >= MOVE) return moDiff(T, ETL[m].ym);
    return null;
  };
  const pl = ev20.map((e) => mP(mons[e.peakI])).filter((v) => v !== null && fin(v));
  const tl = ev20.map((e) => mT(mons[e.troughI])).filter((v) => v !== null && fin(v));
  return { k, peak_lag_median: med(pl), trough_lag_median: med(tl), peak_n: pl.length, trough_n: tl.length };
}
const stress = [stressRun(1), stressRun(2), stressRun(3)];

// ---------------------------------------------------------------- verdict (prereg section 11, literally)
const mpLag = sumPeak20.lag_median ?? NaN, mtLag = sumTrough20.lag_median ?? NaN;
const mdd = sumPeak20.dd_before_median ?? NaN;
const mreb = sumTrough20.rebound_frac_median ?? NaN;
const covMin = Math.min(sumPeak20.coverage ?? 0, sumTrough20.coverage ?? 0);
const lateGlobal = mpLag >= 4 || mtLag >= 6 || mdd >= 0.60;
const okLags = mpLag <= 2 && mtLag <= 4;
const straddle = (mpLag <= 2) !== (mtLag <= 4);
let verdict, verdictNote;
if (ev20.length < 4) { verdict = "deep_history_timing_not_assessable"; verdictNote = "fewer than 4 primary events"; }
else if (lateGlobal && !okLags) {
  verdict = straddle ? "deep_history_timing_mixed_by_cycle" : "deep_history_timing_materially_late";
  verdictNote = straddle ? "peak/trough medians straddle late/acceptable bounds" : "late bound breached on lag or drawdown-missed median";
} else if (okLags && mreb <= 0.60 && covMin >= 0.60) {
  verdict = "deep_history_timing_acceptable_with_limitations"; verdictNote = "all acceptable bounds met";
} else if (straddle) {
  verdict = "deep_history_timing_mixed_by_cycle"; verdictNote = "peak/trough medians straddle bounds";
} else {
  // TREE-GAP (disclosed): lags are within acceptable bounds but the rebound-
  // missed median (or coverage) fails the acceptable gate, while no late bound
  // fires. Prereg section 11 names no category for this cell; it is reported
  // here as mixed_by_cycle because peak-side (early) and trough-side
  // (rebound-missed) evidence point in opposite directions. Raw medians rule.
  verdict = "deep_history_timing_mixed_by_cycle";
  verdictNote = "tree-gap: lags acceptable but rebound-missed median " + (mreb * 100).toFixed(1) + "% > 60% (trough-side weak, peak-side early); reported as mixed with raw numbers primary";
}

// ---------------------------------------------------------------- named case cards (lookup windows frozen here)
const EPISODES = [
  ["1969-70", "1968-01", "1970-12"], ["1973-74", "1972-01", "1975-12"],
  ["1980-82", "1979-01", "1983-12"], ["1987", "1987-01", "1988-12"],
  ["2000-02", "2000-01", "2003-12"], ["2007-09", "2007-01", "2010-12"],
  ["2020", "2020-01", "2020-12"], ["2022", "2021-01", "2023-12"],
];
const cases = EPISODES.map(([name, lo, hi]) => {
  const hits = ev20.map((e, i) => ({ e, i })).filter(({ e }) =>
    (mons[e.peakI] >= lo && mons[e.peakI] <= hi) || (mons[e.troughI] >= lo && mons[e.troughI] <= hi));
  return {
    episode: name, window: [lo, hi],
    primary_events: hits.map(({ e, i }) => ({ peak: mons[e.peakI], trough: mons[e.troughI], severity: e.severity, peak_match: peaks20[i], trough_match: troughs20[i], slope: slope[i] })),
    qualifier_note: hits.length ? null : "NO primary-20% event touches this window (reason: no ≥20% monthly peak-to-trough drawdown with full retracement inside the window under the frozen extractor)",
  };
});

// ---------------------------------------------------------------- write outputs
fs.mkdirSync(GEN186, { recursive: true });
const W = (n, c) => fs.writeFileSync(path.join(GEN186, n), c);
const J = (o) => JSON.stringify(o, null, 2) + "\n";
W("manifest.json", J({ issue: 186, parents: PARENTS, price: JSON.parse(readLF("generated/issue-186/spx-provenance.json")).primary, et_months: ETL.length, et_first: ETL[0].date, et_last: ETL[ETL.length - 1].date, events20: ev20.length, events10: ev10.length, production_authorized: false }));
W("equity-timeline.csv", "date,state,E,dE\n" + ETL.map((r, i) => [r.date, r.state, r.E.toFixed(2), dE[i].toFixed(2)].join(",")).join("\n") + "\n");
W("events-monthly-20.csv", "peak,trough,rec,severity,censored\n" + ev20.map((e) => [mons[e.peakI], mons[e.troughI], e.recI === null ? "" : mons[e.recI], e.severity.toFixed(4), e.censored ? 1 : 0].join(",")).join("\n") + "\n");
W("events-monthly-10.csv", "peak,trough,rec,severity,censored\n" + ev10.map((e) => [mons[e.peakI], mons[e.troughI], e.recI === null ? "" : mons[e.recI], e.severity.toFixed(4), e.censored ? 1 : 0].join(",")).join("\n") + "\n");
W("peaks-20.csv", "peak,match,lag,act,E_peak,dd_frac,era\n" + peaks20.map((r) => [r.peak, r.match, r.lag ?? "", r.act ?? "", r.E_peak, r.dd_frac_before_action ?? "", r.era].join(",")).join("\n") + "\n");
W("peaks-10.csv", "peak,match,lag,act,E_peak,dd_frac,era\n" + peaks10.map((r) => [r.peak, r.match, r.lag ?? "", r.act ?? "", r.E_peak, r.dd_frac_before_action ?? "", r.era].join(",")).join("\n") + "\n");
W("troughs-10.csv", "trough,match,lag,act,E_trough,reb_frac,era\n" + troughs10.map((r) => [r.trough, r.match, r.lag ?? "", r.act ?? "", r.E_trough, r.rebound_frac_before_action ?? "", r.era].join(",")).join("\n") + "\n");
W("troughs-20.csv", "trough,match,lag,act,E_trough,reb_frac,era\n" + troughs20.map((r) => [r.trough, r.match, r.lag ?? "", r.act ?? "", r.E_trough, r.rebound_frac_before_action ?? "", r.era].join(",")).join("\n") + "\n");
W("daily-covid.csv", "date,close\n" + cov.map((r) => [r.date, r.px].join(",")).join("\n") + "\n");
W("daily-covid-events.csv", "peak,trough,severity\n" + evCov.map((e) => [cov[e.peakI].date, cov[e.troughI].date, e.severity.toFixed(4)].join(",")).join("\n") + "\n");
W("summary.json", J({
  issue: 186, verdict, verdict_note: verdictNote,
  events20: ev20.length, events10: ev10.length,
  peaks20: peaks20, troughs20, peaks20_summary: sumPeak20, troughs20_summary: sumTrough20,
  peaks10_summary: sumPeak10, troughs10_summary: sumTrough10,
  era_peaks: eraSplit(peaks20), era_troughs: eraSplit(troughs20),
  era_peaks: eraSplit(peaks20, 0), era_troughs: eraSplit(troughs20, 0),
  slope, stress, cases,
  covid_daily: evCov.map((e) => ({ peak: cov[e.peakI].date, trough: cov[e.troughI].date, severity: e.severity })),
  covid_monthly_resolution: {
    peak_month: "2020-02", peak_match: matchPeak("2020-02", MOVE), E_peak_month: ETL[EIDX.get("2020-02")]?.E ?? null,
    trough_month: "2020-03", trough_match: matchTrough("2020-03", MOVE), E_trough_month: ETL[EIDX.get("2020-03")]?.E ?? null,
    note: "daily peak/trough labelled at monthly resolution; allocation timeline is monthly (no intramonth execution claimed)",
  },
  y1987_daily: ev87.map((e) => ({ peak: y87[e.peakI].date, trough: y87[e.troughI].date, severity: e.severity })),
  medians: { peak_lag: mpLag, trough_lag: mtLag, dd_before: mdd, rebound_frac: sumTrough20.rebound_frac_median },
  production_authorized: false,
}));
console.log("events20:", ev20.length, "peaks summary:", JSON.stringify(sumPeak20));
console.log("troughs summary:", JSON.stringify(sumTrough20));
console.log("verdict:", verdict);
console.log("stress:", JSON.stringify(stress));
