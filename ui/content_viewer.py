from PyQt6.QtWidgets import QStackedWidget, QTextEdit, QLabel
from PyQt6.QtCore import Qt
from pathlib import Path

IMAGE_EXTS = {'.jpg', '.jpeg', '.png', '.gif', '.bmp', '.svg'}
VIDEO_EXTS = {'.avi', '.mp4', '.mkv', '.mov'}
DOC_EXTS = {'.doc', '.docx', '.pdf', '.odt'}


class ContentViewer(QStackedWidget):
    def __init__(self):
        super().__init__()

        self.text_view = QTextEdit()
        self.text_view.setReadOnly(True)

        self.image_view = QLabel()
        self.image_view.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.placeholder = QLabel()
        self.placeholder.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.addWidget(self.text_view)      # index 0
        self.addWidget(self.image_view)     # index 1
        self.addWidget(self.placeholder)    # index 2

        self.set_placeholder("Select a file to view")

    def set_placeholder(self, text: str):
        self.placeholder.setText(text)
        self.setCurrentIndex(2)

    def display(self, file_path: str):
        path = Path(file_path)
        ext = path.suffix.lower()

        if ext in {'.txt', '.py', '.md', '.json', '.xml', '.csv', '.log'}:
            self._show_text(file_path)
        elif ext in IMAGE_EXTS:
            self.image_view.setText(f"Image: {path.name}")
            self.setCurrentIndex(1)
        elif ext in VIDEO_EXTS:
            self.placeholder.setText(f"Video: {path.name}")
            self.setCurrentIndex(2)
        elif ext in DOC_EXTS:
            self.placeholder.setText(f"Document: {path.name}")
            self.setCurrentIndex(2)
        else:
            self.placeholder.setText(f"File: {path.name}")
            self.setCurrentIndex(2)

    def _show_text(self, file_path: str):
        try:
            encodings = ['utf-8', 'cp1251', 'latin-1']
            content = None
            for enc in encodings:
                try:
                    with open(file_path, 'r', encoding=enc) as f:
                        content = f.read()
                    break
                except UnicodeDecodeError:
                    continue
            if content is not None:
                self.text_view.setText(content)
                self.setCurrentIndex(0)
            else:
                self.placeholder.setText("Cannot decode file")
                self.setCurrentIndex(2)
        except Exception as e:
            self.placeholder.setText(f"Error: {e}")
            self.setCurrentIndex(2)
