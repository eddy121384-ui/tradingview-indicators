#!/usr/bin/env node
// Volatility-managed equity — frozen replication prereg a4c729f.
// Leg 1 paper-faithful (factor excess space, ex-post c, unconstrained weights).
// Leg 2 deployable fair comparison (total-return space, expanding-mean scale, [0,1]).
// Research only, production_authorized=false. No macro data. No tuning.
import fs from "node:fs";
import path from "node:path";
import crypto from "node:crypto";

const RES = "indicators/macro-pressure-map/research";
const DAILY = RES + "/generated/classic-equity-baselines/daily-market-total-returns.csv";
const OUT = RES + "/generated/classic-equity-baselines";
const fin = (x) => typeof x === "number" && Number.isFinite(x);
const avg = (a) => a.reduce((x, y) => x + y, 0) / a.length;
const sd = (a) => { const m = avg(a); return Math.sqrt(a.reduce((x, y) => x + (y - m) ** 2, 0) / a.length); };
const ym = (d) => d.slice(0, 7);

// ---- official daily file -> monthly excess + realized variance (paper eq. 2, /22, ddof=0)
const byMonth = new Map();
for (const l of fs.readFileSync(DAILY, "utf8").trim().split("\n").slice(1)) {
  const c = l.split(",");
  const m = c[0].slice(0, 6), ex = parseFloat(c[2]);
  if (!fin(ex)) throw new Error("non-finite daily excess " + c[0]);
  if (!byMonth.has(m)) byMonth.set(m, []);
  byMonth.get(m).push(ex);
}
const months = [...byMonth.keys()].sort().map((m) => {
  const d = byMonth.get(m);
  const comp = d.reduce((a, x) => a * (1 + x), 1) - 1;
  const mean = avg(d);
  const rv = d.reduce((a, x) => a + (x - mean) ** 2, 0) / 22; // paper divisor, not trading-day count
  if (!(rv > 0)) throw new Error("BLOCKED: non-positive realized variance " + m);
  return { m, f: comp, rv, n: d.length };
});
// ---- repo cash proxy (same file/column as classic baselines)
const cash = new Map();
for (const l of fs.readFileSync(RES + "/generated/issue-174/nine-sleeve-monthly-returns.csv", "utf8").trim().split("\n").slice(1)) {
  const c = l.split(",");
  cash.set(c[0].slice(0, 7), parseFloat(c[4]));
}
// ---- common payoff panel 1967-03..2026-08 (needs prior-month RV)
const panel = months.filter((x) => x.m >= "196703" && x.m <= "202608");
if (panel.length !== 714) throw new Error("panel != 714: " + panel.length);
const rvs = new Map(months.map((x) => [x.m, x.rv]));
const fm = new Map(months.map((x) => [x.m, x.f]));
const prevM = (m) => { const y = +m.slice(0, 4), mo = +m.slice(4, 6) - 1; return mo < 1 ? (y - 1) + "12" : y + String(mo).padStart(2, "0"); };

// ---- Leg 1 paper-faithful: f^s[t] = (c/RV[t-1]) * f[t], c = full-sample vol match (EX-POST)
const raw1 = panel.map((x) => fm.get(x.m) / rvs.get(prevM(x.m)));
const sdF = sd(panel.map((x) => fm.get(x.m))), sdR = sd(raw1);
const c1 = sdF / sdR;
const w1 = panel.map((x) => c1 / rvs.get(prevM(x.m)));
const man1 = panel.map((x, i) => w1[i] * fm.get(x.m));
const reg = (() => {
  const F = panel.map((x) => fm.get(x.m));
  const mA = avg(man1), mB = avg(F);
  const cov = avg(man1.map((v, i) => (v - mA) * (F[i] - mB)));
  const variance = avg(F.map((v) => (v - mB) ** 2));
  const beta = cov / variance;
  return { alpha_m: mA - beta * mB, beta };
})();
const wsorted = [...w1].sort((a, b) => a - b);
const leg1 = {
  label: "paper-faithful M&M market leg (EXCESS space, ex-post c, unconstrained)",
  c_full_sample_ex_post: c1,
  n: panel.length,
  weight_stats: { median: wsorted[w1.length >> 1], p75: wsorted[Math.floor(w1.length * .75)], p90: wsorted[Math.floor(w1.length * .9)], p99: wsorted[Math.floor(w1.length * .99)], max: wsorted[w1.length - 1], frac_above_1: w1.filter((w) => w > 1).length / w1.length, frac_above_1_5: w1.filter((w) => w > 1.5).length / w1.length, mean: avg(w1) },
  unmanaged: { cagr: 0, sharpe: 0 },
  managed: { cagr: 0, sharpe: 0 },
  alpha_monthly: reg.alpha_m, beta: reg.beta,
};
// ---- Leg 2 fair deployable: w = min(1, expanding-mean-RV / RVprev), total-return space
const rvHist = months.filter((x) => x.m < "196703").map((x) => x.rv);
const w2 = [], seen = [...rvHist];
for (const x of panel) {
  if (seen.length < 1) throw new Error("empty expanding window");
  const vbar = avg(seen);
  w2.push(Math.min(1, Math.max(0, vbar / rvs.get(prevM(x.m)))));
  seen.push(rvs.get(x.m));
}
const eq = new Map();
for (const l of fs.readFileSync(RES + "/generated/issue-166/equity-monthly-total-returns.csv", "utf8").trim().split("\n").slice(1)) {
  const c = l.split(",");
  eq.set(c[0].slice(0, 7), parseFloat(c[1]));
}
function runFair(weights, fee) {
  const rs = [];
  let prev = null, turnover = 0, switches = 0;
  for (let i = 0; i < panel.length; i++) {
    const date = panel[i].m.slice(0, 4) + "-" + panel[i].m.slice(4, 6);
    const e = eq.get(date), ch = cash.get(date);
    if (!fin(e) || !fin(ch)) throw new Error("missing total/cash " + date);
    const w = weights[i];
    const to = prev === null ? 0 : Math.abs(w - prev);
    if (prev !== null && ((prev === 0) !== (w === 0))) switches++;
    turnover += to;
    const gross = w * e + (1 - w) * ch;
    rs.push({ date, weight: w, net: gross - (prev === null ? 0 : to * fee), cash: ch, equity: e });
    prev = w;
  }
  return { rs, turnover };
}
function metrics(rs) {
  const n = rs.length;
  let wealth = 1, peak = 1, dd = 0, worst = Infinity;
  for (const x of rs) { wealth *= 1 + x.net; peak = Math.max(peak, wealth); dd = Math.min(dd, wealth / peak - 1); worst = Math.min(worst, x.net); }
  const rets = rs.map((x) => x.net);
  const m = avg(rets), s = sd(rets);
  return {
    n, first: rs[0].date, last: rs[rs.length - 1].date,
    cagr: wealth ** (12 / n) - 1, vol: s * Math.sqrt(12),
    sharpe_like: s ? Math.sqrt(12) * avg(rs.map((x) => x.net - x.cash)) / s : null,
    max_dd: dd, worst_month: worst, avg_equity: avg(rs.map((x) => x.weight)),
    turnover_annual: rs.reduce((a, x, i) => a + (i ? Math.abs(x.weight - rs[i - 1].weight) : 0), 0) * 12 / n,
  };
}
const fair = runFair(w2, .0002), fair10 = runFair(w2, .001);
const meanW2 = avg(w2);
const matchW = panel.map(() => meanW2);
const match = runFair(matchW, .0002);
const eras = { E1: ["1967-03", "1979-12"], E2: ["1980-01", "1999-12"], E3: ["2000-01", "2019-12"], E4: ["2020-01", "2026-08"] };
const crises = { "1973-74": ["1973-01", "1974-12"], "1987": ["1987-08", "1987-12"], "2000-02": ["2000-03", "2002-10"], "2007-09": ["2007-10", "2009-03"], "2020": ["2020-02", "2020-04"], "2022": ["2022-01", "2022-12"] };
const sel = (arr, lo, hi) => arr.filter((x) => x.date >= lo && x.date <= hi);
// Leg-1 metrics on excess space
function metricsExcess(rets, cashArr) {
  const n = rets.length;
  let comp = 1, peak = 1, dd = 0;
  for (const r of rets) { comp *= 1 + r; peak = Math.max(peak, comp); dd = Math.min(dd, comp / peak - 1); }
  const m = avg(rets), s = sd(rets);
  return { n, cagr_excess: comp ** (12 / n) - 1, vol: s * Math.sqrt(12), sharpe_excess: s ? Math.sqrt(12) * m / s : null, max_dd: dd, worst_month: Math.min(...rets) };
}
const fEx = panel.map((x) => fm.get(x.m));
const cashM = panel.map((x) => cash.get(x.m.slice(0, 4) + "-" + x.m.slice(4, 6)));
leg1.unmanaged = metricsExcess(fEx, cashM);
leg1.managed = metricsExcess(man1, cashM);
leg1.turnover_weights_annual = w1.slice(1).reduce((a, w, i) => a + Math.abs(w - w1[i]), 0) * 12 / w1.length;
leg1.break_even_cost_per_unit_turnover = leg1.turnover_weights_annual ? (reg.alpha_m * 12) / leg1.turnover_weights_annual : null;
const out = {
  study: "volatility_managed_equity", prereg_commit: "a4c729fd0433c95e1350a1ac7c4e687773bf15c8",
  source_ref: "1fabf0f9c94c391a7c2d302caff6bbdf56062d95",
  daily: { sha256: crypto.createHash("sha256").update(fs.readFileSync(DAILY)).digest("hex"), rows: 26317 },
  panel: { n: panel.length, first: "1967-03", last: "2026-08" },
  leg1_paper_faithful_excess_space: leg1,
  leg2_fair_deployable: {
    label: "expanding-mean scale, weights [0,1], total-return + same cash/costs",
    full: metrics(fair.rs), fee10bp: metrics(fair10.rs),
    mean_exposure: meanW2,
    matched_fixed: metrics(match.rs),
    eras: Object.fromEntries(Object.entries(eras).map(([e, [lo, hi]]) => [e, metrics(sel(fair.rs, lo, hi))])),
    crises: Object.fromEntries(Object.entries(crises).map(([e, [lo, hi]]) => {
      const s = sel(fair.rs, lo, hi);
      return [e, { ret: s.reduce((p, x) => p * (1 + x.net), 1) - 1, avg_equity: avg(s.map((x) => x.weight)), n: s.length }];
    })),
  },
  labels: { leg1: "paper-faithful M&M replication (ex-post c, unconstrained leverage) - NOT deployable", leg2: "deployable fair comparison (expanding calibration, 0-100%, same cash/costs)", historical: "revised-vintage, in-sample monthly, no macro" },
  production_authorized: false,
};
fs.writeFileSync(path.join(OUT, "volatility-managed-results.json"), JSON.stringify(out, null, 2) + "\n");
const cols = ["date", "rv_prev", "w_paper", "w_fair", "mkt_excess", "man_excess", "fair_net_2bp"];
const csv = [cols.join(",")];
for (let i = 0; i < panel.length; i++) {
  csv.push([panel[i].m.slice(0, 4) + "-" + panel[i].m.slice(4, 6), rvs.get(prevM(panel[i].m)).toExponential(4), w1[i].toFixed(4), w2[i].toFixed(4), fm.get(panel[i].m).toFixed(6), man1[i].toFixed(6), fair.rs[i].net.toFixed(6)].join(","));
}
fs.writeFileSync(path.join(OUT, "volatility-managed-monthly.csv"), csv.join("\n") + "\n");
console.log("Leg1 managed excess Sharpe:", leg1.managed.sharpe_excess?.toFixed(3), "unmanaged:", leg1.unmanaged.sharpe_excess?.toFixed(3), "alpha_m:", (reg.alpha_m * 100).toFixed(3) + "pp/mo");
console.log("Leg1 weights p50/p90/p99/max:", leg1.weight_stats.median.toFixed(2), leg1.weight_stats.p90.toFixed(2), leg1.weight_stats.p99.toFixed(2), leg1.weight_stats.max.toFixed(2));
console.log("Leg2 fair CAGR:", metrics(fair.rs).cagr.toFixed(4), "mean exposure:", meanW2.toFixed(4));
