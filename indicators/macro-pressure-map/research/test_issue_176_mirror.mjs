// Issue #176 — Node mirror of Python stdlib tests (executed; no Python runtime).
import assert from "node:assert";
function sp500(pp, pc, d) {
  if (!isFinite(pp) || !isFinite(pc) || pp === 0 || !isFinite(d)) return NaN;
  return pc / pp - 1 + d / 12 / pp;
}
function oil(fp, fc, tb) {
  if (!isFinite(fp) || !isFinite(fc) || fp === 0 || !isFinite(tb)) return NaN;
  return (1 + (fc / fp - 1)) * (1 + tb / 1200) - 1;
}
function wedge(tp, tc, pp, pc) {
  if (![tp, tc, pp, pc].every(isFinite) || tp === 0 || pp === 0) return NaN;
  return tc / tp - 1 - (pc / pp - 1);
}
assert.ok(Math.abs(sp500(100, 110, 3) - 0.1025) < 1e-12);
assert.ok(Number.isNaN(sp500(0, 1, 3)));
assert.ok(Math.abs(oil(50, 50, 12) - 0.01) < 1e-12);
assert.ok(Math.abs(oil(50, 55, 0) - 0.10) < 1e-12);
assert.ok(Math.abs(wedge(100, 101, 100, 100.5) - 0.005) < 1e-12);
console.log("issue-176 Node mirror tests: ALL PASS (5 assertions)");
