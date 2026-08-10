#!/usr/bin/env python3

from __future__ import annotations

import unittest

import numpy as np

from diagnose_v06_state_cardinality import STATE_MAPS, _map_states


class V06StateCardinalityTests(unittest.TestCase):
    def test_all_mappings_cover_exactly_six_source_stages(self) -> None:
        expected = set(range(1, 7))
        for name, mapping in STATE_MAPS.items():
            with self.subTest(name=name):
                self.assertEqual(set(mapping), expected)

    def test_predeclared_four_state_semantics(self) -> None:
        mapping = STATE_MAPS["four_state"]
        self.assertEqual(mapping[1], mapping[3])
        self.assertEqual(mapping[4], mapping[6])
        self.assertNotEqual(mapping[2], mapping[5])
        self.assertEqual(len(set(mapping.values())), 4)

    def test_predeclared_three_state_semantics(self) -> None:
        mapping = STATE_MAPS["three_state"]
        self.assertEqual({mapping[1], mapping[3], mapping[4], mapping[6]}, {1})
        self.assertEqual(mapping[2], 2)
        self.assertEqual(mapping[5], 3)
        self.assertEqual(len(set(mapping.values())), 3)

    def test_mapping_preserves_neutral_zero(self) -> None:
        formal = np.array([0, 1, 2, 3, 4, 5, 6], dtype=int)
        mapped = _map_states(formal, STATE_MAPS["four_state"])
        np.testing.assert_array_equal(mapped, np.array([0, 1, 2, 1, 3, 4, 3], dtype=int))


if __name__ == "__main__":
    unittest.main()
