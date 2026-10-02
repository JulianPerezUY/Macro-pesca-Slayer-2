import unittest
from unittest.mock import patch
from PIL import Image
from fishing.ocr import ItemReader


class ItemReaderTests(unittest.TestCase):
    def test_name_ignores_quantity_and_normalizes_whitespace(self):
        reader = ItemReader()
        lines = [{'text': 'x1', 'height': 30}, {'text': '  Pez   azul__ ', 'height': 45}]
        with patch.object(reader, 'lines', return_value=lines):
            self.assertEqual(reader.name(Image.new('RGB', (200, 32))), 'Pez azul')

    def test_unavailable_ocr_keeps_unknown_item_fallback(self):
        reader = ItemReader()
        with patch.object(reader, 'lines', return_value=[]):
            self.assertIsNone(reader.name(Image.new('RGB', (200, 32))))
