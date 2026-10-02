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
        self.maskers = (white_mask, translucent_white_mask, contrast_white_mask)
        self.references = tuple(masker(rgb) for masker in self.maskers)
        faded = cv2.imread(str(base/'assets'/'received_x1_contrast.png'), cv2.IMREAD_GRAYSCALE)
        if faded is not None:
            self.references = (*self.references[:2], faded)
        self.item_name = 'Sin identificar'
        self.confirmation = None
        self.name_image = None
        self.names = []
        for name, filename in (('Pez dorado', 'title_gold.png'),
                               ('Pez payaso', 'title_clown.png'),
                               ('Pez cebra', 'title_zebra.png'),
                               ('Hilo de seda', 'title_silk.png')):
            title = cv2.imread(str(base/'assets'/filename))
            if title is not None:
                title = cv2.cvtColor(title, cv2.COLOR_BGR2RGB)
                self.names.append((name, tuple(masker(title) for masker in self.maskers)))

    def visible(self, image):
        self.item_name = 'Sin identificar'
        self.confirmation = None
        self.name_image = None
        rgb = np.asarray(image.convert('RGB'))
        h, w = rgb.shape[:2]
        # The item award appears near the center, below the character name.
        crop = rgb[round(h*.20):round(h*.85), round(w*.25):round(w*.80)]
        masks = tuple(masker(crop) for masker in self.maskers)
        for index, mask in enumerate(masks):
            reference_mask = self.references[index]
            threshold = (.86, .70, .80)[index]
            for factor in (.8, .9, 1., 1.1, 1.3, 1.65):
                scale = h/1012*factor
                tw = max(10, round(reference_mask.shape[1]*scale))
                th = max(7, round(reference_mask.shape[0]*scale))
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
                    title = mask[max(0, y-round(32*scale)):y,
                                 max(0, x-round(65*scale)):x+tw+round(65*scale)]
                    if title.size and (title > 0).mean() > .06:
                        self.item_name = self.identify(title, index, scale)
                        self.name_image = image.crop((
                            round(w*.25)+max(0, x-round(95*scale)),
                            round(h*.20)+max(0, y-round(32*scale)),
                            round(w*.25)+x+tw+round(95*scale), round(h*.20)+y))
                        self.confirmation = 'x1'
                        return True
                    scores[max(0, y-th//2):y+th//2+1,
                           max(0, x-tw//2):x+tw//2+1] = -1
        return False

    def named_award(self, image):
        """Independent award-title recognition when the quantity cannot be read.

        Award lettering is larger than the interactive T label. Restrict this
        fallback to known full names at that HUD scale, never to a disappearing T.
        """
        rgb = np.asarray(image.convert('RGB'))
        h, w = rgb.shape[:2]
        crop = rgb[round(h*.20):round(h*.85), round(w*.25):round(w*.80)]
        best_name, best_score = None, .94
        for index in (0, 2):
            mask = self.maskers[index](crop)
            for name, references in self.names:
                reference = references[index]
                for factor in (.9, 1., 1.1):
                    scale = h/1012*factor
                    tw, th = round(reference.shape[1]*scale), round(reference.shape[0]*scale)
                    if tw < 10 or th < 7 or tw > mask.shape[1] or th > mask.shape[0]:
                        continue
                    template = cv2.resize(reference, (tw, th), interpolation=cv2.INTER_NEAREST)
                    _, score, _, _ = cv2.minMaxLoc(cv2.matchTemplate(mask, template, cv2.TM_CCOEFF_NORMED))
                    if score > best_score:
                        best_name, best_score = name, score
        if best_name is not None:
            self.item_name = best_name
            self.confirmation = 'nombre'
            return True
        return False

    def identify(self, title, index, scale):
        best_name, best_score = 'Sin identificar', .80
        for name, masks in self.names:
            reference = masks[index]
            for factor in (.8, .9, 1., 1.1, 1.25):
                tw, th = round(reference.shape[1]*scale*factor), round(reference.shape[0]*scale*factor)
                if tw < 2 or th < 2 or tw > title.shape[1] or th > title.shape[0]:
                    continue
                template = cv2.resize(reference, (tw, th), interpolation=cv2.INTER_NEAREST)
                _, score, _, _ = cv2.minMaxLoc(cv2.matchTemplate(title, template, cv2.TM_CCOEFF_NORMED))
                if score > best_score:
                    best_name, best_score = name, score
        return best_name


def translucent_white_mask(rgb):
    """Match white quantity lettering over bright, semi-transparent panels."""
    pixels = np.asarray(rgb, dtype=np.int16)
    maximum = pixels.max(axis=2)
    minimum = pixels.min(axis=2)
    spread = maximum-minimum
    white = (maximum > 165) & (minimum > 105) & (spread < 125)
    return white.astype(np.uint8)*255


def contrast_white_mask(rgb):
    """Recover faded lettering by local contrast rather than absolute brightness."""
    pixels = np.asarray(rgb, dtype=np.uint8)
    minimum = pixels.min(axis=2)
    background = cv2.morphologyEx(minimum, cv2.MORPH_OPEN, np.ones((5, 5), np.uint8))
    contrast = minimum.astype(np.int16)-background.astype(np.int16)
    spread = pixels.max(axis=2).astype(np.int16)-minimum
    return ((contrast > 22) & (spread < 95)).astype(np.uint8)*255
