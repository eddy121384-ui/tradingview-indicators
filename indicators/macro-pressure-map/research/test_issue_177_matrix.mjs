// Issue #177 — independent acceptance / consistency test suite.
//
// Verifies the generated policy artifacts against the FROZEN #174 / #176 inputs
// with an independent re-implementation (own CSV reader, own state episodes, own
// quantile/compound helpers). It does NOT import the builder.
//
// Covers the 18 acceptance criteria and the 15 internal consistency checks of
// Issue #177, plus a hard determinism test (rebuild + byte-compare).
//
// Run from anywhere:  node indicators/macro-pressure-map/research/test_issue_177_matrix.mjs
import fs from "node:fs";
import path from "node:path";
import crypto from "node:crypto";
import assert from "node:assert";
import { execFileSync } from "node:child_process";
import { fileURLToPath } from "node:url";

const RES = path.dirname(fileURLToPath(import.meta.url));
const ROOT = path.resolve(RES, "../../..");
const GEN = path.join(RES, "generated/issue-177");
const G174 = path.join(RES, "generated/issue-174");
const G176 = path.join(RES, "generated/issue-176");
const sha256 = (b) => crypto.createHash("sha256").update(b).digest("hex");

let passed = 0; const failures = [];
function ok(name, fn) {
  try { fn(); passed++; }
  catch (e) { failures.push(name + " :: " + e.message); }
}

// ---------------------------------------------------------------- own CSV reader
function readCsv(p) {
  const text = fs.readFileSync(p, "utf8").replace(/\r\n/g, "\n").trim();
  const lines = text.split("\n").filter((l) => l.trim() !== "");
  const header = lines[0].split(",").map((k) => k.trim());
  return lines.slice(1).map((l) => {
    const c = l.split(",");
    const o = {};
    header.forEach((k, i) => { o[k] = (c[i] === undefined ? "" : c[i].trim()); });
    return o;
  });
}
const num = (v) => (v === "" || v === undefined ? NaN : parseFloat(v));

// ---------------------------------------------------------------- own stats helpers
const fin = (x) => typeof x === "number" && isFinite(x);
const mean = (a) => { const v = a.filter(fin); return v.length ? v.reduce((s, x) => s + x, 0) / v.length : NaN; };
function pct(a, q) {
  const v = a.filter(fin).slice().sort((x, y) => x - y);
  if (!v.length) return NaN;
  if (v.length === 1) return v[0];
  const pos = q * (v.length - 1), lo = Math.floor(pos), hi = Math.ceil(pos);
  return lo === hi ? v[lo] : v[lo] * (hi - pos) + v[hi] * (pos - lo);
}
const compound = (rs) => { let p = 1; for (const r of rs) { if (!fin(r)) return NaN; p *= 1 + r; } return p - 1; };
const band = (s) => (s < -10 ? "Low" : s > 10 ? "High" : "Neutral");
const stateOf = (g, i) => "G_" + band(g) + "/I_" + band(i);
const calNext = (mo) => { let y = +mo.slice(0, 4), m = +mo.slice(5, 7) + 1; if (m > 12) { m = 1; y++; } return String(y).padStart(4, "0") + "-" + String(m).padStart(2, "0") + "-01"; };
const STATES = []; for (const g of ["Low", "Neutral", "High"]) for (const i of ["Low", "Neutral", "High"]) STATES.push("G_" + g + "/I_" + i);
const NONCASH = ["sp500", "nasdaq", "russell", "treasury2y", "treasury10y", "longtreasury", "gold", "oil"];
const ALL_SLEEVES = ["sp500", "nasdaq", "russell", "cash", "treasury2y", "treasury10y", "longtreasury", "gold", "oil"];

// macro + independent state episodes
const macro = new Map();
for (const r of readCsv(path.join(RES, "generated/issue-160/deep-history-v01-monthly.csv"))) {
  const g = num(r.growth_dh), i = num(r.inflation_dh);
  if (fin(g) && fin(i)) macro.set(r.date, { g, i });
}
const macroMonths = [...macro.keys()].filter((d) => d >= "1966-03-01" && d <= "2026-08-01").sort();
const macroStates = macroMonths.map((d) => stateOf(macro.get(d).g, macro.get(d).i));
const episodes = [];
{
  let s = 0;
  for (let k = 1; k < macroMonths.length; k++) {
    if (macroStates[k] === macroStates[s] && calNext(macroMonths[k - 1]) === macroMonths[k]) continue;
    episodes.push({ start: macroMonths[s], end: macroMonths[k - 1], state: macroStates[s] });
    s = k;
  }
  episodes.push({ start: macroMonths[s], end: macroMonths[macroMonths.length - 1], state: macroStates[s] });
}

// monthly series (independent)
const series174 = readCsv(path.join(G174, "nine-sleeve-monthly-returns.csv"));
const series176 = readCsv(path.join(G176, "hardened-monthly-returns.csv"));
const h176 = new Map(series176.map((r) => [r.date.slice(0, 7), r]));
const rows = [];
for (const r of series174) {
  const m = macro.get(r.date);
  if (!m) continue;
  const n = h176.get(r.date.slice(0, 7)) || {};
  const o = { date: r.date, state: stateOf(m.g, m.i), cash: num(r.cash) };
  for (const sl of ALL_SLEEVES) o[sl] = num(r[sl]);
  o.sp500_tr_hardened = num(n.sp500_tr_hardened);
  o.oil_investable_return = num(n.oil_investable_return);
  rows.push(o);
}

// independent policy-relevant statistics for any series getter
function stats(state, get) {
  const obs = rows.filter((o) => o.state === state && fin(get(o)) && fin(o.cash));
  const ex = obs.map((o) => get(o) - o.cash);
  const nM = obs.length;
  const meanEx = mean(ex), p10ex = pct(ex, 0.10);
  const pMat = nM ? ex.filter((e) => e < -0.02).length / nM : NaN;
  const eps = episodes.filter((e) => e.state === state);
  let worstEp = NaN, wStart = "", wEnd = "", nE = 0;
  for (const e of eps) {
    const em = []; let d = e.start;
    while (true) { const o = rows.find((x) => x.date === d); if (o && fin(get(o)) && fin(o.cash)) em.push(o); if (d === e.end) break; d = calNext(d); }
    if (!em.length) continue;
    nE++;
    const Rs = compound(em.map(get));
    if (fin(Rs) && (!fin(worstEp) || Rs < worstEp)) { worstEp = Rs; wStart = e.start; wEnd = e.end; }
  }
  const keep = obs.filter((o) => !(wStart && o.date >= wStart && o.date <= wEnd));
  const exWorst = keep.length ? mean(keep.map((o) => get(o) - o.cash)) : NaN;
  return { nM, nE, meanEx, p10ex, pMat, worstEp, exWorst };
}
// episode-excess hit rate needs its own pass over episodes
function hitRate(state, get) {
  const eps = episodes.filter((e) => e.state === state);
  const Re = [];
  for (const e of eps) {
    const em = []; let d = e.start;
    while (true) { const o = rows.find((x) => x.date === d); if (o && fin(get(o)) && fin(o.cash)) em.push(o); if (d === e.end) break; d = calNext(d); }
    if (!em.length) continue;
    const Rs = compound(em.map(get)), Rc = compound(em.map((o) => o.cash));
    if (fin(Rs) && fin(Rc)) Re.push((1 + Rs) / (1 + Rc) - 1);
  }
  return Re.length ? Re.filter((r) => r > 0).length / Re.length : NaN;
}
function fullStats(state, get) { const s = stats(state, get); s.epHit = hitRate(state, get); return s; }

// frozen #174/#176 evidence tables (independent reads)
const ev174 = new Map(readCsv(path.join(G174, "evidence-classification.csv")).map((r) => [r.state + "|" + r.sleeve, r]));
const dg174 = new Map(readCsv(path.join(G174, "downside-danger.csv")).map((r) => [r.state + "|" + r.sleeve, r]));
const zero174 = new Map(readCsv(path.join(G174, "future-zero-candidates.csv")).map((r) => [r.state + "|" + r.sleeve, r]));
const sens176 = new Map(readCsv(path.join(G176, "affected-state-sensitivity.csv")).map((r) => [r.state + "|" + r.sleeve, r]));
const inv176 = new Map(readCsv(path.join(G176, "oil-investable-state-cells.csv")).map((r) => [r.state, r]));

// frozen policy rules (independent implementation)
function frozenTier(evidence, meanEx, flagA, b) {
  if (evidence === "historically_favored") return "High";
  if (evidence === "historically_unfavorable") return (flagA || b) ? "0" : "Low";
  if (evidence === "mixed") return (fin(meanEx) && meanEx >= 0) ? "Neutral" : "Low";
  if (evidence === "insufficient_sample") return "Neutral";
  throw new Error("unknown evidence " + evidence);
}
function pathB(evidence, meanEx, epHit, p10ex, worstEp, pMat, exWorst) {
  if (evidence !== "historically_unfavorable") return false;
  if (!(fin(meanEx) && meanEx < 0)) return false;
  if (!(fin(epHit) && epHit <= 0.40)) return false;
  if (!((fin(p10ex) && p10ex <= -0.04) || (fin(worstEp) && worstEp <= -0.15) || (fin(pMat) && pMat >= 0.10))) return false;
  return fin(exWorst) && exWorst < 0;
}
const POINTS = { High: 2, Neutral: 1, Low: 0, "0": -1 };
const cashBias = (s) => (s <= 3 ? "high" : s <= 8 ? "neutral" : "low");

// frozen policy input per cell, taken ONLY from frozen files (matrix independent)
function frozenInput(state, sleeve) {
  if (sleeve === "sp500") {
    const r = sens176.get(state + "|sp500");
    const s = fullStats(state, (o) => o.sp500_tr_hardened);
    return { evidence: r.ev_new, meanEx: num(r.ex_new), epHit: num(r.hit_new), p10ex: s.p10ex, worstEp: s.worstEp, pMat: s.pMat, exWorst: s.exWorst, flagA: r.zero_new === "true" };
  }
  if (sleeve === "oil") {
    const r = inv176.get(state);
    const s = fullStats(state, (o) => o.oil_investable_return);
    return { evidence: r.evidence, meanEx: num(r.meanEx), epHit: num(r.epHit), p10ex: s.p10ex, worstEp: s.worstEp, pMat: s.pMat, exWorst: s.exWorst, flagA: r.zero_candidate === "true" };
  }
  const e = ev174.get(state + "|" + sleeve), d = dg174.get(state + "|" + sleeve), z = zero174.get(state + "|" + sleeve);
  return { evidence: e.evidence, meanEx: num(e.mean_ex), epHit: num(e.ep_hit), p10ex: num(d.p10_ex), worstEp: num(d.worst_episode), pMat: num(d.p_material_monthly), exWorst: num(e.ex_worst_mean_ex), flagA: z.future_zero_weight_candidate === "true" };
}

// ---------------------------------------------------------------- artifacts
const matrix = readCsv(path.join(GEN, "policy-matrix.csv"));
const cashRows = readCsv(path.join(GEN, "cash-bias.csv"));
const zeroAudit = readCsv(path.join(GEN, "zero-audit.csv"));
const conf = readCsv(path.join(GEN, "confidence.csv"));
const sens = readCsv(path.join(GEN, "sensitivity-common-sample.csv"));
const summary = JSON.parse(fs.readFileSync(path.join(GEN, "summary.json"), "utf8"));
const cards = fs.readFileSync(path.join(GEN, "state-cards.md"), "utf8");
const cell = (st, sl) => matrix.find((r) => r.state === st && r.sleeve === sl);
const NC = matrix.filter((r) => r.sleeve !== "cash");
const MATRIX_CASH = matrix.filter((r) => r.sleeve === "cash");

// ---------------------------------------------------------------- 1. structure
ok("1 all 9 states x 9 sleeves present exactly once (72 non-cash cells + 9 Cash rows)", () => {
  assert.strictEqual(matrix.length, 81, "matrix rows " + matrix.length);
  for (const st of STATES) for (const sl of ALL_SLEEVES) {
    const m = matrix.filter((r) => r.state === st && r.sleeve === sl);
    assert.strictEqual(m.length, 1, "dup/missing " + st + "|" + sl);
  }
  for (const r of NC) assert.notStrictEqual(r.exposure, "residual", r.state + "|" + r.sleeve + " non-cash must carry a tier");
  for (const r of MATRIX_CASH) assert.strictEqual(r.exposure, "residual", r.state + " cash exposure");
  assert.strictEqual(cashRows.length, 9, "cash rows " + cashRows.length);
  assert.deepStrictEqual([...new Set(cashRows.map((r) => r.state))].sort(), [...STATES].sort());
});
ok("2 every non-cash exposure is exactly one of 0/Low/Neutral/High", () => {
  for (const r of NC) assert.ok(["0", "Low", "Neutral", "High"].includes(r.exposure), "bad tier " + r.exposure + " " + r.state + "|" + r.sleeve);
});
ok("3 Cash is residual with role/score/bias and never classified against itself", () => {
  for (const r of cashRows) {
    assert.strictEqual(r.cash_role, "residual");
    assert.ok(["high", "neutral", "low"].includes(r.cash_bias));
    assert.ok(/^\d+$/.test(r.opportunity_score));
  }
  // The 9x9 matrix itself must carry the Cash row with its role, score, bias,
  // confidence and limitation note - not just cash-bias.csv.
  assert.strictEqual(MATRIX_CASH.length, 9, "cash rows inside policy-matrix.csv");
  for (const r of MATRIX_CASH) {
    const cr = cashRows.find((x) => x.state === r.state);
    assert.ok(cr, "cash-bias row for " + r.state);
    assert.strictEqual(r.cash_role, "residual", r.state + " matrix cash_role");
    assert.strictEqual(num(r.opportunity_score), num(cr.opportunity_score), r.state + " matrix opportunity_score");
    assert.strictEqual(r.cash_bias, cr.cash_bias, r.state + " matrix cash_bias");
    assert.strictEqual(r.confidence, "full", r.state + " cash confidence");
    assert.ok(r.limitation.length > 5, r.state + " cash limitation note");
    assert.strictEqual(r.source.length > 0, true, r.state + " cash source");
  }
});

// ---------------------------------------------------------------- 2. deterministic re-derivation
ok("4 every tier re-derives from frozen #174/#176 inputs under the frozen rules", () => {
  for (const st of STATES) for (const sl of NONCASH) {
    const inp = frozenInput(st, sl);
    const b = pathB(inp.evidence, inp.meanEx, inp.epHit, inp.p10ex, inp.worstEp, inp.pMat, inp.exWorst);
    const want = frozenTier(inp.evidence, inp.meanEx, inp.flagA, b);
    const got = cell(st, sl).exposure;
    assert.strictEqual(got, want, st + "|" + sl + " got " + got + " want " + want + " (ev=" + inp.evidence + " meanEx=" + inp.meanEx + " flagA=" + inp.flagA + " B=" + b + ")");
  }
});
ok("5 matrix evidence / mean_ex / ep_hit agree with the frozen sources", () => {
  for (const st of STATES) for (const sl of NONCASH) {
    const inp = frozenInput(st, sl), r = cell(st, sl);
    assert.strictEqual(r.evidence, inp.evidence, st + "|" + sl + " evidence");
    assert.ok(Math.abs(num(r.mean_ex) - inp.meanEx) < 1e-12, st + "|" + sl + " mean_ex");
    assert.ok(Math.abs(num(r.ep_hit) - inp.epHit) < 1e-12, st + "|" + sl + " ep_hit");
  }
});
ok("6 #176 S&P / investable-oil tail statistics reproduce independently from raw returns", () => {
  for (const st of STATES) {
    for (const [sl, get, src] of [["sp500", (o) => o.sp500_tr_hardened, sens176.get(st + "|sp500")], ["oil", (o) => o.oil_investable_return, inv176.get(st)]]) {
      const s = fullStats(st, get), r = cell(st, sl);
      assert.ok(Math.abs(num(r.mean_ex) - s.meanEx) < 1e-12, st + "|" + sl + " meanEx " + num(r.mean_ex) + " vs " + s.meanEx);
      assert.ok(Math.abs(num(r.ep_hit) - s.epHit) < 1e-12, st + "|" + sl + " epHit");
      assert.ok(Math.abs(num(r.p10_ex) - s.p10ex) < 1e-12, st + "|" + sl + " p10ex");
      assert.ok(Math.abs(num(r.worst_ep) - s.worstEp) < 1e-12, st + "|" + sl + " worstEp");
      assert.ok(Math.abs(num(r.p_material) - s.pMat) < 1e-12, st + "|" + sl + " pMat");
      assert.ok(Math.abs(num(r.ex_worst_mean_ex) - s.exWorst) < 1e-12, st + "|" + sl + " exWorst");
      const nRef = sl === "sp500" ? num(src.n_new) : num(src.n);
      assert.strictEqual(num(r.n_months), nRef, st + "|" + sl + " n_months");
    }
  }
});
ok("7 #174 non-hardened cells still take their frozen tail inputs unchanged", () => {
  for (const st of STATES) for (const sl of NONCASH) {
    if (sl === "sp500" || sl === "oil") continue;
    const d = dg174.get(st + "|" + sl), e = ev174.get(st + "|" + sl), r = cell(st, sl);
    assert.ok(Math.abs(num(r.p10_ex) - num(d.p10_ex)) < 1e-12, st + "|" + sl + " p10_ex");
    assert.ok(Math.abs(num(r.worst_ep) - num(d.worst_episode)) < 1e-12, st + "|" + sl + " worst_ep");
    assert.ok(Math.abs(num(r.p_material) - num(d.p_material_monthly)) < 1e-12, st + "|" + sl + " p_material");
    assert.ok(Math.abs(num(r.ex_worst_mean_ex) - num(e.ex_worst_mean_ex)) < 1e-12, st + "|" + sl + " ex_worst");
  }
});

// ---------------------------------------------------------------- 3. zero audit
ok("8 every zero cell satisfies condition A or B (audited independently)", () => {
  const zeros = NC.filter((r) => r.exposure === "0");
  assert.strictEqual(zeros.length, zeroAudit.length, "zero-audit row count");
  for (const r of zeros) {
    const inp = frozenInput(r.state, r.sleeve);
    const b = pathB(inp.evidence, inp.meanEx, inp.epHit, inp.p10ex, inp.worstEp, inp.pMat, inp.exWorst);
    assert.ok(inp.flagA || b, r.state + "|" + r.sleeve + " zero without A or B");
    assert.strictEqual(r.future_zero_candidate, String(inp.flagA), r.state + "|" + r.sleeve + " flagA column");
    assert.ok(r.zero_rule_path === "A" || r.zero_rule_path === "B");
    assert.ok(r.zero_rule_reason.length > 5, "zero reason recorded");
  }
  for (const a of zeroAudit) assert.ok(["A", "B"].includes(a.zero_rule_path) && a.zero_rule_reason.length > 5, "audit row " + a.state + "|" + a.sleeve);
});
ok("9 no zero exists outside the frozen zero rule; no unfavorable cell is High", () => {
  for (const r of NC) {
    const inp = frozenInput(r.state, r.sleeve);
    const b = pathB(inp.evidence, inp.meanEx, inp.epHit, inp.p10ex, inp.worstEp, inp.pMat, inp.exWorst);
    if (r.exposure === "0") assert.ok(inp.flagA || b);
    if (inp.evidence === "historically_unfavorable") assert.notStrictEqual(r.exposure, "High", r.state + "|" + r.sleeve + " unfavorable High");
  }
});
ok("10 insufficient_sample cells are never High and never 0 (low_confidence set)", () => {
  for (const r of NC) {
    if (r.evidence === "insufficient_sample") {
      assert.ok(r.exposure === "Neutral", r.state + "|" + r.sleeve + " insufficient -> " + r.exposure);
      assert.strictEqual(r.low_confidence, "true", r.state + "|" + r.sleeve + " low_confidence");
    } else assert.strictEqual(r.low_confidence, "false");
  }
});

// ---------------------------------------------------------------- 4. cash
ok("11 opportunity score and cash bias recompute from the eight non-cash tiers", () => {
  for (const cr of cashRows) {
    const st = cr.state;
    const score = NONCASH.reduce((s, sl) => s + POINTS[cell(st, sl).exposure], 0);
    assert.strictEqual(num(cr.opportunity_score), score, st + " score " + cr.opportunity_score + " vs " + score);
    assert.strictEqual(cr.cash_bias, cashBias(score), st + " bias");
  }
  assert.strictEqual(cashBias(3), "high"); assert.strictEqual(cashBias(4), "neutral");
  assert.strictEqual(cashBias(8), "neutral"); assert.strictEqual(cashBias(9), "low");
});

// ---------------------------------------------------------------- 5. provenance / limitations
ok("12 confidence mapping is exactly: limited for sp500/nasdaq/russell/oil", () => {
  const limited = ["sp500", "nasdaq", "russell", "oil"];
  for (const r of NC) assert.strictEqual(r.confidence, limited.includes(r.sleeve) ? "limited" : "full", r.state + "|" + r.sleeve);
  assert.strictEqual(conf.length, 72);
  for (const r of NC) {
    const c = conf.find((x) => x.state === r.state && x.sleeve === r.sleeve);
    assert.ok(c, "confidence row missing");
    assert.strictEqual(c.confidence, r.confidence);
    assert.ok(c.limitation.replace(/^"|"$/g, "").length > 5, "limitation recorded");
  }
});
ok("13 Nasdaq and Russell price-only limitations are explicit in every artifact", () => {
  for (const sl of ["nasdaq", "russell"]) {
    for (const st of STATES) {
      const r = cell(st, sl);
      assert.strictEqual(r.confidence, "limited");
      assert.ok(/price-only/.test(r.limitation), st + "|" + sl + " limitation text");
      assert.ok(/dividends excluded/.test(r.limitation), st + "|" + sl + " dividend note");
    }
    assert.ok(cards.includes(sl + " (limited)"));
  }
  assert.ok(/price-only/.test(cards));
  assert.ok(/price-only/.test(fs.readFileSync(path.join(GEN, "confidence.csv"), "utf8")));
});
ok("14 S&P and Oil sources record the hardened #176 provenance", () => {
  for (const st of STATES) {
    assert.strictEqual(cell(st, "sp500").source, "#176 hardened S&P TR");
    assert.strictEqual(cell(st, "oil").source, "#176 investable oil");
    assert.strictEqual(cell(st, "sp500").evidence, sens176.get(st + "|sp500").ev_new);
    assert.strictEqual(cell(st, "oil").evidence, inv176.get(st).evidence);
  }
});

// ---------------------------------------------------------------- 6. sensitivity
ok("15 common-sample sensitivity table is complete and flags match the primary matrix", () => {
  assert.strictEqual(sens.length, 72, "sensitivity rows");
  for (const s of sens) {
    const prim = cell(s.state, s.sleeve).exposure;
    assert.strictEqual(s.primary, prim, s.state + "|" + s.sleeve + " primary");
    assert.strictEqual(s.changed, String(s.primary !== s.implied), s.state + "|" + s.sleeve + " changed flag");
    assert.strictEqual(s.policy_sensitive, s.changed);
    assert.strictEqual(cell(s.state, s.sleeve).policy_sensitive, s.changed, s.state + "|" + s.sleeve + " primary policy_sensitive");
  }
  const changed = sens.filter((s) => s.changed === "true");
  assert.strictEqual(changed.length, summary.sensitivity.changed_cells);
  assert.strictEqual(summary.sensitivity.compared_cells, 72);
  assert.strictEqual(summary.policy_sensitive_cells.length, changed.length);
  for (const c of changed) assert.ok(["0", "Low", "Neutral", "High"].includes(c.implied), "implied tier domain");
});

// ---------------------------------------------------------------- 7. boundaries
ok("16 no percentages / weights / optimizer / leverage / shorts; production not authorized", () => {
  assert.strictEqual(summary.percentages_assigned, false);
  assert.strictEqual(summary.optimizer_used, false);
  assert.strictEqual(summary.production_authorized, false);
  assert.strictEqual(summary.trajectory_used, false);
  assert.strictEqual(summary.v6_6_used, false);
  assert.strictEqual(summary.manual_overrides, false);
  for (const k of Object.keys(matrix[0])) assert.ok(!/weight|percent|leverage|short_pos|alloc/i.test(k), "forbidden column " + k);
  for (const f of ["policy-matrix.csv", "cash-bias.csv", "zero-audit.csv", "confidence.csv", "sensitivity-common-sample.csv"]) {
    const header = fs.readFileSync(path.join(GEN, f), "utf8").split("\n")[0];
    assert.ok(!/weight|percent|alloc|leverage|short/i.test(header), "forbidden column in " + f + ": " + header);
  }
  assert.ok(!/\b\d+(\.\d+)?%\b/.test(matrix.map((r) => r.exposure).join(",")), "percentage symbol in exposure domain");
});
ok("17 no trajectory and no V6.6 inputs anywhere in the baseline", () => {
  for (const r of matrix) { assert.ok(!/traj/i.test(r.source)); assert.ok(!/v6/i.test(r.source)); }
  for (const k of Object.keys(matrix[0])) { assert.ok(!/traj/i.test(k)); assert.ok(!/v6/i.test(k)); }
  assert.ok(!/traj/i.test(Object.keys(summary.inputs).join(" ")));
  assert.ok(!/v6/i.test(Object.keys(summary.inputs).join(" ")));
});
ok("18 frozen policy-rule boundary behaviour (negative controls)", () => {
  assert.strictEqual(frozenTier("historically_favored", -1, false, false), "High");
  assert.strictEqual(frozenTier("historically_unfavorable", -1, false, false), "Low");
  assert.strictEqual(frozenTier("mixed", 0, false, false), "Neutral");
  assert.strictEqual(frozenTier("mixed", -1e-9, false, false), "Low");
  assert.strictEqual(frozenTier("insufficient_sample", 5, true, true), "Neutral");
  assert.strictEqual(pathB("historically_unfavorable", -0.01, 0.40, -0.04, 0, 0, -1e-9), true);
  assert.strictEqual(pathB("historically_unfavorable", -0.01, 0.41, -0.04, 0, 0, -1e-9), false);
  assert.strictEqual(pathB("historically_unfavorable", 0.01, 0.30, -0.04, 0, 0, -1e-9), false);
  assert.strictEqual(pathB("mixed", -0.01, 0.30, -0.04, 0, 0, -1e-9), false);
  assert.strictEqual(pathB("historically_unfavorable", -0.01, 0.30, -0.01, -0.01, 0.01, -1e-9), false);
  assert.strictEqual(pathB("historically_unfavorable", -0.01, 0.30, -0.04, 0, 0, 1e-9), false);
});

// ---------------------------------------------------------------- 8. summary + determinism
ok("19 summary.json is internally consistent with the artifacts", () => {
  assert.strictEqual(summary.issue, 177);
  assert.strictEqual(summary.base_head, "5d596047e1da5531f43190bad761a79a8b3ac342");
  assert.strictEqual(summary.prereg_commit, "8fb864ef1a7925235153679f2a2e83220f4f6d18");
  assert.strictEqual(summary.self_check_gate.mismatches, 0);
  assert.strictEqual(summary.panel_coverage_assertion.pass, true);
  assert.strictEqual(summary.percentages_assigned, false);
  assert.ok(summary.checks.length >= 15 && summary.checks.every((c) => c.pass === true), "all builder checks pass");
  assert.strictEqual(matrix.length, 81, "9 states x 9 sleeves in policy-matrix.csv");
  const counts = { High: 0, Neutral: 0, Low: 0, "0": 0 };
  for (const r of NC) counts[r.exposure]++;
  assert.deepStrictEqual(summary.tier_counts, counts, "tier counts");
  assert.strictEqual(counts.High + counts.Neutral + counts.Low + counts["0"], 72);
  assert.strictEqual(summary.zero_cells.length, counts["0"]);
  assert.strictEqual(summary.total_non_cash_cells, 72);
  assert.strictEqual(summary.total_cells ?? 81, 81);
  assert.ok(MATRIX_CASH.every((r) => r.cash_role === "residual"), "cash rows serialised in the 9x9 matrix");
  for (const z of summary.zero_cells) assert.ok(/^[AB]:/.test(z.reason), "zero reason");
  assert.strictEqual(Object.keys(summary.inputs).length, 12);
  for (const [p, v] of Object.entries(summary.inputs)) assert.strictEqual(v.head_blob_sha256, v.worktree_normalised_sha256, "input pin " + p);
});
ok("20 determinism: rebuild reproduces byte-identical artifacts (CRLF-normalised)", () => {
  // The builder always writes LF. Git may check text files out as CRLF
  // (core.autocrlf), so compare canonical LF content: this is stable across
  // clone settings while still proving the builder is a pure function of its inputs.
  const hash = (p) => sha256(Buffer.from(fs.readFileSync(p, "utf8").replace(/\r\n/g, "\n"), "utf8"));
  const files = ["policy-matrix.csv", "cash-bias.csv", "zero-audit.csv", "confidence.csv", "sensitivity-common-sample.csv", "state-cards.md", "summary.json"];
  const before = Object.fromEntries(files.map((f) => [f, hash(path.join(GEN, f))]));
  execFileSync(process.execPath, [path.join(RES, "issue_177_build.mjs")], { cwd: ROOT, stdio: "pipe" });
  for (const f of files) assert.strictEqual(hash(path.join(GEN, f)), before[f], "artifact changed on rerun: " + f);
  for (const [f, h] of Object.entries(summary.artifact_hashes)) assert.strictEqual(hash(path.join(GEN, f)), h, "hash manifest mismatch " + f);
});

// ---------------------------------------------------------------- report
const total = passed + failures.length;
if (failures.length) {
  console.error("issue-177 acceptance tests: " + passed + "/" + total + " PASS");
  for (const f of failures) console.error("  FAIL " + f);
  process.exit(1);
}
console.log("issue-177 acceptance tests: " + passed + "/" + total + " PASS (independent re-derivation + determinism)");
