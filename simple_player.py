"""
Reproductor simple de TV-IP con PyQt y VLC - Con estilo moderno
"""
import sys
import os
import traceback
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout,
                             QHBoxLayout, QListWidget, QLabel, QPushButton,
                             QFileDialog, QListWidgetItem, QMenu, QSizePolicy,
                             QMessageBox)
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QAction, QFont, QColor, QPalette, QActionGroup
import vlc
from src.core.playlist_manager import PlaylistManager, Channel

class ModernStyle:
    """Clase para definir estilos modernos para la aplicación"""
    DARK_BG = "#1E1E1E"
    MEDIUM_BG = "#2D2D2D"
    LIGHT_BG = "#3D3D3D"
    TEXT_COLOR = "#FFFFFF"
    ACCENT_COLOR = "#FF8000"  # Naranja
    ACCENT_HOVER = "#FF9A2E"
    BUTTON_STYLE = f"""
        QPushButton {{
            background-color: {MEDIUM_BG};
            color: {TEXT_COLOR};
            border: 1px solid {ACCENT_COLOR};
            border-radius: 4px;
            padding: 8px 16px;
            font-weight: bold;
        }}
        QPushButton:hover {{
            background-color: {ACCENT_COLOR};
            color: {DARK_BG};
        }}
        QPushButton:pressed {{
            background-color: {ACCENT_HOVER};
        }}
    """
    LIST_STYLE = f"""
        QListWidget {{
            background-color: {MEDIUM_BG};
            color: {TEXT_COLOR};
            border: 1px solid {LIGHT_BG};
            border-radius: 4px;
            padding: 5px;
        }}
        QListWidget::item {{
            padding: 8px;
            border-bottom: 1px solid {LIGHT_BG};
        }}
        QListWidget::item:selected {{
            background-color: {ACCENT_COLOR};
            color: {DARK_BG};
        }}
        QListWidget::item:hover {{
            background-color: {LIGHT_BG};
        }}
    """
    LABEL_STYLE = f"""
        QLabel {{
            color: {TEXT_COLOR};
            font-weight: bold;
            font-size: 14px;
        }}
    """
    MENU_BUTTON_STYLE = f"""
        QPushButton {{
            background-color: rgba(0, 0, 0, 0);
            color: {ACCENT_COLOR};
            border: 1px solid {ACCENT_COLOR};
            border-radius: 12px;
            padding: 0px;
            min-width: 28px;
            min-height: 28px;
            font-weight: bold;
            font-size: 16px;
        }}
        QPushButton:hover {{
            background-color: rgba(255, 128, 0, 0.2);
        }}
    """
    MENU_STYLE = f"""
        QMenu {{
            background-color: {MEDIUM_BG};
            color: {TEXT_COLOR};
            border: 1px solid {LIGHT_BG};
            padding: 5px;
        }}
        QMenu::item {{
            padding: 6px 20px;
        }}
        QMenu::item:selected {{
            background-color: {ACCENT_COLOR};
            color: {DARK_BG};
        }}
        QMenu::separator {{
            height: 1px;
            background-color: {LIGHT_BG};
            margin: 5px 2px;
        }}
    """

class SimplePlayer(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle('TV IP Player')
        self.setGeometry(100, 100, 1200, 700)
        self.setMinimumSize(900, 600)
        
        try:
            # Aplicar estilo moderno
            self.apply_modern_style()
            
            # Variables para control de video
            self.current_audio_track = 0
            self.audio_tracks = []
            self.current_aspect_ratio = 'auto'
            self.current_scale = 1.0
            
            # Inicializar el gestor de listas
            self.playlist_manager = PlaylistManager()
            
            # Inicializar VLC con opciones específicas
            print("Inicializando VLC...")
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
            print("VLC inicializado correctamente")
            
            # Widget principal
            main_widget = QWidget()
            self.setCentralWidget(main_widget)
            layout = QHBoxLayout(main_widget)
            layout.setContentsMargins(10, 10, 10, 10)
            layout.setSpacing(10)
            
            # Panel lateral para lista de canales
            sidebar = QWidget()
            sidebar_layout = QVBoxLayout(sidebar)
            sidebar.setMinimumWidth(280)
            sidebar.setMaximumWidth(350)
            
            # Título del sidebar
            channels_title = QLabel('Canales')
            channels_title.setStyleSheet(ModernStyle.LABEL_STYLE)
            channels_title.setFont(QFont("Arial", 16, QFont.Weight.Bold))
            sidebar_layout.addWidget(channels_title)
            
            # Lista de canales
            self.channel_list = QListWidget()
            self.channel_list.setStyleSheet(ModernStyle.LIST_STYLE)
            self.channel_list.itemClicked.connect(self.play_channel)
            sidebar_layout.addWidget(self.channel_list)
            
            # Botones de control
            buttons_layout = QHBoxLayout()
            
            load_button = QPushButton('Cargar Lista M3U')
            load_button.setStyleSheet(ModernStyle.BUTTON_STYLE)
            load_button.clicked.connect(self.load_playlist)
            buttons_layout.addWidget(load_button)
            
            demo_button = QPushButton('Cargar Demo')
            demo_button.setStyleSheet(ModernStyle.BUTTON_STYLE)
            demo_button.clicked.connect(self.load_demo_channels)
            buttons_layout.addWidget(demo_button)
            
            sidebar_layout.addLayout(buttons_layout)
            
            # Área de video
            video_container = QWidget()
            self.video_layout = QVBoxLayout(video_container)
            video_container.setStyleSheet(f"background-color: {ModernStyle.DARK_BG};")
            video_container.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
            
            # Widget para el video
            self.video_widget = QWidget()
            self.video_widget.setStyleSheet(f"background-color: {ModernStyle.DARK_BG};")
            self.video_widget.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
            self.video_widget.customContextMenuRequested.connect(self.show_video_context_menu)
            
            # Botón flotante de menú contextual
            self.menu_button = QPushButton("≡", self)
            self.menu_button.setStyleSheet(ModernStyle.MENU_BUTTON_STYLE)
            self.menu_button.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
            self.menu_button.setFixedSize(28, 28)
            self.menu_button.setToolTip('Menú de video')
            self.menu_button.clicked.connect(lambda: self.show_video_context_menu(self.menu_button.pos()))
            self.menu_button.move(10, 10)
            
            self.video_layout.addWidget(self.video_widget)
            
            # Añadir componentes al layout principal
            layout.addWidget(sidebar)
            layout.addWidget(video_container, 1)
            
            # Etiqueta de estado
            self.status_label = QLabel("Listo")
            self.status_label.setStyleSheet(ModernStyle.LABEL_STYLE)
            self.video_layout.addWidget(self.status_label)
            
            # Configurar el reproductor VLC para usar el widget de video
            print("Configurando widget de video...")
            if sys.platform.startswith('win'):
                self.player.set_hwnd(int(self.video_widget.winId()))
            elif sys.platform.startswith('linux'):
                self.player.set_xwindow(self.video_widget.winId())
            elif sys.platform.startswith('darwin'):
                self.player.set_nsobject(int(self.video_widget.winId()))
            print("Widget de video configurado correctamente")
            
            # Cargar canales de demo
            QTimer.singleShot(500, self.load_demo_channels)
            
        except Exception as e:
            print(f"Error en la inicialización: {e}")
            print(traceback.format_exc())
            QMessageBox.critical(None, "Error de inicialización", 
                                f"Error al inicializar la aplicación: {str(e)}\n\n{traceback.format_exc()}")
    
    def apply_modern_style(self):
        """Aplica un estilo moderno a la aplicación"""
        # Establecer la paleta de colores
        palette = QPalette()
        palette.setColor(QPalette.ColorRole.Window, QColor(ModernStyle.DARK_BG))
        palette.setColor(QPalette.ColorRole.WindowText, QColor(ModernStyle.TEXT_COLOR))
        palette.setColor(QPalette.ColorRole.Base, QColor(ModernStyle.MEDIUM_BG))
        palette.setColor(QPalette.ColorRole.AlternateBase, QColor(ModernStyle.LIGHT_BG))
        palette.setColor(QPalette.ColorRole.ToolTipBase, QColor(ModernStyle.DARK_BG))
        palette.setColor(QPalette.ColorRole.ToolTipText, QColor(ModernStyle.TEXT_COLOR))
        palette.setColor(QPalette.ColorRole.Text, QColor(ModernStyle.TEXT_COLOR))
        palette.setColor(QPalette.ColorRole.Button, QColor(ModernStyle.MEDIUM_BG))
        palette.setColor(QPalette.ColorRole.ButtonText, QColor(ModernStyle.TEXT_COLOR))
        palette.setColor(QPalette.ColorRole.Highlight, QColor(ModernStyle.ACCENT_COLOR))
        palette.setColor(QPalette.ColorRole.HighlightedText, QColor(ModernStyle.DARK_BG))
        self.setPalette(palette)
    
    def load_playlist(self):
        """Carga una lista de reproducción desde un archivo M3U"""
        try:
            file_path, _ = QFileDialog.getOpenFileName(
                self, "Seleccionar archivo M3U", "", "Archivos M3U (*.m3u *.m3u8);;Todos los archivos (*)"
            )
            
            if file_path:
                self.status_label.setText(f"Cargando lista: {file_path}")
                self.playlist_manager.load_playlist(file_path)
                self.update_channel_list()
                self.status_label.setText(f"Lista cargada: {len(self.playlist_manager.channels)} canales")
        except Exception as e:
            print(f"Error al cargar lista: {e}")
            print(traceback.format_exc())
            self.status_label.setText(f"Error al cargar lista: {str(e)}")
            QMessageBox.warning(self, "Error", f"Error al cargar lista: {str(e)}")
    
    def load_demo_channels(self):
        """Carga canales de demostración para pruebas"""
        try:
            self.status_label.setText("Cargando canales de demostración...")
            
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
            self.status_label.setText(f"Canales demo cargados: {len(self.playlist_manager.channels)}")
            
        except Exception as e:
            print(f"Error al cargar canales demo: {e}")
            print(traceback.format_exc())
            self.status_label.setText(f"Error al cargar demos: {str(e)}")
            QMessageBox.warning(self, "Error", f"Error al cargar canales demo: {str(e)}")
    
    def update_channel_list(self):
        """Actualiza la lista de canales en la UI"""
        try:
            self.channel_list.clear()
            
            for channel in self.playlist_manager.channels:
                item = QListWidgetItem(channel.name)
                item.setData(Qt.ItemDataRole.UserRole, channel)
                self.channel_list.addItem(item)
                
        except Exception as e:
            print(f"Error al actualizar lista de canales: {e}")
            print(traceback.format_exc())
            self.status_label.setText(f"Error al actualizar canales: {str(e)}")
    
    def play_channel(self, item):
        """Reproduce el canal seleccionado"""
        try:
            channel = item.data(Qt.ItemDataRole.UserRole)
            if not channel:
                return
            
            self.status_label.setText(f"Reproduciendo: {channel.name}")
            print(f"Reproduciendo: {channel.name} - {channel.url}")
            
            # Crear un medio con la URL
            media = self.instance.media_new(channel.url)
            self.player.set_media(media)
            
            # Iniciar reproducción
            self.player.play()
            
        except Exception as e:
            print(f"Error al reproducir canal: {e}")
            print(traceback.format_exc())
            self.status_label.setText(f"Error al reproducir: {str(e)}")
            QMessageBox.warning(self, "Error", f"Error al reproducir canal: {str(e)}")
    
    def toggle_fullscreen(self):
        """Alterna entre modo pantalla completa y ventana normal"""
        try:
            if self.isFullScreen():
                self.showNormal()
                self.status_label.setText("Modo ventana")
            else:
                self.showFullScreen()
                self.status_label.setText("Modo pantalla completa")
                
            # Asegurar que el widget de video mantenga el foco
            self.video_widget.setFocus()
        except Exception as e:
            print(f"Error al cambiar modo pantalla completa: {e}")
            print(traceback.format_exc())
            self.status_label.setText(f"Error en pantalla completa: {str(e)}")
    
    def set_scale_mode(self, scale):
        """Cambia la escala de video"""
        try:
            self.current_scale = scale
            self.player.video_set_scale(float(scale))  # Asegurar que sea float
            self.status_label.setText(f"Escala cambiada a: {scale}")
            print(f"Escala cambiada a: {scale}")
        except Exception as e:
            print(f"Error al cambiar escala: {e}")
            print(traceback.format_exc())
            self.status_label.setText(f"Error al cambiar escala: {str(e)}")
    
    def set_aspect_ratio(self, aspect_ratio):
        """Cambia la relación de aspecto del video"""
        try:
            self.current_aspect_ratio = aspect_ratio
            if aspect_ratio == '':  # Si es auto/vacío
                self.player.video_set_aspect_ratio(None)
            else:
                self.player.video_set_aspect_ratio(str(aspect_ratio))  # Asegurar que sea string
            
            self.status_label.setText(f"Relación de aspecto: {aspect_ratio if aspect_ratio else 'Auto'}")
            print(f"Relación de aspecto cambiada a: {aspect_ratio if aspect_ratio else 'Auto'}")
        except Exception as e:
            print(f"Error al cambiar relación de aspecto: {e}")
            print(traceback.format_exc())
            self.status_label.setText(f"Error en relación de aspecto: {str(e)}")
    
    def change_audio_track(self, track_id):
        """Cambia la pista de audio"""
        try:
            self.current_audio_track = track_id
            self.player.audio_set_track(track_id)
            self.status_label.setText(f"Pista de audio: {track_id}")
            print(f"Pista de audio cambiada a: {track_id}")
        except Exception as e:
            print(f"Error al cambiar pista de audio: {e}")
            print(traceback.format_exc())
            self.status_label.setText(f"Error en pista de audio: {str(e)}")

    def show_video_context_menu(self, position):
        """Muestra el menú contextual del video"""
        try:
            context_menu = QMenu(self)
            context_menu.setStyleSheet(ModernStyle.MENU_STYLE)
            
            # Acción de pantalla completa
            fullscreen_action = QAction('Pantalla Completa', self)
            fullscreen_action.triggered.connect(self.toggle_fullscreen)
            context_menu.addAction(fullscreen_action)
            
            # Opciones de cambio de tamaño de video
            scale_menu = QMenu('Escala de Video', self)
            scale_menu.setStyleSheet(ModernStyle.MENU_STYLE)
            scales = {
                'Ajuste Original (1.0x)': 1.0,
                'Ajuste a Ventana (0.5x)': 0.5,
                'Ajuste Doble (2.0x)': 2.0
            }
            
            # Crear grupo de acciones para escala
            scale_group = QActionGroup(self)
            scale_group.setExclusive(True)
            
            for name, scale in scales.items():
                action = QAction(name, self)
                action.setCheckable(True)
                action.setChecked(abs(self.current_scale - scale) < 0.01)  # Comparación con tolerancia
                action.triggered.connect(lambda checked, s=scale: self.set_scale_mode(s))
                scale_group.addAction(action)
                scale_menu.addAction(action)
            
            context_menu.addMenu(scale_menu)
            
            # Opciones de relación de aspecto
            aspect_menu = QMenu('Relación de Aspecto', self)
            aspect_menu.setStyleSheet(ModernStyle.MENU_STYLE)
            aspect_ratios = {
                'Auto': '',
                '16:9': '16:9',
                '4:3': '4:3',
                '1:1': '1:1',
                '16:10': '16:10',
                '2.35:1 (Cinemascope)': '2.35:1'
            }
            
            # Crear grupo de acciones para relación de aspecto
            aspect_group = QActionGroup(self)
            aspect_group.setExclusive(True)
            
            for name, ratio in aspect_ratios.items():
                action = QAction(name, self)
                action.setCheckable(True)
                action.setChecked(self.current_aspect_ratio == ratio)
                action.triggered.connect(lambda checked, r=ratio: self.set_aspect_ratio(r))
                aspect_group.addAction(action)
                aspect_menu.addAction(action)
            
            context_menu.addMenu(aspect_menu)
            
            # Opciones de pistas de audio (si está reproduciendo)
            if self.player.is_playing():
                try:
                    audio_tracks = []
                    # Obtener pistas de audio disponibles
                    media = self.player.get_media()
                    if media:
                        # Método alternativo para obtener pistas de audio
                        # En algunas versiones de VLC, media_player_new() no tiene parse()
                        audio_track_count = self.player.audio_get_track_count()
                        current_track = self.player.audio_get_track()
                        
                        if audio_track_count > 1:
                            audio_menu = QMenu('Pistas de Audio', self)
                            audio_menu.setStyleSheet(ModernStyle.MENU_STYLE)
                            
                            # Añadir pista por defecto
                            action = QAction("Pista por defecto (0)", self)
                            action.setCheckable(True)
                            action.setChecked(current_track == 0)
                            action.triggered.connect(lambda checked: self.change_audio_track(0))
                            audio_menu.addAction(action)
                            
                            # Añadir pistas adicionales
                            for i in range(1, audio_track_count):
                                action = QAction(f"Pista {i}", self)
                                action.setCheckable(True)
                                action.setChecked(current_track == i)
                                action.triggered.connect(lambda checked, tid=i: self.change_audio_track(tid))
                                audio_menu.addAction(action)
                            
                            context_menu.addMenu(audio_menu)
                except Exception as e:
                    print(f"Error al obtener pistas de audio: {e}")
                    print(traceback.format_exc())
            
            # Mostrar el menú en la posición global
            if isinstance(position, QListWidgetItem):
                # Si se llamó desde un botón, usar la posición del botón
                position = self.menu_button.mapToGlobal(self.menu_button.rect().bottomRight())
            else:
                # Si se llamó desde un clic derecho, usar la posición del clic
                position = self.video_widget.mapToGlobal(position)
                
            context_menu.exec(position)
            
        except Exception as e:
            print(f"Error al mostrar menú contextual: {e}")
            print(traceback.format_exc())
            self.status_label.setText(f"Error en menú: {str(e)}")

if __name__ == '__main__':
    try:
        app = QApplication(sys.argv)
        player = SimplePlayer()
        player.show()
        sys.exit(app.exec())
    except Exception as e:
        print(f"Error al iniciar la aplicación: {e}")
        print(traceback.format_exc())
        QMessageBox.critical(None, "Error fatal", 
                            f"Error al iniciar la aplicación: {str(e)}\n\n{traceback.format_exc()}")
        sys.exit(1)
