"""Visual water aiming and the collect interaction prompt from the reference video."""
from pathlib import Path
import sys
import cv2
import numpy as np


def white_mask(rgb):
    return ((rgb.min(axis=2) > 185) & (rgb.max(axis=2)-rgb.min(axis=2) < 65)).astype(np.uint8)*255


class CollectPrompt:
    def __init__(self):
        base = Path(getattr(sys, '_MEIPASS', Path(__file__).resolve().parent.parent))
        template = cv2.imread(str(base/'assets'/'collect_t.png'))
        if template is None:
            raise RuntimeError('Falta la imagen de referencia del aviso T.')
        self.template = white_mask(cv2.cvtColor(template, cv2.COLOR_BGR2RGB))

    def visible(self, image):
        rgb = np.asarray(image.convert('RGB'))
        h, w = rgb.shape[:2]
        # Interaction prompts appear around the character, away from the HUD corners.
        left, top = round(w*.30), round(h*.18)
        crop = rgb[top:round(h*.80), left:round(w*.70)]
        mask = white_mask(crop)
        for factor in (.8, 1., 1.2):
            scale = h/1012*factor
            tw, th = max(12, round(22*scale)), max(12, round(23*scale))
            template = cv2.resize(self.template, (tw, th), interpolation=cv2.INTER_NEAREST)
            if th >= mask.shape[0] or tw >= mask.shape[1]:
                continue
            score = cv2.matchTemplate(mask, template, cv2.TM_CCOEFF_NORMED)
            _, maximum, _, point = cv2.minMaxLoc(score)
            if maximum < .78:
                continue
            x, y = point
            # The T must have a dark interaction label with white text to its right.
            label = crop[y:y+th, x+tw:x+tw+round(65*scale)]
            if label.size and (label.max(axis=2) < 110).mean() > .18 and (white_mask(label)>0).mean() > .025:
                return True
        return False


def find_water(image, excluded=None):
    rgb = np.asarray(image.convert('RGB'))
    h, w = rgb.shape[:2]
    small = cv2.resize(rgb, (320, 180), interpolation=cv2.INTER_AREA).astype(np.int16)
    r, g, b = small.transpose(2, 0, 1)
    water = ((b > r*1.35) & (b > g*1.08) & (g > 50) & (b > 90)).astype(np.uint8)
    # Avoid sky, HUD corners, the avatar and the fishing bar.
    water[:40] = 0
    water[117:] = 0
    water[:, :40] = 0
    water[:, 280:] = 0
    if excluded:
        x1, y1, x2, y2 = excluded
        if x2 > 0 and y2 > 0 and x1 < w and y1 < h:
            water[max(0, round(y1/h*180)):min(180, round(y2/h*180)),
                  max(0, round(x1/w*320)):min(320, round(x2/w*320))] = 0
    # A whole clear patch must be water, not just one blue pixel.
    water = cv2.erode(water, np.ones((7, 9), np.uint8))
    ys, xs = np.nonzero(water)
    if not len(xs):
        return None
    index = np.argmin((xs-160)**2 + (ys-68)**2)
    return round((xs[index]+.5)/320*w), round((ys[index]+.5)/180*h)
