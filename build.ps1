$ErrorActionPreference = 'Stop'
Set-Location $PSScriptRoot
if (-not (Test-Path '.venv/Scripts/python.exe')) {
    py -3 -m venv .venv
    if ($LASTEXITCODE -ne 0) { throw 'No se pudo crear el entorno Python.' }
}
& '.venv/Scripts/python.exe' -m pip install -r requirements.txt
if ($LASTEXITCODE -ne 0) { throw 'No se pudieron instalar las dependencias.' }
& '.venv/Scripts/python.exe' -m unittest discover -s tests
if ($LASTEXITCODE -ne 0) { throw 'Fallaron las pruebas.' }
& '.venv/Scripts/python.exe' -m PyInstaller --noconfirm --clean --onefile --windowed --name Slayer2Pesca main.py
if ($LASTEXITCODE -ne 0) { throw 'No se pudo generar el ejecutable.' }
$smoke = Start-Process -FilePath '.\dist\Slayer2Pesca.exe' -ArgumentList '--smoke-test' -WindowStyle Hidden -PassThru -Wait
if ($smoke.ExitCode -ne 0) { throw 'El ejecutable no pudo iniciar su interfaz.' }
Write-Host 'Ejecutable: dist/Slayer2Pesca.exe'
