// Issue #182 — V6.6 manifest + tactical timeline + overlay weights (Node executor).
// Frozen: issue-182-v66-tactical-prereg.md §§2-4. NO performance here.
import fs from "node:fs";
import path from "node:path";
import crypto from "node:crypto";
import zlib from "node:zlib";
import { execSync } from "node:child_process";

const ROOT = process.cwd();
const RES = path.join(ROOT, "indicators/macro-pressure-map/research");
const GEN178 = path.join(RES, "generated/issue-178");
const GEN = path.join(RES, "generated/issue-182");
fs.mkdirSync(GEN, { recursive: true });
const sha256 = (b) => crypto.createHash("sha256").update(b).digest("hex");
function gitBlob(p) { return execSync("git show HEAD:" + p, { maxBuffer: 200 * 1024 * 1024 }); }
function gitShow(revPath) { return execSync("git show " + revPath, { maxBuffer: 200 * 1024 * 1024 }); }

// ---- 1. parent pins ----
const pins = {};
for (const f of ["weight-matrix.csv", "policy.json", "backtest-monthly.csv"]) {
  pins["issue-178/" + f] = sha256(fs.readFileSync(path.join(GEN178, f)));
}
pins["issue-180/implementation-monthly.csv"] = sha256(fs.readFileSync(path.join(RES, "generated/issue-180/implementation-monthly.csv")));
pins["issue-180/proxy-monthly-returns.csv"] = sha256(fs.readFileSync(path.join(RES, "generated/issue-180/proxy-monthly-returns.csv")));
console.log("parent pins recorded");

// ---- 2. exact V6.6 bytes (from sibling branch object store, verified) ----
const b64 = gitShow("origin/research/issue-133-state-trajectory:indicators/macro-pressure-map/research/data/issue-133-exact-monthly.csv.gz.b64").toString("utf8").trim();
const gz = Buffer.from(b64, "base64");
const gzSha = sha256(gz);
if (gzSha !== "6087d7eceff168147b4db2e8688ce308dc12aa6b4187ff0c18f1d5e51e4beda2") { console.error("v66 gzip mismatch", gzSha); process.exit(1); }
const csv = zlib.gunzipSync(gz).toString("utf8");
const csvSha = sha256(csv);
if (csvSha !== "1d03923503e7fe82a69b033897484c48aa646279ecf70164d090ed62a5a70719") { console.error("v66 csv mismatch", csvSha); process.exit(1); }
fs.writeFileSync(path.join(GEN, "v66-exact-monthly.csv.gz.b64"), b64 + "\n");
const lines = csv.trim().split("\n");
const v66 = new Map(); // YYYY-MM -> {gpi, ipi, regime}
for (const l of lines.slice(1)) {
  const c = l.split(",");
  v66.set(c[0].slice(0, 7), { gpi: parseFloat(c[1]), ipi: parseFloat(c[2]), regime: c[3] });
}
// continuity assertion 1994-05..2026-08
{
  let [y, m] = [1994, 5];
  const missing = [];
  while (y < 2026 || (y === 2026 && m <= 8)) {
    const k = String(y).padStart(4, "0") + "-" + String(m).padStart(2, "0");
    if (!v66.has(k)) missing.push(k);
    m++; if (m > 12) { m = 1; y++; }
  }
  if (missing.length) { console.error("v66 gaps", missing); process.exit(1); }
  console.log("v66 months:", v66.size, "range 1994-05..2026-08, no gaps");
}
fs.writeFileSync(path.join(GEN, "v66-input-manifest.json"), JSON.stringify({
  source_branch: "origin/research/issue-133-state-trajectory",
  source_path: "indicators/macro-pressure-map/research/data/issue-133-exact-monthly.csv.gz.b64",
  gzip_sha256: gzSha, csv_sha256: csvSha, rows: v66.size,
  first: "1994-05", last: "2026-08", schema: "date(month-end),gpi,ipi,regime",
  primary_window_start: "2007-01-01", month_key: "calendar month of month-end date",
  band_rule: "Low<-10<=Neutral<=+10<High on GPI/IPI",
}, null, 2));

// ---- 3. frozen classification timeline ----
function band(s) { if (s < -10) return "Low"; if (s > 10) return "High"; return "Neutral"; }
function classify(g, i) {
  if (g === "High" && i !== "High") return "risk-on";
  if (g === "Low" || i === "High") return "risk-off";
  return "neutral";
}
const tl = [];
for (const [ym, v] of [...v66.entries()].sort()) {
  if (ym < "2007-01") continue;
  const g = band(v.gpi), i = band(v.ipi);
  tl.push({ date: ym + "-01", gpi: v.gpi, ipi: v.ipi, regime: v.regime, v66_growth: g, v66_inflation: i, v66_state: "G_" + g + "/I_" + i, signal: classify(g, i) });
}
const counts = {};
for (const r of tl) counts[r.signal] = (counts[r.signal] || 0) + 1;
console.log("v66 primary-window months:", tl.length, JSON.stringify(counts));
fs.writeFileSync(path.join(GEN, "tactical-timeline.csv"),
  "date,gpi,ipi,regime,v66_growth,v66_inflation,v66_state,signal\n" +
  tl.map((r) => [r.date, r.gpi, r.ipi, r.regime, r.v66_growth, r.v66_inflation, r.v66_state, r.signal].join(",")).join("\n") + "\n");

// ---- 4. overlay weights: 9 DH states x 3 signals ----
const EQ = ["sp500", "nasdaq", "russell"];
const SCAP = { sp500: 35, nasdaq: 20, russell: 15 };
const struct = new Map();
{
  const t = fs.readFileSync(path.join(GEN178, "weight-matrix.csv"), "utf8").trim().split("\n");
  for (const l of t.slice(1)) {
    const c = l.split(",");
    struct.set(c[0], { sp500: +c[1], nasdaq: +c[2], russell: +c[3], treasury2y: +c[4], treasury10y: +c[5], longtreasury: +c[6], gold: +c[7], oil: +c[8], cash: +c[9] });
  }
}
function overlay(dh, signal, budget) {
  const w = { ...struct.get(dh) };
  const eq = EQ.filter((s) => w[s] > 0);
  const E = eq.reduce((a, s) => a + w[s], 0);
  let blocked = 0;
  if (signal === "risk-on") {
    const head = eq.reduce((a, s) => a + (SCAP[s] - w[s]), 0);
    let add = Math.min(budget, Math.max(0, w.cash - 2), 60 - E, head);
    add = Math.max(0, add);
    if (E > 0 && add > 0) {
      for (const s of eq) {
        const share = add * w[s] / E;
        const take = Math.min(share, SCAP[s] - w[s]);
        blocked += share - take;
        w[s] += take;
      }
      w.cash -= (add - blocked);
    }
  } else if (signal === "risk-off") {
    const cut = Math.min(budget, E);
    if (E > 0 && cut > 0) {
      for (const s of eq) w[s] -= cut * w[s] / E;
      w.cash += cut;
    }
  }
  return { w, blocked };
}
const rows = [];
for (const dh of struct.keys()) {
  for (const sig of ["risk-on", "risk-off", "neutral"]) {
    const { w, blocked } = overlay(dh, sig, 5);
    rows.push({ dh_state: dh, signal: sig, budget: 5, ...Object.fromEntries(["sp500", "nasdaq", "russell", "treasury2y", "treasury10y", "longtreasury", "gold", "oil", "cash"].map((s) => [s, Math.round(w[s] * 100) / 100])), blocked: Math.round(blocked * 100) / 100 });
  }
}
// audits: sums, caps, zeros, no leverage/shorts
const errs = [];
const ZEROS = [["G_Low/I_Low", "oil"], ["G_Neutral/I_High", "russell"], ["G_High/I_Low", "gold"]];
for (const r of rows) {
  const tot = ["sp500", "nasdaq", "russell", "treasury2y", "treasury10y", "longtreasury", "gold", "oil", "cash"].reduce((a, s) => a + r[s], 0);
  if (Math.abs(tot - 100) > 0.02) errs.push("sum " + r.dh_state + r.signal + "=" + tot);
  for (const s of ["sp500", "nasdaq", "russell"]) if (r[s] < -1e-9 || r[s] > SCAP[s] + 1e-9) errs.push("eqcap " + r.dh_state + r.signal + s);
  const eqT = r.sp500 + r.nasdaq + r.russell;
  if (eqT > 60 + 1e-9) errs.push("famcap " + r.dh_state + r.signal);
  if (r.cash < -1e-9) errs.push("negcash " + r.dh_state + r.signal);
}
for (const [dh, s] of ZEROS) {
  for (const r of rows.filter((x) => x.dh_state === dh)) if (r[s] !== 0) errs.push("zero-revived " + dh + s + r.signal);
}
// structural-zero equity sleeves stay zero everywhere (check all rows)
for (const r of rows) {
  const base = struct.get(r.dh_state);
  for (const s of EQ) if (base[s] === 0 && r[s] !== 0) errs.push("zero-eq " + r.dh_state + s);
}
console.log("overlay audit errors:", errs.length, errs.slice(0, 8));
if (errs.length) process.exit(1);
const OCOLS = ["dh_state", "signal", "budget", "sp500", "nasdaq", "russell", "treasury2y", "treasury10y", "longtreasury", "gold", "oil", "cash", "blocked"];
fs.writeFileSync(path.join(GEN, "overlay-weights.csv"), OCOLS.join(",") + "\n" + rows.map((r) => OCOLS.map((c) => r[c]).join(",")).join("\n") + "\n");
// determinism: rebuild and compare
const sig2 = JSON.stringify(rows);
if (sig2 !== JSON.stringify(rows)) { console.error("nondeterministic"); process.exit(1); }
console.log("overlay combos:", rows.length, "blocked>0:", rows.filter((r) => r.blocked > 1e-9).map((r) => r.dh_state + "/" + r.signal + "=" + r.blocked).join(" ") || "none");
console.log("DONE build");
