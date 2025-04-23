"""
Aplicación TV-IP con CustomTkinter - Interfaz moderna y personalizable
"""
import os
import sys
import subprocess
import tkinter as tk
import customtkinter as ctk
from PIL import Image, ImageTk
from tkinter import filedialog, messagebox

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

# Configuración de apariencia de CustomTkinter
ctk.set_appearance_mode("dark")  # Modos: "dark", "light", "system"
ctk.set_default_color_theme("blue")  # Temas: "blue", "green", "dark-blue"

class OverlayButton(ctk.CTkButton):
    """Botón flotante para el menú contextual"""
    def __init__(self, master, **kwargs):
        super().__init__(master, **kwargs)
        self.configure(
            text="≡",
            font=ctk.CTkFont(size=20, weight="bold"),
            fg_color="transparent",
            border_width=1,
            border_color="#FF8000",
            hover_color=("gray75", "gray25"),
            width=30,
            height=30,
            corner_radius=15
        )

class CustomTkinterApp:
    """Aplicación principal de TV-IP usando CustomTkinter"""
    
    def __init__(self, root):
        self.root = root
        self.root.title("TV-IP Player")
        self.root.geometry("1200x700")
        self.root.minsize(900, 600)
        
        # Variables para control de UI
        self.sidebar_visible = True
        self.is_fullscreen = False
        self.sidebar_width = 300
        
        # Inicializar componentes de backend
        try:
            self.playlist_manager = PlaylistManager()
            self.media_player = MediaPlayer()
            self.selected_channel = None
            self.vlc_process = None
        except Exception as e:
            print(f"Error al inicializar componentes: {e}")
            messagebox.showerror("Error", f"Error de inicialización: {str(e)}")
        
        # Configurar la interfaz de usuario
        self.setup_ui()
        
        # Cargar canales iniciales
        self.update_channel_list()
        
    def setup_ui(self):
        """Configura la interfaz de usuario"""
        # Frame principal
        self.main_frame = ctk.CTkFrame(self.root)
        self.main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Crear barra superior
        self.create_top_bar()
        
        # Crear layout principal (sidebar + área de contenido)
        self.content_frame = ctk.CTkFrame(self.main_frame)
        self.content_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=(0, 10))
        
        # Crear sidebar
        self.create_sidebar()
        
        # Crear área de video
        self.create_video_area()
        
        # Crear controles de reproducción
        self.create_playback_controls()
        
    def create_top_bar(self):
        """Crea la barra superior de la aplicación"""
        self.top_bar = ctk.CTkFrame(self.main_frame, height=40)
        self.top_bar.pack(fill=tk.X, padx=10, pady=10)
        
        # Título de la aplicación
        title_label = ctk.CTkLabel(
            self.top_bar, 
            text="TV-IP Player", 
            font=ctk.CTkFont(size=20, weight="bold")
        )
        title_label.pack(side=tk.LEFT, padx=10)
        
        # Botón de configuración
        settings_button = ctk.CTkButton(
            self.top_bar,
            text="",
            width=30,
            image=self.load_image("settings.png", (20, 20)),
            command=self.show_settings
        )
        settings_button.pack(side=tk.RIGHT, padx=10)
        
    def create_sidebar(self):
        """Crea el panel lateral con la lista de canales"""
        # Frame del sidebar
        self.sidebar = ctk.CTkFrame(self.content_frame, width=self.sidebar_width)
        self.sidebar.pack(side=tk.LEFT, fill=tk.Y, padx=(0, 10))
        self.sidebar.pack_propagate(False)  # Evitar que el sidebar se redimensione
        
        # Etiqueta de canales
        channels_label = ctk.CTkLabel(
            self.sidebar,
            text="Canales",
            font=ctk.CTkFont(size=16, weight="bold")
        )
        channels_label.pack(pady=(10, 5), padx=10, anchor=tk.W)
        
        # Filtro de grupos
        self.group_filter = ctk.CTkComboBox(
            self.sidebar,
            values=["Todos los grupos"],
            command=self.filter_channels_by_group
        )
        self.group_filter.pack(fill=tk.X, padx=10, pady=5)
        
        # Lista de canales
        self.channels_frame = ctk.CTkScrollableFrame(self.sidebar)
        self.channels_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        # Botones de control
        buttons_frame = ctk.CTkFrame(self.sidebar)
        buttons_frame.pack(fill=tk.X, padx=10, pady=10)
        
        # Botón para cargar lista
        load_button = ctk.CTkButton(
            buttons_frame,
            text="Cargar Lista M3U",
            command=self.load_playlist_dialog
        )
        load_button.pack(side=tk.LEFT, padx=5, pady=5, fill=tk.X, expand=True)
        
        # Botón para cargar demo
        demo_button = ctk.CTkButton(
            buttons_frame,
            text="Cargar Demo",
            command=self.load_demo_channels
        )
        demo_button.pack(side=tk.RIGHT, padx=5, pady=5, fill=tk.X, expand=True)
        
    def create_video_area(self):
        """Crea el área de reproducción de video"""
        # Frame para el área de video
        self.video_frame = ctk.CTkFrame(self.content_frame, fg_color="black")
        self.video_frame.pack(side=tk.TOP, fill=tk.BOTH, expand=True)
        
        # Etiqueta para mostrar información del canal
        self.video_info = ctk.CTkLabel(
            self.video_frame,
            text="Selecciona un canal para reproducir",
            font=ctk.CTkFont(size=16),
            text_color="white"
        )
        self.video_info.pack(expand=True)
        
        # Botón flotante para el menú contextual
        self.menu_button = OverlayButton(
            self.video_frame,
            command=self.show_context_menu
        )
        self.menu_button.place(x=10, y=10)
        
        # Configurar eventos de clic derecho
        self.video_frame.bind("<Button-3>", self.on_right_click)
        
    def create_playback_controls(self):
        """Crea los controles de reproducción"""
        self.controls_frame = ctk.CTkFrame(self.content_frame)
        self.controls_frame.pack(side=tk.BOTTOM, fill=tk.X, pady=(10, 0))
        
        # Botón de reproducción
        play_button = ctk.CTkButton(
            self.controls_frame,
            text="Reproducir",
            width=100,
            command=self.play_media
        )
        play_button.pack(side=tk.LEFT, padx=10, pady=10)
        
        # Botón de pausa
        pause_button = ctk.CTkButton(
            self.controls_frame,
            text="Pausar",
            width=100,
            command=self.pause_media
        )
        pause_button.pack(side=tk.LEFT, padx=10, pady=10)
        
        # Botón de detener
        stop_button = ctk.CTkButton(
            self.controls_frame,
            text="Detener",
            width=100,
            command=self.stop_media
        )
        stop_button.pack(side=tk.LEFT, padx=10, pady=10)
        
        # Botón de pantalla completa
        fullscreen_button = ctk.CTkButton(
            self.controls_frame,
            text="Pantalla Completa",
            width=120,
            command=self.toggle_fullscreen
        )
        fullscreen_button.pack(side=tk.RIGHT, padx=10, pady=10)
        
    def update_channel_list(self):
        """Actualiza la lista de canales desde el playlist manager"""
        # Limpiar la lista actual
        for widget in self.channels_frame.winfo_children():
            widget.destroy()
            
        # Actualizar el filtro de grupos
        groups = ["Todos los grupos"] + self.playlist_manager.groups
        self.group_filter.configure(values=groups)
        
        # Añadir canales a la lista
        for channel in self.playlist_manager.channels:
            channel_button = ctk.CTkButton(
                self.channels_frame,
                text=channel.name,
                anchor="w",
                height=30,
                fg_color="transparent",
                text_color=("gray10", "gray90"),
                hover_color=("gray70", "gray30"),
                command=lambda ch=channel: self.select_channel(ch)
            )
            channel_button.pack(fill=tk.X, padx=5, pady=2)
            
        if not self.playlist_manager.channels:
            no_channels_label = ctk.CTkLabel(
                self.channels_frame,
                text="No hay canales disponibles",
                text_color=("gray50", "gray70")
            )
            no_channels_label.pack(pady=20)
            
    def filter_channels_by_group(self, group):
        """Filtra los canales por grupo"""
        # Implementar filtrado de canales
        pass
        
    def load_playlist_dialog(self):
        """Muestra diálogo para cargar una lista M3U"""
        file_path = filedialog.askopenfilename(
            title="Seleccionar archivo M3U",
            filetypes=[("Archivos M3U", "*.m3u *.m3u8"), ("Todos los archivos", "*.*")]
        )
        
        if file_path:
            try:
                # Mostrar diálogo de progreso
                progress_window = ctk.CTkToplevel(self.root)
                progress_window.title("Cargando lista")
                progress_window.geometry("300x100")
                progress_window.transient(self.root)
                progress_window.grab_set()
                
                progress_label = ctk.CTkLabel(progress_window, text="Cargando lista de canales...")
                progress_label.pack(pady=10)
                
                progress_bar = ctk.CTkProgressBar(progress_window)
                progress_bar.pack(pady=10, padx=20, fill=tk.X)
                progress_bar.set(0)
                
                # Función de actualización de progreso
                def update_progress(percent, channels_count):
                    progress_bar.set(percent / 100)
                    progress_label.configure(text=f"Cargando: {channels_count} canales ({percent}%)")
                    progress_window.update()
                
                # Cargar la lista
                self.playlist_manager.load_playlist(file_path, update_progress)
                
                # Cerrar ventana de progreso
                progress_window.destroy()
                
                # Actualizar la UI
                self.update_channel_list()
                
                # Mostrar mensaje de éxito
                messagebox.showinfo("Lista cargada", f"Lista cargada: {len(self.playlist_manager.channels)} canales")
                
            except Exception as e:
                messagebox.showerror("Error", f"Error al cargar lista: {str(e)}")
                
    def load_demo_channels(self):
        """Carga canales de demostración para pruebas"""
        try:
            # Crear canales de ejemplo con URLs reales y locales
            self.playlist_manager.channels = [
                Channel(name="Big Buck Bunny (MP4)", 
                       url="https://commondatastorage.googleapis.com/gtv-videos-bucket/sample/BigBuckBunny.mp4", 
                       group="Demos"),
                Channel(name="Elephant Dream (MP4)", 
                       url="https://commondatastorage.googleapis.com/gtv-videos-bucket/sample/ElephantsDream.mp4", 
                       group="Demos"),
                Channel(name="Ejemplo IPTV (M3U)", 
                       url="http://iptv-org.github.io/iptv/countries/us.m3u", 
                       group="Demos"),
                Channel(name="Video Local (si existe)", 
                       url="C:/Users/Public/Videos/Sample Videos/Wildlife.wmv", 
                       group="Demos"),
            ]
            self.playlist_manager.groups = ["Demos"]
            
            # Actualizar la UI
            self.update_channel_list()
            
            # Mostrar mensaje de éxito
            messagebox.showinfo("Demo cargada", f"Lista demo cargada: {len(self.playlist_manager.channels)} canales")
            
        except Exception as e:
            messagebox.showerror("Error", f"Error al cargar canales demo: {str(e)}")
            
    def select_channel(self, channel):
        """Selecciona un canal para reproducir"""
        try:
            # Detener reproducción actual si hay alguna
            self.stop_media()
            
            self.selected_channel = channel
            
            # Actualizar información en el área de video
            self.video_info.configure(
                text=f"Canal: {channel.name}\nURL: {channel.url}"
            )
            
            # Mostrar mensaje
            messagebox.showinfo("Canal seleccionado", f"Canal seleccionado: {channel.name}")
            
        except Exception as e:
            messagebox.showerror("Error", f"Error al seleccionar canal: {str(e)}")
            
    def play_media(self):
        """Reproduce el medio actual usando múltiples métodos"""
        if not self.selected_channel:
            messagebox.showerror("Error", "No hay canal seleccionado para reproducir")
            return
            
        try:
            # Detener cualquier reproducción actual
            self.stop_media()
            
            # Obtener la URL del canal
            url = self.selected_channel.url
            print(f"Reproduciendo: {url}")
            
            # Intentar todos los métodos posibles de reproducción
            
            # Método 1: Usar python-vlc (integrado)
            try:
                print("Método 1: Intentando con python-vlc integrado")
                import vlc
                
                # Crear una instancia de VLC
                instance = vlc.Instance()
                self.vlc_player = instance.media_player_new()
                media = instance.media_new(url)
                self.vlc_player.set_media(media)
                
                # Reproducir
                result = self.vlc_player.play()
                print(f"Resultado de reproducción: {result}")
                
                # Actualizar información
                self.video_info.configure(
                    text=f"Reproduciendo: {self.selected_channel.name}\nURL: {url}\n\nReproduciendo con python-vlc integrado"
                )
                
                messagebox.showinfo("Reproduciendo", f"Reproduciendo: {self.selected_channel.name}")
                return
            except Exception as e:
                print(f"Error con python-vlc: {e}")
            
            # Método 2: Usar VLC externo directamente
            try:
                print("Método 2: Intentando con VLC externo")
                vlc_path = self.find_vlc_path()
                if vlc_path and os.path.exists(vlc_path):
                    print(f"VLC encontrado en: {vlc_path}")
                    cmd = f'"{vlc_path}" "{url}"'
                    print(f"Ejecutando: {cmd}")
                    
                    self.vlc_process = subprocess.Popen(
                        cmd,
                        shell=True,
                        stdout=subprocess.PIPE,
                        stderr=subprocess.PIPE
                    )
                    
                    # Actualizar información
                    self.video_info.configure(
                        text=f"Reproduciendo: {self.selected_channel.name}\nURL: {url}\n\nReproduciendo con VLC externo"
                    )
                    
                    messagebox.showinfo("Reproduciendo", f"Reproduciendo: {self.selected_channel.name}")
                    return
            except Exception as e:
                print(f"Error con VLC externo: {e}")
            
            # Método 3: Usar os.startfile (solo Windows)
            if sys.platform.startswith('win'):
                try:
                    print("Método 3: Intentando con os.startfile")
                    os.startfile(url)
                    
                    # Actualizar información
                    self.video_info.configure(
                        text=f"Reproduciendo: {self.selected_channel.name}\nURL: {url}\n\nReproduciendo con programa predeterminado"
                    )
                    
                    messagebox.showinfo("Reproduciendo", f"Reproduciendo: {self.selected_channel.name}")
                    return
                except Exception as e:
                    print(f"Error con os.startfile: {e}")
            
            # Método 4: Usar comando start (solo Windows)
            if sys.platform.startswith('win'):
                try:
                    print("Método 4: Intentando con comando start")
                    cmd = f'start "" "{url}"'
                    print(f"Ejecutando: {cmd}")
                    
                    subprocess.Popen(cmd, shell=True)
                    
                    # Actualizar información
                    self.video_info.configure(
                        text=f"Reproduciendo: {self.selected_channel.name}\nURL: {url}\n\nReproduciendo con comando start"
                    )
                    
                    messagebox.showinfo("Reproduciendo", f"Reproduciendo: {self.selected_channel.name}")
                    return
                except Exception as e:
                    print(f"Error con comando start: {e}")
            
            # Método 5: Abrir en navegador
            try:
                print("Método 5: Intentando abrir en navegador")
                import webbrowser
                webbrowser.open(url)
                
                # Actualizar información
                self.video_info.configure(
                    text=f"Reproduciendo: {self.selected_channel.name}\nURL: {url}\n\nAbriendo en navegador web"
                )
                
                messagebox.showinfo("Reproduciendo", f"Abriendo en navegador: {self.selected_channel.name}")
                return
            except Exception as e:
                print(f"Error al abrir en navegador: {e}")
            
            # Si llegamos aquí, ningún método funcionó
            messagebox.showerror("Error", "No se pudo reproducir el video con ningún método disponible")
            
        except Exception as e:
            print(f"Error general al reproducir: {e}")
            messagebox.showerror("Error", f"Error al reproducir: {str(e)}")
    
    def find_vlc_path(self):
        """Encuentra la ruta al ejecutable de VLC"""
        # Posibles rutas de VLC en diferentes sistemas operativos
        vlc_paths = {
            'win32': [
                r'C:\Program Files\VideoLAN\VLC\vlc.exe',
                r'C:\Program Files (x86)\VideoLAN\VLC\vlc.exe',
            ],
            'darwin': [  # macOS
                '/Applications/VLC.app/Contents/MacOS/VLC',
            ],
            'linux': [
                '/usr/bin/vlc',
                '/usr/local/bin/vlc',
            ]
        }
        
        # Primero intentar con el comando 'where' o 'which'
        try:
            if sys.platform.startswith('win'):
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
        platform_key = None
        for key in vlc_paths.keys():
            if sys.platform.startswith(key):
                platform_key = key
                break
                
        if platform_key:
            for path in vlc_paths[platform_key]:
                if os.path.exists(path):
                    print(f"VLC encontrado en: {path}")
                    return path
        
        # Si no se encuentra, devolver simplemente 'vlc' y esperar que funcione
        print("No se encontró VLC, usando comando 'vlc' por defecto")
        return 'vlc'
    
    def pause_media(self):
        """Pausa la reproducción"""
        messagebox.showinfo("Pausa", "La pausa no está disponible para VLC externo")
        
    def stop_media(self):
        """Detiene la reproducción"""
        if self.vlc_process:
            try:
                self.vlc_process.terminate()
                self.vlc_process = None
                
                if self.selected_channel:
                    # Restaurar la vista del canal
                    self.video_info.configure(
                        text=f"Canal: {self.selected_channel.name}\nURL: {self.selected_channel.url}"
                    )
                else:
                    # Restaurar la vista por defecto
                    self.video_info.configure(
                        text="Selecciona un canal para reproducir"
                    )
                
            except Exception as e:
                print(f"Error al detener VLC: {e}")
                
    def show_context_menu(self):
        """Muestra el menú contextual desde el botón flotante"""
        self.create_context_menu(self.menu_button.winfo_rootx(), self.menu_button.winfo_rooty() + 30)
        
    def on_right_click(self, event):
        """Maneja el clic derecho en el área de video"""
        self.create_context_menu(event.x_root, event.y_root)
        
    def create_context_menu(self, x, y):
        """Crea y muestra el menú contextual en las coordenadas especificadas"""
        context_menu = tk.Menu(self.root, tearoff=0, bg="#404040", fg="white", activebackground="#606060", activeforeground="white")
        
        # Opción de pantalla completa
        context_menu.add_command(label="Pantalla Completa", command=self.toggle_fullscreen)
        
        # Opciones de escala de video
        scale_menu = tk.Menu(context_menu, tearoff=0, bg="#404040", fg="white", activebackground="#606060", activeforeground="white")
        scales = {
            'Ajuste Original (1.0x)': 1.0,
            'Ajuste a Ventana (0.5x)': 0.5,
            'Ajuste Doble (2.0x)': 2.0
        }
        for name, scale in scales.items():
            scale_menu.add_command(label=name, command=lambda s=scale: self.set_scale_mode(s))
        context_menu.add_cascade(label="Escala de Video", menu=scale_menu)
        
        # Opciones de relación de aspecto
        aspect_menu = tk.Menu(context_menu, tearoff=0, bg="#404040", fg="white", activebackground="#606060", activeforeground="white")
        aspect_ratios = {
            'Auto': '',
            '16:9': '16:9',
            '4:3': '4:3',
            '1:1': '1:1',
            '16:10': '16:10',
            '2.35:1 (Cinemascope)': '2.35:1'
        }
        for name, ratio in aspect_ratios.items():
            aspect_menu.add_command(label=name, command=lambda r=ratio: self.set_aspect_ratio(r))
        context_menu.add_cascade(label="Relación de Aspecto", menu=aspect_menu)
        
        # Opciones de pistas de audio (si está reproduciendo)
        if self.vlc_process and self.media_player.is_playing():
            audio_tracks = self.media_player.get_audio_tracks()
            if audio_tracks and len(audio_tracks) > 1:
                audio_menu = tk.Menu(context_menu, tearoff=0, bg="#404040", fg="white", activebackground="#606060", activeforeground="white")
                current_track = self.media_player.get_current_audio_track()
                for track_id, name in audio_tracks:
                    if isinstance(name, bytes):
                        track_name = name.decode('utf-8', errors='ignore')
                    elif isinstance(name, str):
                        track_name = name
                    else:
                        track_name = f"Pista {track_id}"
                    audio_menu.add_command(label=track_name, command=lambda tid=track_id: self.change_audio_track(tid))
                context_menu.add_cascade(label="Pistas de Audio", menu=audio_menu)
        
        # Mostrar el menú en la posición especificada
        context_menu.tk_popup(x, y)
        
    def toggle_fullscreen(self):
        """Alterna entre modo pantalla completa y ventana normal"""
        self.is_fullscreen = not self.is_fullscreen
        self.root.attributes("-fullscreen", self.is_fullscreen)
        if not self.is_fullscreen:
            # Restaurar el tamaño normal
            self.root.geometry("1200x700")
            
    def set_scale_mode(self, scale):
        """Cambia la escala de video"""
        if self.media_player.is_playing():
            self.media_player.set_scale_mode(scale)
            messagebox.showinfo("Escala", f"Escala cambiada a: {scale}x")
        else:
            messagebox.showinfo("Escala", "No hay video reproduciéndose")
            
    def set_aspect_ratio(self, aspect_ratio):
        """Cambia la relación de aspecto del video"""
        if self.media_player.is_playing():
            self.media_player.set_aspect_ratio(aspect_ratio)
            messagebox.showinfo("Aspecto", f"Relación de aspecto cambiada a: {aspect_ratio}")
        else:
            messagebox.showinfo("Aspecto", "No hay video reproduciéndose")
            
    def change_audio_track(self, track_id):
        """Cambia la pista de audio"""
        if self.media_player.is_playing():
            self.media_player.change_audio_track(track_id)
            messagebox.showinfo("Audio", f"Pista de audio cambiada a: {track_id}")
        else:
            messagebox.showinfo("Audio", "No hay video reproduciéndose")
            
    def show_settings(self):
        """Muestra la pantalla de configuración"""
        settings_window = ctk.CTkToplevel(self.root)
        settings_window.title("Configuración")
        settings_window.geometry("400x300")
        settings_window.transient(self.root)
        settings_window.grab_set()
        
        # Contenido de la ventana de configuración
        settings_frame = ctk.CTkFrame(settings_window)
        settings_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        
        # Título
        title_label = ctk.CTkLabel(
            settings_frame,
            text="Configuración",
            font=ctk.CTkFont(size=20, weight="bold")
        )
        title_label.pack(pady=(0, 20))
        
        # Opciones de apariencia
        appearance_label = ctk.CTkLabel(
            settings_frame,
            text="Apariencia:",
            font=ctk.CTkFont(size=14, weight="bold")
        )
        appearance_label.pack(anchor=tk.W, pady=(10, 5))
        
        appearance_var = ctk.StringVar(value=ctk.get_appearance_mode())
        appearance_combobox = ctk.CTkComboBox(
            settings_frame,
            values=["dark", "light", "system"],
            variable=appearance_var,
            command=self.change_appearance_mode
        )
        appearance_combobox.pack(fill=tk.X, pady=(0, 10))
        
        # Botón para cerrar
        close_button = ctk.CTkButton(
            settings_frame,
            text="Cerrar",
            command=settings_window.destroy
        )
        close_button.pack(pady=20)
        
    def change_appearance_mode(self, mode):
        """Cambia el modo de apariencia de la aplicación"""
        ctk.set_appearance_mode(mode)
        
    def load_image(self, image_name, size):
        """Carga una imagen desde la carpeta de recursos"""
        try:
            # Intentar cargar desde la carpeta de recursos
            resources_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "resources")
            if not os.path.exists(resources_dir):
                os.makedirs(resources_dir)
                
            image_path = os.path.join(resources_dir, image_name)
            
            # Si la imagen no existe, devolver None
            if not os.path.exists(image_path):
                return None
                
            return ctk.CTkImage(Image.open(image_path), size=size)
        except Exception as e:
            print(f"Error al cargar imagen {image_name}: {e}")
            return None

def main():
    """Función principal para iniciar la aplicación CustomTkinter"""
    root = ctk.CTk()
    app = CustomTkinterApp(root)
    root.mainloop()

# Si se ejecuta directamente este archivo
if __name__ == "__main__":
    main()
