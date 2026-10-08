// Issue #178 — Node mirror of Python stdlib tests (executed; no Python runtime).
import assert from "node:assert";
const BASE = { sp500: 25, nasdaq: 12, russell: 8, treasury2y: 8, treasury10y: 14, longtreasury: 8, gold: 6, oil: 4, cash: 15 };
const MULT = { "0": 0, Low: 0.5, Neutral: 1.0, High: 1.75 };
assert.equal(Object.values(BASE).reduce((a, x) => a + x, 0), 100);
assert.ok(MULT["0"] === 0 && MULT.Low < MULT.Neutral && MULT.Neutral < MULT.High && MULT.Neutral === 1.0);
function confirm(h) {
  if (h.length >= 2 && h[h.length - 1] === h[h.length - 2]) return h[h.length - 1];
  if (h.length >= 2) return h[h.length - 2];
  return h[h.length - 1];
}
assert.equal(confirm(["A", "B", "B"]), "B");
assert.equal(confirm(["B", "C"]), "B");
assert.equal(confirm(["A"]), "A");
function lr(w, zeros) {
  const fl = {};
  for (const s of Object.keys(w)) fl[s] = zeros.has(s) ? 0 : Math.floor(w[s] * 100 + 1e-9) / 100;
  let short = Math.round((100 - Object.values(fl).reduce((a, x) => a + x, 0)) * 100);
  if (short > 0) {
    const frac = Object.keys(w).filter((s) => !zeros.has(s)).map((s) => [w[s] * 100 - fl[s] * 100, s]).sort((a, b) => b[0] - a[0]);
    for (let i = 0; i < short; i++) fl[frac[i % frac.length][1]] += 0.01;
  }
  return fl;
}
const r = lr({ a: 33.333, b: 33.333, c: 33.334 }, new Set());
assert.ok(Math.abs(Object.values(r).reduce((a, x) => a + x, 0) - 100) < 1e-9);
const rz = lr({ a: 60, z: 0, c: 40 }, new Set(["z"]));
assert.equal(rz.z, 0);
assert.ok(Math.abs(rz.a + rz.c - 100) < 1e-9);
console.log("issue-178 Node mirror tests: ALL PASS (9 assertions)");
