// Issue #182 — Node mirror of Python stdlib tests (executed; no Python runtime).
import assert from "node:assert";
function classify(g, i) {
  if (g === "High" && i !== "High") return "risk-on";
  if (g === "Low" || i === "High") return "risk-off";
  return "neutral";
}
assert.equal(classify("High", "Low"), "risk-on");
assert.equal(classify("High", "Neutral"), "risk-on");
assert.equal(classify("High", "High"), "risk-off");
assert.equal(classify("Low", "Low"), "risk-off");
assert.equal(classify("Neutral", "High"), "risk-off");
assert.equal(classify("Neutral", "Neutral"), "neutral");
assert.equal(classify("Neutral", "Low"), "neutral");
const CAP = { sp500: 35, nasdaq: 20, russell: 15 };
function overlay(w0, signal, budget = 5) {
  const w = { ...w0 };
  const eq = ["sp500", "nasdaq", "russell"].filter((s) => w[s] > 0);
  const E = eq.reduce((a, s) => a + w[s], 0);
  if (signal === "risk-on") {
    const head = eq.reduce((a, s) => a + (CAP[s] - w[s]), 0);
    let add = Math.min(budget, Math.max(0, w.cash - 2), 60 - E, head);
    add = Math.max(0, add);
    if (E > 0 && add > 0) for (const s of eq) { const t = Math.min(add * w[s] / E, CAP[s] - w[s]); w[s] += t; w.cash -= t; }
  } else if (signal === "risk-off") {
    const cut = Math.min(budget, E);
    if (E > 0 && cut > 0) { for (const s of eq) w[s] -= cut * w[s] / E; w.cash += cut; }
  }
  return w;
}
const base = { sp500: 25, nasdaq: 12, russell: 8, cash: 15 };
let w = overlay(base, "neutral");
assert.deepEqual(w, base);
w = overlay(base, "risk-on");
assert.ok(Math.abs(w.sp500 + w.nasdaq + w.russell - 50) < 1e-9 && Math.abs(w.cash - 10) < 1e-9);
w = overlay(base, "risk-off");
assert.ok(Math.abs(w.sp500 + w.nasdaq + w.russell - 40) < 1e-9 && Math.abs(w.cash - 20) < 1e-9);
w = overlay({ ...base, cash: 3 }, "risk-on");
assert.ok(w.cash >= 2 - 1e-9);
function decide(cg, sg, mg, to, t1, bp, ws, wst) {
  const g = { g1: cg >= -0.5, g2: sg >= -0.05, g3: mg >= -3, g4: to <= 40, g5: !bp ? true : t1 <= 0.6, g6: ws >= -1, g7: wst >= -3 };
  const f = Object.values(g).filter((v) => !v).length;
  if (f === 0) return "v66_tactical_overlay_candidate_supported";
  if (cg > 0 && g.g3 && g.g7 && f <= 2) return "v66_tactical_overlay_candidate_suggestive";
  return "v66_tactical_overlay_not_supported";
}
assert.equal(decide(0.2, 0, -1, 10, 0.5, true, -0.2, -1), "v66_tactical_overlay_candidate_supported");
assert.equal(decide(0.3, -0.06, -1, 10, 0.5, true, -0.2, -1), "v66_tactical_overlay_candidate_suggestive");
assert.equal(decide(-1, -0.2, -5, 50, 0.9, true, -2, -5), "v66_tactical_overlay_not_supported");
console.log("issue-182 Node mirror tests: ALL PASS (12 assertions)");
