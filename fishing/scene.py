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
        self.templates = []
        self.loading = False
        for name in ('collect_t.png', 'collect_t_glow.png', 'collect_t_holding.png', 'collect_t_large.png', 'collect_t_fish_holding.png'):
            template = cv2.imread(str(base/'assets'/name))
            if template is None:
                raise RuntimeError('Falta la imagen de referencia del aviso T.')
            self.templates.append((name, white_mask(cv2.cvtColor(template, cv2.COLOR_BGR2RGB))))

    def visible(self, image):
        return self.locate(image) is not None

    def locate(self, image, near=None):
        rgb = np.asarray(image.convert('RGB'))
        h, w = rgb.shape[:2]
        left, top = round(w*.30), round(h*.18)
        right, bottom = round(w*.70), round(h*.80)
        if near is not None:
            left, top = max(0, round((near[0]-.05)*w)), max(0, round((near[1]-.045)*h))
            right, bottom = min(w, round((near[0]+.10)*w)), min(h, round((near[1]+.045)*h))
        crop = rgb[top:bottom, left:right]
        mask = white_mask(crop)
        best = None
        self.loading = False
        best_score = .68 if near is not None else .78
        for name, reference in self.templates:
            for factor in (.8, .9, 1., 1.1, 1.2, 1.4):
                scale = h/1012*factor
                tw, th = max(12, round(reference.shape[1]*scale)), max(12, round(reference.shape[0]*scale))
                if th >= mask.shape[0] or tw >= mask.shape[1]:
                    continue
                template = cv2.resize(reference, (tw, th), interpolation=cv2.INTER_NEAREST)
                scores = cv2.matchTemplate(mask, template, cv2.TM_CCOEFF_NORMED)
                for _ in range(4):
                    _, maximum, _, point = cv2.minMaxLoc(scores)
                    if maximum < best_score:
                        break
                    x, y = point
                    label = crop[y:y+th, x+tw:x+tw+round(65*scale)]
                    if label.size and (label.max(axis=2) < 110).mean() > .18 and (white_mask(label)>0).mean() > .025:
                        best = ((left+x+tw/2)/w, (top+y+th/2)/h)
                        best_score = maximum
                        self.loading = 'holding' in name
                        break
                    scores[max(0,y-th//2):y+th//2+1, max(0,x-tw//2):x+tw//2+1] = -1
        return best


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


def manual_target(width, height, point, excluded=None):
    if point is None or len(point) != 2 or not all(0 < v < 1 for v in point):
        raise ValueError('Elegí primero un punto de apuntado manual con F6.')
    x, y = round(point[0]*width), round(point[1]*height)
    if excluded and excluded[0] <= x <= excluded[2] and excluded[1] <= y <= excluded[3]:
        raise ValueError('La aplicación está tapando el punto manual. Movela a un lado.')
    return x, y
