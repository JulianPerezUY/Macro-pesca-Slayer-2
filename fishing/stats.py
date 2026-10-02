"""Session totals: only confirmed awards count; pauses do not add active time."""
from collections import Counter
from threading import RLock


class SessionStats:
    def __init__(self):
        self.items = Counter()
        self.lock = RLock()
        self.seconds = 0.0
        self.last = None
        self.active = False

    def tick(self, now, active):
        if self.last is not None and self.active:
            self.seconds += max(0, now-self.last)
        self.last, self.active = now, active

    def record(self, item, quantity=1):
        with self.lock:
            self.items[item] += quantity

    def rename_unknown(self, item):
        with self.lock:
            if self.items['Sin identificar']:
                self.items['Sin identificar'] -= 1
                if not self.items['Sin identificar']:
                    del self.items['Sin identificar']
                self.items[item] += 1

    @property
    def total(self):
        with self.lock:
            return sum(self.items.values())

    def snapshot(self):
        with self.lock:
            return self.seconds, dict(self.items)


def duration(seconds):
    hours, remainder = divmod(int(seconds), 3600)
    minutes, seconds = divmod(remainder, 60)
    return f'{hours:02d}:{minutes:02d}:{seconds:02d}'
