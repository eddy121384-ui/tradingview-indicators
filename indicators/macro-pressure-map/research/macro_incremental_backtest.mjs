#!/usr/bin/env node
// Macro vs classic trend/vol baselines — incremental value backtest.
// Frozen prereg: research/macro_incremental_prereg.md (commit c984f6d).
// ONE relative rule: Final_w[t+1] = Baseline_w[t+1] x min(1, E_DH[t+1]/0.45).
// Gap: carry only s_last on 3 missing #183 months; baseline trades continue.
// Primary panel: full 714 continuous months; 711 observed-macro secondary.
// Research only, production_authorized=false. No tuning, no variants, no Pine.
import fs from "node:fs";
import path from "node:path";
import crypto from "node:crypto";
import { fileURLToPath } from "node:url";

const HERE = path.dirname(fileURLToPath(import.meta.url));
const RES = HERE;
const EQUITY = path.join(RES, "generated/issue-166/equity-monthly-total-returns.csv");
const CASHF = path.join(RES, "generated/issue-174/nine-sleeve-monthly-returns.csv");
const MATRIX = path.join(RES, "generated/issue-178/weight-matrix.csv");
const STRUCT = path.join(RES, "generated/issue-183/corrected-structural-monthly.csv");
const SIGF = path.join(RES, "generated/classic-equity-baselines/monthly-signals.csv");
const VOLF = path.join(RES, "generated/classic-equity-baselines/volatility-managed-monthly.csv");
const DAILY = path.join(RES, "generated/classic-equity-baselines/daily-market-total-returns.csv");
const EVENTS = path.join(RES, "generated/issue-186/events-monthly-20.csv");
const OUT = path.join(RES, "generated/classic-equity-baselines");
const NEUTRAL = 0.45;
const FEE = 0.0002, FEE10 = 0.001;

const assert = (ok, msg) => { if (!ok) throw new Error("BLOCKED: " + msg); };
const ym = (s) => { const t = s.slice(0, 7); const [y, m] = t.split("-").map(Number); return y * 12 + m; };
const avg = (a) => a.reduce((x, y) => x + y, 0) / a.length;
const parse = (f) => {
  const lines = fs.readFileSync(f, "utf8").trim().split(/\r?\n/);
  const cols = lines.shift().split(",");
  return { cols, rows: lines.map((l) => Object.fromEntries(l.split(",").map((v, j) => [cols[j], v]))) };
};

// ---- 1. Matrix (#178 frozen) ----
const mx = parse(MATRIX);
assert(mx.rows.length === 9, "matrix rows != 9");
const E = {};
for (const r of mx.rows) {
  const parts = ["sp500", "nasdaq", "russell", "treasury2y", "treasury10y", "longtreasury", "gold", "oil", "cash"].map((k) => Number(r[k]));
  assert(parts.every(Number.isFinite), "matrix non-numeric " + r.state);
  const tot = parts.reduce((a, b) => a + b, 0);
  assert(Math.abs(tot - 100) < 1e-9, "matrix row != 100: " + r.state);
  E[r.state] = (Number(r.sp500) + Number(r.nasdaq) + Number(r.russell)) / 100;
}
assert(Math.abs(E["G_Neutral/I_Neutral"] - NEUTRAL) < 1e-12, "neutral anchor != 0.45");
const eVals = Object.values(E);
assert(Math.min(...eVals) === 0.225 && Math.max(...eVals) === 0.60, "equity range != 22.5-60");
const zc = mx.rows.filter((r) => ["sp500","nasdaq","russell","treasury2y","treasury10y","longtreasury","gold","oil"].some((k) => Number(r[k]) === 0));
assert(zc.length === 3, "zero cells != 3");

// ---- 2. Structural timeline (#183, B-2 applied) ----
const st = parse(STRUCT);
assert(st.rows.length === 721, "struct rows != 721, got " + st.rows.length);
const smap = new Map();
let prevYm = null; const gaps = [];
for (const r of st.rows) {
  const m = r.date.slice(0, 7);
  assert(E[m] === undefined, "internal");
  assert(E[r.alloc_state] !== undefined, "unknown alloc_state " + r.alloc_state);
  assert(!smap.has(m), "dup struct month " + m);
  smap.set(m, r.alloc_state);
  if (prevYm !== null) { const d = ym(m) - prevYm; if (d !== 1) gaps.push([prevYm, m, d]); }
  prevYm = ym(m);
}
assert(smap.size === 721, "struct map size");
const missing = ["2025-10", "2025-11", "2026-01"];
for (const m of missing) assert(!smap.has(m), "gap month present " + m);
assert(gaps.length === 2, "expected 2 gap jumps");

// ---- 3. Baselines byte-identical: SMA10/MOM12 ----
const eqP = parse(EQUITY), cashP = parse(CASHF);
assert(eqP.rows.length === 800 && cashP.rows.length === 726, "input lengths");
const es = new Map(eqP.rows.map((r) => [r.date.slice(0, 7), Number(r.equity_tr)]));
const csh = new Map(cashP.rows.map((r) => [r.date.slice(0, 7), Number(r.cash)]));
const monthsAll = eqP.rows.map((r) => r.date.slice(0, 7));
const idx = new Map(); let px = 100;
for (const m of monthsAll) { px *= 1 + es.get(m); idx.set(m, px); }
const sigP = parse(SIGF);
assert(sigP.rows.length === 714, "signals != 714");
const recomputed = [];
for (let i = 1; i < monthsAll.length; i++) {
  const m = monthsAll[i], t = monthsAll[i - 1];
  if (ym(m) < ym("1967-03")) continue;
  const p10 = monthsAll.slice(i - 10, i), p12 = monthsAll.slice(i - 12, i);
  const sma = idx.get(t) > avg(p10.map((q) => idx.get(q))) ? 1 : 0;
  const elog = p12.reduce((a, q) => a + Math.log1p(es.get(q)) - Math.log1p(csh.get(q)), 0);
  const mom = elog > 0 ? 1 : 0;
  recomputed.push({ m, t, sma, mom });
}
assert(recomputed.length === 714, "recomputed panel != 714");
recomputed.forEach((r, i) => {
  const f = sigP.rows[i];
  assert(f.trade_month === r.m && f.signal_month === r.t, "signal timing mismatch " + r.m);
  assert(Number(f.sma10_weight) === r.sma && Number(f.mom12_weight) === r.mom, "baseline mismatch " + r.m);
});
const sigMap = new Map(sigP.rows.map((r) => [r.trade_month, { sma: Number(r.sma10_weight), mom: Number(r.mom12_weight) }]));

// ---- 4. VolFair byte-identical (Leg2 expanding-mean [0,1]) ----
const byM = new Map();
for (const l of fs.readFileSync(DAILY, "utf8").trim().split("\n").slice(1)) {
  const c = l.split(","); const m = c[0].slice(0, 6); const ex = parseFloat(c[2]);
  assert(Number.isFinite(ex), "daily excess");
  if (!byM.has(m)) byM.set(m, []);
  byM.get(m).push(ex);
}
const mkeys = [...byM.keys()].sort();
const rvMap = new Map();
for (const m of mkeys) {
  const d = byM.get(m); const mu = avg(d);
  const rv = d.reduce((a, x) => a + (x - mu) ** 2, 0) / 22;
  assert(rv > 0, "RV<=0 " + m);
  rvMap.set(m, rv);
}
const prevM = (m) => { const y = +m.slice(0, 4), mo = +m.slice(4, 6) - 1; return mo < 1 ? (y - 1) + "12" : y + String(mo).padStart(2, "0"); };
const panelM = mkeys.filter((x) => x >= "196703" && x <= "202608");
assert(panelM.length === 714, "vol panel != 714");
const hist = mkeys.filter((x) => x < "196703").map((x) => rvMap.get(x));
const wfair = []; const seen = [...hist];
for (const x of panelM) {
  const vb = avg(seen);
  wfair.push(Math.min(1, Math.max(0, vb / rvMap.get(prevM(x)))));
  seen.push(rvMap.get(x));
}
const volP = parse(VOLF);
assert(volP.rows.length === 714, "vol monthly != 714");
let maxDiff = 0;
volP.rows.forEach((r, i) => {
  const d = r.date.slice(0, 7).replace("-", "");
  assert(d === panelM[i], "vol date mismatch " + r.date);
  maxDiff = Math.max(maxDiff, Math.abs(Number(r.w_fair) - wfair[i]));
});
assert(maxDiff < 1e-4, "VolFair mismatch maxDiff=" + maxDiff);
const volMap = new Map(volP.rows.map((r) => [r.date.slice(0, 7), Number(r.w_fair)]));

// ---- 5. Trade panel + macro overlays ----
const tradeMonths = sigP.rows.map((r) => r.trade_month);
assert(tradeMonths.length === 714 && tradeMonths[0] === "1967-03" && tradeMonths.at(-1) === "2026-08", "panel");
const legs = { DH: [], SMA_DH: [], MOM_DH: [], VOL_DH: [] };
const base = { SMA: [], MOM: [], VOL: [] };
const sArr = [], staleFlag = [], eArr = [];
let lastE = null, lastS = null;
for (const m of tradeMonths) {
  const b = sigMap.get(m), v = volMap.get(m);
  assert(b && v !== undefined && es.get(m) !== undefined && csh.get(m) !== undefined, "missing payoff " + m);
  base.SMA.push(b.sma); base.MOM.push(b.mom); base.VOL.push(v);
  let s, e, stale = false;
  if (smap.has(m)) {
    e = E[smap.get(m)]; s = Math.min(1, e / NEUTRAL); lastE = e; lastS = s;
  } else {
    assert(missing.includes(m), "unexpected missing macro " + m);
    assert(lastE !== null && lastS !== null, "no s_last for gap " + m);
    e = null; s = lastS; stale = true; // carry only factor, never future state
  }
  sArr.push(s); staleFlag.push(stale); eArr.push(e === null ? lastE : e);
  assert(s <= 1 + 1e-12 && s >= 0.5 - 1e-12, "s range " + m);
  legs.DH.push((e === null ? lastE : e)); // DH-equity-only holds last known target
  legs.SMA_DH.push(b.sma * s); legs.MOM_DH.push(b.mom * s); legs.VOL_DH.push(v * s);
  assert(legs.SMA_DH.at(-1) <= b.sma + 1e-12 && legs.MOM_DH.at(-1) <= b.mom + 1e-12 && legs.VOL_DH.at(-1) <= v + 1e-12, "w_aug<=w_base violated " + m);
}
assert(staleFlag.filter(Boolean).length === 3, "stale months != 3");

// ---- 6. Backtest (same conventions as baselines) ----
function run(w, fee) {
  return tradeMonths.map((m, i) => {
    const to = i ? Math.abs(w[i] - w[i - 1]) : 0;
    const e = es.get(m), c = csh.get(m);
    return { date: m, weight: w[i], turnover: to, equity: e, cash: c, net: e * w[i] + c * (1 - w[i]) - fee * to, s: sArr[i], stale: staleFlag[i] };
  });
}
function metrics(rs) {
  const n = rs.length, rets = rs.map((x) => x.net), mu = avg(rets);
  const sd = Math.sqrt(rets.reduce((a, r) => a + (r - mu) ** 2, 0) / (n - 1));
  let W = 1, H = 1, dd = 0, worst = Infinity, to = 0, sw = 0, up = 0, dn = 0, upN = 0, dnN = 0, miss = 0, avd = 0;
  for (const x of rs) {
    W *= 1 + x.net; H = Math.max(H, W); dd = Math.min(dd, W / H - 1); worst = Math.min(worst, x.net); to += x.turnover;
    if (x.turnover > 0) sw++;
    if (x.equity > 0) { upN++; up += x.weight; }
    if (x.equity < 0) { dnN++; dn += x.weight; }
    if (x.equity > 0 && x.equity > x.cash) miss += (1 - x.weight) * (x.equity - x.cash);
    if (x.equity < 0 && x.equity < x.cash) avd += (1 - x.weight) * (x.cash - x.equity);
  }
  return { n, first: rs[0].date, last: rs.at(-1).date, cagr: W ** (12 / n) - 1, vol: sd * Math.sqrt(12),
    sharpe_like: sd ? Math.sqrt(12) * avg(rs.map((x) => x.net - x.cash)) / sd : null,
    max_dd: dd, worst_month: worst, avg_equity: avg(rs.map((x) => x.weight)),
    turnover_annual: to * 12 / n, switches: sw,
    part_up: upN ? up / upN : null, part_dn: dnN ? dn / dnN : null,
    missed_pp: miss * 100, avoided_pp: avd * 100, terminal: W };
}
const W8 = {
  BH: tradeMonths.map(() => 1), SMA: base.SMA, MOM: base.MOM, VOL: base.VOL,
  DH: legs.DH, SMA_DH: legs.SMA_DH, MOM_DH: legs.MOM_DH, VOL_DH: legs.VOL_DH,
};
// exposure-matched fixed controls (descriptive hindsight) for the 4 macro legs
for (const k of ["DH", "SMA_DH", "MOM_DH", "VOL_DH"]) W8["MATCH_" + k] = tradeMonths.map(() => avg(W8[k]));
const eras = { E1: ["1967-03", "1979-12"], E2: ["1980-01", "1999-12"], E3: ["2000-01", "2019-12"], E4: ["2020-01", "2026-08"] };
const crises = { "1973-74": ["1973-01", "1974-12"], "1987": ["1987-08", "1987-12"], "2000-02": ["2000-03", "2002-10"], "2007-09": ["2007-10", "2009-03"], "2020": ["2020-02", "2020-04"], "2022": ["2022-01", "2022-12"] };
const sel = (a, lo, hi) => a.filter((x) => ym(x.date) >= ym(lo) && ym(x.date) <= ym(hi));
const sims = {}, res = {};
for (const [k, w] of Object.entries(W8)) {
  const r2 = run(w, FEE), r10 = run(w, FEE10);
  sims[k] = r2;
  res[k] = { full: metrics(r2), fee10bp: metrics(r10),
    eras: Object.fromEntries(Object.entries(eras).map(([e, [lo, hi]]) => [e, metrics(sel(r2, lo, hi))])),
    crises: Object.fromEntries(Object.entries(crises).map(([e, [lo, hi]]) => {
      const s = sel(r2, lo, hi);
      return [e, { ret: s.reduce((p, x) => p * (1 + x.net), 1) - 1, avg_equity: avg(s.map((x) => x.weight)), n: s.length }];
    })) };
}
// 711 observed-macro secondary diagnostic (non-continuous, labelled)
const obsIdx = new Set(tradeMonths.filter((m) => smap.has(m)));
const res711 = {};
for (const [k, w] of Object.entries(W8)) {
  const full = sims[k].filter((x) => obsIdx.has(x.date));
  assert(full.length === 711, "711 subset");
  res711[k] = metrics(full);
}
// ---- 7. Re-entry drag diagnostic (8 #186 troughs, >=95% equity) ----
const evP = parse(EVENTS);
const troughs = evP.rows.map((r) => r.trough.slice(0, 7));
assert(troughs.length === 8, "troughs != 8");
const wSeries = { SMA10: base.SMA, "SMA10+DH": legs.SMA_DH, MOM12: base.MOM, "MOM12+DH": legs.MOM_DH, VolFair: base.VOL, "VolFair+DH": legs.VOL_DH };
const mi = new Map(tradeMonths.map((m, i) => [m, i]));
function firstGE(T) {
  const out = {};
  for (const [k, w] of Object.entries(wSeries)) {
    let m = null;
    for (let i = mi.get(T); i < w.length; i++) if (w[i] >= 0.95) { m = tradeMonths[i]; break; }
    out[k] = m === null ? { lag: null, m: null } : { lag: ym(m) - ym(T), m };
  }
  return out;
}
const reentry = troughs.map((T) => ({ trough: T, legs: firstGE(T) }));
const med = (a) => { const v = a.filter((x) => x !== null).sort((x, y) => x - y); return v.length ? v[v.length >> 1] : null; };
const reSummary = Object.fromEntries(Object.keys(wSeries).map((k) => {
  const lags = reentry.map((r) => r.legs[k].lag);
  return [k, { lags, median: med(lags), never: lags.filter((x) => x === null).length }];
}));
// augmented never earlier than baseline (mechanical check)
for (const [b, a] of [["SMA10", "SMA10+DH"], ["MOM12", "MOM12+DH"], ["VolFair", "VolFair+DH"]]) {
  reentry.forEach((r) => {
    const lb = r.legs[b].lag, la = r.legs[a].lag;
    if (lb !== null && la !== null) assert(la >= lb, "re-entry earlier than baseline at " + r.trough);
  });
}
// ---- 8. Scorecard (descriptive only) ----
function score(aug, bse, match) {
  const A = res[aug].full, B = res[bse].full, M = res[match].full;
  const dS = A.sharpe_like - B.sharpe_like, dD = (A.max_dd - B.max_dd) * 100, dC = (A.cagr - B.cagr) * 100;
  const pass = dS >= 0.02 && dD >= 1.0 && dC >= -0.10 && A.sharpe_like >= M.sharpe_like;
  return { sharpe_diff: dS, maxdd_diff_pp: dD, cagr_diff_pp: dC, sharpe_aug: A.sharpe_like, sharpe_match: M.sharpe_like, pass };
}
const sc = {
  "SMA10+DH": score("SMA_DH", "SMA", "MATCH_SMA_DH"),
  "MOM12+DH": score("MOM_DH", "MOM", "MATCH_MOM_DH"),
  "VolFair+DH": score("VOL_DH", "VOL", "MATCH_VOL_DH"),
};
const npass = Object.values(sc).filter((x) => x.pass).length;
const overall = npass >= 2 ? "descriptively favourable (2/3+ scorecard-PASS; NOT proof of edge)" : npass === 1 ? "mixed (1/3)" : "unfavourable (0/3)";

// ---- 9. Outputs ----
const sha = (f) => crypto.createHash("sha256").update(fs.readFileSync(f)).digest("hex");
const out = { study: "macro_incremental", prereg: "macro_incremental_prereg.md@c984f6d",
  review: ["#6208853986 addressed", "#6211025620 stale-factor carry + 714 primary"],
  panel_primary: { n: 714, first: "1967-03", last: "2026-08", stale_months: missing },
  panel_secondary_711: { n: 711, note: "observed-macro diagnostic only, non-continuous" },
  inputs: { equity_sha: sha(EQUITY), cash_sha: sha(CASHF), matrix_sha: sha(MATRIX), struct_sha: sha(STRUCT), daily_rows: mkeys.length },
  neutral_anchor: NEUTRAL, rule: "Final_w=Baseline_w*min(1,E_DH/0.45); gaps w_aug=w_base*s_last",
  determinism: "single-threaded; rerun must match",
  production_authorized: false,
  results: res, secondary_711: res711, scorecard_descriptive_only: sc, overall_descriptive_only: overall,
  reentry_drag_only: { per_trough: reentry, summary: reSummary, note: "w_aug<=w_base; measures drag, never early re-entry; S&P-dated troughs vs French vehicle ≤2mo mismatch" } };
fs.writeFileSync(path.join(OUT, "macro-incremental-results.json"), JSON.stringify(out, null, 2) + "\n");
const cols = ["date", "signal_month", "equity", "cash", "sma10", "mom12", "volfair", "E_DH", "s_macro", "stale", "dh_only", "sma_dh", "mom_dh", "vol_dh",
  "bh_net", "sma_net", "mom_net", "vol_net", "dh_net", "sma_dh_net", "mom_dh_net", "vol_dh_net"];
const csv = [cols.join(",")];
for (let i = 0; i < tradeMonths.length; i++) {
  const m = tradeMonths[i];
  const sigM = tradeMonths[i].slice(0, 7); // signal month = trade-1 (asserted in §3)
  csv.push([m, sigP.rows[i].signal_month, es.get(m), csh.get(m), base.SMA[i], base.MOM[i], base.VOL[i].toFixed(6),
    eArr[i].toFixed(4), sArr[i].toFixed(6), staleFlag[i] ? 1 : 0, legs.DH[i].toFixed(6),
    legs.SMA_DH[i].toFixed(6), legs.MOM_DH[i].toFixed(6), legs.VOL_DH[i].toFixed(6),
    sims.BH[i].net.toFixed(6), sims.SMA[i].net.toFixed(6), sims.MOM[i].net.toFixed(6), sims.VOL[i].net.toFixed(6),
    sims.DH[i].net.toFixed(6), sims.SMA_DH[i].net.toFixed(6), sims.MOM_DH[i].net.toFixed(6), sims.VOL_DH[i].net.toFixed(6)].join(","));
}
fs.writeFileSync(path.join(OUT, "macro-incremental-monthly.csv"), csv.join("\n") + "\n");
console.log(JSON.stringify({ primary_714: Object.fromEntries(Object.entries(res).map(([k, v]) => [k, { cagr: +v.full.cagr.toFixed(6), sharpe: +v.full.sharpe_like.toFixed(4), dd: +v.full.max_dd.toFixed(4), avgEq: +v.full.avg_equity.toFixed(4) }])), scorecard: sc, overall }, null, 2));
