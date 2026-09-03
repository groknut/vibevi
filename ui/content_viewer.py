from PyQt6.QtWidgets import (
    QStackedWidget, QTextEdit, QLabel, QWidget, QVBoxLayout,
    QPushButton, QHBoxLayout, QSlider
)
from PyQt6.QtCore import Qt, QUrl
from PyQt6.QtGui import QPixmap

try:
    from PyQt6.QtMultimedia import QMediaPlayer, QAudioOutput
    from PyQt6.QtMultimediaWidgets import QVideoWidget
    HAS_MULTIMEDIA = True
except ImportError:
    HAS_MULTIMEDIA = False


class ContentViewer(QStackedWidget):
    def __init__(self):
        super().__init__()

        self.text_view = QTextEdit()
        self.text_view.setReadOnly(True)

        self.image_view = QLabel()
        self.image_view.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.image_view.setScaledContents(True)

        self.placeholder = QLabel()
        self.placeholder.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.addWidget(self.text_view)      # index 0
        self.addWidget(self.image_view)     # index 1
        self.addWidget(self.placeholder)    # index 2

        self._init_raw_view()

        if HAS_MULTIMEDIA:
            self._init_media_player()
        else:
            self.video_view = None
            self.audio_view = None

        self.set_placeholder("Select a file to view")

    def _init_raw_view(self):
        self.raw_text = QTextEdit()
        self.raw_text.setReadOnly(True)

        self.raw_toggle = QPushButton("Show Hex")
        self.raw_toggle.clicked.connect(self._toggle_raw_view)

        self.raw_is_hex = False
        self.raw_result = None

        container = QWidget()
        layout = QVBoxLayout(container)
        layout.addWidget(self.raw_text)
        layout.addWidget(self.raw_toggle)

        self.raw_view = container
        self.addWidget(container)  # index 3

    def _toggle_raw_view(self):
        if self.raw_result is None:
            return
        self.raw_is_hex = not self.raw_is_hex
        if self.raw_is_hex:
            self.raw_text.setText(self.raw_result.get("hex_content", ""))
            self.raw_toggle.setText("Show Text")
        else:
            self.raw_text.setText(self.raw_result.get("content", ""))
            self.raw_toggle.setText("Show Hex")

    def _init_media_player(self):
        self.player = QMediaPlayer()
        self.audio_output = QAudioOutput()
        self.player.setAudioOutput(self.audio_output)

        self.play_btn = QPushButton("Play")
        self.play_btn.clicked.connect(self._toggle_play)

        self.slider = QSlider(Qt.Orientation.Horizontal)
        self.slider.setRange(0, 0)
        self.slider.sliderMoved.connect(self.player.setPosition)

        self.player.positionChanged.connect(self._on_position_changed)
        self.player.durationChanged.connect(self._on_duration_changed)
        self.player.playbackStateChanged.connect(self._on_state_changed)

        # Video view
        self.video_widget = QVideoWidget()
        self.player.setVideoOutput(self.video_widget)

        controls = QHBoxLayout()
        controls.addWidget(self.play_btn)
        controls.addWidget(self.slider)

        video_container = QWidget()
        layout = QVBoxLayout(video_container)
        layout.addWidget(self.video_widget)
        layout.addLayout(controls)

        self.video_view = video_container
        self.addWidget(video_container)  # index 4

        # Audio view
        self.audio_meta = QTextEdit()
        self.audio_meta.setReadOnly(True)

        audio_controls = QHBoxLayout()
        audio_controls.addWidget(self.play_btn)
        audio_controls.addWidget(self.slider)

        audio_container = QWidget()
        layout = QVBoxLayout(audio_container)
        layout.addWidget(self.audio_meta)
        layout.addLayout(audio_controls)

        self.audio_view = audio_container
        self.addWidget(audio_container)  # index 5

    def _toggle_play(self):
        if self.player.playbackState() == QMediaPlayer.PlaybackState.PlayingState:
            self.player.pause()
        else:
            self.player.play()

    def _on_position_changed(self, position):
        self.slider.setValue(position)

    def _on_duration_changed(self, duration):
        self.slider.setRange(0, duration)

    def _on_state_changed(self, state):
        if state == QMediaPlayer.PlaybackState.PlayingState:
            self.play_btn.setText("Pause")
        else:
            self.play_btn.setText("Play")

    def set_placeholder(self, text: str):
        self.placeholder.setText(text)
        self.setCurrentIndex(2)

    def display(self, result: dict):
        content = result.get("content", "")
        file_type = result.get("type", "unknown")

        if file_type == "video":
            if self.video_view and HAS_MULTIMEDIA:
                self.player.setSource(QUrl.fromLocalFile(result["path"]))
                self.setCurrentIndex(4)
            else:
                self.text_view.setText(content)
                self.setCurrentIndex(0)
        elif file_type == "audio":
            if self.audio_view and HAS_MULTIMEDIA:
                self.audio_meta.setText(content)
                self.player.setSource(QUrl.fromLocalFile(result["path"]))
                self.setCurrentIndex(5)
            else:
                self.text_view.setText(content)
                self.setCurrentIndex(0)
        elif file_type == "image":
            path = result.get("path", "")
            pixmap = QPixmap(path)
            if not pixmap.isNull():
                self.image_view.setPixmap(pixmap)
            else:
                self.image_view.setText(content)
            self.setCurrentIndex(1)
        elif file_type in {"text", "markdown", "log", "json", "xml"}:
            self.text_view.setText(content)
            self.setCurrentIndex(0)
        elif file_type == "raw":
            self.raw_result = result
            self.raw_is_hex = False
            self.raw_text.setText(content)
            self.raw_toggle.setText("Show Hex")
            self.setCurrentIndex(3)
        elif file_type == "error":
            self.placeholder.setText(content)
            self.setCurrentIndex(2)
        else:
            self.placeholder.setText(content)
            self.setCurrentIndex(2)
