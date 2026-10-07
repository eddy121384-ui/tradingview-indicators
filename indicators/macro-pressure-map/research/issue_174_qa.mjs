// Issue #174 — QA / validation (unconditional; NO macro join).
import fs from "node:fs";
import path from "node:path";

const ROOT = process.cwd();
const GEN = path.join(ROOT, "indicators/macro-pressure-map/research/generated/issue-174");

function loadBackbone() {
  const txt = fs.readFileSync(path.join(GEN, "nine-sleeve-monthly-returns.csv"), "utf8");
  const lines = txt.trim().split("\n");
  const h = lines[0].split(",");
  return { h, rows: lines.slice(1).map((l) => {
    const c = l.split(",");
    const r = { date: c[0] };
    for (let j = 1; j < h.length; j++) r[h[j]] = c[j] === "" ? NaN : parseFloat(c[j]);
    return r;
  })};
}
function pearson(a, b) {
  const n = a.length;
  const ma = a.reduce((s, x) => s + x, 0) / n, mb = b.reduce((s, x) => s + x, 0) / n;
  let cov = 0, va = 0, vb = 0;
  for (let i = 0; i < n; i++) { cov += (a[i] - ma) * (b[i] - mb); va += (a[i] - ma) ** 2; vb += (b[i] - mb) ** 2; }
  return cov / Math.sqrt(va * vb);
}
function mae(a, b) { return a.reduce((s, x, i) => s + Math.abs(x - b[i]), 0) / a.length; }

// Yahoo ETF adjclose TR (from provenance fetches? re-fetch minimal SHY/IEF/TLT/GLD/QQQ/IWM/SPY/USO monthly adjclose)
const UA = { "User-Agent": "Mozilla/5.0" };
async function yahooAdj(symbol) {
  const url = "https://query1.finance.yahoo.com/v8/finance/chart/" + encodeURIComponent(symbol) + "?interval=1mo&period1=0&period2=1790976000&events=div%7Csplit";
  const r = await fetch(url, { headers: UA });
  const j = await r.json();
  const res = j.chart.result[0];
  const ts = res.timestamp;
  const adj = res.indicators.adjclose?.[0]?.adjclose || res.indicators.quote[0].close;
  const out = new Map();
  for (let i = 0; i < ts.length; i++) {
    if (adj[i] == null) continue;
    const d = new Date(ts[i] * 1000);
    out.set(d.getUTCFullYear() + "-" + String(d.getUTCMonth() + 1).padStart(2, "0"), adj[i]);
  }
  return out;
}
const { rows } = loadBackbone();
const bm = new Map(rows.map((r) => [r.date.slice(0, 7), r]));

const pairs = [
  ["treasury2y", "SHY", "synthetic 2Y vs SHY TR (duration ~1.9y vs ~1.9y; expect high corr)"],
  ["treasury10y", "IEF", "synthetic 10Y vs IEF TR (~8y vs ~7.5y; expect high corr)"],
  ["longtreasury", "TLT", "synthetic 20Y vs TLT TR (~13y vs ~15-18y; expect moderate-high corr, level differs)"],
  ["sp500", "SPY", "French market TR vs SPY TR (universe differs; expect very high corr)"],
  ["nasdaq", "QQQ", "NASDAQCOM price vs QQQ TR (price vs TR + composition; expect high corr, level differs)"],
  ["russell", "IWM", "RUT price vs IWM TR (price vs TR; expect high corr)"],
  ["gold", "GLD", "Pink Sheet gold price vs GLD TR (monthly-avg vs fund; expect very high corr)"],
  ["oil", "USO", "WTI spot vs USO TR (spot vs futures+roll; expect moderate corr, level differs)"],
];
const qa = [];
for (const [sleeve, etf, note] of pairs) {
  try {
    const em = await yahooAdj(etf);
    const common = [...em.keys()].filter((ym) => bm.has(ym) && isFinite(bm.get(ym)[sleeve])).sort();
    // build ETF monthly returns
    const er = [];
    const sr = [];
    for (let i = 1; i < common.length; i++) {
      const p = common[i - 1], c = common[i];
      // require consecutive calendar months
      const ep = em.get(p), ec = em.get(c);
      const s = bm.get(c)[sleeve];
      if (!isFinite(ec / ep - 1) || !isFinite(s)) continue;
      er.push(ec / ep - 1);
      sr.push(s);
    }
    const q = er.length ? { n: er.length, pearson: pearson(sr, er), mae_pp: mae(sr, er) * 100, sign_agree: sr.filter((v, i) => Math.sign(v) === Math.sign(er[i])).length / sr.length, first: common[1], last: common[common.length - 1] } : { n: 0 };
    qa.push({ sleeve, etf, note, ...q });
    console.log(sleeve, etf, JSON.stringify(q));
  } catch (e) { qa.push({ sleeve, etf, error: String(e.message || e) }); console.log(sleeve, etf, "ERR", e.message); }
}
// spot plausibility (unconditional)
function spot(month, col) {
  const r = rows.find((x) => x.date === month);
  return r ? r[col] : NaN;
}
const spots = {
  treasury10y_1981_08: spot("1981-08-01", "treasury10y"),
  treasury2y_1981_08: spot("1981-08-01", "treasury2y"),
  long_1981_08: spot("1981-08-01", "longtreasury"),
  treasury10y_2008_12: spot("2008-12-01", "treasury10y"),
  long_2008_12: spot("2008-12-01", "longtreasury"),
  treasury10y_2022_10: spot("2022-10-01", "treasury10y"),
  long_2022_10: spot("2022-10-01", "longtreasury"),
  gold_1980_01: spot("1980-01-01", "gold"),
  oil_1986_03: spot("1986-03-01", "oil"),
  oil_2008_12: spot("2008-12-01", "oil"),
  oil_2020_04: spot("2020-04-01", "oil"),
  sp500_1987_10: spot("1987-10-01", "sp500"),
  nasdaq_2000_03_vs_2002: [spot("2000-03-01", "nasdaq"), spot("2002-10-01", "nasdaq")],
};
const report = { qa_pairs: qa, spot_plausibility: spots, gaps: JSON.parse(fs.readFileSync(path.join(GEN, "nine-sleeve-coverage.json"), "utf8"))._gaps_missing_returns_in_196603_202608 };
fs.writeFileSync(path.join(GEN, "qa-validation.json"), JSON.stringify(report, null, 2));
console.log("wrote qa-validation.json");
