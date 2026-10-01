"""Detect the colored target and white cursor in a cropped fishing bar."""
from dataclasses import dataclass
import numpy as np
import cv2


@dataclass(frozen=True)
class Detection:
    target: float
    cursor: float
    target_height: float
    cursor_height: float = .05

    @property
    def target_top(self):
        return self.target - self.target_height/2

    @property
    def target_bottom(self):
        return self.target + self.target_height/2


def runs(mask):
    edges = np.diff(np.r_[False, mask, False].astype(int))
    return list(zip(np.flatnonzero(edges == 1), np.flatnonzero(edges == -1)))


def joined_runs(mask, max_gap):
    result = []
    for a, z in runs(mask):
        if result and a-result[-1][1] <= max_gap:
            result[-1] = result[-1][0], z
        else:
            result.append((a, z))
    return result


def detect(image):
    rgb = np.asarray(image.convert('RGB'), dtype=np.int16)
    h, w = rgb.shape[:2]
    if h < 60 or w < 12:
        return None
    # The world is visible through the HUD: green scenery is not the target.
    r, g, b = rgb.transpose(2, 0, 1)
    yellow = (g > r * .65) & (g > b * 1.35) & (b < r * .8)
    green = (g > r * 1.4) & (g > b * 1.06)
    colored = (g > 55) & (yellow | green) & (rgb.min(axis=2) < 150)
    target = rectangle_bounds(colored & (g > 165))
    if target is None:
        target = rectangle_bounds(colored)
    inner = rgb[:, int(w*.25):max(int(w*.75), int(w*.25)+1)]
    # White becomes pale green under the translucent target, particularly near its edges.
    white = (inner.min(axis=2) > 125) & (inner.max(axis=2) > 175) & (inner.max(axis=2)-inner.min(axis=2) < 110)
    cursors = [(a, z) for a, z in joined_runs(white.mean(axis=1) > .4, max(1, round(h*.012))) if h*.025 <= z-a <= h*.12]
    if target is None or not cursors:
        return None
    a, z = target
    c, d = max(cursors, key=lambda pair: pair[1]-pair[0])
    return Detection((a+z)/2/h, (c+d)/2/h, (z-a)/h, (d-c)/h)


def rectangle_bounds(mask):
    """Locate a HUD-sized rectangular contour despite translucent edges."""
    h, w = mask.shape
    original = mask
    size = max(3, round(w*.045) | 1)
    mask = cv2.morphologyEx(mask.astype(np.uint8), cv2.MORPH_CLOSE, np.ones((size, size), np.uint8)).astype(bool)
    contours, _ = cv2.findContours(mask.astype(np.uint8), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    candidates = []
    for contour in contours:
        x, y, cw, ch = cv2.boundingRect(contour)
        if x == 0 and cw == w and original[y:y+ch, 0].mean() > .5:
            # Scenery extending across both crop boundaries is outside the HUD.
            continue
        if not (.7*w <= cw <= w and .035*h <= ch <= .22*h):
            continue
        patch = mask[y:y+ch, x:x+cw]
        inset = max(1, round(cw*.15))
        edge = max(2, round(w*.045))
        # Measure horizontal/vertical edge support outside rounded corners.
        top = patch[:edge, inset:-inset].any(axis=0).mean()
        bottom = patch[-edge:, inset:-inset].any(axis=0).mean()
        side_inset = max(1, round(ch*.2))
        left = patch[side_inset:-side_inset, :edge].any(axis=1).mean()
        right = patch[side_inset:-side_inset, -edge:].any(axis=1).mean()
        # Translucency can erase edges. A full horizontal edge and side still
        # bound the rectangle; do not accept irregular green scenery blobs.
        if max(top, bottom) >= .8 and max(left, right) >= .8:
            candidates.append((top+bottom+left+right, y, y+ch))
    if not candidates:
        return None
    _, top, bottom = max(candidates)
    return top, bottom


def automatic_region(width, height):
    """The fishing HUD is anchored at 75% of the Roblox client width."""
    return tuple(round(v * (width if i % 2 == 0 else height))
                 for i, v in enumerate((.733, .29, .766, .66)))
