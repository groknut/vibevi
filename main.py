import sys
from pathlib import Path
from PyQt6.QtWidgets import QApplication
from ui import MainWindow


def main():
    app = QApplication(sys.argv)

    directory = None
    if len(sys.argv) > 1:
        path = Path(sys.argv[1])
        if path.is_dir():
            directory = str(path)

    window = MainWindow(directory=directory)
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
