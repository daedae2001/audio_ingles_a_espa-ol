"""
Reproductor de prueba simplificado para diagnosticar problemas
"""
import sys
import os
from PyQt6.QtWidgets import QApplication, QMainWindow, QWidget, QVBoxLayout, QPushButton, QLabel
from PyQt6.QtCore import Qt
import vlc

class TestPlayer(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle('Reproductor de Prueba')
        self.setGeometry(100, 100, 800, 600)
        
        # Widget principal
        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        layout = QVBoxLayout(main_widget)
        
        # Etiqueta informativa
        info_label = QLabel("Reproductor de prueba - Haz clic en reproducir")
        layout.addWidget(info_label)
        
        # Widget para el video
        self.video_widget = QWidget()
        self.video_widget.setStyleSheet("background-color: black;")
        layout.addWidget(self.video_widget, 1)
        
        # Botón de reproducción
        play_button = QPushButton("Reproducir video de prueba")
        play_button.clicked.connect(self.play_test_video)
        layout.addWidget(play_button)
        
        # Inicializar VLC
        self.instance = vlc.Instance()
        self.player = self.instance.media_player_new()
        
        # Configurar el reproductor para usar el widget
        if sys.platform.startswith('win'):
            self.player.set_hwnd(int(self.video_widget.winId()))
        elif sys.platform.startswith('linux'):
            self.player.set_xwindow(self.video_widget.winId())
        elif sys.platform.startswith('darwin'):
            self.player.set_nsobject(int(self.video_widget.winId()))
    
    def play_test_video(self):
        """Reproduce un video de prueba"""
        try:
            # URL de un video de prueba
            test_url = "https://commondatastorage.googleapis.com/gtv-videos-bucket/sample/BigBuckBunny.mp4"
            
            # Crear un medio con la URL
            media = self.instance.media_new(test_url)
            self.player.set_media(media)
            
            # Iniciar reproducción
            self.player.play()
            
            print(f"Reproduciendo: {test_url}")
        except Exception as e:
            print(f"Error al reproducir: {e}")

if __name__ == '__main__':
    app = QApplication(sys.argv)
    player = TestPlayer()
    player.show()
    sys.exit(app.exec())
