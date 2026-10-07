// Issue #174 — Node mirror of Python stdlib tests (executed; Python has no runtime).
// Mirrors test_issue_174_nine_sleeve_backbone.py analytic vectors.
import assert from "node:assert";

function band(s) {
  if (!isFinite(s)) return "NA";
  if (s < -10) return "Low";
  if (s > 10) return "High";
  return "Neutral";
}
function stateOf(g, i) {
  const gb = band(g), ib = band(i);
  if (gb === "NA" || ib === "NA") return "NA";
  return "G_" + gb + "/I_" + ib;
}
function eraOf(mo) {
  if (mo >= "1966-03-01" && mo <= "1979-12-01") return "E1_pre_volcker";
  if (mo >= "1980-01-01" && mo <= "2007-12-01") return "E2_great_moderation";
  if (mo >= "2008-01-01" && mo <= "2019-12-01") return "E3_post_gfc_qe";
  if (mo >= "2020-01-01" && mo <= "2026-08-01") return "E4_post_2020";
  return "OUT";
}
function bondMonthly(yT, yNext, years) {
  if (!isFinite(yT) || !isFinite(yNext) || yT < 0 || yNext < 0) return NaN;
  const n = 2 * years;
  const coupon = (100 * yT) / 2, per = yNext / 2;
  let pv = 0;
  for (let k = 1; k <= n; k++) {
    const periods = 2 * (k / 2 - 1 / 12);
    pv += (coupon + (k === n ? 100 : 0)) * Math.pow(1 + per, -periods);
  }
  return pv / 100 - 1;
}
function pct(a, q) {
  const v = a.filter(isFinite).sort((x, y) => x - y);
  if (!v.length) return NaN;
  if (v.length === 1) return v[0];
  const pos = q * (v.length - 1), lo = Math.floor(pos), hi = Math.ceil(pos);
  if (lo === hi) return v[lo];
  return v[lo] * (hi - pos) + v[hi] * (pos - lo);
}
function classify(nM, nE, meanEx, posM, epHit, p10ex, worst, pUnder, pPos, pNeg) {
  if (nM < 24 || nE < 4) return "insufficient_sample";
  if (meanEx > 0.001 && posM >= 0.55 && epHit >= 0.60 && p10ex >= -0.04 && worst > -0.20 && !pNeg) return "historically_favored";
  if (meanEx < -0.0005 && (posM <= 0.45 || epHit <= 0.40) && (p10ex <= -0.03 || worst <= -0.10 || pUnder >= 0.60) && !pPos) return "historically_unfavorable";
  return "mixed";
}

// tests
assert.equal(band(-10), "Neutral");
assert.equal(band(10), "Neutral");
assert.equal(band(-10.0001), "Low");
assert.equal(stateOf(-11, -11), "G_Low/I_Low");
assert.equal(eraOf("1966-03-01"), "E1_pre_volcker");
assert.equal(eraOf("2026-09-01"), "OUT");
assert.ok(Math.abs(bondMonthly(0.06, 0.06, 10) - 0.06 / 12) < 0.001);
assert.ok(bondMonthly(0.05, 0.10, 10) < -0.02);
assert.ok(bondMonthly(0.10, 0.05, 10) > 0.02);
assert.ok(bondMonthly(0.05, 0.06, 20) < bondMonthly(0.05, 0.06, 2));
assert.ok(Math.abs(pct([0, 1, 2, 3, 4, 5, 6, 7, 8, 9], 0.10) - 0.9) < 1e-9);
assert.equal(classify(10, 2, 0.01, 0.9, 0.9, 0, 0, 0.1, false, false), "insufficient_sample");
assert.equal(classify(100, 10, 0.002, 0.6, 0.7, -0.01, -0.05, 0.4, false, false), "historically_favored");
assert.equal(classify(100, 10, -0.002, 0.4, 0.3, -0.05, -0.12, 0.6, false, false), "historically_unfavorable");
console.log("issue-174 Node mirror tests: ALL PASS (12 assertions)");
