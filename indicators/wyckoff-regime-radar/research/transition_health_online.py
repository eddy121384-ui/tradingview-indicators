#!/usr/bin/env python3
"""Online Transition Health state machine for Issue #57.

This module is an implementation of the frozen visual-preview contract.  It is
intentionally threshold-free beyond the already frozen +3 checkpoint and 20-bar
bridge watch horizon.  The output is descriptive state/pulse data, not a trading
signal.
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from diagnose_bridge_formation_outcomes import bridge_direction
from diagnose_consensus_formation_and_formal_lag import action_pair_direction
from diagnose_handoff_weight_behavior import decompose_bridge
from diagnose_transition_formation_and_regime_decay import weight_matrix
from diagnose_v06_top2_directional_consensus import top_ids_and_values

CHECKPOINT = 3
MAX_WATCH_BARS = 20

STATE_NONE = 0
STATE_HANDOFF = 1
STATE_HEALTHY = 2
STATE_DAMAGED = 3


def compute_transition_health(model: pd.DataFrame) -> pd.DataFrame:
    """Return one online Transition Health row per model bar.

    Non-overlap, resolution timing, seizure eligibility and +3 health semantics
    are written to mirror the frozen research extractor exactly.
    """
    top1, top2, _, _ = top_ids_and_values(model)
    bridge = bridge_direction(top1, top2)
    actionable = action_pair_direction(top1, top2)
    weights = weight_matrix(model)
    n = len(model)

    state = np.zeros(n, dtype=int)
    direction = np.zeros(n, dtype=int)
    watch_age = np.zeros(n, dtype=int)
    handoff_pulse = np.zeros(n, dtype=bool)
    healthy_pulse = np.zeros(n, dtype=bool)
    damaged_pulse = np.zeros(n, dtype=bool)
    resolution_pulse = np.zeros(n, dtype=bool)
    tracked_out = np.zeros(n, dtype=bool)
    lead_held_out = np.zeros(n, dtype=bool)

    active = False
    watch_dir = 0
    age = 0
    context_id = 0
    carried_id = 0
    tracked = False
    lead_held = False
    current_state = STATE_NONE

    for i in range(n):
        if not active:
            if float(bridge[i]) != 0.0:
                active = True
                watch_dir = int(bridge[i])
                age = 0
                context_id, carried_id, _ = decompose_bridge(int(top1[i]), int(top2[i]), float(watch_dir))
                context_weight = float(weights[i, context_id - 1])
                carried_weight = float(weights[i, carried_id - 1])
                tracked = bool(carried_weight > context_weight)
                lead_held = tracked
                current_state = STATE_HANDOFF if tracked else STATE_NONE
                if tracked:
                    handoff_pulse[i] = True
        else:
            age += 1
            resolves_now = (
                int(actionable[i]) == watch_dir
                or int(actionable[i]) == -watch_dir
                or age >= MAX_WATCH_BARS
            )

            if tracked and age <= CHECKPOINT:
                context_weight = float(weights[i, context_id - 1])
                carried_weight = float(weights[i, carried_id - 1])
                # Frozen research uses np.all(carried > context). Any NaN therefore
                # breaks the continuous-hold condition rather than being ignored.
                if not (carried_weight > context_weight):
                    lead_held = False

            # Frozen research eligibility is resolution_lag > CHECKPOINT.
            if tracked and age == CHECKPOINT and not resolves_now:
                if lead_held:
                    current_state = STATE_HEALTHY
                    healthy_pulse[i] = True
                else:
                    current_state = STATE_DAMAGED
                    damaged_pulse[i] = True

            if resolves_now:
                resolution_pulse[i] = True
                active = False
                watch_dir = 0
                age = 0
                context_id = 0
                carried_id = 0
                tracked = False
                lead_held = False
                current_state = STATE_NONE

        state[i] = current_state
        direction[i] = watch_dir if tracked else 0
        watch_age[i] = age if active else 0
        tracked_out[i] = tracked
        lead_held_out[i] = lead_held if tracked else False

    return pd.DataFrame(
        {
            "transition_health_state": state,
            "transition_health_direction": direction,
            "transition_health_watch_age": watch_age,
            "transition_health_tracked": tracked_out,
            "transition_health_lead_held": lead_held_out,
            "transition_health_handoff_pulse": handoff_pulse,
            "transition_health_healthy_pulse": healthy_pulse,
            "transition_health_damaged_pulse": damaged_pulse,
            "transition_health_resolution_pulse": resolution_pulse,
        },
        index=model.index,
    )
