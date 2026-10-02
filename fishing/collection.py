"""Hold T through collection, retry missed presses, and recover empty casts."""


class Collection:
    CHECK_SECONDS = 2.0
    RELEASE_SECONDS = .1
    EMPTY_SECONDS = 6.0
    MAX_HOLD_SECONDS = 12.0

    def __init__(self, now):
        self.started = now
        self.seen = False
        self.held = False
        self.loading = False
        self.pressed_at = now
        self.retry_at = now
        self.idle_since = None
        self.attempts = 0

    def pause(self, duration):
        self.started += duration
        self.held = False
        self.loading = False
        self.idle_since = None

    def update(self, now, visible, loading, received):
        if received:
            self.held = False
            return 'received'
        self.seen |= visible
        if not self.seen and now-self.started >= self.EMPTY_SECONDS:
            return 'empty'
        if not self.held:
            if (visible or self.seen) and now >= self.retry_at:
                self.held = True
                self.loading = bool(loading)
                self.pressed_at = now
                self.idle_since = None
            return 'holding' if self.held else 'waiting'
        if visible and loading:
            self.loading = True
            self.idle_since = None
        elif visible:
            if self.idle_since is None:
                self.idle_since = now
        else:
            # Disappearance during loading can precede the award banner.
            self.idle_since = None
        failed_start = not self.loading and now-self.pressed_at >= self.CHECK_SECONDS
        stalled = self.idle_since is not None and now-self.idle_since >= self.CHECK_SECONDS
        timed_out = now-self.pressed_at >= self.MAX_HOLD_SECONDS
        if failed_start or stalled or timed_out:
            self.held = False
            self.loading = False
            self.attempts += 1
            if self.attempts >= 3:
                return 'empty'
            self.retry_at = now+self.RELEASE_SECONDS
            return 'retry'
        return 'holding'
