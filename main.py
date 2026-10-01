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
from PIL import ImageGrab, ImageTk
from fishing.vision import detect
from fishing.windows import Mouse, roblox_active, key_down, collect_fish

ctypes.windll.user32.SetProcessDPIAware()
SETTINGS = Path(os.environ.get('LOCALAPPDATA', str(Path.home()))) / 'Slayer2Fishing' / 'settings.json'


class App:
    def __init__(self, root):
        self.root = root
        self.stop = threading.Event()
        self.stop.set()
        self.worker = None
        self.events = queue.Queue()
        self.region = [.733, .29, .766, .66]
        self.invert = tk.BooleanVar(value=False)
        self.cast_seconds = tk.StringVar(value='0.3')
        self.bite_seconds = tk.StringVar(value='45')
        try:
            saved = json.loads(SETTINGS.read_text())
            region = saved.get('region', self.region)
            if len(region) == 4 and all(0 <= v <= 1 for v in region) and region[0] < region[2] and region[1] < region[3]:
                self.region = region
            self.invert.set(bool(saved.get('invert', False)))
        except (OSError, ValueError, TypeError):
            pass
        root.title('Slayer 2 · Pesca')
        root.geometry('450x390')
        root.resizable(False, False)
        panel = ttk.Frame(root, padding=22)
        panel.pack(fill='both', expand=True)
        ttk.Label(panel, text='SLAYER 2 · PESCA', font=('Segoe UI', 20, 'bold')).pack(anchor='w')
        ttk.Label(panel, text='Equipá la caña y dejá Roblox visible.\nF8 activa/desactiva · F9 detiene', padding=(0, 12)).pack(anchor='w')
        self.button = ttk.Button(panel, text='Activar (F8)', command=self.toggle)
        self.button.pack(fill='x', pady=6)
        ttk.Button(panel, text='Seleccionar barra en pantalla', command=self.select_region).pack(fill='x', pady=6)
        ttk.Checkbutton(panel, text='Invertir control (el clic baja el cuadrado)', variable=self.invert).pack(anchor='w', pady=8)
        fields = ttk.Frame(panel)
        fields.pack(fill='x')
        for label, variable in [('Duración del lanzamiento (seg.)', self.cast_seconds), ('Espera máxima del pique (seg.)', self.bite_seconds)]:
            row = ttk.Frame(fields)
            row.pack(fill='x', pady=3)
            ttk.Label(row, text=label).pack(side='left')
            ttk.Entry(row, textvariable=variable, width=8).pack(side='right')
        self.status = tk.StringVar(value='Desactivado')
        ttk.Label(panel, textvariable=self.status, wraplength=400).pack(anchor='w', pady=12)
        root.protocol('WM_DELETE_WINDOW', self.close)
        self.previous_f8 = False
        self.poll()

    def save(self):
        SETTINGS.parent.mkdir(parents=True, exist_ok=True)
        SETTINGS.write_text(json.dumps({'region': self.region, 'invert': self.invert.get()}))

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
        self.worker = threading.Thread(target=self.run, args=(tuple(self.region), self.invert.get(), cast, bite), daemon=True)
        self.worker.start()

    def run(self, region, invert, cast, bite):
        mouse = Mouse()
        try:
            self.events.put('Activando en 3 segundos: enfocá Roblox y apuntá al agua.')
            if self.stop.wait(3):
                return
            screen = ImageGrab.grab()
            w, h = screen.size
            bbox = tuple(round(v * (w if i % 2 == 0 else h)) for i, v in enumerate(region))
            state = 'cast'
            deadline = time.monotonic()
            missing = 0
            while not self.stop.is_set():
                now = time.monotonic()
                if not roblox_active():
                    mouse.hold(False)
                    self.events.put('Pausado: enfocá Roblox para continuar.')
                    # Suspend timers and reset input when returning to the game.
                    self.stop.wait(.25)
                    deadline += time.monotonic() - now
                    continue
                result = detect(ImageGrab.grab(bbox=bbox))
                if result:
                    if state != 'play':
                        state = 'play'
                        deadline = now + 120
                        self.events.put('Pescando: siguiendo la zona verde/amarilla.')
                    missing = 0
                    error = result.cursor - result.target
                    # Screen Y increases downward. Holding normally raises the cursor.
                    if abs(error) > max(.012, result.target_height * .12):
                        mouse.hold((error > 0) != invert)
                    if now > deadline:
                        raise RuntimeError('La barra lleva 120 segundos visible. Revisá la selección y el control.')
                elif state == 'play':
                    mouse.hold(False)
                    missing += 1
                    if missing >= 12:
                        state, deadline = 'collect', now + .7
                        self.events.put('Minijuego terminado. Preparando recogida con T…')
                elif state == 'cast' and now >= deadline:
                    mouse.hold(True)
                    if self.stop.wait(cast):
                        break
                    mouse.hold(False)
                    state, deadline = 'waiting', time.monotonic() + bite
                    self.events.put('Caña lanzada. Esperando el minijuego…')
                elif state == 'waiting' and now >= deadline:
                    raise RuntimeError('No apareció la barra. Revisá la región, la caña y la duración del lanzamiento.')
                elif state == 'collect' and now >= deadline:
                    collect_fish(self.stop)
                    state, deadline = 'cooldown', time.monotonic() + 2.5
                    self.events.put('T pulsada. Preparando otro lanzamiento…')
                elif state == 'cooldown' and now >= deadline:
                    state = 'cast'
                self.stop.wait(.035)
        except Exception as exc:
            self.events.put('Error: ' + str(exc))
        finally:
            mouse.hold(False)
            self.stop.set()
            self.events.put(None)

    def select_region(self):
        if self.worker and self.worker.is_alive():
            self.stop.set()
            self.status.set('Esperá a que se detenga antes de seleccionar.')
            return
        self.root.withdraw()
        self.root.after(250, self.overlay)

    def overlay(self):
        shot = ImageGrab.grab()
        w, h = shot.size
        overlay = tk.Toplevel(self.root)
        overlay.overrideredirect(True)
        overlay.geometry(f'{w}x{h}+0+0')
        overlay.attributes('-topmost', True)
        canvas = tk.Canvas(overlay, width=w, height=h, cursor='crosshair', highlightthickness=0)
        canvas.pack()
        photo = ImageTk.PhotoImage(shot)
        canvas.create_image(0, 0, anchor='nw', image=photo)
        canvas.image = photo
        canvas.create_text(w//2, 40, text='Arrastrá alrededor de TODA la barra vertical (sin el porcentaje). Esc cancela.', fill='white', font=('Segoe UI', 16, 'bold'))
        start = []
        rectangle = []

        def finish(event=None):
            overlay.destroy()
            self.root.deiconify()

        def press(event):
            start[:] = [event.x, event.y]
            if rectangle:
                canvas.delete(rectangle.pop())
            rectangle.append(canvas.create_rectangle(event.x, event.y, event.x, event.y, outline='#00ff99', width=3))

        def drag(event):
            if start:
                canvas.coords(rectangle[0], *start, event.x, event.y)

        def release(event):
            if not start:
                return
            x1, x2 = sorted([start[0], event.x])
            y1, y2 = sorted([start[1], event.y])
            if x2-x1 >= 12 and y2-y1 >= 60:
                self.region = [x1/w, y1/h, x2/w, y2/h]
                try:
                    self.save()
                    self.status.set('Barra guardada. Podés activar el macro.')
                except OSError as exc:
                    self.status.set('No se pudo guardar: ' + str(exc))
                finish()

        canvas.bind('<ButtonPress-1>', press)
        canvas.bind('<B1-Motion>', drag)
        canvas.bind('<ButtonRelease-1>', release)
        overlay.bind('<Escape>', finish)
        overlay.focus_force()

    def poll(self):
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
                if not self.status.get().startswith('Error:'):
                    self.status.set('Desactivado')
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
    App(root)
    if '--smoke-test' in sys.argv:
        root.withdraw()
        root.update()
        root.destroy()
    else:
        root.mainloop()
