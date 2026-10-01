import unittest
from pathlib import Path
from PIL import Image
from fishing.control import Controller
from fishing.vision import Detection, automatic_region, detect


class ControlTests(unittest.TestCase):
    def test_video_square_above_rectangle_releases_instead_of_chasing_leaves(self):
        with Image.open(Path(__file__).parent/'fixtures'/'bar_leaves_20.png') as im:
            d = detect(im)
        self.assertLess(d.cursor, d.target_top)
        self.assertFalse(Controller().update(d, 0, True))

    def test_moves_toward_target_and_can_invert(self):
        d = Detection(.5, .7, .1)
        self.assertTrue(Controller().update(d, 0, False))
        self.assertFalse(Controller().update(d, 0, False, invert=True))

    def test_brakes_before_overshoot(self):
        c = Controller()
        c.update(Detection(.5, .58, .1), 0, True)
        # Cursor is above its previous position and still below the center.
        self.assertFalse(c.update(Detection(.5, .515, .1), .05, True))

    def test_reset_discards_stale_velocity(self):
        c = Controller()
        c.update(Detection(.5, .58, .1), 0, True)
        c.update(Detection(.5, .515, .1), .05, True)
        c.reset()
        self.assertTrue(c.update(Detection(.5, .515, .1), 1, False))

    def test_dead_band_prevents_input_chatter(self):
        d = Detection(.5, .501, .1)
        self.assertTrue(Controller().update(d, 0, True))
        self.assertFalse(Controller().update(d, 0, False))

    def test_brakes_upward_motion_even_before_reaching_target(self):
        c = Controller()
        c.update(Detection(.5, .66, .1), 0, True)
        self.assertFalse(c.update(Detection(.5, .63, .1), .04, True))
        self.assertFalse(c.brake(True))

    def test_brakes_downward_motion_and_preserves_inverted_control(self):
        c = Controller()
        c.update(Detection(.5, .34, .1), 0, False)
        self.assertTrue(c.update(Detection(.5, .37, .1), .04, False))
        self.assertTrue(c.brake(False))
        self.assertFalse(c.brake(True, invert=True))

    def test_long_gap_discards_motion_and_accumulated_correction(self):
        c = Controller()
        c.update(Detection(.5, .56, .1), 0, True)
        c.update(Detection(.5, .54, .1), .04, True)
        c.update(Detection(.5, .5, .1), 1, False)
        self.assertEqual(c.cursor_speed, 0)
        self.assertEqual(c.bias, 0)

    def test_region_scales_with_game_window(self):
        a = automatic_region(1920, 1080)
        b = automatic_region(960, 540)
        self.assertTrue(all(abs(x-2*y) <= 1 for x, y in zip(a, b)))


if __name__ == '__main__':
    unittest.main()
