#!/usr/bin/env node
// Issue #189 I3/I4/I5 re-verify — frozen analysis (prereg addendum).
// C1 extreme points, C2 alt-I ledger + pairing, C3 revision spreads,
// C4 old-vs-new decomposition, verdicts. Macro-only. No returns.
import fs from "node:fs";
import path from "node:path";

const ROOT = process.cwd();
const RES = path.join(ROOT, "indicators/macro-pressure-map/research");
const GEN2B = path.join(RES, "generated/issue-189/phase2b");
const SCRATCH = "C:\\Users\\EDDY\\AppData\\Local\\Temp\\opencode\\issue189p2b";
const fin = (x) => typeof x === "number" && Number.isFinite(x);
// pressure_score mirror (verified vs frozen Python maxdiff 2.6e-13 in Phase 2)
function meanSd(a) {
  const m = a.reduce((x, y) => x + y, 0) / a.length;
  return [m, Math.sqrt(a.reduce((x, y) => x + (y - m) ** 2, 0) / a.length)];
}
function lastValid(xs, i, n) {
  const o = [];
  for (let k = i; k >= 0 && o.length < n; k--) if (fin(xs[k])) o.unshift(xs[k]);
  return o;
}
function pressureScore(xs) {
  const out = new Array(xs.length).fill(NaN);
  for (let i = 0; i < xs.length; i++) {
    if (!fin(xs[i])) continue;
    const lv = lastValid(xs, i, 60);
    if (lv.length < 60) continue;
    const [mL, sL] = meanSd(lv);
    if (sL === 0) continue;
    const d1 = fin(xs[i - 1]) ? xs[i] - xs[i - 1] : NaN;
    const d3 = fin(xs[i - 3]) ? xs[i] - xs[i - 3] : NaN;
    if (!fin(d1) || !fin(d3)) continue;
    const momRaw = 0.6 * d1 + 0.4 * (d3 / 3);
    const mv = [];
    for (let j = 0; j <= i; j++) {
      if (fin(xs[j]) && fin(xs[j - 1]) && fin(xs[j - 3])) mv.push(0.6 * (xs[j] - xs[j - 1]) + 0.4 * ((xs[j] - xs[j - 3]) / 3));
    }
    const mw = mv.slice(-60);
    if (mw.length < 60) continue;
    const [mM, sM] = meanSd(mw);
    if (sM === 0) continue;
    const s3 = lastValid(xs, i, 3), s12 = lastValid(xs, i, 12);
    if (s3.length < 3 || s12.length < 12) continue;
    out[i] = 100 * Math.tanh((0.5 * ((xs[i] - mL) / sL) + 0.3 * ((momRaw - mM) / sM) + 0.2 * Math.tanh(((s3.reduce((a, x) => a + x, 0) / 3) - (s12.reduce((a, x) => a + x, 0) / 12)) / sL)) / 2);
  }
  return out;
}
const band = (x) => (x < -10 ? "Low" : x > 10 ? "High" : "Neutral");
const addM = (ym, k) => {
  let y = +ym.slice(0, 4), m = +ym.slice(5, 7) + k;
  while (m > 12) { m -= 12; y++; }
  while (m < 1) { m += 12; y--; }
  return `${y}-${String(m).padStart(2, "0")}`;
};
function loadCols(key) {
  const p = path.join(SCRATCH, key + ".jsonl");
  if (!fs.existsSync(p)) return []; // missing pull set (e.g. I3_SOP: no ALFRED vintages) -> UNVERIFIED path
  return fs.readFileSync(p, "utf8").trim().split("\n").filter(Boolean).map((l) => {
    const o = JSON.parse(l);
    const obs = {};
    for (const r of o.rows) {
      const c = r.split(",");
      const v = parseFloat(c[1]);
      if (c[0] && fin(v)) obs[c[0].slice(0, 7)] = v;
    }
    return { vd: o.vd, obs };
  });
}
const COLS = { I3_SOP: loadCols("I3_SOP"), I3_FD: loadCols("I3_FD"), I4_PAY: loadCols("I4_PAY"), I5_NSA: loadCols("I5_NSA") };
console.log("cols:", Object.entries(COLS).map(([k, v]) => `${k}:${v.length}`).join(" "));
const SOP_MISSING = COLS.I3_SOP.length === 0;
if (SOP_MISSING) console.log("NOTE I3_SOP columns absent (no ALFRED vintages; see no-vintage.json): C1-SOP UNVERIFIED, C2 full-swap not identifiable");
// latest-wins value for obs m as of decision D from a column list
function asofVal(cols, m, D) {
  let best = null;
  for (const { vd, obs } of cols) {
    if (vd > D) continue;
    if (m in obs && (best === null || vd >= best[0])) best = [vd, obs[m]];
  }
  return best; // [vd, value] or null
}
const yoyAt = (cols, m, D) => {
  const a = asofVal(cols, m, D), b = asofVal(cols, addM(m, -12), D);
  if (!a || !b || b[1] === 0) return null;
  return { v: 100 * (a[1] - b[1]) / b[1], vd: a[0] > b[0] ? a[0] : b[0] };
};
// ---- C1 extreme points (first eligible vintage values)
const TV = {
  I3_SOP_1974_11: 19.57, I3_FD_2009_07: -6.86,
  I4_2020_04: -5.89, I4_2021_04: 15.28,
  I5_1980_03: 47.13, I5_2009_07: -28.09,
};
const C1 = {};
{
  // earliest decision whose vintage set can see the extreme month: use first vintage covering it
  const firstCover = (cols, m) => {
    const cands = [];
    for (const { vd, obs } of cols) if (m in obs && addM(m, -12) in obs) cands.push(vd);
    cands.sort();
    return cands.length ? cands[0] : null;
  };
  const at = (cols, m) => {
    const vd = firstCover(cols, m);
    if (!vd) return { value: null, vintage: null };
    const a = asofVal(cols, m, vd), b = asofVal(cols, addM(m, -12), vd);
    return { value: 100 * (a[1] - b[1]) / b[1], vintage: vd };
  };
  C1.I3_SOP_1974_11 = SOP_MISSING ? { tv: TV.I3_SOP_1974_11, value: null, vintage: null } : { tv: TV.I3_SOP_1974_11, ...at(COLS.I3_SOP, "1974-11") };
  C1.I3_FD_2009_07 = { tv: TV.I3_FD_2009_07, ...at(COLS.I3_FD, "2009-07") };
  C1.I4_2020_04 = { tv: TV.I4_2020_04, ...at(COLS.I4_PAY, "2020-04") };
  C1.I4_2021_04 = { tv: TV.I4_2021_04, ...at(COLS.I4_PAY, "2021-04") };
  C1.I5_1980_03 = { tv: TV.I5_1980_03, ...at(COLS.I5_NSA, "1980-03") };
  C1.I5_2009_07 = { tv: TV.I5_2009_07, ...at(COLS.I5_NSA, "2009-07") };
  for (const [k, r] of Object.entries(C1)) r.diff_pp = r.value === null ? null : +(r.value - r.tv).toFixed(3);
}
console.log("C1:", JSON.stringify(C1, null, 0).slice(0, 900));
// ---- C2 alt-I ledger: swap I3/I4/I5 inputs, same clock/warmup/engine
const STALE = JSON.parse(fs.readFileSync(path.join(RES, "generated/issue-189/phase2/staleness.json"), "utf8")).rows;
const REV = {};
for (const l of fs.readFileSync(path.join(RES, "generated/issue-160/deep-history-v01-monthly.csv"), "utf8").replace(/\r/g, "").trim().split("\n").slice(1)) {
  const c = l.split(",");
  const g = parseFloat(c[1]), v = parseFloat(c[2]);
  if (fin(g) && fin(v)) REV[c[0].slice(0, 7)] = { G: g, I: v };
}
// old-candidate as-of I series not stored; rebuild old I3/I4/I5 YoY from Phase 2 scratch for the same decisions
const OLDSCRATCH = "C:\\Users\\EDDY\\AppData\\Local\\Temp\\opencode\\issue189pit";
const OLDSID = { I3: "PPIACO", I4: "AHETPI", I5: "CPIENGSL" };
const OLDCOLS = {};
for (const [r, sid] of Object.entries(OLDSID)) {
  const p = path.join(OLDSCRATCH, sid + ".jsonl");
  OLDCOLS[r] = fs.readFileSync(p, "utf8").trim().split("\n").filter(Boolean).map((l) => {
    const o = JSON.parse(l);
    const obs = {};
    for (const x of o.rows) {
      const c = x.split(",");
      const v = parseFloat(c[1]);
      if (c[0] && fin(v)) obs[c[0].slice(0, 7)] = v;
    }
    return { vd: o.vd, obs };
  });
}
// I1/I2 as-of YoY from Phase 2 scratch (same values the frozen ledger used)
const P2SCRATCH = OLDSCRATCH;
const P2SID = { I1: "CPIAUCSL", I2: "PCEPILFE" };
const P2COLS = {};
for (const [r, sid] of Object.entries(P2SID)) {
  const p = path.join(P2SCRATCH, sid + ".jsonl");
  P2COLS[r] = fs.readFileSync(p, "utf8").trim().split("\n").filter(Boolean).map((l) => {
    const o = JSON.parse(l);
    const obs = {};
    for (const x of o.rows) {
      const c = x.split(",");
      const v = parseFloat(c[1]);
      if (c[0] && fin(v)) obs[c[0].slice(0, 7)] = v;
    }
    return { vd: o.vd, obs };
  });
}
const yoyColsAt = (cols, m, D) => {
  let ba = null;
  for (const { vd, obs } of cols) {
    if (vd > D) continue;
    if (m in obs && addM(m, -12) in obs && obs[addM(m, -12)] !== 0 && (ba === null || vd >= ba[0])) ba = [vd, obs];
  }
  if (!ba) return null;
  return 100 * (ba[1][m] - ba[1][addM(m, -12)]) / ba[1][addM(m, -12)];
};
// monthly history builder for a role YoY series ending at common (75 obs)
function histFor(yoyFn, common, D) {
  const out = [];
  let y = +common.slice(0, 4), m = +common.slice(5, 7);
  const ms = [];
  for (let k = 0; k < 75; k++) {
    ms.unshift(`${y}-${String(m).padStart(2, "0")}`);
    m--;
    if (m < 1) { m = 12; y--; }
  }
  for (const mm of ms) {
    const v = yoyFn(mm, D);
    out.push(v === null || v === undefined ? NaN : v);
  }
  return { months: ms, X: out };
}
const newI3 = (m, D) => {
  if (SOP_MISSING && m < "2014-01") return undefined; // no SOP vintages: pre-2014 new-I3 unbuildable
  return (m < "2014-01" ? yoyColsAt(COLS.I3_SOP, m, D) : yoyColsAt(COLS.I3_FD, m, D));
};
const newI4 = (m, D) => yoyColsAt(COLS.I4_PAY, m, D);
const newI5 = (m, D) => yoyColsAt(COLS.I5_NSA, m, D);
const oldI3 = (m, D) => yoyColsAt(OLDCOLS.I3, m, D);
const oldI4 = (m, D) => yoyColsAt(OLDCOLS.I4, m, D);
const oldI5 = (m, D) => yoyColsAt(OLDCOLS.I5, m, D);
const keepI12 = (m, D) => yoyColsAt(P2COLS.I1, m, D);
const keepI22 = (m, D) => yoyColsAt(P2COLS.I2, m, D);
function scoreI(seriesList, common) {
  // seriesList: 5 arrays aligned to months grid ending at common; score at common
  const sc = seriesList.map((X) => pressureScore(X));
  const li = sc[0].length - 1;
  const v = sc.map((s) => s[li]);
  if (!v.every(fin)) return null;
  return v.reduce((a, x) => a + x, 0) / 5;
}
const altRows = [], oldRows = [];
let C2;
if (SOP_MISSING) {
  // Frozen stop rule: without the SOP leg the pre-2014 new-I3 series cannot be
  // built, so the specified full-swap C2 ledger is not identifiable. Recorded,
  // not approximated (no partial-swap variant: would violate the frozen spec).
  C2 = { status: "not-identifiable", reason: "I3_SOP has no ALFRED vintages (see no-vintage.json); pre-2014 new-I3 unbuildable; C2 full-swap ledger withheld" };
  console.log("C2:", JSON.stringify(C2));
} else {
for (const s of STALE) {
  const D = s.decision, common = s.common_obs;
  if (!common) continue;
  const mk = (fn) => histFor(fn, common, D);
  const hN3 = mk(newI3), hN4 = mk(newI4), hN5 = mk(newI5);
  const hO3 = mk(oldI3), hO4 = mk(oldI4), hO5 = mk(oldI5);
  const hK1 = mk(keepI12), hK2 = mk(keepI22);
  const scN = scoreI([hK1.X, hK2.X, hN3.X, hN4.X, hN5.X], common);
  const scO = scoreI([hK1.X, hK2.X, hO3.X, hO4.X, hO5.X], common);
  const rv = REV[common];
  altRows.push({ D, common, I: scN, band: scN === null ? null : band(scN), rev: rv ? rv.I : null, revBand: rv ? band(rv.I) : null });
  oldRows.push({ D, common, I: scO, band: scO === null ? null : band(scO), rev: rv ? rv.I : null, revBand: rv ? band(rv.I) : null });
}
const agree = (rows) => {
  const p = rows.filter((r) => r.band && r.revBand);
  return { n: p.length, agree: p.filter((r) => r.band === r.revBand).length };
};
const C2 = SOP_MISSING ? { status: "not-identifiable", reason: "I3_SOP has no ALFRED vintages (see no-vintage.json); pre-2014 new-I3 unbuildable; C2 full-swap ledger withheld" } : (() => {
const aN = agree(altRows), aO = agree(oldRows);
let selDis = 0, bothDis = 0, bothN = 0;
for (let i = 0; i < altRows.length; i++) {
  const a = altRows[i], o = oldRows[i];
  if (!a.revBand || !o.revBand || !a.band || !o.band) continue;
  bothN++;
  if (a.band !== o.band) selDis++;
  if (a.band !== a.revBand && o.band !== o.revBand) bothDis++;
}
return { alt: { ...aN, pct: +(100 * aN.agree / Math.max(1, aN.n)).toFixed(1) }, old: { ...aO, pct: +(100 * aO.agree / Math.max(1, aO.n)).toFixed(1) }, decomposition: { comparable_months: bothN, selection_effect_upper: selDis, genuine_revision_lower: bothDis } };
})();
console.log("C2:", JSON.stringify(C2));
} // end else (SOP_MISSING guard opened above)
// ---- C3 revision spreads (same benchmark grid as Phase 2 YoY analysis)
const BENCH = [];
{ let y = 2002, m = 1; while (y < 2026 || (y === 2026 && m <= 1)) { BENCH.push(`${y}-${String(m).padStart(2, "0")}`); m += 12; if (m > 12) { m -= 12; y++; } } }
function spreads(cols) {
  return BENCH.map((b) => {
    const vals = [];
    for (const { vd, obs } of cols) {
      if (obs[b] !== undefined && obs[addM(b, -12)] !== undefined && obs[addM(b, -12)] !== 0) vals.push(100 * (obs[b] - obs[addM(b, -12)]) / obs[addM(b, -12)]);
    }
    if (vals.length < 2) return { obs: b, n: vals.length };
    return { obs: b, n: vals.length, spread_pp: +(Math.max(...vals) - Math.min(...vals)).toFixed(3) };
  });
}
const C3 = {};
for (const [k, cols] of [["I3_SOP", COLS.I3_SOP], ["I3_FD", COLS.I3_FD], ["I4_PAY", COLS.I4_PAY], ["I5_NSA", COLS.I5_NSA]]) {
  const rows = spreads(cols);
  const sp = rows.filter((r) => r.spread_pp !== undefined).map((r) => r.spread_pp).sort((a, b) => a - b);
  C3[k] = { median_spread_pp: sp.length ? +sp[sp.length >> 1].toFixed(3) : null, max_spread_pp: sp.length ? Math.max(...sp) : null };
}
console.log("C3:", JSON.stringify(C3));
// ---- verdicts (frozen rules)
const V = {};
const c1ok = (r) => r.value !== null && Math.abs(r.value - r.tv) < 0.5;
V.I3 = c1ok(C1.I3_SOP_1974_11) && c1ok(C1.I3_FD_2009_07) ? "CONFIRMED" : "UNVERIFIED";
V.I4 = c1ok(C1.I4_2020_04) && c1ok(C1.I4_2021_04) ? "CONFIRMED" : "UNVERIFIED";
V.I5 = c1ok(C1.I5_1980_03) && c1ok(C1.I5_2009_07) ? "CONFIRMED" : "UNVERIFIED";
console.log("verdicts:", JSON.stringify(V));
fs.mkdirSync(path.join(RES, "generated/issue-189/phase2b"), { recursive: true });
const W = (n, c) => fs.writeFileSync(path.join(RES, "generated/issue-189/phase2b", n), c);
const J = (o) => JSON.stringify(o, null, 1) + "\n";
W("extreme-points.json", J(C1));
W("alt-ledger.json", J(altRows));
W("comparison.json", J(C2));
W("revision-spreads.json", J(C3));
W("verdicts.json", J({ roles: V, tv_extremes: { I3_SOP_1974_11: 19.57, I3_FD_2009_07: -6.86, I4_2020_04: -5.89, I4_2021_04: 15.28, I5_1980_03: 47.13, I5_2009_07: -28.09 }, production_authorized: false }));
console.log("wrote phase2b outputs");
