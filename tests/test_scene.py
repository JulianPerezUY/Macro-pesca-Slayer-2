import unittest
from pathlib import Path
from PIL import Image, ImageDraw
from fishing.scene import CollectPrompt, find_water


class SceneTests(unittest.TestCase):
    def test_water_aim_avoids_overlay_and_land(self):
        im = Image.new('RGB', (1920, 1012), (60, 45, 30))
        ImageDraw.Draw(im).rectangle((600, 250, 1400, 550), fill=(40, 100, 190))
        point = find_water(im, (850, 250, 1100, 550))
        self.assertIsNotNone(point)
        x, y = point
        self.assertTrue(600 <= x <= 1400 and 250 <= y <= 550)
        self.assertFalse(850 <= x <= 1100)

    def test_no_blue_water_does_not_guess(self):
        self.assertIsNone(find_water(Image.new('RGB', (1920, 1012), (60, 45, 30))))

    def test_overlay_outside_game_does_not_mask_water(self):
        image = Image.new('RGB', (1920, 1012), (40, 100, 190))
        self.assertEqual(find_water(image), find_water(image, (-600, -300, -100, -20)))

    def prompt_image(self, label=True):
        im = Image.new('RGB', (1920, 1012), (40, 100, 190))
        template = Image.open(Path(__file__).resolve().parent.parent/'assets'/'collect_t.png')
        im.paste(template, (950, 430))
        if label:
            d = ImageDraw.Draw(im)
            d.rectangle((973, 430, 1037, 453), fill=(25, 30, 35))
            d.text((977, 432), 'Fish\nTake', fill='white')
        return im

    def test_t_requires_interaction_label(self):
        detector = CollectPrompt()
        self.assertTrue(detector.visible(self.prompt_image()))
        self.assertFalse(detector.visible(self.prompt_image(False)))

    def test_no_prompt_does_not_collect(self):
        self.assertFalse(CollectPrompt().visible(Image.new('RGB', (1920, 1012), (40, 100, 190))))

    def test_real_glowing_prompt_is_located(self):
        im = Image.new('RGB', (1920, 1012), (40, 100, 190))
        with Image.open(Path(__file__).parent/'fixtures'/'collect_glow.png') as patch:
            im.paste(patch, (1045, 490))
        point = CollectPrompt().locate(im)
        self.assertIsNotNone(point)
        self.assertAlmostEqual(point[0], 1081/1920, delta=.01)
        self.assertAlmostEqual(point[1], 527/1012, delta=.01)
