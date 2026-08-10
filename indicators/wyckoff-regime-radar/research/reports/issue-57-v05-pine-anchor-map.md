# Issue #57 frozen Pine anchor map

0374: rangeHighBreak = ta.highest(high[1], breakoutBars)
0375: rangeLowBreak  = ta.lowest(low[1], breakoutBars)
0376: rangeBreakUp   = not na(rangeHighBreak) and close > rangeHighBreak and close[1] <= rangeHighBreak[1]
0377: rangeBreakDn   = not na(rangeLowBreak) and close < rangeLowBreak and close[1] >= rangeLowBreak[1]
0378: maCrossUp      = ta.crossover(close, ma)
0379: maCrossDn      = ta.crossunder(close, ma)
0380: 
0381: recentBreakUp = f_recent(rangeBreakUp or maCrossUp, breakoutBars)
0382: recentBreakDn = f_recent(rangeBreakDn or maCrossDn, breakoutBars)
0383: recentRangeBreakDn = f_recent(rangeBreakDn, breakoutBars)
0384: recentMaCrossDn = f_recent(maCrossDn, breakoutBars)
0385: 
0386: breakoutModeUp  = useBreakoutExemption and heatUp >= orangeLevel and maturityUp < maturityConfirm and lowVolRecently and recentBreakUp
0387: breakdownModeDn = useBreakoutExemption and panicHeatDn >= orangeLevel and maturityDn < maturityConfirm and lowVolRecently and recentBreakDn
0388: 
0389: redUpCore = endRiskUpRaw >= redLevel and heatUp >= highHeatConfirm and speedRank >= speedRankConfirm and maturityUp >= maturityConfirm and longSlopeRank >= longSlopeRankConfirm
0390: redDnCore = endRiskDnRaw >= redLevel and panicHeatDn >= highHeatConfirm and speedRank <= 100.0 - speedRankConfirm and maturityDn >= maturityConfirm and longSlopeRank <= 100.0 - longSlopeRankConfirm
0391: redUp = redUpCore and not breakoutModeUp
0392: redDn = redDnCore and not breakdownModeDn
0393: 
0394: endRiskUp = endRiskUpRaw
...
0431: structureWeak   = bearStructure
0432: 
0433: breakoutScore = breakoutModeUp ? 100.0 : recentBreakUp ? 70.0 : close > ma ? 35.0 : 0.0
0434: explicitBreakdownScore = breakdownModeDn ? 100.0 : recentRangeBreakDn ? 85.0 : (recentMaCrossDn and panicHeatDn >= orangeLevel and structureWeak >= 50.0 ? 55.0 : 0.0)
0435: 
0436: // v0.3.3 Absorption vs Distribution Layer
...
0445: prevAbsHigh = ta.highest(high[1], absorbLen)
0446: 
0447: noBreakLowScore   = close > prevAbsLow ? 100.0 : 0.0
0448: noBreakHighScore  = close < prevAbsHigh ? 100.0 : 0.0
0449: negSlopeDullScore = f_gate(speedRank, 15.0, 55.0) * 100.0
0450: posSlopeDullScore = f_gate(100.0 - speedRank, 15.0, 55.0) * 100.0
0451: panicDullScore    = f_weighted2(100.0 - panicHeatDn, 0.55, panicCooling, 0.45)
0452: heatDullScore     = f_weighted2(100.0 - heatUp, 0.55, heatCooling, 0.45)
0453: lowZoneStableScore  = f_weighted2(100.0 - absRangePos, 0.50, noBreakLowScore, 0.50)
0454: highZoneStableScore = f_weighted2(absRangePos, 0.50, noBreakHighScore, 0.50)
0455: 
0456: downsideExhaustion = f_clamp(f_weighted5(noBreakLowScore, 0.30, negSlopeDullScore, 0.25, panicDullScore, 0.20, lowVolScore, 0.15, lowZoneStableScore, 0.10), 0.0, 100.0)
0457: upsideExhaustion   = f_clamp(f_weighted5(noBreakHighScore, 0.30, posSlopeDullScore, 0.25, heatDullScore, 0.20, lowVolScore, 0.15, highZoneStableScore, 0.10), 0.0, 100.0)
0458: 
0459: supportProbe = low <= absRangeLow + absRangeW * 0.35
0460: supportReclaimScore = close > absRangeMid ? 100.0 : close > ma ? 70.0 : close > absRangeLow + absRangeW * 0.35 ? 45.0 : 0.0
0461: panicNotContinueScore = 100.0 - panicHeatDn
0462: supportHoldingRaw = supportProbe ? f_weighted4(noBreakLowScore, 0.35, supportReclaimScore, 0.25, panicNotContinueScore, 0.25, lowZoneStableScore, 0.15) : f_weighted3(noBreakLowScore, 0.45, panicNotContinueScore, 0.35, lowZoneStableScore, 0.20)
0463: supportHolding = f_clamp(supportHoldingRaw, 0.0, 100.0)
0464: 
...
0466: resistanceRejectScore = close < absRangeMid ? 100.0 : close < ma ? 70.0 : close < absRangeHigh - absRangeW * 0.35 ? 45.0 : 0.0
0467: heatNotContinueScore = 100.0 - heatUp
0468: resistanceHoldingRaw = resistanceProbe ? f_weighted4(noBreakHighScore, 0.35, resistanceRejectScore, 0.25, heatNotContinueScore, 0.25, highZoneStableScore, 0.15) : f_weighted3(noBreakHighScore, 0.45, heatNotContinueScore, 0.35, highZoneStableScore, 0.20)
0469: resistanceHolding = f_clamp(resistanceHoldingRaw, 0.0, 100.0)
0470: 
...
0518: downInefficiencyScore = f_clamp(100.0 - downProgressScore, 0.0, 100.0)
0519: 
0520: effortResultUp = volumeActive ? f_clamp(f_weighted5(volumeParticipation, 0.30, noBreakHighScore, 0.25, upInefficiencyScore, 0.20, resistanceHolding, 0.15, upsideExhaustion, 0.10), 0.0, 100.0) : 0.0
0521: effortResultDown = volumeActive ? f_clamp(f_weighted5(volumeParticipation, 0.30, noBreakLowScore, 0.25, downInefficiencyScore, 0.20, supportHolding, 0.15, downsideExhaustion, 0.10), 0.0, 100.0) : 0.0
0522: 
0523: volumeAbsorptionScore = volumeActive ? f_clamp(f_weighted4(effortResultDown, 0.35, downsideExhaustion, 0.25, supportHolding, 0.25, volumeParticipation, 0.15), 0.0, 100.0) : 0.0
0524: volumeDistributionScore = volumeActive ? f_clamp(f_weighted4(effortResultUp, 0.35, upsideExhaustion, 0.25, resistanceHolding, 0.25, volumeParticipation, 0.15), 0.0, 100.0) : 0.0
0525: volumeBreakoutConfirmation = volumeActive ? f_clamp(f_weighted4(breakoutScore, 0.35, volumeParticipation, 0.25, upProgressScore, 0.25, 100.0 - math.max(upsideExhaustion, resistanceHolding), 0.15), 0.0, 100.0) : 0.0
0526: volumeBreakdownConfirmation = volumeActive ? f_clamp(f_weighted4(explicitBreakdownScore, 0.35, volumeParticipation, 0.25, downProgressScore, 0.25, 100.0 - math.max(downsideExhaustion, supportHolding), 0.15), 0.0, 100.0) : 0.0
0527: 
0528: volumeDemandClue = volumeActive and volumeAbsorptionScore >= effortResultThreshold
...
0664: barsSinceAboveRangeLost = ta.barssince(not abovePrevRange)
0665: barsSinceBelowRangeLost = ta.barssince(not belowPrevRange)
0666: sustainedAboveRange = abovePrevRange and (continuationHoldBars <= 1 or (not na(barsSinceAboveRangeLost) and barsSinceAboveRangeLost >= continuationHoldBars - 1))
0667: sustainedBelowRange = belowPrevRange and (continuationHoldBars <= 1 or (not na(barsSinceBelowRangeLost) and barsSinceBelowRangeLost >= continuationHoldBars - 1))
0668: 
0669: rangeContinuationUpScore = sustainedAboveRange ? 100.0 : abovePrevRange ? 80.0 : recentBreakUp ? 65.0 : close > rangeMid ? 35.0 : 0.0
0670: rangeContinuationDnScore = sustainedBelowRange ? 100.0 : belowPrevRange ? 80.0 : recentBreakDn ? 65.0 : close < rangeMid ? 35.0 : 0.0
0671: 
0672: maSpreadATR = f_safeDiv(ma - maturityMa, atr)
...
0694: 
0695: accTraceForMarkup = ta.highest(accRaw0, absorbLen)
0696: markupBaseRaw = f_weighted5(breakoutScore, 0.20, heatUp, 0.20, structureStrong, 0.20, markupExtensionScore, 0.25, markupContinuationScore, 0.15)
0697: markupRaw0 = f_weighted2(markupBaseRaw, 0.85, accTraceForMarkup, 0.15)
0698: 
...
0700: distRaw0 = f_weighted5(bullMaturityTrace, 0.20, rangeScore, 0.20, upsideExhaustion, 0.25, resistanceHolding, 0.25, bearPressureRising, 0.10)
0701: 
0702: markdownBaseRaw = f_weighted5(explicitBreakdownScore, 0.20, panicHeatDn, 0.20, structureWeak, 0.20, markdownExtensionScore, 0.25, markdownContinuationScore, 0.15)
0703: distTraceForMarkdown = ta.highest(distRaw0, absorbLen)
0704: markdownRaw0 = f_weighted2(markdownBaseRaw, 0.85, distTraceForMarkdown, 0.15)
...
0722: bearBackgroundForAccGate = f_gate(math.max(bearBg, bearMaturityTrace), 35.0, 75.0)
0723: 
0724: breakoutGate = breakoutModeUp ? 1.0 : recentBreakUp ? 0.85 : f_gate(breakoutScore, 30.0, 70.0)
0725: explicitBreakdownGate = breakdownModeDn ? 1.0 : recentRangeBreakDn ? 0.90 : f_gate(explicitBreakdownScore, 50.0, 85.0)
0726: structureStrongGate = f_gate(structureStrong, 40.0, 100.0)
0727: structureWeakGate = f_gate(structureWeak, 40.0, 100.0)
...
0734: 
0735: breakoutMarkupGate =
0736:      breakoutGate *
0737:      structureStrongGate *
0738:      nonEndUpGate
...
0755: 
0756: breakdownMarkdownGate =
0757:      explicitBreakdownGate *
0758:      f_gate(panicHeatDn, 40.0, 80.0) *
0759:      structureWeakGate
...
0790: 
0791: 
0792: // v0.5.2 Divergence Witness Layer｜confirmed pivot + risk alignment window + hold.
0793: bullChaseRisk = endRiskUp
0794: bearChaseRisk = endRiskDn
...
0990: 
0991: stageSupportStrength = topId == 1 ? f_weighted2(downsideExhaustion, 0.50, supportHolding, 0.50) :
0992:      topId == 2 ? f_weighted3(markupExtensionScore, 0.45, markupContinuationScore, 0.35, math.max(breakoutScore, structureStrong), 0.20) :
0993:      topId == 3 ? f_weighted2(supportHolding, 0.50, 100.0 - upsideExhaustion, 0.50) :
0994:      topId == 4 ? f_weighted2(upsideExhaustion, 0.50, resistanceHolding, 0.50) :
0995:      topId == 5 ? f_weighted3(markdownExtensionScore, 0.45, markdownContinuationScore, 0.35, math.max(explicitBreakdownGate * 100.0, panicHeatDn), 0.20) :
0996:      topId == 6 ? f_weighted2(resistanceHolding, 0.50, 100.0 - downsideExhaustion, 0.50) : 0.0
0997: 
...
1055: coexistRaw = (hasSharp and topVal >= dominantMin and topGap < topGapMin and evidenceStrength >= 25.0) or lowStageDispute or highStageDispute
1056: weakCandidateRaw = hasSharp and topVal >= dominantMin and topGap >= topGapMin and (not hasEvidence or candidateConflict)
1057: strongCandidate = hasSharp and topVal >= dominantMin and topGap >= topGapMin and hasEvidence and not candidateConflict
1058: 
1059: // v0.3.8：強候選快速轉正。當候選權重、Gap、證據與趨勢延伸壓倒性領先時，使用較短確認根數。
1060: fastMarkupSwitch = strongCandidate and topId == 2 and topVal >= fastSwitchWeight and topGap >= fastSwitchGap and evidenceStrength >= fastSwitchEvidence and markupContinuationScore >= fastSwitchExt and markupExtensionScore >= trendExtThreshold and close > ma and close > maturityMa
1061: fastMarkdownSwitch = strongCandidate and topId == 5 and topVal >= fastSwitchWeight and topGap >= fastSwitchGap and evidenceStrength >= fastSwitchEvidence and markdownContinuationScore >= fastSwitchExt and markdownExtensionScore >= trendExtThreshold and close < ma and close < maturityMa
1062: fastSwitchActive = fastMarkupSwitch or fastMarkdownSwitch
1063: activeConfirmBars = fastSwitchActive ? fastSwitchConfirmBars : confirmBars
1064: candidateRawId = strongCandidate ? topId : 0
1065: 
1066: // Regime Inertia
1067: 
1068: var int confirmedId = 0
1069: var int candidateId = 0
1070: var int candidateBars = 0
1071: var int noRegimeBars = 0
1072: 
1073: if strongCandidate
1074:     noRegimeBars := 0
1075:     if candidateRawId == candidateId
1076:         candidateBars += 1
1077:     else
1078:         candidateId := candidateRawId
1079:         candidateBars := 1
1080:     if candidateBars >= activeConfirmBars
1081:         confirmedId := candidateId
1082: else
1083:     candidateId := 0
1084:     candidateBars := 0
1085:     if chaosRaw
1086:         noRegimeBars += 1
1087:         if noRegimeBars >= confirmBars
1088:             confirmedId := 0
1089:     else
1090:         noRegimeBars := 0
1091: 
1092: formalId = confirmedId
1093: candidateDisplayId = (strongCandidate or weakCandidateRaw) ? topId : 0
1094: secondaryId = hasSharp ? secondId : 0
1095: 
...
1107:      f_stageName(id)
1108: 
1109: formalSubtypeText = f_stageSubtype(formalId)
1110: candidateSubtypeText = f_stageSubtype(candidateDisplayId)
1111: 
1112: confidenceText = chaosRaw and formalId == 0 ? "混沌" :
1113:      lowStageDispute ? "低位階段分歧" :
1114:      highStageDispute ? "高位階段分歧" :
...
1119:      weakCandidateRaw ? "弱候選" :
1120:      coexistRaw ? "並存" :
1121:      strongCandidate and candidateId != formalId ? "候選" :
1122:      strongCandidate and topVal >= highConfidence and hasHighEvidence ? "高信心" :
1123:      strongCandidate ? "主導" : "轉換觀察"
1124: 
1125: 
...
1128: // 它從空手者、多單持有者、空單持有者三種角度，提示目前較合理的風控節奏。
1129: 
1130: paceStageId = formalId != 0 ? formalId : candidateDisplayId
1131: 
1132: int paceCode = 0
...
1282: // Flat Action 不是買賣命令，而是「空手者是否具備試單條件」的節奏授權。
1283: 
1284: bullFormalAction = formalId == 2 or formalId == 3
1285: bearFormalAction = formalId == 5 or formalId == 6
1286: bullCandidateAction = allowCandidateFlatAction and (candidateDisplayId == 2 or candidateDisplayId == 3)
1287: bearCandidateAction = allowCandidateFlatAction and (candidateDisplayId == 5 or candidateDisplayId == 6)
1288: flatBullStage = bullFormalAction or bullCandidateAction
1289: flatBearStage = bearFormalAction or bearCandidateAction
1290: 
1291: flatBullTrigger =
1292:      breakoutModeUp or
1293:      recentBreakUp or
1294:      markupExtensionScore >= trendExtThreshold or
1295:      markupContinuationScore >= trendExtThreshold or
...
1297: 
1298: flatBearTrigger =
1299:      breakdownModeDn or
1300:      recentBreakDn or
1301:      markdownExtensionScore >= trendExtThreshold or
1302:      markdownContinuationScore >= trendExtThreshold or
...
1372:      (not requireFormalForTrendAction or bearFormalAction or fastMarkdownSwitch)
1373: 
1374: flatWaitLong = enableFlatAction and not flatNoChaseLong and (flatBullStage or markupExtensionScore >= trendExtThreshold or markupContinuationScore >= trendExtThreshold or breakoutModeUp or recentBreakUp)
1375: flatWaitShort = enableFlatAction and not flatNoChaseShort and (flatBearStage or markdownExtensionScore >= trendExtThreshold or markdownContinuationScore >= trendExtThreshold or breakdownModeDn or recentBreakDn)
1376: 
1377: int rawFlatActionLevel = 0
...
1465: // Visuals
1466: 
1467: upColor = f_riskColor(endRiskUp, redUp, breakoutModeUp, false)
1468: dnColor = f_riskColor(endRiskDn, redDn, false, breakdownModeDn)
1469: formalColor = f_stageColor(formalId)
1470: 
1471: plot(endRiskUp, "上漲末段風險", color=upColor, linewidth=2)
...
1545: hline(100, "100", color=color.new(colNeutral, 85), linestyle=hline.style_dotted)
1546: 
1547: bgBaseColor = formalId != 0 ? formalColor :
1548:      lowStageDispute ? colLowDispute :
1549:      highStageDispute ? colHighDispute :
...
1554:      coexistRaw ? colCoexist : colNeutral
1555: 
1556: bgTransp = formalId != 0 and topVal >= highConfidence and hasHighEvidence ? bgTranspFormal : bgTranspWeak
1557: 
1558: // v0.3.8.2 Dual Layer Background
...
1567: dualBgEnabled = dualFormalCandidateBg or dualPaceCandidateBg
1568: 
1569: candidateBgOk = candidateDisplayId != 0 and topVal >= candidateBgMinWeight
1570: candidateBgBaseColor = candidateBgOk ? f_stageColor(candidateDisplayId) : colNeutral
1571: singleBgBaseColor = singleCandidateBg ? candidateBgBaseColor : singlePaceBg ? paceColor : bgBaseColor
1572: singleBgTransp = singleCandidateBg ? bgTranspCandidate : singlePaceBg ? bgTranspPace : bgTransp
...
1594: 
1595: if barstate.islast and showTable
1596:     domColor = f_stageColor(formalId)
1597:     secColor = f_stageColor(secondaryId)
1598:     candColor = f_stageColor(candidateDisplayId)
1599:     ts = f_tableTextSize()
1600:     rowBg = color.new(colRowBg, dashboardTransp)
...
1608:          weakCandidateRaw ? "弱候選" :
1609:          coexistRaw ? "並存" :
1610:          strongCandidate ? "主導候選" : "轉換觀察"
1611: 
1612:     
1613:     modeText = breakoutModeUp ? "突破啟動" :
1614:          breakdownModeDn ? "下破啟動" :
1615:          redUp ? "上漲紅燈" :
1616:          redDn ? "恐慌紅燈" : "一般"
...
1651:         table.cell(dash, 1, rowOffset + 0, formalSubtypeText + "｜" + confidenceText, text_color=colDarkText, bgcolor=color.new(domColor, 0), text_size=ts)
1652:         table.cell(dash, 0, rowOffset + 1, "候選", text_color=colText, bgcolor=color.new(candColor, 0), text_size=ts)
1653:         table.cell(dash, 1, rowOffset + 1, candidateSubtypeText + "｜" + f_pct(topVal) + "｜" + str.tostring(candidateBars) + "/" + str.tostring(activeConfirmBars), text_color=colDarkText, bgcolor=color.new(candColor, 0), text_size=ts)
1654:         table.cell(dash, 0, rowOffset + 2, "次要 / Gap", text_color=colText, bgcolor=color.new(secColor, 0), text_size=ts)
1655:         table.cell(dash, 1, rowOffset + 2, f_stageName(secondaryId) + " " + f_pct(secondVal) + "｜G " + f_pct(topGap), text_color=colDarkText, bgcolor=color.new(secColor, 0), text_size=ts)
...
1688:         table.cell(dash, 1, rowOffset + 0, formalSubtypeText + "｜" + confidenceText, text_color=colDarkText, bgcolor=color.new(domColor, 0), text_size=ts)
1689:         table.cell(dash, 0, rowOffset + 1, "候選主導", text_color=colText, bgcolor=color.new(candColor, 0), text_size=ts)
1690:         table.cell(dash, 1, rowOffset + 1, candidateSubtypeText + "｜" + f_pct(topVal) + "｜" + str.tostring(candidateBars) + "/" + str.tostring(activeConfirmBars), text_color=colDarkText, bgcolor=color.new(candColor, 0), text_size=ts)
1691:         table.cell(dash, 0, rowOffset + 2, "次要 / Gap", text_color=colText, bgcolor=color.new(secColor, 0), text_size=ts)
1692:         table.cell(dash, 1, rowOffset + 2, f_stageName(secondaryId) + " " + f_pct(secondVal) + "｜" + f_pct(topGap), text_color=colDarkText, bgcolor=color.new(secColor, 0), text_size=ts)
...
1769: // 2. Any alert() function call，用來接收完整動態訊息。
1770: 
1771: formalChanged = formalId != formalId[1]
1772: candidateStarted = strongCandidate and candidateId != formalId and candidateBars == 1
1773: anyDisputeStarted = (lowStageDispute and not lowStageDispute[1]) or (highStageDispute and not highStageDispute[1]) or (trendStageDispute and not trendStageDispute[1]) or (highClueObservation and not highClueObservation[1]) or (lowClueObservation and not lowClueObservation[1]) or (trendClueDispute and not trendClueDispute[1])
1774: anyWeakStateStarted = (chaosRaw and not chaosRaw[1]) or (coexistRaw and not coexistRaw[1]) or (weakCandidateRaw and not weakCandidateRaw[1])
1775: anyRiskRedStarted = (redUp and not redUp[1]) or (redDn and not redDn[1])
1776: anyStartMode = (breakoutModeUp and not breakoutModeUp[1]) or (breakdownModeDn and not breakdownModeDn[1])
1777: anyEvidenceCross = ta.crossover(evidenceStrength, evidenceAlertLevel)
1778: anyExtensionCross = ta.crossover(markupExtensionScore, trendExtThreshold) or ta.crossover(markdownExtensionScore, trendExtThreshold) or ta.crossover(markupContinuationScore, trendExtThreshold) or ta.crossover(markdownContinuationScore, trendExtThreshold)
...
1810: 
1811: // Dynamic alerts. 建立 TradingView alert 時，選 Any alert() function call。
1812: if barstate.isconfirmed
1813:     if paceChanged
1814:         alert("Chase Risk v0.5｜Pace Guide｜" + paceTitle + "｜空手:" + flatGuide + "｜多單:" + longGuide + "｜空單:" + shortGuide + "｜原因:" + paceReason, alert.freq_once_per_bar_close)
...
1820:         alert("Chase Risk v0.5｜正式主導切換為 " + formalSubtypeText + "｜證據 " + f_num(evidenceStrength) + " " + evidenceLabel + "｜權重 " + f_pct(topVal), alert.freq_once_per_bar_close)
1821:     if candidateStarted
1822:         alert("Chase Risk v0.5｜新候選 " + candidateSubtypeText + "｜權重 " + f_pct(topVal) + "｜確認 " + str.tostring(candidateBars) + "/" + str.tostring(activeConfirmBars), alert.freq_once_per_bar_close)
1823:     if lowStageDispute and not lowStageDispute[1]
1824:         alert("Chase Risk v0.5｜低位階段分歧：吸籌 / 再出貨｜吸籌 " + f_pct(probAcc) + "｜再出貨 " + f_pct(probRedist), alert.freq_once_per_bar_close)
...
1837:     if redDn and not redDn[1]
1838:         alert("Chase Risk v0.5｜下跌末段恐慌紅燈｜分數 " + f_num(endRiskDn) + "｜這不是抄底訊號。", alert.freq_once_per_bar_close)
1839:     if breakoutModeUp and not breakoutModeUp[1]
1840:         alert("Chase Risk v0.5｜突破啟動模式出現｜上漲即時熱度 " + f_num(heatUp), alert.freq_once_per_bar_close)
1841:     if breakdownModeDn and not breakdownModeDn[1]
1842:         alert("Chase Risk v0.5｜下破啟動模式出現｜下跌即時恐慌熱度 " + f_num(panicHeatDn), alert.freq_once_per_bar_close)
1843:     if anyEvidenceCross
