from PyQt6.QtWidgets import (
    QStackedWidget, QTextBrowser, QLabel, QWidget, QVBoxLayout,
    QPushButton, QHBoxLayout, QSlider, QTextEdit, QScrollArea, QSizePolicy
)
from PyQt6.QtCore import Qt, QUrl, QSize, QMarginsF
from PyQt6.QtGui import QPixmap, QPageSize
from parser.epub import cleanup_epub_images
import os
import shutil

try:
    from PyQt6.QtPrintSupport import QPrinter
    HAS_PRINTER = True
except ImportError:
    HAS_PRINTER = False

try:
    from PyQt6.QtMultimedia import QMediaPlayer, QAudioOutput
    from PyQt6.QtMultimediaWidgets import QVideoWidget
    HAS_MULTIMEDIA = True
except ImportError:
    HAS_MULTIMEDIA = False


def _format_audio_info(result: dict) -> str:
    tags = result.get("tags", {})
    title = tags.get("title", "")
    artist = tags.get("artist", "")
    album = tags.get("album", "")
    duration = result.get("duration", 0)
    fmt = result.get("format", "")
    bit_rate = result.get("bit_rate", 0)

    if not title:
        name = result.get("name", "Unknown")
        title = name.rsplit("/", 1)[-1].rsplit("\\", 1)[-1]
        if "." in title:
            title = title.rsplit(".", 1)[0]

    parts = []
    if fmt:
        parts.append(fmt.upper())
    if duration:
        mins = int(duration) // 60
        secs = int(duration) % 60
        parts.append(f"{mins}:{secs:02d}")
    if bit_rate:
        kbps = bit_rate // 1000
        parts.append(f"{kbps} kbps")

    info_line = " · ".join(parts)

    html = f"""
    <div style="text-align: center; padding: 20px;">
        <div style="font-size: 18px; font-weight: bold; margin-bottom: 4px;">{title}</div>
        <div style="font-size: 14px; color: #666; margin-bottom: 4px;">{artist}</div>
        {"<div style='font-size: 12px; color: #999; margin-bottom: 4px;'>" + album + "</div>" if album else ""}
        <div style="font-size: 12px; color: #999;">{info_line}</div>
    </div>
    """
    return html


def _escape_html(text: str) -> str:
    return text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def _html_to_page_images(html: str, dpi: int = 200) -> list[dict]:
    """Render HTML content to page images using QPrinter and PyMuPDF."""
    if not HAS_PRINTER:
        return []

    import tempfile

    from PyQt6.QtGui import QTextDocument, QPageLayout

    doc = QTextDocument()
    doc.setHtml(html)

    pdf_path = os.path.join(tempfile.mkdtemp(prefix="vibevi_docx_"), "rendered.pdf")
    printer = QPrinter(QPrinter.PrinterMode.HighResolution)
    printer.setOutputFormat(QPrinter.OutputFormat.PdfFormat)
    printer.setOutputFileName(pdf_path)

    layout = QPageLayout(
        QPageSize(QPageSize.PageSizeId.A4),
        QPageLayout.Orientation.Portrait,
        QMarginsF(15, 15, 15, 15),
        QPageLayout.Unit.Millimeter,
    )
    printer.setPageLayout(layout)

    doc.print(printer)

    try:
        import pymupdf
    except ImportError:
        return []

    pdf_doc = pymupdf.open(pdf_path)
    page_images: list[dict] = []
    img_dir = tempfile.mkdtemp(prefix="vibevi_docx_img_")

    for i in range(len(pdf_doc)):
        page = pdf_doc.load_page(i)
        pix = page.get_pixmap(dpi=dpi)
        image_path = os.path.join(img_dir, f"page_{i + 1}.png")
        pix.save(image_path)
        page_images.append({"page": i + 1, "image_path": image_path})

    pdf_doc.close()
    return page_images


class PdfViewer(QWidget):
    def __init__(self):
        super().__init__()
        self._pages: list[dict] = []
        self._current = 0
        self._tmp_dir = ""

        self.image_label = QLabel()
        self.image_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.image_label.setScaledContents(True)
        self.image_label.setSizePolicy(
            QSizePolicy.Policy.Expanding,
            QSizePolicy.Policy.Expanding,
        )

        self.scroll_area = QScrollArea()
        self.scroll_area.setWidget(self.image_label)
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.prev_btn = QPushButton("< Prev")
        self.prev_btn.clicked.connect(self._prev_page)

        self.next_btn = QPushButton("Next >")
        self.next_btn.clicked.connect(self._next_page)

        self.page_label = QLabel()
        self.page_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        controls = QHBoxLayout()
        controls.addWidget(self.prev_btn)
        controls.addWidget(self.page_label)
        controls.addWidget(self.next_btn)

        layout = QVBoxLayout(self)
        layout.addWidget(self.scroll_area)
        layout.addLayout(controls)

    def load(self, result: dict):
        self._cleanup()
        self._pages = result.get("page_images", [])
        self._current = 0
        if self._pages:
            self._tmp_dir = os.path.dirname(self._pages[0]["image_path"])
        self._show_page(0)

    def _cleanup(self):
        if self._tmp_dir and os.path.isdir(self._tmp_dir):
            try:
                shutil.rmtree(self._tmp_dir)
            except Exception:
                pass
            self._tmp_dir = ""

    def _show_page(self, index: int):
        if not self._pages:
            self.image_label.setText("No pages")
            self.page_label.setText("")
            self.prev_btn.setEnabled(False)
            self.next_btn.setEnabled(False)
            return

        self._current = index
        page = self._pages[index]
        pixmap = QPixmap(page["image_path"])
        if not pixmap.isNull():
            scaled = pixmap.scaled(
                self.scroll_area.size(),
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation,
            )
            self.image_label.setPixmap(scaled)
        else:
            self.image_label.setText(f"Failed to render page {index + 1}")

        self.page_label.setText(f"Page {index + 1} / {len(self._pages)}")
        self.prev_btn.setEnabled(index > 0)
        self.next_btn.setEnabled(index < len(self._pages) - 1)

    def _prev_page(self):
        if self._current > 0:
            self._show_page(self._current - 1)

    def _next_page(self):
        if self._current < len(self._pages) - 1:
            self._show_page(self._current + 1)


class ContentViewer(QStackedWidget):
    def __init__(self):
        super().__init__()

        self.text_view = QTextBrowser()
        self.text_view.setOpenExternalLinks(True)

        self.image_label = QLabel()
        self.image_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.image_scroll = QScrollArea()
        self.image_scroll.setWidget(self.image_label)
        self.image_scroll.setWidgetResizable(True)
        self.image_scroll.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.placeholder = QLabel()
        self.placeholder.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.addWidget(self.text_view)      # index 0
        self.addWidget(self.image_scroll)   # index 1
        self.addWidget(self.placeholder)    # index 2

        self._init_raw_view()

        if HAS_MULTIMEDIA:
            self._init_media_player()
        else:
            self.video_view = None
            self.audio_view = None

        self.pdf_viewer = PdfViewer()
        self.addWidget(self.pdf_viewer)  # index 7

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

        self._init_epub_view()

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

    def _init_epub_view(self):
        self.epub_browser = QTextBrowser()
        self.epub_browser.setOpenExternalLinks(True)

        self.epub_title = QLabel()
        self.epub_title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.epub_title.setStyleSheet("font-size: 14px; font-weight: bold; padding: 5px;")

        self.epub_chapter_label = QLabel()
        self.epub_chapter_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.epub_prev_btn = QPushButton("← Назад")
        self.epub_prev_btn.clicked.connect(self._epub_prev)

        self.epub_next_btn = QPushButton("Вперёд →")
        self.epub_next_btn.clicked.connect(self._epub_next)

        nav_layout = QHBoxLayout()
        nav_layout.addWidget(self.epub_prev_btn)
        nav_layout.addWidget(self.epub_chapter_label)
        nav_layout.addWidget(self.epub_next_btn)

        container = QWidget()
        layout = QVBoxLayout(container)
        layout.addWidget(self.epub_title)
        layout.addWidget(self.epub_browser)
        layout.addLayout(nav_layout)

        self.epub_view = container
        self.epub_chapters = []
        self.epub_index = 0
        self._epub_images_dir = None
        self.addWidget(container)  # index 4

    def _epub_prev(self):
        if self.epub_chapters and self.epub_index > 0:
            self.epub_index -= 1
            self._epub_show_chapter()

    def _epub_next(self):
        if self.epub_chapters and self.epub_index < len(self.epub_chapters) - 1:
            self.epub_index += 1
            self._epub_show_chapter()

    def _epub_show_chapter(self):
        if not self.epub_chapters:
            return
        ch = self.epub_chapters[self.epub_index]
        self.epub_browser.setHtml(ch["html"])
        self.epub_chapter_label.setText(
            f"Глава {self.epub_index + 1} из {len(self.epub_chapters)}"
        )
        self.epub_prev_btn.setEnabled(self.epub_index > 0)
        self.epub_next_btn.setEnabled(self.epub_index < len(self.epub_chapters) - 1)

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
        self.addWidget(video_container)  # index 5

        # Audio view
        self.audio_title = QLabel()
        self.audio_title.setAlignment(Qt.AlignmentFlag.AlignCenter)

        audio_controls = QHBoxLayout()
        audio_controls.addWidget(self.play_btn)
        audio_controls.addWidget(self.slider)

        audio_container = QWidget()
        layout = QVBoxLayout(audio_container)
        layout.addWidget(self.audio_title)
        layout.addLayout(audio_controls)

        self.audio_view = audio_container
        self.addWidget(audio_container)  # index 6

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
                self.setCurrentIndex(5)
            else:
                self.text_view.setText(content)
                self.setCurrentIndex(0)
        elif file_type == "audio":
            if self.audio_view and HAS_MULTIMEDIA:
                self.audio_title.setText(_format_audio_info(result))
                self.player.setSource(QUrl.fromLocalFile(result["path"]))
                self.setCurrentIndex(6)
            else:
                self.text_view.setText(content)
                self.setCurrentIndex(0)
        elif file_type == "epub":
            cleanup_epub_images(self._epub_images_dir)
            self._epub_images_dir = result.get("images_dir", "")
            self.epub_title.setText(
                f"{result.get('title', '')} — {result.get('creator', '')}"
            )
            self.epub_chapters = result.get("chapters", [])
            self.epub_index = result.get("current_index", 0)
            self._epub_show_chapter()
            self.setCurrentIndex(4)
        elif file_type == "markdown":
            self.text_view.setHtml(content)
            self.setCurrentIndex(0)
        elif file_type in {"yaml", "toml", "json", "ini"}:
            html = f'<pre style="font-size: 14pt; line-height: 1.5;">{_escape_html(content)}</pre>'
            self.text_view.setHtml(html)
            self.setCurrentIndex(0)
        elif file_type in {"xlsx", "xls"}:
            self.text_view.setHtml(content)
            self.setCurrentIndex(0)
        elif file_type == "docx":
            page_images = _html_to_page_images(content)
            if page_images:
                result["page_images"] = page_images
                result["pages"] = len(page_images)
                self.pdf_viewer.load(result)
                self.setCurrentIndex(7)
            else:
                self.text_view.setHtml(content)
                self.setCurrentIndex(0)
        elif file_type == "html":
            self.text_view.setHtml(content)
            self.setCurrentIndex(0)
        elif file_type in {"text", "log", "xml", "properties", "csv", "code",
                           "svg", "archive"}:
            self.text_view.setText(content)
            self.setCurrentIndex(0)
        elif file_type == "pdf":
            self.pdf_viewer.load(result)
            self.setCurrentIndex(7)
        elif file_type == "image":
            path = result.get("path", "")
            pixmap = QPixmap(path)
            if not pixmap.isNull():
                max_w = self.image_scroll.viewport().width() - 20
                max_h = self.image_scroll.viewport().height() - 20
                scaled = pixmap.scaled(
                    max_w, max_h,
                    Qt.AspectRatioMode.KeepAspectRatio,
                    Qt.TransformationMode.SmoothTransformation,
                )
                self.image_label.setPixmap(scaled)
            else:
                self.image_label.setText(content)
            self.setCurrentIndex(1)
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
