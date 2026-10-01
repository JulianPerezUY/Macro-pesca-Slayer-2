"""Detect the colored target and white cursor in a cropped fishing bar."""
from dataclasses import dataclass
import numpy as np


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
    # Measure target boundaries along both sides, outside the white square.
    r, g, b = rgb.transpose(2, 0, 1)
    yellow = (g > r * .65) & (g > b * 1.35) & (b < r * .8)
    green = (g > r * 1.4) & (g > b * 1.06)
    colored = (g > 55) & (yellow | green) & (rgb.min(axis=2) < 150)
    lanes = np.r_[np.arange(int(w*.08), max(int(w*.23), int(w*.08)+1)),
                  np.arange(int(w*.77), max(int(w*.92), int(w*.77)+1))]
    target_rows = colored[:, lanes].mean(axis=1) > .25
    inner = rgb[:, int(w*.25):max(int(w*.75), int(w*.25)+1)]
    # White becomes pale green under the translucent target, particularly near its edges.
    white = (inner.min(axis=2) > 125) & (inner.max(axis=2) > 175) & (inner.max(axis=2)-inner.min(axis=2) < 110)
    targets = [(a, z) for a, z in joined_runs(target_rows, max(1, round(h*.01))) if 8 <= z-a <= h*.45]
    cursors = [(a, z) for a, z in joined_runs(white.mean(axis=1) > .4, max(1, round(h*.018))) if 7 <= z-a <= h*.15]
    if not targets or not cursors:
        return None
    a, z = max(targets, key=lambda pair: pair[1]-pair[0])
    c, d = max(cursors, key=lambda pair: pair[1]-pair[0])
    return Detection((a+z)/2/h, (c+d)/2/h, (z-a)/h, (d-c)/h)


def automatic_region(width, height):
    """The fishing HUD is anchored at 75% of the Roblox client width."""
    return tuple(round(v * (width if i % 2 == 0 else height))
                 for i, v in enumerate((.733, .29, .766, .66)))
