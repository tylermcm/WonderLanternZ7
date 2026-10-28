"""A native yellow menu highlight must not be reported as a leftover spiral."""
from pathlib import Path
import sys
import unittest

from PIL import Image, ImageDraw

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'tools'))
from probe_spiral_lifecycle import classify_pixels
from probe_spiral_gray import classify_gray
from spiral_geometry import spiral_points


class SpiralObservationTests(unittest.TestCase):
    def test_nikon_menu_yellow_and_scene_bars_are_not_the_curve(self):
        for color in ((252, 215, 37), (251, 214, 36), (250, 213, 36),
                      (242, 212, 72), (255, 255, 0), (255, 255, 255)):
            with self.subTest(color=color):
                self.assertEqual(classify_pixels(Image.new('RGB', (10, 10), color))['curve'], 0)

    def test_asset_and_observed_native_curve_colors_are_counted(self):
        for color in ((255, 208, 64), (255, 208, 65)):
            with self.subTest(color=color):
                self.assertEqual(classify_pixels(Image.new('RGB', (10, 10), color))['curve'], 100)

    def test_gray_straight_grids_and_lower_gradient_do_not_count_as_curve(self):
        image = Image.new('RGB', (720, 480), (0, 255, 255))
        draw = ImageDraw.Draw(image)
        draw.rectangle((0, 240, 720, 480), fill=(216, 216, 216))
        for ratio in (1/3, 2/3, .38196601125, .61803398875):
            x, y = round(720*ratio), round(480*ratio)
            draw.line((x, 0, x, 480), fill=(216, 216, 216), width=2)
            draw.line((0, y, 720, y), fill=(216, 216, 216), width=2)
        self.assertEqual(classify_gray(image)['curve'], 0)
        draw.line(spiral_points(), fill=(216, 216, 216), width=2)
        self.assertGreater(classify_gray(image)['curve'], 1000)
