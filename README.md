# Macro de pesca · Slayer 2

Aplicación de escritorio para Windows en Python. Lanza la caña con clic izquierdo, detecta la zona verde/amarilla y el cuadrado blanco de la barra, y mantiene o suelta el clic para seguir la zona. Cuando desaparece el minijuego, espera 0,7 segundos, pulsa **T** para recoger el pescado, espera 2,5 segundos y vuelve a lanzar. No mueve al personaje.

## Uso

1. Abrí `dist/Slayer2Pesca.exe`. No necesita Python instalado.
2. Abrí Roblox, equipá la caña y apuntá al agua.
3. La aplicación localiza la posición habitual de la barra dentro de la ventana de Roblox automáticamente. No hace falta seleccionar una región.
4. Pulsá **Activar** o **F8**. Tenés tres segundos para enfocar Roblox. Si el minijuego ya está visible, continúa esa pesca.
5. **F8** activa/desactiva; **F9** detiene. Al desactivar o cerrar se suelta el clic. Al cambiar de ventana, pausa y suelta el clic; continúa al enfocar Roblox.

La posición se calcula respecto al área del juego y se actualiza si movés o redimensionás la ventana. Corresponde al HUD de la captura y el video de referencia, con la barra centrada al 75% del ancho. Mantené toda la ventana visible y el HUD en su distribución habitual. El control estima la velocidad del cuadrado y de la zona para frenar antes de pasar el centro; usa una tolerancia pequeña y captura aproximadamente cada 15 ms más el tiempo de procesamiento. El control supone que mantener el clic sube el cuadrado; si lo baja, activá **Invertir control** antes de iniciar. La duración del lanzamiento y la espera máxima del pique son ajustables. El sentido se guarda en `%LOCALAPPDATA%/Slayer2Fishing/settings.json`; las antiguas selecciones manuales se ignoran.

La interfaz tiene fondo negro, texto blanco y botones, checkbox y bordes de entrada naranjas.

## Compilar o ejecutar desde Python

Con Python 3.11 o posterior para Windows instalado (incluyendo Tkinter):

```powershell
powershell -ExecutionPolicy Bypass -File .\build.ps1
```

El script crea `.venv`, instala dependencias, ejecuta las pruebas y genera `dist/Slayer2Pesca.exe` mediante PyInstaller. Para ejecutar el código: `.\.venv\Scripts\python.exe main.py`.

Los binarios generados se excluyen de Git. El workflow de GitHub Actions compila el ejecutable en Windows y lo ofrece como artifact **Slayer2Pesca-Windows** en la pestaña Actions para cada push a `feature/pesca` y al ejecutarlo manualmente.

## Alcance de la primera versión

La mecánica del clic y los tiempos necesitan una prueba dentro del juego. El macro no lee el porcentaje: sigue la barra hasta que desaparece; esto permite repetir tanto después de una captura como después de un fallo. No distingue ambos resultados. Si no detecta el pique dentro del tiempo configurado o la barra permanece más de 120 segundos, se detiene con un mensaje. Usa captura de pantalla y entradas de mouse de Windows; no modifica el cliente de Roblox.
