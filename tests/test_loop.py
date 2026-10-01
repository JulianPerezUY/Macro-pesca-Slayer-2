import queue
import sys
import unittest
from unittest.mock import patch, Mock

if sys.platform == 'win32':
    import main
    from fishing.vision import Detection


@unittest.skipUnless(sys.platform == 'win32', 'Windows application')
class LoopTests(unittest.TestCase):
    def simulate_three_catches(self, empty=False, long_hold=False):
        class Clock:
            now = 0.0
            stopped = False

            def is_set(self):
                return self.stopped

            def set(self):
                self.stopped = True

            def wait(self, duration):
                self.now += duration
                if self.now > 80:
                    self.stopped = True
                return self.stopped

        clock = Clock()
        game = Mock(phase='ready', catches=0, casts=0, presses=0, stamp=0.0, awarded=False)

        class Mouse:
            held = False

            def hold(self, value):
                self.held = value
                if value and game.phase in ('ready', 'awarded'):
                    game.phase = 'casting'
                    game.casts += 1
                elif not value and game.phase == 'casting':
                    game.phase, game.stamp = 'waiting', clock.now

        class Key:
            held = False

            def hold(self, value):
                if value and not self.held:
                    assert game.aim == (960, 506)
                    game.presses += 1
                    game.phase, game.stamp = 'holding', clock.now
                if not value and self.held and (game.awarded or empty):
                    game.catches += 1
                    game.phase, game.awarded = 'awarded', False
                    if game.catches == 3:
                        clock.set()
                self.held = value

        def detection(_):
            if game.phase in ('waiting', 'play'):
                elapsed = clock.now-game.stamp
                if .2 <= elapsed <= 1.2:
                    game.phase = 'play'
                    return Detection(.5, .5, .1)
                if elapsed > 1.2:
                    game.phase = 'collect'
            return None

        def received(_):
            if not empty and game.phase == 'holding' and clock.now-game.stamp >= (5 if long_hold else .8):
                game.awarded = True
                return True
            return False

        app = main.App.__new__(main.App)
        app.stop, app.events = clock, queue.Queue()
        app.window_bounds = (0, 0, 400, 400)
        key = Key()
        moves_while_held = []

        def aim(x, y):
            if key.held:
                moves_while_held.append((x, y))
            game.aim = (x, y)
        with patch.object(main, 'Mouse', side_effect=[Mouse(), key]), \
             patch.object(main, 'roblox_active', return_value=True), \
             patch.object(main, 'game_rect', return_value=(0, 0, 1920, 1012)), \
             patch.object(main, 'aim_at', side_effect=aim), patch.object(main, 'unlock_cursor'), \
             patch.object(main.ImageGrab, 'grab', return_value=object()), \
             patch.object(main, 'detect', side_effect=detection), \
             patch.object(main, 'ReceiptDetector') as receipt, patch.object(main, 'CollectPrompt') as prompt, \
             patch.object(main.time, 'monotonic', side_effect=lambda: clock.now):
            receipt.return_value.visible.side_effect = received
            prompt.return_value.locate.side_effect = lambda _, **kwargs: (.5, .5) if game.phase == 'collect' or (game.phase == 'holding' and (not empty or clock.now-game.stamp < .5)) else None
            app.run(False, .3, 5, False, (.5, .4))
        self.assertEqual(game.catches, 1 if empty else 3)
        self.assertEqual(game.casts, 1 if empty else 3)
        self.assertFalse(key.held)
        self.assertTrue(clock.stopped)
        self.assertEqual(game.presses, 1 if empty else 3)
        self.assertEqual(moves_while_held, [])

    def test_three_complete_catches_then_user_stop(self):
        self.simulate_three_catches()

    def test_missing_receipt_never_recasts(self):
        self.simulate_three_catches(empty=True)

    def test_long_loading_keeps_one_fixed_click_per_catch(self):
        self.simulate_three_catches(long_hold=True)
