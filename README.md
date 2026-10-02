# Macro de pesca · Slayer 2

Aplicación de escritorio para Windows en Python. Lanza la caña con clic izquierdo, detecta los bordes superior e inferior del rectángulo verde/amarillo y el centro del cuadrado blanco, y mantiene o suelta el clic para dejar el cuadrado dentro del rectángulo. Al terminar el minijuego, mantiene T para recoger peces u objetos: comprueba que empiece a cargar el rombo a los dos segundos y reintenta la pulsación sostenida si no carga. Al registrar una recogida, suelta T y vuelve a lanzar inmediatamente. Si después de tres intentos T no hay una recogida registrada ni `x1`, suelta T y lanza de nuevo. No mueve al personaje.

## Uso

1. Abrí `dist/Slayer2Pesca.exe`. No necesita Python instalado.
2. Abrí Roblox, equipá la caña y ubicá al personaje junto al agua con agua azul visible en la cámara.
3. La aplicación localiza la posición habitual de la barra dentro de la ventana de Roblox automáticamente. No hace falta seleccionar una región.
4. Pulsá **Activar** o **F8**. Tenés tres segundos para enfocar Roblox. Con **Apuntado automático** marcado, pulsa Alt izquierdo antes del primer lanzamiento para liberar el cursor y busca una zona de agua azul despejada. Con el checkbox desmarcado, apunta al punto manual guardado y no pulsa Alt: dejá el cursor libre. Si el minijuego ya está visible, continúa esa pesca sin cambiar el modo del cursor.
5. Para apuntar manualmente, pulsá **Apuntado manual** al lado del checkbox, enfocá Roblox, ubicá el mouse sobre el agua y pulsá **F6** sin hacer clic. Si el cursor está bloqueado, liberalo con Alt. Tenés 30 segundos; Esc cancela. Al guardar, desmarca el automático y reutiliza ese punto en cada lanzamiento. El punto se escala si movés o redimensionás la ventana; volvé a marcarlo si girás la cámara.
6. **F8** activa/desactiva; **F9** detiene. Al desactivar o cerrar se sueltan el clic y la T. Al cambiar de ventana, pausa y suelta el clic y la T; continúa al enfocar Roblox.

La posición se calcula respecto al área del juego y se actualiza si movés o redimensionás la ventana. Corresponde al HUD de la captura y el video de referencia, con la barra centrada al 75% del ancho. Mantené toda la ventana visible y el HUD en su distribución habitual. El control busca el contorno rectangular del objetivo y mide sus bordes superior e inferior, y el centro y tamaño del cuadrado independientemente. Rechaza las manchas verdes del escenario que atraviesan el recorte del HUD; no elige la mayor mancha verde. Las medidas se normalizan al tamaño de la barra. Estos tres valores aparecen en la aplicación junto a una miniatura de la barra con los dos límites naranjas y la línea blanca del centro del cuadrado. Calcula un intervalo seguro considerando el tamaño del cuadrado. Estima la velocidad relativa al objetivo, anticipa la distancia de frenado y reduce la velocidad de aproximación al centro; compensa diferencias persistentes entre subida y caída. La lectura usa captura directa de la región de la barra con MSS y una espera de 2 ms entre iteraciones del minijuego, además del tiempo de captura y procesamiento. Si se pierde una lectura brevemente, frena conservando la velocidad estimada; después de 120 ms sin detección libera el clic y descarta esa estimación. El control supone que mantener el clic sube el cuadrado; si lo baja, activá **Invertir control** antes de iniciar. La duración del lanzamiento y la espera máxima del pique son ajustables antes de iniciar. El modo de apuntado, el punto manual y el sentido se guardan en `%LOCALAPPDATA%/Slayer2Fishing/settings.json`; las antiguas selecciones manuales se ignoran.

La interfaz tiene fondo negro, texto blanco y controles naranjas. Se mantiene siempre encima de Roblox; dejala a un lado para que no cubra la barra ni el aviso T. Al hacer clic en la aplicación se pausa hasta volver a enfocar Roblox. La búsqueda de agua excluye la ventana del macro.

## Compilar o ejecutar desde Python

Con Python 3.11 o posterior para Windows instalado (incluyendo Tkinter):

```powershell
powershell -ExecutionPolicy Bypass -File .\build.ps1
```

El script crea `.venv`, instala dependencias, ejecuta las pruebas y genera `dist/Slayer2Pesca.exe` mediante PyInstaller. Para ejecutar el código: `.\.venv\Scripts\python.exe main.py`.

Los binarios generados se excluyen de Git. El workflow de GitHub Actions compila el ejecutable en Windows y lo ofrece como artifact **Slayer2Pesca-Windows** en la pestaña Actions para cada push a `feature/pesca`, `feature/apuntado-y-recoleccion` o `feature/fix-x1-movimientoJG-recuento` y al ejecutarlo manualmente.

## Recolección y recuperación

La interfaz muestra el total recogido, un inventario por nombre y el tiempo activo `HH:MM:SS`. Los valores se conservan al desactivar/reactivar y se reinician al cerrar. El tiempo excluye la cuenta regresiva inicial y las pausas fuera de Roblox. El inventario admite desplazamiento con la rueda del mouse cuando hay más de cinco tipos.

Reconoce las referencias de Pez dorado, Pez payaso, Pez cebra e Hilo de seda y usa el OCR local de Windows para leer otros nombres, como Pez azul o Chatarra. Si la cantidad está confirmada pero no puede leer el nombre, suma a Sin identificar. El OCR necesita un idioma de reconocimiento instalado en Windows; si no está disponible, mantiene la detección visual de las referencias y el total por x1. No envía imágenes a servicios externos.

El aumento del recuento confirma el ciclo: al reconocer un cartel de recompensa, suma una unidad, suelta T y prepara otro lanzamiento aunque no lea x1. Cada ciclo suma una sola vez. Como segunda señal usa nombres de referencia con la tipografía del cartel de recompensa y nombres de peces, Chatarra o Hilo de seda leídos por OCR con ese tamaño de letra. No suma por terminar el minijuego ni por desaparecer T. Relanza en la misma iteración que confirma la recogida, sin pausa de 2,5 segundos ni esperar a que desaparezca el cartel anterior. Evita contar nuevamente un aviso que siga visible. Si x1 confirma un objeto nuevo, la lectura OCR de su nombre continúa en segundo plano después del relanzamiento. La cantidad se reconoce también por contraste local para recuperar letras atenuadas, dentro de una región más amplia para avisos desplazados.

Para el lanzamiento inicial y la recuperación sin recogida confirmada, espera 0,6 segundos de estabilidad del escenario, ignorando el agua azul animada. Después de una recogida confirmada, omite esa espera y la pausa de posicionamiento del mouse; reutiliza la captura de confirmación para apuntar y lanzar inmediatamente. Si se mueve la cámara o el personaje, espera; en automático recalcula el agua. Esto evita lanzar durante el desplazamiento, pero no impide los empujones físicos del juego. En manual, marcá nuevamente el punto con F6 si cambia la posición o la cámara.

Cuando aparece el cartel T después del minijuego, envía una entrada de tecla abajo con el código físico de T. La mantiene durante al menos dos segundos antes de reintentar. Si no detecta el rombo cargando, suelta T durante 0,1 segundos y vuelve a mantenerla. Una vez detectada la carga, mantiene T sin repetir entradas; si el cartel vuelve al estado sin carga durante dos segundos, reintenta. Una desaparición del cartel durante la carga no interrumpe la pulsación. El aviso de cantidad (`x1`) o un nombre reconocido en el cartel de recompensa confirma la recogida y actualiza el inventario; ese aumento habilita el siguiente lanzamiento. La detección busca tanto el texto nítido como sus letras blancas atenuadas sobre un panel translúcido.

Para una vuelta vacía, espera seis segundos desde el final del minijuego sin haber visto un aviso T ni `x1`, y lanza otra vez. Es una inferencia visual por ausencia de aviso, no una lectura del contenido de la caña. Si vio el cartel T, realiza hasta tres intentos de recogida. Si ninguno confirma un objeto, suelta T y relanza incluso si el cartel sigue visible. Cada intento espera dos segundos si no carga; si llegó a cargar, tiene un límite de doce segundos para evitar una espera indefinida. Después de una desaparición, puede repetir T hasta completar esos tres intentos. El margen permite que la caña vuelva antes de relanzar.

El clic y la T se liberan al perder el foco de Roblox, detener, cerrar o ante un error. Las pausas no cuentan para el margen de retorno vacío. Al volver a Roblox, detecta el cartel e inicia una nueva pulsación sostenida. Si no aparece el minijuego dentro del tiempo de pique configurado, vuelve a lanzar; si no encuentra agua o la aplicación tapa el punto manual, espera y reintenta.

La detección de agua usa color azul y una zona despejada cerca del centro de la cámara. No gira la cámara para explorar. Si no encuentra agua, orientá la cámara hacia ella. Alt izquierdo es una tecla de alternancia: iniciá con el cursor centrado/bloqueado para que libere el mouse. Mantené visibles la barra, el rombo T y el aviso de cantidad.

Las pruebas usan recortes de los videos aportados: objetivo amarillo, objetivo verde, cuadrado teñido por el fondo, hojas verdes detrás del HUD y avisos de recogida/carga/`x1`. Cubren distintas escalas, control con inercia y demora de entrada a 30/60 lecturas por segundo, aceleraciones de subida/caída distintas, pulsación continua, reintento tras dos segundos sin carga, relanzamiento después de tres intentos sin confirmar recogida, reconocimiento por nombre sin x1, inventario y tiempo con pausas, estabilidad del escenario, confirmación de peces/objetos y detección de `x1` translúcido.
