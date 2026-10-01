import unittest
from pathlib import Path
from PIL import Image
from fishing.receipt import ReceiptDetector
from fishing.scene import CollectPrompt


class ReceiptTests(unittest.TestCase):
    def test_fish_loading_from_latest_video(self):
        image = Image.new('RGB', (1920, 1012), (40, 100, 190))
        with Image.open(Path(__file__).parent/'fixtures'/'fish_loading.png') as patch:
            image.paste(patch, (875, 415))
        prompt = CollectPrompt()
        point = prompt.locate(image)
        self.assertIsNotNone(point)
        self.assertTrue(prompt.loading)
        self.assertFalse(ReceiptDetector().visible(image))

    def test_fish_receipt_from_latest_video(self):
        image = Image.new('RGB', (1920, 1012), (40, 100, 190))
        with Image.open(Path(__file__).parent/'fixtures'/'fish_received.png') as patch:
            image.paste(patch, (940, 520))
        self.assertTrue(ReceiptDetector().visible(image))
    def test_item_quantity_is_receipt(self):
        image = Image.new('RGB', (1920, 1012), (40, 100, 190))
        with Image.open(Path(__file__).parent/'fixtures'/'received_item.png') as patch:
            image.paste(patch, (995, 530))
        self.assertTrue(ReceiptDetector().visible(image))

    def test_x1_on_translucent_white_panel_is_detected(self):
        image = Image.new('RGB', (1920, 1012), (40, 100, 190))
        banner = Image.open(Path(__file__).parent/'fixtures'/'fish_received.png').convert('RGB')
        x, y = 940, 520
        image.paste(banner, (x, y))
        # Reproduce the pale, translucent white treatment from the recording.
        panel = Image.new('RGB', banner.size, (100, 110, 120))
        image.paste(Image.blend(banner, panel, .5), (x, y))
        self.assertTrue(ReceiptDetector().visible(image))

    def test_t_prompt_is_not_receipt(self):
        image = Image.new('RGB', (1920, 1012), (40, 100, 190))
        with Image.open(Path(__file__).parent/'fixtures'/'collect_glow.png') as patch:
            image.paste(patch, (1045, 490))
        self.assertFalse(ReceiptDetector().visible(image))

    def test_holding_diamond_is_still_interaction(self):
        image = Image.new('RGB', (1920, 1012), (40, 100, 190))
        with Image.open(Path(__file__).parent/'fixtures'/'holding_prompt.png') as patch:
            image.paste(patch, (1045, 490))
        self.assertTrue(CollectPrompt().visible(image))
        self.assertFalse(ReceiptDetector().visible(image))

    def test_moving_large_prompt_is_recognized_without_loading(self):
        image = Image.new('RGB', (1920, 1012), (40, 100, 190))
        with Image.open(Path(__file__).parent/'fixtures'/'moving_prompt.png') as patch:
            image.paste(patch, (990, 605))
        prompt = CollectPrompt()
        self.assertTrue(prompt.visible(image))
        self.assertFalse(prompt.loading)

    def test_diamond_is_classified_as_loading(self):
        image = Image.new('RGB', (1920, 1012), (40, 100, 190))
        with Image.open(Path(__file__).parent/'fixtures'/'holding_prompt.png') as patch:
            image.paste(patch, (1045, 490))
        prompt = CollectPrompt()
        self.assertTrue(prompt.visible(image))
        self.assertTrue(prompt.loading)
