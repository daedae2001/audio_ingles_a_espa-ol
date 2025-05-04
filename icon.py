#!/usr/bin/env python3
"""
Script para crear un icono básico para la aplicación TV IP Player
"""

from PyQt6.QtGui import QIcon, QPixmap, QPainter, QColor, QFont, QBrush
from PyQt6.QtCore import Qt, QSize
import os

def create_app_icon():
    """Crea un icono básico para la aplicación"""
    # Colores del tema
    accent_color = QColor("#FF8000")  # Naranja
    dark_bg = QColor("#1E1E1E")       # Fondo oscuro
    
    # Tamaños de icono para Windows
    sizes = [16, 32, 48, 64, 128, 256]
    
    # Crear el icono
    icon = QIcon()
    
    for size in sizes:
        # Crear un pixmap del tamaño adecuado
        pixmap = QPixmap(size, size)
        pixmap.fill(Qt.GlobalColor.transparent)
        
        # Configurar el pintor
        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        # Dibujar un círculo con el color de acento
        painter.setBrush(QBrush(accent_color))
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawEllipse(0, 0, size, size)
        
        # Dibujar las letras "TV" en el centro
        font_size = size // 2
        font = QFont("Arial", font_size, QFont.Weight.Bold)
        painter.setFont(font)
        painter.setPen(dark_bg)
        painter.drawText(pixmap.rect(), Qt.AlignmentFlag.AlignCenter, "TV")
        
        # Finalizar el pintor
        painter.end()
        
        # Añadir el pixmap al icono
        icon.addPixmap(pixmap, QIcon.Mode.Normal)
    
    # Guardar el icono
    icon_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "icon.ico")
    
    # Crear una aplicación temporal para guardar el icono
    from PyQt6.QtWidgets import QApplication
    import sys
    app = QApplication.instance() or QApplication(sys.argv)
    
    # Guardar el icono como archivo .ico
    icon.pixmap(QSize(256, 256)).save(icon_path, "ICO")
    
    print(f"Icono creado exitosamente en: {icon_path}")
    return icon_path

if __name__ == "__main__":
    create_app_icon()
