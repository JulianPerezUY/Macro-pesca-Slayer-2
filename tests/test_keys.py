import sys
import unittest
from unittest.mock import patch

if sys.platform == 'win32':
    from fishing import windows


@unittest.skipUnless(sys.platform == 'win32', 'Windows input adapter')
class KeyTests(unittest.TestCase):
    def test_hold_is_continuous_until_explicit_release(self):
        with patch.object(windows.user32, 'keybd_event') as key, patch.object(windows, 'roblox_active', return_value=True):
            held = windows.CollectKey()
            for _ in range(100):
                held.hold(True)
            self.assertTrue(held.held)
            self.assertEqual(len(key.call_args_list), 1)
            held.hold(False)
            held.hold(False)
            self.assertFalse(held.held)
            self.assertEqual([call.args for call in key.call_args_list], [(0x54, 0, 0, 0), (0x54, 0, 2, 0)])

    def test_inactive_game_prevents_key_press(self):
        with patch.object(windows.user32, 'keybd_event') as key, patch.object(windows, 'roblox_active', return_value=False):
            held = windows.CollectKey()
            held.hold(True)
            self.assertFalse(held.held)
            key.assert_not_called()

    def test_focus_loss_releases_t(self):
        with patch.object(windows.user32, 'keybd_event') as key, patch.object(windows, 'roblox_active') as active:
            held = windows.CollectKey()
            active.return_value = True
            held.hold(True)
            active.return_value = False
            held.hold(True)
            self.assertFalse(held.held)
            self.assertEqual(key.call_args.args, (0x54, 0, 2, 0))
