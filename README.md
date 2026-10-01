# Macro de pesca · Slayer 2

Aplicación de escritorio para Windows en Python. Lanza la caña con clic izquierdo, detecta la zona verde/amarilla y el cuadrado blanco de la barra, y mantiene o suelta el clic para seguir la zona. Cuando desaparece el minijuego, mantiene clic sobre el cartel T en cuanto aparece el aviso, siguiendo su posición aunque se mueva, sin un tiempo fijo hasta detectar el aviso de objeto recibido con cantidad (`x1`) y espera 2,5 segundos para volver a lanzar. No mueve al personaje.

## Uso

1. Abrí `dist/Slayer2Pesca.exe`. No necesita Python instalado.
2. Abrí Roblox, equipá la caña y ubicá al personaje junto al agua con agua azul visible en la cámara.
3. La aplicación localiza la posición habitual de la barra dentro de la ventana de Roblox automáticamente. No hace falta seleccionar una región.
4. Pulsá **Activar** o **F8**. Tenés tres segundos para enfocar Roblox. Con **Apuntado automático** marcado, pulsa Alt izquierdo antes del primer lanzamiento para liberar el cursor y busca una zona de agua azul despejada. Con el checkbox desmarcado, apunta al punto manual guardado y no pulsa Alt: dejá el cursor libre. Si el minijuego ya está visible, continúa esa pesca sin cambiar el modo del cursor.
5. Para apuntar manualmente, pulsá **Apuntado manual** al lado del checkbox, enfocá Roblox, ubicá el mouse sobre el agua y pulsá **F6** sin hacer clic. Si el cursor está bloqueado, liberalo con Alt. Tenés 30 segundos; Esc cancela. Al guardar, desmarca el automático y reutiliza ese punto en cada lanzamiento. El punto se escala si movés o redimensionás la ventana; volvé a marcarlo si girás la cámara.
6. **F8** activa/desactiva; **F9** detiene. Al desactivar o cerrar se suelta el clic. Al cambiar de ventana, pausa y suelta el clic; continúa al enfocar Roblox.

La posición se calcula respecto al área del juego y se actualiza si movés o redimensionás la ventana. Corresponde al HUD de la captura y el video de referencia, con la barra centrada al 75% del ancho. Mantené toda la ventana visible y el HUD en su distribución habitual. El control mide los bordes superior e inferior de la zona en los laterales de la barra, y el centro y tamaño del cuadrado independientemente. Estos tres valores aparecen en la aplicación. Calcula un intervalo seguro considerando el tamaño del cuadrado y estima la velocidad para frenar antes de pasar el centro; usa una tolerancia pequeña y captura aproximadamente cada 15 ms más el tiempo de procesamiento. El control supone que mantener el clic sube el cuadrado; si lo baja, activá **Invertir control** antes de iniciar. La duración del lanzamiento y la espera máxima del pique son ajustables antes de iniciar. El modo de apuntado, el punto manual y el sentido se guardan en `%LOCALAPPDATA%/Slayer2Fishing/settings.json`; las antiguas selecciones manuales se ignoran.

La interfaz tiene fondo negro, texto blanco y controles naranjas. Se mantiene siempre encima de Roblox; dejala a un lado para que no cubra la barra ni el aviso T. Al hacer clic en la aplicación se pausa hasta volver a enfocar Roblox. La búsqueda de agua excluye la ventana del macro.

## Compilar o ejecutar desde Python

Con Python 3.11 o posterior para Windows instalado (incluyendo Tkinter):

```powershell
powershell -ExecutionPolicy Bypass -File .\build.ps1
```

El script crea `.venv`, instala dependencias, ejecuta las pruebas y genera `dist/Slayer2Pesca.exe` mediante PyInstaller. Para ejecutar el código: `.\.venv\Scripts\python.exe main.py`.

Los binarios generados se excluyen de Git. El workflow de GitHub Actions compila el ejecutable en Windows y lo ofrece como artifact **Slayer2Pesca-Windows** en la pestaña Actions para cada push a `feature/pesca` o `feature/apuntado-y-recoleccion` y al ejecutarlo manualmente.

## Alcance de la primera versión

La mecánica del clic y los tiempos necesitan una prueba dentro del juego. El macro no lee el porcentaje: sigue la barra hasta que desaparece; la recogida se activa después de que termina la barra. No distingue los resultados por el porcentaje. En cuanto aparece T después del minijuego, mantiene el botón izquierdo aunque el aviso se mueva. Reconoce también el icono de la acción cargando. Si sigue apareciendo el aviso normal sin comenzar la carga durante 1,5 segundos, suelta el clic durante 0,12 segundos y vuelve a hacer clic sobre el centro actualizado del cartel. Una vez reconocida la carga, mantiene el clic continuamente incluso si una captura no reconoce momentáneamente el icono. Si el cartel vuelve al estado normal durante 2,5 segundos seguidos, reintenta el clic para recuperar una carga cancelada.

Solo el aviso de objeto recibido con cantidad (`x1`) habilita soltar el clic y volver a lanzar. La desaparición del aviso T no confirma una captura y no causa un relanzamiento. Si todavía no aparece el aviso o la cantidad, continúa esperando hasta detener el macro. Se trata de una confirmación visual del juego; no se consulta el inventario interno. El botón izquierdo se libera al perder el foco de Roblox, detener o cerrar la aplicación; al volver a Roblox se retoma la recogida pendiente. Si no aparece el minijuego dentro del tiempo de pique configurado, vuelve a lanzar; si no encuentra agua o la aplicación tapa el punto manual, espera y reintenta. Los errores de captura o del sistema pueden detenerlo con un mensaje.

La detección de agua usa color azul y una zona despejada cerca del centro de la cámara. No mueve al personaje ni gira la cámara para explorar. Si no encuentra agua, espera y reintenta; orientá la cámara hacia ella. Alt izquierdo es una tecla de alternancia: iniciá con el cursor centrado/bloqueado para que libere el mouse. La detección del aviso T usa una referencia visual del video y puede requerir ajustes si cambia la apariencia del HUD.

La detección usa los videos aportados, con plantillas del aviso normal, el aviso grande y la acción cargando. Las pruebas cubren avisos en movimiento, carga continua, reintentos sin carga, confirmación x1 y ausencia de confirmación sin relanzamiento.

La recogida utiliza clic izquierdo mantenido sobre el icono T, no entradas de teclado T. El cursor sigue el aviso dentro de la ventana de Roblox. La aplicación no inicia un clic si está tapando ese punto: movela a un lado. La tecla T sigue siendo una entrada manual del juego.
