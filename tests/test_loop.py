import queue
import sys
import unittest
from unittest.mock import patch, Mock

if sys.platform == 'win32':
    import main
    from fishing.vision import Detection


@unittest.skipUnless(sys.platform == 'win32', 'Windows application')
class LoopTests(unittest.TestCase):
    def simulate_three_catches(self, empty=False, long_hold=False, interrupt=None, empty_return=False, name_only=False, ocr_only=False, unknown=False, persistent=False):
        class Clock:
            now = 0.0
            stopped = False

            def is_set(self):
                return self.stopped

            def set(self):
                self.stopped = True

            def wait(self, duration):
                self.now += duration
                if self.now > 100:
                    self.stopped = True
                return self.stopped

        clock = Clock()
        game = Mock(phase='ready', catches=0, casts=0, presses=0, stamp=0.0, awarded=False, receipt_at=None)
        recast_delays = []

        class Mouse:
            held = False

            def hold(self, value):
                self.held = value
                if value and (game.phase in ('ready', 'awarded') or ((empty_return or empty) and game.phase == 'collect')):
                    if game.phase == 'awarded':
                        recast_delays.append(clock.now-game.receipt_at)
                    game.phase = 'casting'
                    game.prompt_since = None
                    game.casts += 1
                    if (empty_return or empty) and game.casts == 3:
                        clock.set()
                elif not value and game.phase == 'casting':
                    game.phase, game.stamp = 'waiting', clock.now

        class Key:
            held = False

            def hold(self, value):
                if value and not self.held:
                    assert game.aim == (960, 405)
                    game.presses += 1
                    game.phase, game.stamp = 'holding', clock.now
                if not value and self.held and game.awarded:
                    game.catches += 1
                    game.phase, game.awarded = 'awarded', False
                    if game.catches == 3:
                        clock.set()
                elif not value and self.held and empty:
                    game.phase = 'collect'
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
            if interrupt == 'error' and game.phase == 'holding':
                raise OSError('Simulated capture failure')
            if persistent and game.receipt_at is not None and clock.now-game.receipt_at < 2.6:
                return True
            if not empty and game.phase == 'holding' and clock.now-game.stamp >= (5 if long_hold else .8):
                game.awarded = True
                game.receipt_at = clock.now
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

        def active():
            if interrupt == 'focus' and key.held:
                clock.set()
                return False
            return True

        with patch.object(main, 'Mouse', return_value=Mouse()), \
             patch.object(main, 'Key', return_value=key) as key_factory, \
             patch.object(main, 'roblox_active', side_effect=active), \
             patch.object(main, 'game_rect', return_value=(0, 0, 1920, 1012)), \
             patch.object(main, 'aim_at', side_effect=aim), patch.object(main, 'unlock_cursor'), \
             patch.object(main, 'ScreenCapture'), \
             patch.object(main, 'SceneStability'), \
             patch.object(main, 'ItemReader') as reader, \
             patch.object(main.threading, 'Thread') as name_thread, \
             patch.object(main, 'detect', side_effect=detection), \
             patch.object(main, 'ReceiptDetector') as receipt, patch.object(main, 'CollectPrompt') as prompt, \
             patch.object(main.time, 'monotonic', side_effect=lambda: clock.now):
            receipt.return_value.visible.side_effect = (lambda _: False) if name_only or ocr_only else received
            receipt.return_value.named_award.side_effect = received if name_only else (lambda _: False)
            if unknown:
                receipt.return_value.item_name = 'Sin identificar'
            reader.return_value.award_name.side_effect = (lambda scene: 'Pez azul' if received(scene) else None) if ocr_only else (lambda _: None)
            def locate(_, **kwargs):
                prompt.return_value.loading = game.phase == 'holding'
                if ocr_only and game.phase == 'holding' and clock.now-game.stamp >= .8:
                    return None
                if empty_return:
                    return None
                if game.phase in ('collect', 'holding'):
                    if game.prompt_since is None:
                        game.prompt_since = clock.now
                    return (.5, .5)
                return None
            prompt.return_value.locate.side_effect = locate
            app.run(False, .3, 5, False, (.5, .4))
        key_factory.assert_called_once_with(0x54)
        self.assertEqual(game.catches, 0 if interrupt or empty_return or empty else 3)
        self.assertEqual(game.casts, 1 if interrupt else 3)
        self.assertFalse(key.held)
        self.assertTrue(clock.stopped)
        self.assertEqual(game.presses, 0 if empty_return else (1 if interrupt else (6 if empty else 3)))
        self.assertEqual(moves_while_held, [])
        self.assertEqual(sum(app.stats.items.values()), 0 if interrupt or empty_return or empty else 3)
        if ocr_only:
            self.assertEqual(app.stats.items, {'Pez azul': 3})
        if not empty and not empty_return and not interrupt:
            self.assertEqual(recast_delays, [0, 0])
        if unknown:
            reader.return_value.name.assert_not_called()
            self.assertEqual(name_thread.call_count, 3)

    def test_three_complete_catches_then_user_stop(self):
        self.simulate_three_catches()

    def test_counter_increment_recasts_even_without_x1(self):
        self.simulate_three_catches(name_only=True)

    def test_unknown_item_ocr_never_delays_recast(self):
        self.simulate_three_catches(unknown=True)

    def test_previous_banner_does_not_count_twice_after_immediate_recast(self):
        self.simulate_three_catches(persistent=True)

    def test_new_fish_name_from_ocr_recasts_without_x1(self):
        self.simulate_three_catches(ocr_only=True)

    def test_three_failed_attempts_recast_without_increasing_counter(self):
        self.simulate_three_catches(empty=True)

    def test_long_loading_keeps_one_continuous_t_press_per_catch(self):
        self.simulate_three_catches(long_hold=True)

    def test_focus_loss_releases_t(self):
        self.simulate_three_catches(interrupt='focus')

    def test_capture_error_releases_t(self):
        self.simulate_three_catches(interrupt='error')

    def test_empty_return_casts_again_without_t_or_receipt(self):
        self.simulate_three_catches(empty_return=True)
