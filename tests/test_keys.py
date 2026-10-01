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
