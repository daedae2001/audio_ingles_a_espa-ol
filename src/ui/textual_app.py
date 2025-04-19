from textual.app import App, ComposeResult
from textual.containers import Container
from textual.widgets import Header, Footer, Static

class TVIPTextualApp(App):
    """Aplicación principal con Textual."""
    CSS_PATH = None

    def compose(self) -> ComposeResult:
        yield Header(show_clock=True)
        yield Container(
            Static("Bienvenido a TV IP Player (Textual UI)", id="main-title"),
            id="main-container"
        )
        yield Footer()

if __name__ == "__main__":
    TVIPTextualApp().run()
