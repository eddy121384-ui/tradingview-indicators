import unittest

import pandas as pd

from freeze_transition_health_independent_oos import normalize_download, sha256_bytes


class FreezeTransitionHealthOOSTests(unittest.TestCase):
    def test_normalize_download_keeps_sorted_unique_ohlc(self):
        idx = pd.to_datetime(["2024-01-03", "2024-01-02", "2024-01-02"])
        raw = pd.DataFrame(
            {
                "Open": [1.2, 1.0, 1.0],
                "High": [1.3, 1.1, 1.1],
                "Low": [1.1, 0.9, 0.9],
                "Close": [1.25, 1.05, 1.05],
            },
            index=idx,
        )
        out = normalize_download(raw)
        self.assertEqual(list(out.columns), ["date", "open", "high", "low", "close"])
        self.assertEqual([str(x) for x in out["date"]], ["2024-01-02", "2024-01-03"])

    def test_sha256_is_deterministic(self):
        self.assertEqual(sha256_bytes(b"abc"), "ba7816bf8f01cfea414140de5dae2223b00361a396177a9cb410ff61f20015ad")


if __name__ == "__main__":
    unittest.main()
