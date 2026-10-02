# Macro de pesca · Slayer 2

Aplicación de escritorio para Windows que lanza la caña, juega el minijuego de pesca y recoge peces u objetos. No mueve al personaje. El código está en este repositorio; el ejecutable se genera aparte y no se guarda en Git.

## Ejecutarlo desde el código

Necesitás Windows y Python 3.12 (o posterior) instalado con **Tcl/Tk**. Para instalar Python 3.12 con WinGet, abrí PowerShell y ejecutá:

```powershell
winget install --exact --id Python.Python.3.12
```

Después, desde PowerShell en la carpeta del proyecto, prepará el entorno e iniciá la aplicación:

```powershell
py -3 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe main.py
```

Si ya existe `.venv`, no vuelvas a crearla: ejecutá los dos últimos comandos. La ventana **Slayer 2 · Pesca** debería abrirse. También podés usar `python` en lugar de `py -3` si ese es el comando configurado en tu Windows.

## Crear el ejecutable

Con Python y Tcl/Tk instalados, ejecutá:

```powershell
powershell -ExecutionPolicy Bypass -File .\build.ps1
```

El script instala las dependencias en `.venv`, corre las pruebas y compila `dist\Slayer2Pesca.exe`. Ese ejecutable es autocontenido y no requiere instalar Python en el equipo donde se use. Si ya se compiló correctamente, podés abrirlo directamente:

```powershell
.\dist\Slayer2Pesca.exe
```

También se puede obtener el ejecutable sin compilar: en GitHub abrí **Actions → Compilar Windows**, elegí **Run workflow** con la rama `main`, y al terminar descargá el artifact **Slayer2Pesca-Windows**. Extraé el ZIP y abrí `Slayer2Pesca.exe`.

## Preparar y usar la pesca

1. Abrí Roblox, equipá la caña y orientá la cámara hacia el agua. Dejá visible el área de pesca.
2. Abrí la aplicación y ubicá su ventana a un costado para que no cubra la barra del minijuego, el aviso **T** ni el mensaje de cantidad.
3. Elegí el apuntado. **Apuntado automático** viene activado y busca agua azul despejada en la cámara. Si preferís un punto fijo, usá **Apuntado manual**, enfocá Roblox, dejá el cursor sobre el agua y pulsá **F6** sin hacer clic. Tenés 30 segundos para elegir; **Esc** cancela. El punto se guarda y se escala al mover o redimensionar la ventana del juego. Volvé a marcarlo si girás la cámara.
4. Ajustá **Duración del lanzamiento** si hace falta (de 0,05 a 5 segundos) y **Espera máxima del pique** (de 5 a 180 segundos). Normalmente podés dejar los valores iniciales.
5. Pulsá **Activar** o **F8** y enfocá Roblox durante la cuenta regresiva de tres segundos. En apuntado automático, el programa usa **Alt izquierdo** para liberar el cursor y busca dónde lanzar. Si Roblox está configurado para reaccionar distinto a Alt, probá el apuntado manual.
6. Cuando aparezca el minijuego, el programa detecta el rectángulo verde/amarillo y el cuadrado blanco, y mantiene o suelta el clic para conservar el cuadrado dentro del objetivo. La miniatura de la aplicación muestra los límites detectados.
7. Al terminar, mantiene **T** para recoger. Espera la confirmación visual `x1` antes del siguiente lanzamiento. Si la caña vuelve sin aviso de interacción, reintenta el lanzamiento automáticamente.

La barra se localiza dentro de la ventana del juego y se adapta a su tamaño. Conservá el HUD en su disposición habitual y la ventana de Roblox visible. Si no encuentra agua, orientá la cámara hacia una zona azul despejada. Si el clic hace bajar el cuadrado en vez de subirlo, activá **Invertir control** antes de iniciar.

## Teclas y pausa

- **F8**: activar o desactivar el ciclo.
- **F9**: detenerlo.
- **F6**: guardar el punto de apuntado manual mientras elegís la ubicación.
- **Esc**: cancelar la selección manual.

Al detener, cerrar o cambiar el foco fuera de Roblox, la aplicación suelta el clic y la tecla **T**. Al volver a enfocar Roblox, continúa el ciclo. Las preferencias de apuntado y sentido se guardan en `%LOCALAPPDATA%\Slayer2Fishing\settings.json`.

## Si algo no funciona

- **La aplicación no abre desde Python:** comprobá que Python incluya Tcl/Tk y volvé a instalar las dependencias con `python -m pip install -r requirements.txt`.
- **El ejecutable no aparece:** revisá que `build.ps1` haya terminado sin errores; el archivo queda en `dist\Slayer2Pesca.exe`.
- **No encuentra el agua:** girá la cámara hacia agua azul despejada o guardá un punto manual con F6.
- **La barra no se detecta:** dejá todo el HUD visible, sin que lo tape la ventana del macro, y usá la distribución habitual de la interfaz del juego.
- **El cuadrado se mueve en sentido contrario:** activá **Invertir control**.
- **La tecla T o el `x1` no se detectan:** mantené visibles el aviso T, el rombo de carga y el mensaje de objeto recibido.

Las pruebas automatizadas se ejecutan durante la compilación. Para correrlas por separado:

```powershell
.\.venv\Scripts\python.exe -m unittest discover -s tests
```
