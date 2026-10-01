"""Reuse a Windows capture context and copy only the requested screen region."""
from mss import MSS
from PIL import Image


class ScreenCapture:
    def __init__(self):
        self.screen = MSS()

    def grab(self, bbox):
        shot = self.screen.grab(bbox)
        return Image.frombytes('RGB', shot.size, shot.bgra, 'raw', 'BGRX')

    def close(self):
        self.screen.close()
