import os
from PyQt6.QtWidgets import (
    QMainWindow, QSplitter, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QLabel, QListWidget, QListWidgetItem, QStyle
)
from PyQt6.QtCore import Qt, pyqtSignal
from .file_tree import FileTree
from .content_viewer import ContentViewer
from sort import sort_files, SortKey


class MainWindow(QMainWindow):
    file_selected = pyqtSignal(str)

    def __init__(self, directory: str | None = None):
        super().__init__()
        self.setWindowTitle("Vibevi - File Viewer")
        self.setGeometry(100, 100, 1200, 800)

        self._home_dir = os.path.expanduser('~')
        self._current_dir = directory or ""
        self._sort_key = SortKey.NAME
        self._sort_reverse = False

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

        sort_bar = QWidget()
        sort_layout = QHBoxLayout(sort_bar)
        sort_layout.setContentsMargins(4, 2, 4, 2)
        sort_layout.setSpacing(2)

        sort_label = QLabel("Sort:")
        sort_label.setStyleSheet("color: #666; padding: 2px;")
        sort_layout.addWidget(sort_label)

        self.btn_sort_name = QPushButton("Name")
        self.btn_sort_name.setCheckable(True)
        self.btn_sort_name.setChecked(True)
        self.btn_sort_name.clicked.connect(lambda: self._set_sort(SortKey.NAME))

        self.btn_sort_date = QPushButton("Date")
        self.btn_sort_date.setCheckable(True)
        self.btn_sort_date.clicked.connect(lambda: self._set_sort(SortKey.DATE))

        self.btn_sort_ext = QPushButton(".ext")
        self.btn_sort_ext.setCheckable(True)
        self.btn_sort_ext.clicked.connect(lambda: self._set_sort(SortKey.EXTENSION))

        self.btn_sort_order = QPushButton("A→Z")
        self.btn_sort_order.setFixedWidth(40)
        self.btn_sort_order.clicked.connect(self._toggle_sort_order)

        sort_layout.addWidget(self.btn_sort_name)
        sort_layout.addWidget(self.btn_sort_date)
        sort_layout.addWidget(self.btn_sort_ext)
        sort_layout.addWidget(self.btn_sort_order)
        sort_layout.addStretch()

        self.file_tree = FileTree()
        self.file_tree.clicked.connect(self._on_tree_clicked)

        self.sorted_list = QListWidget()
        self.sorted_list.setVisible(False)
        self.sorted_list.itemClicked.connect(self._on_sorted_click)

        self.dir_label = QLabel()
        self.dir_label.setStyleSheet("padding: 4px; color: #666;")

        right_layout.addWidget(nav_bar)
        right_layout.addWidget(sort_bar)
        right_layout.addWidget(self.file_tree)
        right_layout.addWidget(self.sorted_list)
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

    def _set_sort(self, key: SortKey):
        self._sort_key = key
        for btn in (self.btn_sort_name, self.btn_sort_date, self.btn_sort_ext):
            btn.setChecked(False)

        if key == SortKey.NAME:
            self.btn_sort_name.setChecked(True)
        elif key == SortKey.DATE:
            self.btn_sort_date.setChecked(True)
        elif key == SortKey.EXTENSION:
            self.btn_sort_ext.setChecked(True)

        self._refresh_sorted_list()

    def _toggle_sort_order(self):
        self._sort_reverse = not self._sort_reverse
        self.btn_sort_order.setText("Z→A" if self._sort_reverse else "A→Z")
        self._refresh_sorted_list()

    def _refresh_sorted_list(self):
        if not self._current_dir or not os.path.isdir(self._current_dir):
            return

        entries = sort_files(
            self._current_dir,
            sort_by=self._sort_key,
            reverse=self._sort_reverse,
        )

        style = self.style()
        file_icon = style.standardIcon(QStyle.StandardPixmap.SP_FileIcon)
        dir_icon = style.standardIcon(QStyle.StandardPixmap.SP_DirIcon)

        self.sorted_list.clear()
        for entry in entries:
            item = QListWidgetItem(entry["name"])
            item.setData(Qt.ItemDataRole.UserRole, entry["path"])

            if os.path.isdir(entry["path"]):
                item.setIcon(dir_icon)
            else:
                item.setIcon(file_icon)

            self.sorted_list.addItem(item)

        self.file_tree.setVisible(False)
        self.sorted_list.setVisible(True)

    def _on_sorted_click(self, item: QListWidgetItem):
        path = item.data(Qt.ItemDataRole.UserRole)
        if path and os.path.isfile(path):
            self._current_dir = os.path.dirname(path)
            self.dir_label.setText(self._current_dir)
            self._update_nav()
            self.file_selected.emit(path)

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
