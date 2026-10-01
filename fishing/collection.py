"""Hold collection input until receipt; retry if the interaction has not started."""
class CollectionTracker:
    def __init__(self, started, retry_wait=1.5):
        self.last_attempt = started
        self.retry_wait = retry_wait
        self.loading_seen = False
        self.idle_since = None

    def update(self, received, prompt_visible, now, loading=False):
        if received:
            return 'received'
        if loading:
            self.loading_seen = True
            self.idle_since = None
            return None
        if not prompt_visible:
            self.idle_since = None
            return None
        if self.loading_seen:
            if self.idle_since is None:
                self.idle_since = now
            if now-self.idle_since < 2.5:
                return None
            self.loading_seen = False
            self.last_attempt = now
            return 'retry'
        if prompt_visible and now-self.last_attempt >= self.retry_wait:
            self.last_attempt = now
            return 'retry'
        return None
