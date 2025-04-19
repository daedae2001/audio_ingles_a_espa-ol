"""
Aplicación Textual para TV-IP - Versión mínima para pruebas
"""
import os
import sys
import traceback
from textual.app import App, ComposeResult
from textual.containers import Container, Horizontal, Vertical
from textual.widgets import Header, Footer, Static, Label, Button

# CSS mínimo para la aplicación
CSS = """
#main-container {
    height: 100%;
    background: #222;
    color: #ddd;
}

#status-label {
    text-align: center;
    padding: 2;
}

Button {
    margin: 1;
}
"""

class TVIPTextualApp(App):
    """Aplicación Textual mínima para TV-IP"""
    CSS_PATH = None
    CSS = CSS
    BINDINGS = [
        ("q", "quit", "Salir"),
    ]
    
    def compose(self) -> ComposeResult:
        """Composición de la interfaz principal"""
        yield Header(show_clock=True)
        
        with Container(id="main-container"):
            yield Label("Aplicación TV-IP con Textual", id="status-label")
            yield Label("Versión mínima para pruebas", id="status-label")
            yield Button("Botón de prueba", id="test-button")
        
        yield Footer()
    
    def on_button_pressed(self, event):
        """Maneja los eventos de botones"""
        self.notify("Botón presionado")
    
    def notify(self, message):
        """Muestra una notificación"""
        self.bell()
        self.log.info(message)

def run_app():
    """Ejecuta la aplicación con manejo de errores"""
    try:
        app = TVIPTextualApp()
        app.run()
    except Exception as e:
        print(f"Error fatal: {str(e)}")
        traceback.print_exc()
        input("Presiona Enter para salir...")
        sys.exit(1)

if __name__ == "__main__":
    run_app()
