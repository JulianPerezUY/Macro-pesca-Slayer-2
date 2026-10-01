"""Brake using relative velocity and stopping distance, not just position."""
import math


class Controller:
    def __init__(self):
        self.previous = None
        self.cursor_speed = 0.0
        self.target_speed = 0.0
        self.interval = 1/60
        self.bias = 0.0

    def reset(self):
        self.previous = None
        self.cursor_speed = self.target_speed = 0.0
        self.interval = 1/60
        self.bias = 0.0

    def update(self, detection, now, held, invert=False):
        if self.previous is not None:
            previous, timestamp = self.previous
            dt = now - timestamp
            if .001 <= dt <= .25:
                self.interval = dt
                cursor_speed = max(-2, min(2, (detection.cursor-previous.cursor)/dt))
                target_speed = max(-1, min(1, (detection.target-previous.target)/dt))
                # Time-based filtering behaves consistently at different FPS.
                cursor_weight = 1-math.exp(-dt/.015)
                target_weight = 1-math.exp(-dt/.035)
                self.cursor_speed += cursor_weight*(cursor_speed-self.cursor_speed)
                self.target_speed += target_weight*(target_speed-self.target_speed)
            else:
                self.reset()
        self.previous = detection, now
        # Keep the whole square within the target, with a pixel-scale margin.
        half_cursor = detection.cursor_height/2
        safe_top = detection.target_top + half_cursor + .004
        safe_bottom = detection.target_bottom - half_cursor - .004
        desired = detection.target
        if safe_top <= safe_bottom:
            desired = max(safe_top, min(safe_bottom, desired))
        relative_speed = self.cursor_speed-self.target_speed
        # Correct a persistent offset when raising/falling have different
        # acceleration. Do not accumulate correction during large excursions.
        if abs(detection.cursor-desired) < .08:
            self.bias = max(-.04, min(.04, self.bias + (detection.cursor-desired)*self.interval))
        # Damping reduces approach speed near the center. The look-ahead also
        # covers capture/input latency; a fixed 60 ms was too late to brake.
        reaction = .20 + min(.06, self.interval/2)
        braking_acceleration = 2.5
        stopping_distance = relative_speed*abs(relative_speed)/(2*braking_acceleration)
        error = detection.cursor-desired + relative_speed*reaction + stopping_distance + self.bias
        margin = max(.001, min(.003, (detection.target_height-detection.cursor_height)*.035))
        if abs(error) <= margin:
            return held
        return (error > 0) != invert

    def brake(self, held, invert=False):
        """Slow the square during a brief missed frame without losing velocity."""
        if abs(self.cursor_speed) < .03:
            return held
        return (self.cursor_speed > 0) != invert
