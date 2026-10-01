import unittest
from pathlib import Path
from PIL import Image
from fishing.receipt import ReceiptDetector
from fishing.scene import CollectPrompt


class ReceiptTests(unittest.TestCase):
    def test_item_quantity_is_receipt(self):
        image = Image.new('RGB', (1920, 1012), (40, 100, 190))
        with Image.open(Path(__file__).parent/'fixtures'/'received_item.png') as patch:
            image.paste(patch, (995, 530))
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
