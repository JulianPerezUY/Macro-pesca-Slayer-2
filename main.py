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
from fishing.capture import ScreenCapture
from fishing.vision import detect, automatic_region
from fishing.control import Controller
from fishing.scene import CollectPrompt, find_water, manual_target
from fishing.receipt import ReceiptDetector
from fishing.collection import Collection
from fishing.stats import SessionStats, duration
from fishing.stability import SceneStability
from fishing.ocr import ItemReader
from fishing.windows import Mouse, Key, roblox_active, key_down, game_rect, unlock_cursor, aim_at, cursor_position

ctypes.windll.user32.SetProcessDPIAware()
SETTINGS = Path(os.environ.get('LOCALAPPDATA', str(Path.home()))) / 'Slayer2Fishing' / 'settings.json'


class App:
    def __init__(self, root):
        self.root = root
        self.stop = threading.Event()
        self.stop.set()
        self.worker = None
        self.events = queue.Queue()
        self.stats = SessionStats()
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
        ttk.Label(panel, text='T mantenida hasta confirmar la recogida · Ciclo continuo', wraplength=440).pack(anchor='w', pady=6)
        self.stats_total = tk.StringVar(value='Recogidos: 0 · Tiempo activo: 00:00:00')
        ttk.Label(panel, textvariable=self.stats_total).pack(anchor='w', pady=(8, 3))
        inventory_panel = ttk.Frame(panel)
        inventory_panel.pack(fill='x')
        self.inventory = tk.Listbox(inventory_panel, height=5, bg='#111111', fg='white',
                                   highlightthickness=0, borderwidth=0,
                                   font=('Segoe UI', 10))
        inventory_scroll = ttk.Scrollbar(inventory_panel, orient='vertical', command=self.inventory.yview)
        inventory_scroll.pack(side='right', fill='y')
        self.inventory.configure(yscrollcommand=inventory_scroll.set)
        self.inventory.pack(side='left', fill='x', expand=True)
        self.inventory.insert('end', 'Todavía no hay recogidas confirmadas.')
        self.tracking = tk.Canvas(panel, height=120, bg='#111111', highlightthickness=0)
        self.tracking.pack(fill='x', pady=(8, 0))
        self.draw_tracking(None)
        self.status = tk.StringVar(value='Desactivado')
        ttk.Label(panel, textvariable=self.status, wraplength=400).pack(anchor='w', pady=12)
        root.update_idletasks()
        # Reserve two extra status lines at the current Windows display scale.
        status_space = round(float(root.tk.call('tk', 'scaling')) * 30)
        root.geometry(f'{max(510, panel.winfo_reqwidth())}x{max(680, panel.winfo_reqheight()+status_space)}+16+70')
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

    def launch(self, mouse, point, origin, cast):
        if point is None or self.stop.is_set() or not roblox_active():
            return False
        aim_at(origin[0]+point[0], origin[1]+point[1])
        if self.stop.is_set() or not roblox_active():
            return False
        try:
            mouse.hold(True)
            return not self.stop.wait(cast)
        finally:
            mouse.hold(False)

    def resolve_item(self, reader, image, stats):
        name = reader.name(image)
        if name:
            stats.rename_unknown(name)
            self.events.put(('stats', stats.snapshot()))

    def run(self, invert, cast, bite, auto_aim, manual_point):
        mouse = Mouse()
        collect_key = Key(0x54)
        controller = Controller()
        capture = None
        stats = getattr(self, 'stats', None)
        if stats is None:
            stats = self.stats = SessionStats()
        try:
            capture = ScreenCapture()
            prompt = CollectPrompt()
            receipt = ReceiptDetector()
            item_reader = ItemReader()
            self.events.put('Activando en 3 segundos: enfocá Roblox. Prepararé el lanzamiento elegido.')
            if self.stop.wait(3):
                return
            state = 'prepare'
            deadline = time.monotonic()
            missing_since = None
            last_preview = 0.0
            last_prompt_poll = 0.0
            collection = None
            stability = SceneStability()
            last_stats = 0.0
            last_name_poll = 0.0
            award_latched = False
            latch_needs_prompt = False
            while not self.stop.is_set():
                now = time.monotonic()
                active = roblox_active()
                stats.tick(now, active)
                if now-last_stats >= .25:
                    self.events.put(('stats', stats.snapshot()))
                    last_stats = now
                if not active:
                    mouse.hold(False)
                    collect_key.hold(False)
                    controller.reset()
                    missing_since = None
                    stability = SceneStability()
                    if collection is not None:
                        collection.pause(.25)
                    self.events.put('Pausado: enfocá Roblox para continuar.')
                    # Suspend timers and reset input when returning to the game.
                    self.stop.wait(.25)
                    deadline += time.monotonic() - now
                    continue
                x, y, width, height = game_rect()
                if width < 320 or height < 240:
                    stats.tick(now, False)
                    mouse.hold(False)
                    collect_key.hold(False)
                    controller.reset()
                    if collection is not None:
                        collection.pause(.1)
                    deadline += .1
                    self.stop.wait(.1)
                    continue
                left, top, right, bottom = automatic_region(width, height)
                result = None if state in ('collect', 'cooldown') else detect(capture.grab(bbox=(x+left, y+top, x+right, y+bottom)))
                if result:
                    collect_key.hold(False)
                    if state != 'play':
                        state = 'play'
                        collection = None
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
                    if missing_since is None:
                        missing_since = now
                    if now-missing_since < .12:
                        mouse.hold(controller.brake(mouse.held, invert))
                    else:
                        mouse.hold(False)
                        controller.reset()
                    if now > deadline:
                        deadline = now+120
                    if now - missing_since >= .8:
                        state = 'collect'
                        collection = Collection(now)
                        collected_before = stats.total
                        self.events.put('Esperando el cartel T para recoger con T mantenida…')
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
                    scene = capture.grab(bbox=(x, y, x+width, y+height))
                    if not stability.ready(scene, now, excluded):
                        self.events.put('Esperando que se estabilice el personaje/la cámara antes de lanzar…')
                        deadline = now+.1
                        self.stop.wait(.015)
                        continue
                    if auto_aim:
                        point = find_water(scene, excluded)
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
                    stability = SceneStability()
                    self.events.put('Caña lanzada. Esperando el minijuego…')
                elif state == 'waiting' and now >= deadline:
                    state, deadline = 'cooldown', now+2.5
                    self.events.put('No hubo pique detectado. Reintentando el lanzamiento…')
                elif state == 'collect':
                    if now-last_prompt_poll >= .1:
                        last_prompt_poll = now
                        scene = capture.grab(bbox=(x, y, x+width, y+height))
                        candidate = receipt.visible(scene) or receipt.named_award(scene)
                        if not candidate and not latch_needs_prompt:
                            award_latched = False
                        received = candidate and not award_latched
                        position = None if received else prompt.locate(scene)
                        if award_latched and latch_needs_prompt and position is not None:
                            award_latched = False
                            latch_needs_prompt = False
                        used_ocr = False
                        if not received and not award_latched and position is None and now-last_name_poll >= 1:
                            last_name_poll = now
                            name = item_reader.award_name(scene)
                            if name:
                                receipt.item_name, receipt.confirmation = name, 'nombre'
                                received = True
                                used_ocr = True
                        if not roblox_active() or self.stop.is_set():
                            collect_key.hold(False)
                            collection.pause(0)
                            continue
                        if received and stats.total == collected_before:
                            collect_key.hold(False)
                            item = receipt.item_name
                            stats.record(item if isinstance(item, str) else 'Sin identificar')
                            self.events.put(('stats', stats.snapshot()))
                        # A confirmed increment is enough, even without x1.
                        action = collection.update(time.monotonic(), position is not None,
                                                   prompt.loading, stats.total > collected_before)
                        collect_key.hold(collection.held)
                        if action == 'received':
                            award_latched = True
                            latch_needs_prompt = used_ocr
                            app_rect = self.window_bounds
                            excluded = (app_rect[0]-x, app_rect[1]-y, app_rect[2]-x, app_rect[3]-y)
                            # Reuse this frame: no cooldown, stability wait or OCR
                            # naming step may delay a confirmed catch's next cast.
                            point = find_water(scene, excluded) if auto_aim else manual_target(width, height, manual_point, excluded)
                            if self.launch(mouse, point, (x, y), cast):
                                state, deadline = 'waiting', time.monotonic()+bite
                                stability = SceneStability()
                                self.events.put('Recogida confirmada. Caña relanzada; esperando el minijuego…')
                            else:
                                state, deadline = 'cast', time.monotonic()
                            if receipt.item_name == 'Sin identificar' and receipt.name_image is not None:
                                threading.Thread(target=self.resolve_item,
                                                 args=(item_reader, receipt.name_image, stats),
                                                 daemon=True).start()
                        elif action == 'empty':
                            state, deadline = 'cast', time.monotonic()
                            self.events.put('Sin recogida confirmada tras tres intentos. Volviendo a lanzar…'
                                            if collection.attempts >= 3 else 'Caña sin aviso de recogida. Volviendo a lanzar…')
                        elif action == 'retry':
                            self.events.put('La T no carga: soltando y reintentando una pulsación sostenida…')
                        elif action == 'holding':
                            self.events.put('T mantenida: esperando una recogida registrada o x1…')
                elif state == 'cooldown' and now >= deadline:
                    collect_key.hold(False)
                    # Do not start another cycle while the previous x1 persists.
                    scene = capture.grab(bbox=(x, y, x+width, y+height))
                    if receipt.visible(scene) or receipt.named_award(scene):
                        deadline = now+.1
                    else:
                        state = 'cast'
                self.stop.wait(.002 if state == 'play' else .015)
        except Exception as exc:
            self.events.put('Error: ' + str(exc))
        finally:
            stats.tick(time.monotonic(), False)
            self.events.put(('stats', stats.snapshot()))
            collect_key.hold(False)
            mouse.hold(False)
            if capture is not None:
                capture.close()
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
        self.tracking.create_rectangle(365, 6, 400, 114, outline='#666666')
        if detection is not None:
            upper = 6 + 108*detection.target_top
            lower = 6 + 108*detection.target_bottom
            center = 6 + 108*detection.cursor
            self.tracking.create_rectangle(365, upper, 400, lower, fill='#365b28', outline='')
            half = 54*detection.cursor_height
            self.tracking.create_rectangle(375, center-half, 390, center+half, outline='white')
            for y, color in [(upper, '#ff8c32'), (lower, '#ff8c32'), (center, '#ffffff')]:
                self.tracking.create_line(355, y, 410, y, fill=color, width=2)
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
            elif isinstance(event, tuple) and event[0] == 'stats':
                seconds, items = event[1]
                self.stats_total.set(f'Recogidos: {sum(items.values())} · Tiempo activo: {duration(seconds)}')
                self.inventory.delete(0, 'end')
                for name, count in sorted(items.items()):
                    self.inventory.insert('end', f'{name}: {count}')
                if not items:
                    self.inventory.insert('end', 'Todavía no hay recogidas confirmadas.')
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
        assert ItemReader().script.is_file()
        app.events.put(('stats', (3661, {'Pez azul': 1, 'Chatarra': 20,
                                      'Pez dorado': 2, 'Pez payaso': 3,
                                      'Hilo de seda': 4, 'Pez cebra': 1})))
        app.poll()
        assert app.inventory.size() == 6
        assert app.stats_total.get() == 'Recogidos: 31 · Tiempo activo: 01:01:01'
        capture = ScreenCapture()
        try:
            assert capture.grab((0, 0, 16, 16)).size == (16, 16)
        finally:
            capture.close()
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
