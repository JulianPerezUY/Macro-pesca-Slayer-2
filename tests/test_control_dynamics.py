"""Closed-loop checks with inertia, input delay and pixel-quantized vision.

These are model tests, not a claim about the game's exact physics.
"""
from collections import deque
import math
import unittest
from fishing.control import Controller
from fishing.vision import Detection


def simulate(interval, up, down, moving):
    control = Controller()
    x, velocity, held, applied = .5, 0.0, False, False
    samples, commands = deque(), deque()
    next_frame = 0.0
    errors = []
    for tick in range(7500):
        now = tick*.002
        target = .5 + (.15*math.sin(now*1.5) if moving else 0)
        samples.append((now, x, target))
        while len(samples) > 1 and samples[1][0] <= now-.02:
            samples.popleft()
        if now+1e-9 >= next_frame:
            _, cursor, goal = samples[0]
            detection = Detection(round(goal*400)/400, round(cursor*400)/400, .1, .06)
            held = control.update(detection, now, held)
            commands.append((now+.02, held))
            next_frame += interval
        while commands and commands[0][0] <= now:
            applied = commands.popleft()[1]
        velocity += (-up if applied else down)*.002
        x += velocity*.002
        if now > 1:
            errors.append(abs(x-target))
    return sum(errors)/len(errors), sum(e <= .02 for e in errors)/len(errors)


class DynamicsTests(unittest.TestCase):
    def test_stationary_target_does_not_develop_large_oscillations(self):
        error, inside = simulate(.02, 3, 3, False)
        self.assertLess(error, .012)
        self.assertGreater(inside, .9)

    def test_tracks_moving_rectangle_with_inertia_and_unequal_acceleration(self):
        for interval in (1/60, 1/30):
            for up, down in ((3, 3), (2, 3), (4, 2)):
                with self.subTest(interval=interval, up=up, down=down):
                    error, inside = simulate(interval, up, down, True)
                    self.assertLess(error, .02)
                    self.assertGreater(inside, .65)
