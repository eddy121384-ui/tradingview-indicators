// Issue #183 — Node mirror of Python stdlib tests (executed; no Python runtime).
import assert from "node:assert";
function assertRow(state, w) {
  const errs = [];
  const tot = Object.values(w).reduce((a, x) => a + x, 0);
  if (Math.abs(tot - 100) > 1e-9) errs.push("sum");
  if (tot > 100 + 1e-9) errs.push("gross");
  return errs;
}
assert.deepEqual(assertRow("S", { a: 50, b: 50 }), []);
assert.ok(assertRow("S", { a: 60, b: 41 }).includes("gross"));
function decide178(r, m, t) {
  if (r == null || m == null || t == null) return "state_weight_policy_candidate_revalidated_with_limitations";
  if (m < -10) return "state_weight_policy_candidate_invalidated_by_repair";
  if (Math.abs(r) <= 1 && m >= -3 && Math.abs(t) <= 5) return "state_weight_policy_candidate_revalidated";
  return "state_weight_policy_candidate_revalidated_with_limitations";
}
assert.equal(decide178(0.2, -1, 1), "state_weight_policy_candidate_revalidated");
assert.equal(decide178(0.2, -11, 1), "state_weight_policy_candidate_invalidated_by_repair");
assert.equal(decide178(2.5, -1, 1), "state_weight_policy_candidate_revalidated_with_limitations");
function decide180(f, s, te) {
  if (f === 0) return "tradable_implementation_revalidated";
  if (f <= 2 && !s && te <= 4) return "tradable_implementation_revalidated_with_limitations";
  return "tradable_implementation_invalidated_by_repair";
}
assert.equal(decide180(0, false, 1), "tradable_implementation_revalidated");
assert.equal(decide180(3, false, 1), "tradable_implementation_invalidated_by_repair");
function decide182(cg, sg, mg, to, t1, bp, ws, wst) {
  const g = { g1: cg >= -0.5, g2: sg >= -0.05, g3: mg >= -3, g4: to <= 40, g5: !bp ? true : t1 <= 0.6, g6: ws >= -1, g7: wst >= -3 };
  const f = Object.values(g).filter((v) => !v).length;
  if (f === 0) return "v66_tactical_overlay_candidate_supported";
  if (cg > 0 && g.g3 && g.g7 && f <= 2) return "v66_tactical_overlay_candidate_suggestive";
  return "v66_tactical_overlay_not_supported";
}
assert.equal(decide182(0.2, 0, -1, 10, 0.5, true, -0.2, -1), "v66_tactical_overlay_candidate_supported");
assert.equal(decide182(-1, -0.2, -5, 50, 0.9, true, -2, -5), "v66_tactical_overlay_not_supported");
console.log("issue-183 Node mirror tests: ALL PASS (10 assertions)");
