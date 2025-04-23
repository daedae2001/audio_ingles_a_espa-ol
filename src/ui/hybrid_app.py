"""
Aplicación híbrida TV-IP con CustomTkinter para UI y PyQt para reproducción de video
"""
import os
import sys
import subprocess
import tkinter as tk
import customtkinter as ctk
from PIL import Image, ImageTk
from tkinter import filedialog, messagebox
import threading
import time

# Importamos PyQt para la reproducción de video
from PyQt6.QtWidgets import QApplication, QMainWindow, QWidget, QVBoxLayout
from PyQt6.QtCore import Qt
import vlc

# Importamos los módulos del núcleo
try:
    from src.core.playlist_manager import PlaylistManager, Channel
except ImportError:
    # Por si ejecutamos standalone
    import sys
    sys.path.append(os.path.join(os.path.dirname(__file__), '../..'))
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

class VideoPlayerWindow(QMainWindow):
    """Ventana de reproducción de video con PyQt y VLC"""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Reproductor de Video")
        self.setGeometry(100, 100, 800, 600)
        
        # Inicializar VLC con opciones específicas
        vlc_args = [
            '--embedded-video',  # Forzar video embebido
            '--no-snapshot-preview',  # Deshabilitar vista previa de capturas
            '--quiet',  # Reducir mensajes de registro
            '--no-video-title-show',  # No mostrar título de video
            '--no-fullscreen',  # Evitar pantalla completa automática
            '--video-on-top',  # Mantener video encima
        ]
        self.instance = vlc.Instance(vlc_args)
        self.player = self.instance.media_player_new()
        
        # Widget central
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # Widget de video
        self.video_widget = QWidget()
        self.video_widget.setStyleSheet("background-color: black;")
        layout.addWidget(self.video_widget)
        
        # Configurar el reproductor para usar este widget
        if sys.platform.startswith('win'):
            self.player.set_hwnd(int(self.video_widget.winId()))
        elif sys.platform.startswith('linux'):
            self.player.set_xwindow(self.video_widget.winId())
        elif sys.platform.startswith('darwin'):
            self.player.set_nsobject(int(self.video_widget.winId()))
        
        # Variables para control de video
        self.current_audio_track = 0
        self.current_aspect_ratio = 'auto'
        self.current_scale = 1.0
    
    def play(self, url):
        """Reproduce la URL especificada"""
        print(f"Reproduciendo URL: {url}")
        media = self.instance.media_new(url)
        self.player.set_media(media)
        self.player.play()
    
    def stop(self):
        """Detiene la reproducción"""
        self.player.stop()
    
    def set_scale_mode(self, scale):
        """Cambia la escala de video"""
        self.current_scale = scale
        self.player.video_set_scale(scale)
        print(f"Escala cambiada a: {scale}")
    
    def set_aspect_ratio(self, aspect_ratio):
        """Cambia la relación de aspecto del video"""
        self.current_aspect_ratio = aspect_ratio
        self.player.video_set_aspect_ratio(aspect_ratio)
        print(f"Relación de aspecto cambiada a: {aspect_ratio}")
    
    def change_audio_track(self, track_id):
        """Cambia la pista de audio"""
        self.current_audio_track = track_id
        self.player.audio_set_track(track_id)
        print(f"Pista de audio cambiada a: {track_id}")
    
    def toggle_fullscreen(self):
        """Alterna entre modo pantalla completa y ventana normal"""
        if self.isFullScreen():
            self.showNormal()
        else:
            self.showFullScreen()
    
    def closeEvent(self, event):
        """Maneja el cierre de la ventana"""
        self.stop()
        event.accept()

class HybridApp:
    """Aplicación híbrida con CustomTkinter para UI y PyQt para video"""
    
    def __init__(self, root):
        self.root = root
        self.root.title("TV-IP Player")
        self.root.geometry("1200x700")
        self.root.minsize(900, 600)
        
        # Variables para control de UI
        self.sidebar_visible = True
        self.is_fullscreen = False
        self.sidebar_width = 300
        self.selected_channel = None
        
        # Inicializar PyQt para el reproductor de video
        self.qt_app = QApplication.instance()
        if not self.qt_app:
            self.qt_app = QApplication([])
        
        # Crear el reproductor de video
        self.video_player = VideoPlayerWindow()
        
        # Inicializar componentes de backend
        try:
            self.playlist_manager = PlaylistManager()
        except Exception as e:
            print(f"Error al inicializar componentes: {e}")
            messagebox.showerror("Error", f"Error de inicialización: {str(e)}")
        
        # Configurar la interfaz de usuario
        self.setup_ui()
        
        # Cargar canales iniciales
        self.update_channel_list()
        
        # Configurar el cierre de la aplicación
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
        
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
            text="Configuración",
            width=120,
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
            # Crear canales de ejemplo con URLs reales
            self.playlist_manager.channels = [
                Channel(name="Big Buck Bunny (MP4)", 
                       url="https://commondatastorage.googleapis.com/gtv-videos-bucket/sample/BigBuckBunny.mp4", 
                       group="Demos"),
                Channel(name="Elephant Dream (MP4)", 
                       url="https://commondatastorage.googleapis.com/gtv-videos-bucket/sample/ElephantsDream.mp4", 
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
        """Reproduce el medio actual usando la ventana PyQt"""
        if not self.selected_channel:
            messagebox.showerror("Error", "No hay canal seleccionado para reproducir")
            return
            
        try:
            # Mostrar la ventana de reproducción
            self.video_player.show()
            
            # Reproducir el canal seleccionado
            self.video_player.play(self.selected_channel.url)
            
            # Actualizar información
            self.video_info.configure(
                text=f"Reproduciendo: {self.selected_channel.name}\nURL: {self.selected_channel.url}\n\nReproduciendo en ventana externa"
            )
            
            # Procesar eventos Qt para asegurar que la ventana se muestre
            self.qt_app.processEvents()
            
        except Exception as e:
            print(f"Error al reproducir: {e}")
            messagebox.showerror("Error", f"Error al reproducir: {str(e)}")
            
    def pause_media(self):
        """Pausa la reproducción"""
        try:
            if self.video_player.isVisible():
                self.video_player.player.pause()
        except Exception as e:
            messagebox.showerror("Error", f"Error al pausar: {str(e)}")
        
    def stop_media(self):
        """Detiene la reproducción"""
        try:
            if self.video_player.isVisible():
                self.video_player.stop()
        except Exception as e:
            messagebox.showerror("Error", f"Error al detener: {str(e)}")
                
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
        
        # Mostrar el menú en la posición especificada
        context_menu.tk_popup(x, y)
        
    def toggle_fullscreen(self):
        """Alterna entre modo pantalla completa y ventana normal"""
        if self.video_player.isVisible():
            self.video_player.toggle_fullscreen()
        else:
            self.is_fullscreen = not self.is_fullscreen
            self.root.attributes("-fullscreen", self.is_fullscreen)
            if not self.is_fullscreen:
                # Restaurar el tamaño normal
                self.root.geometry("1200x700")
            
    def set_scale_mode(self, scale):
        """Cambia la escala de video"""
        if self.video_player.isVisible():
            self.video_player.set_scale_mode(scale)
        else:
            messagebox.showinfo("Escala", "No hay video reproduciéndose")
            
    def set_aspect_ratio(self, aspect_ratio):
        """Cambia la relación de aspecto del video"""
        if self.video_player.isVisible():
            self.video_player.set_aspect_ratio(aspect_ratio)
        else:
            messagebox.showinfo("Aspecto", "No hay video reproduciéndose")
            
    def change_audio_track(self, track_id):
        """Cambia la pista de audio"""
        if self.video_player.isVisible():
            self.video_player.change_audio_track(track_id)
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
    
    def on_closing(self):
        """Maneja el cierre de la aplicación"""
        # Cerrar el reproductor de video
        if hasattr(self, 'video_player') and self.video_player:
            self.video_player.close()
        
        # Cerrar la aplicación
        self.root.destroy()
        sys.exit(0)

def main():
    """Función principal para iniciar la aplicación híbrida"""
    root = ctk.CTk()
    app = HybridApp(root)
    
    # Iniciar el bucle de eventos
    root.mainloop()

# Si se ejecuta directamente este archivo
if __name__ == "__main__":
    main()
