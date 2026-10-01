import unittest
from pathlib import Path
import numpy as np
from PIL import Image
from fishing.vision import detect


class VisionTests(unittest.TestCase):
    def test_real_tinted_square_from_video(self):
        with Image.open(Path(__file__).parent/'fixtures'/'tinted_bar.png') as image:
            result = detect(image)
        self.assertIsNotNone(result)
        self.assertGreater(result.cursor_height, .05)
        self.assertLess(result.cursor_height, .08)
        self.assertLess(result.target_top, result.cursor)
        self.assertGreater(result.target_bottom, result.cursor)

    def frame(self, target=(87, 91, 32), scale=1):
        image = np.full((400*scale, 60*scale, 3), (25, 45, 65), dtype=np.uint8)
        image[:, :3*scale] = 220
        image[:, -3*scale:] = 220
        image[300*scale:340*scale, 4*scale:56*scale] = target
        image[360*scale:384*scale, 17*scale:43*scale] = 220
        return Image.fromarray(image)

    def test_yellow_target_and_cursor(self):
        result = detect(self.frame())
        self.assertIsNotNone(result)
        self.assertAlmostEqual(result.target, .8)
        self.assertAlmostEqual(result.cursor, .93)

    def test_green_and_scaled_bar(self):
        for scale in (1, 2, 3):
            result = detect(self.frame((70, 150, 30), scale))
            self.assertIsNotNone(result)
            self.assertAlmostEqual(result.target_height, .1)

    def test_scene_without_bar(self):
        self.assertIsNone(detect(Image.new('RGB', (60, 400), (50, 90, 170))))

    def test_outline_cannot_be_cursor(self):
        frame = np.array(self.frame())
        frame[360:384, 17:43] = (25, 45, 65)
        self.assertIsNone(detect(Image.fromarray(frame)))

    def test_translucent_green_and_tinted_cursor(self):
        frame = np.array(self.frame((39, 99, 79)))
        frame[360:384, 17:43] = (187, 231, 186)
        self.assertIsNotNone(detect(Image.fromarray(frame)))

    def test_cursor_overlaps_translucent_target(self):
        frame = np.array(self.frame((40, 98, 90)))
        frame[360:384, 17:43] = (25, 45, 65)
        frame[310:334, 17:43] = (187, 231, 186)
        result = detect(Image.fromarray(frame))
        self.assertIsNotNone(result)
        self.assertAlmostEqual(result.target, .8)
        self.assertAlmostEqual(result.cursor, .805)

    def test_target_outline_does_not_split_cursor(self):
        frame = np.array(self.frame())
        frame[370:373, 17:43] = (80, 140, 80)
        result = detect(Image.fromarray(frame))
        self.assertIsNotNone(result)
        self.assertAlmostEqual(result.cursor, .93)
        self.assertAlmostEqual(result.cursor_height, .06)

    def test_tinted_cursor_and_independent_target_edges(self):
        frame = np.array(self.frame((40, 98, 90)))
        frame[360:384, 17:43] = (25, 45, 65)
        frame[310:334, 17:43] = (134, 190, 134)
        result = detect(Image.fromarray(frame))
        self.assertIsNotNone(result)
        self.assertAlmostEqual(result.target_top, .75)
        self.assertAlmostEqual(result.target_bottom, .85)
        self.assertAlmostEqual(result.cursor, .805)
        self.assertAlmostEqual(result.cursor_height, .06)


if __name__ == '__main__':
    unittest.main()
