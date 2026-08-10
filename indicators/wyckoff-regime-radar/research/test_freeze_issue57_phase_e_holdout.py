#!/usr/bin/env python3

from __future__ import annotations

import unittest

from freeze_issue57_phase_e_holdout import (
    EXPECTED_END,
    EXPECTED_ROWS,
    EXPECTED_START,
    HOLDOUT_PAIRS,
    SOURCE_COMMIT,
    _source_path,
)


class Issue57PhaseEHoldoutFreezeTests(unittest.TestCase):
    def test_holdout_pair_set_is_exact_and_untouched(self) -> None:
        self.assertEqual(HOLDOUT_PAIRS, ("USDCAD", "USDCHF", "NZDUSD"))

    def test_source_is_pinned_to_issue55_static_commit(self) -> None:
        self.assertEqual(SOURCE_COMMIT, "a7c5089d96379d4de03cf0001eb5807304675f0e")
        self.assertEqual(_source_path("USDCAD"), "USDCAD/USDCAD_D1.csv")

    def test_expected_coverage_is_frozen_before_download(self) -> None:
        self.assertEqual(EXPECTED_ROWS, 2400)
        self.assertEqual(EXPECTED_START, "2012-12-04")
        self.assertEqual(EXPECTED_END, "2022-03-04")


if __name__ == "__main__":
    unittest.main()
