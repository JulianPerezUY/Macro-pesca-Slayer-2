import unittest
import numpy as np
from PIL import Image
from fishing.vision import detect


class VisionTests(unittest.TestCase):
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


if __name__ == '__main__':
    unittest.main()
