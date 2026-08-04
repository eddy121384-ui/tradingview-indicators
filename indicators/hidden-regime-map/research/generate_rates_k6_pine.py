#!/usr/bin/env python3
"""Generate the U.S. Rates K=6 Pine visual prototype from a frozen JSON profile."""

from __future__ import annotations

import argparse
import json
import math
from pathlib import Path
from typing import Any

STATE_COUNT = 6
FEATURE_COUNT = 5


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate K=6 rates Pine from profile")
    parser.add_argument("--profile", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    return parser.parse_args()


def number(value: Any) -> str:
    value = float(value)
    if not math.isfinite(value):
        raise ValueError("Pine profile contains a non-finite number")
    if value == 0.0:
        return "0.0"
    text = format(value, ".17g")
    if "e" not in text and "." not in text:
        text += ".0"
    return text


def flat(values: list[list[float]]) -> list[float]:
    return [item for row in values for item in row]


def array_literal(values: list[float]) -> str:
    return "array.from(" + ", ".join(number(value) for value in values) + ")"


def validate_profile(profile: dict[str, Any]) -> None:
    if profile.get("hmm", {}).get("state_count") != STATE_COUNT:
        raise ValueError("profile must contain exactly six states")
    if len(profile.get("feature_names", [])) != FEATURE_COUNT:
        raise ValueError("profile must contain exactly five features")
    hmm = profile["hmm"]
    if len(hmm["start_probability"]) != STATE_COUNT:
        raise ValueError("invalid start-probability length")
    if len(hmm["transition_matrix"]) != STATE_COUNT or any(
        len(row) != STATE_COUNT for row in hmm["transition_matrix"]
    ):
        raise ValueError("invalid transition dimensions")
    if len(hmm["emission_means"]) != STATE_COUNT or any(
        len(row) != FEATURE_COUNT for row in hmm["emission_means"]
    ):
        raise ValueError("invalid emission-mean dimensions")
    if len(hmm["emission_variances"]) != STATE_COUNT or any(
        len(row) != FEATURE_COUNT for row in hmm["emission_variances"]
    ):
        raise ValueError("invalid emission-variance dimensions")


def generate(profile: dict[str, Any]) -> str:
    validate_profile(profile)
    hmm = profile["hmm"]
    scaler = profile["scaler"]
    symbols = profile["requested_symbols"]
    drift = profile["instability_diagnostics"]
    cutoff = profile["provenance"]["feature_last_date"]
    profile_id = profile["profile_id"]

    start = array_literal(hmm["start_probability"])
    transition = array_literal(flat(hmm["transition_matrix"]))
    means = array_literal(flat(hmm["emission_means"]))
    variances = array_literal(flat(hmm["emission_variances"]))
    scaler_mean = array_literal(scaler["mean"])
    scaler_scale = array_literal(scaler["scale"])

    return f'''//@version=6
indicator("Hidden Regime Map — U.S. Rates K=6 Visual", shorttitle = "HRM Rates K6", overlay = true, max_bars_back = 5000)

// Descriptive full-sample reference profile. Historical colors are retrospective
// classifications, not historical out-of-sample evidence or trading signals.
const string PROFILE_ID = "{profile_id}"
const string PROFILE_CUTOFF = "{cutoff}"
const int K = 6
const int F = 5
const float EPSILON = 1e-300
const float TWO_PI = 6.283185307179586
const int VOL_WINDOW = 20
const int CONCENTRATION_WINDOW = {int(drift['state_concentration_window_bars'])}
const float DRIFT_THRESHOLD = {number(drift['feature_drift_threshold'])}
const float CONCENTRATION_THRESHOLD = {number(drift['state_concentration_threshold'])}

string symbol2Y = input.symbol("{symbols['DGS2']}", "2Y yield", group = "Rates data")
string symbol5Y = input.symbol("{symbols['DGS5']}", "5Y yield", group = "Rates data")
string symbol10Y = input.symbol("{symbols['DGS10']}", "10Y yield", group = "Rates data")
string symbol30Y = input.symbol("{symbols['DGS30']}", "30Y yield", group = "Rates data")
bool showBackground = input.bool(true, "Shade dominant regime", group = "Display")
bool showTransitions = input.bool(true, "Show transitions", group = "Display")
bool showDashboard = input.bool(true, "Show dashboard", group = "Display")

float y2 = request.security(symbol2Y, "D", close, gaps = barmerge.gaps_on, lookahead = barmerge.lookahead_off, ignore_invalid_symbol = true)
float y5 = request.security(symbol5Y, "D", close, gaps = barmerge.gaps_on, lookahead = barmerge.lookahead_off, ignore_invalid_symbol = true)
float y10 = request.security(symbol10Y, "D", close, gaps = barmerge.gaps_on, lookahead = barmerge.lookahead_off, ignore_invalid_symbol = true)
float y30 = request.security(symbol30Y, "D", close, gaps = barmerge.gaps_on, lookahead = barmerge.lookahead_off, ignore_invalid_symbol = true)

bool supportedTimeframe = timeframe.isdaily and timeframe.multiplier == 1
bool commonObservation = supportedTimeframe and not na(y2) and not na(y5) and not na(y10) and not na(y30)
float curveLevel = commonObservation ? (y2 + y5 + y10 + y30) / 4.0 : na
float slope2s10s = commonObservation ? y10 - y2 : na
float slope5s30s = commonObservation ? y30 - y5 : na

var float previousCurveLevel = na
var float[] levelChanges = array.new_float()
float levelChangeBp = na
float levelVol20Bp = na
bool modelUpdate = false

if barstate.isconfirmed and commonObservation
    if not na(previousCurveLevel)
        levelChangeBp := (curveLevel - previousCurveLevel) * 100.0
        array.push(levelChanges, levelChangeBp)
        if array.size(levelChanges) > VOL_WINDOW
            array.shift(levelChanges)
    previousCurveLevel := curveLevel
    if array.size(levelChanges) == VOL_WINDOW
        float meanChange = 0.0
        for i = 0 to VOL_WINDOW - 1
            meanChange += array.get(levelChanges, i)
        meanChange /= VOL_WINDOW
        float varianceChange = 0.0
        for i = 0 to VOL_WINDOW - 1
            float delta = array.get(levelChanges, i) - meanChange
            varianceChange += delta * delta
        levelVol20Bp := math.sqrt(varianceChange / VOL_WINDOW)
        modelUpdate := true

var float[] scalerMean = {scaler_mean}
var float[] scalerScale = {scaler_scale}
var float[] startProb = {start}
var float[] transition = {transition}
var float[] emissionMean = {means}
var float[] emissionVariance = {variances}
var float[] logAlpha = array.new_float(K, na)
var float[] posterior = array.new_float(K, na)
var int[] stateHistory = array.new_int()
var bool initialized = false
var int dominantState = na
var int previousDominantState = na
var int stateDuration = 0
var float rollingConcentration = na
var float maxAbsFeatureZ = na

f_logsumexp(float[] values) =>
    float maximum = array.get(values, 0)
    for i = 1 to array.size(values) - 1
        maximum := math.max(maximum, array.get(values, i))
    float total = 0.0
    for i = 0 to array.size(values) - 1
        total += math.exp(array.get(values, i) - maximum)
    maximum + math.log(total)

f_log_emission(int state, float[] x) =>
    float result = 0.0
    for feature = 0 to F - 1
        int offset = state * F + feature
        float variance = array.get(emissionVariance, offset)
        float delta = array.get(x, feature) - array.get(emissionMean, offset)
        result += math.log(TWO_PI * variance) + delta * delta / variance
    -0.5 * result

if modelUpdate
    float[] x = array.from(
         (curveLevel - array.get(scalerMean, 0)) / array.get(scalerScale, 0),
         (slope2s10s - array.get(scalerMean, 1)) / array.get(scalerScale, 1),
         (slope5s30s - array.get(scalerMean, 2)) / array.get(scalerScale, 2),
         (levelChangeBp - array.get(scalerMean, 3)) / array.get(scalerScale, 3),
         (levelVol20Bp - array.get(scalerMean, 4)) / array.get(scalerScale, 4))
    maxAbsFeatureZ := 0.0
    for feature = 0 to F - 1
        maxAbsFeatureZ := math.max(maxAbsFeatureZ, math.abs(array.get(x, feature)))

    float[] raw = array.new_float(K, na)
    if not initialized
        for state = 0 to K - 1
            array.set(raw, state, math.log(math.max(array.get(startProb, state), EPSILON)) + f_log_emission(state, x))
    else
        for current = 0 to K - 1
            float[] incoming = array.new_float(K, na)
            for previous = 0 to K - 1
                float probability = array.get(transition, previous * K + current)
                array.set(incoming, previous, array.get(logAlpha, previous) + math.log(math.max(probability, EPSILON)))
            array.set(raw, current, f_logsumexp(incoming) + f_log_emission(current, x))

    float normalizer = f_logsumexp(raw)
    float bestProbability = -1.0
    int bestState = 0
    for state = 0 to K - 1
        float normalized = array.get(raw, state) - normalizer
        float probability = math.exp(normalized)
        array.set(logAlpha, state, normalized)
        array.set(posterior, state, probability)
        if probability > bestProbability
            bestProbability := probability
            bestState := state

    previousDominantState := dominantState
    dominantState := bestState
    stateDuration := initialized and dominantState == previousDominantState ? stateDuration + 1 : 1
    initialized := true

    array.push(stateHistory, dominantState)
    if array.size(stateHistory) > CONCENTRATION_WINDOW
        array.shift(stateHistory)
    if array.size(stateHistory) == CONCENTRATION_WINDOW
        int[] counts = array.new_int(K, 0)
        for i = 0 to array.size(stateHistory) - 1
            int state = array.get(stateHistory, i)
            array.set(counts, state, array.get(counts, state) + 1)
        int largestCount = 0
        for state = 0 to K - 1
            largestCount := math.max(largestCount, array.get(counts, state))
        rollingConcentration := float(largestCount) / CONCENTRATION_WINDOW

float p1 = initialized ? array.get(posterior, 0) : na
float p2 = initialized ? array.get(posterior, 1) : na
float p3 = initialized ? array.get(posterior, 2) : na
float p4 = initialized ? array.get(posterior, 3) : na
float p5 = initialized ? array.get(posterior, 4) : na
float p6 = initialized ? array.get(posterior, 5) : na
float probabilitySum = p1 + p2 + p3 + p4 + p5 + p6
float maxPosterior = initialized ? math.max(p1, math.max(p2, math.max(p3, math.max(p4, math.max(p5, p6))))) : na
float secondPosterior = na
if initialized
    float[] ranked = array.copy(posterior)
    array.sort(ranked, order.descending)
    secondPosterior := array.get(ranked, 1)
float posteriorMargin = initialized ? maxPosterior - secondPosterior : na

color[] regimeColors = array.from(
     color.rgb(56, 96, 160),
     color.rgb(54, 132, 126),
     color.rgb(104, 142, 76),
     color.rgb(184, 145, 51),
     color.rgb(184, 92, 58),
     color.rgb(143, 68, 121))
color currentColor = initialized ? array.get(regimeColors, dominantState) : na
int backgroundTransparency = initialized ? int(math.round(92.0 - 62.0 * maxPosterior)) : 100
bgcolor(showBackground and initialized ? color.new(currentColor, math.max(20, math.min(92, backgroundTransparency))) : na)

bool transitionEvent = modelUpdate and initialized and not na(previousDominantState) and dominantState != previousDominantState
plotshape(showTransitions and transitionEvent, title = "Rates regime transition", style = shape.labeldown, location = location.top, text = "R", color = currentColor, textcolor = color.white, size = size.tiny)

bool driftWarning = initialized and maxAbsFeatureZ >= DRIFT_THRESHOLD
bool concentrationWarning = initialized and not na(rollingConcentration) and rollingConcentration >= CONCENTRATION_THRESHOLD

var table dashboard = table.new(position.top_right, 2, 13, border_width = 1)
if showDashboard and barstate.islast
    string regimeText = initialized ? "R" + str.tostring(dominantState + 1) : "warming up"
    table.cell(dashboard, 0, 0, "Rates K=6", text_color = color.white, bgcolor = color.rgb(35, 39, 48))
    table.cell(dashboard, 1, 0, regimeText, text_color = color.white, bgcolor = initialized ? currentColor : color.gray)
    table.cell(dashboard, 0, 1, "Posterior max")
    table.cell(dashboard, 1, 1, initialized ? str.tostring(maxPosterior, "#.000") : "—")
    table.cell(dashboard, 0, 2, "Top-two margin")
    table.cell(dashboard, 1, 2, initialized ? str.tostring(posteriorMargin, "#.000") : "—")
    table.cell(dashboard, 0, 3, "Duration")
    table.cell(dashboard, 1, 3, initialized ? str.tostring(stateDuration) + " obs" : "—")
    table.cell(dashboard, 0, 4, "Curve level")
    table.cell(dashboard, 1, 4, not na(curveLevel) ? str.tostring(curveLevel, "#.000") + "%" : "—")
    table.cell(dashboard, 0, 5, "2s10s")
    table.cell(dashboard, 1, 5, not na(slope2s10s) ? str.tostring(slope2s10s * 100.0, "#.0") + " bp" : "—")
    table.cell(dashboard, 0, 6, "5s30s")
    table.cell(dashboard, 1, 6, not na(slope5s30s) ? str.tostring(slope5s30s * 100.0, "#.0") + " bp" : "—")
    table.cell(dashboard, 0, 7, "R1…R3")
    table.cell(dashboard, 1, 7, initialized ? str.format("{{0,number,#.00}} {{1,number,#.00}} {{2,number,#.00}}", p1, p2, p3) : "—")
    table.cell(dashboard, 0, 8, "R4…R6")
    table.cell(dashboard, 1, 8, initialized ? str.format("{{0,number,#.00}} {{1,number,#.00}} {{2,number,#.00}}", p4, p5, p6) : "—")
    table.cell(dashboard, 0, 9, "Feature drift")
    table.cell(dashboard, 1, 9, initialized ? str.tostring(maxAbsFeatureZ, "#.00") + (driftWarning ? " ⚠" : "") : "—", bgcolor = driftWarning ? color.new(color.orange, 20) : na)
    table.cell(dashboard, 0, 10, "126-observation concentration")
    table.cell(dashboard, 1, 10, not na(rollingConcentration) ? str.tostring(rollingConcentration, "#.0%") + (concentrationWarning ? " ⚠" : "") : "—", bgcolor = concentrationWarning ? color.new(color.orange, 20) : na)
    table.cell(dashboard, 0, 11, "Profile")
    table.cell(dashboard, 1, 11, PROFILE_ID)
    table.cell(dashboard, 0, 12, "Boundary")
    table.cell(dashboard, 1, 12, supportedTimeframe ? "retrospective ≤ " + PROFILE_CUTOFF : "1D only", text_color = supportedTimeframe ? color.silver : color.white, bgcolor = supportedTimeframe ? na : color.red)

// Data-window/export diagnostics for Python-to-Pine comparison.
plot(y2, "HRM Rates 2Y", display = display.data_window)
plot(y5, "HRM Rates 5Y", display = display.data_window)
plot(y10, "HRM Rates 10Y", display = display.data_window)
plot(y30, "HRM Rates 30Y", display = display.data_window)
plot(curveLevel, "HRM Rates Curve Level", display = display.data_window)
plot(slope2s10s, "HRM Rates 2s10s", display = display.data_window)
plot(slope5s30s, "HRM Rates 5s30s", display = display.data_window)
plot(levelChangeBp, "HRM Rates Level Change BP", display = display.data_window)
plot(levelVol20Bp, "HRM Rates Level Vol 20 BP", display = display.data_window)
plot(p1, "HRM Rates Posterior R1", display = display.data_window)
plot(p2, "HRM Rates Posterior R2", display = display.data_window)
plot(p3, "HRM Rates Posterior R3", display = display.data_window)
plot(p4, "HRM Rates Posterior R4", display = display.data_window)
plot(p5, "HRM Rates Posterior R5", display = display.data_window)
plot(p6, "HRM Rates Posterior R6", display = display.data_window)
plot(probabilitySum, "HRM Rates Probability Sum", display = display.data_window)
plot(initialized ? dominantState + 1 : na, "HRM Rates Dominant State", display = display.data_window)
plot(maxAbsFeatureZ, "HRM Rates Max Abs Feature Z", display = display.data_window)
plot(rollingConcentration, "HRM Rates Rolling State Concentration", display = display.data_window)
'''


def main() -> int:
    args = parse_args()
    if not args.profile.exists():
        raise FileNotFoundError(f"profile not found: {args.profile}")
    profile = json.loads(args.profile.read_text(encoding="utf-8"))
    script = generate(profile)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(script, encoding="utf-8")
    print(f"wrote: {args.output}")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (FileNotFoundError, ValueError, KeyError, TypeError) as exc:
        print(f"error: {exc}")
        raise SystemExit(2)
