from PyQt6.QtWidgets import (
    QMainWindow, QSplitter, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QLineEdit
)
from PyQt6.QtCore import Qt, pyqtSignal
from .file_tree import FileTree
from .content_viewer import ContentViewer


class MainWindow(QMainWindow):
    file_selected = pyqtSignal(str)

    def __init__(self, directory: str | None = None):
        super().__init__()
        self.setWindowTitle("Vibevi - File Viewer")
        self.setGeometry(100, 100, 1200, 800)

        self._history: list[str] = []
        self._history_index: int = -1
        self._home_dir: str = directory or ""

        central = QWidget()
        self.setCentralWidget(central)
        layout = QVBoxLayout(central)
        layout.setContentsMargins(0, 0, 0, 0)

        nav = QWidget()
        nav_layout = QHBoxLayout(nav)
        nav_layout.setContentsMargins(4, 4, 4, 4)

        self.btn_back = QPushButton("<")
        self.btn_back.setFixedWidth(30)
        self.btn_back.clicked.connect(self._go_back)
        self.btn_back.setEnabled(False)

        self.btn_forward = QPushButton(">")
        self.btn_forward.setFixedWidth(30)
        self.btn_forward.clicked.connect(self._go_forward)
        self.btn_forward.setEnabled(False)

        self.btn_home = QPushButton("Home")
        self.btn_home.setFixedWidth(50)
        self.btn_home.clicked.connect(self._go_home)

        self.address_bar = QLineEdit()
        self.address_bar.setReadOnly(True)
        self.address_bar.returnPressed.connect(self._on_address_submit)

        nav_layout.addWidget(self.btn_back)
        nav_layout.addWidget(self.btn_forward)
        nav_layout.addWidget(self.btn_home)
        nav_layout.addWidget(self.address_bar)

        layout.addWidget(nav)

        splitter = QSplitter(Qt.Orientation.Horizontal)

        self.content_viewer = ContentViewer()
        self.file_tree = FileTree()

        splitter.addWidget(self.content_viewer)
        splitter.addWidget(self.file_tree)
        splitter.setSizes([600, 600])

        layout.addWidget(splitter)

        self.file_tree.file_selected.connect(self._on_file_selected)

        if directory:
            self.file_tree.set_root(directory)

    def _on_file_selected(self, path: str):
        if self._history_index < len(self._history) - 1:
            self._history = self._history[:self._history_index + 1]
        self._history.append(path)
        self._history_index = len(self._history) - 1
        self._update_nav()
        self.file_selected.emit(path)

    def _update_nav(self):
        self.address_bar.setText(self._history[self._history_index])
        self.btn_back.setEnabled(self._history_index > 0)
        self.btn_forward.setEnabled(self._history_index < len(self._history) - 1)

    def _go_back(self):
        if self._history_index > 0:
            self._history_index -= 1
            self._update_nav()
            self.file_selected.emit(self._history[self._history_index])

    def _go_forward(self):
        if self._history_index < len(self._history) - 1:
            self._history_index += 1
            self._update_nav()
            self.file_selected.emit(self._history[self._history_index])

    def _go_home(self):
        if self._home_dir:
            self.file_tree.set_root(self._home_dir)
            self._history.clear()
            self._history_index = -1
            self.address_bar.clear()
            self.btn_back.setEnabled(False)
            self.btn_forward.setEnabled(False)

    def _on_address_submit(self):
        pass
