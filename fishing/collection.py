"""Hold collection input until receipt; retry if the interaction has not started."""
class CollectionTracker:
    def __init__(self, started, retry_wait=1.5):
        self.last_attempt = started
        self.retry_wait = retry_wait

    def update(self, received, prompt_visible, now, loading=False):
        if received:
            return 'received'
        if loading:
            self.last_attempt = now
        elif prompt_visible and now-self.last_attempt >= self.retry_wait:
            self.last_attempt = now
            return 'retry'
        return None
