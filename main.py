import sys
from PyQt6.QtWidgets import QApplication
from src.ui.main_window import MainWindow

def main():
    """Punto de entrada principal de la aplicación"""
    # Crear la aplicación Qt
    app = QApplication(sys.argv)
    
    # Crear y mostrar la ventana principal
    window = MainWindow()
    window.show()
    
    # Ejecutar el bucle de eventos
    sys.exit(app.exec())

if __name__ == '__main__':
    main()
