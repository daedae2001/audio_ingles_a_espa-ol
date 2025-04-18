from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QMenu, QSizePolicy)
from PyQt6.QtCore import Qt, QEvent
from PyQt6.QtGui import QAction

import sys
import os
from src.core.media_player import MediaPlayer

class VideoWidget(QWidget):
    """
    Widget que muestra el contenido de video y proporciona controles
    contextuales para manipular la reproducción.
    """
    
    def __init__(self, media_player, parent=None):
        super().__init__(parent)
        self.media_player = media_player
        self.parent_window = parent
        
        # Configuración básica del widget
        self.setStyleSheet("background-color: black;")
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.setMouseTracking(True)
        
        # Layout principal (sin márgenes para maximizar espacio)
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.main_layout.setSpacing(0)
        self.setLayout(self.main_layout)
        
        # Configurar el reproductor para usar este widget
        self.media_player.set_window_handle(self.winId())
        
        # Establecer la política de menú contextual
        self.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.customContextMenuRequested.connect(self.show_context_menu)
        
        # Instalar filtro de eventos para eventos adicionales
        self.installEventFilter(self)
    
    def eventFilter(self, obj, event):
        """Filtro de eventos para el widget"""
        return super().eventFilter(obj, event)
        
    def show_context_menu(self, position):
        """Muestra el menú contextual con todas las opciones"""
        print("MENÚ CONTEXTUAL INVOCADO", position)
        
        # Definir el estilo que se aplicará a todos los menús
        menu_style = """
            QMenu {
                background-color: #404040;
                color: white;
                border: 1px solid #555555;
                padding: 5px;
            }
            QMenu::item {
                background-color: transparent;
                color: white;
                padding: 6px 20px;
            }
            QMenu::item:selected {
                background-color: #606060;
            }
            QMenu::item:checked {
                background-color: #505050;
                font-weight: bold;
            }
            QMenu::separator {
                height: 1px;
                background-color: #555555;
                margin: 5px 2px;
            }
        """
        
        # Crear el menú contextual
        context_menu = QMenu(self.parent_window or self)
        context_menu.setStyleSheet(menu_style)
        
        # Pantalla completa
        is_fullscreen = self.parent_window and self.parent_window.isFullScreen()
        fullscreen_text = 'Salir de Pantalla Completa' if is_fullscreen else 'Pantalla Completa'
        fullscreen_action = QAction(fullscreen_text, self)
        fullscreen_action.triggered.connect(self.toggle_fullscreen)
        context_menu.addAction(fullscreen_action)
        
        # Opciones de escala de video
        scale_menu = QMenu('Escala de Video', self)
        scale_menu.setStyleSheet(menu_style)  # Aplicar el mismo estilo al submenú
        scales = {
            'Ajuste Original (1.0x)': 1.0,
            'Ajuste a Ventana (0.5x)': 0.5,
            'Ajuste Doble (2.0x)': 2.0
        }
        for name, scale in scales.items():
            action = QAction(name, self)
            action.setCheckable(True)
            action.setChecked(self.media_player.current_scale == scale)
            # Usar una función interior para evitar problemas de captura en lambdas
            def create_scale_handler(s):
                return lambda: self.media_player.set_scale_mode(s)
            action.triggered.connect(create_scale_handler(scale))
            scale_menu.addAction(action)
        context_menu.addMenu(scale_menu)
        
        # Opciones de relación de aspecto
        aspect_menu = QMenu('Relación de Aspecto', self)
        aspect_menu.setStyleSheet(menu_style)  # Aplicar el mismo estilo al submenú
        aspect_ratios = {
            'Auto': '',
            '16:9': '16:9',
            '4:3': '4:3',
            '1:1': '1:1',
            '16:10': '16:10',
            '2.35:1 (Cinemascope)': '2.35:1',
            '2.21:1 (Panavision)': '221:100',
            '1.85:1 (Cine)': '185:100'
        }
        for name, ratio in aspect_ratios.items():
            action = QAction(name, self)
            action.setCheckable(True)
            action.setChecked(self.media_player.current_aspect_ratio == ratio)
            # Usar una función interior para evitar problemas de captura en lambdas
            def create_ratio_handler(r):
                return lambda: self.media_player.set_aspect_ratio(r)
            action.triggered.connect(create_ratio_handler(ratio))
            aspect_menu.addAction(action)
        context_menu.addMenu(aspect_menu)
        
        # Opciones de pistas de audio
        if self.media_player.is_playing():
            audio_tracks = self.media_player.get_audio_tracks()
            if audio_tracks and len(audio_tracks) > 1:
                audio_menu = QMenu('Pistas de Audio', self)
                audio_menu.setStyleSheet(menu_style)  # Aplicar el mismo estilo al submenú
                current_track = self.media_player.get_current_audio_track()
                for track_id, name in audio_tracks:
                    if isinstance(name, bytes):
                        track_name = name.decode('utf-8', errors='ignore')
                    elif isinstance(name, str):
                        track_name = name
                    else:
                        track_name = f"Pista {track_id}"
                    action = QAction(track_name, self)
                    action.setCheckable(True)
                    action.setChecked(track_id == current_track)
                    # Usar una función interior para evitar problemas de captura en lambdas
                    def create_track_handler(tid):
                        return lambda: self.media_player.change_audio_track(tid)
                    action.triggered.connect(create_track_handler(track_id))
                    audio_menu.addAction(action)
                context_menu.addMenu(audio_menu)
        
        # Mostrar el menú en la posición global
        global_pos = self.mapToGlobal(position)
        context_menu.exec(global_pos)
    
    def toggle_fullscreen(self):
        """Alterna entre modo pantalla completa y ventana normal"""
        if self.parent_window:
            self.parent_window.toggle_fullscreen()
