# Macro de pesca · Slayer 2

Aplicación de escritorio para Windows en Python. Lanza la caña con clic izquierdo, detecta la zona verde/amarilla y el cuadrado blanco de la barra, y mantiene o suelta el clic para seguir la zona. Cuando desaparece el minijuego, espera hasta detectar el aviso de **T** junto al pescado, pulsa la tecla, comprueba que desaparezca el aviso y espera 2,5 segundos para volver a lanzar. No mueve al personaje.

## Uso

1. Abrí `dist/Slayer2Pesca.exe`. No necesita Python instalado.
2. Abrí Roblox, equipá la caña y ubicá al personaje junto al agua con agua azul visible en la cámara.
3. La aplicación localiza la posición habitual de la barra dentro de la ventana de Roblox automáticamente. No hace falta seleccionar una región.
4. Pulsá **Activar** o **F8**. Tenés tres segundos para enfocar Roblox. Antes del primer lanzamiento pulsa Alt izquierdo para liberar el cursor, busca una zona de agua azul despejada y coloca el mouse allí. Si el minijuego ya está visible, continúa esa pesca sin cambiar el modo del cursor.
5. **F8** activa/desactiva; **F9** detiene. Al desactivar o cerrar se suelta el clic. Al cambiar de ventana, pausa y suelta el clic; continúa al enfocar Roblox.

La posición se calcula respecto al área del juego y se actualiza si movés o redimensionás la ventana. Corresponde al HUD de la captura y el video de referencia, con la barra centrada al 75% del ancho. Mantené toda la ventana visible y el HUD en su distribución habitual. El control mide los bordes superior e inferior de la zona en los laterales de la barra, y el centro y tamaño del cuadrado independientemente. Estos tres valores aparecen en la aplicación. Calcula un intervalo seguro considerando el tamaño del cuadrado y estima la velocidad para frenar antes de pasar el centro; usa una tolerancia pequeña y captura aproximadamente cada 15 ms más el tiempo de procesamiento. El control supone que mantener el clic sube el cuadrado; si lo baja, activá **Invertir control** antes de iniciar. La duración del lanzamiento y la espera máxima del pique son ajustables. El sentido se guarda en `%LOCALAPPDATA%/Slayer2Fishing/settings.json`; las antiguas selecciones manuales se ignoran.

La interfaz tiene fondo negro, texto blanco y controles naranjas. Se mantiene siempre encima de Roblox; dejala a un lado para que no cubra la barra ni el aviso T. Al hacer clic en la aplicación se pausa hasta volver a enfocar Roblox. La búsqueda de agua excluye la ventana del macro.

## Compilar o ejecutar desde Python

Con Python 3.11 o posterior para Windows instalado (incluyendo Tkinter):

```powershell
powershell -ExecutionPolicy Bypass -File .\build.ps1
```

El script crea `.venv`, instala dependencias, ejecuta las pruebas y genera `dist/Slayer2Pesca.exe` mediante PyInstaller. Para ejecutar el código: `.\.venv\Scripts\python.exe main.py`.

Los binarios generados se excluyen de Git. El workflow de GitHub Actions compila el ejecutable en Windows y lo ofrece como artifact **Slayer2Pesca-Windows** en la pestaña Actions para cada push a `feature/pesca` y al ejecutarlo manualmente.

## Alcance de la primera versión

La mecánica del clic y los tiempos necesitan una prueba dentro del juego. El macro no lee el porcentaje: sigue la barra hasta que desaparece; esto permite repetir tanto después de una captura como después de un fallo. No distingue ambos resultados por el porcentaje; la recogida depende de detectar el aviso T. Si el aviso no aparece en 25 segundos, se detiene sin volver a lanzar para que puedas revisar el pescado. Si sigue visible después de pulsar T, reintenta hasta tres veces y se detiene si no desaparece. La desaparición del aviso confirma el cambio visual, no garantiza que el inventario haya recibido el pescado. Si no detecta el pique dentro del tiempo configurado o la barra permanece más de 120 segundos, se detiene con un mensaje. Usa captura de pantalla y entradas de mouse de Windows; no modifica el cliente de Roblox.

La detección de agua usa color azul y una zona despejada cerca del centro de la cámara. No mueve al personaje ni gira la cámara para explorar. Si no encuentra agua, muestra un error; orientá la cámara hacia ella antes de reactivar. Alt izquierdo es una tecla de alternancia: iniciá con el cursor centrado/bloqueado para que libere el mouse. La detección del aviso T usa una referencia visual del video y puede requerir ajustes si cambia la apariencia del HUD.
