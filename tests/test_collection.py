import unittest
from fishing.collection import ReelGate
from fishing.scene import manual_target


class CollectionTests(unittest.TestCase):
    def test_early_prompt_does_not_collect(self):
        gate = ReelGate(0, delay=4)
        self.assertFalse(gate.update((.5, .5), 1))
        self.assertFalse(gate.update((.5, .5), 2))
        self.assertFalse(gate.update((.5, .5), 3.9))
        self.assertTrue(gate.update((.5, .5), 4))

    def test_moving_prompt_must_settle(self):
        gate = ReelGate(0)
        self.assertFalse(gate.update((.3, .5), 4))
        self.assertFalse(gate.update((.4, .5), 4.5))
        self.assertFalse(gate.update((.5, .5), 5))
        self.assertFalse(gate.update((.501, .5), 5.5))
        self.assertTrue(gate.update((.5, .5), 6))

    def test_missing_prompt_never_triggers_collection(self):
        gate = ReelGate(0)
        self.assertFalse(gate.update(None, 10))
        self.assertFalse(gate.update((.5, .5), 11))
        self.assertFalse(gate.update(None, 12))
        self.assertFalse(gate.update((.5, .5), 13))
        self.assertTrue(gate.update((.5, .5), 14))

    def test_brief_detection_flicker_preserves_settling(self):
        gate = ReelGate(0)
        self.assertFalse(gate.update((.5, .5), 4))
        self.assertFalse(gate.update((.5, .5), 4.3))
        self.assertFalse(gate.update(None, 4.5))
        self.assertFalse(gate.update((.5, .5), 4.6))
        self.assertTrue(gate.update((.5, .5), 5))

    def test_manual_point_scales_and_rejects_overlay(self):
        self.assertEqual(manual_target(1920, 1080, (.5, .4)), (960, 432))
        self.assertEqual(manual_target(960, 540, (.5, .4)), (480, 216))
        with self.assertRaises(ValueError):
            manual_target(1920, 1080, (.5, .4), (900, 400, 1000, 500))
        with self.assertRaises(ValueError):
            manual_target(1920, 1080, None)
