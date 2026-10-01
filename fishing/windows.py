"""Windows input; release always works, including when Roblox loses focus."""
import ctypes
from ctypes import wintypes

user32 = ctypes.WinDLL('user32', use_last_error=True)
user32.GetForegroundWindow.restype = wintypes.HWND
user32.GetWindowTextW.argtypes = [wintypes.HWND, wintypes.LPWSTR, ctypes.c_int]
user32.GetAsyncKeyState.argtypes = [ctypes.c_int]
user32.GetClientRect.argtypes = [wintypes.HWND, ctypes.POINTER(wintypes.RECT)]
user32.ClientToScreen.argtypes = [wintypes.HWND, ctypes.POINTER(wintypes.POINT)]
user32.SetCursorPos.argtypes = [ctypes.c_int, ctypes.c_int]


def roblox_active():
    title = ctypes.create_unicode_buffer(512)
    user32.GetWindowTextW(user32.GetForegroundWindow(), title, 512)
    return 'roblox' in title.value.lower()


def game_rect():
    window = user32.GetForegroundWindow()
    rect, origin = wintypes.RECT(), wintypes.POINT()
    if not user32.GetClientRect(window, ctypes.byref(rect)) or not user32.ClientToScreen(window, ctypes.byref(origin)):
        raise OSError('No se pudo localizar la ventana de Roblox.')
    return origin.x, origin.y, rect.right, rect.bottom


def key_down(code):
    return bool(user32.GetAsyncKeyState(code) & 0x8000)


def tap_key(code, stop):
    user32.keybd_event(code, 0, 0, 0)
    try:
        stop.wait(.1)
    finally:
        user32.keybd_event(code, 0, 0x0002, 0)


def collect_fish(stop):
    tap_key(0x54, stop)


def unlock_cursor(stop):
    tap_key(0xA4, stop)  # left Alt


def aim_at(x, y):
    if not user32.SetCursorPos(round(x), round(y)):
        raise OSError('No se pudo apuntar al agua.')


class Mouse:
    held = False

    def hold(self, value):
        if value != self.held:
            user32.mouse_event(0x0002 if value else 0x0004, 0, 0, 0, 0)
            self.held = value
