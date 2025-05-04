# TV IP Player

Una aplicación moderna y simple para reproducir canales de TV IP mediante listas M3U/M3U8.

## Características

- Interfaz gráfica moderna y fácil de usar
- Soporte para listas M3U y M3U8
- Reproducción de canales en pantalla completa o ventana
- Filtrado de canales por grupos
- Carga de múltiples listas de reproducción
- Reproductor de video integrado con VLC
- Optimizado para Windows con integración en la barra de tareas
- Atajos de teclado específicos para Windows
- Detección automática de plugins de VLC en Windows

## Requisitos

- Python 3.8 o superior
- VLC Media Player instalado en el sistema

## Instalación

1. Clonar o descargar este repositorio
2. Instalar las dependencias:
   ```
   pip install -r requirements.txt
   ```

## Uso

1. Ejecutar la aplicación:
   ```
   python modern_player.py
   ```
2. Hacer clic en 'Cargar Lista M3U' para abrir un archivo de lista de reproducción
3. Seleccionar un grupo de canales usando el filtro (opcional)
4. Hacer clic en un canal para comenzar la reproducción
5. Usar el botón 'Pantalla Completa' para alternar entre modos de visualización

## Atajos de teclado

- **F11** o **Alt+Enter**: Alternar pantalla completa
- **Esc**: Salir de pantalla completa
- **Alt+F**: Abrir menú de archivo (Windows)
- **Ctrl+M**: Mostrar/ocultar menú contextual (Windows)

## Formatos Soportados

- M3U
- M3U8
- Streams HTTP/RTMP

## Optimizaciones para Windows

- Integración con la barra de tareas de Windows
- Detección automática de la ruta de plugins de VLC
- Normalización de rutas de archivos para Windows
- Identificación de aplicación en la barra de tareas de Windows