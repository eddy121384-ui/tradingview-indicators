#!/usr/bin/env python3

from __future__ import annotations

import unittest

import pandas as pd

from diagnose_v06_state_persistence import analyze_outputs


class V06StatePersistenceMetricTests(unittest.TestCase):
    def test_metrics_detect_disagreement_carry_adoption_and_one_bar_flip(self) -> None:
        # Formal path contains a deliberate 1 -> 2 -> 1 one-bar flip at bars 1..3,
        # then later adopts a sustained stage-2 strong candidate after two bars.
        outputs = pd.DataFrame(
            {
                "candidate_id": [0, 0, 0, 0, 2, 2, 2, 0, 0, 0],
                "candidate_display_id": [0, 0, 0, 0, 2, 2, 2, 4, 0, 0],
                "formal_id": [1, 1, 2, 1, 1, 1, 2, 2, 2, 0],
            }
        )
        metrics = analyze_outputs(outputs)

        self.assertEqual(metrics["bars"], 10)
        self.assertEqual(metrics["one_bar_formal_flips"], 1)
        self.assertGreater(metrics["formal_carry_without_strong_candidate_share"], 0.0)
        self.assertGreater(metrics["candidate_formal_disagreement_share_candidate_bars"], 0.0)
        self.assertEqual(metrics["candidate_adoption"]["switch_demand_candidate_runs"], 1)
        self.assertEqual(metrics["candidate_adoption"]["adopted_runs"], 1)
        self.assertEqual(metrics["candidate_adoption"]["adopted_delay_bars"]["median"], 2.0)
        self.assertGreater(metrics["weak_only_candidate_share"], 0.0)

    def test_empty_candidate_demands_do_not_invent_adoption_rate(self) -> None:
        outputs = pd.DataFrame(
            {
                "candidate_id": [0, 0, 0, 0],
                "candidate_display_id": [0, 0, 0, 0],
                "formal_id": [0, 0, 0, 0],
            }
        )
        metrics = analyze_outputs(outputs)
        self.assertIsNone(metrics["candidate_adoption"]["adoption_rate"])
        self.assertEqual(metrics["candidate_adoption"]["switch_demand_candidate_runs"], 0)
        self.assertEqual(metrics["formal_switches"], 0)
        self.assertEqual(metrics["one_bar_formal_flips"], 0)


if __name__ == "__main__":
    unittest.main()
