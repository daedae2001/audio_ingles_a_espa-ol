import sys
from PyQt6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
                            QSizePolicy, QLabel, QApplication, QPushButton)
from PyQt6.QtCore import Qt, QEvent, QTimer, QPoint
from PyQt6.QtGui import QCursor, QFont

from src.ui.sidebar import Sidebar
from src.ui.video_widget import VideoWidget
from src.core.media_player import MediaPlayer
from src.core.playlist_manager import PlaylistManager, Channel

class MainWindow(QMainWindow):
    """
    Ventana principal de la aplicación que integra todos los componentes de la UI.
    Esta clase es responsable de la disposición general de la interfaz y de la
    coordinación entre los diferentes componentes.
    """
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle('TV IP Player')
        self.setGeometry(100, 100, 1200, 700)
        self.setMinimumSize(900, 600)
        self.installEventFilter(self)
        
        # Variables para control de panel lateral
        self.sidebar_visible = True
        self.is_fullscreen_mode = False
        self.sidebar_hover_margin = 20
        self.sidebar_position = "right"  # Posición del sidebar (right o left)
        self.cursor_crossed_right_edge = False  # Nueva variable para detectar cruce
        
        # Temporizador para ocultar el sidebar después de un tiempo sin usarse
        self.sidebar_hide_timer = QTimer(self)
        self.sidebar_hide_timer.setSingleShot(True)  # Una sola ejecución
        self.sidebar_hide_timer.timeout.connect(self.hide_sidebar_timeout)
        self.sidebar_hide_delay = 5000  # 5 segundos
        
        # Inicializar componentes principales
        self.media_player = MediaPlayer()
        self.playlist_manager = PlaylistManager()
        
        # Configurar temporizador para verificar posición del ratón
        self.mouse_check_timer = QTimer(self)
        self.mouse_check_timer.timeout.connect(self.check_mouse_position)
        self.mouse_check_timer.start(100)
        
        # Configurar la interfaz de usuario
        self.setup_ui()
        
        # Cargar la última lista de reproducción si existe
        self.sidebar.load_last_playlist()
    
    def setup_ui(self):
        """Configura la interfaz de usuario principal"""
        # Widget principal
        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        layout = QHBoxLayout(main_widget)
        layout.setContentsMargins(0, 0, 0, 0)  # Eliminar márgenes para maximizar espacio
        
        # Crear el panel de video
        self.video_widget = VideoWidget(self.media_player, self)
        
        # Crear el panel lateral
        self.sidebar = Sidebar(self.playlist_manager, self.media_player, self)
        
        # Botón flotante de menú contextual en la esquina izquierda
        self.menu_button = QPushButton("≡", self)
        self.menu_button.setFont(QFont("Arial", 18, QFont.Weight.Bold))
        self.menu_button.setStyleSheet("""
            QPushButton {
                background-color: rgba(0, 0, 0, 0);
                color: #FF8000;
                border: 1px solid #FF8000;
                border-radius: 12px;
                padding: 0px;
                min-width: 28px;
                min-height: 28px;
            }
            QPushButton:hover {
                background-color: rgba(255, 128, 0, 0.2);
            }
        """)
        self.menu_button.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.menu_button.setFixedSize(28, 28)
        self.menu_button.setToolTip('Menú de video')
        self.menu_button.clicked.connect(self.show_video_menu)
        
        # Añadir componentes al layout principal
        layout.addWidget(self.video_widget)
        
        # Añadir el sidebar según su posición configurada
        if self.sidebar_position == "right":
            layout.addWidget(self.sidebar)
        else:
            # Insertar al principio si debe estar a la izquierda
            layout.insertWidget(0, self.sidebar)
        
        # Mostrar el botón y asegurar que sea visible
        self.menu_button.show()
        self.menu_button.raise_()
        
        # Actualizar la posición inicial del botón
        QTimer.singleShot(100, self.update_menu_button_position)
        
        # Instalar event filter global para clic derecho sobre video 
        QApplication.instance().installEventFilter(self)
        
    def update_menu_button_position(self):
        """Actualiza la posición del botón de menú a la esquina superior izquierda del video"""
        if not hasattr(self, 'menu_button') or not hasattr(self, 'video_widget'):
            return
            
        # Obtener la geometría del widget de video relativa a la ventana principal
        video_rect = self.video_widget.geometry()
        video_top_left = self.video_widget.mapTo(self, video_rect.topLeft())
        
        # Colocar el botón en la esquina superior izquierda con un pequeño margen
        margin = 4
        self.menu_button.move(video_top_left.x() + margin, video_top_left.y() + margin)
        self.menu_button.raise_()
    
    def show_video_menu(self):
        """Muestra el menú contextual del video"""
        if hasattr(self, 'video_widget'):
            # Calcular la posición exacta del punto inferior izquierdo del botón
            button = self.menu_button
            menu_x = button.x()  # Posición X del botón dentro de su padre
            menu_y = button.y() + button.height()  # Posición Y + altura (punto inferior)
            
            # Convertir a coordenadas globales a través del widget padre
            local_point = QPoint(menu_x, menu_y)
            global_point = button.parentWidget().mapToGlobal(local_point)
            
            # Mostrar el menú contextual exactamente donde termina el botón
            self.video_widget.show_context_menu(global_point)
    
    def toggle_fullscreen(self):
        """Alterna entre modo pantalla completa y ventana normal"""
        print(f"toggle_fullscreen llamado. is_fullscreen_mode={self.is_fullscreen_mode}, isFullScreen()={self.isFullScreen()}")
        
        if not self.isFullScreen():
            # Guardamos la geometría actual antes de ir a pantalla completa
            self.normal_geometry = self.geometry()
            
            # Ocultar completamente el sidebar
            if hasattr(self, 'sidebar'):
                self.sidebar.hide()
                self.sidebar_visible = False
            
            # Cambiar a pantalla completa
            self.showFullScreen()
            self.is_fullscreen_mode = True
            print("Entrando a pantalla completa")
            
            # Dar foco al widget de video para capturar eventos de teclado
            if hasattr(self, 'video_widget'):
                self.video_widget.setFocus()
        else:
            # Restaurar a ventana normal
            self.showNormal()
            if hasattr(self, 'normal_geometry'):
                self.setGeometry(self.normal_geometry)
            self.is_fullscreen_mode = False
            print("Saliendo de pantalla completa")
            
            # Mostrar el sidebar al salir de pantalla completa
            if hasattr(self, 'sidebar'):
                self.sidebar.show()
                self.sidebar_visible = True
    
    def check_mouse_position(self):
        """Verifica la posición del ratón para mostrar/ocultar el panel lateral en modo pantalla completa"""
        if not self.is_fullscreen_mode:
            return
            
        cursor_pos = QCursor.pos()
        window_pos = self.mapToGlobal(QPoint(0, 0))
        window_width = self.width()
        relative_x = cursor_pos.x() - window_pos.x()
        
        # Verificar si el cursor está dentro de los límites de la ventana
        is_cursor_in_window = (0 <= relative_x <= window_width) and (0 <= cursor_pos.y() - window_pos.y() <= self.height())
        
        # Verificar si el cursor está cerca del borde derecho
        cursor_at_right_edge = relative_x >= (window_width - self.sidebar_hover_margin) and is_cursor_in_window
        
        # Detectar cuando el cursor cruza el borde derecho
        if cursor_at_right_edge and not self.cursor_crossed_right_edge:
            # El cursor acaba de cruzar el borde derecho, mostrar el panel
            self.sidebar.show()
            self.sidebar_visible = True
            self.sidebar_position = "right"
            self.cursor_crossed_right_edge = True
            
            # Iniciar el temporizador para ocultar automáticamente
            self.sidebar_hide_timer.start(self.sidebar_hide_delay)
        
        # Restablecer el estado de cruce cuando el cursor ya no está en el borde
        elif not cursor_at_right_edge:
            self.cursor_crossed_right_edge = False
        
        # Reiniciar el temporizador si el usuario interactúa con el sidebar
        if self.sidebar_visible and is_cursor_in_window:
            sidebar_rect = self.sidebar.geometry()
            if sidebar_rect.contains(self.mapFromGlobal(cursor_pos)):
                # Reiniciar el temporizador cuando el cursor está sobre el sidebar
                self.sidebar_hide_timer.start(self.sidebar_hide_delay)
    
    def hide_sidebar_timeout(self):
        """Oculta el sidebar después de que expire el temporizador"""
        if self.is_fullscreen_mode and self.sidebar_visible:
            print("Auto-ocultando sidebar después de 5 segundos de inactividad")
            self.sidebar.hide()
            self.sidebar_visible = False
    
    def eventFilter(self, obj, event):
        """Filtro de eventos para manejar teclas y otros eventos globales"""
        try:
            # Reiniciar el temporizador si hay actividad del mouse en pantalla completa
            if self.is_fullscreen_mode and self.sidebar_visible:
                if event.type() in [QEvent.Type.MouseMove, QEvent.Type.MouseButtonPress]:
                    # Reiniciar el temporizador de ocultación
                    self.sidebar_hide_timer.start(self.sidebar_hide_delay)
            
            # Manejar eventos de teclado
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
    
    def keyPressEvent(self, event):
        """Maneja eventos de teclado específicos"""
        print(f"keyPressEvent: key={event.key()} esc={Qt.Key.Key_Escape} fullscreen={self.isFullScreen()} is_fullscreen_mode={self.is_fullscreen_mode}")
        # Asegura que los atajos funcionen incluso si el foco está en otro widget
        if event.key() == Qt.Key.Key_F11 or \
           (event.key() == Qt.Key.Key_Return and event.modifiers() == Qt.KeyboardModifier.AltModifier):
            self.toggle_fullscreen()
        elif event.key() == Qt.Key.Key_Escape and self.isFullScreen():
            print("ESC detectado, intentando salir de pantalla completa")
            self.toggle_fullscreen()
        else:
            super().keyPressEvent(event)
    
    def resizeEvent(self, event):
        """Maneja eventos de redimensionamiento de la ventana"""
        super().resizeEvent(event)
        # Actualizar la posición del botón de menú
        self.update_menu_button_position()
        
    def _check_fullscreen_after_play(self):
        """Verifica y corrige el estado de pantalla completa después de iniciar la reproducción"""
        if self.isFullScreen():
            print("Detectado cambio a pantalla completa después de reproducir, forzando salida")
            self.showNormal()
            if hasattr(self, 'normal_geometry'):
                self.setGeometry(self.normal_geometry)
            self.is_fullscreen_mode = False
            print("Forzado a modo ventana completado")
