@echo off
echo Creando ejecutable de TV IP Player...
echo.

REM Detener cualquier instancia en ejecución
taskkill /f /im python.exe 2>nul
taskkill /f /im "TV IP Player.exe" 2>nul

REM Limpiar directorios anteriores si existen
if exist dist rmdir /s /q dist
if exist build rmdir /s /q build

REM Crear el ejecutable con PyInstaller usando el archivo de especificación
pyinstaller --noconfirm tv_ip_player.spec

echo.
if %ERRORLEVEL% EQU 0 (
    echo Ejecutable creado correctamente en la carpeta 'dist'
    echo Ruta: %CD%\dist\TV IP Player.exe
    
    REM Copiar el archivo de icono al directorio del ejecutable para asegurar que esté disponible
    copy icono.ico dist\ /Y
    
    echo.
    echo ¿Desea ejecutar la aplicación ahora? (S/N)
    choice /C SN /M "Seleccione una opción:"
    if %ERRORLEVEL% EQU 1 (
        echo Iniciando TV IP Player...
        start "" "dist\TV IP Player.exe"
    )
) else (
    echo Error al crear el ejecutable
)

pause
