from PyQt6.QtWidgets import QTreeView
from PyQt6.QtGui import QFileSystemModel
from PyQt6.QtCore import pyqtSignal, QDir, QSortFilterProxyModel
from pathlib import Path


class FileTree(QTreeView):
    file_selected = pyqtSignal(str)

    def __init__(self):
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
        self.model.setRootPath(path)
        index = self.model.index(path)
        self.setRootIndex(self.proxy.mapFromSource(index))

    def _on_click(self, index):
        source_index = self.proxy.mapToSource(index)
        file_path = self.model.filePath(source_index)
        if Path(file_path).is_file():
            self.file_selected.emit(file_path)
