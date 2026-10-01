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
        error = detection.cursor + .10*self.cursor_speed - detection.target - .06*self.target_speed
        margin = max(.003, min(.008, (detection.target_height-detection.cursor_height)*.08))
        if abs(error) <= margin:
            return held
        return (error > 0) != invert
