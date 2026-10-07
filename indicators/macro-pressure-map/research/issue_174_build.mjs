// Issue #174 — Phase A backbone builder (Node executor).
// Frozen methodology: issue-174-nine-sleeve-map-prereg.md
// Fetches genuine long-history sources, builds deterministic monthly returns,
// reuses #166 files verbatim, writes generated/issue-174 backbone + provenance.
// No macro x asset join here. No state-conditioned computation here.
import fs from "node:fs";
import path from "node:path";
import crypto from "node:crypto";
import { execSync } from "node:child_process";

const ROOT = process.cwd();
const GEN = path.join(ROOT, "indicators/macro-pressure-map/research/generated/issue-174");
fs.mkdirSync(GEN, { recursive: true });

const sha256 = (buf) => crypto.createHash("sha256").update(buf).digest("hex");
const gitBlobSha = (p) => {
  const buf = execSync("git show HEAD:" + p, { maxBuffer: 100 * 1024 * 1024 });
  return { bytes: buf.length, sha: sha256(buf) };
};
const sleep = (ms) => new Promise((r) => setTimeout(r, ms));

async function fetchText(url, headers, retries = 4) {
  let last = null;
  for (let i = 0; i < retries; i++) {
    try {
      const r = await fetch(url, { headers });
      if (!r.ok) throw new Error("HTTP " + r.status);
      const buf = Buffer.from(await r.arrayBuffer());
      return { buf, text: buf.toString("utf8"), status: r.status };
    } catch (e) {
      last = e;
      await sleep(800 * (i + 1));
    }
  }
  throw last;
}

// Frozen synthetic bond math (identical to Python primitive).
function bondMonthly(yT, yNext, years) {
  if (!isFinite(yT) || !isFinite(yNext) || yT < 0 || yNext < 0) return NaN;
  const n = 2 * years;
  const coupon = (100 * yT) / 2;
  const per = yNext / 2;
  let pv = 0;
  for (let k = 1; k <= n; k++) {
    const tauY = k / 2 - 1 / 12;
    const periods = 2 * tauY;
    const df = Math.pow(1 + per, -periods);
    if (!isFinite(df)) return NaN;
    const cf = coupon + (k === n ? 100 : 0);
    pv += cf * df;
  }
  return pv / 100 - 1;
}

function monthKeyFirstOfMonth(d) {
  return d.slice(0, 7) + "-01";
}
function parseFredDaily(csvText) {
  // returns Map YYYY-MM -> {date, value} last available daily in month
  const lines = csvText.trim().split("\n").slice(1);
  const byM = new Map();
  for (const l of lines) {
    const idx = l.indexOf(",");
    const d = l.slice(0, idx);
    const v = l.slice(idx + 1).trim();
    if (!v || v === "." || v === "NA") continue;
    const m = d.slice(0, 7);
    byM.set(m, { date: d, value: parseFloat(v) });
  }
  return byM;
}
function parseFredMonthly(csvText) {
  const lines = csvText.trim().split("\n").slice(1);
  const out = [];
  for (const l of lines) {
    const idx = l.indexOf(",");
    const d = l.slice(0, idx);
    const v = l.slice(idx + 1).trim();
    if (!v || v === "." || v === "NA") continue;
    out.push({ date: d, value: parseFloat(v) });
  }
  return out;
}

const UA_FRED = { "User-Agent": "tradingview-indicators-research/1.0" };
const UA_YAHOO = { "User-Agent": "Mozilla/5.0" };

console.log("Issue #174 build: fetching sources...");

const prov = { fetched_at: new Date().toISOString(), sources: {} };

// 1. FRED DGS2 / DGS20 / TB3MS / NASDAQCOM / MCOILWTICO
const fredIds = ["DGS2", "DGS20", "TB3MS", "NASDAQCOM", "MCOILWTICO"];
const fredRaw = {};
for (const id of fredIds) {
  const { buf, text } = await fetchText(
    "https://fred.stlouisfed.org/graph/fredgraph.csv?id=" + id,
    UA_FRED
  );
  fredRaw[id] = text;
  const lines = text.trim().split("\n");
  prov.sources["FRED:" + id] = {
    url: "https://fred.stlouisfed.org/graph/fredgraph.csv?id=" + id,
    bytes: buf.length,
    sha256: sha256(buf),
    header: lines[0],
    n_lines: lines.length - 1,
    first_line: lines[1],
    last_line: lines[lines.length - 1],
  };
  console.log("FRED", id, "bytes", buf.length);
}

// 2. Gold monthly (World Bank Pink Sheet via datahub)
const { buf: goldBuf, text: goldText } = await fetchText(
  "https://datahub.io/core/gold-prices/_r/-/data/monthly.csv",
  UA_YAHOO
);
prov.sources["PINK_SHEET:gold_monthly"] = {
  url: "https://datahub.io/core/gold-prices/_r/-/data/monthly.csv",
  mirror_of: "World Bank Commodity Price Data (Pink Sheet) monthly gold, USD/oz; CC BY 4.0",
  bytes: goldBuf.length,
  sha256: sha256(goldBuf),
  n_lines: goldText.trim().split("\n").length - 1,
  first_line: goldText.trim().split("\n")[1],
  last_line: goldText.trim().split("\n").slice(-1)[0],
};
console.log("gold bytes", goldBuf.length);

// 3. Yahoo ^RUT + ^IXIC QA + SHY/IEF/TLT QA (fetch RUT primary; others QA-only)
async function yahooMonthly(symbol) {
  const url =
    "https://query1.finance.yahoo.com/v8/finance/chart/" +
    encodeURIComponent(symbol) +
    "?interval=1mo&period1=0&period2=1790976000";
  const r = await fetch(url, { headers: UA_YAHOO });
  if (!r.ok) throw new Error("Yahoo " + symbol + " HTTP " + r.status);
  const buf = Buffer.from(await r.arrayBuffer());
  const j = JSON.parse(buf.toString("utf8"));
  const res = j.chart?.result?.[0];
  if (!res) throw new Error("Yahoo " + symbol + " no result");
  return { buf, json: j, res };
}
const yahooSyms = ["^RUT", "^IXIC", "SHY", "IEF", "TLT", "SPY", "GLD", "USO"];
const yahooRaw = {};
for (const s of yahooSyms) {
  try {
    const { buf, res } = await yahooMonthly(s);
    yahooRaw[s] = res;
    const ft = res.meta?.firstTradeDate
      ? new Date(res.meta.firstTradeDate * 1000).toISOString()
      : null;
    prov.sources["Yahoo:" + s] = {
      url: "https://query1.finance.yahoo.com/v8/finance/chart/" + encodeURIComponent(s),
      bytes: buf.length,
      sha256: sha256(buf),
      firstTradeDate: ft,
      n_points: res.timestamp?.length ?? 0,
      currency: res.meta?.currency,
      exchange: res.meta?.fullExchangeName,
    };
    console.log("Yahoo", s, "n", res.timestamp?.length, "first", ft);
  } catch (e) {
    console.log("Yahoo", s, "FAILED", e.message);
    prov.sources["Yahoo:" + s] = { error: String(e.message || e) };
  }
}

// 4. Reuse #166 files verbatim (record both git-blob and working-tree hashes)
for (const p of [
  "indicators/macro-pressure-map/research/generated/issue-166/equity-monthly-total-returns.csv",
  "indicators/macro-pressure-map/research/generated/issue-166/treasury-monthly-total-returns.csv",
]) {
  const blob = gitBlobSha(p);
  const wt = fs.readFileSync(path.join(ROOT, p));
  prov.sources["REUSE:" + p] = {
    git_blob_bytes: blob.bytes,
    git_blob_sha256: blob.sha,
    working_tree_bytes: wt.length,
    working_tree_sha256: sha256(wt),
  };
}
prov.sources["FROZEN:macro"] = {
  path: "indicators/macro-pressure-map/research/generated/issue-160/deep-history-v01-monthly.csv",
  ...gitBlobSha(
    "indicators/macro-pressure-map/research/generated/issue-160/deep-history-v01-monthly.csv"
  ),
  expected: "42516418ec8d1ce981d1b4bc05e2ae86809d6acbf5de63dccbad515db507dcfc",
};
prov.sources["FROZEN:damodaran"] = {
  url: "https://pages.stern.nyu.edu/adamodar/New_Home_Page/datafile/histretSP.html",
  note: "validation reference from #166; bytes/sha on record 656121 / 127c772f0fea8763391dbf2c1c7d3ecd3a07ca2b23f81ab47af58b529e2b5647",
};
prov.sources["FROZEN:french"] = {
  url: "https://mba.tuck.dartmouth.edu/pages/faculty/ken.french/ftp/F-F_Research_Data_Factors_CSV.zip",
  note: "underlying #166 equity; file_sha256 d7d7fe37b150b5b15c9c069b3ba101dfe1af568c6d7b5db6e73cd0a6c0c9e5e5",
};

// ---- Build monthly returns ----
const dgs2M = parseFredDaily(fredRaw["DGS2"]);
const dgs20M = parseFredDaily(fredRaw["DGS20"]);
const nasM = parseFredDaily(fredRaw["NASDAQCOM"]);
const tb3 = parseFredMonthly(fredRaw["TB3MS"]); // [{date,value}]
const oilM = parseFredMonthly(fredRaw["MCOILWTICO"]);

// gold: Date,Price with YYYY-MM
const goldRows = goldText
  .trim()
  .split("\n")
  .slice(1)
  .map((l) => {
    const [d, p] = l.split(",");
    return { date: d + "-01", price: parseFloat(p) };
  })
  .filter((r) => isFinite(r.price));

// Yahoo ^RUT monthly: use timestamp + close
function yahooMonthCloses(res) {
  const ts = res.timestamp || [];
  const closes = res.indicators?.quote?.[0]?.close || [];
  const out = new Map();
  for (let i = 0; i < ts.length; i++) {
    const d = new Date(ts[i] * 1000);
    const ym = d.getUTCFullYear() + "-" + String(d.getUTCMonth() + 1).padStart(2, "0");
    const c = closes[i];
    if (c == null || !isFinite(c)) continue;
    out.set(ym, c); // last bar in month wins (data already monthly)
  }
  return out;
}
const rutM = yahooRaw["^RUT"] ? yahooMonthCloses(yahooRaw["^RUT"]) : new Map();

// #166 reuse
function readCsvMap(p, valCol) {
  const txt = fs.readFileSync(path.join(ROOT, p), "utf8");
  const lines = txt.trim().split("\n").slice(1);
  const m = new Map();
  for (const l of lines) {
    const c = l.split(",");
    m.set(c[0].slice(0, 7), parseFloat(c[valCol]));
  }
  return m;
}
const eqM = readCsvMap(
  "indicators/macro-pressure-map/research/generated/issue-166/equity-monthly-total-returns.csv",
  1
);
const t10M = (() => {
  const txt = fs.readFileSync(
    path.join(
      ROOT,
      "indicators/macro-pressure-map/research/generated/issue-166/treasury-monthly-total-returns.csv"
    ),
    "utf8"
  );
  const lines = txt.trim().split("\n").slice(1);
  const m = new Map();
  for (const l of lines) {
    const c = l.split(",");
    m.set(c[0].slice(0, 7), parseFloat(c[1]));
  }
  return m;
})();

// Union calendar months: build from 1966-02 (prev for 1966-03 returns) .. 2026-08;
// output filtered to macro window 1966-03+.
function monthList(loYm, hiYm) {
  const out = [];
  let [y, m] = loYm.split("-").map(Number);
  const [ey, em] = hiYm.split("-").map(Number);
  while (y < ey || (y === ey && m <= em)) {
    out.push(String(y).padStart(4, "0") + "-" + String(m).padStart(2, "0") + "-01");
    m++;
    if (m > 12) {
      m = 1;
      y++;
    }
  }
  return out;
}
const calBuild = monthList("1966-02", "2026-08");
const calMonths = calBuild.filter((d) => d >= "1966-03-01");

// Helpers: month-end yield decimal
const ymd = (ym) => {
  const e2 = dgs2M.get(ym);
  const e20 = dgs20M.get(ym);
  return {
    y2: e2 ? e2.value / 100 : NaN,
    y20: e20 ? e20.value / 100 : NaN,
  };
};

const rows = [];
for (let i = 0; i < calMonths.length; i++) {
  const mo = calMonths[i];
  const ym = mo.slice(0, 7);
  const prevYm =
    i === 0
      ? null
      : calMonths[i - 1].slice(0, 7);
  // sp500 / 10Y direct
  const sp = eqM.has(ym) ? eqM.get(ym) : NaN;
  const t10 = t10M.has(ym) ? t10M.get(ym) : NaN;
  // cash: TB3MS_{t-1}/1200 — need TB3MS monthly map
  // build tb map
  // (built below once)
  rows.push({ mo, ym, sp, t10 });
}
// TB3 map
const tbMap = new Map(tb3.map((r) => [r.date.slice(0, 7), r.value]));
const oilMap = new Map(oilM.map((r) => [r.date.slice(0, 7), r.value]));
const goldMap = new Map(goldRows.map((r) => [r.date.slice(0, 7), r.price]));
const nasMap = nasM; // YYYY-MM -> {date,value}

const outAll = [];
const gaps = { treasury2y: 0, longtreasury: 0, nasdaq: 0, russell: 0, cash: 0, gold: 0, oil: 0 };
// Build over calBuild (includes 1966-02 as prev), then filter to calMonths for output/gaps.
for (let i = 0; i < calBuild.length; i++) {
  const mo = calBuild[i];
  const ym = mo.slice(0, 7);
  const prevMo = i > 0 ? calBuild[i - 1] : null;
  const prevYm = prevMo ? prevMo.slice(0, 7) : null;
  const sp = eqM.has(ym) ? eqM.get(ym) : NaN;
  const t10 = t10M.has(ym) ? t10M.get(ym) : NaN;
  // cash
  const tbPrev = prevYm && tbMap.has(prevYm) ? tbMap.get(prevYm) : NaN;
  const cash = isFinite(tbPrev) ? tbPrev / 1200 : NaN;
  if (!isFinite(cash)) gaps.cash++;
  // 2Y synthetic: needs y(ym-prev?) — careful: return for month mo uses y_{prevMo-end} -> y_{mo-end}.
  // Our dgs2M is keyed by calendar month of the daily bar. Month-end yield for month X = last daily in X.
  // Return for month mo = bondMonthly(y_{prevMo}, y_{mo}, M).
  let r2 = NaN;
  if (prevYm && dgs2M.has(prevYm) && dgs2M.has(ym)) {
    r2 = bondMonthly(dgs2M.get(prevYm).value / 100, dgs2M.get(ym).value / 100, 2);
  } else gaps.treasury2y++;
  let rL = NaN;
  if (prevYm && dgs20M.has(prevYm) && dgs20M.has(ym)) {
    rL = bondMonthly(dgs20M.get(prevYm).value / 100, dgs20M.get(ym).value / 100, 20);
  } else gaps.longtreasury++;
  // nasdaq price return
  let rN = NaN;
  if (prevYm && nasM.has(prevYm) && nasM.has(ym)) {
    const a = nasM.get(prevYm).value, b = nasM.get(ym).value;
    rN = b / a - 1;
  } else gaps.nasdaq++;
  // russell
  let rR = NaN;
  if (prevYm && rutM.has(prevYm) && rutM.has(ym)) {
    rR = rutM.get(ym) / rutM.get(prevYm) - 1;
  } else gaps.russell++;
  // gold
  let rG = NaN;
  if (prevYm && goldMap.has(prevYm) && goldMap.has(ym)) {
    rG = goldMap.get(ym) / goldMap.get(prevYm) - 1;
  } else gaps.gold++;
  // oil
  let rO = NaN;
  if (prevYm && oilMap.has(prevYm) && oilMap.has(ym)) {
    rO = oilMap.get(ym) / oilMap.get(prevYm) - 1;
  } else gaps.oil++;
  outAll.push({
    date: mo, sp500: sp, nasdaq: rN, russell: rR, cash, treasury2y: r2,
    treasury10y: t10, longtreasury: rL, gold: rG, oil: rO,
  });
}
// Output/gaps/coverage use macro window only (1966-03+).
const out = outAll.filter((r) => r.date >= "1966-03-01");
for (const k of Object.keys(gaps)) gaps[k] = 0;
for (const r of out) {
  if (!isFinite(r.cash)) gaps.cash++;
  if (!isFinite(r.treasury2y)) gaps.treasury2y++;
  if (!isFinite(r.longtreasury)) gaps.longtreasury++;
  if (!isFinite(r.nasdaq)) gaps.nasdaq++;
  if (!isFinite(r.russell)) gaps.russell++;
  if (!isFinite(r.gold)) gaps.gold++;
  if (!isFinite(r.oil)) gaps.oil++;
}

const header = "date,sp500,nasdaq,russell,cash,treasury2y,treasury10y,longtreasury,gold,oil";
const lines = [header];
for (const r of out) {
  const f = (v) => (isFinite(v) ? String(v) : "");
  lines.push([r.date, f(r.sp500), f(r.nasdaq), f(r.russell), f(r.cash), f(r.treasury2y), f(r.treasury10y), f(r.longtreasury), f(r.gold), f(r.oil)].join(","));
}
fs.writeFileSync(path.join(GEN, "nine-sleeve-monthly-returns.csv"), lines.join("\n") + "\n");

// coverage
function firstLast(key) {
  let f = null, l = null, n = 0;
  for (const r of out) {
    if (isFinite(r[key])) {
      if (!f) f = r.date;
      l = r.date;
      n++;
    }
  }
  return { first: f, last: l, n };
}
const coverage = {};
for (const k of ["sp500", "nasdaq", "russell", "cash", "treasury2y", "treasury10y", "longtreasury", "gold", "oil"]) {
  coverage[k] = firstLast(k);
}
coverage._gaps_missing_returns_in_196603_202608 = gaps;
coverage._window = { first: "1966-03-01", last: "2026-08-01", calendar_months: calMonths.length };
fs.writeFileSync(path.join(GEN, "nine-sleeve-coverage.json"), JSON.stringify(coverage, null, 2));

// source matrix
const smHeader = "candidate,layer,provider,exact_series,first_obs,last_obs,n_obs,unit,dividends_coupon,frequency,methodology,status,why,hash_or_note";
const smRows = [smHeader];
const q = (s) => '"' + String(s).replace(/"/g, "'") + '"';
smRows.push(["S&P500 proxy (French market TR)", "equity", "Kenneth R. French Data Library (CRSP underlying)", "F-F_Research_Data_Factors Mkt-RF+RF reused via issue-166 file", coverage.sp500.first, coverage.sp500.last, coverage.sp500.n, "decimal monthly", "included (CRSP)", "monthly", "reuse verbatim; no alteration", "SELECTED backbone", "long-history TR-equivalent; universe != S&P500 exactly", "wt_sha=" + prov.sources["REUSE:indicators/macro-pressure-map/research/generated/issue-166/equity-monthly-total-returns.csv"].working_tree_sha256].map(q).join(","));
smRows.push(["NASDAQCOM month-end price", "equity", "FRED", "NASDAQCOM daily -> month-end last close -> price return", coverage.nasdaq.first, coverage.nasdaq.last, coverage.nasdaq.n, "decimal monthly", "excluded (price-only)", "monthly", "P_t/P_{t-1}-1; last available daily", "SELECTED backbone w/ limitation", "genuine history from 1971-02; NOT tech sector; dividends missing", "fred_sha=" + prov.sources["FRED:NASDAQCOM"].sha256].map(q).join(","));
smRows.push(["Russell 2000 ^RUT price", "equity", "Yahoo Finance (Chicago Options)", "^RUT monthly close -> price return", coverage.russell.first, coverage.russell.last, coverage.russell.n, "decimal monthly", "excluded (price-only)", "monthly", "P_t/P_{t-1}-1; month-end", "SELECTED backbone w/ limitation", "genuine Russell history; no backfill; no IWM; dividends missing", "yahoo_sha=" + (prov.sources["Yahoo:^RUT"].sha256 || "ERR")].map(q).join(","));
smRows.push(["Cash TB3MS accrual", "rates", "FRED", "TB3MS monthly % p.a. -> cash_t=TB3MS_{t-1}/1200", coverage.cash.first, coverage.cash.last, coverage.cash.n, "decimal monthly", "interest accrual", "monthly", "simple y/12; separate from 2Y", "SELECTED backbone", "risk-free benchmark and sleeve", "fred_sha=" + prov.sources["FRED:TB3MS"].sha256].map(q).join(","));
smRows.push(["Synthetic 2Y CMT TR", "rates", "FRED DGS2 + frozen par-bond", "2Y par/semiannual/dirty-price roll (S2)", coverage.treasury2y.first, coverage.treasury2y.last, coverage.treasury2y.n, "decimal monthly", "coupon-inclusive", "monthly", "init 2Y par at y_t; reprice 1y11m at y_{t+1}; roll", "SELECTED backbone (synthetic)", "validated vs SHY modern; month-end last-daily", "fred_sha=" + prov.sources["FRED:DGS2"].sha256].map(q).join(","));
smRows.push(["Synthetic 10Y CMT TR (frozen #166)", "rates", "FRED DGS10 via #166", "reuse issue-166 treasury file verbatim", coverage.treasury10y.first, coverage.treasury10y.last, coverage.treasury10y.n, "decimal monthly", "coupon-inclusive", "monthly", "per #166; UNCHANGED", "SELECTED backbone", "do not modify #166", "wt_sha=" + prov.sources["REUSE:indicators/macro-pressure-map/research/generated/issue-166/treasury-monthly-total-returns.csv"].working_tree_sha256].map(q).join(","));
smRows.push(["Synthetic 20Y CMT TR", "rates", "FRED DGS20 + frozen par-bond", "20Y par/semiannual/dirty-price roll (S20); GAP 1987-1993 (20Y discontinued)", coverage.longtreasury.first, coverage.longtreasury.last, coverage.longtreasury.n, "decimal monthly", "coupon-inclusive", "monthly", "init 20Y par at y_t; reprice 19y11m at y_{t+1}; roll; no interpolation", "SELECTED backbone w/ limitation", "single-yield approx; 81-mo yield gap disclosed; validated vs TLT/Damodaran", "fred_sha=" + prov.sources["FRED:DGS20"].sha256].map(q).join(","));
smRows.push(["Gold Pink Sheet monthly avg", "real", "World Bank Pink Sheet via datahub", "monthly avg USD/oz -> price return", coverage.gold.first, coverage.gold.last, coverage.gold.n, "decimal monthly", "none (complete for gold)", "monthly", "P_t/P_{t-1}-1; monthly-average convention", "SELECTED backbone w/ limitation", "no GLD; pre-1971 fixed parity acknowledged", "gold_sha=" + prov.sources["PINK_SHEET:gold_monthly"].sha256].map(q).join(","));
smRows.push(["WTI spot MCOILWTICO", "real", "FRED", "MCOILWTICO monthly USD/bbl -> spot price return", coverage.oil.first, coverage.oil.last, coverage.oil.n, "decimal monthly", "none (spot; no roll/collateral)", "monthly", "P_t/P_{t-1}-1; labeled oil_price_proxy", "SELECTED backbone w/ limitation", "NOT investable futures TR; short history; never stitched", "fred_sha=" + prov.sources["FRED:MCOILWTICO"].sha256].map(q).join(","));
smRows.push(["SPY/QQQ/IWM/SHY/IEF/TLT/GLD/USO", "validation", "Yahoo Finance", "monthly adjclose-derived TR", "", "", "", "decimal monthly", "adjusted", "monthly", "modern overlap QA only", "QA ONLY", "never backbones", ""].map(q).join(","));
fs.writeFileSync(path.join(GEN, "nine-sleeve-source-matrix.csv"), smRows.join("\n") + "\n");
fs.writeFileSync(path.join(GEN, "nine-sleeve-provenance.json"), JSON.stringify(prov, null, 2));

console.log("coverage", JSON.stringify(coverage, null, 2));
console.log("DONE build");
