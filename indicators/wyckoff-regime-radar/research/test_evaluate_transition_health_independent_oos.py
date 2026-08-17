import unittest

from evaluate_transition_health_independent_oos import EXPECTED_PAIRS, load_frozen_pairs


class TransitionHealthIndependentOOSTests(unittest.TestCase):
    def test_frozen_manifest_and_hashes_load(self):
        manifest, pairs = load_frozen_pairs()
        self.assertEqual(set(pairs), EXPECTED_PAIRS)
        self.assertEqual(manifest["score_start"], "2022-01-01")
        self.assertEqual(manifest["score_end"], "2026-08-14")
        for pair, frame in pairs.items():
            self.assertGreater(len(frame), 2000, pair)
            self.assertEqual(str(frame["date"].iloc[-1]), "2026-08-14")


if __name__ == "__main__":
    unittest.main()
