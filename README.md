# Vibevi

Open-source file viewer built with Python/PyQt6. Two-panel UI with a content viewer on the left and a file tree on the right. All rendering is done programmatically — no external applications required.

## Features

- Two-panel layout: content viewer (left) + file tree (right)
- Sorting files by name, date, or extension (A→Z / Z→A)
- Navigation bar with back, forward, and home buttons
- Keyboard shortcuts (Ctrl+Q, Alt+Left/Right/Home)
- Animated GIF playback
- Video/audio playback with controls
- Multi-page PDF/DOCX viewer with page navigation
- EPUB/FB2 reader with chapter navigation
- Hex/raw file viewer toggle

## Supported Formats

| Category | Extensions |
|----------|------------|
| Text | `.txt`, `.md`, `.log` |
| Data | `.json`, `.xml`, `.csv`, `.yaml`, `.yml`, `.toml` |
| Markup | `.html`, `.htm`, `.svg` |
| Source code | `.py`, `.js`, `.ts`, `.c`, `.cpp`, `.java`, `.go`, `.rs`, `.rb`, `.php`, `.swift`, `.kt`, `.sh`, `.sql`, and more |
| Config | `.ini`, `.cfg`, `.conf`, `.properties` |
| Documents | `.pdf`, `.docx`, `.epub`, `.fb2` |
| Spreadsheets | `.xlsx`, `.xls` |
| Images | `.png`, `.jpg`, `.jpeg`, `.gif`, `.bmp`, `.webp`, `.tiff` |
| Video | `.mp4`, `.avi`, `.mkv`, `.mov`, `.wmv`, `.flv`, `.webm`, `.m4v` |
| Audio | `.mp3`, `.wav`, `.m4a`, `.ogg`, `.flac`, `.aac` |
| Archives | `.zip`, `.tar`, `.tar.gz`, `.tgz`, `.tar.bz2`, `.tar.xz`, `.7z`, `.rar` |

## Requirements

- Python >= 3.12
- uv (package manager)
- System dependencies for video/audio (ffmpeg, Qt multimedia libs)

## Installation

```bash
# Clone the repo
git clone https://github.com/vibevi/vibevi.git
cd vibevi

# Install dependencies
uv sync

# Run
uv run start
# or
uv run main.py
```

### Starting directory

```bash
uv run start /path/to/directory
```

## Keyboard Shortcuts

| Shortcut | Action |
|----------|--------|
| `Ctrl+Q` | Quit |
| `Alt+Left` | Parent directory |
| `Alt+Right` | First subdirectory |
| `Alt+Home` | Home directory |

## Architecture

```
main.py          # Entry point
core/            # Application controller (connects UI and parsers)
ui/              # PyQt6 GUI components
  main_window.py    # Two-panel window with nav and sort bar
  file_tree.py      # File system tree widget
  content_viewer.py # Multi-format viewer (text, image, video, PDF, etc.)
parser/          # File parsing by extension
  dispatch.py       # Central dispatcher (extension → parser)
  text.py, image.py, video.py, audio.py, document.py, ...
sort/            # File sorting logic
```

## Development

```bash
uv sync
uv run main.py
```

Doxygen configuration is in `Doxyfile`. Generate docs with:

```bash
doxygen Doxyfile
```

## License

See [LICENSE](LICENSE) for details.
