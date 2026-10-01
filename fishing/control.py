"""Predictive cursor control with filtered velocity and a small dead band."""
class Controller:
    def __init__(self):
        self.previous = None
        self.cursor_speed = 0.0
        self.target_speed = 0.0

    def reset(self):
        self.previous = None
        self.cursor_speed = self.target_speed = 0.0

    def update(self, detection, now, held, invert=False):
        if self.previous is not None:
            previous, timestamp = self.previous
            dt = now - timestamp
            if .005 <= dt <= .25:
                cursor_speed = max(-2, min(2, (detection.cursor-previous.cursor)/dt))
                target_speed = max(-2, min(2, (detection.target-previous.target)/dt))
                self.cursor_speed = .55*self.cursor_speed + .45*cursor_speed
                self.target_speed = .55*self.target_speed + .45*target_speed
            else:
                self.cursor_speed = self.target_speed = 0.0
        self.previous = detection, now
        # Brake before crossing the center rather than after the cursor overshoots.
        half_cursor = detection.cursor_height/2
        safe_top = detection.target_top + half_cursor + .004
        safe_bottom = detection.target_bottom - half_cursor - .004
        predicted = detection.cursor + .06*self.cursor_speed
        desired = detection.target + .04*self.target_speed
        if safe_top <= safe_bottom:
            desired = max(safe_top, min(safe_bottom, desired))
        error = predicted - desired
        margin = max(.003, min(.008, (detection.target_height-detection.cursor_height)*.08))
        if abs(error) <= margin:
            return held
        return (error > 0) != invert
