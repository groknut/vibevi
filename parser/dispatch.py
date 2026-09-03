from pathlib import Path
from typing import Callable
from ._meta import file_meta
from .text import parse_txt, parse_log
from .markdown import parse_md
from .data import parse_json, parse_xml
from .document import parse_pdf, parse_docx
from .spreadsheet import parse_xlsx, parse_xls
from .image import parse_image
from .video import parse_video
from .audio import parse_audio
from .raw import parse_raw


PARSERS: dict[str, Callable[[str], dict]] = {
    ".txt": parse_txt,
    ".md": parse_md,
    ".log": parse_log,
    ".json": parse_json,
    ".xml": parse_xml,
    ".pdf": parse_pdf,
    ".docx": parse_docx,
    ".xlsx": parse_xlsx,
    ".xls": parse_xls,
    ".png": parse_image,
    ".jpeg": parse_image,
    ".jpg": parse_image,
    ".mp4": parse_video,
    ".avi": parse_video,
    ".mkv": parse_video,
    ".mov": parse_video,
    ".mp3": parse_audio,
    ".wav": parse_audio,
    ".m4a": parse_audio,
}


def parse_file(path: str) -> dict:
    ext = Path(path).suffix.lower()
    parser = PARSERS.get(ext)

    if parser is None:
        try:
            return parse_raw(path)
        except Exception as e:
            return {"type": "error", "content": f"[Error reading raw file]: {e}", **file_meta(path)}

    try:
        return parser(path)
    except Exception as e:
        return {"type": "error", "content": f"[Error parsing {ext}]: {e}", **file_meta(path)}
