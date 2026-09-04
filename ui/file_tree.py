"""File tree widget for browsing the filesystem."""

from PyQt6.QtWidgets import QTreeView
from PyQt6.QtGui import QFileSystemModel, QKeySequence
from PyQt6.QtCore import pyqtSignal, QDir, QSortFilterProxyModel, Qt
from pathlib import Path


class FileTree(QTreeView):
    """File tree view with keyboard navigation and file selection.

    Displays the filesystem using QFileSystemModel with a proxy filter.
    Supports clicking and Enter/Space keys for file selection.
    Enter on directories navigates into them.

    Signals:
        file_selected(str): Emitted when a file is selected.
    """

    file_selected = pyqtSignal(str)

    def __init__(self):
        """Initialize the file tree with filesystem model and proxy."""
        super().__init__()

        self.model = QFileSystemModel()
        self.model.setRootPath(QDir.rootPath())
        self.model.setFilter(
            QDir.Filter.Dirs | QDir.Filter.Files | QDir.Filter.NoDotAndDotDot
        )

        self.proxy = QSortFilterProxyModel()
        self.proxy.setSourceModel(self.model)

        self.setModel(self.proxy)
        self.setRootIndex(
            self.proxy.mapFromSource(self.model.index(QDir.rootPath()))
        )

        self.setColumnWidth(0, 250)
        self.setHeaderHidden(False)

        self.clicked.connect(self._on_click)

    def set_root(self, path: str):
        """Set the root directory for the file tree.

        Args:
            path: Path to the directory to display.
        """
        self.model.setRootPath(path)
        index = self.model.index(path)
        self.setRootIndex(self.proxy.mapFromSource(index))

    def _on_click(self, index):
        """Handle click events on tree items.

        Emits file_selected if a file is clicked.

        Args:
            index: Model index of the clicked item.
        """
        source_index = self.proxy.mapToSource(index)
        file_path = self.model.filePath(source_index)
        if Path(file_path).is_file():
            self.file_selected.emit(file_path)

    def keyPressEvent(self, event):
        """Handle keyboard events for file selection.

        Enter/Space on a file emits file_selected.
        Enter/Space on a directory navigates into it.
        """
        if event.key() in (Qt.Key.Key_Return, Qt.Key.Key_Enter, Qt.Key.Key_Space):
            index = self.currentIndex()
            if index.isValid():
                source_index = self.proxy.mapToSource(index)
                file_path = self.model.filePath(source_index)
                if Path(file_path).is_file():
                    self.file_selected.emit(file_path)
                    return
                elif Path(file_path).is_dir():
                    self.set_root(file_path)
                    return
        super().keyPressEvent(event)
