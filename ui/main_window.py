from PyQt6.QtWidgets import QMainWindow, QSplitter
from PyQt6.QtCore import Qt, pyqtSignal
from .file_tree import FileTree
from .content_viewer import ContentViewer


class MainWindow(QMainWindow):
    file_selected = pyqtSignal(str)

    def __init__(self, directory: str | None = None):
        super().__init__()
        self.setWindowTitle("Vibevi - File Viewer")
        self.setGeometry(100, 100, 1200, 800)

        splitter = QSplitter(Qt.Orientation.Horizontal)

        self.content_viewer = ContentViewer()
        self.file_tree = FileTree()

        splitter.addWidget(self.content_viewer)
        splitter.addWidget(self.file_tree)
        splitter.setSizes([600, 600])

        self.setCentralWidget(splitter)

        self.file_tree.file_selected.connect(self.file_selected)

        if directory:
            self.file_tree.set_root(directory)
