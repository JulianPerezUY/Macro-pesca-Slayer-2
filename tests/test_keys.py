import sys
import unittest
from unittest.mock import patch

if sys.platform == 'win32':
    from fishing import windows


@unittest.skipUnless(sys.platform == 'win32', 'Windows input adapter')
class KeyTests(unittest.TestCase):
    def simulate(self, cancelled=False, loses_focus=False):
        class Stop:
            now = 0.0

            def is_set(self):
                return cancelled

            def wait(self, seconds):
                self.now += seconds

        stop = Stop()
        with patch.object(windows.user32, 'keybd_event') as key, \
             patch.object(windows, 'roblox_active', side_effect=lambda: not loses_focus or stop.now < .06), \
             patch('time.monotonic', side_effect=lambda: stop.now):
            windows.collect_fish(stop, 2)
            return stop.now, key.call_args_list

    def test_holds_t_for_configured_time_and_releases(self):
        elapsed, calls = self.simulate()
        self.assertAlmostEqual(elapsed, 2)
        self.assertEqual([call.args for call in calls], [(0x54, 0, 0, 0), (0x54, 0, 2, 0)])

    def test_stop_prevents_key_press(self):
        elapsed, calls = self.simulate(cancelled=True)
        self.assertEqual(elapsed, 0)
        self.assertEqual(calls, [])

    def test_focus_loss_releases_t_early(self):
        elapsed, calls = self.simulate(loses_focus=True)
        self.assertLess(elapsed, .1)
        self.assertEqual(calls[-1].args, (0x54, 0, 2, 0))
