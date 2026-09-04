#!/usr/bin/env python3
"""Generate Issue #68 FR10Y vs DE10Y NegSlopeDull transformation audit Pine."""
from __future__ import annotations

import argparse
from pathlib import Path

import generate_issue68_phase_b_lifecycle_pine as phase_b
from generate_price_only_parity_pine import SOURCE_RELATIVE, replace_once

HERE = Path(__file__).resolve().parent
AUDIT_DECL = 'indicator("Chase Risk Radar｜Issue #68 NegSlope Transform", shorttitle="ChaseRisk #68 NegSlope", overlay=false, precision=3)'

BODY = r'''

// ============================================================================
// Issue #68 FR10Y vs DE10Y NegSlopeDull Transformation Audit.
// Shared window: 2022-01-03 -> 2023-12-29, expected Bull yield regime.
// DISCOVERY ONLY. NO PNL. NO TUNING. FROZEN C-2.
// ============================================================================

groupIssue68NST = "Issue #68｜NegSlope Transform"
showIssue68NSTTable = input.bool(true, "顯示 NegSlope transform 表", group=groupIssue68NST)

int issue68NSTStart = timestamp(2022, 1, 3, 0, 0)
int issue68NSTEnd = timestamp(2023, 12, 29, 23, 59)
bool issue68NSTInWindow = time >= issue68NSTStart and time <= issue68NSTEnd
bool issue68NSTBaseValid = issue68NSTInWindow and not na(accRaw) and not na(markupRaw) and not na(accEff) and not na(markupEff) and not na(speedZ) and not na(speedRank) and not na(negSlopeDullScore)
bool issue68NSTFlip = issue68NSTBaseValid and accRaw >= markupRaw and markupEff > accEff
bool issue68NSTNoFlip = issue68NSTBaseValid and accRaw >= markupRaw and not (markupEff > accEff)

f_issue68NSTAvg(float s, int n) => n > 0 ? s / n : na
f_issue68NSTFmt(float x) => na(x) ? "NA" : str.tostring(x, "#.##")
f_issue68NSTFmtN(float s, int n) => n > 0 ? str.tostring(s / n, "#.##") + " (" + str.tostring(n) + ")" : "NA"
f_issue68NSTPct(int n, int d) => d > 0 ? str.tostring(100.0 * n / d, "#.##") + "%" : "NA"

// --- Frozen production chain plus diagnostic shadows ---
float issue68NSTRegCloseNow = ta.linreg(close, speedLen, 0)
float issue68NSTRegClosePrev = ta.linreg(close, speedLen, 1)
float issue68NSTBpSlope20 = (issue68NSTRegCloseNow - issue68NSTRegClosePrev) * speedLen * 100.0
float issue68NSTBpRankFull = ta.percentrank(issue68NSTBpSlope20, rankLen)

float issue68NSTRegLogNow = ta.linreg(logPrice, speedLen, 0)
float issue68NSTRegLogPrev = ta.linreg(logPrice, speedLen, 1)
float issue68NSTLogSlopeTotal = (issue68NSTRegLogNow - issue68NSTRegLogPrev) * speedLen
float issue68NSTLogMovePct = not na(issue68NSTLogSlopeTotal) ? (math.exp(issue68NSTLogSlopeTotal) - 1.0) * 100.0 : na
float issue68NSTBpSlopePositive = not na(issue68NSTLogSlopeTotal) ? issue68NSTBpSlope20 : na
float issue68NSTBpRankPositive = ta.percentrank(issue68NSTBpSlopePositive, rankLen)
float issue68NSTLogSlopeRank = ta.percentrank(issue68NSTLogSlopeTotal, rankLen)
float issue68NSTVolPct = vol * 100.0
float issue68NSTSpeedZRecon = not na(issue68NSTLogSlopeTotal) and not na(vol) and vol != 0.0 ? issue68NSTLogSlopeTotal / (vol * math.sqrt(speedLen)) : na
float issue68NSTReconErr = not na(issue68NSTSpeedZRecon) and not na(speedZ) ? math.abs(issue68NSTSpeedZRecon - speedZ) : na

float issue68NSTPositiveShare = ta.sma(close > 0.0 ? 1.0 : 0.0, rankLen) * 100.0
float issue68NSTSpeedValidShare = ta.sma(not na(speedZ) ? 1.0 : 0.0, rankLen) * 100.0

float issue68NSTShiftFullPos = not na(issue68NSTBpRankFull) and not na(issue68NSTBpRankPositive) ? issue68NSTBpRankPositive - issue68NSTBpRankFull : na
float issue68NSTShiftPosLog = not na(issue68NSTBpRankPositive) and not na(issue68NSTLogSlopeRank) ? issue68NSTLogSlopeRank - issue68NSTBpRankPositive : na
float issue68NSTShiftLogSpeed = not na(issue68NSTLogSlopeRank) and not na(speedRank) ? speedRank - issue68NSTLogSlopeRank : na

// --- Base population counts ---
var int issue68NSTNAll = 0
var int issue68NSTNFlip = 0
var int issue68NSTNNoFlip = 0

if issue68NSTBaseValid
    issue68NSTNAll += 1
    issue68NSTNFlip += issue68NSTFlip ? 1 : 0
    issue68NSTNNoFlip += issue68NSTNoFlip ? 1 : 0

// --- Metric accumulators; each row carries its own valid N. ---
var float issue68NSTSumBpAll = 0.0
var float issue68NSTSumBpFlip = 0.0
var float issue68NSTSumBpNo = 0.0
var int issue68NSTNBpAll = 0
var int issue68NSTNBpFlip = 0
var int issue68NSTNBpNo = 0

var float issue68NSTSumBpRankAll = 0.0
var float issue68NSTSumBpRankFlip = 0.0
var float issue68NSTSumBpRankNo = 0.0
var int issue68NSTNBpRankAll = 0
var int issue68NSTNBpRankFlip = 0
var int issue68NSTNBpRankNo = 0

var float issue68NSTSumBpPosRankAll = 0.0
var float issue68NSTSumBpPosRankFlip = 0.0
var float issue68NSTSumBpPosRankNo = 0.0
var int issue68NSTNBpPosRankAll = 0
var int issue68NSTNBpPosRankFlip = 0
var int issue68NSTNBpPosRankNo = 0

var float issue68NSTSumLogMoveAll = 0.0
var float issue68NSTSumLogMoveFlip = 0.0
var float issue68NSTSumLogMoveNo = 0.0
var int issue68NSTNLogMoveAll = 0
var int issue68NSTNLogMoveFlip = 0
var int issue68NSTNLogMoveNo = 0

var float issue68NSTSumLogRankAll = 0.0
var float issue68NSTSumLogRankFlip = 0.0
var float issue68NSTSumLogRankNo = 0.0
var int issue68NSTNLogRankAll = 0
var int issue68NSTNLogRankFlip = 0
var int issue68NSTNLogRankNo = 0

var float issue68NSTSumVolAll = 0.0
var float issue68NSTSumVolFlip = 0.0
var float issue68NSTSumVolNo = 0.0
var int issue68NSTNVolAll = 0
var int issue68NSTNVolFlip = 0
var int issue68NSTNVolNo = 0

var float issue68NSTSumZAll = 0.0
var float issue68NSTSumZFlip = 0.0
var float issue68NSTSumZNo = 0.0
var int issue68NSTNZAll = 0
var int issue68NSTNZFlip = 0
var int issue68NSTNZNo = 0

var float issue68NSTSumRankAll = 0.0
var float issue68NSTSumRankFlip = 0.0
var float issue68NSTSumRankNo = 0.0
var int issue68NSTRankAll = 0
var int issue68NSTRankFlip = 0
var int issue68NSTRankNo = 0

var float issue68NSTSumDullAll = 0.0
var float issue68NSTSumDullFlip = 0.0
var float issue68NSTSumDullNo = 0.0
var int issue68NSTDullAll = 0
var int issue68NSTDullFlip = 0
var int issue68NSTDullNo = 0

var float issue68NSTSumPosShareAll = 0.0
var float issue68NSTSumPosShareFlip = 0.0
var float issue68NSTSumPosShareNo = 0.0
var int issue68NSTNPosShareAll = 0
var int issue68NSTNPosShareFlip = 0
var int issue68NSTNPosShareNo = 0

var float issue68NSTSumValidShareAll = 0.0
var float issue68NSTSumValidShareFlip = 0.0
var float issue68NSTSumValidShareNo = 0.0
var int issue68NSTNValidShareAll = 0
var int issue68NSTNValidShareFlip = 0
var int issue68NSTNValidShareNo = 0

var float issue68NSTSumShiftFPAll = 0.0
var float issue68NSTSumShiftFPFlip = 0.0
var float issue68NSTSumShiftFPNo = 0.0
var int issue68NSTNShiftFPAll = 0
var int issue68NSTNShiftFPFlip = 0
var int issue68NSTNShiftFPNo = 0

var float issue68NSTSumShiftPLAll = 0.0
var float issue68NSTSumShiftPLFlip = 0.0
var float issue68NSTSumShiftPLNo = 0.0
var int issue68NSTNShiftPLAll = 0
var int issue68NSTNShiftPLFlip = 0
var int issue68NSTNShiftPLNo = 0

var float issue68NSTSumShiftLSAll = 0.0
var float issue68NSTSumShiftLSFlip = 0.0
var float issue68NSTSumShiftLSNo = 0.0
var int issue68NSTNShiftLSAll = 0
var int issue68NSTNShiftLSFlip = 0
var int issue68NSTNShiftLSNo = 0

var int issue68NSTLowRankAll = 0
var int issue68NSTMidRankAll = 0
var int issue68NSTHighRankAll = 0
var int issue68NSTLowRankFlip = 0
var int issue68NSTMidRankFlip = 0
var int issue68NSTHighRankFlip = 0
var int issue68NSTLowRankNo = 0
var int issue68NSTMidRankNo = 0
var int issue68NSTHighRankNo = 0
var int issue68NSTRankBandAll = 0
var int issue68NSTRankBandFlip = 0
var int issue68NSTRankBandNo = 0
var float issue68NSTMaxReconErr = 0.0

if issue68NSTBaseValid
    if not na(issue68NSTBpSlope20)
        issue68NSTSumBpAll += issue68NSTBpSlope20
        issue68NSTNBpAll += 1
        if issue68NSTFlip
            issue68NSTSumBpFlip += issue68NSTBpSlope20
            issue68NSTNBpFlip += 1
        if issue68NSTNoFlip
            issue68NSTSumBpNo += issue68NSTBpSlope20
            issue68NSTNBpNo += 1
    if not na(issue68NSTBpRankFull)
        issue68NSTSumBpRankAll += issue68NSTBpRankFull
        issue68NSTNBpRankAll += 1
        if issue68NSTFlip
            issue68NSTSumBpRankFlip += issue68NSTBpRankFull
            issue68NSTNBpRankFlip += 1
        if issue68NSTNoFlip
            issue68NSTSumBpRankNo += issue68NSTBpRankFull
            issue68NSTNBpRankNo += 1
    if not na(issue68NSTBpRankPositive)
        issue68NSTSumBpPosRankAll += issue68NSTBpRankPositive
        issue68NSTNBpPosRankAll += 1
        if issue68NSTFlip
            issue68NSTSumBpPosRankFlip += issue68NSTBpRankPositive
            issue68NSTNBpPosRankFlip += 1
        if issue68NSTNoFlip
            issue68NSTSumBpPosRankNo += issue68NSTBpRankPositive
            issue68NSTNBpPosRankNo += 1
    if not na(issue68NSTLogMovePct)
        issue68NSTSumLogMoveAll += issue68NSTLogMovePct
        issue68NSTNLogMoveAll += 1
        if issue68NSTFlip
            issue68NSTSumLogMoveFlip += issue68NSTLogMovePct
            issue68NSTNLogMoveFlip += 1
        if issue68NSTNoFlip
            issue68NSTSumLogMoveNo += issue68NSTLogMovePct
            issue68NSTNLogMoveNo += 1
    if not na(issue68NSTLogSlopeRank)
        issue68NSTSumLogRankAll += issue68NSTLogSlopeRank
        issue68NSTNLogRankAll += 1
        if issue68NSTFlip
            issue68NSTSumLogRankFlip += issue68NSTLogSlopeRank
            issue68NSTNLogRankFlip += 1
        if issue68NSTNoFlip
            issue68NSTSumLogRankNo += issue68NSTLogSlopeRank
            issue68NSTNLogRankNo += 1
    if not na(issue68NSTVolPct)
        issue68NSTSumVolAll += issue68NSTVolPct
        issue68NSTNVolAll += 1
        if issue68NSTFlip
            issue68NSTSumVolFlip += issue68NSTVolPct
            issue68NSTNVolFlip += 1
        if issue68NSTNoFlip
            issue68NSTSumVolNo += issue68NSTVolPct
            issue68NSTNVolNo += 1
    if not na(speedZ)
        issue68NSTSumZAll += speedZ
        issue68NSTNZAll += 1
        if issue68NSTFlip
            issue68NSTSumZFlip += speedZ
            issue68NSTNZFlip += 1
        if issue68NSTNoFlip
            issue68NSTSumZNo += speedZ
            issue68NSTNZNo += 1
    if not na(speedRank)
        issue68NSTSumRankAll += speedRank
        issue68NSTRankAll += 1
        issue68NSTRankBandAll += 1
        issue68NSTLowRankAll += speedRank <= 15.0 ? 1 : 0
        issue68NSTMidRankAll += speedRank > 15.0 and speedRank < 55.0 ? 1 : 0
        issue68NSTHighRankAll += speedRank >= 55.0 ? 1 : 0
        if issue68NSTFlip
            issue68NSTSumRankFlip += speedRank
            issue68NSTRankFlip += 1
            issue68NSTRankBandFlip += 1
            issue68NSTLowRankFlip += speedRank <= 15.0 ? 1 : 0
            issue68NSTMidRankFlip += speedRank > 15.0 and speedRank < 55.0 ? 1 : 0
            issue68NSTHighRankFlip += speedRank >= 55.0 ? 1 : 0
        if issue68NSTNoFlip
            issue68NSTSumRankNo += speedRank
            issue68NSTRankNo += 1
            issue68NSTRankBandNo += 1
            issue68NSTLowRankNo += speedRank <= 15.0 ? 1 : 0
            issue68NSTMidRankNo += speedRank > 15.0 and speedRank < 55.0 ? 1 : 0
            issue68NSTHighRankNo += speedRank >= 55.0 ? 1 : 0
    if not na(negSlopeDullScore)
        issue68NSTSumDullAll += negSlopeDullScore
        issue68NSTDullAll += 1
        if issue68NSTFlip
            issue68NSTSumDullFlip += negSlopeDullScore
            issue68NSTDullFlip += 1
        if issue68NSTNoFlip
            issue68NSTSumDullNo += negSlopeDullScore
            issue68NSTDullNo += 1
    if not na(issue68NSTPositiveShare)
        issue68NSTSumPosShareAll += issue68NSTPositiveShare
        issue68NSTNPosShareAll += 1
        if issue68NSTFlip
            issue68NSTSumPosShareFlip += issue68NSTPositiveShare
            issue68NSTNPosShareFlip += 1
        if issue68NSTNoFlip
            issue68NSTSumPosShareNo += issue68NSTPositiveShare
            issue68NSTNPosShareNo += 1
    if not na(issue68NSTSpeedValidShare)
        issue68NSTSumValidShareAll += issue68NSTSpeedValidShare
        issue68NSTNValidShareAll += 1
        if issue68NSTFlip
            issue68NSTSumValidShareFlip += issue68NSTSpeedValidShare
            issue68NSTNValidShareFlip += 1
        if issue68NSTNoFlip
            issue68NSTSumValidShareNo += issue68NSTSpeedValidShare
            issue68NSTNValidShareNo += 1
    if not na(issue68NSTShiftFullPos)
        issue68NSTSumShiftFPAll += issue68NSTShiftFullPos
        issue68NSTNShiftFPAll += 1
        if issue68NSTFlip
            issue68NSTSumShiftFPFlip += issue68NSTShiftFullPos
            issue68NSTNShiftFPFlip += 1
        if issue68NSTNoFlip
            issue68NSTSumShiftFPNo += issue68NSTShiftFullPos
            issue68NSTNShiftFPNo += 1
    if not na(issue68NSTShiftPosLog)
        issue68NSTSumShiftPLAll += issue68NSTShiftPosLog
        issue68NSTNShiftPLAll += 1
        if issue68NSTFlip
            issue68NSTSumShiftPLFlip += issue68NSTShiftPosLog
            issue68NSTNShiftPLFlip += 1
        if issue68NSTNoFlip
            issue68NSTSumShiftPLNo += issue68NSTShiftPosLog
            issue68NSTNShiftPLNo += 1
    if not na(issue68NSTShiftLogSpeed)
        issue68NSTSumShiftLSAll += issue68NSTShiftLogSpeed
        issue68NSTNShiftLSAll += 1
        if issue68NSTFlip
            issue68NSTSumShiftLSFlip += issue68NSTShiftLogSpeed
            issue68NSTNShiftLSFlip += 1
        if issue68NSTNoFlip
            issue68NSTSumShiftLSNo += issue68NSTShiftLogSpeed
            issue68NSTNShiftLSNo += 1
    if not na(issue68NSTReconErr)
        issue68NSTMaxReconErr := math.max(issue68NSTMaxReconErr, issue68NSTReconErr)

string issue68NSTBandsAll = f_issue68NSTPct(issue68NSTLowRankAll, issue68NSTRankBandAll) + " / " + f_issue68NSTPct(issue68NSTMidRankAll, issue68NSTRankBandAll) + " / " + f_issue68NSTPct(issue68NSTHighRankAll, issue68NSTRankBandAll)
string issue68NSTBandsFlip = f_issue68NSTPct(issue68NSTLowRankFlip, issue68NSTRankBandFlip) + " / " + f_issue68NSTPct(issue68NSTMidRankFlip, issue68NSTRankBandFlip) + " / " + f_issue68NSTPct(issue68NSTHighRankFlip, issue68NSTRankBandFlip)
string issue68NSTBandsNo = f_issue68NSTPct(issue68NSTLowRankNo, issue68NSTRankBandNo) + " / " + f_issue68NSTPct(issue68NSTMidRankNo, issue68NSTRankBandNo) + " / " + f_issue68NSTPct(issue68NSTHighRankNo, issue68NSTRankBandNo)

color issue68NSTRankColor = speedRank <= 15.0 ? colRed : speedRank < 55.0 ? colYellow : colGreen
plot(issue68NSTInWindow ? 3.0 : na, "EXPECTED Bull", color=colGreen, linewidth=4, style=plot.style_linebr, display=display.pane)
plot(issue68NSTBaseValid ? 2.0 : na, "RAW S1 to EFF S2 flip", color=issue68NSTFlip ? colGreen : colRed, linewidth=4, style=plot.style_linebr, display=display.pane)
plot(issue68NSTBaseValid ? 1.0 : na, "speedRank band", color=issue68NSTRankColor, linewidth=4, style=plot.style_linebr, display=display.pane)

var table t = table.new(position.middle_right, 4, 18, border_width=1)
if barstate.islast
    if showIssue68NSTTable
        table.cell(t, 0, 0, "NEGSLOPE TRANSFORM", bgcolor=colNeutral, text_color=color.white)
        table.cell(t, 1, 0, "ALL", bgcolor=colNeutral, text_color=color.white)
        table.cell(t, 2, 0, "FLIP", bgcolor=colGreen, text_color=color.white)
        table.cell(t, 3, 0, "NO-FLIP", bgcolor=colRed, text_color=color.white)

        table.cell(t, 0, 1, "Population", bgcolor=colNeutral, text_color=color.white)
        table.cell(t, 1, 1, str.tostring(issue68NSTNAll), bgcolor=colNeutral, text_color=color.white)
        table.cell(t, 2, 1, str.tostring(issue68NSTNFlip), bgcolor=colGreen, text_color=color.white)
        table.cell(t, 3, 1, str.tostring(issue68NSTNNoFlip), bgcolor=colRed, text_color=color.white)

        table.cell(t, 0, 2, "20D bp slope", bgcolor=colNeutral, text_color=color.white)
        table.cell(t, 1, 2, f_issue68NSTFmtN(issue68NSTSumBpAll, issue68NSTNBpAll), bgcolor=colNeutral, text_color=color.white)
        table.cell(t, 2, 2, f_issue68NSTFmtN(issue68NSTSumBpFlip, issue68NSTNBpFlip), bgcolor=colGreen, text_color=color.white)
        table.cell(t, 3, 2, f_issue68NSTFmtN(issue68NSTSumBpNo, issue68NSTNBpNo), bgcolor=colRed, text_color=color.white)

        table.cell(t, 0, 3, "BP rank full", bgcolor=colNeutral, text_color=color.white)
        table.cell(t, 1, 3, f_issue68NSTFmtN(issue68NSTSumBpRankAll, issue68NSTNBpRankAll), bgcolor=colNeutral, text_color=color.white)
        table.cell(t, 2, 3, f_issue68NSTFmtN(issue68NSTSumBpRankFlip, issue68NSTNBpRankFlip), bgcolor=colGreen, text_color=color.white)
        table.cell(t, 3, 3, f_issue68NSTFmtN(issue68NSTSumBpRankNo, issue68NSTNBpRankNo), bgcolor=colRed, text_color=color.white)

        table.cell(t, 0, 4, "BP rank pos-support", bgcolor=colNeutral, text_color=color.white)
        table.cell(t, 1, 4, f_issue68NSTFmtN(issue68NSTSumBpPosRankAll, issue68NSTNBpPosRankAll), bgcolor=colNeutral, text_color=color.white)
        table.cell(t, 2, 4, f_issue68NSTFmtN(issue68NSTSumBpPosRankFlip, issue68NSTNBpPosRankFlip), bgcolor=colGreen, text_color=color.white)
        table.cell(t, 3, 4, f_issue68NSTFmtN(issue68NSTSumBpPosRankNo, issue68NSTNBpPosRankNo), bgcolor=colRed, text_color=color.white)

        table.cell(t, 0, 5, "Log 20D move %", bgcolor=colNeutral, text_color=color.white)
        table.cell(t, 1, 5, f_issue68NSTFmtN(issue68NSTSumLogMoveAll, issue68NSTNLogMoveAll), bgcolor=colNeutral, text_color=color.white)
        table.cell(t, 2, 5, f_issue68NSTFmtN(issue68NSTSumLogMoveFlip, issue68NSTNLogMoveFlip), bgcolor=colGreen, text_color=color.white)
        table.cell(t, 3, 5, f_issue68NSTFmtN(issue68NSTSumLogMoveNo, issue68NSTNLogMoveNo), bgcolor=colRed, text_color=color.white)

        table.cell(t, 0, 6, "Log slope rank", bgcolor=colNeutral, text_color=color.white)
        table.cell(t, 1, 6, f_issue68NSTFmtN(issue68NSTSumLogRankAll, issue68NSTNLogRankAll), bgcolor=colNeutral, text_color=color.white)
        table.cell(t, 2, 6, f_issue68NSTFmtN(issue68NSTSumLogRankFlip, issue68NSTNLogRankFlip), bgcolor=colGreen, text_color=color.white)
        table.cell(t, 3, 6, f_issue68NSTFmtN(issue68NSTSumLogRankNo, issue68NSTNLogRankNo), bgcolor=colRed, text_color=color.white)

        table.cell(t, 0, 7, "Vol60 logret %", bgcolor=colNeutral, text_color=color.white)
        table.cell(t, 1, 7, f_issue68NSTFmtN(issue68NSTSumVolAll, issue68NSTNVolAll), bgcolor=colNeutral, text_color=color.white)
        table.cell(t, 2, 7, f_issue68NSTFmtN(issue68NSTSumVolFlip, issue68NSTNVolFlip), bgcolor=colGreen, text_color=color.white)
        table.cell(t, 3, 7, f_issue68NSTFmtN(issue68NSTSumVolNo, issue68NSTNVolNo), bgcolor=colRed, text_color=color.white)

        table.cell(t, 0, 8, "speedZ", bgcolor=colNeutral, text_color=color.white)
        table.cell(t, 1, 8, f_issue68NSTFmtN(issue68NSTSumZAll, issue68NSTNZAll), bgcolor=colNeutral, text_color=color.white)
        table.cell(t, 2, 8, f_issue68NSTFmtN(issue68NSTSumZFlip, issue68NSTNZFlip), bgcolor=colGreen, text_color=color.white)
        table.cell(t, 3, 8, f_issue68NSTFmtN(issue68NSTSumZNo, issue68NSTNZNo), bgcolor=colRed, text_color=color.white)

        table.cell(t, 0, 9, "speedRank", bgcolor=colNeutral, text_color=color.white)
        table.cell(t, 1, 9, f_issue68NSTFmtN(issue68NSTSumRankAll, issue68NSTRankAll), bgcolor=colNeutral, text_color=color.white)
        table.cell(t, 2, 9, f_issue68NSTFmtN(issue68NSTSumRankFlip, issue68NSTRankFlip), bgcolor=colGreen, text_color=color.white)
        table.cell(t, 3, 9, f_issue68NSTFmtN(issue68NSTSumRankNo, issue68NSTRankNo), bgcolor=colRed, text_color=color.white)

        table.cell(t, 0, 10, "NegSlopeDull", bgcolor=colNeutral, text_color=color.white)
        table.cell(t, 1, 10, f_issue68NSTFmtN(issue68NSTSumDullAll, issue68NSTDullAll), bgcolor=colNeutral, text_color=color.white)
        table.cell(t, 2, 10, f_issue68NSTFmtN(issue68NSTSumDullFlip, issue68NSTDullFlip), bgcolor=colGreen, text_color=color.white)
        table.cell(t, 3, 10, f_issue68NSTFmtN(issue68NSTSumDullNo, issue68NSTDullNo), bgcolor=colRed, text_color=color.white)

        table.cell(t, 0, 11, "Rank <=15 / mid / >=55", bgcolor=colNeutral, text_color=color.white)
        table.cell(t, 1, 11, issue68NSTBandsAll, bgcolor=colNeutral, text_color=color.white)
        table.cell(t, 2, 11, issue68NSTBandsFlip, bgcolor=colGreen, text_color=color.white)
        table.cell(t, 3, 11, issue68NSTBandsNo, bgcolor=colRed, text_color=color.white)

        table.cell(t, 0, 12, "Positive close %756", bgcolor=colNeutral, text_color=color.white)
        table.cell(t, 1, 12, f_issue68NSTFmtN(issue68NSTSumPosShareAll, issue68NSTNPosShareAll), bgcolor=colNeutral, text_color=color.white)
        table.cell(t, 2, 12, f_issue68NSTFmtN(issue68NSTSumPosShareFlip, issue68NSTNPosShareFlip), bgcolor=colGreen, text_color=color.white)
        table.cell(t, 3, 12, f_issue68NSTFmtN(issue68NSTSumPosShareNo, issue68NSTNPosShareNo), bgcolor=colRed, text_color=color.white)

        table.cell(t, 0, 13, "Valid speedZ %756", bgcolor=colNeutral, text_color=color.white)
        table.cell(t, 1, 13, f_issue68NSTFmtN(issue68NSTSumValidShareAll, issue68NSTNValidShareAll), bgcolor=colNeutral, text_color=color.white)
        table.cell(t, 2, 13, f_issue68NSTFmtN(issue68NSTSumValidShareFlip, issue68NSTNValidShareFlip), bgcolor=colGreen, text_color=color.white)
        table.cell(t, 3, 13, f_issue68NSTFmtN(issue68NSTSumValidShareNo, issue68NSTNValidShareNo), bgcolor=colRed, text_color=color.white)

        table.cell(t, 0, 14, "Shift fullBP -> posBP", bgcolor=colNeutral, text_color=color.white)
        table.cell(t, 1, 14, f_issue68NSTFmtN(issue68NSTSumShiftFPAll, issue68NSTNShiftFPAll), bgcolor=colNeutral, text_color=color.white)
        table.cell(t, 2, 14, f_issue68NSTFmtN(issue68NSTSumShiftFPFlip, issue68NSTNShiftFPFlip), bgcolor=colGreen, text_color=color.white)
        table.cell(t, 3, 14, f_issue68NSTFmtN(issue68NSTSumShiftFPNo, issue68NSTNShiftFPNo), bgcolor=colRed, text_color=color.white)

        table.cell(t, 0, 15, "Shift posBP -> log", bgcolor=colNeutral, text_color=color.white)
        table.cell(t, 1, 15, f_issue68NSTFmtN(issue68NSTSumShiftPLAll, issue68NSTNShiftPLAll), bgcolor=colNeutral, text_color=color.white)
        table.cell(t, 2, 15, f_issue68NSTFmtN(issue68NSTSumShiftPLFlip, issue68NSTNShiftPLFlip), bgcolor=colGreen, text_color=color.white)
        table.cell(t, 3, 15, f_issue68NSTFmtN(issue68NSTSumShiftPLNo, issue68NSTNShiftPLNo), bgcolor=colRed, text_color=color.white)

        table.cell(t, 0, 16, "Shift log -> speedRank", bgcolor=colNeutral, text_color=color.white)
        table.cell(t, 1, 16, f_issue68NSTFmtN(issue68NSTSumShiftLSAll, issue68NSTNShiftLSAll), bgcolor=colNeutral, text_color=color.white)
        table.cell(t, 2, 16, f_issue68NSTFmtN(issue68NSTSumShiftLSFlip, issue68NSTNShiftLSFlip), bgcolor=colGreen, text_color=color.white)
        table.cell(t, 3, 16, f_issue68NSTFmtN(issue68NSTSumShiftLSNo, issue68NSTNShiftLSNo), bgcolor=colRed, text_color=color.white)

        table.cell(t, 0, 17, "Recon max / READ", bgcolor=colNeutral, text_color=color.white)
        table.cell(t, 1, 17, f_issue68NSTFmt(issue68NSTMaxReconErr), bgcolor=issue68NSTMaxReconErr < 0.001 ? colGreen : colRed, text_color=color.white)
        table.cell(t, 2, 17, "find split step", bgcolor=colGreen, text_color=color.white)
        table.cell(t, 3, 17, "NO TUNING", bgcolor=colRed, text_color=color.white)
    else
        table.clear(t, 0, 0, 3, 17)
'''.strip()


def generate(source: Path) -> str:
    d1_text = phase_b.d1.generate(source)
    if d1_text.count(phase_b.D1_EXPORT_MARKER) != 1:
        raise RuntimeError("expected exactly one D1 parity export marker")
    core = d1_text.split(phase_b.D1_EXPORT_MARKER, 1)[0].rstrip()
    core = replace_once(core, phase_b.D1_INDICATOR_DECL, AUDIT_DECL)
    out = core + "\n\n" + BODY + "\n"
    for token in (
        "NegSlopeDull Transformation Audit",
        "20D bp slope",
        "BP rank pos-support",
        "Log slope rank",
        "Valid speedZ %756",
        "Shift posBP -> log",
        "Recon max / READ",
    ):
        if token not in out:
            raise RuntimeError(f"missing required audit token: {token}")
    if "strategy.entry" in out or "strategy.close" in out:
        raise RuntimeError("NegSlope transform audit leaked strategy order logic")
    return out


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--source", type=Path, default=HERE / SOURCE_RELATIVE)
    ap.add_argument("--output", type=Path, required=True)
    args = ap.parse_args()
    text = generate(args.source)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(text, encoding="utf-8")


if __name__ == "__main__":
    main()
