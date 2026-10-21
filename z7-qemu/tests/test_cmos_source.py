# SPDX-License-Identifier: GPL-2.0-or-later
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]/"tools"))
import unittest
import numpy as np
from cmos_source import mosaic, pack_rows, scene


class SensorSourceTests(unittest.TestCase):
    def test_cfa_channels_and_levels(self):
        red = np.zeros((2, 2, 3)); red[..., 0] = 1
        expected = {'RGGB': [[4095, 64], [64, 64]], 'BGGR': [[64, 64], [64, 4095]],
                    'GRBG': [[64, 4095], [64, 64]], 'GBRG': [[64, 64], [4095, 64]]}
        for cfa, result in expected.items():
            self.assertEqual(mosaic(red, cfa, 12, 64).tolist(), result)

    def test_little_endian_and_row_padding(self):
        self.assertEqual(pack_rows([[0x123, 0x456], [0x789, 0xabc]], 6),
                         bytes.fromhex('2301560400008907bc0a0000'))

    def test_repeatability_frame_progress_and_static_region(self):
        first, later = scene(64, 48, 0), scene(64, 48, 1)
        np.testing.assert_array_equal(first, scene(64, 48, 0))
        np.testing.assert_array_equal(first[:36], later[:36])
        self.assertFalse(np.array_equal(first[36:], later[36:]))

    def test_invalid_geometry_and_stride(self):
        with self.assertRaises(ValueError):
            scene(63, 48, 0)
        with self.assertRaises(ValueError):
            pack_rows([[0, 1]], 2)
        with self.assertRaises(ValueError):
            mosaic(np.ones((2, 2, 3)), 'RGGB', 12, 4095)


if __name__ == '__main__':
    unittest.main()
