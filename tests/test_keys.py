import sys
import unittest
from unittest.mock import patch

if sys.platform == 'win32':
    from fishing import windows


@unittest.skipUnless(sys.platform == 'win32', 'Windows input adapter')
class MouseInputTests(unittest.TestCase):
    def test_click_is_continuous_until_release(self):
        with patch.object(windows.user32, 'mouse_event') as event:
            mouse = windows.Mouse()
            for _ in range(100):
                mouse.hold(True)
            self.assertEqual(len(event.call_args_list), 1)
            self.assertTrue(mouse.held)
            mouse.hold(False)
            self.assertFalse(mouse.held)
            self.assertEqual([call.args[0] for call in event.call_args_list], [2, 4])

    def test_repeated_release_does_not_send_extra_clicks(self):
        with patch.object(windows.user32, 'mouse_event') as event:
            mouse = windows.Mouse()
            mouse.hold(True)
            mouse.hold(False)
            mouse.hold(False)
            self.assertEqual(len(event.call_args_list), 2)

    def test_release_works_without_game_focus(self):
        with patch.object(windows.user32, 'mouse_event') as event, patch.object(windows, 'roblox_active', return_value=False):
            mouse = windows.Mouse()
            mouse.held = True
            mouse.hold(False)
            self.assertEqual(event.call_args.args[0], 4)


@unittest.skipUnless(sys.platform == 'win32', 'Windows input adapter')
class KeyInputTests(unittest.TestCase):
    def test_t_uses_one_sendinput_scan_code_down_and_up(self):
        with patch.object(windows.user32, 'SendInput', return_value=1) as event:
            key = windows.Key(0x54)
            for _ in range(100):
                key.hold(True)
            self.assertEqual(event.call_count, 1)
            down = event.call_args.args[1]._obj
            self.assertEqual(down.type, 1)
            self.assertEqual(down.ki.wVk, 0)
            self.assertEqual(down.ki.wScan, 0x14)
            self.assertEqual(down.ki.dwFlags, 0x0008)
            key.hold(False)
            key.hold(False)
            self.assertFalse(key.held)
            self.assertEqual(event.call_count, 2)
            up = event.call_args.args[1]._obj
            self.assertEqual(up.ki.wScan, 0x14)
            self.assertEqual(up.ki.dwFlags, 0x000A)

    def test_t_sendinput_failure_is_reported_without_changing_held_state(self):
        with patch.object(windows.user32, 'SendInput', return_value=0):
            key = windows.Key(0x54)
            with self.assertRaises(OSError):
                key.hold(True)
            self.assertFalse(key.held)

    def test_t_release_works_without_game_focus(self):
        with patch.object(windows.user32, 'SendInput', return_value=1) as event, patch.object(windows, 'roblox_active', return_value=False):
            key = windows.Key(0x54)
            key.held = True
            key.hold(False)
            self.assertEqual(event.call_count, 1)
            self.assertEqual(event.call_args.args[1]._obj.ki.dwFlags, 0x000A)
