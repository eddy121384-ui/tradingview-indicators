// Issue #177 — Node mirror of Python stdlib tests (executed; no Python runtime).
import assert from "node:assert";
function tier(ev, mx) {
  if (ev === "historically_favored") return "High";
  if (ev === "historically_unfavorable") return "Low";
  if (ev === "mixed") return Number.isFinite(mx) && mx >= 0 ? "Neutral" : "Low";
  if (ev === "insufficient_sample") return "Neutral";
  throw new Error("unknown");
}
function zeroB(ev, mx, hit, p10, we, pm, exw) {
  if (ev !== "historically_unfavorable") return false;
  if (!(Number.isFinite(mx) && mx < 0)) return false;
  if (!(Number.isFinite(hit) && hit <= 0.40)) return false;
  if (!((Number.isFinite(p10) && p10 <= -0.04) || (Number.isFinite(we) && we <= -0.15) || (Number.isFinite(pm) && pm >= 0.10))) return false;
  return Number.isFinite(exw) && exw < 0;
}
const PTS = { High: 2, Neutral: 1, Low: 0, "0": -1 };
function bias(s) { return s <= 3 ? "high" : s <= 8 ? "neutral" : "low"; }
assert.equal(tier("historically_favored", -9), "High");
assert.equal(tier("mixed", 0), "Neutral");
assert.equal(tier("mixed", -0.001), "Low");
assert.equal(tier("insufficient_sample", 9), "Neutral");
assert.equal(zeroB("historically_unfavorable", -0.01, 0.4, -0.04, 0, 0, -0.001), true);
assert.equal(zeroB("historically_unfavorable", -0.01, 0.41, -0.04, 0, 0, -0.001), false);
assert.equal(bias(3), "high");
assert.equal(bias(4), "neutral");
assert.equal(bias(8), "neutral");
assert.equal(bias(9), "low");
console.log("issue-177 Node mirror tests: ALL PASS (10 assertions)");
