"""Recognize the quantity banner displayed when a catch is awarded."""
from pathlib import Path
import sys
import cv2
import numpy as np
from fishing.scene import white_mask


class ReceiptDetector:
    def __init__(self):
        base = Path(getattr(sys, '_MEIPASS', Path(__file__).resolve().parent.parent))
        reference = cv2.imread(str(base/'assets'/'received_x1.png'))
        if reference is None:
            raise RuntimeError('Falta la referencia del objeto recibido.')
        rgb = cv2.cvtColor(reference, cv2.COLOR_BGR2RGB)
        self.references = (white_mask(rgb), translucent_white_mask(rgb))

    def visible(self, image):
        rgb = np.asarray(image.convert('RGB'))
        h, w = rgb.shape[:2]
        # The item award appears near the center, below the character name.
        crop = rgb[round(h*.35):round(h*.72), round(w*.35):round(w*.68)]
        masks = (white_mask(crop), translucent_white_mask(crop))
        for index, mask in enumerate(masks):
            reference_mask = self.references[index]
            threshold = .86 if index == 0 else .70
            for factor in (.8, 1., 1.3, 1.65):
                scale = h/1012*factor
                tw, th = max(10, round(20*scale)), max(7, round(14*scale))
                if th >= mask.shape[0] or tw >= mask.shape[1]:
                    continue
                reference = cv2.resize(reference_mask, (tw, th), interpolation=cv2.INTER_NEAREST)
                scores = cv2.matchTemplate(mask, reference, cv2.TM_CCOEFF_NORMED)
                for _ in range(4):
                    _, score, _, point = cv2.minMaxLoc(scores)
                    if score < threshold:
                        break
                    x, y = point
                    # Quantity must sit below the larger white item name.
                    title = mask[max(0, y-round(23*scale)):y,
                                 max(0, x-round(65*scale)):x+tw+round(65*scale)]
                    if title.size and (title > 0).mean() > .06:
                        return True
                    scores[max(0, y-th//2):y+th//2+1,
                           max(0, x-tw//2):x+tw//2+1] = -1
        return False


def translucent_white_mask(rgb):
    """Match white quantity lettering over bright, semi-transparent panels."""
    pixels = np.asarray(rgb, dtype=np.int16)
    maximum = pixels.max(axis=2)
    minimum = pixels.min(axis=2)
    spread = maximum-minimum
    white = (maximum > 165) & (minimum > 105) & (spread < 125)
    return white.astype(np.uint8)*255
