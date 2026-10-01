"""Wait for the reel to finish moving before using its interaction prompt."""
class ReelGate:
    def __init__(self, started, delay=4.0, settle=1.0):
        self.started = started
        self.delay = delay
        self.settle = settle
        self.anchor = None
        self.stable_since = None
        self.last_seen = started

    def update(self, position, now):
        if position is None:
            if now-self.last_seen > .4:
                self.anchor = self.stable_since = None
            return False
        self.last_seen = now
        if self.anchor is None or max(abs(a-b) for a, b in zip(self.anchor, position)) > .012:
            self.anchor = position
            self.stable_since = now
        return now-self.started >= self.delay and now-self.stable_since >= self.settle


class CollectionTracker:
    """A vanished T alone cannot finish collection: it also vanishes while holding."""
    def __init__(self, started, empty_wait=6.0):
        self.started = started
        self.last_prompt = started
        self.empty_wait = empty_wait

    def update(self, received, prompt_visible, now):
        if received:
            return 'received'
        if prompt_visible:
            self.last_prompt = now
        if now-self.last_prompt >= self.empty_wait:
            return 'empty'
        return None
