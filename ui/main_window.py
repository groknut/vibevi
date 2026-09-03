import os
from PyQt6.QtWidgets import (
    QMainWindow, QSplitter, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QLabel
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QKeySequence, QShortcut
from .file_tree import FileTree
from .content_viewer import ContentViewer


class MainWindow(QMainWindow):
    file_selected = pyqtSignal(str)

    def __init__(self, directory: str | None = None):
        super().__init__()
        self.setWindowTitle("Vibevi - File Viewer")
        self.setGeometry(100, 100, 1200, 800)

        self._home_dir = os.path.expanduser('~')
        self._current_dir = directory or ""

        central = QWidget()
        self.setCentralWidget(central)
        main_layout = QVBoxLayout(central)
        main_layout.setContentsMargins(0, 0, 0, 0)

        splitter = QSplitter(Qt.Orientation.Horizontal)

        self.content_viewer = ContentViewer()

        right_panel = QWidget()
        right_layout = QVBoxLayout(right_panel)
        right_layout.setContentsMargins(0, 0, 0, 0)
        right_layout.setSpacing(0)

        nav_bar = QWidget()
        nav_layout = QHBoxLayout(nav_bar)
        nav_layout.setContentsMargins(4, 4, 4, 4)
        nav_layout.setSpacing(2)

        self.btn_back = QPushButton("<")
        self.btn_back.setFixedWidth(30)
        self.btn_back.clicked.connect(self._go_back)

        self.btn_forward = QPushButton(">")
        self.btn_forward.setFixedWidth(30)
        self.btn_forward.clicked.connect(self._go_forward)

        self.btn_home = QPushButton("Home")
        self.btn_home.setFixedWidth(50)
        self.btn_home.clicked.connect(self._go_home)

        nav_layout.addWidget(self.btn_back)
        nav_layout.addWidget(self.btn_forward)
        nav_layout.addWidget(self.btn_home)
        nav_layout.addStretch()

        self.file_tree = FileTree()
        self.file_tree.clicked.connect(self._on_tree_clicked)

        self.dir_label = QLabel()
        self.dir_label.setStyleSheet("padding: 4px; color: #666;")

        right_layout.addWidget(nav_bar)
        right_layout.addWidget(self.file_tree)
        right_layout.addWidget(self.dir_label)

        splitter.addWidget(self.content_viewer)
        splitter.addWidget(right_panel)
        splitter.setSizes([600, 600])

        main_layout.addWidget(splitter)

        self.file_tree.file_selected.connect(self._on_file_selected)

        if directory:
            self.file_tree.set_root(directory)
            self._current_dir = directory
            self.dir_label.setText(directory)
        self._update_nav()

        quit_shortcut = QShortcut(QKeySequence("Ctrl+Q"), self)
        quit_shortcut.activated.connect(self.close)

    def _on_tree_clicked(self, index):
        from pathlib import Path
        source_index = self.file_tree.proxy.mapToSource(index)
        path = self.file_tree.model.filePath(source_index)
        if Path(path).is_dir():
            self._current_dir = path
            self.dir_label.setText(path)
            self.file_tree.set_root(path)
            self._update_nav()

    def _on_file_selected(self, path: str):
        self._current_dir = os.path.dirname(path)
        self.dir_label.setText(self._current_dir)
        self._update_nav()
        self.file_selected.emit(path)

    def _update_nav(self):
        self.btn_back.setEnabled(self._current_dir != "" and self._current_dir != "/")
        self.btn_forward.setEnabled(self._has_subdirs())

    def _has_subdirs(self) -> bool:
        if not self._current_dir or not os.path.isdir(self._current_dir):
            return False
        try:
            for entry in os.scandir(self._current_dir):
                if entry.is_dir() and not entry.name.startswith("."):
                    return True
        except PermissionError:
            pass
        return False

    def _go_back(self):
        parent = os.path.dirname(self._current_dir)
        if parent and parent != self._current_dir:
            self._current_dir = parent
            self.dir_label.setText(parent)
            self.file_tree.set_root(parent)
            self._update_nav()

    def _go_forward(self):
        if not self._current_dir or not os.path.isdir(self._current_dir):
            return
        try:
            for entry in os.scandir(self._current_dir):
                if entry.is_dir() and not entry.name.startswith("."):
                    self._current_dir = entry.path
                    self.dir_label.setText(entry.path)
                    self.file_tree.set_root(entry.path)
                    self._update_nav()
                    return
        except PermissionError:
            pass

    def _go_home(self):
        self._current_dir = self._home_dir
        self.dir_label.setText(self._home_dir)
        self.file_tree.set_root(self._home_dir)
        self._update_nav()
