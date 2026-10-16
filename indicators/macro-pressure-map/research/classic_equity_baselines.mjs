// Classic equity de-risking baselines. Run: node research/classic_equity_baselines.mjs
// Frozen study: research/classic_equity_baselines_prereg.md (commit 3445dc4).
// Inputs pinned to 1fabf0f. Output is descriptive, not a live-PIT signal.
import fs from 'node:fs';
import path from 'node:path';
import crypto from 'node:crypto';
import { fileURLToPath } from 'node:url';

const HERE = path.dirname(fileURLToPath(import.meta.url));
const EQUITY = path.join(HERE, 'generated/issue-166/equity-monthly-total-returns.csv');
const CASH = path.join(HERE, 'generated/issue-174/nine-sleeve-monthly-returns.csv');
const OUT = path.join(HERE, 'generated/classic-equity-baselines');
const assert = (ok, msg) => { if (!ok) throw Error(msg); };
const ym = str => { const [year, month] = str.slice(0, 7).split('-').map(Number); return year * 12 + month; };
const avg = x => x.reduce((a, b) => a + b, 0) / x.length;
const parse = file => {
  const lines = fs.readFileSync(file, 'utf8').trim().split(/\r?\n/);
  const cols = lines.shift().split(',');
  return lines.map(l => Object.fromEntries(l.split(',').map((v, j) => [cols[j], v])));
};
const validate = (rows, field, name) => {
  for (let i = 0; i < rows.length; i++) {
    const v = Number(rows[i][field]);
    assert(rows[i][field] !== '' && Number.isFinite(v) && v > -1, name + ' invalid row ' + i);
    if (i) assert(ym(rows[i].date) - ym(rows[i - 1].date) === 1, name + ' gap at ' + rows[i].date);
  }
};
const eqRows = parse(EQUITY);
const cashRows = parse(CASH);
validate(eqRows, 'equity_tr', 'equity');
validate(cashRows, 'cash', 'cash');
assert(eqRows.length === 800 && cashRows.length === 726, 'unexpected input lengths; verify source version');
const es = new Map(eqRows.map(r => [r.date.slice(0, 7), Number(r.equity_tr)]));
const cs = new Map(cashRows.map(r => [r.date.slice(0, 7), Number(r.cash)]));
const months = eqRows.map(r => r.date.slice(0, 7));
const idx = new Map();
let price = 100;
for (const m of months) { price *= 1 + es.get(m); idx.set(m, price); }

const rows = [];
const weights = {BH: [], CASH: [], FIX50: [], FIX60: [], SMA10: [], MOM12: []};
for (let i = 1; i < months.length; i++) {
  const m = months[i], t = months[i - 1];
  if (ym(m) < ym('1967-03')) continue;
  const past10 = months.slice(i - 10, i), past12 = months.slice(i - 12, i);
  assert(past10.length === 10 && past12.length === 12, 'signal warmup not met');
  assert(es.has(m) && cs.has(m), 'payoff missing at ' + m);
  for (const q of past12) assert(es.has(q) && cs.has(q), 'signal history missing at ' + q);
  const sma = idx.get(t) > avg(past10.map(q => idx.get(q))) ? 1 : 0;
  const excessLog = past12.reduce((a, q) => a + Math.log1p(es.get(q)) - Math.log1p(cs.get(q)), 0);
  const mom = excessLog > 0 ? 1 : 0;
  rows.push({ date: m, signal_month: t, equity: es.get(m), cash: cs.get(m), 
    market_index_signal: idx.get(t), excess12_log: excessLog, sma10: sma, mom12: mom });
  for (const [key, w] of Object.entries({BH: 1, CASH: 0, FIX50: .5, FIX60: .6, SMA10: sma, MOM12: mom})) weights[key].push(w);
}
assert(rows.length === 714 && rows.at(-1).date === '2026-08', 'unexpected common panel');
for (const r of rows) assert(ym(r.signal_month) === ym(r.date) - 1, 'lookahead!');

// Fixed exposure matches are FULL-SAMPLE lookback diagnostics, NOT ex-ante tradable controls.
weights.MATCH_SMA10 = Array(rows.length).fill(avg(weights.SMA10));
weights.MATCH_MOM12 = Array(rows.length).fill(avg(weights.MOM12));

function backtest(w, fee) {
  return rows.map((r, i) => {
    const turnover = i ? Math.abs(w[i] - w[i - 1]) : 0; // initial position cost omitted for all
    return {...r, weight: w[i], turnover,
      net: r.equity * w[i] + r.cash * (1 - w[i]) - fee * turnover };
  });
}
function metrics(rs) {
  assert(rs.length > 1, 'too short to estimate volatility');
  const n = rs.length, returns = rs.map(x => x.net), mean = avg(returns);
  const sd = Math.sqrt(returns.reduce((a, r) => a + (r - mean) ** 2, 0) / (n - 1));
  let wealth = 1, high = 1, dd = 0, worst = Infinity, turnover = 0, switches = 0;
  let positiveN = 0, negativeN = 0, upPart = 0, downPart = 0, missed = 0, avoided = 0;
  for (const x of rs) {
    wealth *= 1 + x.net;
    high = Math.max(high, wealth);
    dd = Math.min(dd, wealth / high - 1);
    worst = Math.min(worst, x.net);
    turnover += x.turnover;
    if (x.turnover > 0) switches++;
    if (x.equity > 0) { positiveN++; upPart += x.weight; }
    if (x.equity < 0) { negativeN++; downPart += x.weight; }
    if (x.equity > 0 && x.equity > x.cash) missed += (1 - x.weight) * (x.equity - x.cash);
    if (x.equity < 0 && x.equity < x.cash) avoided += (1 - x.weight) * (x.cash - x.equity);
  }
  return {
    n, first: rs[0].date, last: rs.at(-1).date,
    cagr: wealth ** (12 / n) - 1,
    vol: sd * Math.sqrt(12),
    sharpe_like: sd ? Math.sqrt(12) * avg(rs.map(x => x.net - x.cash)) / sd : null,
    max_dd: dd, worst_month: worst, avg_equity: avg(rs.map(x => x.weight)),
    turnover_annual: turnover * 12 / n, switches,
    positive_market_months: positiveN, negative_market_months: negativeN,
    equity_participation_up: positiveN ? upPart / positiveN : null,
    equity_participation_down: negativeN ? downPart / negativeN : null,
    missed_upside_pp_uncompounded: missed * 100,
    avoided_downside_pp_uncompounded: avoided * 100,
    terminal_growth: wealth
  };
}
const eras = {
  E1: ['1967-03', '1979-12'],
  E2: ['1980-01', '1999-12'],
  E3: ['2000-01', '2019-12'],
  E4: ['2020-01', '2026-08']
};
const crises = {
  '1973-74': ['1973-01', '1974-12'],
  '1987': ['1987-08', '1987-12'],
  '2000-02': ['2000-03', '2002-10'],
  '2007-09': ['2007-10', '2009-03'],
  '2020': ['2020-02', '2020-04'],
  '2022': ['2022-01', '2022-12']
};
const select = (arr, lo, hi) => arr.filter(x => ym(x.date) >= ym(lo) && ym(x.date) <= ym(hi));
const sims = {}, results = {};
for (const [name, w] of Object.entries(weights)) {
  const run = backtest(w, .0002), fee10 = backtest(w, .001);
  sims[name] = run;
  const eraResults = Object.fromEntries(Object.entries(eras).map(([e, [lo, hi]]) => [e, metrics(select(run, lo, hi))]));
  const crisisResults = Object.fromEntries(Object.entries(crises).map(([e, [lo, hi]]) => {
    const subset = select(run, lo, hi);
    return [e, {return: subset.reduce((p, x) => p * (1 + x.net), 1) - 1, 
      avg_equity: avg(subset.map(x => x.weight)), n: subset.length}];
  }));
  results[name] = {full: metrics(run), fee10bp: metrics(fee10), eras: eraResults, crises: crisisResults};
}
const sha256 = filename => crypto.createHash('sha256').update(fs.readFileSync(filename)).digest('hex');
const summary = {
  study: 'classic_equity_baselines', prereg_commit: '3445dc46f23a72697d154cc44358295f0719e7a9',
  source_ref: '1fabf0f9c94c391a7c2d302caff6bbdf56062d95',
  source: {eq_rows: eqRows.length, cash_rows: cashRows.length, equity_sha256: sha256(EQUITY),
    cash_sha256: sha256(CASH), eq_start: eqRows[0].date, eq_end: eqRows.at(-1).date,
    cash_start: cashRows[0].date, cash_end: cashRows.at(-1).date},
  panel: {n: rows.length, first: rows[0].date, last: rows.at(-1).date},
  labels: {equity: 'Fama-French broad-US equity total returns, not S&P500',
    mom12: 'restricted equity-long/cash excess momentum, not original futures strategy',
    historical: 'revised-vintage, in-sample, monthly, no macro'},
  production_authorized: false,
  results
};
fs.mkdirSync(OUT, {recursive: true});
fs.writeFileSync(path.join(OUT, 'performance.json'), JSON.stringify(summary, null, 2) + '\n');
const cols = ['date', 'signal_month', 'equity', 'cash', 'market_index_signal', 'excess12_log',
  'sma10', 'mom12', 'sma10_net_2bp', 'mom12_net_2bp', 'bh_net', 'fix50_net', 'fix60_net',
  'match_sma_net', 'match_mom_net'];
const csv = [cols.join(',')];
for (let i = 0; i < rows.length; i++) {
  const r = rows[i];
  csv.push([r.date, r.signal_month, r.equity, r.cash, r.market_index_signal, r.excess12_log,
    r.sma10, r.mom12, sims.SMA10[i].net, sims.MOM12[i].net, sims.BH[i].net,
    sims.FIX50[i].net, sims.FIX60[i].net, sims.MATCH_SMA10[i].net, sims.MATCH_MOM12[i].net].join(','));
}
fs.writeFileSync(path.join(OUT, 'monthly.csv'), csv.join('\n') + '\n');
console.log('Built', rows.length, 'common months; no macro data; outputs:', OUT);
console.log(Object.fromEntries(Object.entries(results).map(([k, v]) => 
  [k, {cagr: v.full.cagr, max_dd: v.full.max_dd, avg_equity: v.full.avg_equity}])));
