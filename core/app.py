from parser import parse_file
from ui import MainWindow


class App:
    """Application controller connecting UI and parsers."""

    def __init__(self, directory: str | None = None):
        self.window = MainWindow(directory=directory)
        self.window.file_selected.connect(self._on_file_selected)

    def _on_file_selected(self, path: str):
        result = parse_file(path)
        self.window.content_viewer.display(result)

    def show(self):
        self.window.show()
