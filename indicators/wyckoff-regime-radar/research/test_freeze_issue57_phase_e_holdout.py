#!/usr/bin/env python3

from __future__ import annotations

import unittest

from freeze_issue57_phase_e_holdout import (
    EXPECTED_COVERAGE,
    HOLDOUT_PAIRS,
    SOURCE_REF,
    _source_path,
)


class Issue57PhaseEHoldoutFreezeTests(unittest.TestCase):
    def test_holdout_pair_set_is_exact_and_untouched(self) -> None:
        self.assertEqual(HOLDOUT_PAIRS, ("USDCAD", "USDCHF", "EURCHF"))

    def test_source_contract_matches_static_repo(self) -> None:
        self.assertEqual(SOURCE_REF, "main")
        self.assertEqual(_source_path("USDCAD"), "USDCAD/USDCADd1.csv")
        self.assertEqual(_source_path("USDCHF"), "USDCHF/USDCHFd1.csv")
        self.assertEqual(_source_path("EURCHF"), "EURCHF/EURCHFd1.csv")

    def test_expected_coverage_is_frozen_per_pair_before_download(self) -> None:
        self.assertEqual(
            EXPECTED_COVERAGE,
            {
                "USDCAD": {"rows": 2400, "start": "2012-12-04", "end": "2022-03-04"},
                "USDCHF": {"rows": 2400, "start": "2012-12-03", "end": "2022-03-04"},
                "EURCHF": {"rows": 2400, "start": "2012-11-16", "end": "2022-03-04"},
            },
        )


if __name__ == "__main__":
    unittest.main()
