import unittest
from fishing.scene import manual_target


class CollectionTests(unittest.TestCase):
    def test_manual_point_scales_and_rejects_overlay(self):
        self.assertEqual(manual_target(1920, 1080, (.5, .4)), (960, 432))
        self.assertEqual(manual_target(960, 540, (.5, .4)), (480, 216))
        with self.assertRaises(ValueError):
            manual_target(1920, 1080, (.5, .4), (900, 400, 1000, 500))
        with self.assertRaises(ValueError):
            manual_target(1920, 1080, None)
