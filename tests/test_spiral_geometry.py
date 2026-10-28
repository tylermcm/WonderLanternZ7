"""Verify actual Fibonacci arc joins and bounds, independently of rendering."""
import math
from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'tools'))
from spiral_geometry import fibonacci_arcs, spiral_points, overlay_png


class SpiralTests(unittest.TestCase):
    def test_fibonacci_tiling_and_tangent_continuity(self):
        arcs = fibonacci_arcs()
        self.assertEqual(sum(arc[2] ** 2 for arc in arcs), 144 * 89)
        for left, right in zip(arcs, arcs[1:]):
            a = (left[0] + left[2] * math.cos(left[4]), left[1] + left[2] * math.sin(left[4]))
            b = (right[0] + right[2] * math.cos(right[3]), right[1] + right[2] * math.sin(right[3]))
            self.assertAlmostEqual(math.dist(a, b), 0)
            self.assertAlmostEqual(math.cos(left[4]), math.cos(right[3]))
            self.assertAlmostEqual(math.sin(left[4]), math.sin(right[3]))

    def test_bounds_aspect_and_mirrors(self):
        for width, height in ((720, 480), (1024, 682), (640, 426), (480, 720)):
            original = spiral_points(width, height)
            for x, y in original:
                self.assertTrue(11.99 <= x <= width - 12.99)
                self.assertTrue(11.99 <= y <= height - 12.99)
            mirrored = spiral_points(width, height, mirror_x=True, mirror_y=True)
            self.assertTrue(all(abs(a[0] + b[0] - width + 1) < 1e-8
                                and abs(a[1] + b[1] - height + 1) < 1e-8
                                for a, b in zip(original, mirrored)))

    def test_asset_is_sparse_transparent_rgba(self):
        image, encoded = overlay_png()
        self.assertEqual(image.mode, 'RGBA')
        self.assertEqual(image.size, (720, 480))
        self.assertEqual(encoded[24:26], bytes([8, 6]))
        opaque = sum(alpha != 0 for alpha in image.getchannel('A').tobytes())
        self.assertTrue(100 < opaque < 720 * 480 // 20)
        self.assertEqual(image.getpixel((0, 0)), (0, 0, 0, 0))

    def test_invalid_dimensions(self):
        for args in ((24, 480), (720, 24), (720, 480, -1)):
            with self.assertRaises(ValueError):
                spiral_points(*args)

    def test_gray_variant_matches_native_grid_rgb_and_keeps_transparency(self):
        image, encoded = overlay_png(color=(216, 216, 216, 255))
        colors = set(image.getdata())
        self.assertEqual(colors, {(0, 0, 0, 0), (216, 216, 216, 255)})
        self.assertEqual(encoded[24:26], bytes([8, 6]))


if __name__ == '__main__':
    unittest.main()
