"""Native HUD orientation and exclusive bounds; no guest or supplied pixels."""
import sys
import unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'tools'))
from display_pixel_geometry import control_scanout_box


class ControlGeometryTests(unittest.TestCase):
    def test_native_shooting_mode_stays_at_top_left(self):
        self.assertEqual(control_scanout_box((0, 0, 40, 40), (1024, 682)), (0, 0, 57, 57))

    def test_native_focus_mode_stays_at_top(self):
        self.assertEqual(control_scanout_box((283, 2, 333, 38), (1024, 682)), (402, 2, 474, 54))

    def test_native_exposure_readout_stays_at_bottom(self):
        self.assertEqual(control_scanout_box((116, 420, 590, 480), (720, 480)), (116, 420, 590, 480))

    def test_invalid_rectangles_and_sizes_reject(self):
        for rect, size in (((0, 0, 0, 1), (720, 480)), ((-1, 0, 1, 1), (720, 480)),
                           ((0, 0, 721, 480), (720, 480)), ((0, 0, 1, 481), (720, 480)),
                           ((0, 0, 1, 1), (0, 480))):
            with self.assertRaises(ValueError): control_scanout_box(rect, size)


if __name__ == '__main__': unittest.main()
