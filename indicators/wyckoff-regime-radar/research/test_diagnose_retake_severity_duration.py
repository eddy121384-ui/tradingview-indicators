import unittest

import numpy as np
import pandas as pd

from diagnose_retake_severity_duration import (
    duration_bin,
    first_control_spell_metrics,
    normalized_margin,
    severity_terciles,
)


class RetakeSeverityDurationTests(unittest.TestCase):
    def test_normalized_margin_is_scale_free(self):
        self.assertAlmostEqual(normalized_margin(60.0, 40.0), 0.2)
        self.assertAlmostEqual(normalized_margin(30.0, 20.0), 0.2)

    def test_first_control_spell_stops_when_carried_regains_lead(self):
        # columns are context stage 1 and carried stage 2; other stages remain zero
        weights = np.array([
            [40.0, 60.0, 0, 0, 0, 0],  # onset: carried leads
            [55.0, 45.0, 0, 0, 0, 0],  # retake lag 1
            [70.0, 30.0, 0, 0, 0, 0],  # old context still controls
            [45.0, 55.0, 0, 0, 0, 0],  # reseizure -> stop before this bar
            [80.0, 20.0, 0, 0, 0, 0],
        ])
        out = first_control_spell_metrics(weights, 0, 1, 5, 1, 2)
        self.assertEqual(out["first_control_spell_bars"], 2)
        self.assertAlmostEqual(out["normalized_first_retake_margin"], 0.10)
        self.assertAlmostEqual(out["max_normalized_retake_margin"], 0.40)
        self.assertAlmostEqual(out["dominance_area"], 0.50)

    def test_resolution_boundary_is_not_included(self):
        weights = np.array([
            [40.0, 60.0, 0, 0, 0, 0],
            [55.0, 45.0, 0, 0, 0, 0],
            [60.0, 40.0, 0, 0, 0, 0],
            [90.0, 10.0, 0, 0, 0, 0],  # resolution lag 3; excluded
        ])
        out = first_control_spell_metrics(weights, 0, 1, 3, 1, 2)
        self.assertEqual(out["first_control_spell_bars"], 2)
        self.assertAlmostEqual(out["max_normalized_retake_margin"], 0.20)

    def test_duration_bins_are_fixed(self):
        self.assertEqual(duration_bin(1), "1_bar")
        self.assertEqual(duration_bin(2), "2_3_bars")
        self.assertEqual(duration_bin(3), "2_3_bars")
        self.assertEqual(duration_bin(4), "4_plus_bars")

    def test_severity_terciles_use_predictor_rank_only(self):
        values = pd.Series([0.10, 0.20, 0.30, 0.40, 0.50, 0.60])
        bins = severity_terciles(values).tolist()
        self.assertEqual(bins, ["low", "low", "mid", "mid", "high", "high"])


if __name__ == "__main__":
    unittest.main()
