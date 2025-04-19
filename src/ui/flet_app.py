"""
Aplicación Flet para TV-IP - Interfaz multiplataforma moderna
"""
import os
import subprocess
import platform
import flet as ft
from flet import (
    Page, AppBar, ElevatedButton, Text, ListView, Container, 
    Column, Row, IconButton, Dropdown, dropdown, 
    PopupMenuButton, PopupMenuItem, colors, icons, margin, padding, border, alignment
)

# Importamos los módulos del núcleo
try:
    from src.core.media_player import MediaPlayer
    from src.core.playlist_manager import PlaylistManager, Channel
except ImportError:
    # Por si ejecutamos standalone
    import sys
    sys.path.append(os.path.join(os.path.dirname(__file__), '../..'))
    from src.core.media_player import MediaPlayer
    from src.core.playlist_manager import PlaylistManager, Channel

# Posibles rutas de VLC en diferentes sistemas operativos
VLC_PATHS = {
    'Windows': [
        r'C:\Program Files\VideoLAN\VLC\vlc.exe',
        r'C:\Program Files (x86)\VideoLAN\VLC\vlc.exe',
    ],
    'Darwin': [  # macOS
        '/Applications/VLC.app/Contents/MacOS/VLC',
    ],
    'Linux': [
        '/usr/bin/vlc',
        '/usr/local/bin/vlc',
    ]
}

def find_vlc_path():
    """Encuentra la ruta al ejecutable de VLC"""
    # Primero intentar con el comando 'where' o 'which'
    try:
        if platform.system() == 'Windows':
            result = subprocess.run(['where', 'vlc'], capture_output=True, text=True)
            if result.returncode == 0 and result.stdout.strip():
                return result.stdout.strip().split('\n')[0]
        else:
            result = subprocess.run(['which', 'vlc'], capture_output=True, text=True)
            if result.returncode == 0 and result.stdout.strip():
                return result.stdout.strip()
    except Exception as e:
        print(f"Error al buscar VLC en PATH: {e}")
    
    # Si no se encuentra, buscar en las rutas predefinidas
    system = platform.system()
    if system in VLC_PATHS:
        for path in VLC_PATHS[system]:
            if os.path.exists(path):
                print(f"VLC encontrado en: {path}")
                return path
    
    # Si no se encuentra, devolver simplemente 'vlc' y esperar que funcione
    print("No se encontró VLC, usando comando 'vlc' por defecto")
    return 'vlc'

class FletTVApp:
    """Aplicación principal de TV-IP usando Flet"""
    
    def __init__(self, page: Page):
        self.page = page
        self.page.title = "TV-IP Player"
        self.page.theme_mode = ft.ThemeMode.DARK
        self.page.padding = 0
        
        # Encontrar ruta de VLC
        self.vlc_path = find_vlc_path()
        print(f"Usando VLC en: {self.vlc_path}")
        
        # Inicializar componentes de backend
        try:
            self.playlist_manager = PlaylistManager()
            self.media_player = MediaPlayer()
            self.selected_channel = None
            self.vlc_process = None
            print(f"PlaylistManager inicializado, canales: {len(self.playlist_manager.channels)}")
        except Exception as e:
            print(f"Error al inicializar componentes: {e}")
            self.show_error(f"Error de inicialización: {str(e)}")
        
        # Crear file picker y añadirlo a la página
        self.file_picker = ft.FilePicker(on_result=self.on_file_picker_result)
        self.page.overlay.append(self.file_picker)
        self.page.update()
        
        # Componentes de UI
        self.setup_ui()
        
    def setup_ui(self):
        """Configura la interfaz de usuario"""
        # Barra superior
        self.app_bar = AppBar(
            title=Text("TV-IP Player", size=20, weight="bold"),
            center_title=True,
            bgcolor=colors.BLUE_GREY_900,
            actions=[
                IconButton(
                    icon=icons.SETTINGS,
                    tooltip="Configuración",
                    on_click=self.show_settings
                ),
            ],
        )
        
        # Área de video (simulada)
        self.video_area = Container(
            content=Column([
                Text("Área de Video", size=16, weight="bold"),
                Text("Selecciona un canal para reproducir", size=14),
            ], alignment=ft.MainAxisAlignment.CENTER),
            alignment=alignment.center,
            bgcolor=colors.BLACK,
            border_radius=10,
            padding=20,
            expand=True,
        )
        
        # Botón flotante de menú en la esquina superior izquierda
        self.menu_float_button = IconButton(
            icon=icons.MENU,
            icon_color=colors.WHITE,
            bgcolor=colors.BLUE_GREY_800,
            icon_size=20,
            tooltip="Menú contextual",
            on_click=self.show_context_menu
        )
        
        # Botón de menú contextual
        self.menu_button = PopupMenuButton(
            icon=icons.MENU,
            tooltip="Opciones de reproducción",
            items=[
                PopupMenuItem(
                    text="Pantalla Completa",
                    icon=icons.FULLSCREEN,
                    on_click=self.toggle_fullscreen
                ),
                PopupMenuItem(
                    text="Escala de Video",
                    icon=icons.ASPECT_RATIO,
                    on_click=self.change_scale
                ),
                PopupMenuItem(
                    text="Relación de Aspecto",
                    icon=icons.CROP,
                    on_click=self.change_aspect
                ),
                PopupMenuItem(
                    text="Cambiar Audio",
                    icon=icons.AUDIOTRACK,
                    on_click=self.change_audio
                ),
            ],
        )
        
        # Lista de canales
        self.channels_list = ListView(
            expand=1,
            spacing=2,
            padding=10,
            auto_scroll=True
        )
        
        # Botón para cargar lista
        self.load_button = ElevatedButton(
            "Cargar Lista M3U",
            icon=icons.PLAYLIST_ADD,
            on_click=self.load_playlist_dialog,
        )
        
        # Botón para cargar lista de ejemplo (para pruebas)
        self.load_demo_button = ElevatedButton(
            "Cargar Demo",
            icon=icons.PLAYLIST_PLAY,
            on_click=self.load_demo_channels,
        )
        
        # Sidebar con lista de canales
        self.sidebar = Container(
            content=Column([
                Container(
                    content=Text("Canales", size=16, weight="bold"),
                    bgcolor=colors.BLUE_GREY_800,
                    padding=10,
                    border_radius=ft.border_radius.only(top_left=10, top_right=10),
                ),
                self.channels_list,
                Row([
                    self.load_button,
                    self.load_demo_button,
                ], alignment=ft.MainAxisAlignment.CENTER),
            ]),
            width=300,
            bgcolor=colors.BLUE_GREY_900,
            border_radius=10,
            padding=padding.only(bottom=10),
            margin=10,
        )
        
        # Controles de reproducción
        self.controls = Row(
            [
                IconButton(
                    icon=icons.PLAY_ARROW,
                    tooltip="Reproducir",
                    on_click=self.play_media
                ),
                IconButton(
                    icon=icons.PAUSE,
                    tooltip="Pausar",
                    on_click=self.pause_media
                ),
                IconButton(
                    icon=icons.STOP,
                    tooltip="Detener",
                    on_click=self.stop_media
                ),
                Container(width=20),  # Espaciador
                self.menu_button,
            ],
            alignment=ft.MainAxisAlignment.CENTER,
        )
        
        # Área de video con botón flotante
        video_stack = ft.Stack([
            self.video_area,
            Container(
                content=self.menu_float_button,
                alignment=alignment.top_left,
                margin=10
            )
        ])
        
        # Layout principal
        self.page.add(
            self.app_bar,
            Row(
                [
                    self.sidebar,
                    Container(
                        content=Column([
                            video_stack,
                            self.controls,
                        ]),
                        expand=True,
                        margin=10,
                    ),
                ],
                expand=True,
            ),
        )
        
        # Cargar canales iniciales
        self.update_channel_list()
    
    def show_context_menu(self, e):
        """Muestra el menú contextual desde el botón flotante"""
        # Crear un menú contextual en la posición del botón
        menu = ft.PopupMenuButton(
            items=[
                PopupMenuItem(
                    text="Pantalla Completa",
                    icon=icons.FULLSCREEN,
                    on_click=self.toggle_fullscreen
                ),
                PopupMenuItem(
                    text="Escala de Video",
                    icon=icons.ASPECT_RATIO,
                    on_click=self.change_scale
                ),
                PopupMenuItem(
                    text="Relación de Aspecto",
                    icon=icons.CROP,
                    on_click=self.change_aspect
                ),
                PopupMenuItem(
                    text="Cambiar Audio",
                    icon=icons.AUDIOTRACK,
                    on_click=self.change_audio
                ),
            ],
        )
        # Mostrar el menú
        menu.open = True
        self.page.update()
    
    def update_channel_list(self):
        """Actualiza la lista de canales desde el playlist manager"""
        try:
            self.channels_list.controls.clear()
            
            print(f"Actualizando lista de canales: {len(self.playlist_manager.channels)} canales")
            
            for channel in self.playlist_manager.channels:
                try:
                    channel_item = Container(
                        content=Text(channel.name, size=14),
                        padding=10,
                        border_radius=5,
                        bgcolor=colors.BLUE_GREY_700,
                        on_click=lambda e, ch=channel: self.select_channel(ch),
                        data=channel,  # Almacenamos el canal como data
                    )
                    self.channels_list.controls.append(channel_item)
                except Exception as e:
                    print(f"Error al añadir canal {channel.name}: {e}")
            
            if not self.playlist_manager.channels:
                self.channels_list.controls.append(
                    Text("No hay canales disponibles", italic=True, color=colors.GREY_400)
                )
            
            self.page.update()
            print(f"Lista de canales actualizada con {len(self.channels_list.controls)} elementos")
        except Exception as e:
            print(f"Error al actualizar lista de canales: {e}")
            self.show_error(f"Error al actualizar lista: {str(e)}")
    
    def load_demo_channels(self, e):
        """Carga canales de demostración para pruebas"""
        try:
            # Crear canales de ejemplo con URLs reales
            self.playlist_manager.channels = [
                Channel(name="Ejemplo IPTV 1", url="http://iptv-org.github.io/iptv/countries/us.m3u", group="Demos"),
                Channel(name="Big Buck Bunny", url="https://commondatastorage.googleapis.com/gtv-videos-bucket/sample/BigBuckBunny.mp4", group="Demos"),
                Channel(name="Elephant Dream", url="https://commondatastorage.googleapis.com/gtv-videos-bucket/sample/ElephantsDream.mp4", group="Demos"),
            ]
            self.playlist_manager.groups = ["Demos"]
            
            # Actualizar la UI
            self.update_channel_list()
            
            # Mostrar mensaje de éxito
            self.page.snack_bar = ft.SnackBar(
                content=Text(f"Lista demo cargada: {len(self.playlist_manager.channels)} canales"),
                action="Ok",
            )
            self.page.snack_bar.open = True
            self.page.update()
        except Exception as e:
            self.show_error(f"Error al cargar canales demo: {str(e)}")
    
    def select_channel(self, channel):
        """Selecciona un canal para reproducir"""
        try:
            # Detener reproducción actual si hay alguna
            self.stop_media(None)
            
            self.selected_channel = channel
            
            # Actualizar área de video con información del canal
            self.video_area.content = Column([
                Text(f"Canal: {channel.name}", size=16, weight="bold"),
                Text(f"URL: {channel.url}", size=12, selectable=True),
                Row([
                    ElevatedButton(
                        "Reproducir",
                        icon=icons.PLAY_CIRCLE,
                        on_click=self.play_media
                    ),
                    ElevatedButton(
                        "Reproducir en VLC externo",
                        icon=icons.OPEN_IN_NEW,
                        on_click=lambda e: self.play_in_external_vlc(channel.url)
                    ),
                ], alignment=ft.MainAxisAlignment.CENTER),
            ], alignment=ft.MainAxisAlignment.CENTER)
            
            self.page.update()
            
            # Notificar selección
            self.page.snack_bar = ft.SnackBar(
                content=Text(f"Canal seleccionado: {channel.name}"),
                action="Ok",
            )
            self.page.snack_bar.open = True
            self.page.update()
        except Exception as e:
            self.show_error(f"Error al seleccionar canal: {str(e)}")
    
    def play_in_external_vlc(self, url):
        """Reproduce la URL en VLC externo"""
        try:
            # Detener cualquier reproducción actual
            self.stop_media(None)
            
            # Lanzar VLC externo con la ruta encontrada
            print(f"Lanzando VLC externo con URL: {url}")
            
            # Usar la ruta de VLC encontrada
            cmd = [self.vlc_path, url]
            print(f"Comando: {cmd}")
            
            # Usar shell=True para Windows
            self.vlc_process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE, 
                stderr=subprocess.PIPE,
                text=True,
                shell=True if platform.system() == 'Windows' else False
            )
            
            # Verificar si VLC se inició correctamente
            return_code = self.vlc_process.poll()
            if return_code is not None:
                # VLC terminó inmediatamente, lo que indica un error
                stdout, stderr = self.vlc_process.communicate()
                print(f"VLC salió con código: {return_code}")
                print(f"Salida estándar: {stdout}")
                print(f"Error estándar: {stderr}")
                self.show_error(f"Error al iniciar VLC. Código: {return_code}")
                return
            
            self.page.snack_bar = ft.SnackBar(
                content=Text("Reproduciendo en VLC externo"),
                action="Ok",
            )
            self.page.snack_bar.open = True
            self.page.update()
        except Exception as e:
            print(f"Error al lanzar VLC: {e}")
            self.show_error(f"Error al lanzar VLC: {str(e)}")
    
    def load_playlist_dialog(self, e):
        """Muestra diálogo para cargar una lista M3U"""
        try:
            # Mostrar el selector de archivos directamente
            self.file_picker.pick_files(
                dialog_title="Seleccionar archivo M3U",
                allowed_extensions=["m3u", "m3u8"],
                allow_multiple=False
            )
        except Exception as e:
            print(f"Error al abrir selector de archivos: {e}")
            self.show_error(f"Error al abrir selector de archivos: {str(e)}")
    
    def on_file_picker_result(self, e: ft.FilePickerResultEvent):
        """Maneja el resultado del selector de archivos"""
        try:
            if e.files and len(e.files) > 0:
                file_path = e.files[0].path
                print(f"Archivo seleccionado: {file_path}")
                
                # Mostrar diálogo de carga
                self.show_loading_dialog("Cargando lista...")
                
                # Cargar la lista
                print(f"Cargando playlist desde: {file_path}")
                self.playlist_manager.load_playlist(file_path)
                print(f"Playlist cargada: {len(self.playlist_manager.channels)} canales")
                
                # Actualizar la UI
                self.update_channel_list()
                
                # Cerrar diálogo de carga
                self.close_dialog()
                
                # Mostrar mensaje de éxito
                self.page.snack_bar = ft.SnackBar(
                    content=Text(f"Lista cargada: {len(self.playlist_manager.channels)} canales"),
                    action="Ok",
                )
                self.page.snack_bar.open = True
                self.page.update()
            else:
                print("No se seleccionó ningún archivo")
        except Exception as e:
            print(f"Error al cargar lista: {e}")
            self.close_dialog()
            self.show_error(f"Error al cargar lista: {str(e)}")
    
    def show_loading_dialog(self, message):
        """Muestra un diálogo de carga"""
        dialog = ft.AlertDialog(
            title=Text("Cargando"),
            content=Row([
                ft.ProgressRing(),
                Text(message),
            ], alignment=ft.MainAxisAlignment.CENTER),
        )
        self.page.dialog = dialog
        dialog.open = True
        self.page.update()
    
    def close_dialog(self):
        """Cierra el diálogo actual"""
        if self.page.dialog:
            self.page.dialog.open = False
            self.page.update()
    
    def show_error(self, message):
        """Muestra un mensaje de error"""
        self.page.snack_bar = ft.SnackBar(
            content=Text(message),
            bgcolor=colors.RED_700,
            action="Cerrar",
        )
        self.page.snack_bar.open = True
        self.page.update()
    
    def show_settings(self, e):
        """Muestra la pantalla de configuración"""
        # Crear un diálogo de configuración
        dialog = ft.AlertDialog(
            title=Text("Configuración"),
            content=Column([
                Text("Ruta de VLC:"),
                Row([
                    Text(self.vlc_path, selectable=True),
                    IconButton(
                        icon=icons.EDIT,
                        tooltip="Cambiar ruta",
                        on_click=self.change_vlc_path
                    )
                ]),
                Text("Versión: 1.0.0"),
            ], tight=True, spacing=10),
            actions=[
                ft.TextButton("Cerrar", on_click=lambda e: self.close_dialog())
            ],
        )
        
        self.page.dialog = dialog
        dialog.open = True
        self.page.update()
    
    def change_vlc_path(self, e):
        """Permite al usuario cambiar la ruta de VLC"""
        def close_dlg(e):
            self.page.dialog.open = False
            self.page.update()
        
        def save_path(e):
            new_path = input_field.value
            if os.path.exists(new_path):
                self.vlc_path = new_path
                print(f"Nueva ruta de VLC: {self.vlc_path}")
                close_dlg(e)
                self.show_settings(None)  # Actualizar diálogo de configuración
            else:
                input_field.error_text = "La ruta no existe"
                self.page.update()
        
        input_field = ft.TextField(
            label="Ruta de VLC",
            value=self.vlc_path,
            width=400
        )
        
        dialog = ft.AlertDialog(
            title=Text("Cambiar ruta de VLC"),
            content=Column([
                Text("Introduce la ruta completa al ejecutable de VLC:"),
                input_field,
            ], tight=True, spacing=10),
            actions=[
                ft.TextButton("Cancelar", on_click=close_dlg),
                ft.TextButton("Guardar", on_click=save_path),
            ],
        )
        
        self.page.dialog = dialog
        dialog.open = True
        self.page.update()
    
    def toggle_fullscreen(self, e):
        """Alterna el modo de pantalla completa"""
        self.page.window_full_screen = not self.page.window_full_screen
        self.page.update()
    
    def change_scale(self, e):
        """Cambia la escala de video"""
        self.page.snack_bar = ft.SnackBar(
            content=Text("Cambio de escala (no implementado)"),
            action="Ok",
        )
        self.page.snack_bar.open = True
        self.page.update()
    
    def change_aspect(self, e):
        """Cambia la relación de aspecto"""
        self.page.snack_bar = ft.SnackBar(
            content=Text("Cambio de aspecto (no implementado)"),
            action="Ok",
        )
        self.page.snack_bar.open = True
        self.page.update()
    
    def change_audio(self, e):
        """Cambia la pista de audio"""
        self.page.snack_bar = ft.SnackBar(
            content=Text("Cambio de audio (no implementado)"),
            action="Ok",
        )
        self.page.snack_bar.open = True
        self.page.update()
    
    def play_media(self, e):
        """Reproduce el medio actual usando VLC"""
        if not self.selected_channel:
            self.show_error("No hay canal seleccionado para reproducir")
            return
            
        try:
            # Detener cualquier reproducción actual
            self.stop_media(None)
            
            # Usar VLC para reproducir con la ruta encontrada
            print(f"Reproduciendo: {self.selected_channel.url}")
            print(f"Usando VLC en: {self.vlc_path}")
            
            # Construir el comando
            cmd = [self.vlc_path, self.selected_channel.url]
            print(f"Comando: {cmd}")
            
            # Usar shell=True para Windows
            self.vlc_process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE, 
                stderr=subprocess.PIPE,
                text=True,
                shell=True if platform.system() == 'Windows' else False
            )
            
            # Verificar si VLC se inició correctamente
            return_code = self.vlc_process.poll()
            if return_code is not None:
                # VLC terminó inmediatamente, lo que indica un error
                stdout, stderr = self.vlc_process.communicate()
                print(f"VLC salió con código: {return_code}")
                print(f"Salida estándar: {stdout}")
                print(f"Error estándar: {stderr}")
                self.show_error(f"Error al iniciar VLC. Código: {return_code}")
                return
            
            # Actualizar UI
            self.video_area.content = Column([
                Text(f"Reproduciendo: {self.selected_channel.name}", size=16, weight="bold"),
                Text(f"URL: {self.selected_channel.url}", size=12, selectable=True),
                Text("VLC se ha lanzado para reproducir este canal", size=14),
                Row([
                    ElevatedButton(
                        "Detener",
                        icon=icons.STOP,
                        on_click=self.stop_media
                    ),
                ], alignment=ft.MainAxisAlignment.CENTER),
            ], alignment=ft.MainAxisAlignment.CENTER)
            
            self.page.snack_bar = ft.SnackBar(
                content=Text(f"Reproduciendo: {self.selected_channel.name}"),
                action="Ok",
            )
            self.page.snack_bar.open = True
            self.page.update()
        except Exception as e:
            print(f"Error al reproducir: {e}")
            self.show_error(f"Error al reproducir: {str(e)}")
    
    def pause_media(self, e):
        """Pausa la reproducción"""
        self.page.snack_bar = ft.SnackBar(
            content=Text("La pausa no está disponible para VLC externo"),
            action="Ok",
        )
        self.page.snack_bar.open = True
        self.page.update()
    
    def stop_media(self, e):
        """Detiene la reproducción"""
        if self.vlc_process:
            try:
                print("Deteniendo VLC")
                self.vlc_process.terminate()
                self.vlc_process = None
                
                if self.selected_channel:
                    # Restaurar la vista del canal
                    self.select_channel(self.selected_channel)
                else:
                    # Restaurar la vista por defecto
                    self.video_area.content = Column([
                        Text("Área de Video", size=16, weight="bold"),
                        Text("Selecciona un canal para reproducir", size=14),
                    ], alignment=ft.MainAxisAlignment.CENTER)
                
                if e:  # Solo mostrar mensaje si fue una acción del usuario
                    self.page.snack_bar = ft.SnackBar(
                        content=Text("Reproducción detenida"),
                        action="Ok",
                    )
                    self.page.snack_bar.open = True
                
                self.page.update()
            except Exception as e:
                print(f"Error al detener VLC: {e}")

def main(page: Page):
    """Función principal para iniciar la aplicación Flet"""
    app = FletTVApp(page)

# Si se ejecuta directamente este archivo
if __name__ == "__main__":
    ft.app(target=main)
