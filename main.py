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
from fishing.scene import CollectPrompt, find_water, manual_target
from fishing.collection import CollectionTracker
from fishing.receipt import ReceiptDetector
from fishing.windows import Mouse, roblox_active, key_down, game_rect, unlock_cursor, aim_at, cursor_position

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
        self.auto_aim = tk.BooleanVar(value=True)
        self.manual_point = None
        self.selecting_aim = False
        self.selection_deadline = 0
        self.cast_seconds = tk.StringVar(value='0.3')
        self.bite_seconds = tk.StringVar(value='45')
        try:
            saved = json.loads(SETTINGS.read_text())
            self.invert.set(bool(saved.get('invert', False)))
            self.auto_aim.set(bool(saved.get('auto_aim', True)))
            point = saved.get('manual_point')
            if isinstance(point, list) and len(point) == 2 and all(isinstance(v, (int, float)) and 0 < v < 1 for v in point):
                self.manual_point = tuple(point)
        except (OSError, ValueError, TypeError):
            pass
        root.title('Slayer 2 · Pesca')
        root.geometry('510x680+16+70')
        root.attributes('-topmost', True)
        self.style(root)
        root.resizable(False, False)
        panel = ttk.Frame(root, padding=22)
        panel.pack(fill='both', expand=True)
        ttk.Label(panel, text='SLAYER 2 · PESCA', font=('Segoe UI', 20, 'bold')).pack(anchor='w')
        ttk.Label(panel, text='Equipá la caña cerca del agua. Ventana siempre arriba.\nF8 activa/desactiva · F9 detiene', padding=(0, 12)).pack(anchor='w')
        self.button = ttk.Button(panel, text='Activar (F8)', command=self.toggle)
        self.button.pack(fill='x', pady=6)
        aiming = ttk.Frame(panel)
        aiming.pack(fill='x', pady=6)
        self.auto_check = tk.Checkbutton(aiming, text='Apuntado automático', variable=self.auto_aim, bg='#111111', fg='white', activebackground='#111111', activeforeground='white', selectcolor='#f07820', highlightthickness=0, font=('Segoe UI', 10))
        self.auto_check.pack(side='left')
        self.manual_button = ttk.Button(aiming, text='Apuntado manual', command=self.select_manual_aim)
        self.manual_button.pack(side='right')
        self.aim_status = tk.StringVar(value='Punto manual guardado' if self.manual_point else 'Manual: elegí el punto con F6')
        ttk.Label(panel, textvariable=self.aim_status).pack(anchor='w', pady=3)
        ttk.Label(panel, text='Detección automática de la barra').pack(anchor='w', pady=8)
        tk.Checkbutton(panel, text='Invertir control (el clic baja el cuadrado)', variable=self.invert, bg='#111111', fg='white', activebackground='#111111', activeforeground='white', selectcolor='#f07820', highlightthickness=0, font=('Segoe UI', 10)).pack(anchor='w', pady=8)
        fields = ttk.Frame(panel)
        fields.pack(fill='x')
        for label, variable in [('Duración del lanzamiento (seg.)', self.cast_seconds), ('Espera máxima del pique (seg.)', self.bite_seconds)]:
            row = ttk.Frame(fields)
            row.pack(fill='x', pady=3)
            ttk.Label(row, text=label).pack(side='left')
            ttk.Entry(row, textvariable=variable, width=8).pack(side='right')
        ttk.Label(panel, text='Clic sobre T hasta confirmar la recogida · Ciclo continuo', wraplength=440).pack(anchor='w', pady=6)
        self.tracking = tk.Canvas(panel, height=86, bg='#111111', highlightthickness=0)
        self.tracking.pack(fill='x', pady=(8, 0))
        self.draw_tracking(None)
        self.status = tk.StringVar(value='Desactivado')
        ttk.Label(panel, textvariable=self.status, wraplength=400).pack(anchor='w', pady=12)
        root.protocol('WM_DELETE_WINDOW', self.close)
        self.previous_f8 = False
        self.previous_f6 = False
        self.poll()

    def save(self):
        SETTINGS.parent.mkdir(parents=True, exist_ok=True)
        SETTINGS.write_text(json.dumps({'invert': self.invert.get(), 'auto_aim': self.auto_aim.get(), 'manual_point': self.manual_point}))

    def toggle(self):
        if not self.stop.is_set():
            self.stop.set()
            return
        if self.worker and self.worker.is_alive():
            return
        try:
            cast = float(self.cast_seconds.get().replace(',', '.'))
            bite = float(self.bite_seconds.get().replace(',', '.'))
            if not self.auto_aim.get() and self.manual_point is None:
                self.status.set('Elegí primero Apuntado manual y guardá el punto con F6.')
                return
            if not .05 <= cast <= 5 or not 5 <= bite <= 180:
                raise ValueError
            self.save()
        except (ValueError, OSError) as exc:
            messagebox.showerror('Configuración', 'Rangos: lanzamiento 0,05–5; pique 5–180.. \n' + str(exc))
            return
        self.stop.clear()
        self.selecting_aim = False
        self.button.configure(text='Desactivar (F8)')
        self.auto_check.configure(state='disabled')
        self.manual_button.configure(state='disabled')
        self.worker = threading.Thread(target=self.run, args=(self.invert.get(), cast, bite, self.auto_aim.get(), self.manual_point), daemon=True)
        self.worker.start()

    def run(self, invert, cast, bite, auto_aim, manual_point):
        mouse = Mouse()
        collect_mouse = Mouse()
        last_interaction = None
        controller = Controller()
        try:
            prompt = CollectPrompt()
            receipt = ReceiptDetector()
            self.events.put('Activando en 3 segundos: enfocá Roblox. Prepararé el lanzamiento elegido.')
            if self.stop.wait(3):
                return
            state = 'prepare'
            deadline = time.monotonic()
            missing_since = None
            last_preview = 0.0
            tracker = None
            last_prompt_poll = 0.0
            while not self.stop.is_set():
                now = time.monotonic()
                if not roblox_active():
                    mouse.hold(False)
                    collect_mouse.hold(False)
                    controller.reset()
                    missing_since = None
                    if state == 'holding':
                        tracker = CollectionTracker(time.monotonic())
                    self.events.put('Pausado: enfocá Roblox para continuar.')
                    # Suspend timers and reset input when returning to the game.
                    self.stop.wait(.25)
                    deadline += time.monotonic() - now
                    continue
                x, y, width, height = game_rect()
                if width < 320 or height < 240:
                    mouse.hold(False)
                    collect_mouse.hold(False)
                    controller.reset()
                    deadline += .1
                    self.stop.wait(.1)
                    continue
                left, top, right, bottom = automatic_region(width, height)
                result = detect(ImageGrab.grab(bbox=(x+left, y+top, x+right, y+bottom)))
                if result:
                    collect_mouse.hold(False)
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
                        deadline = now+120
                        self.events.put('La pesca continúa; esperando a que termine la barra…')
                elif state == 'play':
                    mouse.hold(False)
                    controller.reset()
                    if missing_since is None:
                        missing_since = now
                    if now > deadline:
                        deadline = now+120
                    if now - missing_since >= .8:
                        state = 'collect'
                        self.events.put('Esperando el cartel T para recoger con clic mantenido…')
                elif state == 'prepare':
                    if auto_aim:
                        self.events.put('Pulsando Alt izquierdo para liberar el cursor…')
                        unlock_cursor(self.stop)
                    else:
                        self.events.put('Usando el punto manual con el cursor libre…')
                    if self.stop.wait(.25):
                        break
                    state = 'cast'
                elif state == 'cast' and now >= deadline:
                    app_rect = self.window_bounds
                    excluded = (app_rect[0]-x, app_rect[1]-y, app_rect[2]-x, app_rect[3]-y)
                    if auto_aim:
                        point = find_water(ImageGrab.grab(bbox=(x, y, x+width, y+height)), excluded)
                    else:
                        try:
                            point = manual_target(width, height, manual_point, excluded)
                        except ValueError as exc:
                            self.events.put(str(exc))
                            deadline = now+2
                            continue
                    if point is None:
                        self.events.put('Esperando agua azul despejada. Orientá la cámara hacia el agua…')
                        deadline = now+2
                        continue
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
                    state, deadline = 'cooldown', now+2.5
                    self.events.put('No hubo pique detectado. Reintentando el lanzamiento…')
                elif state in ('collect', 'holding'):
                    if now-last_prompt_poll >= .15:
                        last_prompt_poll = now
                        scene = ImageGrab.grab(bbox=(x, y, x+width, y+height))
                        received = receipt.visible(scene)
                        position = prompt.locate(scene, near=last_interaction if state == 'holding' else None)
                        visible = position is not None
                        clickable = False
                        if visible and not received:
                            bounds = self.window_bounds
                            excluded = (bounds[0]-x, bounds[1]-y, bounds[2]-x, bounds[3]-y)
                            try:
                                px, py = manual_target(width, height, position, excluded)
                                if roblox_active() and not self.stop.is_set():
                                    aim_at(x+px, y+py)
                                    last_interaction = position
                                    clickable = True
                            except ValueError:
                                collect_mouse.hold(False)
                                self.events.put('La aplicación tapa el cartel T. Movela a un lado para recoger…')
                        if state == 'holding' and clickable:
                            collect_mouse.hold(True)
                        if state == 'collect':
                            if received:
                                state, deadline = 'cooldown', time.monotonic()+2.5
                                self.events.put('Objeto recibido: detectado el aviso de cantidad. Volviendo a pescar…')
                            elif clickable:
                                if not roblox_active() or self.stop.is_set():
                                    continue
                                collect_mouse.hold(True)
                                tracker = CollectionTracker(time.monotonic())
                                state = 'holding'
                                self.events.put('Manteniendo clic sobre el cartel T hasta recibir el pez u objeto…')
                        else:
                            outcome = tracker.update(received, visible, time.monotonic(), loading=prompt.loading)
                            if outcome == 'received':
                                collect_mouse.hold(False)
                                state, deadline = 'cooldown', time.monotonic()+2.5
                                self.events.put('Objeto recibido: detectado x1. Volviendo a pescar…')
                            elif outcome == 'retry' and clickable:
                                collect_mouse.hold(False)
                                self.events.put('La carga no empezó. Volviendo a hacer clic y mantener…')
                                if self.stop.wait(.12):
                                    break
                                collect_mouse.hold(True)
                elif state == 'cooldown' and now >= deadline:
                    collect_mouse.hold(False)
                    state = 'cast'
                self.stop.wait(.015)
        except Exception as exc:
            self.events.put('Error: ' + str(exc))
        finally:
            collect_mouse.hold(False)
            mouse.hold(False)
            self.stop.set()
            self.events.put(None)

    def select_manual_aim(self):
        if self.worker and self.worker.is_alive():
            return
        self.selecting_aim = True
        self.selection_deadline = time.monotonic()+30
        self.status.set('Enfocá Roblox, apuntá al agua y pulsá F6. Alt libera el cursor; Esc cancela.')

    def capture_manual_aim(self):
        if not roblox_active():
            self.status.set('Para guardar con F6, enfocá Roblox y apuntá al agua.')
            return
        try:
            x, y, width, height = game_rect()
            px, py = cursor_position()
            point = ((px-x)/max(1, width), (py-y)/max(1, height))
            bounds = self.window_bounds
            manual_target(width, height, point, (bounds[0]-x, bounds[1]-y, bounds[2]-x, bounds[3]-y))
            self.manual_point = point
            self.auto_aim.set(False)
            self.save()
        except (OSError, ValueError) as exc:
            self.status.set(str(exc))
            return
        self.selecting_aim = False
        self.aim_status.set(f'Punto manual: {point[0]*100:.1f}% × {point[1]*100:.1f}%')
        self.status.set('Punto guardado. Se usará en cada lanzamiento; podés activar con F8.')

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
        f6 = key_down(0x75)
        if self.selecting_aim:
            if key_down(0x1B) or time.monotonic() >= self.selection_deadline:
                self.selecting_aim = False
                self.status.set('Selección manual cancelada.')
            elif f6 and not self.previous_f6:
                self.capture_manual_aim()
        self.previous_f6 = f6
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
                self.auto_check.configure(state='normal')
                self.manual_button.configure(state='normal')
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
        CollectPrompt()
        ReceiptDetector()
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
