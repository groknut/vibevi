"""Application controller connecting UI and parsers."""

from parser import parse_file
from ui import MainWindow


class App:
    """Application controller connecting UI and parsers.

    Creates the main window and routes file selection events
    to the appropriate parser, then displays the result.

    Attributes:
        window: The main application window.
    """

    def __init__(self, directory: str | None = None):
        """Initialize the application.

        Args:
            directory: Optional starting directory for the file tree.
        """
        self.window = MainWindow(directory=directory)
        self.window.file_selected.connect(self._on_file_selected)

    def _on_file_selected(self, path: str):
        """Handle file selection from the file tree.

        Parses the file and displays the result in the content viewer.

        Args:
            path: Full path to the selected file.
        """
        result = parse_file(path)
        self.window.content_viewer.display(result)

    def show(self):
        """Show the main window."""
        self.window.show()
