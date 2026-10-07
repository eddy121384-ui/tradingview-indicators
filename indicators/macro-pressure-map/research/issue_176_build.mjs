// Issue #176 — Phase B hardened build (Node executor).
// Frozen methodology: issue-176-allocation-backbone-prereg.md §§3-5.
// Unconditional ONLY: NO macro join, NO state/episode/era cut anywhere here.
import fs from "node:fs";
import path from "node:path";
import crypto from "node:crypto";
import { execSync } from "node:child_process";
import zlib from "node:zlib";

const ROOT = process.cwd();
const RES = path.join(ROOT, "indicators/macro-pressure-map/research");
const GEN174 = path.join(RES, "generated/issue-174");
const GEN = path.join(RES, "generated/issue-176");
fs.mkdirSync(GEN, { recursive: true });

const sha256 = (b) => crypto.createHash("sha256").update(b).digest("hex");
const sleep = (ms) => new Promise((r) => setTimeout(r, ms));
const UA = { "User-Agent": "Mozilla/5.0" };
const UAF = { "User-Agent": "tradingview-indicators-research/1.0" };
const prov = { fetched_at: new Date().toISOString(), sources: {} };
async function fetchBuf(url, headers, retries = 4) {
  let last = null;
  for (let i = 0; i < retries; i++) {
    try {
      const r = await fetch(url, { headers });
      if (!r.ok) throw new Error("HTTP " + r.status);
      return Buffer.from(await r.arrayBuffer());
    } catch (e) { last = e; await sleep(700 * (i + 1)); }
  }
  throw last;
}

// ---- verify frozen #174 inputs (no join) ----
function gitBlob(p) { return execSync("git show HEAD:" + p, { maxBuffer: 100 * 1024 * 1024 }); }
const macroSha = sha256(gitBlob("indicators/macro-pressure-map/research/generated/issue-160/deep-history-v01-monthly.csv"));
if (macroSha !== "42516418ec8d1ce981d1b4bc05e2ae86809d6acbf5de63dccbad515db507dcfc") { console.error("macro blob mismatch"); process.exit(1); }
prov.sources["FROZEN:macro_blob_sha256"] = macroSha;
{
  const b = fs.readFileSync(path.join(GEN174, "nine-sleeve-monthly-returns.csv"));
  prov.sources["FROZEN:issue174_backbone_sha256"] = sha256(b);
}
console.log("frozen inputs verified");

// ---- 1. Yahoo ^GSPC daily 1966-2026 (yearly windows) -> month-end closes ----
const gspcDaily = new Map(); // YYYY-MM-DD -> close
{
  let rawBytes = 0;
  const hashes = [];
  for (let y = 1966; y <= 2026; y++) {
    const p1 = Math.floor(Date.UTC(y, 0, 1) / 1000), p2 = Math.floor(Date.UTC(y + 1, 0, 1) / 1000);
    const url = "https://query1.finance.yahoo.com/v8/finance/chart/" + encodeURIComponent("^GSPC") + "?interval=1d&period1=" + p1 + "&period2=" + p2 + "&events=div%7Csplit";
    const buf = await fetchBuf(url, UA);
    rawBytes += buf.length; hashes.push(sha256(buf));
    const j = JSON.parse(buf.toString("utf8"));
    const res = j.chart?.result?.[0];
    if (res) {
      const cl = res.indicators.quote[0].close;
      res.timestamp.forEach((t, i) => {
        if (cl[i] == null) return;
        gspcDaily.set(new Date(t * 1000).toISOString().slice(0, 10), cl[i]);
      });
    }
    await sleep(150);
  }
  const h = crypto.createHash("sha256"); hashes.forEach((x) => h.update(x));
  prov.sources["Yahoo:^GSPC_daily_1966_2026"] = { windows: 61, raw_bytes_total: rawBytes, chained_sha256: h.digest("hex"), daily_points: gspcDaily.size };
  console.log("^GSPC daily points:", gspcDaily.size);
}
const gspcME = new Map(); // YYYY-MM -> {date, close} last trading day
for (const [d, c] of gspcDaily) {
  const m = d.slice(0, 7);
  if (!gspcME.has(m) || d > gspcME.get(m).date) gspcME.set(m, { date: d, close: c });
}

// ---- 2. Shiller/datahub monthly D ----
let shillerDiv = new Map(), shillerBytes = 0, shillerSha = "";
{
  const buf = await fetchBuf("https://datahub.io/core/s-and-p-500/_r/-/data/data.csv", UA);
  shillerBytes = buf.length; shillerSha = sha256(buf);
  for (const l of buf.toString("utf8").trim().split("\n").slice(1)) {
    const c = l.split(",");
    const d = parseFloat(c[2]);
    if (isFinite(d) && d !== 0) shillerDiv.set(c[0].slice(0, 7), d);
  }
  prov.sources["Shiller:datahub_s-and-p-500"] = { url: "https://datahub.io/core/s-and-p-500/_r/-/data/data.csv", bytes: shillerBytes, sha256: shillerSha, license: "ODC-PDDL-1.0", upstream: "http://www.econ.yale.edu/~shiller/data.htm", div_months_nonzero: shillerDiv.size, note: "dividends zeroed by mirror from 2023-07; recon coverage ends 2023-06 (disclosed truncation)" };
  console.log("shiller div months:", shillerDiv.size);
}

// ---- 3. Yahoo monthly TR series (^SP500TR, ^RUTTR, ^RUT, ^XCMP, CL=F, USO) ----
async function yahooMonthly(s) {
  const url = "https://query1.finance.yahoo.com/v8/finance/chart/" + encodeURIComponent(s) + "?interval=1mo&period1=0&period2=1790976000&events=div%7Csplit";
  const buf = await fetchBuf(url, UA);
  const j = JSON.parse(buf.toString("utf8"));
  const res = j.chart.result[0];
  prov.sources["Yahoo:" + s + "_monthly"] = { bytes: buf.length, sha256: sha256(buf), firstTradeDate: new Date(res.meta.firstTradeDate * 1000).toISOString(), n_points: res.timestamp.length };
  const m = new Map();
  res.timestamp.forEach((t, i) => {
    const d = new Date(t * 1000);
    const ym = d.getUTCFullYear() + "-" + String(d.getUTCMonth() + 1).padStart(2, "0");
    const q = res.indicators.quote[0];
    m.set(ym, { close: q.close[i], adj: res.indicators.adjclose?.[0]?.adjclose?.[i] ?? q.close[i] });
  });
  return m;
}
const sp500trM = await yahooMonthly("^SP500TR");
const rutM = await yahooMonthly("^RUT");
const ruttrM = await yahooMonthly("^RUTTR");
const clfM = await yahooMonthly("CL=F");
const usoM = await yahooMonthly("USO");
// CL=F daily-derived month-ends (fills Yahoo monthly-bar holes, e.g. 2020-03;
// same frozen series: continuous front-month month-end closes).
const clfDailyME = new Map();
{
  for (let y = 2000; y <= 2026; y++) {
    const p1 = Math.floor(Date.UTC(y, 0, 1) / 1000), p2 = Math.floor(Date.UTC(y + 1, 0, 1) / 1000);
    const url = "https://query1.finance.yahoo.com/v8/finance/chart/" + encodeURIComponent("CL=F") + "?interval=1d&period1=" + p1 + "&period2=" + p2 + "&events=div%7Csplit";
    try {
      const buf = await fetchBuf(url, UA);
      const j = JSON.parse(buf.toString("utf8"));
      const res = j.chart?.result?.[0];
      if (res) {
        const cl = res.indicators.quote[0].close;
        res.timestamp.forEach((t, i) => {
          if (cl[i] == null) return;
          const d = new Date(t * 1000);
          const ym = d.getUTCFullYear() + "-" + String(d.getUTCMonth() + 1).padStart(2, "0");
          const cur = clfDailyME.get(ym);
          const ds = d.toISOString().slice(0, 10);
          if (!cur || ds > cur.date) clfDailyME.set(ym, { date: ds, close: cl[i] });
        });
      }
    } catch (e) { console.log("CL=F daily window", y, "FAILED", e.message); }
    await sleep(120);
  }
  prov.sources["Yahoo:CL=F_daily_2000_2026_monthends"] = { months: clfDailyME.size };
  console.log("CL=F daily month-ends:", clfDailyME.size);
}
const clfME = new Map(); // merged: daily-derived preferred, monthly-bar fallback
for (const ym of new Set([...clfDailyME.keys(), ...clfM.keys()])) {
  if (clfDailyME.has(ym)) clfME.set(ym, clfDailyME.get(ym).close);
  else if (clfM.get(ym)?.close != null) clfME.set(ym, clfM.get(ym).close);
}

// ---- 4. FRED dailies (NASDAQCOM, NASDAQXCMP) + TB3MS monthly + MCOILWTICO ref ----
async function fredCsv(id) {
  const buf = await fetchBuf("https://fred.stlouisfed.org/graph/fredgraph.csv?id=" + id, UAF);
  prov.sources["FRED:" + id] = { url: "https://fred.stlouisfed.org/graph/fredgraph.csv?id=" + id, bytes: buf.length, sha256: sha256(buf) };
  return buf.toString("utf8");
}
const nasdD = fredCsvToDailyMonthEnds(await fredCsv("NASDAQCOM"));
const nasxD = fredCsvToDailyMonthEnds(await fredCsv("NASDAQXCMP"));
function fredCsvToDailyMonthEnds(t) {
  const byM = new Map();
  for (const l of t.trim().split("\n").slice(1)) {
    const i = l.indexOf(","); const d = l.slice(0, i), v = l.slice(i + 1).trim();
    if (!v || v === ".") continue;
    byM.set(d.slice(0, 7), { date: d, value: parseFloat(v) });
  }
  return byM;
}
const tb3M = new Map();
for (const l of (await fredCsv("TB3MS")).trim().split("\n").slice(1)) {
  const i = l.indexOf(","); const v = l.slice(i + 1).trim();
  if (v && v !== ".") tb3M.set(l.slice(0, 7), parseFloat(v));
}
// Damodaran (annual cross-check ref)
{
  const buf = await fetchBuf("https://pages.stern.nyu.edu/adamodar/New_Home_Page/datafile/histretSP.html", UA);
  prov.sources["Damodaran:histretSP"] = { bytes: buf.length, sha256: sha256(buf), note: "annual S&P TR cross-check; expected sha 127c772f… (vintage drift disclosed if differs)" };
}
// French ME zip (REJECTED candidate provenance; filenames only, no inflate)
{
  const buf = await fetchBuf("https://mba.tuck.dartmouth.edu/pages/faculty/ken.french/ftp/Portfolios_Formed_on_ME_CSV.zip", UAF);
  const names = [];
  let off = 0;
  while (off + 46 < buf.length) {
    const sig = buf.readUInt32LE(off);
    if (sig === 0x02014b50) {
      const nl = buf.readUInt16LE(off + 28), el = buf.readUInt16LE(off + 30), cl = buf.readUInt16LE(off + 32);
      names.push(buf.slice(off + 46, off + 46 + nl).toString("utf8"));
      off += 46 + nl + el + cl;
    } else if (sig === 0x06054b50) break; else break;
  }
  prov.sources["French:Portfolios_Formed_on_ME"] = { url: "https://mba.tuck.dartmouth.edu/pages/faculty/ken.french/ftp/Portfolios_Formed_on_ME_CSV.zip", bytes: buf.length, sha256: sha256(buf), members: names, verdict: "REJECTED substitute (different small-cap universe; documented, not used)" };
}

// ---- build hardened series ----
function monthList(a, b) {
  const out = []; let [y, m] = a.split("-").map(Number); const [ey, em] = b.split("-").map(Number);
  while (y < ey || (y === ey && m <= em)) { out.push(String(y).padStart(4, "0") + "-" + String(m).padStart(2, "0") + "-01"); m++; if (m > 12) { m = 1; y++; } }
  return out;
}
const calOut = monthList("1966-03", "2026-08");
const calBuild = monthList("1966-02", "2026-08");
const outRows = [];
for (let i = 0; i < calBuild.length; i++) {
  const mo = calBuild[i], ym = mo.slice(0, 7);
  const prev = i > 0 ? calBuild[i - 1].slice(0, 7) : null;
  let spH = NaN;
  if (prev && gspcME.has(prev) && gspcME.has(ym) && shillerDiv.has(ym)) {
    const p0 = gspcME.get(prev).close, p1 = gspcME.get(ym).close;
    spH = p1 / p0 - 1 + (shillerDiv.get(ym) / 12) / p0;
  }
  let oilI = NaN;
  if (prev && clfME.has(prev) && clfME.has(ym) && tb3M.has(prev)) {
    const ex = clfME.get(ym) / clfME.get(prev) - 1;
    oilI = (1 + ex) * (1 + tb3M.get(prev) / 1200) - 1;
  }
  outRows.push({ date: mo, sp500_tr_hardened: spH, oil_investable_return: oilI });
}
const out = outRows.filter((r) => r.date >= "1966-03-01");
fs.writeFileSync(path.join(GEN, "hardened-monthly-returns.csv"),
  "date,sp500_tr_hardened,oil_investable_return\n" + out.map((r) => [r.date, isFinite(r.sp500_tr_hardened) ? r.sp500_tr_hardened : "", isFinite(r.oil_investable_return) ? r.oil_investable_return : ""].join(",")).join("\n") + "\n");

// ---- helpers ----
const fin = (x) => typeof x === "number" && isFinite(x);
function load174() {
  const t = fs.readFileSync(path.join(GEN174, "nine-sleeve-monthly-returns.csv"), "utf8").trim().split("\n");
  const h = t[0].split(",").map((k) => k.trim());
  const m = new Map();
  for (const l of t.slice(1)) { const c = l.split(","); const r = {}; h.forEach((k, j) => r[k] = j === 0 ? c[j] : (c[j] === "" ? NaN : parseFloat(c[j]))); m.set(r.date.slice(0, 7), r); }
  return m;
}
const old174 = load174();
function stats(a, b) {
  const p = a.map((x, i) => [x, b[i]]).filter(([x, y]) => fin(x) && fin(y));
  const n = p.length;
  const ma = p.reduce((s, [x]) => s + x, 0) / n, mb = p.reduce((s, [, y]) => s + y, 0) / n;
  let co = 0, va = 0, vb = 0;
  for (const [x, y] of p) { co += (x - ma) * (y - mb); va += (x - ma) ** 2; vb += (y - mb) ** 2; }
  const sda = Math.sqrt(p.reduce((s, [x]) => s + (x - ma) ** 2, 0) / n) * Math.sqrt(12);
  const sdb = Math.sqrt(p.reduce((s, [, y]) => s + (y - mb) ** 2, 0) / n) * Math.sqrt(12);
  let ca = 1, cb = 1; for (const [x, y] of p) { ca *= 1 + x; cb *= 1 + y; }
  return { n, pearson: co / Math.sqrt(va * vb), mean_a: ma, mean_b: mb, mean_diff_pp: (ma - mb) * 100, vol_a: sda, vol_b: sdb, vol_diff: sda - sdb, cum_a: ca - 1, cum_b: cb - 1, cum_ratio: ca / cb, mae_pp: p.reduce((s, [x, y]) => s + Math.abs(x - y), 0) / n * 100 };
}

// ---- S&P recon QA gate vs ^SP500TR ----
{
  const a = [], b = [];
  for (const r of out) {
    const ym = r.date.slice(0, 7);
    if (fin(r.sp500_tr_hardened) && sp500trM.has(ym) && sp500trM.has(prevYm(ym))) {
      const rt = sp500trM.get(ym).adj / sp500trM.get(prevYm(ym)).adj - 1;
      if (fin(rt)) { a.push(r.sp500_tr_hardened); b.push(rt); }
    }
  }
  function prevYm(ym) { let [y, m] = ym.split("-").map(Number); m--; if (m < 1) { m = 12; y--; } return String(y).padStart(4, "0") + "-" + String(m).padStart(2, "0"); }
  const s = stats(a, b);
  const pass = s.pearson >= 0.99 && (s.mae_pp) <= 0.20 && s.cum_ratio >= 0.90 && s.cum_ratio <= 1.10;
  console.log("SP recon gate:", JSON.stringify(s), "PASS=", pass);
  fs.writeFileSync(path.join(GEN, "qa-comparison.json"), JSON.stringify({ sp500_recon_vs_SP500TR: { ...s, gate: "pear>=0.99 & mae<=0.20pp & cum_ratio in [0.90,1.10]", pass, verdict: pass ? "hardened_with_limitation" : "unresolved_keep_issue174_semantics" } }, null, 2));
}
function prevYm(ym) { let [y, m] = ym.split("-").map(Number); m--; if (m < 1) { m = 12; y--; } return String(y).padStart(4, "0") + "-" + String(m).padStart(2, "0"); }

// ---- old-vs-new unconditional ----
const newMap = new Map(outRows.map((r) => [r.date.slice(0, 7), r]));
function disc(dates, o, n, k = 10) {
  return dates.map((d, i) => ({ date: d, old: o[i], new: n[i], diff: n[i] - o[i] })).filter((r) => fin(r.old) && fin(r.new)).sort((x, y) => Math.abs(y.diff) - Math.abs(x.diff)).slice(0, k);
}
const oldNew = [];
{ // sp500
  const d = [], o = [], n = [];
  for (const r of out) { const ym = r.date.slice(0, 7); const oo = old174.get(ym)?.sp500; if (fin(oo) && fin(r.sp500_tr_hardened)) { d.push(r.date); o.push(oo); n.push(r.sp500_tr_hardened); } }
  const s = stats(n, o);
  oldNew.push({ sleeve: "sp500", old: "french_market_TR", new: "gspc_daily_monthend+shiller_div", coverage_old: "1966-03–2026-08", coverage_new: "1966-03–2023-06", ...s });
  console.log("sp500 old-vs-new:", JSON.stringify({ ...s, top: disc(d, o, n, 3) }));
}
{ // oil spot vs investable (different semantics)
  const d = [], o = [], n = [];
  for (const r of out) { const ym = r.date.slice(0, 7); const oo = old174.get(ym)?.oil; if (fin(oo) && fin(r.oil_investable_return)) { d.push(r.date); o.push(oo); n.push(r.oil_investable_return); } }
  const s = stats(n, o);
  oldNew.push({ sleeve: "oil", old: "wti_spot_proxy", new: "clf_excess+tb3_collateral", coverage_old: "1986-02–2026-08", coverage_new: "2000-09–2026-08", ...s });
  console.log("oil spot-vs-investable:", JSON.stringify({ ...s, top: disc(d, o, n, 3) }));
}
{ // oil investable vs USO QA
  const a = [], b = [];
  for (const r of out) { const ym = r.date.slice(0, 7); if (fin(r.oil_investable_return) && usoM.has(ym) && usoM.has(prevYm(ym))) { const u = usoM.get(ym).adj / usoM.get(prevYm(ym)).adj - 1; if (fin(u)) { a.push(r.oil_investable_return); b.push(u); } } }
  const s = stats(a, b);
  console.log("oil investable vs USO:", JSON.stringify(s), "gate pear>=0.80:", s.pearson >= 0.80);
  const qa = JSON.parse(fs.readFileSync(path.join(GEN, "qa-comparison.json"), "utf8"));
  qa.oil_investable_vs_USO = { ...s, gate: "pear>=0.80", pass: s.pearson >= 0.80 };
  // nasdaq wedge
  const wn = [];
  for (const ym of [...nasdD.keys()].filter((k) => nasxD.has(k)).sort()) { const p = prevYm(ym); if (nasdD.has(p) && nasxD.has(p)) wn.push((nasxD.get(ym).value / nasxD.get(p).value - 1) - (nasdD.get(ym).value / nasdD.get(p).value - 1)); }
  qa.nasdaq_wedge_TR_minus_price_200310plus = { n: wn.length, mean_pp: wn.reduce((s, x) => s + x, 0) / wn.length * 100, ann_pct: wn.reduce((s, x) => s + x, 0) / wn.length * 12 * 100 };
  // russell wedge
  const wr = [];
  for (const ym of [...rutM.keys()].filter((k) => ruttrM.has(k)).sort()) { const p = prevYm(ym); if (rutM.has(p) && ruttrM.has(p)) wr.push((ruttrM.get(ym).adj / ruttrM.get(p).adj - 1) - (rutM.get(ym).close / rutM.get(p).close - 1)); }
  qa.russell_wedge_TR_minus_price_199507plus = { n: wr.length, mean_pp: wr.reduce((s, x) => s + x, 0) / wr.length * 100, ann_pct: wr.reduce((s, x) => s + x, 0) / wr.length * 12 * 100 };
  fs.writeFileSync(path.join(GEN, "qa-comparison.json"), JSON.stringify(qa, null, 2));
}
fs.writeFileSync(path.join(GEN, "old-vs-new-unconditional.csv"),
  "sleeve,old,new,coverage_old,coverage_new,n_overlap,pearson,mean_new_pp_mo,mean_old_pp_mo,mean_diff_pp,vol_new_ann,vol_old_ann,vol_diff,cum_ratio,mae_pp\n" +
  oldNew.map((r) => [r.sleeve, r.old, r.new, r.coverage_old, r.coverage_new, r.n, r.pearson, r.mean_a * 100, r.mean_b * 100, r.mean_diff_pp, r.vol_a, r.vol_b, r.vol_diff, r.cum_ratio, r.mae_pp].join(",")).join("\n") + "\n");

// ---- source-candidate audit ----
const audit = [
  ["sp500", "Yahoo ^GSPC daily month-ends + Shiller D accrual", "S&P 500 TR reconstruction", "1966-03–2023-06", "TR", "SELECTED (hardened_with_limitation pending gate)", "month-end timing; validated 0.9999 vs ^SP500TR"],
  ["sp500", "Yahoo ^SP500TR monthly adjclose", "S&P 500 TR official", "1988-01+", "TR", "QA ONLY (gate benchmark; too short as backbone)"],
  ["sp500", "Fama-French market TR (#174 sp500)", "broad US market TR", "1966-03–2026-08", "TR", "SUPERSEDED for S&P sleeve; retained as broad_market_tr_french reference"],
  ["sp500", "Shiller monthly-average P+D", "S&P TR (avg-price base)", "1871+", "TR", "REJECTED (0.63 corr vs month-end; timing smoothing)"],
  ["sp500", "FRED SP500", "S&P 500 price", "2016+", "price", "REJECTED (no history)"],
  ["nasdaq", "FRED NASDAQCOM month-end price (#174)", "Nasdaq Composite price", "1971-03+", "price", "RETAINED (unresolved_keep; genuine full history)"],
  ["nasdaq", "FRED NASDAQXCMP / Yahoo ^XCMP TR", "Nasdaq Composite TR official", "2003-09-25+", "TR", "QA/wedge ONLY (fails ≤1990 adoption rule; never stitched)"],
  ["nasdaq", "QQQ / Nasdaq-100", "Nasdaq-100 TR", "1999+", "TR", "REJECTED (wrong index; forbidden substitute)"],
  ["russell", "Yahoo ^RUT month-end price (#174)", "Russell 2000 price", "1987-10+", "price", "RETAINED (unresolved_keep; genuine; no backfill)"],
  ["russell", "Yahoo ^RUTTR TR", "Russell 2000 TR official", "1995-06+", "TR", "QA/wedge ONLY (fails ≤1990 adoption rule; never stitched)"],
  ["russell", "IWM", "Russell 2000 ETF TR", "2000+", "TR", "REJECTED (ETF deep-history forbidden)"],
  ["russell", "French ME portfolios", "academic small-cap TR", "1926+", "TR", "REJECTED substitute (different universe; documented)"],
  ["oil", "FRED MCOILWTICO spot (#174 proxy)", "WTI spot price", "1986-02+", "price", "RETAINED as oil_price_proxy (separate; never stitched)"],
  ["oil", "CL=F excess + TB3MS collateral (new)", "WTI futures investable TR", "2000-09+", "TR", "SELECTED as oil_investable_return (hardened_with_limitation pending gate)"],
  ["oil", "USO", "oil fund TR", "2006+", "TR", "QA ONLY"],
];
fs.writeFileSync(path.join(GEN, "source-candidate-audit.csv"),
  "sleeve,candidate,semantics,coverage,return_type,status,note\n" + audit.map((r) => r.map((c) => '"' + c + '"').join(",")).join("\n") + "\n");
fs.writeFileSync(path.join(GEN, "provenance.json"), JSON.stringify(prov, null, 2));
console.log("DONE build");
