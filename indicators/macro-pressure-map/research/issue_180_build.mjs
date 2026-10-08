// Issue #180 — proxy fetch + tracking study (Node executor).
// Frozen: issue-180-implementation-prereg.md §§1-3,8. UNCONDITIONAL ONLY:
// no state cut, no portfolio result here.
import fs from "node:fs";
import path from "node:path";
import crypto from "node:crypto";

const ROOT = process.cwd();
const RES = path.join(ROOT, "indicators/macro-pressure-map/research");
const GEN174 = path.join(RES, "generated/issue-174");
const GEN176 = path.join(RES, "generated/issue-176");
const GEN = path.join(RES, "generated/issue-180");
fs.mkdirSync(GEN, { recursive: true });
const sha256 = (b) => crypto.createHash("sha256").update(b).digest("hex");
const sleep = (ms) => new Promise((r) => setTimeout(r, ms));
const UA = { "User-Agent": "Mozilla/5.0" };
const UAF = { "User-Agent": "tradingview-indicators-research/1.0" };
const fin = (x) => typeof x === "number" && isFinite(x);
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

// ---- 1. Yahoo monthly adjclose proxies ----
const PROXIES = {
  sp500: { ticker: "SPY", er: "0.0945%", inception: "1993-01-29" },
  nasdaq: { ticker: "QQQ", er: "0.20%", inception: "1999-03-10", label: "Nasdaq-100 proxy (NOT Composite)" },
  nasdaq_alt: { ticker: "ONEQ", er: "0.21%", inception: "2003-09-25", label: "genuine Nasdaq Composite ETF" },
  russell: { ticker: "IWM", er: "0.19%", inception: "2000-05-22" },
  treasury2y: { ticker: "SHY", er: "0.15%", inception: "2002-07-22" },
  treasury10y: { ticker: "IEF", er: "0.15%", inception: "2002-07-22" },
  longtreasury: { ticker: "TLT", er: "0.15%", inception: "2002-07-30" },
  gold: { ticker: "GLD", er: "0.40%", inception: "2004-11-18" },
  oil: { ticker: "USO", er: "0.60%", inception: "2006-04-10", label: "front-month WTI fund; laddered since Apr-2020" },
};
const monthly = {}; // key -> Map ym -> adjclose
for (const [k, p] of Object.entries(PROXIES)) {
  const url = "https://query1.finance.yahoo.com/v8/finance/chart/" + encodeURIComponent(p.ticker) + "?interval=1mo&period1=0&period2=1790976000&events=div%7Csplit";
  const buf = await fetchBuf(url, UA);
  prov.sources["Yahoo:" + p.ticker] = { bytes: buf.length, sha256: sha256(buf), ticker: p.ticker, er: p.er, inception: p.inception };
  const j = JSON.parse(buf.toString("utf8"));
  const res = j.chart.result[0];
  const m = new Map();
  res.timestamp.forEach((t, i) => {
    const d = new Date(t * 1000);
    const a = res.indicators.adjclose?.[0]?.adjclose?.[i];
    if (a != null) m.set(d.getUTCFullYear() + "-" + String(d.getUTCMonth() + 1).padStart(2, "0"), a);
  });
  monthly[k] = m;
  console.log(p.ticker, "bars:", m.size);
}
// FRED NASDAQCOM + NASDAQXCMP dailies (wedge reference / option-2 quantification)
async function fredDailyMonthEnds(id) {
  const buf = await fetchBuf("https://fred.stlouisfed.org/graph/fredgraph.csv?id=" + id, UAF);
  prov.sources["FRED:" + id] = { bytes: buf.length, sha256: sha256(buf) };
  const byM = new Map();
  for (const l of buf.toString("utf8").trim().split("\n").slice(1)) {
    const i = l.indexOf(","); const d = l.slice(0, i), v = l.slice(i + 1).trim();
    if (v && v !== ".") byM.set(d.slice(0, 7), parseFloat(v));
  }
  return byM;
}
const nasPrice = await fredDailyMonthEnds("NASDAQCOM");
const nasTR = await fredDailyMonthEnds("NASDAQXCMP");

// ---- 2. research sleeve month-end levels/returns ----
function loadRet(p) {
  const t = fs.readFileSync(p, "utf8").trim().split("\n");
  const h = t[0].split(",").map((k) => k.trim());
  const m = new Map();
  for (const l of t.slice(1)) {
    const c = l.split(","); const r = {};
    h.forEach((k, j) => r[k] = j === 0 ? c[j] : (c[j] === "" ? NaN : parseFloat(c[j])));
    m.set(r.date.slice(0, 7), r);
  }
  return m;
}
const r174 = loadRet(path.join(GEN174, "nine-sleeve-monthly-returns.csv"));
const r176 = loadRet(path.join(GEN176, "hardened-monthly-returns.csv"));
function prevYm(ym) { let [y, m] = ym.split("-").map(Number); m--; if (m < 1) { m = 12; y--; } return String(y).padStart(4, "0") + "-" + String(m).padStart(2, "0"); }
function proxyRet(m, ym) {
  if (!m.has(ym) || !m.has(prevYm(ym))) return NaN;
  const a = m.get(ym), b = m.get(prevYm(ym));
  return (a == null || b == null || b === 0) ? NaN : a / b - 1;
}
// research sleeve return getters (monthly returns as stored)
function researchRet(sl, ym) {
  if (sl === "sp500") { const v = r176.get(ym)?.sp500_tr_hardened; return fin(v) ? v : NaN; }
  if (sl === "oil") { const v = r176.get(ym)?.oil_investable_return; return fin(v) ? v : NaN; }
  if (sl === "cash") { const v = r174.get(ym)?.cash; return fin(v) ? v : NaN; }
  const v = r174.get(ym)?.[sl];
  return fin(v) ? v : NaN;
}

// ---- 3. implementation-monthly.csv (proxy returns; cash = research T-bill) ----
function monthList(a, b) {
  const out = []; let [y, m] = a.split("-").map(Number); const [ey, em] = b.split("-").map(Number);
  while (y < ey || (y === ey && m <= em)) { out.push(String(y).padStart(4, "0") + "-" + String(m).padStart(2, "0") + "-01"); m++; if (m > 12) { m = 1; y++; } }
  return out;
}
const PROXY_OF = { sp500: "sp500", nasdaq: "nasdaq", russell: "russell", treasury2y: "treasury2y", treasury10y: "treasury10y", longtreasury: "longtreasury", gold: "gold", oil: "oil" };
const rows = [];
for (const mo of monthList("1993-01", "2026-08")) {
  const ym = mo.slice(0, 7);
  const r = { date: mo };
  for (const [sl, pk] of Object.entries(PROXY_OF)) r[sl] = proxyRet(monthly[pk], ym);
  r.cash = researchRet("cash", ym);
  r.nasdaq_alt = proxyRet(monthly.nasdaq_alt, ym);
  rows.push(r);
}
const ICOLS = ["date", "sp500", "nasdaq", "russell", "treasury2y", "treasury10y", "longtreasury", "gold", "oil", "cash", "nasdaq_alt"];
fs.writeFileSync(path.join(GEN, "proxy-monthly-returns.csv"),
  ICOLS.join(",") + "\n" + rows.map((r) => {
    const ym = r.date.slice(0, 7);
    const alt = monthly.nasdaq_alt.has(ym) && monthly.nasdaq_alt.has(prevYm(ym))
      ? monthly.nasdaq_alt.get(ym) / monthly.nasdaq_alt.get(prevYm(ym)) - 1 : NaN;
    return ICOLS.map((c) => {
      if (c === "date") return r.date;
      if (c === "nasdaq_alt") return fin(alt) ? alt : "";
      return fin(r[c]) ? r[c] : "";
    }).join(",");
  }).join("\n") + "\n");

// ---- 4. tracking study (unconditional) ----
function compound(rs) { let p = 1; for (const r of rs) p *= 1 + r; return p - 1; }
function track(sl, researchFn, extraNote) {
  const P = [], R = [], DD = [];
  const yms = [...monthly[{ sp500: "sp500", nasdaq: "nasdaq", russell: "russell", treasury2y: "treasury2y", treasury10y: "treasury10y", longtreasury: "longtreasury", gold: "gold", oil: "oil" }[sl]].keys()].sort();
  for (const ym of yms) {
    const p = proxyRet(monthly[{ sp500: "sp500", nasdaq: "nasdaq", russell: "russell", treasury2y: "treasury2y", treasury10y: "treasury10y", longtreasury: "longtreasury", gold: "gold", oil: "oil" }[sl]], ym);
    const r = researchFn(ym);
    if (fin(p) && fin(r)) { P.push(p); R.push(r); DD.push({ ym, d: p - r }); }
  }
  const n = P.length;
  const mp = P.reduce((a, x) => a + x, 0) / n, mr = R.reduce((a, x) => a + x, 0) / n;
  let co = 0, va = 0, vb = 0;
  for (let i = 0; i < n; i++) { co += (P[i] - mp) * (R[i] - mr); va += (P[i] - mp) ** 2; vb += (R[i] - mr) ** 2; }
  const md = DD.reduce((a, x) => a + x.d, 0) / n;
  const te = Math.sqrt(DD.reduce((a, x) => a + (x.d - md) ** 2, 0) / n) * Math.sqrt(12);
  const cp = compound(P), cr = compound(R);
  const annDiff = ((1 + cp) / (1 + cr)) ** (12 / n) - 1;
  DD.sort((a, b) => Math.abs(b.d) - Math.abs(a.d));
  return {
    sleeve: sl, proxy: PROXIES[{ sp500: "sp500", nasdaq: "nasdaq", russell: "russell", treasury2y: "treasury2y", treasury10y: "treasury10y", longtreasury: "longtreasury", gold: "gold", oil: "oil" }[sl]].ticker,
    n, first: DD.length ? [...DD].sort((a, b) => a.ym < b.ym ? -1 : 1)[0].ym : "", last: DD.length ? [...DD].sort((a, b) => a.ym < b.ym ? -1 : 1)[DD.length - 1].ym : "",
    corr: co / Math.sqrt(va * vb), mean_diff_pp: md * 100,
    ann_ret_diff_pp: annDiff * 100,
    te_vol_pct: te * 100, worst_diff_pp: Math.min(...DD.map((x) => x.d)) * 100,
    cum_ratio: (1 + cp) / (1 + cr),
    top3: DD.slice(0, 3).map((x) => x.ym + ":" + (x.d * 100).toFixed(2) + "pp").join(" "),
    note: extraNote,
  };
}
const tres = [
  track("sp500", (ym) => researchRet("sp500", ym), "SPY vs hardened S&P recon"),
  track("nasdaq", (ym) => { const p = prevYm(ym); if (!nasPrice.has(ym) || !nasPrice.has(p)) return NaN; return nasPrice.get(ym) / nasPrice.get(p) - 1; }, "QQQ(Nasdaq-100) vs Composite PRICE; mismatch labeled"),
  track("russell", (ym) => researchRet("russell", ym), "IWM vs RUT price"),
  track("treasury2y", (ym) => researchRet("treasury2y", ym), "SHY vs synth 2Y"),
  track("treasury10y", (ym) => researchRet("treasury10y", ym), "IEF vs synth 10Y"),
  track("longtreasury", (ym) => researchRet("longtreasury", ym), "TLT vs synth 20Y"),
  track("gold", (ym) => researchRet("gold", ym), "GLD vs Pink Sheet"),
  track("oil", (ym) => researchRet("oil", ym), "USO vs investable CL+collateral"),
];
// QQQ vs official TR (^XCMP via FRED) 2003+ for option-2 quantification
{
  const P = [], R = [];
  const yms = [...monthly.nasdaq.keys()].filter((ym) => nasTR.has(ym) && nasTR.has(prevYm(ym))).sort();
  for (const ym of yms) {
    const p = proxyRet(monthly.nasdaq, ym);
    const r = nasTR.get(ym) / nasTR.get(prevYm(ym)) - 1;
    if (fin(p) && fin(r)) { P.push(p); R.push(r); }
  }
  const mp = P.reduce((a, x) => a + x, 0) / P.length, mr = R.reduce((a, x) => a + x, 0) / R.length;
  let co = 0, va = 0, vb = 0;
  for (let i = 0; i < P.length; i++) { co += (P[i] - mp) * (R[i] - mr); va += (P[i] - mp) ** 2; vb += (R[i] - mr) ** 2; }
  tres.push({ sleeve: "nasdaq_vs_TR", proxy: "QQQ", n: P.length, first: yms[0], last: yms[yms.length - 1], corr: co / Math.sqrt(va * vb), mean_diff_pp: (mp - mr) * 100, ann_ret_diff_pp: "", te_vol_pct: "", worst_diff_pp: "", cum_ratio: "", top3: "", note: "QQQ vs official Composite TR (option-2 gap)" });
  // ONEQ vs Composite price (alternate proxy QA)
  const Q = [], S = [];
  const y2 = [...monthly.nasdaq_alt.keys()].filter((ym) => nasPrice.has(ym) && nasPrice.has(prevYm(ym))).sort();
  for (const ym of y2) {
    const p = proxyRet(monthly.nasdaq_alt, ym);
    const r = nasPrice.get(ym) / nasPrice.get(prevYm(ym)) - 1;
    if (fin(p) && fin(r)) { Q.push(p); S.push(r); }
  }
  const mq = Q.reduce((a, x) => a + x, 0) / Q.length, ms = S.reduce((a, x) => a + x, 0) / S.length;
  let c2 = 0, vq = 0, vs = 0;
  for (let i = 0; i < Q.length; i++) { c2 += (Q[i] - mq) * (S[i] - ms); vq += (Q[i] - mq) ** 2; vs += (S[i] - ms) ** 2; }
  tres.push({ sleeve: "nasdaq_alt", proxy: "ONEQ", n: Q.length, first: y2[0], last: y2[y2.length - 1], corr: c2 / Math.sqrt(vq * vs), mean_diff_pp: (mq - ms) * 100, ann_ret_diff_pp: "", te_vol_pct: "", worst_diff_pp: "", cum_ratio: "", top3: "", note: "ONEQ genuine Composite ETF vs Composite price" });
}
// classification (frozen §8)
function classify(t, mismatch) {
  if (t.n < 60) return "implementation_not_ready";
  if (Math.abs(t.ann_ret_diff_pp) <= 0.5 && t.te_vol_pct <= 1.5 && t.corr >= 0.99 && !mismatch) return "implementation_faithful";
  if (t.corr >= 0.95 && t.te_vol_pct <= 4.0) return "implementation_acceptable_with_limitation";
  return "implementation_materially_different";
}
const MISMATCH = { sp500: false, nasdaq: true, russell: false, treasury2y: false, treasury10y: false, longtreasury: false, gold: false, oil: false };
for (const t of tres) {
  if (t.sleeve.includes("vs_TR") || t.sleeve.includes("alt")) { t.class = "QA_only"; continue; }
  t.class = classify(t, MISMATCH[t.sleeve]);
  console.log(t.sleeve, t.proxy, "n=" + t.n, "corr=" + t.corr?.toFixed?.(4), "TE=" + t.te_vol_pct?.toFixed?.(2), "annDiff=" + t.ann_ret_diff_pp?.toFixed?.(2), "=>", t.class);
}
// proxy map audit
const pmap = [
  ["sp500", "S&P 500 TR", "SPY", "ETF", "S&P 500 TR net of 0.0945% ER", "dividends included", "—", "0.0945%", "1993-01", "very high liquidity", ""],
  ["nasdaq", "Nasdaq Composite", "QQQ", "ETF", "Nasdaq-100 TR net of 0.20% ER — LABELED PROXY, NOT Composite", "Nasdaq-100 dividends", "—", "0.20%", "1999-03", "very high liquidity", "universe mismatch quantified"],
  ["russell", "Russell 2000 price", "IWM", "ETF", "Russell 2000 TR net of 0.19% ER (dividends INCLUDED — improvement over price)", "dividends included", "—", "0.19%", "2000-05", "high liquidity", "TR-vs-price wedge favors implementation"],
  ["cash", "3M T-bill", "T-bill accrual", "bills", "identical series (no tracking diff)", "interest", "—", "—", "1934+", "perfect", "none"],
  ["treasury2y", "~2Y CMT TR", "SHY", "ETF", "1-3Y Treasury TR net of 0.15% ER (maturity-band vs point)", "coupons", "—", "0.15%", "2002-07", "high liquidity", "band-vs-point duration nuance"],
  ["treasury10y", "~10Y CMT TR", "IEF", "ETF", "7-10Y Treasury TR net of 0.15% ER", "coupons", "—", "0.15%", "2002-07", "high liquidity", "band-vs-point duration nuance"],
  ["longtreasury", "~20Y CMT TR", "TLT", "ETF", "20+Y Treasury TR net of 0.15% ER (longer duration than 20Y point)", "coupons", "—", "0.15%", "2002-07", "high liquidity", "TLT duration ~15-18y vs synth ~13y"],
  ["gold", "gold price", "GLD", "ETF", "gold price net of 0.40% ER", "none", "—", "0.40%", "2004-11", "high liquidity", "ER drag + monthly-avg vs month-end timing"],
  ["oil", "investable CL+collateral", "USO", "commodity pool", "front-month WTI fund net of 0.60% ER; laddered since Apr-2020", "collateral in NAV", "front-month roll (laddered post-2020)", "0.60%", "2006-04", "high liquidity", "roll-calendar + 2020-regime differences"],
];
fs.writeFileSync(path.join(GEN, "proxy-map.csv"),
  "sleeve,target,proxy,type,exposure,carry,roll,fee,start,liquidty,mismatch\n" + pmap.map((r) => r.map((c) => '"' + c + '"').join(",")).join("\n") + "\n");
const tcols = ["sleeve", "proxy", "n", "first", "last", "corr", "mean_diff_pp", "ann_ret_diff_pp", "te_vol_pct", "worst_diff_pp", "cum_ratio", "top3", "class", "note"];
fs.writeFileSync(path.join(GEN, "tracking.csv"),
  tcols.join(",") + "\n" + tres.map((t) => tcols.map((c) => { const v = t[c]; return typeof v === "number" ? (isFinite(v) ? v : "") : (v ?? ""); }).join(",")).join("\n") + "\n");
fs.writeFileSync(path.join(GEN, "provenance.json"), JSON.stringify(prov, null, 2));
console.log("DONE build");
