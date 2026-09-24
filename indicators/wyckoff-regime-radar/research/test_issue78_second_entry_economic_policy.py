#!/usr/bin/env python3
from __future__ import annotations

import pandas as pd

import analyze_issue78_second_entry_economic_policy as m


def fake_episode(stage=2, n=8):
    rows = [
        {
            "event_time": 1_700_000_000_000 + i * 86_400_000,
            "move1": 0.1,
            "scale": 1.0,
            "repr": "PRICE",
        }
        for i in range(n)
    ]
    return ("TEST", stage, 0, 0, rows)


def fake_frames(closes):
    return {
        "TEST": pd.DataFrame(
            {
                "close_coord": closes,
                "high_coord": [x + 0.1 for x in closes],
                "low_coord": [x - 0.1 for x in closes],
            }
        )
    }


def levels(direction=1):
    return {
        "t3_idx": 3,
        "t3_local": 3,
        "direction": direction,
        "r5_anchor": 0.7 if direction == 1 else -0.7,
        "r1_anchor": 1.0 if direction == 1 else -1.0,
        "r4_anchor": 0.9 if direction == 1 else -0.9,
        "box_high": 0.2,
        "box_low": -0.2,
    }


def test_markup_trigger_timing():
    episode = fake_episode(stage=2)
    frames = fake_frames([0.0, 0.1, 0.2, 0.3, 0.5, 0.8, 1.2, 1.1])
    state = {"path": "P1_WickHold"}
    lv = levels(1)

    expected = {
        "R0_Immediate": 3,
        "R5_LocalClose": 5,
        "R1_CloseExtreme": 6,
        "R4_Progress05": 6,
    }
    for policy, trigger in expected.items():
        exp, got = m.exposures_for_episode(policy, episode, state, lv, frames)
        assert got == trigger, (policy, got, trigger)
        assert exp[:trigger] == [m.PROBE] * trigger
        assert exp[trigger:] == [m.FULL] * (len(exp) - trigger)


def test_markdown_trigger_timing():
    episode = fake_episode(stage=5)
    frames = fake_frames([0.0, -0.1, -0.2, -0.3, -0.5, -0.8, -1.2, -1.1])
    state = {"path": "P2_Reclaim"}
    lv = levels(-1)

    expected = {
        "R0_Immediate": 3,
        "R5_LocalClose": 5,
        "R1_CloseExtreme": 6,
        "R4_Progress05": 6,
    }
    for policy, trigger in expected.items():
        exp, got = m.exposures_for_episode(policy, episode, state, lv, frames)
        assert got == trigger, (policy, got, trigger)
        assert exp[:trigger] == [m.PROBE] * trigger
        assert exp[trigger:] == [m.FULL] * (len(exp) - trigger)


def test_p0_adds_at_t3_for_all_candidates():
    episode = fake_episode()
    frames = fake_frames([0.0] * 8)
    state = {"path": "P0_NoTouch"}
    lv = levels(1)
    for policy in m.CANDIDATES:
        exp, trigger = m.exposures_for_episode(policy, episode, state, lv, frames)
        assert trigger == 3
        assert exp[:3] == [m.PROBE] * 3
        assert exp[3:] == [m.FULL] * 5


def test_p3_never_adds():
    episode = fake_episode()
    frames = fake_frames([0.0, 0.2, 0.4, 0.6, 1.2, 1.5, 2.0, 3.0])
    state = {"path": "P3_FailedAcceptance"}
    lv = levels(1)
    for policy in m.CANDIDATES:
        exp, trigger = m.exposures_for_episode(policy, episode, state, lv, frames)
        assert trigger is None
        assert exp == [m.PROBE] * len(exp)


def test_no_usable_b3_remains_probe():
    episode = fake_episode()
    frames = fake_frames([0.0] * 8)
    for policy in m.CANDIDATES:
        exp, trigger = m.exposures_for_episode(policy, episode, None, None, frames)
        assert trigger is None
        assert exp == [m.PROBE] * len(exp)


def test_no_trigger_is_counted_as_missed_opportunity_not_dropped():
    episode = fake_episode()
    frames = fake_frames([0.0, 0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.65])
    state = {"path": "P1_WickHold"}
    lv = levels(1)
    for policy in ("R5_LocalClose", "R1_CloseExtreme", "R4_Progress05"):
        exp, trigger = m.exposures_for_episode(policy, episode, state, lv, frames)
        assert trigger is None
        assert exp == [m.PROBE] * len(exp)


def test_probe_and_formal_hold_accounting_baselines():
    episode = fake_episode()
    frames = fake_frames([0.0] * 8)
    probe, probe_trigger = m.exposures_for_episode(
        "ProbeOnly", episode, None, None, frames
    )
    full, full_trigger = m.exposures_for_episode(
        "FormalHold", episode, None, None, frames
    )
    assert probe == [m.PROBE] * 8
    assert probe_trigger is None
    assert full == [m.FULL] * 8
    assert full_trigger == 0
