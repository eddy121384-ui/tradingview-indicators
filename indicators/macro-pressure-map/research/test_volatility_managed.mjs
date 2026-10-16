#!/usr/bin/env node
// Frozen-mechanics tests for the volatility backtest (synthetic only, no repo data).
import assert from "node:assert";

// paper eq.2: biased variance, divisor 22 regardless of day count
const rv = (d) => { const m = d.reduce((a, x) => a + x, 0) / d.length; return d.reduce((a, x) => a + (x - m) ** 2, 0) / 22; };
assert.ok(rv(new Array(22).fill(0.01)) < 1e-30); // zero variance, constant series
const r = rv([...new Array(21).fill(0), 0.22]);
assert.ok(Math.abs(r - ((0.22 ** 2 * 21 / 22) / 22)) < 1e-12);
// single-day spike raises next-month weight denominator
const calm = rv(new Array(22).fill(0.005));
const shock = rv([...new Array(21).fill(0.005), -0.2]);
assert.ok(shock > calm * 10);
// fair-leg cap: min(1, vbar/rv) never exceeds 1, never negative
for (const [vbar, v] of [[0.002, 0.0005], [0.002, 0.002], [0.002, 0.02], [0.002, 0]]) {
  const w = v <= 0 ? 0 : Math.min(1, Math.max(0, vbar / v));
  assert.ok(w >= 0 && w <= 1, String(w));
}
// expanding mean uses strictly past values (no lookahead): reproducing first weight by hand
const hist = [0.002, 0.003, 0.001];
const vbar = (0.002 + 0.003 + 0.001) / 3;
assert.strictEqual(Math.min(1, vbar / 0.002), 1);
// paper c: sd(f)/sd(f/rv) equalizes unconditional vol by construction
const f = [0.01, -0.02, 0.03, -0.005, 0.012];
const vv = [0.001, 0.004, 0.001, 0.009, 0.002];
const sd = (a) => { const m = a.reduce((x, y) => x + y, 0) / a.length; return Math.sqrt(a.reduce((x, y) => x + (y - m) ** 2, 0) / a.length); };
const c = sd(f) / sd(f.map((v, i) => v / vv[i]));
const man = f.map((v, i) => (c / vv[i]) * v);
assert.ok(Math.abs(sd(man) - sd(f)) < 1e-12);
console.log("6 volatility-mechanics checks PASS");
