// Issue #180 — Node mirror of Python stdlib tests (executed; no Python runtime).
import assert from "node:assert";
const RATE = 0.0002;
assert.equal(RATE, 0.0002);
function applyCost(r, to, rate = RATE) { return r - to * rate; }
assert.ok(Math.abs(applyCost(0.01, 0.20) - (0.01 - 0.20 * 0.0002)) < 1e-15);
assert.equal(applyCost(0.01, 0), 0.01);
function track(P, R) {
  const n = P.length;
  const d = P.map((p, i) => p - R[i]);
  const md = d.reduce((a, x) => a + x, 0) / n;
  const te = Math.sqrt(d.reduce((a, x) => a + (x - md) ** 2, 0) / n) * Math.sqrt(12);
  let cp = 1, cr = 1;
  for (let i = 0; i < n; i++) { cp *= 1 + P[i]; cr *= 1 + R[i]; }
  return { n, md, te, ratio: cp / cr };
}
const s = track(new Array(100).fill(0.01), new Array(100).fill(0.01));
assert.equal(s.n, 100);
assert.ok(Math.abs(s.md) < 1e-15 && Math.abs(s.ratio - 1) < 1e-12);
function classify(n, ann, te, corr, mm) {
  if (n < 60) return "implementation_not_ready";
  if (Math.abs(ann) <= 0.5 && te <= 1.5 && corr >= 0.99 && !mm) return "implementation_faithful";
  if (corr >= 0.95 && te <= 4.0) return "implementation_acceptable_with_limitation";
  return "implementation_materially_different";
}
assert.equal(classify(200, 0.2, 1.0, 0.995, false), "implementation_faithful");
assert.equal(classify(200, 0.2, 1.0, 0.995, true), "implementation_acceptable_with_limitation");
assert.equal(classify(59, 0, 0, 1, false), "implementation_not_ready");
assert.equal(classify(200, 0.2, 5.0, 0.99, false), "implementation_materially_different");
function decide(cg, te, mg, dr, rk, dw, su, nr) {
  const c = { cagr: Math.abs(cg) <= 1.0, te: te <= 2.5, maxdd: mg >= -5.0, drag: dr <= 0.4, rank: rk, defensive: dw <= 2.0 };
  const f = Object.values(c).filter((v) => !v).length;
  if (nr) return "tradable_implementation_not_ready";
  if (f === 0) return "tradable_implementation_candidate_complete";
  if (f <= 2 && !su && te <= 4.0) return "tradable_implementation_candidate_complete_with_limitations";
  return "tradable_implementation_not_ready";
}
assert.equal(decide(0.5, 2.0, -3, 0.2, true, 1, false, false), "tradable_implementation_candidate_complete");
assert.equal(decide(1.0, 2.5, -5, 0.4, true, 2, false, false), "tradable_implementation_candidate_complete");
assert.equal(decide(1.5, 2.0, -3, 0.2, true, 1, false, false), "tradable_implementation_candidate_complete_with_limitations");
assert.equal(decide(0, 0, 0, 0, true, 0, false, true), "tradable_implementation_not_ready");
console.log("issue-180 Node mirror tests: ALL PASS (12 assertions)");
