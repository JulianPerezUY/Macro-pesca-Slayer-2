"""Read new item names with Windows' local OCR; no network service required."""
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import tempfile
import cv2
import numpy as np
from fishing.scene import white_mask


class ItemReader:
    def __init__(self):
        base = Path(getattr(sys, '_MEIPASS', Path(__file__).resolve().parent.parent))
        self.script = base/'assets'/'read_text.ps1'
        self.shell = Path(os.environ.get('WINDIR', 'C:/Windows'))/'System32'/'WindowsPowerShell'/'v1.0'/'powershell.exe'

    def lines(self, image):
        if sys.platform != 'win32':
            return []
        with tempfile.TemporaryDirectory(prefix='slayer2-ocr-') as directory:
            path = Path(directory)/'title.png'
            image.resize((image.width*3, image.height*3)).save(path)
            try:
                result = subprocess.run([str(self.shell), '-NoProfile', '-NonInteractive',
                                         '-ExecutionPolicy', 'Bypass', '-File', str(self.script),
                                         '-ImagePath', str(path)], capture_output=True, timeout=5,
                                        creationflags=subprocess.CREATE_NO_WINDOW)
                if result.returncode:
                    return []
                return json.loads(result.stdout.decode('utf-8-sig'))
            except (OSError, subprocess.TimeoutExpired, ValueError):
                return []

    def name(self, image):
        candidates = []
        for line in self.lines(image):
            text = ' '.join(line['text'].split()).strip(' .,:;|_-')
            if len(text) >= 3 and any(c.isalpha() for c in text) and not re.fullmatch(r'[xX×]\s*\d+', text):
                candidates.append((line['height'], text))
        return max(candidates, default=(0, None))[1]

    def award_name(self, scene):
        # Secondary recognition uses award-sized fish/material names. Small T
        # labels and player names cannot increment the collector.
        w, h = scene.size
        scale = h/1012
        left, top = round(w*.25), round(h*.20)
        crop = scene.crop((left, top, round(w*.80), round(h*.85)))
        mask = white_mask(np.asarray(crop))
        joined = cv2.morphologyEx(mask, cv2.MORPH_CLOSE,
                                 np.ones((1, max(3, round(9*scale))), np.uint8))
        candidates = []
        for contour in cv2.findContours(joined, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)[0]:
            x, y, width, height = cv2.boundingRect(contour)
            if 12*scale <= height <= 23*scale and 45*scale <= width <= 240*scale:
                candidates.append((x, y, width, height))
        # Limit OCR work to the three lines nearest the usual award position.
        candidates.sort(key=lambda box: abs(left+box[0]-w*.53)+abs(top+box[1]-h*.53))
        for x, y, width, height in candidates[:3]:
            patch = crop.crop((max(0, x-3), max(0, y-3), x+width+3, y+height+3))
            for line in self.lines(patch):
                text = ' '.join(line['text'].split()).strip(' .,:;|_-')
                if line['height'] >= 12*scale*3 and re.fullmatch(r'(?i)(?:pez\s+[\wáéíóúñ ]+|chatarra|hilo de seda)', text):
                    return text[0].upper()+text[1:].lower()
        return None
