#!/usr/bin/env python3
"""
TV-IP Player - Reproductor de canales IPTV con estilo moderno
Versión mejorada estéticamente usando PyQt6
"""

import sys
import os
import traceback
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout,
                             QHBoxLayout, QListWidget, QLabel, QPushButton,
                             QComboBox, QFileDialog, QListWidgetItem, QSizePolicy,
                             QProgressDialog, QInputDialog, QMessageBox, QMenu, QGridLayout)
from PyQt6.QtCore import Qt, QEvent, QTimer, QPoint
from PyQt6.QtGui import QKeyEvent, QColor, QCursor, QAction, QIcon, QPalette, QFont
import vlc
import asyncio
from playlist_manager import PlaylistManager, Channel

class ModernStyle:
    """Clase para definir estilos modernos para la aplicación"""
    DARK_BG = "#1E1E1E"
    MEDIUM_BG = "#2D2D2D"
    LIGHT_BG = "#3D3D3D"
    TEXT_COLOR = "#FFFFFF"
    ACCENT_COLOR = "#FF8000"  # Naranja
    ACCENT_HOVER = "#FF9A2E"
    STATUS_COLOR = "#FFCC00"  # Amarillo más visible para estados
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
            color: {DARK_BG};
        }}
    """
    LABEL_STYLE = f"""
        QLabel {{
            color: {TEXT_COLOR};
            font-weight: bold;
        }}
    """
    STATUS_LABEL_STYLE = f"""
        QLabel {{
            color: {STATUS_COLOR};
            font-weight: bold;
        }}
    """
    LIST_STYLE = f"""
        QListWidget {{
            background-color: {MEDIUM_BG};
            color: {TEXT_COLOR};
            border: 1px solid {LIGHT_BG};
            border-radius: 4px;
            padding: 5px;
            font-size: 12pt;
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
    COMBOBOX_STYLE = f"""
        QComboBox {{
            background-color: {MEDIUM_BG};
            color: {TEXT_COLOR};
            border: 1px solid {LIGHT_BG};
            border-radius: 4px;
            padding: 5px;
            min-height: 25px;
        }}
        QComboBox::drop-down {{
            subcontrol-origin: padding;
            subcontrol-position: top right;
            width: 25px;
            border-left: 1px solid {LIGHT_BG};
        }}
        QComboBox QAbstractItemView {{
            background-color: {MEDIUM_BG};
            color: {TEXT_COLOR};
            selection-background-color: {ACCENT_COLOR};
            selection-color: {DARK_BG};
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
    CHANNEL_NAME_COLOR = "#80FFFF"  # Cyan claro (complementario del naranja)
    ONLINE_COLOR = "#80FF80"        # Verde claro
    SLOW_COLOR = "#FFFF80"          # Amarillo claro
    OFFLINE_COLOR = "#FF8080"       # Rojo claro
    RESPONSE_TIME_COLOR = "#FFC080" # Naranja claro

    # Estilo para el botón de menú
    MENU_BUTTON_STYLE = """
        QPushButton {
            background-color: #FF8000;
            color: #1E1E1E;
            border: 2px solid #FFFFFF;
            border-radius: 20px;
            font-weight: bold;
            font-size: 18px;
            padding: 5px;
        }
        QPushButton:hover {
            background-color: #FF9A2E;
        }
    """

    # Estilo para la barra de título
    TITLE_BAR_STYLE = """
        QMainWindow::title {
            background-color: #FF8000;
            color: #1E1E1E;
            font-weight: bold;
            height: 30px;
            padding-left: 10px;
            border-bottom: 2px solid #FF9A2E;
        }
        QMenuBar {
            background-color: #FF8000;
            color: #1E1E1E;
            border-bottom: 2px solid #FF9A2E;
            font-weight: bold;
        }
        QMenuBar::item {
            background-color: #FF8000;
            color: #1E1E1E;
            padding: 5px 10px;
            margin: 0px;
        }
        QMenuBar::item:selected {
            background-color: #FF9A2E;
        }
        QMenu {
            background-color: #2D2D2D;
            color: #FFFFFF;
            border: 1px solid #FF8000;
        }
        QMenu::item:selected {
            background-color: #FF8000;
            color: #1E1E1E;
        }
        QStatusBar {
            background-color: #2D2D2D;
            color: #FFFFFF;
            border-top: 1px solid #FF8000;
        }
        QStatusBar QLabel {
            padding: 3px 5px;
        }
    """

class ModernTVIPPlayer(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle('TV IP Player - Moderno')
        self.setGeometry(100, 100, 1200, 700)
        self.setMinimumSize(900, 600)
        self.installEventFilter(self)
        
        # Aplicar estilo moderno a toda la aplicación
        self.apply_modern_style()
        
        # Variables para control de panel lateral
        self.sidebar_visible = True
        self.is_fullscreen_mode = False
        self.sidebar_hover_margin = 20
        self.sidebar_position = "right"
        self.mouse_check_timer = QTimer(self)
        self.mouse_check_timer.timeout.connect(self.check_mouse_position)
        self.mouse_check_timer.start(200)  # Verificar cada 200ms
        
        # Variables para control de video
        self.current_audio_track = 0
        self.audio_tracks = []
        self.current_aspect_ratio = 'auto'
        self.current_scale = 1.0
        
        # Inicializar el gestor de listas
        self.playlist_manager = PlaylistManager()
        
        # Inicializar VLC con opciones específicas
        vlc_args = [
            '--embedded-video',  # Forzar video embebido
            '--no-snapshot-preview',  # Deshabilitar vista previa de capturas
            '--avcodec-hw=none',  # Deshabilitar decodificación por hardware
            '--no-direct3d11-hw-blending',  # Deshabilitar mezcla por hardware en Direct3D11
            '--no-direct3d11',  # Deshabilitar Direct3D11
            '--quiet',  # Reducir mensajes de registro
            '--no-video-title-show',  # No mostrar título de video
            '--no-fullscreen',  # Evitar pantalla completa automática
            '--video-on-top',  # Mantener video encima
        ]
        self.instance = vlc.Instance(vlc_args)
        self.player = self.instance.media_player_new()
        
        # Widget principal
        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        layout = QHBoxLayout(main_widget)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(10)
        
        # Panel lateral para lista de canales
        self.sidebar = QWidget()
        sidebar_layout = QVBoxLayout(self.sidebar)
        sidebar_layout.setContentsMargins(10, 10, 10, 10)
        sidebar_layout.setSpacing(10)
        self.sidebar.setMinimumWidth(280)
        self.sidebar.setMaximumWidth(350)
        self.sidebar.setStyleSheet(f"background-color: {ModernStyle.MEDIUM_BG};")
        
        # Título del sidebar
        sidebar_title = QLabel('TV IP Player')
        sidebar_title.setStyleSheet(ModernStyle.LABEL_STYLE)
        sidebar_title.setFont(QFont("Arial", 18, QFont.Weight.Bold))
        sidebar_title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        sidebar_layout.addWidget(sidebar_title)
        
        # Filtro por grupos
        group_label = QLabel('Filtrar por grupo:')
        group_label.setStyleSheet(ModernStyle.LABEL_STYLE)
        sidebar_layout.addWidget(group_label)
        
        self.group_filter = QComboBox()
        self.group_filter.addItem('Todos los grupos')
        self.group_filter.setStyleSheet(ModernStyle.COMBOBOX_STYLE)
        self.group_filter.currentTextChanged.connect(lambda text: self.update_channel_list(text))
        sidebar_layout.addWidget(self.group_filter)
        
        # Lista de canales
        channels_label = QLabel('Canales:')
        channels_label.setStyleSheet(ModernStyle.LABEL_STYLE)
        sidebar_layout.addWidget(channels_label)
        
        self.channel_list = QListWidget()
        self.channel_list.setStyleSheet(f"""
            QListWidget {{
                background-color: {ModernStyle.MEDIUM_BG};
                color: {ModernStyle.CHANNEL_NAME_COLOR};
                border: 1px solid {ModernStyle.LIGHT_BG};
                border-radius: 4px;
                outline: none;
                font-size: 11pt;
            }}
            QListWidget::item {{
                padding: 6px;
                min-height: 24px;
                border-bottom: 1px solid {ModernStyle.DARK_BG};
            }}
            QListWidget::item:selected {{
                background-color: {ModernStyle.ACCENT_COLOR};
                color: {ModernStyle.DARK_BG};
            }}
            QListWidget::item:hover {{
                background-color: {ModernStyle.LIGHT_BG};
            }}
        """)
        self.channel_list.itemClicked.connect(self.play_channel)
        sidebar_layout.addWidget(self.channel_list)
        
        # Botones de control
        buttons_grid = QGridLayout()
        buttons_grid.setSpacing(10)
        
        # Primera fila de botones
        load_button = QPushButton('Cargar Lista M3U')
        load_button.clicked.connect(self.load_playlist)
        load_button.setStyleSheet(ModernStyle.BUTTON_STYLE)
        load_button.setMinimumWidth(140)
        
        download_button = QPushButton('Descargar Lista')
        download_button.clicked.connect(self.download_playlist)
        download_button.setStyleSheet(ModernStyle.BUTTON_STYLE)
        download_button.setMinimumWidth(140)
        
        buttons_grid.addWidget(load_button, 0, 0)
        buttons_grid.addWidget(download_button, 0, 1)
        
        # Segunda fila de botones
        check_button = QPushButton('Verificar Canales')
        check_button.clicked.connect(self.check_channels)
        check_button.setStyleSheet(ModernStyle.BUTTON_STYLE)
        check_button.setMinimumWidth(140)
        
        save_working_button = QPushButton('Guardar Canales')
        save_working_button.clicked.connect(self.save_working_channels)
        save_working_button.setStyleSheet(ModernStyle.BUTTON_STYLE)
        save_working_button.setMinimumWidth(140)
        
        buttons_grid.addWidget(check_button, 1, 0)
        buttons_grid.addWidget(save_working_button, 1, 1)
        
        sidebar_layout.addLayout(buttons_grid)
        
        # Área de video
        video_container = QWidget()
        self.video_layout = QVBoxLayout(video_container)
        self.video_layout.setContentsMargins(0, 0, 0, 0)
        self.video_layout.setSpacing(0)  # Eliminar espacio entre widgets
        video_container.setStyleSheet(f"background-color: {ModernStyle.DARK_BG};")
        video_container.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        
        # Widget para el video
        self.video_widget = QWidget()
        self.video_widget.setStyleSheet(f"background-color: {ModernStyle.DARK_BG};")
        self.video_widget.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.video_widget.customContextMenuRequested.connect(self.show_video_context_menu)
        self.video_widget.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        
        # Overlay transparente para capturar eventos de ratón
        self.overlay_widget = QWidget(self.video_widget)
        self.overlay_widget.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, False)
        self.overlay_widget.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.overlay_widget.customContextMenuRequested.connect(self.show_video_context_menu)
        self.overlay_widget.setStyleSheet("background-color: rgba(0, 0, 0, 0);")
        self.overlay_widget.resize(self.video_widget.size())
        
        # Contenedor para el botón de menú - lo hacemos hijo de la ventana principal, no del video
        self.button_container = QWidget(self)
        self.button_container.setGeometry(10, 10, 40, 40)
        
        # Botón de menú
        self.menu_button = QPushButton("≡", self.button_container)
        self.menu_button.setStyleSheet(ModernStyle.MENU_BUTTON_STYLE)
        self.menu_button.setFixedSize(40, 40)
        self.menu_button.setToolTip('Menú de video')
        self.menu_button.clicked.connect(self.show_fixed_menu)
        
        # Inicialmente ocultamos el botón hasta que se reproduzca un video
        self.button_container.hide()
        
        self.video_layout.addWidget(self.video_widget, 1)  # El 1 hace que ocupe todo el espacio disponible
        
        # Barra de herramientas con botón de menú
        toolbar = QWidget()
        toolbar_layout = QHBoxLayout(toolbar)
        toolbar_layout.setContentsMargins(5, 5, 5, 5)
        toolbar_layout.setSpacing(5)
        
        # Añadir espacio flexible
        toolbar_layout.addStretch(1)
        
        # Añadir la barra de herramientas al layout de video
        self.video_layout.addWidget(toolbar)
        
        # Etiqueta de estado
        self.status_label = QLabel("Listo")
        self.status_label.setStyleSheet(ModernStyle.LABEL_STYLE)
        self.status_label.setMaximumHeight(20)  # Limitar altura de la etiqueta de estado
        self.video_layout.addWidget(self.status_label)
        
        # Añadir componentes al layout principal
        layout.addWidget(self.sidebar)
        layout.addWidget(video_container, 1)
        
        # Configurar el reproductor VLC para usar el widget de video
        if sys.platform.startswith('win'):
            self.player.set_hwnd(int(self.video_widget.winId()))
        elif sys.platform.startswith('linux'):
            self.player.set_xwindow(self.video_widget.winId())
        elif sys.platform.startswith('darwin'):
            self.player.set_nsobject(int(self.video_widget.winId()))
        
        # Intentar cargar la última lista de reproducción si existe
        last_playlist = os.path.join(os.path.dirname(os.path.abspath(__file__)), "last_playlist.json")
        if os.path.exists(last_playlist):
            try:
                self.playlist_manager.load_json_playlist(last_playlist)
                self.update_channel_list("Todos los grupos")
                # Actualizar el combobox de grupos
                groups = ["Todos los grupos"] + sorted(set(ch.group for ch in self.playlist_manager.channels if ch.group))
                self.group_filter.clear()
                self.group_filter.addItems(groups)
                self.status_label.setText(f"Lista cargada: {len(self.playlist_manager.channels)} canales")
            except Exception as e:
                print(f"Error al cargar la última lista: {e}")
                
        # Timer para verificar las pistas de audio disponibles
        self.audio_check_timer = QTimer(self)
        self.audio_check_timer.timeout.connect(self.check_audio_tracks)
        self.audio_check_timer.start(1000)  # Verificar cada segundo

        # Aplicar estilo moderno para la barra de título
        self.setStyleSheet(f"""
            QMainWindow {{
                background-color: {ModernStyle.DARK_BG};
                color: {ModernStyle.TEXT_COLOR};
            }}
            {ModernStyle.TITLE_BAR_STYLE}
        """)

    def apply_modern_style(self):
        """Aplica un estilo moderno a toda la aplicación"""
        # Establecer la paleta de colores para toda la aplicación
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
        
        # Establecer la fuente predeterminada
        font = QFont("Arial", 10)
        QApplication.setFont(font)
        
        # Establecer estilo global para los menús
        QApplication.setStyle("Fusion")

    def check_mouse_position(self):
        """Verifica la posición del ratón para mostrar/ocultar el panel lateral en modo pantalla completa"""
        if not self.is_fullscreen_mode:
            return
            
        cursor_pos = QCursor.pos()
        window_pos = self.mapToGlobal(QPoint(0, 0))
        window_width = self.width()
        relative_x = cursor_pos.x() - window_pos.x()
        
        # Verificar si el cursor está cerca del borde derecho
        if relative_x >= (window_width - self.sidebar_hover_margin) and not self.sidebar_visible:
            # El cursor está cerca del borde derecho, mostrar el panel
            self.sidebar.show()
            self.sidebar_visible = True
            self.sidebar_position = "right"
        # Verificar si el cursor está lejos del panel cuando está visible
        elif self.sidebar_visible and self.sidebar_position == "right":
            # Si está a la derecha, verificar si el cursor está lejos del borde derecho
            if relative_x < (window_width - self.sidebar.width() - 10):
                self.sidebar.hide()
                self.sidebar_visible = False
                
    def load_playlist(self):
        file_name, _ = QFileDialog.getOpenFileName(self, 'Abrir Lista M3U',
                                                 '', 'M3U Files (*.m3u *.m3u8)')
        if file_name:
            try:
                # Crear diálogo de progreso
                progress = QProgressDialog('Cargando lista de canales...', 'Cancelar', 0, 100, self)
                progress.setWindowModality(Qt.WindowModality.WindowModal)
                progress.setMinimumDuration(0)
                progress.setAutoClose(True)
                progress.setAutoReset(True)
                progress.setStyleSheet(f"""
                    QProgressDialog {{
                        background-color: {ModernStyle.MEDIUM_BG};
                        color: {ModernStyle.TEXT_COLOR};
                    }}
                    QProgressBar {{
                        border: 1px solid {ModernStyle.LIGHT_BG};
                        border-radius: 4px;
                        background-color: {ModernStyle.DARK_BG};
                        text-align: center;
                    }}
                    QProgressBar::chunk {{
                        background-color: {ModernStyle.ACCENT_COLOR};
                        width: 10px;
                    }}
                """)
                
                def update_progress(percent, channels_count):
                    if progress.wasCanceled():
                        return
                    progress.setValue(int(percent))
                    progress.setLabelText(f'Cargando lista de canales...\nCanales encontrados: {channels_count}')
                    QApplication.processEvents()
                
                self.playlist_manager.load_playlist(file_name, progress_callback=update_progress)
                progress.setValue(100)
                self.playlist_manager.save_last_playlist()
                
                # Actualizar filtro de grupos
                self.group_filter.clear()
                self.group_filter.addItem('Todos los grupos')
                self.group_filter.addItems(sorted(self.playlist_manager.groups))
                
                # Mostrar canales
                self.update_channel_list('Todos los grupos')
                
                self.status_label.setText(f"Lista cargada: {len(self.playlist_manager.channels)} canales en {len(self.playlist_manager.groups)} grupos")
                
            except Exception as e:
                # Mostrar un mensaje de error detallado al usuario
                error_message = f"Error al cargar la lista: {str(e)}"
                print(error_message)  # Imprimir en consola para depuración
                
    def update_channel_list(self, group: str):
        self.channel_list.clear()
        channels = self.playlist_manager.get_channels_by_group(group)
        for channel in channels:
            # Crear un item simple con solo el nombre del canal en texto plano
            item = QListWidgetItem(channel.name)
            item.setData(Qt.ItemDataRole.UserRole, channel)
            
            # Establecer color según el estado del canal
            if channel.status == 'online':
                item.setForeground(QColor(ModernStyle.ONLINE_COLOR))
            elif channel.status == 'slow':
                item.setForeground(QColor(ModernStyle.SLOW_COLOR))
            elif channel.status == 'offline':
                item.setForeground(QColor(ModernStyle.OFFLINE_COLOR))
            else:
                item.setForeground(QColor(ModernStyle.CHANNEL_NAME_COLOR))
                
            # Añadir información de tiempo de respuesta si está disponible
            if hasattr(channel, 'response_time') and channel.response_time:
                response_text = f" ({channel.response_time}ms)"
                response_item = QListWidgetItem(response_text)
                response_item.setForeground(QColor(ModernStyle.RESPONSE_TIME_COLOR))
                self.channel_list.addItem(item)
                self.channel_list.addItem(response_item)
            else:
                self.channel_list.addItem(item)
                
        # Ocultar el botón de menú cuando se cambia la lista de canales
        if hasattr(self, 'button_container'):
            self.button_container.hide()
            
    def play_channel(self, item):
        try:
            channel = item.data(Qt.ItemDataRole.UserRole)
            if channel and channel.url:
                print(f"Iniciando reproducción de canal: {channel.name}")
                
                # Configurar opciones de reproducción específicas para este medio
                media = self.instance.media_new(channel.url)
                media.add_option('avcodec-hw=none')  # Deshabilitar decodificación por hardware
                media.add_option('no-direct3d11-hw-blending')  # Deshabilitar mezcla por hardware
                media.add_option('no-direct3d11')  # Deshabilitar Direct3D11
                media.add_option('no-fullscreen')  # Evitar pantalla completa automática
                media.add_option('embedded-video')  # Forzar video embebido
                
                self.player.set_media(media)
                self.player.play()
                
                # Configurar un timer para verificar cuando el video comience realmente a reproducirse
                # y mostrar el botón solo cuando haya contenido visible
                def check_playing_status():
                    if self.player and self.player.is_playing():
                        # Asegurar que el botón de menú esté en la posición correcta y visible
                        self.update_menu_button_position()
                        # Detener este timer de verificación
                        check_timer.stop()
                
                check_timer = QTimer(self)
                check_timer.timeout.connect(check_playing_status)
                check_timer.start(100)  # Verificar cada 100ms
                
                # Usar timers para mantener el botón visible durante la reproducción
                for delay in [1000, 2000, 3000, 4000, 5000]:
                    QTimer.singleShot(delay, lambda: self.update_menu_button_position())
                
                # Configurar un timer para mantener el botón visible periódicamente
                if hasattr(self, 'button_visibility_timer'):
                    self.button_visibility_timer.stop()
                
                self.button_visibility_timer = QTimer(self)
                self.button_visibility_timer.timeout.connect(self.update_menu_button_position)
                self.button_visibility_timer.start(1000)  # Verificar cada segundo
                
                self.status_label.setText(f"Reproduciendo: {channel.name}")
                
        except Exception as e:
            print(f"Error al reproducir canal: {e}")
            
    def check_audio_tracks(self):
        if not self.player.is_playing():
            return
        
        media = self.player.get_media()
        if not media:
            return
        
        # Obtener la lista de pistas de audio
        tracks = []
        for i in range(self.player.audio_get_track_count()):
            track_description = self.player.audio_get_track_description()[i]
            if track_description:
                tracks.append(track_description)
        
        # Actualizar el botón si hay múltiples pistas
        if len(tracks) > 1:
            current_track = self.player.audio_get_track()
            current_track_info = next((t for t in tracks if t[0] == current_track), None)
            self.audio_tracks = tracks
        else:
            self.audio_tracks = []
            
    def toggle_fullscreen(self):
        """Alterna entre modo pantalla completa y ventana normal"""
        print(f"toggle_fullscreen llamado. is_fullscreen_mode={self.is_fullscreen_mode}, isFullScreen()={self.isFullScreen()}")
        if not self.isFullScreen():
            self.normal_geometry = self.geometry()
            if hasattr(self, 'sidebar'):
                self.sidebar.hide()
                self.sidebar_visible = False
            self.showFullScreen()
            self.is_fullscreen_mode = True
            print("Entrando a pantalla completa")
            if hasattr(self, 'video_widget'):
                self.video_widget.setFocus()
        else:
            self.showNormal()
            if hasattr(self, 'normal_geometry'):
                self.setGeometry(self.normal_geometry)
            self.is_fullscreen_mode = False
            print("Saliendo de pantalla completa")
            if hasattr(self, 'sidebar'):
                self.sidebar.show()
                self.sidebar_visible = True
                
    def eventFilter(self, obj, event):
        try:
            # Mantener overlay del tamaño del video_widget
            if obj == self.video_widget and event.type() == QEvent.Type.Resize:
                self.overlay_widget.resize(self.video_widget.size())
                
            # El evento ya es un QKeyEvent, no necesitamos convertirlo
            if event.type() == QEvent.Type.KeyPress:
                if event.key() == Qt.Key.Key_F11 or \
                   (event.key() == Qt.Key.Key_Return and event.modifiers() == Qt.KeyboardModifier.AltModifier):
                    self.toggle_fullscreen()
                    return True
                elif event.key() == Qt.Key.Key_Escape and self.isFullScreen():
                    self.toggle_fullscreen()
                    return True
            return super().eventFilter(obj, event)
        except Exception as e:
            print(f"Error en el manejo de eventos: {e}")
            return False
            
    def check_channels(self):
        try:
            # Configurar una política de manejo de eventos para evitar errores de conexión
            asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
            asyncio.run(self.check_channels_async())
        except Exception as e:
            print(f"Error al ejecutar verificación de canales: {e}")
            
    async def check_channels_async(self):
        progress = QProgressDialog('Verificando canales...', 'Cancelar', 0, len(self.playlist_manager.channels), self)
        progress.setWindowModality(Qt.WindowModality.WindowModal)
        progress.setMinimumDuration(500)  # Mostrar diálogo solo si tarda más de 500ms
        progress.setValue(0)
        progress.setStyleSheet(f"""
            QProgressDialog {{
                background-color: {ModernStyle.MEDIUM_BG};
                color: {ModernStyle.TEXT_COLOR};
            }}
            QProgressBar {{
                border: 1px solid {ModernStyle.LIGHT_BG};
                border-radius: 4px;
                background-color: {ModernStyle.DARK_BG};
                text-align: center;
            }}
            QProgressBar::chunk {{
                background-color: {ModernStyle.ACCENT_COLOR};
                width: 10px;
            }}
        """)
        progress.show()
        
        # Variable para rastrear si la operación fue cancelada
        was_cancelled = False
        
        try:
            # Configurar una función de actualización para el progreso
            completed_count = 0
            
            # Modificar el método check_all_channels para que actualice el progreso
            original_check_channel = self.playlist_manager.check_channel
            
            async def wrapped_check_channel(channel):
                nonlocal completed_count
                try:
                    await original_check_channel(channel)
                finally:
                    completed_count += 1
                    progress.setValue(completed_count)
                    # Procesar eventos para mantener la UI responsiva
                    QApplication.processEvents()
                    
                    # Verificar si el usuario canceló la operación
                    if progress.wasCanceled():
                        raise asyncio.CancelledError("Usuario canceló la operación")
            
            # Reemplazar temporalmente el método
            self.playlist_manager.check_channel = wrapped_check_channel
            
            try:
                # Ejecutar verificación con el método modificado
                await self.playlist_manager.check_all_channels()
            finally:
                # Restaurar el método original
                self.playlist_manager.check_channel = original_check_channel
        
        except asyncio.CancelledError:
            was_cancelled = True
            print("Verificación de canales cancelada por el usuario")
        except Exception as e:
            print(f"Error al ejecutar verificación de canales: {str(e)}")
        finally:
            progress.setValue(len(self.playlist_manager.channels))
            progress.close()
            
            # Actualizar la lista solo si no fue cancelada
            if not was_cancelled:
                self.update_channel_list(self.group_filter.currentText())
                
                # Mostrar resumen de verificación
                online_count = sum(1 for ch in self.playlist_manager.channels if ch.status == 'online')
                slow_count = sum(1 for ch in self.playlist_manager.channels if ch.status == 'slow')
                offline_count = sum(1 for ch in self.playlist_manager.channels if ch.status == 'offline')
                
                if was_cancelled:
                    message = "La verificación fue cancelada.\n\nResultados parciales:"
                else:
                    message = "Verificación completada.\n\nResultados:"
                
                print(f'{message}\n'
                      f'- Canales en línea: {online_count}\n'
                      f'- Canales lentos: {slow_count}\n'
                      f'- Canales fuera de línea: {offline_count}\n'
                      f'- Total verificado: {completed_count}')
    
    def save_working_channels(self):
        file_name, _ = QFileDialog.getSaveFileName(self, 'Guardar Canales Funcionales',
                                                '', 'M3U Files (*.m3u *.m3u8)')
        if file_name:
            self.playlist_manager.save_working_channels(file_name)
            print(f'Los canales funcionales han sido guardados en:\n{file_name}')
                              
    def download_playlist(self):
        url, ok = QInputDialog.getText(self, 'Descargar Lista M3U', 
                                     'Ingrese la URL de la lista M3U:')
        if ok and url:
            # Mostrar diálogo de progreso
            progress = QProgressDialog('Descargando lista...', 'Cancelar', 0, 0, self)
            progress.setWindowModality(Qt.WindowModality.WindowModal)
            progress.setStyleSheet(f"""
                QProgressDialog {{
                    background-color: {ModernStyle.MEDIUM_BG};
                    color: {ModernStyle.TEXT_COLOR};
                }}
            """)
            progress.show()
            
            try:
                # Configurar una política de manejo de eventos para evitar errores de conexión
                asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
                
                print(f"Iniciando descarga desde URL: {url}")
                # Descargar la lista con manejo de excepciones mejorado
                success, message, file_path = self.playlist_manager.download_playlist_from_url_sync(url)
                
                if success:
                    try:
                        print(f"Descarga exitosa, cargando lista desde: {file_path}")
                        # Cargar la lista descargada
                        self.playlist_manager.load_playlist(file_path)
                        self.playlist_manager.save_last_playlist()
                        
                        # Actualizar filtro de grupos
                        self.group_filter.clear()
                        self.group_filter.addItem('Todos los grupos')
                        self.group_filter.addItems(self.playlist_manager.groups)
                        
                        # Mostrar canales
                        self.update_channel_list('Todos los grupos')
                        
                        self.status_label.setText(f"Lista descargada: {len(self.playlist_manager.channels)} canales en {len(self.playlist_manager.groups)} grupos")
                        
                    except Exception as e:
                        print(f"Error al cargar la lista descargada: {e}")
                else:
                    print(f"Error en la descarga: {message}")
            except Exception as e:
                print(f"Error inesperado durante la descarga: {e}")
            finally:
                progress.close()
    
    def show_fixed_menu(self):
        """Muestra un menú contextual fijo con las opciones principales"""
        try:
            print("Mostrando menú fijo")
            
            # Crear un menú directamente
            menu = QMenu(self)
            menu.setStyleSheet(ModernStyle.MENU_STYLE)
            
            # Opción de pantalla completa
            fullscreen_action = QAction('Pantalla Completa', self)
            fullscreen_action.triggered.connect(self.toggle_fullscreen)
            menu.addAction(fullscreen_action)
            
            # Opciones de escala de video
            scale_menu = QMenu('Escala de Video', self)
            scale_menu.setStyleSheet(ModernStyle.MENU_STYLE)
            
            for scale in ['0.5', '1.0', '1.5', '2.0']:
                scale_action = QAction(f'Escala {scale}x', self)
                scale_action.triggered.connect(lambda checked, s=scale: self.set_scale_mode(s))
                scale_menu.addAction(scale_action)
                
            menu.addMenu(scale_menu)
            
            # Opciones de relación de aspecto
            aspect_menu = QMenu('Relación de Aspecto', self)
            aspect_menu.setStyleSheet(ModernStyle.MENU_STYLE)
            
            for aspect, label in [
                ('', 'Predeterminado'),
                ('16:9', '16:9 Panorámico'),
                ('4:3', '4:3 Estándar'),
                ('1:1', '1:1 Cuadrado'),
                ('16:10', '16:10 Pantalla Ancha'),
                ('2.35:1', '2.35:1 Cinemático')
            ]:
                aspect_action = QAction(label, self)
                aspect_action.triggered.connect(lambda checked, a=aspect: self.set_aspect_ratio(a))
                aspect_menu.addAction(aspect_action)
                
            menu.addMenu(aspect_menu)
            
            # Pistas de audio si están disponibles
            if hasattr(self, 'audio_tracks') and self.audio_tracks:
                try:
                    audio_menu = QMenu('Pistas de Audio', self)
                    audio_menu.setStyleSheet(ModernStyle.MENU_STYLE)
                    
                    for track in self.audio_tracks:
                        track_id, track_name = track
                        track_action = QAction(f'{track_name.decode("utf-8", errors="replace")}', self)
                        track_action.triggered.connect(lambda checked, t=track_id: self.change_audio_track(t))
                        audio_menu.addAction(track_action)
                    
                    menu.addMenu(audio_menu)
                except Exception as e:
                    print(f"Error al añadir pistas de audio al menú: {e}")
        
            # Mostrar el menú en la posición del cursor
            cursor_pos = QCursor.pos()
            print(f"Mostrando menú en posición: {cursor_pos.x()}, {cursor_pos.y()}")
            menu.exec(cursor_pos)
            
        except Exception as e:
            print(f"Error al mostrar el menú fijo: {e}")
            traceback.print_exc()
    
    def show_video_context_menu(self, position):
        """Muestra el menú contextual para el widget de video"""
        try:
            print(f"Iniciando show_video_context_menu con posición: {position}")
            # Redirigir al menú fijo para mantener consistencia
            self.show_fixed_menu()
        except Exception as e:
            print(f"Error en show_video_context_menu: {e}")
            traceback.print_exc()
    
    def set_scale_mode(self, scale):
        try:
            scale = float(scale)
            self.player.video_set_scale(scale)
            self.current_scale = scale
            print(f"Escala de video cambiada a: {scale}")
        except Exception as e:
            print(f"Error al cambiar la escala del video: {e}")
    
    def change_audio_track(self, track_id):
        try:
            if not self.player.get_media():
                print("No hay medio cargado para cambiar la pista de audio")
                return False
            result = self.player.audio_set_track(track_id)
            if result:
                print(f"Pista de audio cambiada a ID: {track_id}")
                return True
            else:
                print(f"Error al cambiar la pista de audio a ID: {track_id}")
                return False
        except Exception as e:
            print(f"Excepción al cambiar pista de audio: {e}")
            return False
            
    def set_aspect_ratio(self, aspect_ratio):
        """Cambia la relación de aspecto del video"""
        try:
            if not self.player.get_media():
                print("No hay medio cargado para cambiar la relación de aspecto")
                return False
            
            # Establecer la relación de aspecto
            self.player.video_set_aspect_ratio(aspect_ratio)
            self.current_aspect_ratio = aspect_ratio
            print(f"Relación de aspecto cambiada a: {aspect_ratio}")
            return True
        except Exception as e:
            print(f"Error al cambiar la relación de aspecto: {e}")
            return False
            
    def update_menu_button_position(self):
        """Actualiza la posición del botón de menú para que aparezca sobre el video"""
        try:
            if hasattr(self, 'button_container') and hasattr(self, 'video_widget'):
                # Verificar si hay reproducción activa
                if not self.player or not self.player.is_playing():
                    self.button_container.hide()
                    return
                    
                # Obtener coordenadas globales del widget de video
                video_pos = self.video_widget.mapToGlobal(QPoint(0, 0))
                # Convertir a coordenadas relativas a la ventana principal
                rel_pos = self.mapFromGlobal(video_pos)
                
                # Posicionar el botón en la esquina superior izquierda del video
                self.button_container.move(rel_pos.x() + 10, rel_pos.y() + 10)
                
                # Asegurar que el botón esté visible solo si hay reproducción
                if self.player and self.player.is_playing():
                    self.button_container.show()
                    self.button_container.raise_()
                    self.menu_button.raise_()
                else:
                    self.button_container.hide()
                
                print(f"Botón posicionado en: {rel_pos.x() + 10}, {rel_pos.y() + 10}")
        except Exception as e:
            print(f"Error al actualizar posición del botón: {e}")
    
    def stop_playback(self):
        """Detiene la reproducción actual"""
        if self.player:
            self.player.stop()
            self.status_label.setText("Reproducción detenida")
            
            # Ocultar el botón de menú cuando se detiene la reproducción
            if hasattr(self, 'button_container'):
                self.button_container.hide()
                
            # Detener el timer de visibilidad
            if hasattr(self, 'button_visibility_timer'):
                self.button_visibility_timer.stop()
                
    def resizeEvent(self, event):
        super().resizeEvent(event)
        if hasattr(self, 'overlay_widget'):
            self.overlay_widget.resize(self.video_widget.size())
            
        # Actualizar posición del botón de menú
        self.update_menu_button_position()
    
    def keyPressEvent(self, event):
        # Asegura que los atajos funcionen incluso si el foco está en el botón flotante
        if event.key() == Qt.Key.Key_F11 or \
           (event.key() == Qt.Key.Key_Return and event.modifiers() == Qt.KeyboardModifier.AltModifier):
            self.toggle_fullscreen()
        elif event.key() == Qt.Key.Key_Escape and self.isFullScreen():
            print("ESC detectado, intentando salir de pantalla completa")
            self.toggle_fullscreen()
        else:
            super().keyPressEvent(event)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    player = ModernTVIPPlayer()
    player.show()
    sys.exit(app.exec())
