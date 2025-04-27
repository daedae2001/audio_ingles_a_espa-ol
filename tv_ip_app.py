import sys
import os
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout,
                             QHBoxLayout, QListWidget, QLabel, QPushButton,
                             QComboBox, QFileDialog, QListWidgetItem, QSizePolicy,
                             QProgressDialog, QInputDialog, QMessageBox, QMenu, QGridLayout)
from PyQt6.QtCore import Qt, QEvent, QTimer, QPoint, QSize, pyqtSlot, Q_ARG, QMetaObject
from PyQt6.QtGui import QKeyEvent, QColor, QCursor, QAction, QIcon, QPalette, QFont
import vlc
import asyncio
from playlist_manager import PlaylistManager, Channel
import threading
from PyQt6.QtCore import QObject, QThread, pyqtSignal
import time
from datetime import datetime

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
        self.setGeometry(100, 100, 1280, 720)
        self.setStyleSheet(f"background-color: {ModernStyle.DARK_BG}; color: {ModernStyle.TEXT_COLOR};")
        
        # Crear instancia de PlaylistManager
        self.playlist_manager = PlaylistManager()
        
        # Crear widgets principales
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        
        # Crear layout principal
        main_layout = QVBoxLayout(self.central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        # Crear barra de título personalizada
        title_bar = QWidget()
        title_bar.setStyleSheet(f"background-color: {ModernStyle.ACCENT_COLOR};")
        title_bar.setFixedHeight(40)
        title_bar_layout = QHBoxLayout(title_bar)
        title_bar_layout.setContentsMargins(10, 0, 10, 0)
        
        # Título de la aplicación
        title_label = QLabel("TV IP Player")
        title_label.setStyleSheet("color: #000000; font-weight: bold; font-size: 16px;")
        title_bar_layout.addWidget(title_label)
        
        # Agregar barra de título al layout principal
        main_layout.addWidget(title_bar)
        
        # Layout para el contenido principal
        content_layout = QHBoxLayout()
        content_layout.setContentsMargins(10, 10, 10, 10)
        content_layout.setSpacing(10)
        
        # Panel izquierdo para lista de canales y controles
        left_panel = QWidget()
        left_panel.setObjectName("left_panel")  # Asignar un nombre para poder referenciarlo
        left_panel.setStyleSheet(f"background-color: {ModernStyle.MEDIUM_BG};")
        left_panel_layout = QVBoxLayout(left_panel)
        
        # Filtro de grupos
        self.group_filter = QComboBox()
        self.group_filter.setStyleSheet(f"""
            QComboBox {{
                background-color: {ModernStyle.LIGHT_BG};
                color: {ModernStyle.TEXT_COLOR};
                border: 1px solid {ModernStyle.ACCENT_COLOR};
                border-radius: 4px;
                padding: 5px;
                min-height: 25px;
            }}
            QComboBox::drop-down {{
                border: none;
                width: 20px;
            }}
            QComboBox QAbstractItemView {{
                background-color: {ModernStyle.MEDIUM_BG};
                color: {ModernStyle.TEXT_COLOR};
                border: 1px solid {ModernStyle.ACCENT_COLOR};
                selection-background-color: {ModernStyle.ACCENT_COLOR};
                selection-color: {ModernStyle.DARK_BG};
            }}
        """)
        self.group_filter.addItem("Todos los grupos")
        self.group_filter.currentTextChanged.connect(self.update_channel_list)
        left_panel_layout.addWidget(self.group_filter)
        
        # Lista de canales
        self.channel_list = QListWidget()
        self.channel_list.setStyleSheet(f"""
            QListWidget {{
                background-color: {ModernStyle.DARK_BG};
                color: {ModernStyle.TEXT_COLOR};
                border: 1px solid {ModernStyle.ACCENT_COLOR};
                border-radius: 4px;
                padding: 5px;
            }}
            QListWidget::item {{
                padding: 5px;
                border-bottom: 1px solid {ModernStyle.LIGHT_BG};
            }}
            QListWidget::item:selected {{
                background-color: {ModernStyle.ACCENT_COLOR};
                color: {ModernStyle.DARK_BG};
            }}
            QListWidget::item:hover {{
                background-color: {ModernStyle.LIGHT_BG};
            }}
        """)
        self.channel_list.itemDoubleClicked.connect(self.play_channel)
        left_panel_layout.addWidget(self.channel_list)
        
        # Botones de acción
        buttons_layout = QGridLayout()
        buttons_layout.setSpacing(5)
        
        # Botón para cargar lista
        load_button = QPushButton("Cargar Lista")
        load_button.setStyleSheet(ModernStyle.BUTTON_STYLE)
        load_button.clicked.connect(self.load_playlist)
        buttons_layout.addWidget(load_button, 0, 0)
        
        # Botón para verificar canales
        check_button = QPushButton("Verificar Canales")
        check_button.setStyleSheet(ModernStyle.BUTTON_STYLE)
        check_button.clicked.connect(self.check_channels)
        buttons_layout.addWidget(check_button, 0, 1)
        
        # Botón para guardar canales que funcionan
        save_button = QPushButton("Guardar Funcionando")
        save_button.setStyleSheet(ModernStyle.BUTTON_STYLE)
        save_button.clicked.connect(self.save_working_channels)
        buttons_layout.addWidget(save_button, 1, 0)
        
        # Botón para unificar canales
        unify_button = QPushButton("Unificar Canales")
        unify_button.setStyleSheet(ModernStyle.BUTTON_STYLE)
        unify_button.clicked.connect(self.unify_channels)
        buttons_layout.addWidget(unify_button, 1, 1)
        
        # Botón para guardar canales unificados
        save_unified_button = QPushButton("Guardar Unificados")
        save_unified_button.setStyleSheet(ModernStyle.BUTTON_STYLE)
        save_unified_button.clicked.connect(self.save_unified_channels)
        buttons_layout.addWidget(save_unified_button, 2, 0, 1, 2)  # Ocupa dos columnas
        
        left_panel_layout.addLayout(buttons_layout)
        
        # Etiqueta de estado
        self.status_label = QLabel("Listo")
        self.status_label.setStyleSheet(f"color: {ModernStyle.TEXT_COLOR}; padding: 5px;")
        left_panel_layout.addWidget(self.status_label)
        
        # Configurar ancho del panel izquierdo
        left_panel.setFixedWidth(300)
        content_layout.addWidget(left_panel)
        
        # Panel derecho para el reproductor de video
        self.video_frame = QWidget()
        self.video_frame.setStyleSheet("background-color: black;")
        self.video_frame.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        
        # Crear instancia de VLC
        self.instance = vlc.Instance()
        self.player = self.instance.media_player_new()
        
        # Configurar el reproductor de VLC para usar el widget de video
        if sys.platform == "win32":
            self.player.set_hwnd(int(self.video_frame.winId()))
        else:
            self.player.set_xwindow(self.video_frame.winId())
        
        content_layout.addWidget(self.video_frame)
        
        # Agregar el contenido principal al layout principal
        main_layout.addLayout(content_layout)
        
        # Crear botón de menú contextual (inicialmente oculto)
        self.menu_button = QPushButton("≡", self)
        self.menu_button.setStyleSheet(f"""
            QPushButton {{
                background-color: rgba(0, 0, 0, 120);
                color: white;
                border: 1px solid {ModernStyle.ACCENT_COLOR};
                border-radius: 4px;
                font-size: 16px;
                padding: 5px;
                min-width: 30px;
                min-height: 30px;
            }}
            QPushButton:hover {{
                background-color: {ModernStyle.ACCENT_COLOR};
                color: black;
            }}
        """)
        self.menu_button.setFixedSize(30, 30)
        self.menu_button.hide()
        self.menu_button.clicked.connect(self.show_context_menu)
        
        # Crear temporizador para verificar si se está reproduciendo video
        self.check_playing_timer = QTimer(self)
        self.check_playing_timer.timeout.connect(self.check_playing_status)
        self.check_playing_timer.start(1000)  # Verificar cada segundo
        
        # Instalar filtro de eventos para manejar teclas y eventos del ratón
        self.installEventFilter(self)
        
        # Variable para almacenar el canal actual
        self.current_channel = None
        
        # Configurar la aplicación para recibir eventos de teclado
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        
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
        
        # Inicializar variables para la barra lateral
        self.left_panel_visible = True
        self.sidebar_timer = QTimer(self)
        self.sidebar_timer.setSingleShot(True)
        self.sidebar_timer.timeout.connect(self.hide_sidebar)
        
        # Configurar el seguimiento del ratón para detectar movimientos
        self.setMouseTracking(True)
    
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
        if not self.isFullScreen():
            return
            
        cursor_pos = QCursor.pos()
        window_pos = self.mapToGlobal(QPoint(0, 0))
        window_width = self.width()
        relative_x = cursor_pos.x() - window_pos.x()
        
        # Verificar si el cursor está cerca del borde derecho
        if relative_x >= (window_width - 20) and not self.menu_button.isVisible():
            # El cursor está cerca del borde derecho, mostrar el panel
            self.menu_button.show()
        # Verificar si el cursor está lejos del panel cuando está visible
        elif self.menu_button.isVisible():
            # Si está a la derecha, verificar si el cursor está lejos del borde derecho
            if relative_x < (window_width - self.menu_button.width() - 10):
                self.menu_button.hide()

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
                progress.setMinimumSize(400, 150)  # Hacer el diálogo más grande
                
                # Establecer una fuente más grande y visible
                font = QFont()
                font.setPointSize(10)
                font.setBold(True)
                progress.setFont(font)
                
                # Estilo con colores de alto contraste
                progress.setStyleSheet(f"""
                    QProgressDialog {{
                        background-color: {ModernStyle.DARK_BG};
                        color: white;
                        border: 1px solid {ModernStyle.ACCENT_COLOR};
                        padding: 10px;
                    }}
                    QProgressBar {{
                        border: 1px solid {ModernStyle.ACCENT_COLOR};
                        border-radius: 4px;
                        background-color: #121212;
                        color: white;
                        text-align: center;
                        min-height: 20px;
                    }}
                    QProgressBar::chunk {{
                        background-color: {ModernStyle.ACCENT_COLOR};
                        width: 10px;
                    }}
                    QPushButton {{
                        background-color: {ModernStyle.MEDIUM_BG};
                        color: white;
                        border: 1px solid {ModernStyle.ACCENT_COLOR};
                        border-radius: 4px;
                        padding: 5px 10px;
                        min-width: 80px;
                    }}
                    QPushButton:hover {{
                        background-color: {ModernStyle.ACCENT_COLOR};
                        color: black;
                    }}
                    QLabel {{
                        color: white;
                        font-weight: bold;
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
            layout.setContentsMargins(8, 8, 8, 8)  # Aumentar márgenes
            layout.setSpacing(10)  # Aumentar espacio entre elementos
            
            # Nombre del canal
            name_label = QLabel(channel.name)
            name_label.setStyleSheet(f"""
                color: {ModernStyle.TEXT_COLOR}; 
                font-weight: bold;
                font-size: 12px;
                background-color: transparent;
            """)
            name_label.setMinimumWidth(200)  # Asegurar un ancho mínimo
            name_label.setMaximumWidth(300)  # Limitar el ancho máximo
            name_label.setWordWrap(True)     # Permitir múltiples líneas
            layout.addWidget(name_label, 1)  # Dar más espacio al nombre
            
            # Estado del canal
            status_label = QLabel()
            status_label.setStyleSheet("""
                font-weight: bold;
                font-size: 11px;
                background-color: transparent;
                padding: 2px 5px;
                border-radius: 3px;
            """)
            
            if channel.status == 'online':
                status_label.setStyleSheet(status_label.styleSheet() + 'color: #4CAF50; background-color: rgba(76, 175, 80, 0.1);')  # Verde
                status_label.setText('✓ Online')
            elif channel.status == 'slow':
                status_label.setStyleSheet(status_label.styleSheet() + 'color: #FF9800; background-color: rgba(255, 152, 0, 0.1);')  # Naranja
                status_label.setText('⚠ Lento')
            elif channel.status == 'offline':
                status_label.setStyleSheet(status_label.styleSheet() + 'color: #F44336; background-color: rgba(244, 67, 54, 0.1);')  # Rojo
                status_label.setText('✗ Offline')
            else:
                status_label.setStyleSheet(status_label.styleSheet() + 'color: #9E9E9E; background-color: rgba(158, 158, 158, 0.1);')  # Gris
                status_label.setText('? Desconocido')
            
            status_label.setFixedWidth(80)  # Ancho fijo para el estado
            layout.addWidget(status_label)
            
            # Tiempo de respuesta si está disponible
            if channel.response_time is not None:
                response_label = QLabel(f'{channel.response_time:.2f}s')
                response_label.setStyleSheet(f"""
                    color: {ModernStyle.TEXT_COLOR};
                    background-color: {ModernStyle.LIGHT_BG};
                    font-size: 11px;
                    padding: 2px 5px;
                    border-radius: 3px;
                """)
                response_label.setFixedWidth(60)  # Ancho fijo para el tiempo
                layout.addWidget(response_label)
            else:
                # Añadir un espacio vacío para mantener la alineación
                spacer = QLabel("")
                spacer.setFixedWidth(60)
                layout.addWidget(spacer)
            
            # Configurar el item
            item.setSizeHint(QSize(channel_widget.sizeHint().width(), max(50, channel_widget.sizeHint().height())))  # Altura mínima
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
        print(f"toggle_fullscreen llamado. isFullScreen()={self.isFullScreen()}")
        if not self.isFullScreen():
            self.normal_geometry = self.geometry()
            self.showFullScreen()
            
            # Ocultar la barra lateral en pantalla completa
            if self.isFullScreen():
                self.hide_sidebar()
        else:
            self.showNormal()
            if hasattr(self, 'normal_geometry'):
                self.setGeometry(self.normal_geometry)
            
            # Mostrar la barra lateral al salir de pantalla completa
            self.show_sidebar()
    
    def hide_sidebar(self):
        """Oculta la barra lateral"""
        left_panel = self.findChild(QWidget, "left_panel")
        if left_panel and self.left_panel_visible:
            left_panel.hide()
            self.left_panel_visible = False
    
    def show_sidebar(self):
        """Muestra la barra lateral"""
        left_panel = self.findChild(QWidget, "left_panel")
        if left_panel and not self.left_panel_visible:
            left_panel.show()
            self.left_panel_visible = True
            
            # Asegurarse de que la barra lateral esté visible y en primer plano
            left_panel.raise_()
            
            # Iniciar temporizador para ocultar la barra lateral después de 3 segundos
            if self.isFullScreen():
                self.sidebar_timer.start(3000)  # 3000 ms = 3 segundos
    
    def eventFilter(self, obj, event):
        """Filtro de eventos para manejar eventos de teclado y ratón"""
        try:
            # Manejar clic derecho en el video_frame
            if obj == self.video_frame and event.type() == QEvent.Type.MouseButtonPress:
                if event.button() == Qt.MouseButton.RightButton:
                    self.show_context_menu()
                    return True
                
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
            print(f"Error en el manejo de eventos: {str(e)}")
            return False
            
    def check_channels(self):
        """Verifica el estado de todos los canales en la lista"""
        if not self.playlist_manager.channels:
            QMessageBox.warning(self, "Sin canales", "No hay canales para verificar.")
            return
        
        # Crear un worker para la verificación en segundo plano
        class VerificationWorker(QObject):
            finished = pyqtSignal()
            progress = pyqtSignal(int, str, int, int, int)
            error = pyqtSignal(str)
            
            def __init__(self, playlist_manager):
                super().__init__()
                self.playlist_manager = playlist_manager
                self.canceled = False
                
            def cancel(self):
                self.canceled = True
                
            def run(self):
                try:
                    # Ejecutar la verificación de canales
                    self._run_verification()
                    self.finished.emit()
                except Exception as e:
                    # Asegurar que el mensaje de error sea seguro para mostrar
                    safe_error = str(e).encode('utf-8', 'replace').decode('utf-8')
                    self.error.emit(safe_error)
                    
            def _run_verification(self):
                # Preparar contadores
                total = len(self.playlist_manager.channels)
                verified = 0
                online = 0
                slow = 0
                offline = 0
                
                # Función para verificar un canal
                def check_channel(channel):
                    nonlocal verified, online, slow, offline
                    
                    if self.canceled:
                        return
                        
                    try:
                        # Obtener un nombre seguro para mostrar
                        try:
                            safe_name = str(channel.name).encode('utf-8', 'replace').decode('utf-8')
                        except Exception:
                            safe_name = f"Canal #{verified+1}"
                        
                        # Verificar el canal de forma sincrónica
                        result = self._check_channel_sync(channel)
                        
                        # Actualizar contadores
                        if result == 'online':
                            online += 1
                        elif result == 'slow':
                            slow += 1
                        else:
                            offline += 1
                            
                        # Actualizar progreso
                        verified += 1
                        try:
                            self.progress.emit(verified, safe_name, online, slow, offline)
                        except Exception as e:
                            print(f"Error al emitir progreso: {str(e)}")
                            # Emitir con un nombre genérico en caso de error
                            self.progress.emit(verified, f"Canal #{verified}", online, slow, offline)
                    except Exception as e:
                        try:
                            error_msg = f"Error al verificar canal {safe_name if 'safe_name' in locals() else 'desconocido'}: {str(e)}"
                            print(error_msg.encode('utf-8', 'replace').decode('utf-8'))
                        except:
                            print(f"Error al verificar canal #{verified+1}")
                            
                        channel.status = 'offline'
                        channel.response_time = 0
                        offline += 1
                        verified += 1
                        self.progress.emit(verified, f"Canal #{verified}", online, slow, offline)
                
                # Verificar cada canal
                for channel in self.playlist_manager.channels:
                    if self.canceled:
                        break
                    check_channel(channel)
                    
                # Guardar resultados si no se canceló
                if not self.canceled:
                    self.playlist_manager.save_last_playlist()
            
            def _check_channel_sync(self, channel):
                """Versión sincrónica de check_channel para evitar problemas con asyncio"""
                import requests
                from urllib.parse import urlparse
                
                # Configurar timeout y verificación SSL
                timeout = 5  # segundos
                verify_ssl = False
                
                try:
                    # Validar URL
                    parsed_url = urlparse(channel.url)
                    if not parsed_url.scheme or not parsed_url.netloc:
                        channel.status = 'offline'
                        channel.response_time = 0
                        return 'offline'
                    
                    # Intentar HEAD primero (más rápido)
                    start_time = time.time()
                    response = requests.head(
                        channel.url, 
                        timeout=timeout, 
                        verify=verify_ssl,
                        allow_redirects=True
                    )
                    
                    # Si HEAD no funciona, intentar GET
                    if response.status_code != 200:
                        response = requests.get(
                            channel.url, 
                            timeout=timeout, 
                            verify=verify_ssl,
                            stream=True,  # No descargar todo el contenido
                            allow_redirects=True
                        )
                        
                        # Leer solo un poco del contenido
                        if response.status_code == 200:
                            for chunk in response.iter_content(chunk_size=1024):
                                if chunk:
                                    break
                    
                    # Calcular tiempo de respuesta
                    response_time = time.time() - start_time
                    
                    # Actualizar estado del canal
                    if response.status_code == 200:
                        if response_time < 2.0:
                            channel.status = 'online'
                        else:
                            channel.status = 'slow'
                        channel.response_time = response_time
                        return channel.status
                    else:
                        channel.status = 'offline'
                        channel.response_time = 0
                        return 'offline'
                        
                except Exception as e:
                    print(f"Error en verificación: {str(e)}")
                    channel.status = 'offline'
                    channel.response_time = 0
                    return 'offline'
                finally:
                    # Actualizar timestamp de verificación
                    channel.last_check = datetime.now().isoformat()
        
        # Crear diálogo de progreso
        progress = QProgressDialog("Preparando verificación...", "Cancelar", 0, len(self.playlist_manager.channels), self)
        progress.setWindowTitle("Verificación de canales")
        progress.setWindowModality(Qt.WindowModality.WindowModal)
        progress.setMinimumDuration(0)
        progress.setMinimumSize(400, 150)
        
        # Establecer una fuente más grande y visible
        font = QFont()
        font.setPointSize(10)
        font.setBold(True)
        progress.setFont(font)
        
        # Estilo con colores de alto contraste
        progress.setStyleSheet("""
            QProgressDialog {
                background-color: #1E1E1E;
                color: white;
                border: 1px solid #FF8000;
                padding: 10px;
            }
            QProgressBar {
                border: 1px solid #FF8000;
                border-radius: 4px;
                background-color: #121212;
                color: white;
                text-align: center;
                min-height: 20px;
            }
            QProgressBar::chunk {
                background-color: #FF8000;
                width: 10px;
            }
            QPushButton {
                background-color: #2D2D2D;
                color: white;
                border: 1px solid #FF8000;
                border-radius: 4px;
                padding: 5px 10px;
                min-width: 80px;
            }
            QPushButton:hover {
                background-color: #FF8000;
                color: black;
            }
            QLabel {
                color: white;
                font-weight: bold;
            }
        """)
        
        # Crear worker y thread
        self.verification_worker = VerificationWorker(self.playlist_manager)
        self.verification_thread = QThread()
        self.verification_worker.moveToThread(self.verification_thread)
        
        # Conectar señales
        self.verification_thread.started.connect(self.verification_worker.run)
        self.verification_worker.finished.connect(self.verification_thread.quit)
        self.verification_worker.finished.connect(self.verification_worker.deleteLater)
        self.verification_thread.finished.connect(self.verification_thread.deleteLater)
        
        # Conectar señal de progreso
        def update_progress(count, name, online, slow, offline):
            if progress.wasCanceled():
                return
                
            try:
                # Asegurar que el nombre del canal sea seguro para mostrar
                safe_name = str(name).encode('utf-8', 'replace').decode('utf-8')
                
                progress.setValue(count)
                progress.setLabelText(
                    f"Verificando canales...\n\n"
                    f"Progreso: {count} de {len(self.playlist_manager.channels)}\n"
                    f"Online: {online}, Lentos: {slow}, Offline: {offline}\n\n"
                    f"Canal actual: {safe_name}"
                )
                QApplication.processEvents()
            except Exception as e:
                print(f"Error al actualizar progreso: {str(e)}")
                # Intentar actualizar con información mínima
                try:
                    progress.setValue(count)
                    progress.setLabelText(f"Verificando canales... {count}/{len(self.playlist_manager.channels)}")
                    QApplication.processEvents()
                except:
                    pass
        
        self.verification_worker.progress.connect(update_progress)
        
        # Conectar señal de error
        self.verification_worker.error.connect(
            lambda error_msg: QMessageBox.critical(self, "Error", f"Error durante la verificación: {error_msg}")
        )
        
        # Conectar señal de finalización
        def verification_finished():
            if not progress.wasCanceled():
                # Actualizar la interfaz
                self.update_channel_list(self.group_filter.currentText())
                
                # Actualizar etiqueta de estado
                online_count = sum(1 for ch in self.playlist_manager.channels if ch.status == 'online')
                slow_count = sum(1 for ch in self.playlist_manager.channels if ch.status == 'slow')
                offline_count = sum(1 for ch in self.playlist_manager.channels if ch.status == 'offline')
                
                self.status_label.setText(f"Canales: {online_count} online, {slow_count} lentos, {offline_count} offline")
                
                # Mostrar mensaje de éxito
                QMessageBox.information(
                    self, 
                    "Verificación completada", 
                    f"Se han verificado {len(self.playlist_manager.channels)} canales.\n"
                    f"Resultado: {online_count} online, {slow_count} lentos, {offline_count} offline."
                )
            
            # Cerrar el diálogo de progreso
            progress.close()
        
        self.verification_thread.finished.connect(verification_finished)
        
        # Conectar señal de cancelación
        progress.canceled.connect(self.verification_worker.cancel)
        
        # Iniciar verificación
        self.verification_thread.start()

    def download_playlist(self):
        """Descarga una lista de reproducción desde una URL"""
        url, ok = QInputDialog.getText(
            self, 
            "Descargar Lista", 
            "Introduce la URL de la lista M3U:",
            text="http://"
        )
        
        if ok and url:
            try:
                # Mostrar diálogo de progreso
                progress = QProgressDialog("Descargando lista...", "Cancelar", 0, 100, self)
                progress.setWindowTitle("Descarga de Lista")
                progress.setWindowModality(Qt.WindowModality.WindowModal)
                progress.setMinimumDuration(0)
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
                
                # Función para actualizar el progreso
                def update_progress(percent):
                    if progress.wasCanceled():
                        return False
                    progress.setValue(int(percent))
                    QApplication.processEvents()
                    return True
                
                # Descargar la lista
                import requests
                import tempfile
                
                try:
                    response = requests.get(url, stream=True)
                    response.raise_for_status()
                    
                    # Crear archivo temporal
                    with tempfile.NamedTemporaryFile(delete=False, suffix='.m3u') as temp_file:
                        temp_path = temp_file.name
                        
                        # Descargar el contenido
                        with open(temp_path, 'wb') as f:
                            total_length = response.headers.get('content-length')
                            
                            if total_length is None:  # No se conoce el tamaño
                                f.write(response.content)
                                update_progress(100)
                            else:
                                total_length = int(total_length)
                                dl = 0
                                for data in response.iter_content(chunk_size=4096):
                                    dl += len(data)
                                    f.write(data)
                                    done = int(100 * dl / total_length)
                                    if not update_progress(done):
                                        break
                    
                    # Cargar la lista descargada
                    if not progress.wasCanceled():
                        self.load_playlist(temp_path)
                        
                        # Mostrar mensaje de éxito
                        QMessageBox.information(
                            self,
                            "Descarga Completada",
                            f"Lista descargada y cargada correctamente desde:\n{url}"
                        )
                
                except Exception as e:
                    QMessageBox.critical(
                        self,
                        "Error de Descarga",
                        f"No se pudo descargar la lista:\n{str(e)}"
                    )
                
                finally:
                    progress.close()
                    
            except Exception as e:
                QMessageBox.critical(
                    self,
                    "Error",
                    f"Error al descargar la lista:\n{str(e)}"
                )
    
    def check_playing_status(self):
        """Verifica si se está reproduciendo video y muestra/oculta el botón de menú"""
        try:
            if self.player and self.player.is_playing():
                # Mostrar el botón de menú solo si no está ya visible
                if not self.menu_button.isVisible():
                    # Posicionar el botón en la esquina superior izquierda del video_frame
                    button_x = 10
                    button_y = 10
                    global_pos = self.video_frame.mapToGlobal(QPoint(button_x, button_y))
                    local_pos = self.mapFromGlobal(global_pos)
                    self.menu_button.move(local_pos)
                    self.menu_button.raise_()
                    self.menu_button.show()
            else:
                # Ocultar el botón si no se está reproduciendo
                self.menu_button.hide()
        except Exception as e:
            print(f"Error al verificar estado de reproducción: {str(e)}")
    
    def show_context_menu(self):
        """Muestra el menú contextual"""
        # Crear menú contextual
        context_menu = QMenu(self)
        context_menu.setStyleSheet(ModernStyle.MENU_STYLE)
        
        # Agregar acciones al menú
        toggle_fullscreen_action = QAction("Pantalla Completa", self)
        toggle_fullscreen_action.triggered.connect(self.toggle_fullscreen)
        context_menu.addAction(toggle_fullscreen_action)
        
        # Agregar opciones de escala
        scale_menu = QMenu("Escala", context_menu)
        scale_menu.setStyleSheet(ModernStyle.MENU_STYLE)
        
        scales = [("Ajustar a ventana", "fit"), ("Original", "original"), 
                  ("0.5x", 0.5), ("1.0x", 1.0), ("1.5x", 1.5), ("2.0x", 2.0)]
        
        for name, scale in scales:
            action = QAction(name, self)
            action.triggered.connect(lambda checked, s=scale: self.set_scale(s))
            scale_menu.addAction(action)
            
        context_menu.addMenu(scale_menu)
        
        # Agregar opciones de relación de aspecto
        aspect_menu = QMenu("Relación de aspecto", context_menu)
        aspect_menu.setStyleSheet(ModernStyle.MENU_STYLE)
        
        aspects = [("Auto", None), ("16:9", "16:9"), ("4:3", "4:3"), 
                   ("1:1", "1:1"), ("16:10", "16:10"), ("2.35:1", "2.35:1")]
        
        for name, ratio in aspects:
            action = QAction(name, self)
            action.triggered.connect(lambda checked, r=ratio: self.set_aspect_ratio(r))
            aspect_menu.addAction(action)
            
        context_menu.addMenu(aspect_menu)
        
        # Agregar opciones de pistas de audio si hay disponibles
        if self.player and self.player.audio_get_track_count() > 1:
            audio_menu = QMenu("Pista de audio", context_menu)
            audio_menu.setStyleSheet(ModernStyle.MENU_STYLE)
            
            current_track = self.player.audio_get_track()
            
            for track_id in range(self.player.audio_get_track_count()):
                track_name = f"Pista {track_id}"
                action = QAction(track_name, self)
                action.setCheckable(True)
                action.setChecked(track_id == current_track)
                action.triggered.connect(lambda checked, t=track_id: self.player.audio_set_track(t))
                audio_menu.addAction(action)
                
            context_menu.addMenu(audio_menu)
        
        # Mostrar el menú contextual justo debajo del botón
        button_pos = self.menu_button.mapToGlobal(self.menu_button.rect().bottomLeft())
        context_menu.exec(button_pos)
    
    def set_scale(self, scale):
        """Establece la escala del video"""
        if not self.player:
            return
            
        if scale == "fit":
            # Ajustar a ventana
            self.player.video_set_scale(0)
        elif scale == "original":
            # Tamaño original
            self.player.video_set_scale(1)
        else:
            # Escala numérica
            try:
                self.player.video_set_scale(float(scale))
            except Exception as e:
                print(f"Error al establecer escala: {str(e)}")
    
    def set_aspect_ratio(self, ratio):
        """Establece la relación de aspecto del video"""
        if not self.player:
            return
            
        try:
            self.player.video_set_aspect_ratio(ratio if ratio else "")
        except Exception as e:
            print(f"Error al establecer relación de aspecto: {str(e)}")
    
    def save_working_channels(self):
        """Guarda solo los canales que funcionan (online o lentos) en un archivo M3U"""
        if not self.playlist_manager.channels:
            QMessageBox.warning(self, "Sin canales", "No hay canales para guardar.")
            return
            
        # Contar canales funcionales
        working_channels = [ch for ch in self.playlist_manager.channels if ch.status in ['online', 'slow']]
        
        if not working_channels:
            QMessageBox.warning(self, "Sin canales funcionales", "No hay canales funcionales para guardar.")
            return
            
        # Mostrar diálogo para seleccionar archivo
        file_name, _ = QFileDialog.getSaveFileName(
            self,
            "Guardar Canales Funcionales",
            os.path.join(os.path.dirname(os.path.abspath(__file__)), "canales_funcionales.m3u"),
            "Listas M3U (*.m3u *.m3u8);;Todos los archivos (*.*)"
        )
        
        if file_name:
            try:
                # Guardar solo los canales funcionales
                self.playlist_manager.save_m3u_playlist(file_name, working_channels)
                
                # Mostrar mensaje de éxito
                QMessageBox.information(
                    self,
                    "Canales guardados",
                    f"Se han guardado {len(working_channels)} canales funcionales en:\n{file_name}"
                )
                
                # Actualizar etiqueta de estado
                self.status_label.setText(f"Guardados: {len(working_channels)} canales funcionales")
                
            except Exception as e:
                # Mostrar mensaje de error
                QMessageBox.critical(
                    self,
                    "Error al guardar",
                    f"No se pudieron guardar los canales funcionales:\n{str(e)}"
                )

    def save_unified_channels(self):
        """Guarda la lista de canales unificados en un archivo M3U"""
        if not self.playlist_manager.channels:
            QMessageBox.warning(self, "Sin canales", "No hay canales para guardar.")
            return
            
        # Mostrar diálogo para seleccionar archivo
        file_name, _ = QFileDialog.getSaveFileName(
            self,
            "Guardar Canales Unificados",
            os.path.join(os.path.dirname(os.path.abspath(__file__)), "canales_unificados.m3u"),
            "Listas M3U (*.m3u *.m3u8);;Todos los archivos (*.*)"
        )
        
        if file_name:
            try:
                # Guardar todos los canales
                self.playlist_manager.save_m3u_playlist(file_name, self.playlist_manager.channels)
                
                # Mostrar mensaje de éxito
                QMessageBox.information(
                    self,
                    "Canales guardados",
                    f"Se han guardado {len(self.playlist_manager.channels)} canales unificados en:\n{file_name}"
                )
                
                # Actualizar etiqueta de estado
                self.status_label.setText(f"Guardados: {len(self.playlist_manager.channels)} canales unificados")
                
            except Exception as e:
                # Mostrar mensaje de error
                QMessageBox.critical(
                    self,
                    "Error al guardar",
                    f"No se pudieron guardar los canales unificados:\n{str(e)}"
                )

    def unify_channels(self):
        """Elimina canales duplicados y unifica nombres similares"""
        if not self.playlist_manager.channels:
            QMessageBox.warning(self, "Sin canales", "No hay canales para unificar.")
            return
            
        # Mostrar diálogo de confirmación
        result = QMessageBox.question(
            self,
            "Unificar Canales",
            "Esta acción eliminará canales duplicados y unificará nombres similares.\n¿Desea continuar?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if result == QMessageBox.StandardButton.Yes:
            try:
                # Mostrar diálogo de progreso
                progress = QProgressDialog("Unificando canales...", "Cancelar", 0, 100, self)
                progress.setWindowTitle("Unificación de canales")
                progress.setWindowModality(Qt.WindowModality.WindowModal)
                progress.setMinimumDuration(0)
                progress.setMinimumSize(400, 150)
                
                # Establecer una fuente más grande y visible
                font = QFont()
                font.setPointSize(10)
                font.setBold(True)
                progress.setFont(font)
                
                # Estilo con colores de alto contraste
                progress.setStyleSheet("""
                    QProgressDialog {
                        background-color: #1E1E1E;
                        color: white;
                        border: 1px solid #FF8000;
                        padding: 10px;
                    }
                    QProgressBar {
                        border: 1px solid #FF8000;
                        border-radius: 4px;
                        background-color: #121212;
                        color: white;
                        text-align: center;
                        min-height: 20px;
                    }
                    QProgressBar::chunk {
                        background-color: #FF8000;
                        width: 10px;
                    }
                    QPushButton {
                        background-color: #2D2D2D;
                        color: white;
                        border: 1px solid #FF8000;
                        border-radius: 4px;
                        padding: 5px 10px;
                        min-width: 80px;
                    }
                    QPushButton:hover {
                        background-color: #FF8000;
                        color: black;
                    }
                    QLabel {
                        color: white;
                        font-weight: bold;
                    }
                """)
                
                # Función para actualizar el progreso
                def update_progress(percent, message):
                    if progress.wasCanceled():
                        return False
                    progress.setValue(int(percent))
                    progress.setLabelText(f"Unificando canales...\n\n{message}")
                    QApplication.processEvents()
                    return True
                
                # Obtener número de canales antes de unificar
                channels_before = len(self.playlist_manager.channels)
                
                # Unificar canales
                try:
                    # Llamar al método de unificación en PlaylistManager
                    result = self.playlist_manager.remove_duplicate_channels(update_progress)
                    
                    # Obtener número de canales después de unificar
                    channels_after = len(self.playlist_manager.channels)
                    duplicates_removed = channels_before - channels_after
                    
                    # Actualizar la interfaz
                    self.group_filter.clear()
                    self.group_filter.addItem("Todos los grupos")
                    self.group_filter.addItems(sorted(self.playlist_manager.groups))
                    self.update_channel_list("Todos los grupos")
                    
                    # Mostrar mensaje de éxito con detalles
                    unified_groups = result.get("unified_groups", {})
                    total_unified = sum(len(group_info["names"]) - 1 for group_info in unified_groups.values())
                    
                    # Crear mensaje detallado
                    message = f"Se han eliminado {duplicates_removed} canales duplicados.\n"
                    message += f"Se han unificado {total_unified} nombres similares.\n\n"
                    
                    # Añadir detalles de grupos unificados (limitado a 10 para no hacer el mensaje muy largo)
                    if unified_groups:
                        message += "Grupos unificados más relevantes:\n"
                        for i, (group_name, group_info) in enumerate(sorted(unified_groups.items(), 
                                                                          key=lambda x: len(x[1]["names"]), 
                                                                          reverse=True)):
                            if i >= 10:  # Limitar a 10 grupos para no hacer el mensaje muy largo
                                message += f"... y {len(unified_groups) - 10} grupos más."
                                break
                            message += f"- Grupo '{group_name}': {len(group_info['names'])} canales unificados como '{group_info['chosen_name']}'\n"
                    
                    # Mostrar mensaje de éxito
                    QMessageBox.information(
                        self,
                        "Unificación completada",
                        message
                    )
                    
                    # Actualizar etiqueta de estado
                    self.status_label.setText(f"Canales unificados: {channels_after} (eliminados {duplicates_removed})")
                    
                except Exception as e:
                    # Capturar y mostrar errores de unificación
                    error_msg = str(e)
                    try:
                        # Intentar codificar el mensaje de error para evitar problemas con caracteres especiales
                        error_msg = error_msg.encode('utf-8', 'replace').decode('utf-8')
                    except:
                        error_msg = "Error desconocido durante la unificación"
                    
                    QMessageBox.critical(
                        self,
                        "Error en unificación",
                        f"Error durante la unificación de canales:\n{error_msg}"
                    )
            
            except Exception as e:
                # Capturar y mostrar errores generales
                QMessageBox.critical(
                    self,
                    "Error",
                    f"Error durante la unificación de canales:\n{str(e)}"
                )
            finally:
                # Cerrar el diálogo de progreso
                if 'progress' in locals():
                    progress.close()

    def mouseMoveEvent(self, event):
        """Maneja el evento de movimiento del ratón"""
        super().mouseMoveEvent(event)
        
        # Solo procesar en modo pantalla completa
        if not self.isFullScreen():
            return
            
        # Obtener la posición del ratón
        pos = event.position() if hasattr(event, 'position') else event.pos()
        
        # Verificar si el ratón está cerca del borde izquierdo o derecho
        if pos.x() < 20:
            # Si está cerca del borde izquierdo, mostrar la barra lateral
            self.show_sidebar()
            # Reiniciar el temporizador
            self.sidebar_timer.start(3000)
        elif pos.x() > self.width() - 20:
            # Si está cerca del borde derecho, también mostrar la barra lateral
            self.show_sidebar()
            # Reiniciar el temporizador
            self.sidebar_timer.start(3000)
        elif self.left_panel_visible:
            # Si la barra lateral está visible y el ratón no está en los bordes,
            # reiniciar el temporizador para ocultarla después de 3 segundos
            self.sidebar_timer.start(3000)
    
    def leaveEvent(self, event):
        """Se llama cuando el cursor sale de la ventana"""
        super().leaveEvent(event)
        
        # Si estamos en pantalla completa y el cursor sale de la ventana,
        # mostrar la barra lateral
        if self.isFullScreen():
            self.show_sidebar()
            # Reiniciar el temporizador
            self.sidebar_timer.start(3000)
    
if __name__ == "__main__":
    app = QApplication(sys.argv)
    
    # Establecer el icono de la aplicación
    try:
        # Intentar cargar el icono desde el directorio actual o desde el ejecutable
        icon_path = "icono.ico"
        
        # Si estamos en un ejecutable creado con PyInstaller, ajustar la ruta
        if getattr(sys, 'frozen', False):
            # Estamos en un ejecutable
            base_dir = os.path.dirname(sys.executable)
            icon_path = os.path.join(base_dir, "icono.ico")
            
            # Si no se encuentra en el directorio del ejecutable, buscar en el directorio temporal de PyInstaller
            if not os.path.exists(icon_path):
                base_dir = sys._MEIPASS if hasattr(sys, '_MEIPASS') else os.path.abspath(".")
                icon_path = os.path.join(base_dir, "icono.ico")
        
        app_icon = QIcon(icon_path)
        app.setWindowIcon(app_icon)
        print(f"Icono cargado desde: {icon_path}")
    except Exception as e:
        print(f"Error al cargar el icono: {str(e)}")
    
    player = TVIPPlayer()
    
    # Establecer el icono en la ventana principal
    try:
        if 'app_icon' in locals():
            player.setWindowIcon(app_icon)
    except Exception as e:
        print(f"Error al establecer el icono en la ventana: {str(e)}")
    
    player.show()
    sys.exit(app.exec())