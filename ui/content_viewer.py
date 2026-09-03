from PyQt6.QtWidgets import QStackedWidget, QTextEdit, QLabel
from PyQt6.QtCore import Qt


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

    def display(self, result: dict):
        content = result.get("content", "")
        file_type = result.get("type", "unknown")
        name = result.get("name", "unknown")

        if file_type in {"text", "markdown", "log", "json", "xml"}:
            self.text_view.setText(content)
            self.setCurrentIndex(0)
        elif file_type == "image":
            self.image_view.setText(content)
            self.setCurrentIndex(1)
        elif file_type == "error":
            self.placeholder.setText(content)
            self.setCurrentIndex(2)
        else:
            self.placeholder.setText(content)
            self.setCurrentIndex(2)
