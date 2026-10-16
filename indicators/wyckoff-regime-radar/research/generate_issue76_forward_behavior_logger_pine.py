#!/usr/bin/env python3
"""Generate the Issue #76 forward-behavior Pine logger from the frozen Issue #68 RC.

The generator is intentionally mechanical: it verifies the exact Git blob SHA of
Issue #68's merged release-candidate source, changes only the indicator identity,
and injects a research-only logging block immediately before the existing Visuals
section. Classifier semantics are not reimplemented or modified.
"""
from __future__ import annotations

import argparse
import hashlib
from pathlib import Path

FROZEN_SOURCE_BLOB = "e5c3fd2622841a6d3f97bdda4b9d0a6378ebda55"
SOURCE_NAME = "chase-risk-market-regime-radar-issue68-rc.pine"
DECL_OLD = 'indicator("Chase Risk Market Regime Radar｜Issue #68 RC", shorttitle="ChaseRisk Radar #68 RC", overlay=false, precision=1)'
DECL_NEW = 'indicator("Wyckoff Regime Radar｜Issue #76 Forward Behavior Logger", shorttitle="#76 Forward Logger", overlay=false, precision=1)'
ANCHOR = "// Visuals"

LOGGER_BLOCK = r'''
// ============================================================================
// Issue #76 — research-only forward-behavior logger.
// Frozen source: Issue #68 merged RC. NO CLASSIFIER TUNING. NO PNL. NO STRATEGY.
// One log row corresponds to event bar t = current bar - 20, so all frozen
// horizons (1 / 5 / 10 / 20 bars) are already observed when the row is emitted.
// ============================================================================

groupIssue76 = "研究｜Issue #76 Forward Behavior Export"
issue76LogEnabled = input.bool(true, "Enable Issue #76 Pine Logs", group=groupIssue76)
issue76LogStart = input.time(0, "Event start time (1970 = all)", group=groupIssue76)
issue76LogEnd = input.time(4102444800000, "Event end time (2100 = all)", group=groupIssue76)

issue76AllowedFeed = syminfo.tickerid == "OANDA:EURUSD" or syminfo.tickerid == "OANDA:GBPUSD" or syminfo.tickerid == "OANDA:USDJPY" or syminfo.tickerid == "TVC:US10Y" or syminfo.tickerid == "TVC:DE10Y" or syminfo.tickerid == "TVC:FR10Y" or syminfo.tickerid == "TVC:GB10Y" or syminfo.tickerid == "TVC:AU10Y" or syminfo.tickerid == "TVC:JP10Y"
issue76D1 = timeframe.isdaily and timeframe.multiplier == 1
issue76Representation = useYieldLevel ? "YIELD_LEVEL" : "PRICE_LOG"

f_issue76ModelMove(float pxNow, float pxEvent) =>
    useYieldLevel ? pxNow - pxEvent : math.log(pxNow / pxEvent)

f_issue76RawMove(float pxNow, float pxEvent) =>
    useYieldLevel ? (pxNow - pxEvent) * 100.0 : math.log(pxNow / pxEvent)

f_issue76NormMove(float pxNow, float pxEvent, float scale) =>
    scale > 0.0 ? f_issue76ModelMove(pxNow, pxEvent) / scale : na

issue76DeltaModel = useYieldLevel ? close - close[1] : math.log(close / close[1])
issue76EventTime = time[20]
issue76EventBar = bar_index - 20
issue76EventClose = close[20]
issue76EventFormal = formalId[20]
issue76PrevFormal = formalId[21]
issue76EventScale = symATR[20]
issue76Fresh = issue76EventFormal != issue76PrevFormal
issue76Transition = str.tostring(issue76PrevFormal) + ">" + str.tostring(issue76EventFormal)
issue76InWindow = issue76EventTime >= issue76LogStart and issue76EventTime <= issue76LogEnd

issue76Hi1 = high[19]
issue76Lo1 = low[19]
issue76Hi5 = ta.highest(high[15], 5)
issue76Lo5 = ta.lowest(low[15], 5)
issue76Hi10 = ta.highest(high[10], 10)
issue76Lo10 = ta.lowest(low[10], 10)
issue76Hi20 = ta.highest(high, 20)
issue76Lo20 = ta.lowest(low, 20)

issue76Move1 = f_issue76RawMove(close[19], issue76EventClose)
issue76Move5 = f_issue76RawMove(close[15], issue76EventClose)
issue76Move10 = f_issue76RawMove(close[10], issue76EventClose)
issue76Move20 = f_issue76RawMove(close, issue76EventClose)
issue76Norm1 = f_issue76NormMove(close[19], issue76EventClose, issue76EventScale)
issue76Norm5 = f_issue76NormMove(close[15], issue76EventClose, issue76EventScale)
issue76Norm10 = f_issue76NormMove(close[10], issue76EventClose, issue76EventScale)
issue76Norm20 = f_issue76NormMove(close, issue76EventClose, issue76EventScale)

issue76Mfe1 = f_issue76RawMove(issue76Hi1, issue76EventClose)
issue76Mfe5 = f_issue76RawMove(issue76Hi5, issue76EventClose)
issue76Mfe10 = f_issue76RawMove(issue76Hi10, issue76EventClose)
issue76Mfe20 = f_issue76RawMove(issue76Hi20, issue76EventClose)
issue76Mae1 = f_issue76RawMove(issue76Lo1, issue76EventClose)
issue76Mae5 = f_issue76RawMove(issue76Lo5, issue76EventClose)
issue76Mae10 = f_issue76RawMove(issue76Lo10, issue76EventClose)
issue76Mae20 = f_issue76RawMove(issue76Lo20, issue76EventClose)
issue76MfeNorm1 = f_issue76NormMove(issue76Hi1, issue76EventClose, issue76EventScale)
issue76MfeNorm5 = f_issue76NormMove(issue76Hi5, issue76EventClose, issue76EventScale)
issue76MfeNorm10 = f_issue76NormMove(issue76Hi10, issue76EventClose, issue76EventScale)
issue76MfeNorm20 = f_issue76NormMove(issue76Hi20, issue76EventClose, issue76EventScale)
issue76MaeNorm1 = f_issue76NormMove(issue76Lo1, issue76EventClose, issue76EventScale)
issue76MaeNorm5 = f_issue76NormMove(issue76Lo5, issue76EventClose, issue76EventScale)
issue76MaeNorm10 = f_issue76NormMove(issue76Lo10, issue76EventClose, issue76EventScale)
issue76MaeNorm20 = f_issue76NormMove(issue76Lo20, issue76EventClose, issue76EventScale)

issue76Rv1Model = math.abs(issue76DeltaModel[19])
issue76Rv5Model = math.sqrt(ta.sma(issue76DeltaModel[15] * issue76DeltaModel[15], 5))
issue76Rv10Model = math.sqrt(ta.sma(issue76DeltaModel[10] * issue76DeltaModel[10], 10))
issue76Rv20Model = math.sqrt(ta.sma(issue76DeltaModel * issue76DeltaModel, 20))
issue76Rv1 = useYieldLevel ? issue76Rv1Model * 100.0 : issue76Rv1Model
issue76Rv5 = useYieldLevel ? issue76Rv5Model * 100.0 : issue76Rv5Model
issue76Rv10 = useYieldLevel ? issue76Rv10Model * 100.0 : issue76Rv10Model
issue76Rv20 = useYieldLevel ? issue76Rv20Model * 100.0 : issue76Rv20Model
issue76RvNorm1 = issue76EventScale > 0.0 ? issue76Rv1Model / issue76EventScale : na
issue76RvNorm5 = issue76EventScale > 0.0 ? issue76Rv5Model / issue76EventScale : na
issue76RvNorm10 = issue76EventScale > 0.0 ? issue76Rv10Model / issue76EventScale : na
issue76RvNorm20 = issue76EventScale > 0.0 ? issue76Rv20Model / issue76EventScale : na

issue76Ready = issue76AllowedFeed and issue76D1 and issue76InWindow and issue76EventFormal >= 1 and issue76EventFormal <= 6 and not na(issue76PrevFormal) and not na(issue76EventScale) and issue76EventScale > 0.0 and not na(issue76Move20) and not na(issue76Rv20)

// Hidden channels are optional conveniences for plans that support chart CSV export.
plot(issue76AllowedFeed and issue76D1 ? formalId : na, "#76 Formal Stage ID", display=display.none)
plot(issue76AllowedFeed and issue76D1 ? symATR : na, "#76 Event-time SymATR", display=display.none)

if issue76LogEnabled and issue76Ready and barstate.isconfirmed
    log.info(
         "ISSUE76|schema=1" +
         "|ticker=" + syminfo.tickerid +
         "|tf=" + timeframe.period +
         "|repr=" + issue76Representation +
         "|event_time=" + str.tostring(issue76EventTime) +
         "|event_bar=" + str.tostring(issue76EventBar) +
         "|stage=" + str.tostring(issue76EventFormal) +
         "|prev=" + str.tostring(issue76PrevFormal) +
         "|fresh=" + (issue76Fresh ? "1" : "0") +
         "|transition=" + issue76Transition +
         "|scale=" + str.tostring(issue76EventScale, "#.##########") +
         "|move1=" + str.tostring(issue76Move1, "#.##########") + "|norm1=" + str.tostring(issue76Norm1, "#.##########") + "|mfe1=" + str.tostring(issue76Mfe1, "#.##########") + "|mae1=" + str.tostring(issue76Mae1, "#.##########") + "|mfen1=" + str.tostring(issue76MfeNorm1, "#.##########") + "|maen1=" + str.tostring(issue76MaeNorm1, "#.##########") + "|rv1=" + str.tostring(issue76Rv1, "#.##########") + "|rvn1=" + str.tostring(issue76RvNorm1, "#.##########") +
         "|move5=" + str.tostring(issue76Move5, "#.##########") + "|norm5=" + str.tostring(issue76Norm5, "#.##########") + "|mfe5=" + str.tostring(issue76Mfe5, "#.##########") + "|mae5=" + str.tostring(issue76Mae5, "#.##########") + "|mfen5=" + str.tostring(issue76MfeNorm5, "#.##########") + "|maen5=" + str.tostring(issue76MaeNorm5, "#.##########") + "|rv5=" + str.tostring(issue76Rv5, "#.##########") + "|rvn5=" + str.tostring(issue76RvNorm5, "#.##########") +
         "|move10=" + str.tostring(issue76Move10, "#.##########") + "|norm10=" + str.tostring(issue76Norm10, "#.##########") + "|mfe10=" + str.tostring(issue76Mfe10, "#.##########") + "|mae10=" + str.tostring(issue76Mae10, "#.##########") + "|mfen10=" + str.tostring(issue76MfeNorm10, "#.##########") + "|maen10=" + str.tostring(issue76MaeNorm10, "#.##########") + "|rv10=" + str.tostring(issue76Rv10, "#.##########") + "|rvn10=" + str.tostring(issue76RvNorm10, "#.##########") +
         "|move20=" + str.tostring(issue76Move20, "#.##########") + "|norm20=" + str.tostring(issue76Norm20, "#.##########") + "|mfe20=" + str.tostring(issue76Mfe20, "#.##########") + "|mae20=" + str.tostring(issue76Mae20, "#.##########") + "|mfen20=" + str.tostring(issue76MfeNorm20, "#.##########") + "|maen20=" + str.tostring(issue76MaeNorm20, "#.##########") + "|rv20=" + str.tostring(issue76Rv20, "#.##########") + "|rvn20=" + str.tostring(issue76RvNorm20, "#.##########"))

'''


def git_blob_sha(data: bytes) -> str:
    header = f"blob {len(data)}\0".encode("ascii")
    return hashlib.sha1(header + data).hexdigest()


def generate(source_path: Path) -> str:
    source_bytes = source_path.read_bytes()
    actual_blob = git_blob_sha(source_bytes)
    if actual_blob != FROZEN_SOURCE_BLOB:
        raise RuntimeError(
            f"frozen source blob mismatch: expected {FROZEN_SOURCE_BLOB}, got {actual_blob}"
        )

    source = source_bytes.decode("utf-8")
    if source.count(DECL_OLD) != 1:
        raise RuntimeError("expected exactly one frozen Issue #68 indicator declaration")
    if source.count(ANCHOR) != 1:
        raise RuntimeError("expected exactly one Visuals anchor")

    candidate = source.replace(DECL_OLD, DECL_NEW, 1)
    candidate = candidate.replace(ANCHOR, LOGGER_BLOCK + "\n" + ANCHOR, 1)

    required = (
        'syminfo.tickerid == "OANDA:EURUSD"',
        'syminfo.tickerid == "TVC:JP10Y"',
        'issue76EventFormal = formalId[20]',
        'issue76EventScale = symATR[20]',
        'issue76Move20 = f_issue76RawMove(close, issue76EventClose)',
        'ISSUE76|schema=1',
        'ctxDownExGate = math.min(downsideExhaustionGate, currentBearGate)',
        'ctxUpExGate = math.min(upsideExhaustionGate, currentBullGate)',
        'autoYieldLevel = syminfo.type == "bond" and syminfo.currency == "NONE"',
    )
    for token in required:
        if token not in candidate:
            raise RuntimeError(f"generated logger missing required token: {token}")

    for forbidden in ("strategy.entry", "strategy.close", "STATEFUL CTX"):
        if forbidden in LOGGER_BLOCK:
            raise RuntimeError(f"forbidden research construct in logger block: {forbidden}")

    return candidate


def main() -> None:
    ap = argparse.ArgumentParser(description="Generate Issue #76 forward-behavior Pine logger")
    default_source = Path(__file__).resolve().parents[1] / "src" / SOURCE_NAME
    ap.add_argument("--source", type=Path, default=default_source)
    ap.add_argument("--output", type=Path, required=True)
    args = ap.parse_args()

    text = generate(args.source)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(text, encoding="utf-8")
    print(args.output)
    print("Issue #76 forward-behavior logger generator PASS")


if __name__ == "__main__":
    main()
