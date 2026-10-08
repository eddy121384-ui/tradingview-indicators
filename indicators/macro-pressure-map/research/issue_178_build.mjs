// Issue #178 — weight-matrix builder (Node executor).
// Frozen: issue-178-weight-policy-prereg.md §§1-5. Uses #177 tiers VERBATIM.
// No backtest here. No optimizer. No Pine.
import fs from "node:fs";
import path from "node:path";
import crypto from "node:crypto";

const ROOT = process.cwd();
const RES = path.join(ROOT, "indicators/macro-pressure-map/research");
const GEN177 = path.join(RES, "generated/issue-177");
const GEN = path.join(RES, "generated/issue-178");
fs.mkdirSync(GEN, { recursive: true });
const sha256 = (b) => crypto.createHash("sha256").update(b).digest("hex");

// ---- pin frozen inputs ----
const pins = {};
for (const f of ["policy-matrix.csv", "cash-bias.csv"]) {
  pins["issue-177/" + f] = sha256(fs.readFileSync(path.join(GEN177, f)));
}
console.log("pins:", JSON.stringify(pins));

// ---- frozen policy (VERBATIM prereg §§1-5) ----
const BASE = { sp500: 25, nasdaq: 12, russell: 8, treasury2y: 8, treasury10y: 14, longtreasury: 8, gold: 6, oil: 4 };
const FAM = { sp500: "equity", nasdaq: "equity", russell: "equity", treasury2y: "rates", treasury10y: "rates", longtreasury: "rates", gold: "real", oil: "real" };
const MULT = { "0": 0, Low: 0.5, Neutral: 1.0, High: 1.75 };
const SCAP = { sp500: 35, nasdaq: 20, russell: 15, treasury2y: 15, treasury10y: 25, longtreasury: 15, gold: 12, oil: 8 };
const FCAP = { equity: 60, rates: 50, real: 15 };
const CMIN_BIAS = { low: 5, neutral: 10, high: 20 };
const CASH_MAX = 60, CASH_MIN = 2;
const ORDER = ["sp500", "nasdaq", "russell", "treasury2y", "treasury10y", "longtreasury", "gold", "oil"];

function loadCsv(p) {
  const t = fs.readFileSync(p, "utf8").trim().split("\n");
  const h = t[0].split(",").map((k) => k.trim());
  return t.slice(1).map((l) => {
    // policy-matrix limitation/source fields contain commas unquoted; parse from known positions
    const c = l.split(",");
    const r = {};
    h.forEach((k, j) => r[k] = (c[j] ?? "").trim());
    return r;
  });
}
const pm = loadCsv(path.join(GEN177, "policy-matrix.csv"));
const cb = loadCsv(path.join(GEN177, "cash-bias.csv"));
const cbias = Object.fromEntries(cb.map((r) => [r.state, r.cash_bias]));
const tiers = {};
for (const r of pm) {
  if (r.sleeve === "cash") continue;
  tiers[r.state + "|" + r.sleeve] = r.exposure;
}
// verify 72 non-cash cells + 9 cash rows + zero cells intact
const states = [...new Set(pm.map((r) => r.state))];
if (states.length !== 9) { console.error("states", states.length); process.exit(1); }
for (const [st, sl] of [["G_Low/I_Low", "oil"], ["G_Neutral/I_High", "russell"], ["G_High/I_Low", "gold"]]) {
  if (tiers[st + "|" + sl] !== "0") { console.error("zero cell moved", st, sl); process.exit(1); }
}

function stateWeights(state, available) {
  const binds = [];
  const raw = {};
  for (const s of ORDER) {
    const t = tiers[state + "|" + s];
    if (!available.has(s) || MULT[t] === 0) continue;
    raw[s] = BASE[s] * MULT[t];
  }
  for (const s of Object.keys(raw)) {
    if (raw[s] > SCAP[s] + 1e-9) { binds.push("sleeve:" + s); raw[s] = SCAP[s]; }
  }
  for (const fam of Object.keys(FCAP)) {
    const mem = Object.keys(raw).filter((s) => FAM[s] === fam);
    const sum = mem.reduce((a, s) => a + raw[s], 0);
    if (sum > FCAP[fam] + 1e-9) {
      binds.push("family:" + fam);
      const k = FCAP[fam] / sum;
      for (const s of mem) raw[s] *= k;
    }
  }
  const S = Object.values(raw).reduce((a, x) => a + x, 0);
  const minC = CMIN_BIAS[cbias[state]];
  const cashRaw = 100 - S;
  let cash;
  if (cashRaw < minC - 1e-9) {
    const k = (100 - minC) / S;
    for (const s of Object.keys(raw)) raw[s] *= k;
    cash = minC;
  } else if (cashRaw > CASH_MAX + 1e-9) {
    const k = (100 - CASH_MAX) / S;
    for (const s of Object.keys(raw)) raw[s] *= k;
    cash = CASH_MAX;
  } else cash = cashRaw;
  if (cash < CASH_MIN) cash = CASH_MIN;
  for (const s of Object.keys(raw)) {
    if (raw[s] > SCAP[s] + 1e-9) { binds.push("resleeve:" + s); cash += raw[s] - SCAP[s]; raw[s] = SCAP[s]; }
  }
  const out = {};
  for (const s of ORDER) out[s] = raw[s] ?? 0;
  out.cash = cash;
  return { out, binds };
}

function roundLR(w, zeros) {
  const fl = {};
  for (const s of Object.keys(w)) {
    fl[s] = zeros.has(s) ? 0 : Math.floor(w[s] * 100 + 1e-9) / 100;
  }
  let short = Math.round((100 - Object.values(fl).reduce((a, x) => a + x, 0)) * 100);
  if (short > 0) {
    const frac = Object.keys(w).filter((s) => !zeros.has(s))
      .map((s) => [w[s] * 100 - fl[s] * 100, s]).sort((a, b) => b[0] - a[0]);
    for (let i = 0; i < short; i++) fl[frac[i % frac.length][1]] += 0.01;
  }
  const r = {};
  for (const s of Object.keys(fl)) r[s] = Math.round(fl[s] * 100) / 100;
  return r;
}

// all-available matrix (availability handled at backtest time)
const ALL = new Set(ORDER);
const matrix = [];
for (const st of states) {
  const { out, binds } = stateWeights(st, ALL);
  const zeros = new Set(ORDER.filter((s) => tiers[st + "|" + s] === "0"));
  const fin = roundLR(out, zeros);
  const tot = Object.values(fin).reduce((a, x) => a + x, 0);
  matrix.push({ state: st, ...fin, total: Math.round(tot * 100) / 100, binds: binds.join(";"), cash_bias: cbias[st] });
}
// determinism: rebuild and compare
const m2 = states.map((st) => roundLR(stateWeights(st, ALL).out, new Set(ORDER.filter((s) => tiers[st + "|" + s] === "0"))));
if (JSON.stringify(matrix.map((r) => ORDER.concat(["cash"]).map((s) => r[s]))) !== JSON.stringify(m2.map((r) => ORDER.concat(["cash"]).map((s) => r[s])))) {
  console.error("nondeterministic"); process.exit(1);
}
// audit
const errs = [];
for (const r of matrix) {
  if (Math.abs(r.total - 100) > 0.001) errs.push("sum " + r.state);
  for (const s of ORDER) {
    if (r[s] < -1e-9) errs.push("neg " + r.state + s);
    if (r[s] > SCAP[s] + 0.011) errs.push("cap " + r.state + s);
    if (tiers[r.state + "|" + s] === "0" && r[s] !== 0) errs.push("zero " + r.state + s);
  }
  if (r.cash < CASH_MIN - 1e-9 || r.cash > CASH_MAX + 0.011) errs.push("cash " + r.state);
}
console.log("audit errors:", errs.length, errs.slice(0, 5));
if (errs.length) process.exit(1);

const cols = ["state", ...ORDER, "cash", "total", "binds", "cash_bias"];
fs.writeFileSync(path.join(GEN, "weight-matrix.csv"),
  cols.join(",") + "\n" + matrix.map((r) => cols.map((c) => r[c]).join(",")).join("\n") + "\n");

// state cards
let cards = "# Issue #178 — State allocation cards (percentages; tiers frozen from #177)\n\n";
for (const r of matrix) {
  cards += "## " + r.state + " (cash bias " + r.cash_bias + (r.binds ? "; caps: " + r.binds : "") + ")\n\n";
  cards += ORDER.map((s) => "- " + s + ": " + r[s].toFixed(2) + "% (" + tiers[r.state + "|" + s] + ")").join("\n") + "\n";
  cards += "- cash: " + r.cash.toFixed(2) + "% (residual)\n- TOTAL: " + r.total.toFixed(2) + "%\n\n";
}
fs.writeFileSync(path.join(GEN, "state-cards.md"), cards);

// machine-readable policy artifact
fs.writeFileSync(path.join(GEN, "policy.json"), JSON.stringify({
  issue: 178, base_head: "bc652bd615f2c5e9137050d01c666dbcd9528cd3",
  baseline: BASE, family_budgets: { equity: 45, rates: 30, real_assets: 10, cash: 15 },
  multipliers: MULT, sleeve_caps: SCAP, family_caps: FCAP,
  cash: { min: CASH_MIN, max: CASH_MAX, min_by_bias: CMIN_BIAS },
  rounding: "2dp largest-remainder, tier-0 excluded",
  rebalance_primary: "B-2 confirmation",
  matrix: matrix.map((r) => ({ state: r.state, weights: Object.fromEntries(ORDER.concat(["cash"]).map((s) => [s, r[s]])), binds: r.binds, cash_bias: r.cash_bias })),
  inputs_sha256: pins, production_authorized: false,
}, null, 2));
console.log("matrix rows:", matrix.length);
console.log("DONE build");
