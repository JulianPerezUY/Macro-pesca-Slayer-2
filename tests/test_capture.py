import unittest
from types import SimpleNamespace
from unittest.mock import patch
from fishing.capture import ScreenCapture


class CaptureTests(unittest.TestCase):
    def test_region_and_bgra_pixels_are_preserved(self):
        with patch('fishing.capture.MSS') as factory:
            factory.return_value.grab.return_value = SimpleNamespace(
                size=(2, 1), bgra=bytes([10, 20, 30, 255, 40, 50, 60, 255]))
            capture = ScreenCapture()
            box = (-200, 50, -198, 51)
            image = capture.grab(box)
            factory.return_value.grab.assert_called_once_with(box)
            self.assertEqual(image.getpixel((0, 0)), (30, 20, 10))
            self.assertEqual(image.getpixel((1, 0)), (60, 50, 40))
            capture.close()
            factory.return_value.close.assert_called_once()
