import unittest
from fishing.control import Controller
from fishing.vision import Detection, automatic_region


class ControlTests(unittest.TestCase):
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

    def test_region_scales_with_game_window(self):
        a = automatic_region(1920, 1080)
        b = automatic_region(960, 540)
        self.assertTrue(all(abs(x-2*y) <= 1 for x, y in zip(a, b)))


if __name__ == '__main__':
    unittest.main()
