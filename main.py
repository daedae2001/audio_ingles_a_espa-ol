import sys
import flet as ft
from src.ui.flet_app import main as flet_main

def main():
    """Punto de entrada principal de la aplicación (Flet UI)"""
    try:
        # Iniciamos la aplicación Flet
        ft.app(target=flet_main)
    except Exception as e:
        print(f"Error al iniciar la aplicación: {e}")
        input("Presiona Enter para salir...")
        sys.exit(1)

if __name__ == '__main__':
    main()
