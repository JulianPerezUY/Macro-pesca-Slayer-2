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
        self.reference = white_mask(cv2.cvtColor(reference, cv2.COLOR_BGR2RGB))

    def visible(self, image):
        rgb = np.asarray(image.convert('RGB'))
        h, w = rgb.shape[:2]
        crop = rgb[round(h*.25):round(h*.78), round(w*.3):round(w*.7)]
        mask = white_mask(crop)
        for factor in (.8, .9, 1., 1.1, 1.2):
            scale = h/1012*factor
            tw, th = max(10, round(20*scale)), max(7, round(14*scale))
            if th >= mask.shape[0] or tw >= mask.shape[1]:
                continue
            reference = cv2.resize(self.reference, (tw, th), interpolation=cv2.INTER_NEAREST)
            scores = cv2.matchTemplate(mask, reference, cv2.TM_CCOEFF_NORMED)
            for _ in range(4):
                _, score, _, point = cv2.minMaxLoc(scores)
                if score < .86:
                    break
                x, y = point
                # Quantity must sit below the larger white item name.
                title = mask[max(0, y-round(23*scale)):y, max(0,x-round(65*scale)):x+tw+round(65*scale)]
                if title.size and (title>0).mean() > .06:
                    return True
                scores[max(0,y-th//2):y+th//2+1, max(0,x-tw//2):x+tw//2+1] = -1
        return False
