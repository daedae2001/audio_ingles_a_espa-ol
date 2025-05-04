#!/usr/bin/env python3
"""
TV-IP Player - Reproductor de canales IPTV con estilo moderno
Versión mejorada estéticamente usando PyQt6
Optimizado para Windows
"""

import sys
import os
import traceback
import platform
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout,
                             QHBoxLayout, QListWidget, QLabel, QPushButton,
                             QComboBox, QFileDialog, QListWidgetItem, QSizePolicy,
                             QProgressDialog, QInputDialog, QMessageBox, QMenu, QGridLayout)
from PyQt6.QtCore import Qt, QEvent, QTimer, QPoint
from PyQt6.QtGui import QKeyEvent, QColor, QCursor, QAction, QIcon, QPalette, QFont
from PyQt6.QtWinExtras import QWinTaskbarButton, QWinTaskbarProgress
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
        
        # Verificar sistema operativo
        self.is_windows = platform.system() == "Windows"
        
        # Inicializar VLC con configuración específica para Windows
        if self.is_windows:
            # En Windows, es recomendable especificar la ruta a los plugins de VLC
            vlc_plugin_path = None
            for path in [
                os.path.join(os.path.dirname(sys.executable), 'vlc-plugins'),
                r'C:\Program Files\VideoLAN\VLC\plugins',
                r'C:\Program Files (x86)\VideoLAN\VLC\plugins'
            ]:
                if os.path.exists(path):
                    vlc_plugin_path = path
                    break
            
            if vlc_plugin_path:
                self.instance = vlc.Instance(f'--plugin-path={vlc_plugin_path}')
            else:
                self.instance = vlc.Instance()
        else:
            self.instance = vlc.Instance()
        
        self.player = self.instance.media_player_new()
        
        # Configuración para la barra de tareas de Windows
        self.taskbar_button = None
        self.taskbar_progress = None
        if self.is_windows:
            self.setup_windows_taskbar()
        
        # Configuración de la interfaz
        self.setup_ui()
        self.apply_modern_style()
        
        # Cargar la última lista de reproducción si existe
        self.playlist_manager = PlaylistManager()
        if self.playlist_manager.channels:
            self.update_groups_combo()
            self.status_label.setText(f"Lista cargada: {len(self.playlist_manager.channels)} canales")
        
        # Timer para verificar la posición del ratón en pantalla completa
        self.mouse_check_timer = QTimer(self)
        self.mouse_check_timer.timeout.connect(self.check_mouse_position)
        self.mouse_check_timer.start(200)
        
        # Timer para actualizar la posición del botón de menú
        self.button_visibility_timer = QTimer(self)
        self.button_visibility_timer.timeout.connect(self.update_menu_button_position)
        self.button_visibility_timer.start(500)
        
        # Variables de estado
        self.is_fullscreen = False
        self.current_aspect_ratio = None
        self.current_scale_mode = None
        
    def setup_windows_taskbar(self):
        """Configura la integración con la barra de tareas de Windows"""
        if not self.is_windows:
            return
            
        try:
            self.taskbar_button = QWinTaskbarButton(self)
            self.taskbar_button.setWindow(self.windowHandle())
            
            self.taskbar_progress = self.taskbar_button.progress()
            self.taskbar_progress.setVisible(True)
            self.taskbar_progress.setValue(0)
            self.taskbar_progress.setRange(0, 100)
            self.taskbar_progress.stop()
        except Exception as e:
            print(f"Error al configurar la barra de tareas de Windows: {e}")

    def load_playlist(self):
        try:
            options = QFileDialog.Options()
            file_path, _ = QFileDialog.getOpenFileName(
                self, "Cargar Lista de Reproducción", "",
                "Listas de Reproducción (*.m3u *.m3u8);;Todos los archivos (*)", options=options
            )
            
            if not file_path:
                return
                
            # Normalizar ruta para Windows
            if self.is_windows:
                file_path = os.path.normpath(file_path)
                
            # Crear un diálogo de progreso
            progress = QProgressDialog("Cargando lista de reproducción...", "Cancelar", 0, 100, self)
            progress.setWindowTitle("Cargando")
            progress.setWindowModality(Qt.WindowModality.WindowModal)
            progress.setMinimumDuration(0)
            progress.setValue(0)
            
            # Función de callback para actualizar el progreso
            def update_progress(percent, channels_count):
                progress.setValue(percent)
                progress.setLabelText(f"Cargando lista... {channels_count} canales encontrados")
                QApplication.processEvents()
                return not progress.wasCanceled()
                
            # Actualizar la barra de tareas de Windows si está disponible
            if self.is_windows and self.taskbar_progress:
                self.taskbar_progress.resume()
                self.taskbar_progress.setValue(0)
            
            # Cargar la lista
            self.playlist_manager.load_playlist(file_path, update_progress)
            
            # Detener la barra de progreso de la barra de tareas
            if self.is_windows and self.taskbar_progress:
                self.taskbar_progress.setValue(100)
                self.taskbar_progress.stop()
            
            # Actualizar la interfaz
            self.update_groups_combo()
            
            # Mostrar información
            channels_count = len(self.playlist_manager.channels)
            groups_count = len(self.playlist_manager.groups)
            self.status_label.setText(f"Lista cargada: {channels_count} canales en {groups_count} grupos")
            
            # Guardar para la próxima vez
            self.playlist_manager.save_last_playlist()
            
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error al cargar la lista: {str(e)}")
            traceback.print_exc()

    def download_playlist(self):
        try:
            url, ok = QInputDialog.getText(
                self, "Descargar Lista", "Introduce la URL de la lista M3U:",
                QInputDialog.InputDialogOptions.Normal, ""
            )
            
            if not ok or not url:
                return
                
            # Crear un diálogo de progreso
            progress = QProgressDialog("Descargando lista de reproducción...", "Cancelar", 0, 100, self)
            progress.setWindowTitle("Descargando")
            progress.setWindowModality(Qt.WindowModality.WindowModal)
            progress.setMinimumDuration(0)
            progress.setValue(10)
            QApplication.processEvents()
            
            # Actualizar la barra de tareas de Windows si está disponible
            if self.is_windows and self.taskbar_progress:
                self.taskbar_progress.resume()
                self.taskbar_progress.setValue(10)
            
            # Descargar la lista
            success, message, file_path = self.playlist_manager.download_playlist_from_url(url)
            
            # Actualizar progreso
            progress.setValue(50)
            QApplication.processEvents()
            
            if self.is_windows and self.taskbar_progress:
                self.taskbar_progress.setValue(50)
            
            if not success:
                progress.close()
                if self.is_windows and self.taskbar_progress:
                    self.taskbar_progress.stop()
                QMessageBox.critical(self, "Error", f"Error al descargar: {message}")
                return
                
            # Normalizar ruta para Windows
            if self.is_windows:
                file_path = os.path.normpath(file_path)
                
            # Función de callback para actualizar el progreso
            def update_progress(percent, channels_count):
                progress.setValue(50 + percent // 2)  # 50% a 100%
                progress.setLabelText(f"Procesando lista... {channels_count} canales encontrados")
                if self.is_windows and self.taskbar_progress:
                    self.taskbar_progress.setValue(50 + percent // 2)
                QApplication.processEvents()
                return not progress.wasCanceled()
                
            # Cargar la lista descargada
            self.playlist_manager.load_playlist(file_path, update_progress)
            
            # Detener la barra de progreso de la barra de tareas
            if self.is_windows and self.taskbar_progress:
                self.taskbar_progress.setValue(100)
                self.taskbar_progress.stop()
            
            # Actualizar la interfaz
            self.update_groups_combo()
            
            # Mostrar información
            channels_count = len(self.playlist_manager.channels)
            groups_count = len(self.playlist_manager.groups)
            self.status_label.setText(f"Lista descargada: {channels_count} canales en {groups_count} grupos")
            
            # Guardar para la próxima vez
            self.playlist_manager.save_last_playlist()
            
        except Exception as e:
            if self.is_windows and self.taskbar_progress:
                self.taskbar_progress.stop()
            QMessageBox.critical(self, "Error", f"Error al descargar la lista: {str(e)}")
            traceback.print_exc()

    def keyPressEvent(self, event):
        # Asegura que los atajos funcionen incluso si el foco está en el botón flotante
        if event.key() == Qt.Key.Key_F11 or \
           (event.key() == Qt.Key.Key_Return and event.modifiers() == Qt.KeyboardModifier.AltModifier):
            self.toggle_fullscreen()
        elif event.key() == Qt.Key.Key_Escape and self.isFullScreen():
            print("ESC detectado, intentando salir de pantalla completa")
            self.toggle_fullscreen()
        # Atajos específicos para Windows
        elif self.is_windows and event.key() == Qt.Key.Key_F and event.modifiers() == Qt.KeyboardModifier.AltModifier:
            # Alt+F para abrir el menú de archivo (común en Windows)
            self.show_fixed_menu()
        elif self.is_windows and event.key() == Qt.Key.Key_M and event.modifiers() == Qt.KeyboardModifier.ControlModifier:
            # Ctrl+M para mostrar/ocultar el menú contextual
            if hasattr(self, 'button_container') and self.button_container.isVisible():
                self.button_container.hide()
            elif hasattr(self, 'button_container'):
                self.update_menu_button_position()
        else:
            super().keyPressEvent(event)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    
    # Configuración específica para Windows
    if platform.system() == "Windows":
        # Establecer el ID de la aplicación para la barra de tareas
        import ctypes
        app_id = 'daedae2001.tvipplayer.modern.1.0'
        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(app_id)
        
        # Establecer el icono de la aplicación
        app_icon_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'icon.ico')
        if os.path.exists(app_icon_path):
            from PyQt6.QtGui import QIcon
            app.setWindowIcon(QIcon(app_icon_path))
    
    player = ModernTVIPPlayer()
    player.show()
    sys.exit(app.exec())
