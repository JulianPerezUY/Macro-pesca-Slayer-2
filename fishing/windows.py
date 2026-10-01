"""Windows input; release always works, including when Roblox loses focus."""
import ctypes
from ctypes import wintypes

user32 = ctypes.WinDLL('user32', use_last_error=True)
user32.GetForegroundWindow.restype = wintypes.HWND
user32.GetWindowTextW.argtypes = [wintypes.HWND, wintypes.LPWSTR, ctypes.c_int]
user32.GetAsyncKeyState.argtypes = [ctypes.c_int]


def roblox_active():
    title = ctypes.create_unicode_buffer(512)
    user32.GetWindowTextW(user32.GetForegroundWindow(), title, 512)
    return 'roblox' in title.value.lower()


def key_down(code):
    return bool(user32.GetAsyncKeyState(code) & 0x8000)


def collect_fish(stop):
    user32.keybd_event(0x54, 0, 0, 0)  # T
    try:
        stop.wait(.1)
    finally:
        user32.keybd_event(0x54, 0, 0x0002, 0)


class Mouse:
    held = False

    def hold(self, value):
        if value != self.held:
            user32.mouse_event(0x0002 if value else 0x0004, 0, 0, 0, 0)
            self.held = value
