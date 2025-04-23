import sys
import os
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
        QComboBox::down-arrow {{
            image: url(resources/down-arrow.png);
            width: 12px;
            height: 12px;
        }}
        QComboBox QAbstractItemView {{
            background-color: {MEDIUM_BG};
            color: {TEXT_COLOR};
            selection-background-color: {ACCENT_COLOR};
            selection-color: {DARK_BG};
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

class TVIPPlayer(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle('TV IP Player')
        self.setGeometry(100, 100, 1200, 700)
        self.setMinimumSize(900, 600)
        self.installEventFilter(self)
        
        # Aplicar estilo moderno a toda la aplicación
        self.apply_modern_style()
        
        # Variables para control de panel lateral
        self.sidebar_visible = True
        self.is_fullscreen_mode = False
        self.sidebar_hover_margin = 20
        self.sidebar_position = "right"  # Nueva variable para controlar la posición del sidebar (right o left)
        self.mouse_check_timer = QTimer(self)
        self.mouse_check_timer.timeout.connect(self.check_mouse_position)
        self.mouse_check_timer.start(100)
        
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
        self.channel_list.setStyleSheet(ModernStyle.LIST_STYLE)
        self.channel_list.itemClicked.connect(self.play_channel)
        sidebar_layout.addWidget(self.channel_list)
        
        # Botones de control
        buttons_grid = QGridLayout()
        buttons_grid.setSpacing(10)
        
        # Primera fila de botones
        load_button = QPushButton('Cargar Lista')
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
        
        save_working_button = QPushButton('Guardar Funcionando')
        save_working_button.clicked.connect(self.save_working_channels)
        save_working_button.setStyleSheet(ModernStyle.BUTTON_STYLE)
        save_working_button.setMinimumWidth(140)
        
        buttons_grid.addWidget(check_button, 1, 0)
        buttons_grid.addWidget(save_working_button, 1, 1)
        
        # Tercera fila de botones (nueva)
        unify_button = QPushButton('Unificar Canales')
        unify_button.clicked.connect(self.unify_channels)
        unify_button.setStyleSheet(ModernStyle.BUTTON_STYLE)
        unify_button.setMinimumWidth(140)
        unify_button.setToolTip('Elimina canales duplicados y unifica nombres similares')
        
        buttons_grid.addWidget(unify_button, 2, 0, 1, 2)  # Ocupa dos columnas
        
        sidebar_layout.addLayout(buttons_grid)
        
        # Área de video
        video_container = QWidget()
        self.video_layout = QVBoxLayout(video_container)
        self.video_layout.setContentsMargins(0, 0, 0, 0)
        video_container.setStyleSheet(f"background-color: {ModernStyle.DARK_BG};")
        video_container.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        
        # Widget para el video
        self.video_widget = QWidget()
        self.video_widget.setStyleSheet(f"background-color: {ModernStyle.DARK_BG};")
        self.video_widget.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.video_widget.customContextMenuRequested.connect(self.show_video_context_menu)
        
        # Overlay transparente para capturar eventos de ratón
        self.overlay_widget = QWidget(self.video_widget)
        self.overlay_widget.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, False)
        self.overlay_widget.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.overlay_widget.customContextMenuRequested.connect(self.show_video_context_menu)
        self.overlay_widget.setStyleSheet("background-color: rgba(0, 0, 0, 0);")
        self.overlay_widget.resize(self.video_widget.size())
        
        # Botón flotante de menú contextual
        self.menu_button = QPushButton("≡", self)
        self.menu_button.setStyleSheet(ModernStyle.MENU_BUTTON_STYLE)
        self.menu_button.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.menu_button.setFixedSize(28, 28)
        self.menu_button.setToolTip('Menú de video')
        self.menu_button.clicked.connect(lambda: self.show_video_context_menu(self.menu_button.pos()))
        self.menu_button.move(10, 10)
        
        self.video_layout.addWidget(self.video_widget)
        
        # Etiqueta de estado
        self.status_label = QLabel("Listo")
        self.status_label.setStyleSheet(ModernStyle.LABEL_STYLE)
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
                
                self.status_label.setText(f"Lista cargada: {len(self.playlist_manager.channels)} canales")
                
                QMessageBox.information(self, 'Lista Cargada', 
                                      f'Se cargaron {len(self.playlist_manager.channels)} canales en {len(self.playlist_manager.groups)} grupos.')
            except Exception as e:
                # Mostrar un mensaje de error detallado al usuario
                error_message = f"Error al cargar la lista: {str(e)}"
                print(error_message)  # Imprimir en consola para depuración
                QMessageBox.critical(self, "Error de carga", 
                                   error_message + "\n\nRevise el formato de la lista y asegúrese de que sea un archivo M3U válido.")
    
    def update_channel_list(self, group: str):
        self.channel_list.clear()
        channels = self.playlist_manager.get_channels_by_group(group)
        for channel in channels:
            item = QListWidgetItem()
            # Crear un widget personalizado para cada canal
            channel_widget = QWidget()
            layout = QHBoxLayout(channel_widget)
            layout.setContentsMargins(5, 5, 5, 5)
            
            # Nombre del canal
            name_label = QLabel(channel.name)
            name_label.setStyleSheet(f"color: {ModernStyle.TEXT_COLOR}; font-weight: bold;")
            layout.addWidget(name_label)
            
            # Estado del canal
            status_label = QLabel()
            if channel.status == 'online':
                status_label.setStyleSheet('color: #4CAF50;')  # Verde
                status_label.setText('✓ Online')
            elif channel.status == 'slow':
                status_label.setStyleSheet('color: #FF9800;')  # Naranja
                status_label.setText('⚠ Lento')
            elif channel.status == 'offline':
                status_label.setStyleSheet('color: #F44336;')  # Rojo
                status_label.setText('✗ Offline')
            else:
                status_label.setText('? Desconocido')
            
            layout.addWidget(status_label)
            layout.addStretch()
            
            # Tiempo de respuesta si está disponible
            if channel.response_time is not None:
                response_label = QLabel(f'{channel.response_time:.2f}s')
                response_label.setStyleSheet(f'color: {ModernStyle.LIGHT_BG};')
                layout.addWidget(response_label)
            
            channel_widget.setLayout(layout)
            
            # Configurar el item
            item.setSizeHint(channel_widget.sizeHint())
            item.setData(Qt.ItemDataRole.UserRole, channel)
            self.channel_list.addItem(item)
            self.channel_list.setItemWidget(item, channel_widget)
            
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
                
                self.status_label.setText(f"Reproduciendo: {channel.name}")
                
        except Exception as e:
            print(f"Error al reproducir canal: {e}")
            QMessageBox.warning(self, "Error de Reproducción", 
                              f"No se pudo reproducir el canal: {str(e)}")
                              
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
        QMessageBox.information(self, 'Verificación de Canales', 
                              'Esta función se ha simplificado en esta versión estética.\nUtilice la versión completa para verificar canales.')
    
    def save_working_channels(self):
        QMessageBox.information(self, 'Guardar Canales', 
                              'Esta función se ha simplificado en esta versión estética.\nUtilice la versión completa para guardar canales funcionales.')
                              
    def download_playlist(self):
        QMessageBox.information(self, 'Descargar Lista', 
                              'Esta función se ha simplificado en esta versión estética.\nUtilice la versión completa para descargar listas.')
    
    def unify_channels(self):
        """Elimina canales duplicados por URL y unifica nombres similares"""
        if not self.playlist_manager.channels:
            QMessageBox.warning(self, "Sin canales", "No hay canales para unificar.")
            return
            
        # Mostrar diálogo de progreso
        progress = QProgressDialog("Unificando canales...", "Cancelar", 0, 100, self)
        progress.setWindowTitle("Unificando canales")
        progress.setWindowModality(Qt.WindowModality.WindowModal)
        progress.setMinimumDuration(0)
        progress.setValue(10)
        
        # Obtener conteo inicial
        initial_count = len(self.playlist_manager.channels)
        
        # Unificar canales
        self.playlist_manager.remove_duplicate_channels()
        
        # Actualizar progreso
        progress.setValue(80)
        
        # Obtener conteo final
        final_count = len(self.playlist_manager.channels)
        removed_count = initial_count - final_count
        
        # Guardar la lista actualizada
        self.playlist_manager.save_last_playlist()
        
        # Actualizar la interfaz
        self.group_filter.clear()
        self.group_filter.addItem("Todos los grupos")
        self.group_filter.addItems(sorted(self.playlist_manager.groups))
        self.update_channel_list('Todos los grupos')
        
        # Actualizar etiqueta de estado
        self.status_label.setText(f"Lista unificada: {len(self.playlist_manager.channels)} canales")
        
        # Completar progreso
        progress.setValue(100)
        
        # Mostrar mensaje de éxito
        QMessageBox.information(
            self, 
            "Canales unificados", 
            f"Se han eliminado {removed_count} canales duplicados.\n"
            f"La lista ahora contiene {final_count} canales únicos ordenados por nombre."
        )
        
    def show_video_context_menu(self, position):
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
        
        # Mostrar el menú en la posición global
        if isinstance(position, QListWidgetItem):
            # Si se llamó desde un botón, usar la posición del botón
            position = self.menu_button.mapToGlobal(self.menu_button.rect().bottomRight())
        else:
            # Si se llamó desde un clic derecho, usar la posición del clic
            position = self.video_widget.mapToGlobal(position)
            
        context_menu.exec(position)
        
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

    def resizeEvent(self, event):
        super().resizeEvent(event)
        if hasattr(self, 'menu_button'):
            # Actualizar posición del botón flotante
            video_rect = self.video_widget.geometry()
            video_top_left = self.video_widget.mapTo(self, video_rect.topLeft())
            self.menu_button.move(video_top_left.x() + 10, video_top_left.y() + 10)
        if hasattr(self, 'overlay_widget'):
            self.overlay_widget.resize(self.video_widget.size())

if __name__ == '__main__':
    app = QApplication(sys.argv)
    player = TVIPPlayer()
    player.show()
    sys.exit(app.exec())