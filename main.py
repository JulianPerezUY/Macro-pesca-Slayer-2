"""Slayer 2 fishing macro. Run on Windows with the rod already equipped."""
import ctypes
import json
import os
from pathlib import Path
import queue
import sys
import threading
import time
import tkinter as tk
from tkinter import ttk, messagebox
from PIL import ImageGrab
from fishing.vision import detect, automatic_region
from fishing.control import Controller
from fishing.scene import CollectPrompt, find_water
from fishing.windows import Mouse, roblox_active, key_down, collect_fish, game_rect, unlock_cursor, aim_at

ctypes.windll.user32.SetProcessDPIAware()
SETTINGS = Path(os.environ.get('LOCALAPPDATA', str(Path.home()))) / 'Slayer2Fishing' / 'settings.json'


class App:
    def __init__(self, root):
        self.root = root
        self.stop = threading.Event()
        self.stop.set()
        self.worker = None
        self.events = queue.Queue()
        self.invert = tk.BooleanVar(value=False)
        self.cast_seconds = tk.StringVar(value='0.3')
        self.bite_seconds = tk.StringVar(value='45')
        try:
            saved = json.loads(SETTINGS.read_text())
            self.invert.set(bool(saved.get('invert', False)))
        except (OSError, ValueError, TypeError):
            pass
        root.title('Slayer 2 · Pesca')
        root.geometry('490x570+16+70')
        root.attributes('-topmost', True)
        self.style(root)
        root.resizable(False, False)
        panel = ttk.Frame(root, padding=22)
        panel.pack(fill='both', expand=True)
        ttk.Label(panel, text='SLAYER 2 · PESCA', font=('Segoe UI', 20, 'bold')).pack(anchor='w')
        ttk.Label(panel, text='Equipá la caña cerca del agua. Ventana siempre arriba.\nF8 activa/desactiva · F9 detiene', padding=(0, 12)).pack(anchor='w')
        self.button = ttk.Button(panel, text='Activar (F8)', command=self.toggle)
        self.button.pack(fill='x', pady=6)
        ttk.Label(panel, text='Detección automática de la barra').pack(anchor='w', pady=8)
        tk.Checkbutton(panel, text='Invertir control (el clic baja el cuadrado)', variable=self.invert, bg='#111111', fg='white', activebackground='#111111', activeforeground='white', selectcolor='#f07820', highlightthickness=0, font=('Segoe UI', 10)).pack(anchor='w', pady=8)
        fields = ttk.Frame(panel)
        fields.pack(fill='x')
        for label, variable in [('Duración del lanzamiento (seg.)', self.cast_seconds), ('Espera máxima del pique (seg.)', self.bite_seconds)]:
            row = ttk.Frame(fields)
            row.pack(fill='x', pady=3)
            ttk.Label(row, text=label).pack(side='left')
            ttk.Entry(row, textvariable=variable, width=8).pack(side='right')
        self.tracking = tk.Canvas(panel, height=86, bg='#111111', highlightthickness=0)
        self.tracking.pack(fill='x', pady=(8, 0))
        self.draw_tracking(None)
        self.status = tk.StringVar(value='Desactivado')
        ttk.Label(panel, textvariable=self.status, wraplength=400).pack(anchor='w', pady=12)
        root.protocol('WM_DELETE_WINDOW', self.close)
        self.previous_f8 = False
        self.poll()

    def save(self):
        SETTINGS.parent.mkdir(parents=True, exist_ok=True)
        SETTINGS.write_text(json.dumps({'invert': self.invert.get()}))

    def toggle(self):
        if not self.stop.is_set():
            self.stop.set()
            return
        if self.worker and self.worker.is_alive():
            return
        try:
            cast = float(self.cast_seconds.get().replace(',', '.'))
            bite = float(self.bite_seconds.get().replace(',', '.'))
            if not .05 <= cast <= 5 or not 5 <= bite <= 180:
                raise ValueError
            self.save()
        except (ValueError, OSError) as exc:
            messagebox.showerror('Configuración', 'Usá un lanzamiento entre 0,05 y 5 segundos y una espera entre 5 y 180.\n' + str(exc))
            return
        self.stop.clear()
        self.button.configure(text='Desactivar (F8)')
        self.worker = threading.Thread(target=self.run, args=(self.invert.get(), cast, bite, (self.root.winfo_rootx(), self.root.winfo_rooty(), self.root.winfo_rootx()+self.root.winfo_width(), self.root.winfo_rooty()+self.root.winfo_height())), daemon=True)
        self.worker.start()

    def run(self, invert, cast, bite, app_rect):
        mouse = Mouse()
        controller = Controller()
        try:
            prompt = CollectPrompt()
            self.events.put('Activando en 3 segundos: enfocá Roblox. Prepararé Alt izquierdo y buscaré agua.')
            if self.stop.wait(3):
                return
            state = 'prepare'
            deadline = time.monotonic()
            missing_since = None
            last_preview = 0.0
            prompt_hits = 0
            attempts = 0
            last_prompt_poll = 0.0
            while not self.stop.is_set():
                now = time.monotonic()
                if not roblox_active():
                    mouse.hold(False)
                    controller.reset()
                    missing_since = None
                    self.events.put('Pausado: enfocá Roblox para continuar.')
                    # Suspend timers and reset input when returning to the game.
                    self.stop.wait(.25)
                    deadline += time.monotonic() - now
                    continue
                x, y, width, height = game_rect()
                if width < 320 or height < 240:
                    mouse.hold(False)
                    controller.reset()
                    deadline += .1
                    self.stop.wait(.1)
                    continue
                left, top, right, bottom = automatic_region(width, height)
                result = detect(ImageGrab.grab(bbox=(x+left, y+top, x+right, y+bottom)))
                if result:
                    if state != 'play':
                        state = 'play'
                        deadline = now + 120
                        self.events.put('Pescando: siguiendo la zona verde/amarilla.')
                    missing_since = None
                    mouse.hold(controller.update(result, time.monotonic(), mouse.held, invert))
                    if now-last_preview >= .1:
                        self.events.put(result)
                        last_preview = now
                    if now > deadline:
                        raise RuntimeError('La barra lleva 120 segundos visible. Revisá el sentido del control.')
                elif state == 'play':
                    mouse.hold(False)
                    controller.reset()
                    if missing_since is None:
                        missing_since = now
                    if now > deadline:
                        raise RuntimeError('La pesca superó 120 segundos. Revisá el sentido del control.')
                    if now - missing_since >= .8:
                        state, deadline = 'collect', now + 25
                        prompt_hits = attempts = 0
                        self.events.put('Esperando que el pescado se acerque y aparezca T…')
                elif state == 'prepare':
                    self.events.put('Pulsando Alt izquierdo para liberar el cursor…')
                    unlock_cursor(self.stop)
                    if self.stop.wait(.25):
                        break
                    state = 'cast'
                elif state == 'cast' and now >= deadline:
                    scene = ImageGrab.grab(bbox=(x, y, x+width, y+height))
                    app_rect = self.window_bounds
                    excluded = (app_rect[0]-x, app_rect[1]-y, app_rect[2]-x, app_rect[3]-y)
                    point = find_water(scene, excluded)
                    if point is None:
                        raise RuntimeError('No encuentro agua azul despejada. Orientá la cámara hacia el agua y activá de nuevo.')
                    aim_at(x+point[0], y+point[1])
                    if self.stop.wait(.15) or not roblox_active():
                        continue
                    mouse.hold(True)
                    if self.stop.wait(cast):
                        break
                    mouse.hold(False)
                    state, deadline = 'waiting', time.monotonic() + bite
                    self.events.put('Caña lanzada. Esperando el minijuego…')
                elif state == 'waiting' and now >= deadline:
                    raise RuntimeError('No apareció la barra. Dejá visible toda la ventana de Roblox y revisá la caña y el lanzamiento.')
                elif state in ('collect', 'verify'):
                    if now >= deadline:
                        raise RuntimeError('No pude confirmar la recogida. Revisá si el pescado está cerca y aparece T.')
                    if now-last_prompt_poll >= .15:
                        last_prompt_poll = now
                        visible = prompt.visible(ImageGrab.grab(bbox=(x, y, x+width, y+height)))
                        if state == 'collect':
                            prompt_hits = prompt_hits+1 if visible else 0
                            if prompt_hits >= 2:
                                if not roblox_active() or self.stop.is_set():
                                    continue
                                collect_fish(self.stop)
                                attempts += 1
                                state, deadline = 'verify', time.monotonic()+5
                                prompt_hits = 0
                                self.events.put('T detectada y pulsada. Confirmando recogida…')
                        elif not visible:
                            prompt_hits += 1
                            if prompt_hits >= 3:
                                state, deadline = 'cooldown', time.monotonic()+2.5
                                self.events.put('El aviso desapareció. Preparando otro lanzamiento…')
                        else:
                            prompt_hits = 0
                            if now >= deadline-3 and attempts < 3:
                                collect_fish(self.stop)
                                attempts += 1
                                deadline = time.monotonic()+5
                elif state == 'cooldown' and now >= deadline:
                    state = 'cast'
                self.stop.wait(.015)
        except Exception as exc:
            self.events.put('Error: ' + str(exc))
        finally:
            mouse.hold(False)
            self.stop.set()
            self.events.put(None)

    def draw_tracking(self, detection):
        self.tracking.delete('all')
        values = [('Superior', None if detection is None else detection.target_top, '#ff8c32'),
                  ('Inferior', None if detection is None else detection.target_bottom, '#ff8c32'),
                  ('Centro del cuadrado', None if detection is None else detection.cursor, '#ffffff')]
        for index, (label, value, color) in enumerate(values):
            y = 15+index*25
            self.tracking.create_line(8, y, 65, y, fill=color, width=2)
            number = '—' if value is None else f'{value*100:.1f}%'
            self.tracking.create_text(80, y, anchor='w', fill='white', text=f'{label}: {number}', font=('Segoe UI', 10))

    def style(self, root):
        root.configure(bg='#111111')
        style = ttk.Style(root)
        style.theme_use('clam')
        style.configure('.', background='#111111', foreground='#ffffff', font=('Segoe UI', 10))
        style.configure('TFrame', background='#111111')
        style.configure('TLabel', background='#111111', foreground='#ffffff')
        style.configure('TButton', background='#e66e19', foreground='#ffffff', bordercolor='#ff8c32', lightcolor='#e66e19', darkcolor='#e66e19', padding=12, font=('Segoe UI', 11, 'bold'))
        style.map('TButton', background=[('pressed', '#ab4909'), ('active', '#fa8834')], foreground=[('disabled', '#aaaaaa')])
        style.configure('TEntry', fieldbackground='#202020', foreground='#ffffff', bordercolor='#f07820', insertcolor='#ffffff', lightcolor='#f07820', darkcolor='#f07820', padding=4)
        style.map('TEntry', bordercolor=[('focus', '#ff9b4b')], lightcolor=[('focus', '#ff9b4b')], darkcolor=[('focus', '#ff9b4b')])

    def poll(self):
        self.window_bounds = (self.root.winfo_rootx(), self.root.winfo_rooty(),
                              self.root.winfo_rootx()+self.root.winfo_width(),
                              self.root.winfo_rooty()+self.root.winfo_height())
        pressed = key_down(0x77)
        if pressed and not self.previous_f8:
            self.toggle()
        self.previous_f8 = pressed
        if key_down(0x78):
            self.stop.set()
        while not self.events.empty():
            event = self.events.get_nowait()
            if event is None:
                self.button.configure(text='Activar (F8)')
                self.draw_tracking(None)
                if not self.status.get().startswith('Error:'):
                    self.status.set('Desactivado')
            elif hasattr(event, 'target_top'):
                self.draw_tracking(event)
            else:
                self.status.set(event)
        self.root.after(60, self.poll)

    def close(self):
        self.stop.set()
        if self.worker and self.worker.is_alive():
            self.root.after(50, self.close)
        else:
            self.root.destroy()


if __name__ == '__main__':
    root = tk.Tk()
    app = App(root)
    if '--smoke-test' in sys.argv:
        app.status.set('Error: No apareció la barra. Dejá visible toda la ventana de Roblox y revisá la caña y el lanzamiento.')
        root.update()
        panel = root.winfo_children()[0]
        assert panel.winfo_reqwidth() <= root.winfo_width()
        assert panel.winfo_reqheight() <= root.winfo_height()
        assert ttk.Style(root).lookup('TButton', 'background') == '#e66e19'
        assert root.attributes('-topmost')
        root.destroy()
    else:
        root.mainloop()
