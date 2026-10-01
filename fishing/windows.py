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
user32.GetCursorPos.argtypes = [ctypes.POINTER(wintypes.POINT)]


class KEYBDINPUT(ctypes.Structure):
    _fields_ = [('wVk', wintypes.WORD), ('wScan', wintypes.WORD),
                ('dwFlags', wintypes.DWORD), ('time', wintypes.DWORD),
                ('dwExtraInfo', ctypes.c_size_t)]


class MOUSEINPUT(ctypes.Structure):
    _fields_ = [('dx', wintypes.LONG), ('dy', wintypes.LONG),
                ('mouseData', wintypes.DWORD), ('dwFlags', wintypes.DWORD),
                ('time', wintypes.DWORD), ('dwExtraInfo', ctypes.c_size_t)]


class HARDWAREINPUT(ctypes.Structure):
    _fields_ = [('uMsg', wintypes.DWORD), ('wParamL', wintypes.WORD), ('wParamH', wintypes.WORD)]


class INPUTUNION(ctypes.Union):
    _fields_ = [('ki', KEYBDINPUT), ('mi', MOUSEINPUT), ('hi', HARDWAREINPUT)]


class INPUT(ctypes.Structure):
    _anonymous_ = ('data',)
    _fields_ = [('type', wintypes.DWORD), ('data', INPUTUNION)]


user32.SendInput.argtypes = [wintypes.UINT, ctypes.POINTER(INPUT), ctypes.c_int]
user32.SendInput.restype = wintypes.UINT


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


def cursor_position():
    point = wintypes.POINT()
    if not user32.GetCursorPos(ctypes.byref(point)):
        raise OSError('No se pudo leer el punto manual.')
    return point.x, point.y


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


class Key:
    SCANCODES = {0x54: 0x14}  # T physical position on a standard US keyboard.

    def __init__(self, code):
        self.code = code
        self.held = False

    def hold(self, value):
        if value != self.held:
            scan = self.SCANCODES.get(self.code)
            if scan is None:
                user32.keybd_event(self.code, 0, 0 if value else 0x0002, 0)
            else:
                flags = 0x0008 | (0 if value else 0x0002)  # SCANCODE | KEYUP
                event = INPUT(type=1, ki=KEYBDINPUT(0, scan, flags, 0, 0))
                if user32.SendInput(1, ctypes.byref(event), ctypes.sizeof(INPUT)) != 1:
                    raise ctypes.WinError(ctypes.get_last_error(), 'No se pudo enviar la tecla T con SendInput.')
            self.held = value
