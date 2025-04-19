# TV IP Player

Una aplicación moderna y modular para reproducir canales de TV IP y contenido multimedia con soporte para cambio de idioma y múltiples opciones de visualización.

## Características Principales

- **Interfaz Modular y Responsiva**: Diseño elegante que se adapta a diferentes tamaños de pantalla
- **Menú Contextual Completo**: Acceso rápido a todas las funcionalidades desde cualquier punto de la aplicación
- **Cambio de Idioma**: Soporte para cambiar entre pistas de audio disponibles
- **Opciones de Visualización Avanzadas**:
  - Pantalla completa con controles inteligentes
  - Múltiples relaciones de aspecto (16:9, 4:3, 2.35:1, etc.)
  - Diferentes escalas de video (0.5x, 1.0x, 2.0x)
- **Soporte para Listas M3U/M3U8**: Carga, filtrado y gestión de listas de canales
- **Verificación de Canales**: Comprobación automática de disponibilidad de canales
- **Integración con VLC**: Aprovecha todas las funcionalidades del motor VLC

## Estructura del Código

La aplicación está organizada de manera modular siguiendo principios de diseño orientado a objetos:

### Módulos Principales

#### `main.py`
Punto de entrada de la aplicación. Inicializa la interfaz gráfica y el bucle de eventos.

#### `src/core/`
Contiene los componentes centrales de la lógica de negocio:

- **`media_player.py`**: Encapsula toda la funcionalidad del reproductor VLC
  - Reproducción de contenido multimedia
  - Cambio de pistas de audio
  - Ajuste de relación de aspecto y escala
  - Control de volumen y posición

- **`playlist_manager.py`**: Gestiona las listas de reproducción
  - Carga y parseo de archivos M3U/M3U8
  - Filtrado y organización de canales por grupos
  - Verificación de estado de canales

#### `src/ui/`
Implementa la interfaz gráfica de usuario:

- **`main_window.py`**: Ventana principal y coordinación de componentes
  - Gestión de pantalla completa
  - Disposición general de la interfaz
  - Coordinación entre sidebar y área de video
  
- **`video_widget.py`**: Widget especializado para reproducción de video
  - Gestión del menú contextual
  - Manejo de eventos del mouse y teclado
  - Opciones de visualización de video
  
- **`sidebar.py`**: Panel lateral con listado de canales y controles
  - Listado de canales filtrable
  - Controles de reproducción
  - Funciones de carga y gestión de playlists

#### `src/utils/`
Utilidades y funciones auxiliares para toda la aplicación.

## Interfaz Visual (Textual UI)

A partir de la rama `feature/flex-ui` la aplicación utiliza [Textual](https://www.textualize.io/) para una interfaz TUI moderna y flexible.

- Interfaz completamente en terminal, con soporte para mouse, teclado, layouts flexibles y widgets avanzados.
- El código de la interfaz principal está en `src/ui/textual_app.py`.

### Ejecución en esta rama:

1. Instala las dependencias:
   ```
   pip install textual rich
   ```
2. Ejecuta la aplicación:
   ```
   python main.py
   ```

Próximos pasos: migrar la lógica de reproducción y gestión de listas a widgets Textual.

## Funcionalidades Detalladas

### Reproducción de Contenido

- **Reproducción Fluida**: Buffer optimizado para streaming de contenido
- **Múltiples Formatos**: Soporte para diversos formatos de video y audio
- **Control Preciso**: Pausa, avance, retroceso, ajuste de velocidad

### Gestión de Audio

- **Múltiples Pistas**: Selección entre pistas de audio disponibles
- **Normalización de Volumen**: Nivelación automática del volumen entre canales
- **Audio Pasthrough**: Soporte para formatos de audio avanzados (AC3, DTS, etc.)

### Personalización de Video

- **Relaciones de Aspecto**: Múltiples opciones preconfiguradas
  - Auto, 16:9, 4:3, 1:1, 16:10, 2.35:1, 2.21:1, 1.85:1
  
- **Escalado de Video**: Opciones para ajustar el tamaño del video
  - Ajuste a ventana (0.5x)
  - Tamaño original (1.0x)
  - Ampliación (2.0x)

### Interfaz de Usuario

- **Menú Contextual**: Accesible mediante botón naranja en la esquina superior izquierda
- **Panel Lateral Inteligente**: Se oculta automáticamente en modo pantalla completa
- **Atajos de Teclado**: Para todas las funciones principales

## Requisitos

- Python 3.8 o superior
- VLC Media Player instalado en el sistema
- PyQt6
- Dependencias listadas en requirements.txt

## Instalación

1. Clonar o descargar este repositorio
2. Instalar las dependencias:
   ```
   pip install -r requirements.txt
   ```

## Uso

1. Ejecutar la aplicación:
   ```
   python main.py
   ```
2. Cargar una lista de canales usando el botón correspondiente
3. Seleccionar un canal para comenzar la reproducción
4. Acceder al menú contextual haciendo clic en el botón naranja (≡)
5. Explorar las diferentes opciones de audio y video disponibles

## Formatos Soportados

- Video: MP4, MKV, AVI, FLV, etc.
- Audio: MP3, AAC, FLAC, etc.
- Streaming: HTTP, HTTPS, RTMP, RTSP, etc.
- Listas: M3U, M3U8, PLS