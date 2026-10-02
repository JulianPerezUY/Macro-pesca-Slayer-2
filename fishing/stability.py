"""Wait for camera/terrain motion to settle before aiming a new cast."""
import cv2
import numpy as np


class SceneStability:
    SETTLE_SECONDS = .6

    def __init__(self):
        self.previous = None
        self.still_since = None

    def ready(self, image, now, excluded=None):
        rgb = cv2.resize(np.asarray(image.convert('RGB')), (320, 180))
        gray = cv2.cvtColor(rgb, cv2.COLOR_RGB2GRAY)
        mask = np.zeros_like(gray)
        mask[35:150, 35:285] = 255
        # Animated blue water is not evidence of character/camera movement.
        r, g, b = rgb.astype(np.int16).transpose(2, 0, 1)
        mask[(b > r*1.25) & (b > g*1.05)] = 0
        mask[65:120, 140:190] = 0  # avatar and collection banner
        if excluded:
            w, h = image.size
            x1, y1, x2, y2 = excluded
            if x2 > 0 and y2 > 0 and x1 < w and y1 < h:
                mask[max(0, round(y1/h*180)):min(180, round(y2/h*180)),
                     max(0, round(x1/w*320)):min(320, round(x2/w*320))] = 0
        moving = False
        if self.previous is not None:
            old, old_mask = self.previous
            points = cv2.goodFeaturesToTrack(old, 100, .03, 7, mask=old_mask)
            if points is not None and len(points) >= 8:
                new, status, _ = cv2.calcOpticalFlowPyrLK(old, gray, points, None)
                valid = status.ravel() > 0
                if valid.sum() >= 8:
                    shifts = (new-points)[valid, 0]
                    moving = np.linalg.norm(np.median(shifts, axis=0)) > 1.0
            else:
                valid = (mask > 0) & (old_mask > 0)
                moving = bool(valid.any() and np.median(np.abs(gray.astype(float)-old)[valid]) > 12)
        self.previous = gray, mask
        if self.still_since is None or moving:
            self.still_since = now
        return now-self.still_since >= self.SETTLE_SECONDS
