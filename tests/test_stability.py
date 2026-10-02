import unittest
import numpy as np
import cv2
from PIL import Image
from fishing.stability import SceneStability


class StabilityTests(unittest.TestCase):
    def terrain(self):
        rng = np.random.default_rng(4)
        noise = rng.integers(30, 160, (180, 320), dtype=np.uint8)
        return np.repeat(noise[:, :, None], 3, axis=2)

    def test_camera_translation_delays_cast_until_settled(self):
        terrain = self.terrain()
        guard = SceneStability()
        self.assertFalse(guard.ready(Image.fromarray(terrain), 0))
        self.assertTrue(guard.ready(Image.fromarray(terrain), .7))
        moved = cv2.warpAffine(terrain, np.float32([[1, 0, 12], [0, 1, 8]]), (320, 180))
        self.assertFalse(guard.ready(Image.fromarray(moved), .8))
        self.assertFalse(guard.ready(Image.fromarray(moved), 1.1))
        self.assertTrue(guard.ready(Image.fromarray(moved), 1.5))

    def test_animated_water_does_not_block_stationary_terrain(self):
        terrain = self.terrain()
        terrain[:, :120] = (30, 90, 180)
        changed = terrain.copy()
        changed[:, :120] = (60, 120, 220)
        guard = SceneStability()
        self.assertFalse(guard.ready(Image.fromarray(terrain), 0))
        self.assertTrue(guard.ready(Image.fromarray(changed), .7))
